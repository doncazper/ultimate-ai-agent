from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.durable_runs import (
    DurableRunRecord,
    DurableRunState,
    restore_durable_run_snapshot,
)
from ultimate_ai_agent.core.execution.run_storage import (
    AppendFirstRunStorage,
    DurableRunStorageEntry,
    DurableRunStorageEntryKind,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


DURABLE_RUN_LIFECYCLE_READ_MODEL_SCHEMA_VERSION = "durable_run_lifecycle_read_model.v1"
DURABLE_RUN_LIFECYCLE_EVENT_READ_MODEL_SCHEMA_VERSION = "durable_run_lifecycle_event_read_model.v1"

CanonicalRunLifecycleState = Literal[
    "created",
    "queued",
    "waiting_for_approval",
    "ready",
    "running",
    "paused",
    "cancel_requested",
    "canceled",
    "failed",
    "succeeded",
    "expired",
    "blocked",
    "replaying",
]

CanonicalRunEventType = Literal[
    "run_created",
    "run_queued",
    "approval_required",
    "approval_attached",
    "approval_denied",
    "step_started",
    "step_progress",
    "step_blocked",
    "step_completed",
    "receipt_recorded",
    "evidence_ref_attached",
    "cost_posture_recorded",
    "redaction_applied",
    "pause_requested",
    "resume_requested",
    "cancel_requested",
    "run_canceled",
    "run_failed",
    "run_succeeded",
    "run_expired",
    "replay_started",
    "replay_event_emitted",
    "replay_completed",
]

CANONICAL_RUN_LIFECYCLE_STATES: tuple[CanonicalRunLifecycleState, ...] = (
    "created",
    "queued",
    "waiting_for_approval",
    "ready",
    "running",
    "paused",
    "cancel_requested",
    "canceled",
    "failed",
    "succeeded",
    "expired",
    "blocked",
    "replaying",
)

CANONICAL_RUN_EVENT_TYPES: tuple[CanonicalRunEventType, ...] = (
    "run_created",
    "run_queued",
    "approval_required",
    "approval_attached",
    "approval_denied",
    "step_started",
    "step_progress",
    "step_blocked",
    "step_completed",
    "receipt_recorded",
    "evidence_ref_attached",
    "cost_posture_recorded",
    "redaction_applied",
    "pause_requested",
    "resume_requested",
    "cancel_requested",
    "run_canceled",
    "run_failed",
    "run_succeeded",
    "run_expired",
    "replay_started",
    "replay_event_emitted",
    "replay_completed",
)


_STATE_MAP: dict[DurableRunState, CanonicalRunLifecycleState] = {
    DurableRunState.created: "created",
    DurableRunState.ready: "ready",
    DurableRunState.running: "running",
    DurableRunState.paused: "paused",
    DurableRunState.blocked: "blocked",
    DurableRunState.retry_pending: "queued",
    DurableRunState.restart_recovery: "blocked",
    DurableRunState.succeeded: "succeeded",
    DurableRunState.failed: "failed",
    DurableRunState.cancelled: "canceled",
    DurableRunState.dead_lettered: "failed",
}


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _canonical_state(state: DurableRunState) -> CanonicalRunLifecycleState:
    return _STATE_MAP[state]


def _safe_metadata_refs(record: DurableRunRecord, key: str) -> list[str]:
    values = record.metadata.get(key, [])
    if not isinstance(values, list):
        return []
    safe_values: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        validate_execution_ref(value, key)
        safe_values.append(value)
    return safe_values


def _record_from_entry(entry: DurableRunStorageEntry) -> DurableRunRecord | None:
    if entry.kind != DurableRunStorageEntryKind.run_record or entry.record_snapshot is None:
        return None
    return restore_durable_run_snapshot(entry.record_snapshot)


def _event_type_for_entry(entry: DurableRunStorageEntry, sequence: int) -> CanonicalRunEventType:
    if entry.kind == DurableRunStorageEntryKind.receipt:
        return "receipt_recorded"
    record = _record_from_entry(entry)
    if record is None:
        return "step_progress"
    if sequence == 1 and record.state == DurableRunState.created:
        return "run_created"
    if record.state == DurableRunState.ready:
        return "run_queued"
    if record.state == DurableRunState.running:
        return "step_started"
    if record.state == DurableRunState.paused:
        return "pause_requested"
    if record.state == DurableRunState.blocked:
        return "step_blocked"
    if record.state == DurableRunState.retry_pending:
        return "step_progress"
    if record.state == DurableRunState.restart_recovery:
        return "step_progress"
    if record.state == DurableRunState.succeeded:
        return "run_succeeded"
    if record.state == DurableRunState.failed:
        return "run_failed"
    if record.state == DurableRunState.cancelled:
        return "run_canceled"
    if record.state == DurableRunState.dead_lettered:
        return "run_failed"
    return "step_progress"


class DurableRunLifecycleEventReadModel(BaseModel):
    schema_version: str = DURABLE_RUN_LIFECYCLE_EVENT_READ_MODEL_SCHEMA_VERSION
    run_id: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=1)
    event_type: CanonicalRunEventType
    storage_entry_kind: str = Field(..., min_length=1)
    storage_entry_ref: str = Field(..., min_length=1)
    status_after: CanonicalRunLifecycleState | None = None
    generation_after: int | None = Field(default=None, ge=0)
    idempotency_key_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    entry_hash_ref: str = Field(..., min_length=1)
    previous_entry_hash_ref: str | None = None
    receipt_hash_ref: str | None = None
    replay_validation_ref: str | None = None
    safe_summary: str = Field(..., min_length=1)
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        for value, field_name in [
            (self.run_id, "run_id"),
            (self.storage_entry_ref, "storage_entry_ref"),
            (self.idempotency_key_ref, "idempotency_key_ref"),
            (self.audit_ref, "audit_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.entry_hash_ref, "entry_hash_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.previous_entry_hash_ref:
            validate_execution_ref(self.previous_entry_hash_ref, "previous_entry_hash_ref")
        if self.receipt_hash_ref:
            validate_execution_ref(self.receipt_hash_ref, "receipt_hash_ref")
        if self.replay_validation_ref:
            validate_execution_ref(self.replay_validation_ref, "replay_validation_ref")
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.storage_entry_kind, "storage_entry_kind")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.safe_refs_only:
            raise ValueError("DURABLE_RUN_LIFECYCLE_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("DURABLE_RUN_LIFECYCLE_RAW_PAYLOADS_DENIED")
        if self.execution_performed:
            raise ValueError("DURABLE_RUN_LIFECYCLE_EXECUTION_DENIED")
        return self


class DurableRunLifecycleReadModel(BaseModel):
    schema_version: str = DURABLE_RUN_LIFECYCLE_READ_MODEL_SCHEMA_VERSION
    run_id: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    parent_run_ref: str | None = None
    child_run_refs: list[str] = Field(default_factory=list)
    origin_surface: str = "task_decomposition"
    status: CanonicalRunLifecycleState
    source_status: str = Field(..., min_length=1)
    generation: int = Field(..., ge=0)
    source_ref: str = Field(..., min_length=1)
    intent_safe_summary_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    approval_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    cost_posture_refs: list[str] = Field(default_factory=list)
    redaction_posture_ref: str = "redaction-posture:durable-run:safe-refs-only"
    authority_boundary_refs: list[str] = Field(
        default_factory=lambda: ["authority-boundary:durable-run-state-only"]
    )
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    failure_refs: list[str] = Field(default_factory=list)
    restart_refs: list[str] = Field(default_factory=list)
    idempotency_key_refs_seen: list[str] = Field(default_factory=list)
    receipt_hash_refs: list[str] = Field(default_factory=list)
    replay_validation_refs: list[str] = Field(default_factory=list)
    event_count: int = Field(..., ge=0)
    run_record_event_count: int = Field(..., ge=0)
    receipt_event_count: int = Field(..., ge=0)
    events: list[DurableRunLifecycleEventReadModel] = Field(default_factory=list)
    canonical_states: list[CanonicalRunLifecycleState] = Field(
        default_factory=lambda: list(CANONICAL_RUN_LIFECYCLE_STATES)
    )
    canonical_event_types: list[CanonicalRunEventType] = Field(default_factory=lambda: list(CANONICAL_RUN_EVENT_TYPES))
    append_only_event_log: bool = True
    deterministic_event_ordering: str = "run_ref_sequence"
    idempotent_append_enforced: bool = True
    hash_chain_verified_on_load: bool = True
    timestamps_recorded: bool = False
    timestamp_recording_status: str = "planned_storage_extension"
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    receipt_summaries_included: bool = False
    approval_refs_are_identifiers_only: bool = True
    execution_authority_enabled: bool = False
    execution_performed: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    provider_model_calls_enabled: bool = False
    tool_execution_expansion_enabled: bool = False
    connector_writes_enabled: bool = False
    streaming_runtime_enabled: bool = False
    cancel_resume_controls_status: str = "planned_blocked_no_execution_authority"
    api_mutation_routes_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        for value, field_name in [
            (self.run_id, "run_id"),
            (self.run_ref, "run_ref"),
            (self.source_ref, "source_ref"),
            (self.intent_safe_summary_ref, "intent_safe_summary_ref"),
            (self.redaction_posture_ref, "redaction_posture_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.parent_run_ref:
            validate_execution_ref(self.parent_run_ref, "parent_run_ref")
        for ref in [
            *self.child_run_refs,
            *self.approval_refs,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.cost_posture_refs,
            *self.authority_boundary_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.failure_refs,
            *self.restart_refs,
            *self.idempotency_key_refs_seen,
            *self.receipt_hash_refs,
            *self.replay_validation_refs,
        ]:
            validate_execution_ref(ref, "durable_run_lifecycle_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.origin_surface, "origin_surface")
        validate_safe_execution_text(self.source_status, "source_status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        validate_safe_execution_text(self.deterministic_event_ordering, "deterministic_event_ordering")
        validate_safe_execution_text(self.timestamp_recording_status, "timestamp_recording_status")
        validate_safe_execution_text(self.cancel_resume_controls_status, "cancel_resume_controls_status")
        validate_safe_execution_payload(self.model_dump(mode="json", exclude={"events"}), "lifecycle_read_model")
        for field_name in [
            "append_only_event_log",
            "idempotent_append_enforced",
            "hash_chain_verified_on_load",
            "safe_refs_only",
            "approval_refs_are_identifiers_only",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"DURABLE_RUN_LIFECYCLE_INVARIANT_FAILED:{field_name}")
        for field_name in [
            "raw_payloads_persisted",
            "receipt_summaries_included",
            "execution_authority_enabled",
            "execution_performed",
            "scheduler_enabled",
            "background_worker_enabled",
            "provider_model_calls_enabled",
            "tool_execution_expansion_enabled",
            "connector_writes_enabled",
            "streaming_runtime_enabled",
            "api_mutation_routes_added",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"DURABLE_RUN_LIFECYCLE_AUTHORITY_DENIED:{field_name}")
        if self.event_count != len(self.events):
            raise ValueError("DURABLE_RUN_LIFECYCLE_EVENT_COUNT_MISMATCH")
        return self


def _event_read_model(entry: DurableRunStorageEntry, *, sequence: int) -> DurableRunLifecycleEventReadModel:
    record = _record_from_entry(entry)
    return DurableRunLifecycleEventReadModel(
        run_id=entry.run_id,
        sequence=sequence,
        event_type=_event_type_for_entry(entry, sequence),
        storage_entry_kind=entry.kind.value,
        storage_entry_ref=entry.entry_id,
        status_after=_canonical_state(record.state) if record is not None else None,
        generation_after=record.generation if record is not None else None,
        idempotency_key_ref=entry.idempotency_key,
        audit_ref=entry.audit_ref,
        receipt_ref=entry.receipt_ref,
        rollback_ref=entry.rollback_ref,
        evidence_refs=list(entry.evidence_refs),
        entry_hash_ref=entry.entry_hash_ref,
        previous_entry_hash_ref=entry.previous_entry_hash_ref,
        receipt_hash_ref=entry.receipt_hash_ref,
        replay_validation_ref=entry.replay_validation_ref,
        safe_summary=entry.safe_summary,
    )


def build_durable_run_lifecycle_read_model(
    storage: AppendFirstRunStorage,
    run_id: str,
    *,
    include_receipts: bool = True,
    limit: int = 50,
) -> DurableRunLifecycleReadModel | None:
    validate_execution_ref(run_id, "run_id")
    bounded_limit = max(1, min(limit, 200))
    record = storage.latest_run_record(run_id)
    if record is None:
        return None

    all_entries = storage.list_entries(run_id)
    visible_entries = all_entries if include_receipts else [
        entry for entry in all_entries if entry.kind != DurableRunStorageEntryKind.receipt
    ]
    limited_entries = visible_entries[-bounded_limit:]
    events = [
        _event_read_model(entry, sequence=index)
        for index, entry in enumerate(limited_entries, start=max(1, len(visible_entries) - len(limited_entries) + 1))
    ]
    receipt_hash_refs = [
        entry.receipt_hash_ref
        for entry in all_entries
        if entry.kind == DurableRunStorageEntryKind.receipt and entry.receipt_hash_ref
    ]
    replay_validation_refs = [
        entry.replay_validation_ref
        for entry in all_entries
        if entry.kind == DurableRunStorageEntryKind.receipt and entry.replay_validation_ref
    ]
    return DurableRunLifecycleReadModel(
        run_id=record.run_id,
        run_ref=_stable_ref("durable-run-ref", record.run_id),
        origin_surface="task_decomposition",
        status=_canonical_state(record.state),
        source_status=record.state.value,
        generation=record.generation,
        source_ref=record.source_ref,
        intent_safe_summary_ref=_stable_ref("intent-summary-ref", record.run_id, str(record.generation)),
        safe_summary=record.safe_summary,
        approval_refs=_safe_metadata_refs(record, "approval_refs"),
        receipt_refs=list(record.receipt_refs),
        evidence_refs=list(record.evidence_refs),
        cost_posture_refs=_safe_metadata_refs(record, "cost_posture_refs"),
        audit_refs=list(record.audit_refs),
        replay_refs=list(record.replay_refs),
        rollback_refs=list(record.rollback_refs),
        failure_refs=list(record.failure_refs),
        restart_refs=list(record.restart_refs),
        idempotency_key_refs_seen=list(record.idempotency_keys_seen),
        receipt_hash_refs=receipt_hash_refs,
        replay_validation_refs=replay_validation_refs,
        event_count=len(events),
        run_record_event_count=sum(1 for entry in all_entries if entry.kind == DurableRunStorageEntryKind.run_record),
        receipt_event_count=sum(1 for entry in all_entries if entry.kind == DurableRunStorageEntryKind.receipt),
        events=events,
    )
