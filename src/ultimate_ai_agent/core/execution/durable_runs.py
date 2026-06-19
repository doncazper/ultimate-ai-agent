import hashlib
import json
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    raw_input_reasons,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
    validation_reason,
)

DURABLE_RUN_SCHEMA_VERSION = "durable_run.v1"
UNSAFE_DURABLE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw response",
    "provider payload",
    "raw path",
    "raw log",
    "environment dump",
    "credential material",
)


class DurableRunError(ValueError):
    """Base error for durable run contract validation failures."""


class DurableRunCorruptionError(DurableRunError):
    """Raised when a durable run snapshot fails integrity checks."""


class DurableRunState(str, Enum):
    created = "created"
    ready = "ready"
    running = "running"
    paused = "paused"
    blocked = "blocked"
    retry_pending = "retry_pending"
    restart_recovery = "restart_recovery"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    dead_lettered = "dead_lettered"


class DurableRunTransitionKind(str, Enum):
    mark_ready = "mark_ready"
    start = "start"
    pause = "pause"
    resume = "resume"
    cancel = "cancel"
    succeed = "succeed"
    fail = "fail"
    block = "block"
    retry = "retry"
    dead_letter = "dead_letter"
    recover_after_restart = "recover_after_restart"


class DurableRunTransitionStatus(str, Enum):
    accepted = "accepted"
    denied = "denied"


TERMINAL_DURABLE_RUN_STATES = {
    DurableRunState.succeeded,
    DurableRunState.cancelled,
    DurableRunState.dead_lettered,
}

ALLOWED_DURABLE_RUN_TRANSITIONS: dict[DurableRunState, set[DurableRunState]] = {
    DurableRunState.created: {
        DurableRunState.ready,
        DurableRunState.failed,
        DurableRunState.cancelled,
    },
    DurableRunState.ready: {
        DurableRunState.running,
        DurableRunState.failed,
        DurableRunState.cancelled,
    },
    DurableRunState.running: {
        DurableRunState.paused,
        DurableRunState.blocked,
        DurableRunState.restart_recovery,
        DurableRunState.succeeded,
        DurableRunState.failed,
        DurableRunState.cancelled,
    },
    DurableRunState.paused: {
        DurableRunState.running,
        DurableRunState.failed,
        DurableRunState.cancelled,
    },
    DurableRunState.blocked: {
        DurableRunState.retry_pending,
        DurableRunState.failed,
        DurableRunState.cancelled,
        DurableRunState.dead_lettered,
    },
    DurableRunState.retry_pending: {
        DurableRunState.running,
        DurableRunState.cancelled,
        DurableRunState.dead_lettered,
    },
    DurableRunState.restart_recovery: {
        DurableRunState.running,
        DurableRunState.failed,
        DurableRunState.cancelled,
        DurableRunState.dead_lettered,
    },
    DurableRunState.failed: {
        DurableRunState.retry_pending,
        DurableRunState.cancelled,
        DurableRunState.dead_lettered,
    },
    DurableRunState.succeeded: set(),
    DurableRunState.cancelled: set(),
    DurableRunState.dead_lettered: set(),
}

TRANSITION_TARGETS: dict[DurableRunTransitionKind, DurableRunState] = {
    DurableRunTransitionKind.mark_ready: DurableRunState.ready,
    DurableRunTransitionKind.start: DurableRunState.running,
    DurableRunTransitionKind.pause: DurableRunState.paused,
    DurableRunTransitionKind.resume: DurableRunState.running,
    DurableRunTransitionKind.cancel: DurableRunState.cancelled,
    DurableRunTransitionKind.succeed: DurableRunState.succeeded,
    DurableRunTransitionKind.fail: DurableRunState.failed,
    DurableRunTransitionKind.block: DurableRunState.blocked,
    DurableRunTransitionKind.retry: DurableRunState.retry_pending,
    DurableRunTransitionKind.dead_letter: DurableRunState.dead_lettered,
    DurableRunTransitionKind.recover_after_restart: DurableRunState.restart_recovery,
}


def _validate_durable_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_DURABLE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe durable evidence language")


def _validate_durable_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_durable_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_durable_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_durable_payload(str(key), field_name)
            _validate_durable_payload(item, field_name)


