from __future__ import annotations

import hashlib
import json
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable

import fcntl

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.execution.validation import (
    SECRET_LIKE_RE,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_ROLLBACK_REF,
    GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF,
    GOVERNED_RUNTIME_SAFE_DISABLE_REF,
    RuntimeActionInboxApprovalDecision,
    RuntimeActionInboxApprovalEnvelope,
    RuntimeApprovalBindingRequest,
    RuntimeAuthority,
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
RUNTIME_GATEWAY_LOCK = "runtime_gateway_invocations.lock"
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
RUNTIME_ACTION_INBOX_REQUESTED_ACTION = "execute_governed_runtime_invocation"


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


def _operator_safe_disable_active(record: RuntimeInvocationRecord) -> bool:
    return (
        record.safe_disable.active
        and record.safe_disable.reason_ref != "reason-ref:governed-runtime-phase-02-disabled"
    )


def _operator_safe_disable_state(
    records: Iterable[RuntimeInvocationRecord],
) -> RuntimeSafeDisableState | None:
    for record in records:
        if _operator_safe_disable_active(record):
            return record.safe_disable
    return None


def _status_after_safe_disable(
    record: RuntimeInvocationRecord,
    desired_status: RuntimeInvocationStatus,
) -> RuntimeInvocationStatus:
    if _operator_safe_disable_active(record):
        return RuntimeInvocationStatus.safe_disabled
    return desired_status


def _derived_exact_scope_ref(record: RuntimeInvocationRecord) -> str:
    return _hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
            "requested_authority": record.request.requested_authority,
        },
    )


def _derived_adapter_id(record: RuntimeInvocationRecord) -> str:
    return (
        "governed-command-runtime-adapter"
        if record.request.requested_authority == RuntimeAuthority.allowlisted_command.value
        else "local-model-runtime-adapter"
    )


def _expected_runtime_action_inbox_approval_ref(
    *,
    record: RuntimeInvocationRecord,
    adapter_id: str,
    command_intent: str | None,
    decision: str,
    exact_scope_ref: str,
) -> str:
    return _hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": record.invocation_ref,
            "requested_authority": record.request.requested_authority,
            "requested_profile": record.request.requested_profile,
            "adapter_id": adapter_id,
            "command_intent": command_intent,
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
    )


def _expected_runtime_action_envelope_ref(
    *,
    record: RuntimeInvocationRecord,
    approval_ref: str,
    decision: str,
    exact_scope_ref: str,
) -> str:
    return _hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
        },
    )


def _runtime_operator_actor_context(approval_ref: str | None = None) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_operator",
        authority_source=AuthoritySource.explicit_user_request,
        approval_ref=approval_ref,
    )


def _runtime_action_inbox_approval_request(
    *,
    record: RuntimeInvocationRecord,
    adapter_id: str,
    command_intent: str | None,
    action_envelope_ref: str,
    exact_scope_ref: str,
    idempotency_ref: str,
    expires_at: Any,
) -> ApprovalRequest:
    command_ref = (
        f"command-intent-ref:{command_intent}"
        if command_intent
        else "command-intent-ref:not-applicable"
    )
    request_ref = _hash_ref(
        "approval-request-ref",
        {
            "invocation_ref": record.invocation_ref,
            "action_envelope_ref": action_envelope_ref,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_ref": idempotency_ref,
        },
    )
    run_ref = _hash_ref(
        "run-ref",
        {
            "operation": RUNTIME_ACTION_INBOX_REQUESTED_ACTION,
            "invocation_ref": record.invocation_ref,
        },
    )
    return ApprovalRequest(
        approval_request_id=request_ref,
        run_id=run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=record.invocation_ref,
        actor_context=_runtime_operator_actor_context(),
        requested_action=RUNTIME_ACTION_INBOX_REQUESTED_ACTION,
        purpose="Approve one exact Action Inbox governed runtime invocation.",
        risk_level=ApprovalRiskLevel.medium,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="governed_runtime_action_inbox",
            requires_redaction=True,
        ),
        resource_refs=[
            record.invocation_ref,
            action_envelope_ref,
            exact_scope_ref,
            record.payload_fingerprint_ref,
            record.policy_decision.policy_decision_ref,
            f"adapter-ref:{adapter_id}",
            command_ref,
            GOVERNED_RUNTIME_ROLLBACK_REF,
            GOVERNED_RUNTIME_SAFE_DISABLE_REF,
            GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF,
            idempotency_ref,
        ],
        event_ref=_hash_ref(
            "event-ref",
            {
                "operation": "runtime-action-inbox-approval",
                "invocation_ref": record.invocation_ref,
                "idempotency_ref": idempotency_ref,
            },
        ),
        trace_id=_hash_ref(
            "trace-ref",
            {
                "operation": "runtime-action-inbox-approval",
                "invocation_ref": record.invocation_ref,
            },
        ),
        expires_at=expires_at,
    )


