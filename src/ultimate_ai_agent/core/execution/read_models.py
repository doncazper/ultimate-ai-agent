from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

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
RUN_PROGRESS_READ_MODEL_SCHEMA_VERSION = "run_progress_read_model.v1"
RUN_PROGRESS_EVENT_READ_MODEL_SCHEMA_VERSION = "run_progress_event_read_model.v1"
RUN_PROGRESS_EVENT_RECEIPT_SCHEMA_VERSION = "run_progress_event_receipt.v1"

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
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
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

RunProgressState = Literal[
    "idle",
    "waiting",
    "running",
    "paused",
    "cancel_requested",
    "completed",
    "failed",
    "blocked",
]

RunProgressEventType = Literal[
    "run_created",
    "run_queued",
    "approval_required",
    "approval_attached",
    "approval_denied",
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
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
    "stream_started",
    "stream_delta_redacted",
    "stream_heartbeat",
    "stream_completed",
    "stream_failed",
    "stream_canceled",
    "stream_redaction_applied",
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
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
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

RUN_PROGRESS_EVENT_TYPES: tuple[RunProgressEventType, ...] = (
    *CANONICAL_RUN_EVENT_TYPES,
    "stream_started",
    "stream_delta_redacted",
    "stream_heartbeat",
    "stream_completed",
    "stream_failed",
    "stream_canceled",
    "stream_redaction_applied",
)

_RUN_PROGRESS_RECEIPT_EVENT_TYPES: set[RunProgressEventType] = {
    "stream_started",
    "stream_delta_redacted",
    "stream_heartbeat",
    "stream_completed",
    "stream_failed",
    "stream_canceled",
    "stream_redaction_applied",
    "step_started",
    "step_progress",
    "step_blocked",
    "step_completed",
    "redaction_applied",
}

_RUN_PROGRESS_TERMINAL_EVENT_TYPES: set[RunProgressEventType] = {
    "stream_completed",
    "stream_failed",
    "stream_canceled",
}

_PROGRESS_RAW_PAYLOAD_FIELD_RE = re.compile(
    r"(?i)(^|[_-])("
    r"raw|prompt|completion|response|payload|provider[_-]?payload|tool[_-]?payload|"
    r"chunk|delta|body|output|text|local[_-]?path|env[_-]?dump|credential|cookie|"
    r"token|secret|password|username|hostname|file[_-]?content"
    r")($|[_-])"
)

_PROGRESS_RAW_PAYLOAD_VALUE_RE = re.compile(
    r"(?i)(raw\s+(prompt|completion|response|chunk|delta|body|output|text|payload|local\s+path|file\s+content)|"
    r"provider[\s_-]?payload|tool[\s_-]?payload|env[\s_-]?dump|"
    r"credential|secret|api[_-]?key|bearer\s+|cookie|token|/Users/|/home/|"
    r"-----BEGIN)"
)
_PROGRESS_RAW_SCAN_ALLOWED_KEYS = {
    "raw_content_persisted",
    "raw_chunk_persisted",
    "raw_content_omitted",
    "redacted_delta_ref",
}

_APPROVAL_RECEIPT_EVENT_TYPES: set[CanonicalRunEventType] = {
    "approval_required",
    "approval_attached",
    "approval_denied",
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
}


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


def _receipt_ref_list(summary: Mapping[str, Any], key: str) -> list[str]:
    values = summary.get(key, [])
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    safe_refs: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        validate_execution_ref(value, key)
        safe_refs.append(value)
    return sorted(dict.fromkeys(safe_refs))


def _optional_receipt_ref(summary: Mapping[str, Any], key: str) -> str | None:
    value = summary.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    validate_execution_ref(value, key)
    return value


def _progress_raw_payload_reasons(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text not in _PROGRESS_RAW_SCAN_ALLOWED_KEYS and _PROGRESS_RAW_PAYLOAD_FIELD_RE.search(key_text):
                reasons.append("RUN_PROGRESS_RAW_PAYLOAD_FIELD_BLOCKED")
            reasons.extend(_progress_raw_payload_reasons(item))
        return sorted(dict.fromkeys(reasons))
    if isinstance(value, list):
        for item in value:
            reasons.extend(_progress_raw_payload_reasons(item))
        return sorted(dict.fromkeys(reasons))
    if isinstance(value, str) and _PROGRESS_RAW_PAYLOAD_VALUE_RE.search(value):
        reasons.append("RUN_PROGRESS_RAW_PAYLOAD_VALUE_BLOCKED")
    return sorted(dict.fromkeys(reasons))


def _progress_state_for_status(status: CanonicalRunLifecycleState, event_count: int) -> RunProgressState:
    if event_count == 0:
        return "idle"
    if status in {"created", "queued", "waiting_for_approval", "ready"}:
        return "waiting"
    if status == "running":
        return "running"
    if status == "paused":
        return "paused"
    if status == "cancel_requested" or status == "canceled":
        return "cancel_requested"
    if status == "succeeded":
        return "completed"
    if status in {"failed", "expired"}:
        return "failed"
    return "blocked"


def _progress_event_type_from_receipt(summary: Mapping[str, Any]) -> RunProgressEventType | None:
    event_type = summary.get("run_progress_event_type")
    if isinstance(event_type, str) and event_type in _RUN_PROGRESS_RECEIPT_EVENT_TYPES:
        return cast(RunProgressEventType, event_type)
    return None


def _progress_event_type_for_entry(entry: DurableRunStorageEntry, sequence: int) -> RunProgressEventType:
    if entry.kind == DurableRunStorageEntryKind.receipt and isinstance(entry.receipt_summary, dict):
        progress_event_type = _progress_event_type_from_receipt(entry.receipt_summary)
        if progress_event_type is not None:
            return progress_event_type
    return cast(RunProgressEventType, _event_type_for_entry(entry, sequence))


def _record_from_entry(entry: DurableRunStorageEntry) -> DurableRunRecord | None:
    if entry.kind != DurableRunStorageEntryKind.run_record or entry.record_snapshot is None:
        return None
    return restore_durable_run_snapshot(entry.record_snapshot)


def _event_type_for_entry(entry: DurableRunStorageEntry, sequence: int) -> CanonicalRunEventType:
    if entry.kind == DurableRunStorageEntryKind.receipt:
        if isinstance(entry.receipt_summary, dict):
            approval_event_type = entry.receipt_summary.get("run_approval_event_type")
            if approval_event_type in _APPROVAL_RECEIPT_EVENT_TYPES:
                return cast(CanonicalRunEventType, approval_event_type)
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


class RunProgressEventReadModel(BaseModel):
    schema_version: str = RUN_PROGRESS_EVENT_READ_MODEL_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=1)
    event_type: RunProgressEventType
    durable_run_event_ref: str = Field(..., min_length=1)
    storage_entry_ref: str = Field(..., min_length=1)
    storage_entry_kind: str = Field(..., min_length=1)
    status_after: CanonicalRunLifecycleState | None = None
    redacted_delta_ref: str | None = None
    heartbeat_ref: str | None = None
    redaction_posture_ref: str | None = None
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    safe_refs_only: bool = True
    raw_content_persisted: bool = False
    raw_chunk_persisted: bool = False
    live_streaming_runtime_enabled: bool = False
    provider_streaming_enabled: bool = False
    tool_streaming_enabled: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_event(self) -> Any:
        for value, field_name in [
            (self.run_ref, "run_ref"),
            (self.durable_run_event_ref, "durable_run_event_ref"),
            (self.storage_entry_ref, "storage_entry_ref"),
        ]:
            validate_execution_ref(value, field_name)
        optional_refs = [
            (self.redacted_delta_ref, "redacted_delta_ref"),
            (self.heartbeat_ref, "heartbeat_ref"),
            (self.redaction_posture_ref, "redaction_posture_ref"),
        ]
        for value, field_name in optional_refs:
            if value:
                validate_execution_ref(value, field_name)
        for ref in [*self.receipt_refs, *self.evidence_refs, *self.blocked_state_refs]:
            validate_execution_ref(ref, "run_progress_event_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.storage_entry_kind, "storage_entry_kind")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if _progress_raw_payload_reasons(self.model_dump(mode="json", exclude={"event_type"})):
            raise ValueError("RUN_PROGRESS_RAW_PAYLOAD_DENIED")
        if self.event_type == "stream_delta_redacted" and not self.redacted_delta_ref:
            raise ValueError("RUN_PROGRESS_REDACTED_DELTA_REF_REQUIRED")
        if self.event_type == "stream_heartbeat" and not self.heartbeat_ref:
            raise ValueError("RUN_PROGRESS_HEARTBEAT_REF_REQUIRED")
        if self.event_type in {"stream_redaction_applied", "redaction_applied"} and not self.redaction_posture_ref:
            raise ValueError("RUN_PROGRESS_REDACTION_POSTURE_REF_REQUIRED")
        for field_name in [
            "safe_refs_only",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"RUN_PROGRESS_INVARIANT_FAILED:{field_name}")
        for field_name in [
            "raw_content_persisted",
            "raw_chunk_persisted",
            "live_streaming_runtime_enabled",
            "provider_streaming_enabled",
            "tool_streaming_enabled",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"RUN_PROGRESS_AUTHORITY_DENIED:{field_name}")
        return self

    def to_receipt_summary(self) -> dict[str, Any]:
        return {
            "schema_version": RUN_PROGRESS_EVENT_RECEIPT_SCHEMA_VERSION,
            "run_progress_event_type": self.event_type,
            "run_ref": self.run_ref,
            "durable_run_event_ref": self.durable_run_event_ref,
            "redacted_delta_ref": self.redacted_delta_ref,
            "heartbeat_ref": self.heartbeat_ref,
            "redaction_posture_ref": self.redaction_posture_ref,
            "receipt_refs": list(self.receipt_refs),
            "evidence_refs": list(self.evidence_refs),
            "blocked_state_refs": list(self.blocked_state_refs),
            "safe_summary_ref": _stable_ref(
                "run-progress-summary-ref",
                self.run_ref,
                self.durable_run_event_ref,
                self.event_type,
            ),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "stream_transport_active": False,
            "runtime_execution_performed": False,
        }


class RunProgressReadModel(BaseModel):
    schema_version: str = RUN_PROGRESS_READ_MODEL_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    sequence_start: int = Field(default=0, ge=0)
    sequence_end: int = Field(default=0, ge=0)
    event_count: int = Field(default=0, ge=0)
    latest_status: CanonicalRunLifecycleState
    progress_state: RunProgressState
    redacted_delta_refs: list[str] = Field(default_factory=list)
    heartbeat_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    events: list[RunProgressEventReadModel] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    safe_refs_only: bool = True
    raw_content_persisted: bool = False
    raw_chunk_persisted: bool = False
    ordered_under_durable_run_event_log: bool = True
    terminal_event_required_for_completed_streams: bool = True
    terminal_event_present: bool = False
    live_streaming_runtime_enabled: bool = False
    stream_transport_enabled: bool = False
    provider_streaming_enabled: bool = False
    tool_streaming_enabled: bool = False
    provider_model_calls_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    mutation_controls_enabled: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_progress(self) -> Any:
        validate_execution_ref(self.run_ref, "run_ref")
        for ref in [
            *self.redacted_delta_refs,
            *self.heartbeat_refs,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.blocked_state_refs,
        ]:
            validate_execution_ref(ref, "run_progress_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        validate_safe_execution_payload(self.model_dump(mode="json", exclude={"events"}), "run_progress_read_model")
        if self.event_count != len(self.events):
            raise ValueError("RUN_PROGRESS_EVENT_COUNT_MISMATCH")
        if self.event_count == 0:
            if self.sequence_start != 0 or self.sequence_end != 0:
                raise ValueError("RUN_PROGRESS_EMPTY_SEQUENCE_RANGE_INVALID")
        elif self.sequence_start < 1 or self.sequence_end < self.sequence_start:
            raise ValueError("RUN_PROGRESS_SEQUENCE_RANGE_INVALID")
        if validate_run_progress_event_sequence(self.events):
            raise ValueError("RUN_PROGRESS_EVENT_SEQUENCE_INVALID")
        has_stream_events = any(event.event_type.startswith("stream_") for event in self.events)
        if has_stream_events and self.progress_state in {"completed", "failed", "cancel_requested"}:
            if not self.terminal_event_present:
                raise ValueError("RUN_PROGRESS_TERMINAL_EVENT_REQUIRED")
        for field_name in [
            "safe_refs_only",
            "ordered_under_durable_run_event_log",
            "terminal_event_required_for_completed_streams",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"RUN_PROGRESS_INVARIANT_FAILED:{field_name}")
        for field_name in [
            "raw_content_persisted",
            "raw_chunk_persisted",
            "live_streaming_runtime_enabled",
            "stream_transport_enabled",
            "provider_streaming_enabled",
            "tool_streaming_enabled",
            "provider_model_calls_enabled",
            "background_worker_enabled",
            "scheduler_enabled",
            "mutation_controls_enabled",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"RUN_PROGRESS_AUTHORITY_DENIED:{field_name}")
        return self


def validate_run_progress_event_sequence(
    events: Sequence[RunProgressEventReadModel | Mapping[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    parsed_events: list[RunProgressEventReadModel] = []
    try:
        for event in events:
            if isinstance(event, Mapping):
                reasons.extend(_progress_raw_payload_reasons(event))
                parsed_events.append(RunProgressEventReadModel.model_validate(event))
            else:
                parsed_events.append(RunProgressEventReadModel.model_validate(event.model_dump(mode="python")))
    except (TypeError, ValueError) as exc:
        return sorted(dict.fromkeys([*reasons, f"RUN_PROGRESS_EVENT_VALIDATION_FAILED:{exc.__class__.__name__}"]))
    if not parsed_events:
        return []

    sequence_values = [event.sequence for event in parsed_events]
    expected_sequence_values = list(range(sequence_values[0], sequence_values[0] + len(parsed_events)))
    if sequence_values != expected_sequence_values:
        reasons.append("RUN_PROGRESS_SEQUENCE_NOT_MONOTONIC")
    durable_refs = [event.durable_run_event_ref for event in parsed_events]
    if len(durable_refs) != len(set(durable_refs)):
        reasons.append("RUN_PROGRESS_DURABLE_EVENT_REF_DUPLICATE")
    run_refs = {event.run_ref for event in parsed_events}
    if len(run_refs) != 1:
        reasons.append("RUN_PROGRESS_RUN_REF_MISMATCH")
    terminal_indexes = [
        index for index, event in enumerate(parsed_events) if event.event_type in _RUN_PROGRESS_TERMINAL_EVENT_TYPES
    ]
    if len(terminal_indexes) > 1:
        reasons.append("RUN_PROGRESS_TERMINAL_EVENT_DUPLICATE")
    if terminal_indexes and terminal_indexes[0] != len(parsed_events) - 1:
        reasons.append("RUN_PROGRESS_TERMINAL_EVENT_MUST_BE_LAST")
    stream_events = [event for event in parsed_events if event.event_type.startswith("stream_")]
    if parsed_events[0].sequence == 1 and stream_events and stream_events[0].event_type != "stream_started":
        reasons.append("RUN_PROGRESS_STREAM_STARTED_REQUIRED")
    return sorted(dict.fromkeys(reasons))


def _progress_event_read_model(entry: DurableRunStorageEntry, *, sequence: int) -> RunProgressEventReadModel:
    record = _record_from_entry(entry)
    receipt_summary = entry.receipt_summary if isinstance(entry.receipt_summary, dict) else {}
    event_type = _progress_event_type_for_entry(entry, sequence)
    redacted_delta_ref = _optional_receipt_ref(receipt_summary, "redacted_delta_ref")
    heartbeat_ref = _optional_receipt_ref(receipt_summary, "heartbeat_ref")
    redaction_posture_ref = _optional_receipt_ref(receipt_summary, "redaction_posture_ref")
    receipt_refs = _receipt_ref_list(receipt_summary, "receipt_refs")
    if entry.receipt_ref not in receipt_refs:
        receipt_refs = sorted([*receipt_refs, entry.receipt_ref])
    blocked_state_refs = _receipt_ref_list(receipt_summary, "blocked_state_refs")
    evidence_refs = sorted(dict.fromkeys([*entry.evidence_refs, *_receipt_ref_list(receipt_summary, "evidence_refs")]))
    return RunProgressEventReadModel(
        run_ref=entry.run_id,
        sequence=sequence,
        event_type=event_type,
        durable_run_event_ref=_stable_ref("durable-run-event-ref", entry.run_id, str(sequence), entry.entry_id),
        storage_entry_ref=entry.entry_id,
        storage_entry_kind=entry.kind.value,
        status_after=_canonical_state(record.state) if record is not None else None,
        redacted_delta_ref=redacted_delta_ref,
        heartbeat_ref=heartbeat_ref,
        redaction_posture_ref=redaction_posture_ref,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        blocked_state_refs=blocked_state_refs,
        safe_summary=entry.safe_summary,
    )


def build_run_progress_read_model(
    storage: AppendFirstRunStorage,
    run_id: str,
    *,
    limit: int = 50,
) -> RunProgressReadModel | None:
    validate_execution_ref(run_id, "run_id")
    bounded_limit = max(1, min(limit, 200))
    record = storage.latest_run_record(run_id)
    if record is None:
        return None

    all_entries = storage.list_entries(run_id)
    limited_entries = all_entries[-bounded_limit:]
    start_sequence = max(1, len(all_entries) - len(limited_entries) + 1)
    events = [
        _progress_event_read_model(entry, sequence=index)
        for index, entry in enumerate(limited_entries, start=start_sequence)
    ]
    terminal_event_present = bool(events and events[-1].event_type in _RUN_PROGRESS_TERMINAL_EVENT_TYPES)
    event_count = len(events)
    status = _canonical_state(record.state)
    return RunProgressReadModel(
        run_ref=record.run_id,
        sequence_start=events[0].sequence if events else 0,
        sequence_end=events[-1].sequence if events else 0,
        event_count=event_count,
        latest_status=status,
        progress_state=_progress_state_for_status(status, event_count),
        redacted_delta_refs=sorted(
            dict.fromkeys(event.redacted_delta_ref for event in events if event.redacted_delta_ref)
        ),
        heartbeat_refs=sorted(dict.fromkeys(event.heartbeat_ref for event in events if event.heartbeat_ref)),
        receipt_refs=sorted(dict.fromkeys(ref for event in events for ref in event.receipt_refs)),
        evidence_refs=sorted(dict.fromkeys(ref for event in events for ref in event.evidence_refs)),
        blocked_state_refs=sorted(dict.fromkeys(ref for event in events for ref in event.blocked_state_refs)),
        events=events,
        safe_summary=(
            "Recorded durable run progress read model; safe refs only, no live stream or runtime execution."
        ),
        terminal_event_present=terminal_event_present,
    )


def append_run_progress_event_receipt(
    storage: AppendFirstRunStorage,
    event: RunProgressEventReadModel,
    *,
    idempotency_key_ref: str,
    audit_ref: str,
    receipt_ref: str,
    rollback_ref: str,
) -> DurableRunStorageEntry:
    validated = RunProgressEventReadModel.model_validate(event.model_dump(mode="python"))
    for value, field_name in [
        (idempotency_key_ref, "idempotency_key_ref"),
        (audit_ref, "audit_ref"),
        (receipt_ref, "receipt_ref"),
        (rollback_ref, "rollback_ref"),
    ]:
        validate_execution_ref(value, field_name)
    return storage.append_receipt_summary(
        run_id=validated.run_ref,
        receipt_ref=receipt_ref,
        idempotency_key=idempotency_key_ref,
        audit_ref=audit_ref,
        rollback_ref=rollback_ref,
        safe_summary="Recorded progress event metadata persisted as safe refs only.",
        receipt_summary=validated.to_receipt_summary(),
        evidence_refs=validated.evidence_refs,
    )


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