class DurableRunPersistenceModel(BaseModel):
    storage_contract: str = "append_first_local_snapshot_contract"
    schema_version: str = DURABLE_RUN_SCHEMA_VERSION
    corruption_detection: str = "schema_version_and_sha256_snapshot"
    append_only_ledger_required: bool = True
    atomic_write_required: bool = True
    offline_restore_required: bool = True
    raw_payload_storage_allowed: bool = False
    production_runtime_authority: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_persistence_model(self):
        if self.raw_payload_storage_allowed:
            raise ValueError("DURABLE_RUN_RAW_PAYLOAD_STORAGE_DENIED")
        if self.production_runtime_authority:
            raise ValueError("DURABLE_RUN_PRODUCTION_AUTHORITY_DENIED")
        if not self.append_only_ledger_required:
            raise ValueError("DURABLE_RUN_APPEND_ONLY_LEDGER_REQUIRED")
        if not self.atomic_write_required:
            raise ValueError("DURABLE_RUN_ATOMIC_WRITE_REQUIRED")
        if not self.offline_restore_required:
            raise ValueError("DURABLE_RUN_OFFLINE_RESTORE_REQUIRED")
        _validate_durable_text(self.storage_contract, "storage_contract")
        _validate_durable_text(self.schema_version, "schema_version")
        _validate_durable_text(self.corruption_detection, "corruption_detection")
        return self


class DurableRunRecord(BaseModel):
    run_id: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    state: DurableRunState = DurableRunState.created
    schema_version: str = DURABLE_RUN_SCHEMA_VERSION
    generation: int = Field(default=0, ge=0)
    safe_summary: str = Field(..., min_length=1)
    transition_ids_seen: List[str] = Field(default_factory=list)
    idempotency_keys_seen: List[str] = Field(default_factory=list)
    audit_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    replay_refs: List[str] = Field(default_factory=list)
    rollback_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    failure_refs: List[str] = Field(default_factory=list)
    restart_refs: List[str] = Field(default_factory=list)
    persistence_model: DurableRunPersistenceModel = Field(default_factory=DurableRunPersistenceModel)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self):
        validate_execution_ref(self.run_id, "run_id")
        validate_execution_ref(self.source_ref, "source_ref")
        _validate_durable_text(self.schema_version, "schema_version")
        _validate_durable_text(self.safe_summary, "safe_summary")
        for ref in [
            *self.transition_ids_seen,
            *self.idempotency_keys_seen,
            *self.audit_refs,
            *self.receipt_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.evidence_refs,
            *self.failure_refs,
            *self.restart_refs,
            *self.metadata_refs,
        ]:
            validate_execution_ref(ref, "durable_run_ref")
        validate_safe_execution_payload(self.metadata, "metadata")
        _validate_durable_payload(self.metadata, "metadata")
        if self.schema_version != DURABLE_RUN_SCHEMA_VERSION:
            raise ValueError("DURABLE_RUN_SCHEMA_VERSION_UNSUPPORTED")
        return self


class DurableRunTransitionRequest(BaseModel):
    run_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    transition_kind: DurableRunTransitionKind
    idempotency_key: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    failure_ref: str | None = None
    restart_ref: str | None = None
    execution_requested: bool = False
    auto_run_requested: bool = False
    schedule_requested: bool = False
    background_worker_requested: bool = False
    side_effect_execution_enabled: bool = False
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    contains_secret_like_content: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self):
        for value, field_name in [
            (self.run_id, "run_id"),
            (self.transition_id, "transition_id"),
            (self.idempotency_key, "idempotency_key"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.replay_ref, "replay_ref"),
            (self.rollback_ref, "rollback_ref"),
        ]:
            validate_execution_ref(value, field_name)
        _validate_durable_text(self.safe_summary, "safe_summary")
        for ref in [*self.evidence_refs, *self.metadata_refs]:
            validate_execution_ref(ref, "durable_run_request_ref")
        if self.failure_ref:
            validate_execution_ref(self.failure_ref, "failure_ref")
        if self.restart_ref:
            validate_execution_ref(self.restart_ref, "restart_ref")
        for reason in raw_input_reasons(self):
            raise ValueError(reason)
        validate_safe_execution_payload(self.metadata, "metadata")
        _validate_durable_payload(self.metadata, "metadata")
        return self


class DurableRunTransitionDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    status: DurableRunTransitionStatus
    transition_kind: DurableRunTransitionKind
    previous_state: DurableRunState
    next_state: DurableRunState
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    audit_ref: str | None = None
    receipt_ref: str | None = None
    replay_ref: str | None = None
    rollback_ref: str | None = None
    execution_authorized: bool = False
    execution_performed: bool = False
    side_effects_performed: List[str] = Field(default_factory=list)
    no_task_execution_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_file_mutation_performed: bool = True
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    no_scheduler_registered: bool = True
    no_background_worker_registered: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self):
        if self.execution_authorized:
            raise ValueError("DURABLE_RUN_EXECUTION_AUTHORITY_DENIED")
        if self.execution_performed:
            raise ValueError("DURABLE_RUN_EXECUTION_PERFORMED_DENIED")
        if self.side_effects_performed:
            raise ValueError("DURABLE_RUN_SIDE_EFFECTS_DENIED")
        for field_name in [
            "no_task_execution_performed",
            "no_tool_execution_performed",
            "no_action_execution_performed",
            "no_memory_write_performed",
            "no_file_mutation_performed",
            "no_network_call_performed",
            "no_model_call_performed",
            "no_scheduler_registered",
            "no_background_worker_registered",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"DURABLE_RUN_INVARIANT_FAILED:{field_name}")
        validate_execution_ref(self.decision_id, "decision_id")
        validate_execution_ref(self.run_id, "run_id")
        _validate_durable_text(self.safe_message, "safe_message")
        for ref in [self.audit_ref, self.receipt_ref, self.replay_ref, self.rollback_ref]:
            if ref:
                validate_execution_ref(ref, "decision_ref")
        return self


class DurableRunTransitionResult(BaseModel):
    record: DurableRunRecord
    decision: DurableRunTransitionDecision

    model_config = ConfigDict(extra="forbid")


class DurableRunSnapshot(BaseModel):
    schema_version: str = DURABLE_RUN_SCHEMA_VERSION
    record: DurableRunRecord
    snapshot_hash_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_snapshot(self):
        _validate_durable_text(self.schema_version, "schema_version")
        validate_execution_ref(self.snapshot_hash_ref, "snapshot_hash_ref")
        if self.schema_version != DURABLE_RUN_SCHEMA_VERSION:
            raise ValueError("DURABLE_RUN_SNAPSHOT_SCHEMA_VERSION_UNSUPPORTED")
        return self


def _target_state(kind: DurableRunTransitionKind) -> DurableRunState:
    return TRANSITION_TARGETS[kind]


def _decision_id(transition_id: str) -> str:
    suffix = transition_id.split(":", 1)[-1]
    return f"durable-run-decision:{suffix}"


def _revalidate_record(record: DurableRunRecord) -> list[str]:
    try:
        DurableRunRecord.model_validate(record.model_dump())
    except (ValidationError, ValueError) as exc:
        return validation_reason(exc, fallback="DURABLE_RUN_RECORD_REVALIDATION_FAILED")
    return []


