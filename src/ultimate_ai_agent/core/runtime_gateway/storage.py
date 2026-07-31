from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Iterable

import fcntl

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.authority import (
    AuthorityDecisionOutcome,
    AuthorityLease,
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
    build_default_authority_leases,
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
    RuntimeLocalModelReceiptMetadata,
    RuntimeProfile,
    RuntimePolicyDecision,
    RuntimeSafeDisableRequest,
    RuntimeSafeDisableState,
    build_blocked_receipt,
    build_local_model_receipt,
    build_policy_decision,
    runtime_invocation_ref,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


RUNTIME_GATEWAY_STORAGE_SCHEMA_VERSION = "runtime_gateway_storage.v1"
RUNTIME_GATEWAY_STATE_DIR_ENV = "UAA_RUNTIME_GATEWAY_STATE_DIR"
RUNTIME_GATEWAY_JSONL = "runtime_gateway_invocations.jsonl"
RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON = "runtime_gateway_safe_disable_state.json"
RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES = 16_384
RUNTIME_GATEWAY_LOCK = "runtime_gateway_invocations.lock"
RUNTIME_GATEWAY_LOCK_TIMEOUT_SECONDS = 1.0
RUNTIME_GATEWAY_LOCK_POLL_SECONDS = 0.01
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


@dataclass(frozen=True)
class RuntimeAdapterDispatchClaim:
    """One durable adapter-boundary claim and its single-call ownership."""

    record: RuntimeInvocationRecord
    acquired: bool


def runtime_gateway_state_dir() -> Path:
    configured = os.getenv(RUNTIME_GATEWAY_STATE_DIR_ENV, "").strip()
    if configured:
        return Path(configured)
    return Path(".uaa") / "runtime-gateway"


_RUNTIME_GATEWAY_STATE_DIR_IDENTITIES: dict[str, tuple[int, int]] = {}
_RUNTIME_GATEWAY_STATE_DIR_IDENTITIES_LOCK = threading.RLock()


def _runtime_gateway_state_dir_key(state_dir: Path) -> str:
    return os.path.abspath(os.fspath(state_dir))


def _open_runtime_gateway_state_dir(
    state_dir: Path,
    *,
    create: bool,
) -> tuple[int, tuple[int, int]] | None:
    """Open and retain the exact validated state-root directory descriptor."""

    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("runtime gateway state directory guard unavailable")
    absolute = Path(_runtime_gateway_state_dir_key(state_dir))
    if absolute == Path(absolute.anchor):
        raise OSError("runtime gateway state directory cannot be a filesystem root")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise OSError("runtime gateway state directory component is invalid")
            try:
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    return None
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        opened = os.fstat(descriptor)
        linked = os.lstat(absolute)
        identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(linked.st_mode)
            or stat.S_ISLNK(linked.st_mode)
            or identity != (linked.st_dev, linked.st_ino)
        ):
            raise OSError("runtime gateway state directory identity mismatch")
        if create:
            os.fchmod(descriptor, 0o700)
        retained_descriptor = descriptor
        descriptor = -1
        return retained_descriptor, identity
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _runtime_gateway_state_dir_chain_identity(
    state_dir: Path,
    *,
    create: bool,
) -> tuple[int, int] | None:
    opened = _open_runtime_gateway_state_dir(state_dir, create=create)
    if opened is None:
        return None
    descriptor, identity = opened
    try:
        return identity
    finally:
        os.close(descriptor)


def _bind_runtime_gateway_state_dir_identity(
    state_dir: Path,
    identity: tuple[int, int] | None,
) -> None:
    key = _runtime_gateway_state_dir_key(state_dir)
    with _RUNTIME_GATEWAY_STATE_DIR_IDENTITIES_LOCK:
        expected = _RUNTIME_GATEWAY_STATE_DIR_IDENTITIES.get(key)
        if identity is None:
            if expected is not None:
                raise OSError("runtime gateway state directory disappeared")
            return
        if expected is not None and expected != identity:
            raise OSError("runtime gateway state directory changed")
        _RUNTIME_GATEWAY_STATE_DIR_IDENTITIES.setdefault(key, identity)


def _validate_runtime_gateway_state_dir(
    state_dir: Path,
    *,
    create: bool,
) -> None:
    identity = _runtime_gateway_state_dir_chain_identity(state_dir, create=create)
    _bind_runtime_gateway_state_dir_identity(state_dir, identity)


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
    materialized = list(records)
    operator_states = [
        record.safe_disable
        for record in materialized
        if _operator_safe_disable_active(record)
    ]
    if not operator_states:
        return None
    canonical = operator_states[0]
    if len(operator_states) != len(materialized) or any(
        state != canonical for state in operator_states[1:]
    ):
        raise RuntimeInvocationStorageError(
            "RUNTIME_SAFE_DISABLE_LEDGER_MISMATCH"
        )
    return canonical