def _runtime_approval_decision_ref(
    *,
    record: RuntimeInvocationRecord,
    approval_ref: str,
    idempotency_ref: str,
) -> str:
    return _hash_ref(
        "approval-decision-ref",
        {
            "operation": "runtime-action-inbox-approval-decision",
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
        },
    )


def _runtime_approval_validation_ref(
    *,
    record: RuntimeInvocationRecord,
    approval_ref: str,
    idempotency_ref: str,
) -> str:
    return _hash_ref(
        "approval-validation-ref",
        {
            "operation": "runtime-action-inbox-approval-validation",
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
        },
    )


def _action_inbox_envelope_for_request(
    *,
    record: RuntimeInvocationRecord,
    request: RuntimeApprovalBindingRequest,
    idempotency_ref: str,
) -> tuple[RuntimeActionInboxApprovalEnvelope, RuntimeInvocationStatus, bool]:
    now = utc_now()
    decision_value = getattr(request.decision, "value", request.decision)
    command_intent_value = (
        getattr(request.command_intent, "value", request.command_intent)
        if request.command_intent is not None
        else None
    )
    action_ref_prefix = "action-ref:runtime-command-"
    derived_command_intent = (
        record.request.action_ref.removeprefix(action_ref_prefix)
        if record.request.action_ref.startswith(action_ref_prefix)
        else None
    )
    expected_payload = request.expected_payload_fingerprint_ref or record.payload_fingerprint_ref
    expected_policy = (
        request.expected_policy_decision_ref
        or record.policy_decision.policy_decision_ref
    )
    adapter_id = _derived_adapter_id(record)
    exact_scope_ref = _derived_exact_scope_ref(record)
    expected_approval_ref = _expected_runtime_action_inbox_approval_ref(
        record=record,
        adapter_id=adapter_id,
        command_intent=derived_command_intent,
        decision=str(decision_value),
        exact_scope_ref=exact_scope_ref,
    )
    expected_action_envelope_ref = _expected_runtime_action_envelope_ref(
        record=record,
        approval_ref=expected_approval_ref,
        decision=str(decision_value),
        exact_scope_ref=exact_scope_ref,
    )
    approval_ref_for_envelope = request.approval_ref or expected_approval_ref
    approval_decision_ref: str | None = None
    approval_validation_ref: str | None = None
    blocked_reason_refs: list[str] = []
    if expected_payload != record.payload_fingerprint_ref:
        blocked_reason_refs.append("blocked-state:runtime-approval-scope-changed")
    if expected_policy != record.policy_decision.policy_decision_ref:
        blocked_reason_refs.append("blocked-state:runtime-approval-policy-stale")
    if request.approval_ref is not None:
        blocked_reason_refs.append("blocked-state:runtime-approval-ref-identifier-only")
    if request.approval_ref is not None and request.approval_ref != expected_approval_ref:
        blocked_reason_refs.append("blocked-state:runtime-action-inbox-approval-ref-mismatch")
    if (
        request.action_envelope_ref is not None
        and request.action_envelope_ref != expected_action_envelope_ref
    ):
        blocked_reason_refs.append("blocked-state:runtime-action-envelope-ref-mismatch")
    if request.exact_scope_ref is not None and request.exact_scope_ref != exact_scope_ref:
        blocked_reason_refs.append("blocked-state:runtime-exact-scope-ref-mismatch")
    if request.adapter_id is not None and request.adapter_id != adapter_id:
        blocked_reason_refs.append("blocked-state:runtime-adapter-ref-mismatch")
    if (
        record.request.requested_authority == RuntimeAuthority.allowlisted_command.value
        and command_intent_value != derived_command_intent
    ):
        blocked_reason_refs.append("blocked-state:runtime-command-intent-mismatch")
    if request.rollback_ref != GOVERNED_RUNTIME_ROLLBACK_REF:
        blocked_reason_refs.append("blocked-state:runtime-rollback-ref-mismatch")
    if request.safe_disable_ref != GOVERNED_RUNTIME_SAFE_DISABLE_REF:
        blocked_reason_refs.append("blocked-state:runtime-safe-disable-ref-mismatch")
    if request.safe_disable_posture_ref != GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF:
        blocked_reason_refs.append("blocked-state:runtime-safe-disable-posture-mismatch")
    if request.risk_class != "medium":
        blocked_reason_refs.append("blocked-state:runtime-risk-class-mismatch")
    if _operator_safe_disable_active(record):
        blocked_reason_refs.append("blocked-state:runtime-safe-disabled")
    if record.request.requested_profile != "operator-approved":
        blocked_reason_refs.append("blocked-state:runtime-profile-not-operator-approved")
    if request.expires_at is not None and request.expires_at <= now:
        blocked_reason_refs.append("blocked-state:runtime-approval-expired")
    if decision_value == RuntimeActionInboxApprovalDecision.deny.value:
        blocked_reason_refs.append("blocked-state:runtime-approval-denied")
    if decision_value == RuntimeActionInboxApprovalDecision.expire.value:
        blocked_reason_refs.append("blocked-state:runtime-approval-expired")
    if decision_value == RuntimeActionInboxApprovalDecision.approve.value:
        approval_request = _runtime_action_inbox_approval_request(
            record=record,
            adapter_id=adapter_id,
            command_intent=derived_command_intent,
            action_envelope_ref=expected_action_envelope_ref,
            exact_scope_ref=exact_scope_ref,
            idempotency_ref=idempotency_ref,
            expires_at=request.expires_at or (now + timedelta(minutes=30)),
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        if request.approval_ref is None and not blocked_reason_refs:
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id=approval_request.actor_context.actor_id,
                approval_ref=expected_approval_ref,
            )
            authority.load_grant_for_validation(grant)
        decision_result = authority.validate_for_request(
            approval_request,
            approval_ref_for_envelope,
        )
        approval_decision_ref = _runtime_approval_decision_ref(
            record=record,
            approval_ref=approval_ref_for_envelope,
            idempotency_ref=idempotency_ref,
        )
        approval_validation_ref = _runtime_approval_validation_ref(
            record=record,
            approval_ref=approval_ref_for_envelope,
            idempotency_ref=idempotency_ref,
        )
        if not decision_result.allowed:
            blocked_reason_refs.append("blocked-state:runtime-backend-approval-missing")
            blocked_reason_refs.extend(
                f"approval-reason-ref:{reason}" for reason in decision_result.reason_codes
            )
    envelope = RuntimeActionInboxApprovalEnvelope(
        action_envelope_ref=expected_action_envelope_ref,
        invocation_ref=record.invocation_ref,
        adapter_id=adapter_id,
        requested_authority=record.request.requested_authority,
        command_intent=derived_command_intent,
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=record.payload_fingerprint_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        approval_ref=approval_ref_for_envelope,
        approval_scope_ref=request.approval_scope_ref,
        approval_decision_ref=approval_decision_ref,
        approval_validation_ref=approval_validation_ref,
        risk_class="medium",
        expires_at=request.expires_at or (now + timedelta(minutes=30)),
        decision=decision_value,
        idempotency_ref=idempotency_ref,
        rollback_ref=GOVERNED_RUNTIME_ROLLBACK_REF,
        safe_disable_ref=GOVERNED_RUNTIME_SAFE_DISABLE_REF,
        safe_disable_posture_ref=GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF,
        stale_policy=expected_policy != record.policy_decision.policy_decision_ref,
        scope_mismatch=expected_payload != record.payload_fingerprint_ref,
        runtime_profile_weaker_or_disabled=(
            record.request.requested_profile != "operator-approved"
        ),
        safe_disable_active=_operator_safe_disable_active(record),
        blocked_reason_refs=blocked_reason_refs,
        evidence_refs=[
            _hash_ref(
                "runtime-evidence-ref",
                {
                    "invocation_ref": record.invocation_ref,
                    "operation": f"approval-{decision_value}",
                },
            )
        ],
    )
    approval_allowed = (
        not blocked_reason_refs
        and decision_value == RuntimeActionInboxApprovalDecision.approve.value
    )
    approval_reason_refs = (
        ["approval-reason-ref:runtime-action-inbox-exact-receipt-matched"]
        if approval_allowed
        else []
    )
    status = RuntimeInvocationStatus.approved_pending_execution
    if decision_value == RuntimeActionInboxApprovalDecision.deny.value:
        status = RuntimeInvocationStatus.approval_denied
    elif decision_value == RuntimeActionInboxApprovalDecision.expire.value:
        status = RuntimeInvocationStatus.approval_expired
    elif "blocked-state:runtime-approval-expired" in blocked_reason_refs:
        status = RuntimeInvocationStatus.approval_expired
    elif blocked_reason_refs:
        status = RuntimeInvocationStatus.execution_blocked
    validated = approval_allowed and not blocked_reason_refs
    envelope = envelope.model_copy(
        update={
            "status": status,
            "approval_validated": validated,
            "blocked_reason_refs": list(dict.fromkeys([*blocked_reason_refs, *approval_reason_refs])),
            "updated_at": utc_now(),
        }
    )
    command_gateway_validated = (
        validated
        and record.request.requested_authority == RuntimeAuthority.allowlisted_command.value
    )
    return envelope, status, command_gateway_validated