def _revalidate_request(request: DurableRunTransitionRequest) -> list[str]:
    reasons: list[str] = []
    try:
        DurableRunTransitionRequest.model_validate(request.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(validation_reason(exc, fallback="DURABLE_RUN_REQUEST_REVALIDATION_FAILED"))
    if request.execution_requested:
        reasons.append("DURABLE_RUN_EXECUTION_REQUEST_DENIED")
    if request.auto_run_requested:
        reasons.append("DURABLE_RUN_AUTO_RUN_DENIED")
    if request.schedule_requested:
        reasons.append("DURABLE_RUN_SCHEDULE_DENIED")
    if request.background_worker_requested:
        reasons.append("DURABLE_RUN_BACKGROUND_WORKER_DENIED")
    if request.side_effect_execution_enabled:
        reasons.append("DURABLE_RUN_SIDE_EFFECT_EXECUTION_DENIED")
    return reasons


def evaluate_durable_run_transition(
    record: DurableRunRecord,
    request: DurableRunTransitionRequest,
) -> DurableRunTransitionDecision:
    reasons: list[str] = []
    reasons.extend(_revalidate_record(record))
    reasons.extend(_revalidate_request(request))

    next_state = _target_state(request.transition_kind)
    if request.run_id != record.run_id:
        reasons.append("DURABLE_RUN_REF_MISMATCH_DENIED")
    if request.transition_id in record.transition_ids_seen:
        reasons.append("DURABLE_RUN_TRANSITION_REPLAY_DENIED")
    if request.idempotency_key in record.idempotency_keys_seen:
        reasons.append("DURABLE_RUN_IDEMPOTENCY_REPLAY_DENIED")
    if request.replay_ref in record.replay_refs:
        reasons.append("DURABLE_RUN_REPLAY_REF_REUSE_DENIED")
    if record.state in TERMINAL_DURABLE_RUN_STATES:
        reasons.append("DURABLE_RUN_TERMINAL_STATE_DENIED")
    if next_state not in ALLOWED_DURABLE_RUN_TRANSITIONS.get(record.state, set()):
        reasons.append("DURABLE_RUN_INVALID_TRANSITION_DENIED")
    if request.transition_kind == DurableRunTransitionKind.fail and not request.failure_ref:
        reasons.append("DURABLE_RUN_FAILURE_REF_REQUIRED")
    if request.transition_kind == DurableRunTransitionKind.recover_after_restart and not request.restart_ref:
        reasons.append("DURABLE_RUN_RESTART_REF_REQUIRED")

    reasons = dedupe_reasons(reasons)
    if reasons:
        return DurableRunTransitionDecision(
            decision_id=_decision_id(request.transition_id),
            run_id=record.run_id,
            status=DurableRunTransitionStatus.denied,
            transition_kind=request.transition_kind,
            previous_state=record.state,
            next_state=record.state,
            reason_codes=reasons,
            safe_message="Durable run transition denied by contract policy.",
            audit_ref=request.audit_ref,
            receipt_ref=request.receipt_ref,
            replay_ref=request.replay_ref,
            rollback_ref=request.rollback_ref,
        )

    return DurableRunTransitionDecision(
        decision_id=_decision_id(request.transition_id),
        run_id=record.run_id,
        status=DurableRunTransitionStatus.accepted,
        transition_kind=request.transition_kind,
        previous_state=record.state,
        next_state=next_state,
        reason_codes=["DURABLE_RUN_TRANSITION_ACCEPTED"],
        safe_message="Durable run transition accepted as state-only contract mutation.",
        audit_ref=request.audit_ref,
        receipt_ref=request.receipt_ref,
        replay_ref=request.replay_ref,
        rollback_ref=request.rollback_ref,
    )


def _append_unique(existing: list[str], *refs: str | None) -> list[str]:
    updated = list(existing)
    for ref in refs:
        if ref and ref not in updated:
            updated.append(ref)
    return updated


def apply_durable_run_transition(
    record: DurableRunRecord,
    request: DurableRunTransitionRequest,
) -> DurableRunTransitionResult:
    decision = evaluate_durable_run_transition(record, request)
    if decision.status != DurableRunTransitionStatus.accepted:
        return DurableRunTransitionResult(record=record, decision=decision)

    next_record = record.model_copy(
        update={
            "state": decision.next_state,
            "generation": record.generation + 1,
            "transition_ids_seen": _append_unique(record.transition_ids_seen, request.transition_id),
            "idempotency_keys_seen": _append_unique(record.idempotency_keys_seen, request.idempotency_key),
            "audit_refs": _append_unique(record.audit_refs, request.audit_ref),
            "receipt_refs": _append_unique(record.receipt_refs, request.receipt_ref),
            "replay_refs": _append_unique(record.replay_refs, request.replay_ref),
            "rollback_refs": _append_unique(record.rollback_refs, request.rollback_ref),
            "evidence_refs": _append_unique(record.evidence_refs, *request.evidence_refs),
            "failure_refs": _append_unique(record.failure_refs, request.failure_ref),
            "restart_refs": _append_unique(record.restart_refs, request.restart_ref),
            "metadata_refs": _append_unique(record.metadata_refs, *request.metadata_refs),
        }
    )
    next_record = DurableRunRecord.model_validate(next_record.model_dump())
    return DurableRunTransitionResult(record=next_record, decision=decision)


def _record_hash_ref(record: DurableRunRecord) -> str:
    payload = json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def build_durable_run_snapshot(record: DurableRunRecord) -> DurableRunSnapshot:
    validated = DurableRunRecord.model_validate(record.model_dump())
    return DurableRunSnapshot(record=validated, snapshot_hash_ref=_record_hash_ref(validated))


def restore_durable_run_snapshot(snapshot: DurableRunSnapshot | dict[str, Any]) -> DurableRunRecord:
    validated = DurableRunSnapshot.model_validate(snapshot)
    expected_hash = _record_hash_ref(validated.record)
    if validated.snapshot_hash_ref != expected_hash:
        raise DurableRunCorruptionError("DURABLE_RUN_SNAPSHOT_HASH_MISMATCH")
    return validated.record