def _runtime_default_safe_disable_state() -> RuntimeSafeDisableState:
    return RuntimeSafeDisableState(
        active=False,
        profile=RuntimeProfile.sealed.value,
        reason_ref="reason-ref:governed-runtime-local-model-active",
        safe_summary="Runtime profile is active for this exact invocation only.",
    )


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
    active_authority_leases: list[AuthorityLease],
    kill_switch_engaged: bool = False,
) -> tuple[
    RuntimeActionInboxApprovalEnvelope,
    RuntimeInvocationStatus,
    bool,
    RuntimePolicyDecision,
]:
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
    validated = approval_allowed
    command_gateway_validated = (
        validated
        and record.request.requested_authority == RuntimeAuthority.allowlisted_command.value
    )
    policy_decision = build_policy_decision(
        record.request,
        invocation_ref=record.invocation_ref,
        approval_ref=approval_ref_for_envelope,
        status=status,
        command_gateway_validated=command_gateway_validated,
        active_authority_leases=active_authority_leases,
        kill_switch_engaged=kill_switch_engaged,
    )
    authority_scope_allowed = (
        policy_decision.authority_decision_outcome == AuthorityDecisionOutcome.allow.value
    )
    authority_blocked_reason_refs: list[str] = []
    if approval_allowed and not authority_scope_allowed:
        authority_blocked_reason_refs = list(
            dict.fromkeys(
                [
                    "blocked-state:runtime-authority-lease-required",
                    *policy_decision.authority_reason_refs,
                ]
            )
        )
        status = RuntimeInvocationStatus.execution_blocked
        policy_decision = policy_decision.model_copy(
            update={"invocation_status": status}
        )
    envelope = RuntimeActionInboxApprovalEnvelope(
        action_envelope_ref=expected_action_envelope_ref,
        invocation_ref=record.invocation_ref,
        adapter_id=adapter_id,
        requested_authority=record.request.requested_authority,
        command_intent=derived_command_intent,
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=record.payload_fingerprint_ref,
        policy_decision_ref=policy_decision.policy_decision_ref,
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
        authority_scope_allowed=authority_scope_allowed,
        authority_decision_ref=policy_decision.authority_decision_ref,
        authority_decision_outcome=policy_decision.authority_decision_outcome,
        authority_lease_ref=policy_decision.authority_lease_ref,
        authority_domain_ref=(
            f"authority-domain-ref:{policy_decision.authority_domain}"
            if policy_decision.authority_domain
            else None
        ),
        authority_capability_ref=(
            f"authority-capability-ref:{policy_decision.authority_capability}"
            if policy_decision.authority_capability
            else None
        ),
        authority_required_mode_ref=(
            f"authority-mode-ref:{str(policy_decision.authority_required_mode).replace('_', '-')}"
            if policy_decision.authority_required_mode
            else None
        ),
        authority_reason_refs=list(policy_decision.authority_reason_refs),
        authority_audit_ref=policy_decision.authority_audit_ref,
        authority_policy_receipt_ref=policy_decision.authority_policy_receipt_ref,
        authority_operator_message=policy_decision.authority_operator_message,
        stale_policy=expected_policy != record.policy_decision.policy_decision_ref,
        scope_mismatch=expected_payload != record.payload_fingerprint_ref,
        runtime_profile_weaker_or_disabled=(
            record.request.requested_profile != "operator-approved"
        ),
        safe_disable_active=_operator_safe_disable_active(record),
        blocked_reason_refs=list(
            dict.fromkeys([*blocked_reason_refs, *authority_blocked_reason_refs])
        ),
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
    envelope = envelope.model_copy(
        update={
            "status": status,
            "approval_validated": validated,
            "blocked_reason_refs": list(
                dict.fromkeys(
                    [
                        *blocked_reason_refs,
                        *authority_blocked_reason_refs,
                        *approval_reason_refs,
                    ]
                )
            ),
            "updated_at": utc_now(),
        }
    )
    return envelope, status, command_gateway_validated, policy_decision


def active_runtime_authority_leases() -> list[AuthorityLease]:
    active = AuthorityLeaseStore().list_leases(active_only=True)
    return active or build_default_authority_leases()


class RuntimeInvocationStore:
    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        active_authority_leases: Iterable[AuthorityLease] | None = None,
    ) -> None:
        self.state_dir = state_dir or runtime_gateway_state_dir()
        self.path = self.state_dir / RUNTIME_GATEWAY_JSONL
        self.lock_path = self.state_dir / RUNTIME_GATEWAY_LOCK
        self._safe_disable_state_path = (
            self.state_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
        )
        self._explicit_active_authority_leases = (
            list(active_authority_leases)
            if active_authority_leases is not None
            else None
        )
        self._records: dict[str, RuntimeInvocationRecord] = {}
        self._entries: list[RuntimeGatewayStorageEntry] = []
        self._idempotency_index: dict[str, str] = {}
        self._idempotency_fingerprint_index: dict[str, str] = {}
        self._canonical_safe_disable_state = _runtime_default_safe_disable_state()
        self._last_entry_hash_ref: str | None = None
        self._loaded_ledger_identity: tuple[int, int] | None = None
        self._loaded = False
        self._process_lock = threading.RLock()
        self._mutation_directory_fds: list[int] = []

    def capabilities_storage_ref(self) -> str:
        return _hash_ref("runtime-storage-ref", {"path": RUNTIME_GATEWAY_JSONL})

    def current_authority_leases(self) -> list[AuthorityLease]:
        if self._explicit_active_authority_leases is not None:
            return list(self._explicit_active_authority_leases)
        return active_runtime_authority_leases()

    def authority_lease_kill_switch_engaged(self) -> bool:
        return authority_lease_kill_switch_engaged()

    def list_invocations(self) -> list[RuntimeInvocationRecord]:
        self._load()
        return sorted(self._records.values(), key=lambda record: record.created_at.isoformat())

    def list_invocations_locked(self) -> list[RuntimeInvocationRecord]:
        """Reload and return one exact durable invocation generation."""

        with self._exclusive_mutation():
            return sorted(
                self._records.values(),
                key=lambda record: record.created_at.isoformat(),
            )

    def list_entries(self) -> list[RuntimeGatewayStorageEntry]:
        self._load()
        return list(self._entries)

    def get_invocation(self, invocation_ref: str) -> RuntimeInvocationRecord:
        self._load()
        validate_execution_ref(invocation_ref, "invocation_ref")
        try:
            return self._records[invocation_ref]
        except KeyError as exc:
            raise RuntimeInvocationNotFoundError(invocation_ref) from exc

    def get_invocation_for_idempotency(
        self,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord | None:
        self._load()
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        invocation_ref = self._idempotency_index.get(idempotency_ref)
        if invocation_ref is None:
            return None
        return self._records[invocation_ref]

    def get_invocation_for_idempotency_locked(
        self,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord | None:
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        with self._exclusive_mutation():
            invocation_ref = self._idempotency_index.get(idempotency_ref)
            if invocation_ref is None:
                return None
            return self._records[invocation_ref]

    def operator_safe_disable_active(self) -> bool:
        self._load()
        return self._canonical_safe_disable_state.active

    def operator_safe_disable_state(self) -> RuntimeSafeDisableState:
        self._load()
        return self._canonical_safe_disable_state.model_copy()

    def create_invocation(
        self,
        request: RuntimeInvocationRequest,
        *,
        idempotency_ref: str,
        local_model_gateway_validated: bool = False,
        command_gateway_validated: bool = False,
        action_inbox_envelope_required: bool = True,
        adapter_dispatch_protocol_ref: str | None = None,
    ) -> RuntimeInvocationStoreResult:
        with self._exclusive_mutation():
            return self._create_invocation_loaded(
                request,
                idempotency_ref=idempotency_ref,
                local_model_gateway_validated=local_model_gateway_validated,
                command_gateway_validated=command_gateway_validated,
                action_inbox_envelope_required=action_inbox_envelope_required,
                adapter_dispatch_protocol_ref=adapter_dispatch_protocol_ref,
            )

    def _create_invocation_loaded(
        self,
        request: RuntimeInvocationRequest,
        *,
        idempotency_ref: str,
        local_model_gateway_validated: bool = False,
        command_gateway_validated: bool = False,
        action_inbox_envelope_required: bool = True,
        adapter_dispatch_protocol_ref: str | None = None,
    ) -> RuntimeInvocationStoreResult:
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        if adapter_dispatch_protocol_ref is not None:
            validate_execution_ref(
                adapter_dispatch_protocol_ref,
                "adapter_dispatch_protocol_ref",
            )
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
            if (
                existing.approval_requirement.action_inbox_envelope_required
                != action_inbox_envelope_required
            ):
                legacy_readonly_pre_dispatch = bool(
                    existing.request.requested_authority
                    == RuntimeAuthority.allowlisted_command.value
                    and existing.request.action_ref
                    == "action-ref:runtime-command-git_status"
                    and command_gateway_validated
                    and existing.approval_requirement.action_inbox_envelope_required
                    and not action_inbox_envelope_required
                    and adapter_dispatch_protocol_ref is not None
                    and existing.adapter_dispatch_protocol_ref
                    == adapter_dispatch_protocol_ref
                    and not existing.adapter_dispatch_started
                    and existing.receipt is None
                )
                if not legacy_readonly_pre_dispatch:
                    raise RuntimeInvocationConflictError(
                        "RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT"
                    )
                existing = existing.model_copy(
                    update={
                        "approval_requirement": (
                            existing.approval_requirement.model_copy(
                                update={
                                    "action_inbox_envelope_required": False,
                                }
                            )
                        ),
                        "updated_at": utc_now(),
                    }
                )
                migration_idempotency_ref = _hash_ref(
                    "idempotency-ref",
                    {
                        "base_idempotency_ref": idempotency_ref,
                        "operation": (
                            "legacy-readonly-action-inbox-requirement-migrated"
                        ),
                    },
                )
                migration_fingerprint_ref = _hash_ref(
                    "runtime-operation-fingerprint-ref",
                    {
                        "operation": (
                            "legacy-readonly-action-inbox-requirement-migrated"
                        ),
                        "invocation_ref": existing.invocation_ref,
                        "adapter_dispatch_protocol_ref": (
                            adapter_dispatch_protocol_ref
                        ),
                    },
                )
                self._append(
                    "legacy_readonly_action_inbox_requirement_migrated",
                    existing,
                    entry_idempotency_ref=migration_idempotency_ref,
                    payload_fingerprint_ref=migration_fingerprint_ref,
                )
            if (
                adapter_dispatch_protocol_ref is not None
                and existing.adapter_dispatch_protocol_ref
                != adapter_dispatch_protocol_ref
                and not (
                    existing.adapter_dispatch_protocol_ref is None
                    and existing.receipt is not None
                )
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_ADAPTER_DISPATCH_PROTOCOL_MISMATCH"
                )
            replayed = existing.model_copy(update={"replay_count": existing.replay_count + 1})
            self._records[existing_ref] = replayed
            return RuntimeInvocationStoreResult(record=replayed, replayed=True)

        operator_safe_disable = self._canonical_safe_disable_state
        if operator_safe_disable.active:
            local_model_gateway_validated = False
            command_gateway_validated = False
        invocation_ref = runtime_invocation_ref(idempotency_ref, payload_fingerprint_ref)
        request_with_idempotency = request.model_copy(update={"idempotency_ref": idempotency_ref})
        storage_request = request_with_idempotency.model_copy(
            update={"safe_summary": _summary_storage_ref(request.safe_summary)}
        )
        active_authority_leases = self.current_authority_leases()
        policy_decision = build_policy_decision(
            storage_request,
            invocation_ref=invocation_ref,
            status=RuntimeInvocationStatus.pending_approval,
            local_model_gateway_validated=local_model_gateway_validated,
            command_gateway_validated=command_gateway_validated,
            active_authority_leases=active_authority_leases,
            kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
        )
        record = RuntimeInvocationRecord(
            invocation_ref=invocation_ref,
            request=storage_request,
            policy_decision=policy_decision,
            approval_requirement=policy_decision.approval_requirement.model_copy(
                update={
                    "action_inbox_envelope_required": (
                        action_inbox_envelope_required
                    )
                }
            ),
            payload_fingerprint_ref=payload_fingerprint_ref,
            idempotency_ref=idempotency_ref,
            adapter_dispatch_protocol_ref=adapter_dispatch_protocol_ref,
            safe_disable=(
                operator_safe_disable
                if operator_safe_disable.active
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
                if operator_safe_disable.active
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

    def mark_adapter_dispatch_started(
        self,
        invocation_ref: str,
        *,
        protocol_ref: str,
        idempotency_ref: str,
        command_gateway_validated: bool | None = None,
        action_inbox_envelope_ref: str | None = None,
        action_inbox_approval_ref: str | None = None,
    ) -> RuntimeAdapterDispatchClaim:
        """Durably cross the exact adapter-attempt boundary once."""

        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(protocol_ref, "protocol_ref")
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            payload_fingerprint_ref = _hash_ref(
                "runtime-operation-fingerprint-ref",
                {
                    "operation": "adapter_dispatch_started",
                    "invocation_ref": invocation_ref,
                    "protocol_ref": protocol_ref,
                },
            )
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return RuntimeAdapterDispatchClaim(
                    record=replayed,
                    acquired=False,
                )
            if (
                record.adapter_dispatch_protocol_ref != protocol_ref
                or record.adapter_dispatch_started
                or record.receipt is not None
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_ADAPTER_DISPATCH_STATE_INVALID"
                )
            if command_gateway_validated is not None:
                current_policy = build_policy_decision(
                    record.request,
                    invocation_ref=record.invocation_ref,
                    approval_ref=record.approval_requirement.approval_ref,
                    status=RuntimeInvocationStatus(record.status),
                    command_gateway_validated=command_gateway_validated,
                    active_authority_leases=self.current_authority_leases(),
                    kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
                )
                if (
                    self._canonical_safe_disable_state.active
                    or not current_policy.allowed_to_execute
                ):
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_COMMAND_DISPATCH_AUTHORITY_REVOKED"
                    )
                if (
                    command_gateway_validated
                    and record.approval_requirement.action_inbox_envelope_required
                ):
                    envelope = record.action_inbox_envelope
                    if envelope is None:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_COMMAND_DISPATCH_APPROVAL_REVOKED"
                        )
                    effective_envelope_ref = (
                        action_inbox_envelope_ref
                        or envelope.action_envelope_ref
                    )
                    effective_approval_ref = (
                        action_inbox_approval_ref or envelope.approval_ref
                    )
                    validate_execution_ref(
                        effective_envelope_ref,
                        "action_inbox_envelope_ref",
                    )
                    validate_execution_ref(
                        effective_approval_ref,
                        "action_inbox_approval_ref",
                    )
                    if (
                        envelope.action_envelope_ref
                        != effective_envelope_ref
                        or envelope.approval_ref != effective_approval_ref
                        or envelope.decision
                        != RuntimeActionInboxApprovalDecision.approve.value
                        or envelope.status
                        != RuntimeInvocationStatus.approved_pending_execution.value
                        or record.status
                        != RuntimeInvocationStatus.approved_pending_execution.value
                        or not envelope.approval_validated
                        or not envelope.authority_scope_allowed
                        or envelope.safe_disable_active
                        or envelope.scope_mismatch
                        or envelope.runtime_profile_weaker_or_disabled
                        or envelope.expires_at <= utc_now()
                    ):
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_COMMAND_DISPATCH_APPROVAL_REVOKED"
                        )
            updated = record.model_copy(
                update={
                    "adapter_dispatch_started": True,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "adapter_dispatch_started",
                updated,
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return RuntimeAdapterDispatchClaim(
                record=updated,
                acquired=True,
            )

    def prepare_adapter_dispatch_protocol(
        self,
        invocation_ref: str,
        *,
        protocol_ref: str,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord:
        """Bind an undispatched prepared invocation to the boundary protocol."""

        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(protocol_ref, "protocol_ref")
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            payload_fingerprint_ref = _hash_ref(
                "runtime-operation-fingerprint-ref",
                {
                    "operation": "adapter_dispatch_protocol_prepared",
                    "invocation_ref": invocation_ref,
                    "protocol_ref": protocol_ref,
                },
            )
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return replayed
            if record.adapter_dispatch_protocol_ref == protocol_ref:
                return record
            if (
                record.adapter_dispatch_protocol_ref is not None
                or record.adapter_dispatch_started
                or record.receipt is not None
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_ADAPTER_DISPATCH_PROTOCOL_MISMATCH"
                )
            updated = record.model_copy(
                update={
                    "adapter_dispatch_protocol_ref": protocol_ref,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "adapter_dispatch_protocol_prepared",
                updated,
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return updated

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
                active_authority_leases = self.current_authority_leases()
                envelope, status, _command_gateway_validated, policy_decision = (
                    _action_inbox_envelope_for_request(
                        record=record,
                        request=request,
                        idempotency_ref=idempotency_ref,
                        active_authority_leases=active_authority_leases,
                        kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
                    )
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
                            if policy_decision.command_execution_enabled
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
            active_authority_leases = self.current_authority_leases()
            policy_decision = build_policy_decision(
                record.request,
                invocation_ref=record.invocation_ref,
                approval_ref=request.approval_ref,
                status=RuntimeInvocationStatus.pending_approval,
                active_authority_leases=active_authority_leases,
                kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
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
                safe_summary=(
                    "Runtime execution remains blocked until an active "
                    "AuthorityLease capability and approval binding allow the "
                    "requested adapter; operator summary omitted."
                ),
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

    def refresh_policy_decision_for_execution(
        self,
        invocation_ref: str,
        *,
        idempotency_ref: str,
    ) -> RuntimeInvocationRecord:
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            active_authority_leases = self.current_authority_leases()
            active_lease_refs = [
                lease.lease_ref for lease in active_authority_leases if lease.is_active()
            ]
            payload_fingerprint_ref = _hash_ref(
                "runtime-operation-fingerprint-ref",
                {
                    "operation": "authority_policy_refreshed_for_execution",
                    "invocation_ref": invocation_ref,
                    "previous_policy_decision_ref": (
                        record.policy_decision.policy_decision_ref
                    ),
                    "approval_ref": record.approval_requirement.approval_ref,
                    "active_lease_refs": active_lease_refs,
                },
            )
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return replayed
            envelope = record.action_inbox_envelope
            command_gateway_validated = (
                bool(envelope and envelope.approval_validated)
                and record.request.requested_authority
                == RuntimeAuthority.allowlisted_command.value
            )
            policy_decision = build_policy_decision(
                record.request,
                invocation_ref=record.invocation_ref,
                approval_ref=record.approval_requirement.approval_ref,
                status=RuntimeInvocationStatus(record.status),
                command_gateway_validated=command_gateway_validated,
                active_authority_leases=active_authority_leases,
                kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
            )
            if envelope is not None:
                policy_decision = policy_decision.model_copy(
                    update={
                        "approval_requirement": (
                            policy_decision.approval_requirement.model_copy(
                                update={
                                    "approval_validated": envelope.approval_validated,
                                    "approval_binding_recorded": True,
                                }
                            )
                        )
                    }
                )
            updated = record.model_copy(
                update={
                    "policy_decision": policy_decision,
                    "approval_requirement": policy_decision.approval_requirement,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "authority_policy_refreshed_for_execution",
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
        policy_decision: RuntimePolicyDecision | None = None,
        local_model_gateway_error_recheck: Callable[[], str | None] | None = None,
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
            if (
                local_model_gateway_error_recheck is not None
                and policy_decision is None
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_LOCAL_MODEL_ATTEMPT_POLICY_REQUIRED"
                )
            receipt_policy_decision = policy_decision or record.policy_decision
            decision_to_store = receipt_policy_decision
            status_to_store = _status_after_safe_disable(
                record,
                RuntimeInvocationStatus(receipt.invocation_status),
            )
            if local_model_gateway_error_recheck is not None:
                gateway_error = local_model_gateway_error_recheck()
                if gateway_error is not None and not isinstance(gateway_error, str):
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_LOCAL_MODEL_GATEWAY_RECHECK_INVALID"
                    )
                if gateway_error is not None:
                    validate_safe_execution_text(
                        gateway_error,
                        "gateway_error_category",
                    )
                    if status_to_store is not RuntimeInvocationStatus.safe_disabled:
                        status_to_store = RuntimeInvocationStatus.execution_blocked
                decision_to_store = build_policy_decision(
                    record.request,
                    invocation_ref=record.invocation_ref,
                    approval_ref=record.approval_requirement.approval_ref,
                    status=status_to_store,
                    local_model_gateway_validated=gateway_error is None,
                    active_authority_leases=self.current_authority_leases(),
                    kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
                ).model_copy(
                    update={
                        "approval_requirement": record.approval_requirement,
                        "invocation_status": status_to_store,
                    }
                )
                if (
                    status_to_store is not RuntimeInvocationStatus.safe_disabled
                    and not decision_to_store.allowed_to_execute
                ):
                    status_to_store = RuntimeInvocationStatus.execution_blocked
                    decision_to_store = decision_to_store.model_copy(
                        update={"invocation_status": status_to_store}
                    )
            if (
                receipt_policy_decision.policy_decision_ref
                != record.policy_decision.policy_decision_ref
                or decision_to_store.policy_decision_ref
                != record.policy_decision.policy_decision_ref
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_POLICY_DECISION_REF_MISMATCH"
                )
            receipt_to_store = receipt.model_copy(
                update={
                    "policy_decision_ref": receipt_policy_decision.policy_decision_ref,
                    "safe_disable": record.safe_disable,
                }
            )
            updated = record.model_copy(
                update={
                    "policy_decision": decision_to_store,
                    "receipt": receipt_to_store,
                    "status": status_to_store,
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

    def record_local_model_replay_without_receipt(
        self,
        invocation_ref: str,
        metadata: RuntimeLocalModelReceiptMetadata,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationStoreResult:
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            validate_execution_ref(
                payload_fingerprint_ref,
                "payload_fingerprint_ref",
            )
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return RuntimeInvocationStoreResult(record=replayed, replayed=True)
            if record.receipt is not None:
                return RuntimeInvocationStoreResult(record=record, replayed=True)
            status = _status_after_safe_disable(
                record,
                RuntimeInvocationStatus.execution_blocked,
            )
            policy_decision = build_policy_decision(
                record.request,
                invocation_ref=record.invocation_ref,
                approval_ref=record.approval_requirement.approval_ref,
                status=status,
                local_model_gateway_validated=False,
                active_authority_leases=self.current_authority_leases(),
                kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
            ).model_copy(
                update={
                    "approval_requirement": record.approval_requirement,
                    "invocation_status": status,
                }
            )
            receipt = build_local_model_receipt(
                record,
                metadata=metadata,
                execution_performed=False,
                model_call_performed=False,
                status=RuntimeInvocationStatus.execution_blocked,
            ).model_copy(
                update={
                    "policy_decision_ref": policy_decision.policy_decision_ref,
                    "safe_disable": record.safe_disable,
                }
            )
            updated = record.model_copy(
                update={
                    "policy_decision": policy_decision,
                    "receipt": receipt,
                    "status": status,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "receipt_recorded",
                updated,
                entry_idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
            )
            return RuntimeInvocationStoreResult(record=updated, replayed=False)

    def record_replay_posture(
        self,
        invocation_ref: str,
        policy_decision: RuntimePolicyDecision,
        status: RuntimeInvocationStatus,
        *,
        local_model_gateway_validated: bool,
        gateway_error_category: str | None,
        gateway_error_recheck: Callable[[], str | None],
        expected_receipt: RuntimeInvocationReceipt,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationRecord:
        with self._exclusive_mutation():
            record = self.get_invocation(invocation_ref)
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            validate_execution_ref(
                payload_fingerprint_ref,
                "payload_fingerprint_ref",
            )
            if (
                policy_decision.policy_decision_ref
                != record.policy_decision.policy_decision_ref
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_POLICY_DECISION_REF_MISMATCH"
                )
            if record.receipt is None:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_RECEIPT_REQUIRED"
                )
            if policy_decision.invocation_status != status:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_STATUS_MISMATCH"
                )
            target_status = _status_after_safe_disable(record, status)
            if target_status != status:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_CHANGED_DURING_REVALIDATION"
                )
            if record.receipt != expected_receipt:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_RECEIPT_CHANGED_DURING_REVALIDATION"
                )
            revalidated_gateway_error = gateway_error_recheck()
            if (
                (
                    revalidated_gateway_error is not None
                    and not isinstance(revalidated_gateway_error, str)
                )
                or revalidated_gateway_error != gateway_error_category
                or (
                    local_model_gateway_validated
                    and revalidated_gateway_error is not None
                )
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_GATEWAY_CHANGED_DURING_REVALIDATION"
                )
            if revalidated_gateway_error is not None:
                validate_safe_execution_text(
                    revalidated_gateway_error,
                    "gateway_error_category",
                )
            current_policy_decision = build_policy_decision(
                record.request,
                invocation_ref=record.invocation_ref,
                approval_ref=record.approval_requirement.approval_ref,
                status=status,
                local_model_gateway_validated=local_model_gateway_validated,
                active_authority_leases=self.current_authority_leases(),
                kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
            ).model_copy(
                update={
                    "approval_requirement": record.approval_requirement,
                    "invocation_status": status,
                }
            )
            expected_policy_posture = policy_decision.model_dump(
                mode="json",
                exclude={"decided_at"},
            )
            current_policy_posture = current_policy_decision.model_dump(
                mode="json",
                exclude={"decided_at"},
            )
            if expected_policy_posture != current_policy_posture:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_AUTHORITY_CHANGED_DURING_REVALIDATION"
                )
            persisted_policy_posture = record.policy_decision.model_dump(
                mode="json",
                exclude={"decided_at"},
            )
            if (
                record.status == target_status.value
                and persisted_policy_posture == expected_policy_posture
            ):
                replayed = record.model_copy(
                    update={"replay_count": record.replay_count + 1}
                )
                self._records[record.invocation_ref] = replayed
                return replayed
            prior_entry_hash_ref = next(
                (
                    entry.entry_hash_ref
                    for entry in reversed(self._entries)
                    if entry.invocation_ref == invocation_ref
                ),
                None,
            )
            if prior_entry_hash_ref is None:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_REPLAY_POSTURE_PRIOR_ENTRY_REQUIRED"
                )
            transition_idempotency_ref = _hash_ref(
                "idempotency-ref",
                {
                    "base_idempotency_ref": idempotency_ref,
                    "prior_entry_hash_ref": prior_entry_hash_ref,
                },
            )
            replayed = self._idempotent_operation_replay(
                transition_idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is not None:
                return replayed
            updated = record.model_copy(
                update={
                    "approval_requirement": policy_decision.approval_requirement,
                    "policy_decision": policy_decision,
                    "status": target_status,
                    "updated_at": utc_now(),
                }
            )
            self._append(
                "replay_posture_recorded",
                updated,
                entry_idempotency_ref=transition_idempotency_ref,
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

    def replay_idempotent_operation(
        self,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> RuntimeInvocationStoreResult | None:
        with self._exclusive_mutation():
            validate_execution_ref(idempotency_ref, "idempotency_ref")
            validate_execution_ref(payload_fingerprint_ref, "payload_fingerprint_ref")
            replayed = self._idempotent_operation_replay(
                idempotency_ref,
                payload_fingerprint_ref,
            )
            if replayed is None:
                return None
            return RuntimeInvocationStoreResult(record=replayed, replayed=True)

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
                preserve_original_result=True,
            )
            if replayed is not None and replayed.safe_disable:
                if replayed.safe_disable == self._canonical_safe_disable_state:
                    self._persist_operator_safe_disable_state(replayed.safe_disable)
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
                        active_authority_leases=self.current_authority_leases(),
                        kill_switch_engaged=self.authority_lease_kill_switch_engaged(),
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
            self._canonical_safe_disable_state = state
            self._persist_operator_safe_disable_state(state)
            return state

    def _persist_operator_safe_disable_state(
        self,
        state: RuntimeSafeDisableState,
    ) -> None:
        if not state.active:
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_INVALID"
            )
        payload = state.model_dump(mode="json")
        _validate_storage_payload(payload, "runtime_safe_disable_state")
        encoded = _canonical_json(payload).encode("utf-8")
        if len(encoded) > RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES:
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_INVALID"
            )
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_GUARD_UNAVAILABLE"
            )

        directory_fd = self._active_mutation_directory_fd()
        temporary_fd = -1
        temporary_name: str | None = None
        try:
            directory_info = os.fstat(directory_fd)
            if not stat.S_ISDIR(directory_info.st_mode):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_INVALID"
                )
            for _attempt in range(16):
                candidate = (
                    f".{RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON}."
                    f"{secrets.token_hex(12)}.tmp"
                )
                try:
                    temporary_fd = os.open(
                        candidate,
                        os.O_WRONLY
                        | os.O_CREAT
                        | os.O_EXCL
                        | os.O_NOFOLLOW
                        | getattr(os, "O_CLOEXEC", 0),
                        0o600,
                        dir_fd=directory_fd,
                    )
                    temporary_name = candidate
                    break
                except FileExistsError:
                    continue
            if temporary_fd < 0 or temporary_name is None:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_WRITE_FAILED"
                )
            written = 0
            while written < len(encoded):
                write_count = os.write(temporary_fd, encoded[written:])
                if write_count <= 0:
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_SAFE_DISABLE_STATE_WRITE_FAILED"
                    )
                written += write_count
            os.fsync(temporary_fd)
            os.close(temporary_fd)
            temporary_fd = -1
            os.replace(
                temporary_name,
                RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            temporary_name = None
            os.fsync(directory_fd)
        except RuntimeInvocationStorageError:
            raise
        except OSError as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_WRITE_FAILED"
            ) from exc
        finally:
            if temporary_fd >= 0:
                os.close(temporary_fd)
            if temporary_name is not None and directory_fd >= 0:
                try:
                    os.unlink(temporary_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass

    def _load_operator_safe_disable_state(self) -> RuntimeSafeDisableState:
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_GUARD_UNAVAILABLE"
            )
        directory_fd = -1
        state_fd = -1
        try:
            directory_fd = os.open(
                self.state_dir,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            state_fd = os.open(
                RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | os.O_NONBLOCK
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            before = os.fstat(state_fd)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_size > RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_INVALID"
                )
            encoded = bytearray()
            while len(encoded) <= RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES:
                chunk = os.read(
                    state_fd,
                    min(
                        65_536,
                        RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES
                        + 1
                        - len(encoded),
                    ),
                )
                if not chunk:
                    break
                encoded.extend(chunk)
            after = os.fstat(state_fd)
            path_after = os.stat(
                RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                len(encoded) > RUNTIME_GATEWAY_SAFE_DISABLE_STATE_MAX_BYTES
                or len(encoded) != after.st_size
                or not stat.S_ISREG(path_after.st_mode)
                or (before.st_dev, before.st_ino)
                != (after.st_dev, after.st_ino)
                or (before.st_dev, before.st_ino)
                != (path_after.st_dev, path_after.st_ino)
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
                or before.st_size != path_after.st_size
                or before.st_mtime_ns != path_after.st_mtime_ns
                or before.st_ctime_ns != path_after.st_ctime_ns
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_INVALID"
                )
            payload = json.loads(bytes(encoded).decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_INVALID"
                )
            _validate_storage_payload(payload, "runtime_safe_disable_state")
            state = RuntimeSafeDisableState.model_validate_json(
                bytes(encoded),
                strict=True,
            )
            if not state.active:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_SAFE_DISABLE_STATE_INVALID"
                )
            return state
        except RuntimeInvocationStorageError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_INVALID"
            ) from exc
        finally:
            if state_fd >= 0:
                os.close(state_fd)
            if directory_fd >= 0:
                os.close(directory_fd)

    def _safe_disable_state_path_present(self) -> bool:
        try:
            os.lstat(self._safe_disable_state_path)
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_SAFE_DISABLE_STATE_INVALID"
            ) from exc

    def _read_ledger_text(self) -> str | None:
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_GUARD_UNAVAILABLE"
            )
        directory_fd = -1
        ledger_fd = -1
        try:
            _validate_runtime_gateway_state_dir(self.state_dir, create=False)
            try:
                directory_fd = os.open(
                    self.state_dir,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                )
            except FileNotFoundError:
                return None
            try:
                expected_info = os.stat(
                    RUNTIME_GATEWAY_JSONL,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                return None
            if not stat.S_ISREG(expected_info.st_mode):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            ledger_fd = os.open(
                RUNTIME_GATEWAY_JSONL,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            opened_info = os.fstat(ledger_fd)
            if (
                not stat.S_ISREG(opened_info.st_mode)
                or not os.path.samestat(expected_info, opened_info)
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            chunks: list[bytes] = []
            while True:
                chunk = os.read(ledger_fd, 64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after_info = os.fstat(ledger_fd)
            path_after = os.stat(
                RUNTIME_GATEWAY_JSONL,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(path_after.st_mode)
                or not os.path.samestat(expected_info, after_info)
                or not os.path.samestat(expected_info, path_after)
                or expected_info.st_size != after_info.st_size
                or expected_info.st_size != path_after.st_size
                or expected_info.st_mtime_ns != after_info.st_mtime_ns
                or expected_info.st_mtime_ns != path_after.st_mtime_ns
                or expected_info.st_ctime_ns != after_info.st_ctime_ns
                or expected_info.st_ctime_ns != path_after.st_ctime_ns
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            self._loaded_ledger_identity = (
                opened_info.st_dev,
                opened_info.st_ino,
            )
            return b"".join(chunks).decode("utf-8")
        except RuntimeInvocationStorageError:
            raise
        except (OSError, UnicodeDecodeError) as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
            ) from exc
        finally:
            if ledger_fd >= 0:
                os.close(ledger_fd)
            if directory_fd >= 0:
                os.close(directory_fd)

    def _load(self) -> None:
        if self._loaded:
            return
        self._reload()

    def _reload(self) -> None:
        self._records = {}
        self._entries = []
        self._idempotency_index = {}
        self._idempotency_fingerprint_index = {}
        self._last_entry_hash_ref = None
        self._canonical_safe_disable_state = _runtime_default_safe_disable_state()
        self._loaded_ledger_identity = None
        self._loaded = False
        try:
            ledger_text = self._read_ledger_text()
            if ledger_text is None:
                if self._safe_disable_state_path_present():
                    self._load_operator_safe_disable_state()
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_SAFE_DISABLE_STATE_MISMATCH"
                    )
            else:
                previous_hash: str | None = None
                for line in ledger_text.splitlines():
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    try:
                        entry = RuntimeGatewayStorageEntry(**payload)
                    except ValidationError as exc:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_STORAGE_ENTRY_INVALID"
                        ) from exc
                    expected_hash = _entry_hash(
                        entry.model_dump(mode="json", exclude={"entry_hash_ref"})
                    )
                    if entry.entry_hash_ref != expected_hash:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_STORAGE_ENTRY_HASH_MISMATCH"
                        )
                    if entry.previous_entry_hash_ref != previous_hash:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_STORAGE_HASH_CHAIN_MISMATCH"
                        )
                    self._records[entry.invocation_ref] = entry.record
                    self._idempotency_index[entry.idempotency_ref] = (
                        entry.invocation_ref
                    )
                    self._idempotency_fingerprint_index[entry.idempotency_ref] = (
                        entry.payload_fingerprint_ref
                    )
                    self._entries.append(entry)
                    previous_hash = entry.entry_hash_ref
                derived_state = _operator_safe_disable_state(self._records.values())
                if self._safe_disable_state_path_present():
                    persisted_state = self._load_operator_safe_disable_state()
                    if derived_state is None:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_SAFE_DISABLE_STATE_MISMATCH"
                        )
                    if derived_state is not None and persisted_state != derived_state:
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_SAFE_DISABLE_STATE_MISMATCH"
                        )
                    self._canonical_safe_disable_state = persisted_state
                elif derived_state is not None:
                    self._canonical_safe_disable_state = derived_state
                self._last_entry_hash_ref = previous_hash
            self._loaded = True
        except BaseException:
            self._loaded = False
            self._canonical_safe_disable_state = (
                _runtime_default_safe_disable_state()
            )
            raise

    @contextmanager
    def _exclusive_mutation(self):
        directory_fd = -1
        lock_fd = -1
        process_lock_acquired = self._process_lock.acquire(
            timeout=RUNTIME_GATEWAY_LOCK_TIMEOUT_SECONDS
        )
        if not process_lock_acquired:
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
            )
        try:
            try:
                opened = _open_runtime_gateway_state_dir(
                    self.state_dir,
                    create=True,
                )
                if opened is None:
                    raise OSError("runtime gateway state directory missing")
                directory_fd, identity = opened
                _bind_runtime_gateway_state_dir_identity(
                    self.state_dir,
                    identity,
                )
                lock_fd = os.open(
                    RUNTIME_GATEWAY_LOCK,
                    os.O_RDWR
                    | os.O_CREAT
                    | os.O_NOFOLLOW
                    | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                    dir_fd=directory_fd,
                )
                lock_info = os.fstat(lock_fd)
                if not stat.S_ISREG(lock_info.st_mode):
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                    )
                lock_deadline = (
                    time.monotonic() + RUNTIME_GATEWAY_LOCK_TIMEOUT_SECONDS
                )
                while True:
                    try:
                        fcntl.flock(
                            lock_fd,
                            fcntl.LOCK_EX | fcntl.LOCK_NB,
                        )
                        break
                    except BlockingIOError as exc:
                        if time.monotonic() >= lock_deadline:
                            raise RuntimeInvocationStorageError(
                                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                            ) from exc
                        time.sleep(RUNTIME_GATEWAY_LOCK_POLL_SECONDS)
                self._mutation_directory_fds.append(directory_fd)
                try:
                    self._reload()
                    yield
                except BaseException:
                    self._loaded = False
                    raise
                finally:
                    active_directory_fd = self._mutation_directory_fds.pop()
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    if active_directory_fd != directory_fd:
                        self._loaded = False
                        raise RuntimeInvocationStorageError(
                            "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                        )
            except RuntimeInvocationStorageError:
                raise
            except OSError as exc:
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                ) from exc
            finally:
                if lock_fd >= 0:
                    os.close(lock_fd)
                if directory_fd >= 0:
                    os.close(directory_fd)
        finally:
            self._process_lock.release()

    def _active_mutation_directory_fd(self) -> int:
        if not self._mutation_directory_fds:
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
            )
        directory_fd = self._mutation_directory_fds[-1]
        try:
            directory_info = os.fstat(directory_fd)
        except OSError as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
            ) from exc
        if not stat.S_ISDIR(directory_info.st_mode):
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
            )
        return directory_fd

    def _idempotent_operation_replay(
        self,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
        *,
        preserve_original_result: bool = False,
    ) -> RuntimeInvocationRecord | None:
        existing_ref = self._idempotency_index.get(idempotency_ref)
        if existing_ref is None:
            return None
        existing_fingerprint = self._idempotency_fingerprint_index.get(idempotency_ref)
        if existing_fingerprint != payload_fingerprint_ref:
            raise RuntimeInvocationConflictError("RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT")
        existing = self._records[existing_ref]
        if preserve_original_result:
            existing = next(
                entry.record
                for entry in self._entries
                if entry.idempotency_ref == idempotency_ref
            )
        replayed = existing.model_copy(update={"replay_count": existing.replay_count + 1})
        if not preserve_original_result:
            self._records[existing_ref] = replayed
        return replayed

    def _append_ledger_line(self, encoded_line: bytes) -> None:
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_GUARD_UNAVAILABLE"
            )
        directory_fd = self._active_mutation_directory_fd()
        ledger_fd = -1
        created = False
        try:
            open_flags = (
                os.O_WRONLY
                | os.O_APPEND
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0)
            )
            try:
                ledger_fd = os.open(
                    RUNTIME_GATEWAY_JSONL,
                    open_flags,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                if self._loaded_ledger_identity is not None:
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                    )
                try:
                    ledger_fd = os.open(
                        RUNTIME_GATEWAY_JSONL,
                        open_flags | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=directory_fd,
                    )
                    created = True
                except FileExistsError:
                    ledger_fd = os.open(
                        RUNTIME_GATEWAY_JSONL,
                        open_flags,
                        dir_fd=directory_fd,
                    )
            ledger_info = os.fstat(ledger_fd)
            ledger_identity = (ledger_info.st_dev, ledger_info.st_ino)
            if (
                not stat.S_ISREG(ledger_info.st_mode)
                or (
                    self._loaded_ledger_identity is None
                    and not created
                )
                or (
                    self._loaded_ledger_identity is not None
                    and ledger_identity != self._loaded_ledger_identity
                )
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            written = 0
            while written < len(encoded_line):
                write_count = os.write(ledger_fd, encoded_line[written:])
                if write_count <= 0:
                    raise RuntimeInvocationStorageError(
                        "RUNTIME_STORAGE_LEDGER_WRITE_FAILED"
                    )
                written += write_count
            os.fsync(ledger_fd)
            path_after = os.stat(
                RUNTIME_GATEWAY_JSONL,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(path_after.st_mode)
                or not os.path.samestat(ledger_info, path_after)
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            os.fsync(directory_fd)
            durable_path = os.stat(
                RUNTIME_GATEWAY_JSONL,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(durable_path.st_mode)
                or not os.path.samestat(ledger_info, durable_path)
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_STORAGE_LEDGER_PATH_INVALID"
                )
            self._loaded_ledger_identity = ledger_identity
        except RuntimeInvocationStorageError:
            raise
        except OSError as exc:
            raise RuntimeInvocationStorageError(
                "RUNTIME_STORAGE_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            if ledger_fd >= 0:
                os.close(ledger_fd)

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
        encoded_line = (
            _canonical_json(entry.model_dump(mode="json")) + "\n"
        ).encode("utf-8")
        self._append_ledger_line(encoded_line)
        self._records[record.invocation_ref] = record
        self._entries.append(entry)
        self._idempotency_index[entry_idempotency_ref] = record.invocation_ref
        self._idempotency_fingerprint_index[entry_idempotency_ref] = payload_fingerprint_ref
        self._last_entry_hash_ref = entry.entry_hash_ref