class RuntimeInvocationStore:
    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or runtime_gateway_state_dir()
        self.path = self.state_dir / RUNTIME_GATEWAY_JSONL
        self.lock_path = self.state_dir / RUNTIME_GATEWAY_LOCK
        self._records: dict[str, RuntimeInvocationRecord] = {}
        self._idempotency_index: dict[str, str] = {}
        self._idempotency_fingerprint_index: dict[str, str] = {}
        self._last_entry_hash_ref: str | None = None
        self._loaded = False
        self._process_lock = threading.RLock()

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
        return any(_operator_safe_disable_active(record) for record in self._records.values())

    def create_invocation(
        self,
        request: RuntimeInvocationRequest,
        *,
        idempotency_ref: str,
        local_model_gateway_validated: bool = False,
        command_gateway_validated: bool = False,
    ) -> RuntimeInvocationStoreResult:
        with self._exclusive_mutation():
            return self._create_invocation_loaded(
                request,
                idempotency_ref=idempotency_ref,
                local_model_gateway_validated=local_model_gateway_validated,
                command_gateway_validated=command_gateway_validated,
            )

    def _create_invocation_loaded(
        self,
        request: RuntimeInvocationRequest,
        *,
        idempotency_ref: str,
        local_model_gateway_validated: bool = False,
        command_gateway_validated: bool = False,
    ) -> RuntimeInvocationStoreResult:
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

        operator_safe_disable = _operator_safe_disable_state(self._records.values())
        if operator_safe_disable is not None:
            local_model_gateway_validated = False
            command_gateway_validated = False
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
            command_gateway_validated=command_gateway_validated,
        )
        record = RuntimeInvocationRecord(
            invocation_ref=invocation_ref,
            request=storage_request,
            policy_decision=policy_decision,
            approval_requirement=policy_decision.approval_requirement,
            payload_fingerprint_ref=payload_fingerprint_ref,
            idempotency_ref=idempotency_ref,
            safe_disable=(
                operator_safe_disable
                if operator_safe_disable is not None
                else (
                RuntimeSafeDisableState(
                    active=False,
                    profile=policy_decision.profile,
                    reason_ref="reason-ref:governed-runtime-local-model-active",
                    safe_summary="Runtime profile is active for this exact invocation only.",
                )
                if policy_decision.allowed_to_execute
                else RuntimeSafeDisableState()
                )
            ),
            status=(
                RuntimeInvocationStatus.safe_disabled
                if operator_safe_disable is not None
                else RuntimeInvocationStatus.pending_approval
            ),
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
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            payload_fingerprint_ref = _hash_ref(
                "runtime-operation-fingerprint-ref",
                {
                    "operation": "approval_binding_recorded",
                    "invocation_ref": invocation_ref,
                    "approval_ref": request.approval_ref,
                    "approval_scope_ref": request.approval_scope_ref,
                    "decision": request.decision,
                    "action_envelope_ref": request.action_envelope_ref,
                    "exact_scope_ref": request.exact_scope_ref,
                    "expected_payload_fingerprint_ref": (
                        request.expected_payload_fingerprint_ref
                    ),
                    "expected_policy_decision_ref": request.expected_policy_decision_ref,
                    "adapter_id": request.adapter_id,
                    "command_intent": request.command_intent,
                    "expires_at": (
                        request.expires_at.isoformat() if request.expires_at else None
                    ),
                    "metadata_refs": request.metadata_refs,
                },
            )
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return replayed
            if request.action_envelope_ref:
                envelope, status, command_gateway_validated = (
                    _action_inbox_envelope_for_request(
                        record=record,
                        request=request,
                        idempotency_ref=idempotency_ref,
                    )
                )
                policy_decision = build_policy_decision(
                    record.request,
                    invocation_ref=record.invocation_ref,
                    approval_ref=envelope.approval_ref,
                    status=status,
                    command_gateway_validated=command_gateway_validated,
                )
                policy_decision = policy_decision.model_copy(
                    update={
                        "approval_requirement": policy_decision.approval_requirement.model_copy(
                            update={
                                "approval_validated": envelope.approval_validated,
                                "approval_binding_recorded": True,
                            }
                        ),
                        "reason_codes": [
                            *policy_decision.reason_codes,
                            *[
                                reason_ref.replace("blocked-state:", "BLOCKED_").upper()
                                for reason_ref in envelope.blocked_reason_refs
                            ],
                        ],
                    }
                )
                updated = record.model_copy(
                    update={
                        "policy_decision": policy_decision,
                        "approval_requirement": policy_decision.approval_requirement,
                        "action_inbox_envelope": envelope,
                        "safe_disable": (
                            RuntimeSafeDisableState(
                                active=False,
                                profile=policy_decision.profile,
                                reason_ref="reason-ref:governed-runtime-action-inbox-approved",
                                safe_summary="Runtime profile is active for this exact Action Inbox approved invocation only.",
                            )
                            if command_gateway_validated
                            else record.safe_disable
                        ),
                        "status": _status_after_safe_disable(record, status),
                        "updated_at": utc_now(),
                    }
                )
                self._append(
                    f"action_inbox_approval_{request.decision}_recorded",
                    updated,
                    entry_idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                )
                return updated
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
                    "status": _status_after_safe_disable(
                        record,
                        RuntimeInvocationStatus.pending_approval,
                    ),
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
        with self._exclusive_mutation():
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
                    "status": _status_after_safe_disable(
                        record,
                        RuntimeInvocationStatus.execution_blocked,
                    ),
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
        with self._exclusive_mutation():
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
            receipt_to_store = receipt.model_copy(update={"safe_disable": record.safe_disable})
            updated = record.model_copy(
                update={
                    "receipt": receipt_to_store,
                    "status": _status_after_safe_disable(
                        record,
                        receipt.invocation_status,
                    ),
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

    def mark_action_inbox_execution_receipt(
        self,
        invocation_ref: str,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationRecord:
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            validate_execution_ref(payload_fingerprint_ref, "payload_fingerprint_ref")
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return replayed
            if record.action_inbox_envelope is None:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_ACTION_INBOX_ENVELOPE_MISSING"
                )
            receipt_refs = (
                [record.receipt.receipt_ref]
                if record.receipt is not None
                else []
            )
            evidence_refs = (
                list(record.receipt.evidence_refs)
                if record.receipt is not None
                else []
            )
            envelope = record.action_inbox_envelope.model_copy(
                update={
                    "status": record.status,
                    "execution_performed": bool(
                        record.receipt and record.receipt.execution_performed
                    ),
                    "receipt_refs": receipt_refs,
                    "evidence_refs": list(
                        dict.fromkeys(
                            [
                                *record.action_inbox_envelope.evidence_refs,
                                *evidence_refs,
                            ]
                        )
                    ),
                    "updated_at": utc_now(),
                }
            )
            updated = record.model_copy(
                update={
                    "action_inbox_envelope": envelope,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "action_inbox_execution_receipt_linked",
                updated,
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return updated

    def begin_action_inbox_execution(
        self,
        invocation_ref: str,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationStoreResult:
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            validate_execution_ref(payload_fingerprint_ref, "payload_fingerprint_ref")
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return RuntimeInvocationStoreResult(record=replayed, replayed=True)
            self._append(
                "action_inbox_execution_started",
                record.model_copy(update={"updated_at": utc_now()}),
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return RuntimeInvocationStoreResult(record=record, replayed=False)

    def safe_disable(
        self,
        request: RuntimeSafeDisableRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeSafeDisableState:
        with self._exclusive_mutation():
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
                    policy_decision = build_policy_decision(
                        record.request,
                        invocation_ref=record.invocation_ref,
                        approval_ref=record.approval_requirement.approval_ref,
                        status=RuntimeInvocationStatus.safe_disabled,
                    )
                    receipt = (
                        record.receipt.model_copy(update={"safe_disable": state})
                        if record.receipt is not None
                        else None
                    )
                    updated = record.model_copy(
                        update={
                            "approval_requirement": policy_decision.approval_requirement,
                            "policy_decision": policy_decision,
                            "receipt": receipt,
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
                result = self._create_invocation_loaded(
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
        self._reload()

    def _reload(self) -> None:
        self._records = {}
        self._idempotency_index = {}
        self._idempotency_fingerprint_index = {}
        self._last_entry_hash_ref = None
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

    @contextmanager
    def _exclusive_mutation(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self._process_lock:
            with self.lock_path.open("a", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                try:
                    self._reload()
                    yield
                finally:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

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
