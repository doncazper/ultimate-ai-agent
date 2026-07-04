from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.validation import (
    SECRET_LIKE_RE,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeApprovalBindingRequest,
    RuntimeInvocationRecord,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeSafeDisableRequest,
    RuntimeSafeDisableState,
    build_blocked_receipt,
    build_policy_decision,
    runtime_invocation_ref,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


RUNTIME_GATEWAY_STORAGE_SCHEMA_VERSION = "runtime_gateway_storage.v1"
RUNTIME_GATEWAY_STATE_DIR_ENV = "UAA_RUNTIME_GATEWAY_STATE_DIR"
RUNTIME_GATEWAY_JSONL = "runtime_gateway_invocations.jsonl"
UNSAFE_RUNTIME_STORAGE_KEY_FRAGMENTS = (
    "raw",
    "prompt_text",
    "response_text",
    "content_body",
    "command_output",
    "stdout",
    "stderr",
    "local_path",
    "absolute_path",
    "environment_dump",
    "credential_value",
    "secret_value",
    "provider_payload",
)
UNSAFE_RUNTIME_STORAGE_TEXT_FRAGMENTS = (
    "-----BEGIN",
    "authorization:",
    "bearer ",
    "cookie:",
    "password=",
    "api_key=",
    "/Users/",
    "/home/",
)
SAFE_FALSE_PERSISTENCE_FLAG_KEYS = {
    "prompt_content_persisted",
    "response_content_persisted",
    "command_output_persisted",
    "local_path_persisted",
    "environment_persisted",
    "sensitive_material_persisted",
    "provider_exchange_persisted",
}


class RuntimeInvocationStorageError(RuntimeError):
    """Base error for governed runtime pilot storage."""


class RuntimeInvocationConflictError(RuntimeInvocationStorageError):
    """Raised when idempotency replay detects a changed payload."""


class RuntimeInvocationNotFoundError(RuntimeInvocationStorageError):
    """Raised when an invocation ref is unknown."""


class RuntimeInvocationUnsafePayloadError(RuntimeInvocationStorageError):
    """Raised when a payload is unsafe for durable runtime storage."""


class RuntimeGatewayStorageEntry(BaseModel):
    schema_version: str = RUNTIME_GATEWAY_STORAGE_SCHEMA_VERSION
    entry_ref: str = Field(..., min_length=1)
    entry_kind: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    record: RuntimeInvocationRecord
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "RuntimeGatewayStorageEntry":
        for value, field_name in [
            (self.entry_ref, "entry_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.entry_hash_ref, "entry_hash_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.previous_entry_hash_ref:
            validate_execution_ref(self.previous_entry_hash_ref, "previous_entry_hash_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.entry_kind, "entry_kind")
        _validate_storage_payload(self.model_dump(mode="json", exclude={"entry_hash_ref"}))
        return self


@dataclass(frozen=True)
class RuntimeInvocationStoreResult:
    record: RuntimeInvocationRecord
    replayed: bool = False


def runtime_gateway_state_dir() -> Path:
    configured = os.getenv(RUNTIME_GATEWAY_STATE_DIR_ENV, "").strip()
    if configured:
        return Path(configured)
    return Path(".uaa") / "runtime-gateway"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()[:24]}"


def _summary_storage_ref(value: str, *, prefix: str = "runtime-summary-ref") -> str:
    validate_safe_execution_text(value, "runtime_safe_summary")
    return _hash_ref(prefix, {"summary": value})


def _validate_storage_payload(value: Any, field_name: str = "runtime_storage") -> None:
    if isinstance(value, str):
        validate_safe_execution_text(value, field_name)
        lowered = value.lower()
        if SECRET_LIKE_RE.search(value):
            raise RuntimeInvocationUnsafePayloadError("RUNTIME_STORAGE_SECRET_LIKE_TEXT_DENIED")
        if any(fragment.lower() in lowered for fragment in UNSAFE_RUNTIME_STORAGE_TEXT_FRAGMENTS):
            raise RuntimeInvocationUnsafePayloadError("RUNTIME_STORAGE_UNSAFE_TEXT_DENIED")
        return
    if isinstance(value, list):
        for item in value:
            _validate_storage_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            validate_safe_execution_text(key_text, "runtime_storage_key")
            normalized = key_text.lower().replace("-", "_")
            if normalized in SAFE_FALSE_PERSISTENCE_FLAG_KEYS:
                if item is not False:
                    raise RuntimeInvocationUnsafePayloadError(
                        "RUNTIME_STORAGE_UNSAFE_PERSISTENCE_FLAG_DENIED"
                    )
                continue
            if any(fragment in normalized for fragment in UNSAFE_RUNTIME_STORAGE_KEY_FRAGMENTS):
                raise RuntimeInvocationUnsafePayloadError("RUNTIME_STORAGE_UNSAFE_KEY_DENIED")
            _validate_storage_payload(item, field_name)
        return
    validate_safe_execution_payload(value, field_name)


def _entry_hash(entry_payload: dict[str, Any]) -> str:
    return _hash_ref("runtime-storage-entry-hash-ref", entry_payload)


class RuntimeInvocationStore:
    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or runtime_gateway_state_dir()
        self.path = self.state_dir / RUNTIME_GATEWAY_JSONL
        self._records: dict[str, RuntimeInvocationRecord] = {}
        self._idempotency_index: dict[str, str] = {}
        self._idempotency_fingerprint_index: dict[str, str] = {}
        self._last_entry_hash_ref: str | None = None
        self._loaded = False

    def capabilities_storage_ref(self) -> str:
        return _hash_ref("runtime-storage-ref", {"path": RUNTIME_GATEWAY_JSONL})

    def list_invocations(self) -> list[RuntimeInvocationRecord]:
        self._load()
        return sorted(self._records.values(), key=lambda record: record.created_at.isoformat())

    def get_invocation(self, invocation_ref: str) -> RuntimeInvocationRecord:
        self._load()
        validate_execution_ref(invocation_ref, "invocation_ref")
        try:
            return self._records[invocation_ref]
        except KeyError as exc:
            raise RuntimeInvocationNotFoundError(invocation_ref) from exc

    def operator_safe_disable_active(self) -> bool:
        self._load()
        return any(
            record.status == RuntimeInvocationStatus.safe_disabled.value
            and record.safe_disable.active
            and record.safe_disable.reason_ref != "reason-ref:governed-runtime-phase-02-disabled"
            for record in self._records.values()
        )

    def create_invocation(
        self,
        request: RuntimeInvocationRequest,
        *,
        idempotency_ref: str,
        local_model_gateway_validated: bool = False,
    ) -> RuntimeInvocationStoreResult:
        self._load()
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        payload_fingerprint_ref = runtime_payload_fingerprint_ref(request)
        existing_ref = self._idempotency_index.get(idempotency_ref)
        if existing_ref:
            existing = self._records[existing_ref]
            existing_fingerprint = self._idempotency_fingerprint_index.get(
                idempotency_ref,
                existing.payload_fingerprint_ref,
            )
            if existing_fingerprint != payload_fingerprint_ref:
                raise RuntimeInvocationConflictError("RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT")
            replayed = existing.model_copy(update={"replay_count": existing.replay_count + 1})
            self._records[existing_ref] = replayed
            return RuntimeInvocationStoreResult(record=replayed, replayed=True)

        invocation_ref = runtime_invocation_ref(idempotency_ref, payload_fingerprint_ref)
        request_with_idempotency = request.model_copy(update={"idempotency_ref": idempotency_ref})
        storage_request = request_with_idempotency.model_copy(
            update={"safe_summary": _summary_storage_ref(request.safe_summary)}
        )
        policy_decision = build_policy_decision(
            storage_request,
            invocation_ref=invocation_ref,
            status=RuntimeInvocationStatus.pending_approval,
            local_model_gateway_validated=local_model_gateway_validated,
        )
        record = RuntimeInvocationRecord(
            invocation_ref=invocation_ref,
            request=storage_request,
            policy_decision=policy_decision,
            approval_requirement=policy_decision.approval_requirement,
            payload_fingerprint_ref=payload_fingerprint_ref,
            idempotency_ref=idempotency_ref,
            safe_disable=(
                RuntimeSafeDisableState(
                    active=False,
                    profile=policy_decision.profile,
                    reason_ref="reason-ref:governed-runtime-local-model-active",
                    safe_summary="Local model runtime profile is active for this invocation only.",
                )
                if policy_decision.allowed_to_execute
                else RuntimeSafeDisableState()
            ),
            status=RuntimeInvocationStatus.pending_approval,
        )
        self._append(
            "invocation_created",
            record,
            entry_idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        return RuntimeInvocationStoreResult(record=record, replayed=False)

    def bind_approval(
        self,
        invocation_ref: str,
        request: RuntimeApprovalBindingRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord:
        record = self.get_invocation(invocation_ref)
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        payload_fingerprint_ref = _hash_ref(
            "runtime-operation-fingerprint-ref",
            {
                "operation": "approval_binding_recorded",
                "invocation_ref": invocation_ref,
                "approval_ref": request.approval_ref,
                "approval_scope_ref": request.approval_scope_ref,
                "metadata_refs": request.metadata_refs,
            },
        )
        replayed = self._idempotent_operation_replay(
            idempotency_ref,
            payload_fingerprint_ref,
        )
        if replayed is not None:
            return replayed
        policy_decision = build_policy_decision(
            record.request,
            invocation_ref=record.invocation_ref,
            approval_ref=request.approval_ref,
            status=RuntimeInvocationStatus.pending_approval,
        )
        updated = record.model_copy(
            update={
                "policy_decision": policy_decision,
                "approval_requirement": policy_decision.approval_requirement,
                "status": RuntimeInvocationStatus.pending_approval,
                "updated_at": utc_now(),
            }
        )
        self._append(
            "approval_binding_recorded",
            updated,
            entry_idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        return updated

    def record_blocked_execute(
        self,
        invocation_ref: str,
        *,
        safe_summary: str,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord:
        record = self.get_invocation(invocation_ref)
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        payload_fingerprint_ref = _hash_ref(
            "runtime-operation-fingerprint-ref",
            {
                "operation": "execution_blocked_receipt_recorded",
                "invocation_ref": invocation_ref,
                "safe_summary_ref": _summary_storage_ref(
                    safe_summary,
                    prefix="runtime-execute-summary-ref",
                ),
            },
        )
        replayed = self._idempotent_operation_replay(
            idempotency_ref,
            payload_fingerprint_ref,
        )
        if replayed is not None:
            return replayed
        receipt = build_blocked_receipt(
            record,
            safe_summary="Runtime execution remains blocked for unpromoted authority; operator summary omitted.",
        )
        updated = record.model_copy(
            update={
                "receipt": receipt,
                "status": RuntimeInvocationStatus.execution_blocked,
                "updated_at": utc_now(),
            }
        )
        self._append(
            "execution_blocked_receipt_recorded",
            updated,
            entry_idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        return updated

    def record_receipt(
        self,
        invocation_ref: str,
        receipt: RuntimeInvocationReceipt,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str | None = None,
    ) -> RuntimeInvocationRecord:
        record = self.get_invocation(invocation_ref)
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        payload_fingerprint_ref = payload_fingerprint_ref or _hash_ref(
            "runtime-operation-fingerprint-ref",
            {
                "operation": "receipt_recorded",
                "invocation_ref": invocation_ref,
                "receipt_ref": receipt.receipt_ref,
                "receipt_status": receipt.invocation_status,
            },
        )
        replayed = self._idempotent_operation_replay(
            idempotency_ref,
            payload_fingerprint_ref,
        )
        if replayed is not None:
            return replayed
        updated = record.model_copy(
            update={
                "receipt": receipt,
                "status": receipt.invocation_status,
                "updated_at": utc_now(),
            }
        )
        self._append(
            "receipt_recorded",
            updated,
            entry_idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        return updated

    def safe_disable(
        self,
        request: RuntimeSafeDisableRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeSafeDisableState:
        self._load()
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        payload_fingerprint_ref = _hash_ref(
            "runtime-operation-fingerprint-ref",
            {
                "operation": "safe_disable_recorded",
                "reason_ref": request.reason_ref,
                "metadata_refs": request.metadata_refs,
            },
        )
        replayed = self._idempotent_operation_replay(
            idempotency_ref,
            payload_fingerprint_ref,
        )
        if replayed is not None and replayed.safe_disable:
            return replayed.safe_disable
        state = RuntimeSafeDisableState(
            reason_ref=request.reason_ref,
            safe_summary="Runtime pilot safe-disable posture recorded; operator summary omitted.",
        )
        if self._records:
            for index, record in enumerate(list(self._records.values())):
                updated = record.model_copy(
                    update={
                        "safe_disable": state,
                        "status": RuntimeInvocationStatus.safe_disabled,
                        "updated_at": utc_now(),
                    }
                )
                self._append(
                    "safe_disable_recorded",
                    updated,
                    entry_idempotency_ref=(
                        idempotency_ref
                        if index == 0
                        else _hash_ref(
                            "idempotency-ref",
                            {
                                "base_idempotency_ref": idempotency_ref,
                                "invocation_ref": record.invocation_ref,
                            },
                        )
                    ),
                    payload_fingerprint_ref=payload_fingerprint_ref,
                )
        else:
            placeholder_request = RuntimeInvocationRequest(
                requested_authority="local_model",
                requested_profile="sealed",
                input_ref="runtime-input-ref:safe-disable-placeholder",
                safe_summary="Safe-disable state recorded before any runtime invocation.",
            )
            result = self.create_invocation(
                placeholder_request,
                idempotency_ref=_hash_ref(
                    "idempotency-ref",
                    {"reason_ref": request.reason_ref, "kind": "safe-disable"},
                ),
            )
            updated = result.record.model_copy(
                update={
                    "safe_disable": state,
                    "status": RuntimeInvocationStatus.safe_disabled,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "safe_disable_recorded",
                updated,
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
        return state

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.path.exists():
            return
        previous_hash: str | None = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            try:
                entry = RuntimeGatewayStorageEntry(**payload)
            except ValidationError as exc:
                raise RuntimeInvocationStorageError("RUNTIME_STORAGE_ENTRY_INVALID") from exc
            expected_hash = _entry_hash(
                entry.model_dump(mode="json", exclude={"entry_hash_ref"})
            )
            if entry.entry_hash_ref != expected_hash:
                raise RuntimeInvocationStorageError("RUNTIME_STORAGE_ENTRY_HASH_MISMATCH")
            if entry.previous_entry_hash_ref != previous_hash:
                raise RuntimeInvocationStorageError("RUNTIME_STORAGE_HASH_CHAIN_MISMATCH")
            self._records[entry.invocation_ref] = entry.record
            self._idempotency_index[entry.idempotency_ref] = entry.invocation_ref
            self._idempotency_fingerprint_index[entry.idempotency_ref] = (
                entry.payload_fingerprint_ref
            )
            previous_hash = entry.entry_hash_ref
        self._last_entry_hash_ref = previous_hash

    def _idempotent_operation_replay(
        self,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationRecord | None:
        existing_ref = self._idempotency_index.get(idempotency_ref)
        if existing_ref is None:
            return None
        existing_fingerprint = self._idempotency_fingerprint_index.get(idempotency_ref)
        if existing_fingerprint != payload_fingerprint_ref:
            raise RuntimeInvocationConflictError("RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT")
        existing = self._records[existing_ref]
        replayed = existing.model_copy(update={"replay_count": existing.replay_count + 1})
        self._records[existing_ref] = replayed
        return replayed

    def _append(
        self,
        entry_kind: str,
        record: RuntimeInvocationRecord,
        *,
        entry_idempotency_ref: str | None = None,
        payload_fingerprint_ref: str | None = None,
    ) -> None:
        self._load()
        entry_idempotency_ref = entry_idempotency_ref or record.idempotency_ref
        payload_fingerprint_ref = payload_fingerprint_ref or record.payload_fingerprint_ref
        payload_without_hash = {
            "schema_version": RUNTIME_GATEWAY_STORAGE_SCHEMA_VERSION,
            "entry_ref": _hash_ref(
                "runtime-storage-entry-ref",
                {
                    "entry_kind": entry_kind,
                    "invocation_ref": record.invocation_ref,
                    "updated_at": record.updated_at.isoformat(),
                    "previous": self._last_entry_hash_ref,
                },
            ),
            "entry_kind": entry_kind,
            "invocation_ref": record.invocation_ref,
            "idempotency_ref": entry_idempotency_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "record": record.model_dump(mode="json"),
            "previous_entry_hash_ref": self._last_entry_hash_ref,
        }
        _validate_storage_payload(payload_without_hash)
        entry_payload = {
            **payload_without_hash,
            "entry_hash_ref": _entry_hash(payload_without_hash),
        }
        entry = RuntimeGatewayStorageEntry(**entry_payload)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(entry.model_dump(mode="json")) + "\n")
        self._records[record.invocation_ref] = record
        self._idempotency_index[entry_idempotency_ref] = record.invocation_ref
        self._idempotency_fingerprint_index[entry_idempotency_ref] = payload_fingerprint_ref
        self._last_entry_hash_ref = entry.entry_hash_ref
