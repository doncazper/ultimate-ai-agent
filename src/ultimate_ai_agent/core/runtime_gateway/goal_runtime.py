from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from collections.abc import Iterable
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now

if TYPE_CHECKING:
    from ultimate_ai_agent.core.runtime_gateway.contracts import RuntimeInvocationRecord


GOAL_RUNTIME_STATE_DIR_ENV = "UAA_GOAL_RUNTIME_STATE_DIR"
DEFAULT_GOAL_RUNTIME_STATE_DIR = Path(".uaa") / "goal_runtime"
GOAL_JOURNAL_SCHEMA_VERSION = "goal_journal.v1"
RUN_EVENT_SCHEMA_VERSION = "durable_run_event.v1"
GOAL_RUNTIME_CONTRACT_REF = "contract-ref:proof-backed-goals-durable-events:v1"
GOAL_RUNTIME_REDACTIONS = (
    "raw_prompt_omitted",
    "raw_response_omitted",
    "raw_provider_payload_omitted",
    "raw_runtime_payload_omitted",
    "raw_log_omitted",
    "raw_local_path_omitted",
    "credential_material_omitted",
)
MAX_GOALS = 500
MAX_GOAL_TEXT = 1200
MAX_GOAL_LIST_ITEMS = 32
MAX_RUN_EVENT_RETENTION = 512
DEFAULT_RUN_EVENT_RETENTION = 256
MAX_REPLAY_EVENTS = 100
MAX_RUN_EVENT_IDEMPOTENCY_RECORDS = 4096
MAX_GOAL_JOURNAL_ENTRIES = 4096
MAX_GOAL_JOURNAL_BYTES = 16 * 1024 * 1024
RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS = 120


class GoalRuntimeError(ValueError):
    """Base error for the local proof-backed goal runtime."""


class GoalRuntimeCorruptionError(GoalRuntimeError):
    """Raised when durable goal or event evidence fails integrity validation."""


class GoalNotFoundError(GoalRuntimeError):
    """Raised when a goal ref is not present in the durable journal."""


class GoalVersionConflictError(GoalRuntimeError):
    """Raised when a goal mutation is based on a stale version."""


class GoalIdempotencyConflictError(GoalRuntimeError):
    """Raised when an idempotency ref is reused for a different request."""


class GoalTransitionDeniedError(GoalRuntimeError):
    """Raised when a goal lifecycle transition is not allowed."""


class RunEventNotFoundError(GoalRuntimeError):
    """Raised when a run event stream is not present."""


class GoalState(str, Enum):
    active = "active"
    paused = "paused"
    blocked = "blocked"
    waiting = "waiting"
    complete_requested = "complete_requested"
    verified_complete = "verified_complete"
    cancelled = "cancelled"
    cleared = "cleared"


class GoalTransitionKind(str, Enum):
    pause = "pause"
    resume = "resume"
    block = "block"
    wait = "wait"
    cancel = "cancel"
    clear = "clear"
    request_completion = "request_completion"
    verify_completion = "verify_completion"


class GoalJournalOperation(str, Enum):
    create = "create"
    edit = "edit"
    transition = "transition"


class AcceptedLocalRunType(str, Enum):
    local_read_task = "local_read_task"
    local_metadata_action = "local_metadata_action"


class DurableRunEventKind(str, Enum):
    goal_linked = "goal_linked"
    plan_linked = "plan_linked"
    run_started = "run_started"
    approval_wait_entered = "approval_wait_entered"
    approval_resumed = "approval_resumed"
    worker_restart_recovered = "worker_restart_recovered"
    allowed_local_action_recorded = "allowed_local_action_recorded"
    receipt_recorded = "receipt_recorded"
    evidence_linked = "evidence_linked"
    completion_verified = "completion_verified"
    cancellation_requested = "cancellation_requested"
    cancelled = "cancelled"
    failed_retryable = "failed_retryable"
    failed_terminal = "failed_terminal"
    dead_lettered = "dead_lettered"


TERMINAL_RUN_EVENT_KINDS = frozenset(
    {
        DurableRunEventKind.completion_verified.value,
        DurableRunEventKind.cancelled.value,
        DurableRunEventKind.failed_terminal.value,
        DurableRunEventKind.dead_lettered.value,
    }
)


class RunEventReplayStatus(str, Enum):
    ok = "ok"
    unknown_run = "unknown_run"
    stale_cursor = "stale_cursor"
    retention_loss = "retention_loss"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _bounded_safe_text(value: str, field_name: str) -> str:
    candidate = value.strip()
    if not candidate or len(candidate) > MAX_GOAL_TEXT:
        raise ValueError(f"{field_name} must be between 1 and {MAX_GOAL_TEXT} characters")
    validate_safe_execution_text(candidate, field_name)
    return candidate


def _validate_refs(refs: Iterable[str], field_name: str) -> list[str]:
    values = list(dict.fromkeys(refs))
    if len(values) > MAX_GOAL_LIST_ITEMS:
        raise ValueError(f"{field_name} exceeds the bounded item limit")
    for ref in values:
        validate_execution_ref(ref, field_name)
    return values


def _validate_safe_texts(values: Iterable[str], field_name: str) -> list[str]:
    items = list(dict.fromkeys(value.strip() for value in values))
    if len(items) > MAX_GOAL_LIST_ITEMS:
        raise ValueError(f"{field_name} exceeds the bounded item limit")
    for item in items:
        _bounded_safe_text(item, field_name)
    return items


def _utc_iso() -> str:
    return utc_now().isoformat()


class GoalBudget(BaseModel):
    operation_limit: StrictInt = Field(default=25, ge=1, le=10_000)
    cost_budget_microusd: StrictInt = Field(default=0, ge=0, le=10_000_000_000)
    deadline_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class GoalLinks(BaseModel):
    plan_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    action_inbox_refs: list[str] = Field(default_factory=list)
    work_board_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_links(self) -> "GoalLinks":
        self.plan_refs = _validate_refs(self.plan_refs, "plan_refs")
        self.run_refs = _validate_refs(self.run_refs, "run_refs")
        self.action_inbox_refs = _validate_refs(
            self.action_inbox_refs, "action_inbox_refs"
        )
        self.work_board_refs = _validate_refs(
            self.work_board_refs, "work_board_refs"
        )
        return self


class GoalCreateRequest(BaseModel):
    objective: str
    desired_outcome: str
    success_criteria: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    in_scope_resource_refs: list[str] = Field(default_factory=list)
    stop_condition: str
    budget: GoalBudget = Field(default_factory=GoalBudget)
    links: GoalLinks = Field(default_factory=GoalLinks)
    evidence_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "GoalCreateRequest":
        self.objective = _bounded_safe_text(self.objective, "objective")
        self.desired_outcome = _bounded_safe_text(
            self.desired_outcome, "desired_outcome"
        )
        self.stop_condition = _bounded_safe_text(
            self.stop_condition, "stop_condition"
        )
        self.success_criteria = _validate_safe_texts(
            self.success_criteria, "success_criteria"
        )
        self.constraints = _validate_safe_texts(self.constraints, "constraints")
        self.in_scope_resource_refs = _validate_refs(
            self.in_scope_resource_refs, "in_scope_resource_refs"
        )
        self.evidence_refs = _validate_refs(self.evidence_refs, "evidence_refs")
        return self


class GoalEditRequest(BaseModel):
    expected_version: StrictInt = Field(ge=1)
    objective: str | None = None
    desired_outcome: str | None = None
    success_criteria: list[str] | None = None
    constraints: list[str] | None = None
    in_scope_resource_refs: list[str] | None = None
    stop_condition: str | None = None
    budget: GoalBudget | None = None
    links: GoalLinks | None = None
    evidence_refs: list[str] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "GoalEditRequest":
        if not any(
            getattr(self, field_name) is not None
            for field_name in (
                "objective",
                "desired_outcome",
                "success_criteria",
                "constraints",
                "in_scope_resource_refs",
                "stop_condition",
                "budget",
                "links",
                "evidence_refs",
            )
        ):
            raise ValueError("GOAL_EDIT_EMPTY")
        if self.objective is not None:
            self.objective = _bounded_safe_text(self.objective, "objective")
        if self.desired_outcome is not None:
            self.desired_outcome = _bounded_safe_text(
                self.desired_outcome, "desired_outcome"
            )
        if self.stop_condition is not None:
            self.stop_condition = _bounded_safe_text(
                self.stop_condition, "stop_condition"
            )
        if self.success_criteria is not None:
            self.success_criteria = _validate_safe_texts(
                self.success_criteria, "success_criteria"
            )
            if not self.success_criteria:
                raise ValueError("GOAL_SUCCESS_CRITERIA_REQUIRED")
        if self.constraints is not None:
            self.constraints = _validate_safe_texts(
                self.constraints, "constraints"
            )
        if self.in_scope_resource_refs is not None:
            self.in_scope_resource_refs = _validate_refs(
                self.in_scope_resource_refs, "in_scope_resource_refs"
            )
        if self.evidence_refs is not None:
            self.evidence_refs = _validate_refs(
                self.evidence_refs, "evidence_refs"
            )
        return self


class GoalCompletionEvidence(BaseModel):
    goal_ref: str
    goal_version: StrictInt = Field(ge=1)
    run_ref: str
    receipt_ref: str
    proof_ref: str
    evidence_ref: str
    verifier_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_evidence(self) -> "GoalCompletionEvidence":
        for value, field_name in (
            (self.goal_ref, "goal_ref"),
            (self.run_ref, "run_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.proof_ref, "proof_ref"),
            (self.evidence_ref, "evidence_ref"),
            (self.verifier_ref, "verifier_ref"),
        ):
            validate_execution_ref(value, field_name)
        return self


class GoalTransitionRequest(BaseModel):
    expected_version: StrictInt = Field(ge=1)
    transition: GoalTransitionKind
    reason_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    completion_evidence: GoalCompletionEvidence | None = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "GoalTransitionRequest":
        validate_execution_ref(self.reason_ref, "reason_ref")
        self.evidence_refs = _validate_refs(self.evidence_refs, "evidence_refs")
        if self.transition == GoalTransitionKind.verify_completion.value:
            if self.completion_evidence is None:
                raise ValueError("GOAL_COMPLETION_EVIDENCE_REQUIRED")
        elif self.completion_evidence is not None:
            raise ValueError("GOAL_COMPLETION_EVIDENCE_NOT_ALLOWED")
        return self


class PersistentGoal(BaseModel):
    schema_version: str = "persistent_goal.v1"
    contract_ref: str = GOAL_RUNTIME_CONTRACT_REF
    goal_ref: str
    objective: str
    desired_outcome: str
    success_criteria: list[str]
    constraints: list[str]
    in_scope_resource_refs: list[str]
    stop_condition: str
    state: GoalState
    budget: GoalBudget
    links: GoalLinks
    version: StrictInt = Field(ge=1)
    created_at: datetime
    updated_at: datetime
    evidence_refs: list[str]
    completion_run_ref: str | None = None
    completion_plan_ref: str | None = None
    completion_evidence_ref: str | None = None
    completion_receipt_ref: str | None = None
    completion_proof_ref: str | None = None
    completion_verifier_ref: str | None = None
    safe_refs_only: bool = True
    model_output_authoritative: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_goal(self) -> "PersistentGoal":
        validate_execution_ref(self.goal_ref, "goal_ref")
        self.objective = _bounded_safe_text(self.objective, "objective")
        self.desired_outcome = _bounded_safe_text(
            self.desired_outcome, "desired_outcome"
        )
        self.stop_condition = _bounded_safe_text(
            self.stop_condition, "stop_condition"
        )
        self.success_criteria = _validate_safe_texts(
            self.success_criteria, "success_criteria"
        )
        self.constraints = _validate_safe_texts(self.constraints, "constraints")
        self.in_scope_resource_refs = _validate_refs(
            self.in_scope_resource_refs, "in_scope_resource_refs"
        )
        self.evidence_refs = _validate_refs(self.evidence_refs, "evidence_refs")
        if not self.success_criteria:
            raise ValueError("GOAL_SUCCESS_CRITERIA_REQUIRED")
        for value, field_name in (
            (self.completion_run_ref, "completion_run_ref"),
            (self.completion_plan_ref, "completion_plan_ref"),
            (self.completion_evidence_ref, "completion_evidence_ref"),
            (self.completion_receipt_ref, "completion_receipt_ref"),
            (self.completion_proof_ref, "completion_proof_ref"),
            (self.completion_verifier_ref, "completion_verifier_ref"),
        ):
            if value is not None:
                validate_execution_ref(value, field_name)
        completion_refs = (
            self.completion_run_ref,
            self.completion_evidence_ref,
            self.completion_receipt_ref,
            self.completion_proof_ref,
            self.completion_verifier_ref,
        )
        if self.completion_plan_ref is not None:
            if self.completion_plan_ref not in self.links.plan_refs:
                raise ValueError("GOAL_COMPLETION_PLAN_NOT_LINKED")
        if self.state == GoalState.verified_complete.value:
            if any(value is None for value in completion_refs):
                raise ValueError("GOAL_VERIFIED_COMPLETION_PROOF_REQUIRED")
        elif self.state == GoalState.cleared.value and any(
            value is not None for value in completion_refs
        ):
            if any(value is None for value in completion_refs):
                raise ValueError("GOAL_CLEARED_COMPLETION_PROOF_INCOMPLETE")
        elif any(value is not None for value in completion_refs):
            raise ValueError("GOAL_UNVERIFIED_COMPLETION_PROOF_DENIED")
        if not self.safe_refs_only or self.model_output_authoritative:
            raise ValueError("GOAL_UNSAFE_AUTHORITY_POSTURE")
        return self


class GoalJournalEntry(BaseModel):
    schema_version: str = GOAL_JOURNAL_SCHEMA_VERSION
    entry_ref: str
    operation: GoalJournalOperation
    goal_ref: str
    goal_version: StrictInt = Field(ge=1)
    idempotency_ref: str
    request_fingerprint_ref: str
    approval_ref: str
    approval_decision_ref: str
    recorded_at: datetime
    goal: PersistentGoal
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "GoalJournalEntry":
        for value, field_name in (
            (self.entry_ref, "entry_ref"),
            (self.goal_ref, "goal_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.approval_ref, "approval_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.entry_hash_ref, "entry_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        if self.previous_entry_hash_ref is not None:
            validate_execution_ref(
                self.previous_entry_hash_ref, "previous_entry_hash_ref"
            )
        if self.goal.goal_ref != self.goal_ref or self.goal.version != self.goal_version:
            raise ValueError("GOAL_JOURNAL_SNAPSHOT_BINDING_MISMATCH")
        return self


class DurableRunEventAppendRequest(BaseModel):
    run_ref: str
    run_type: AcceptedLocalRunType
    event_kind: DurableRunEventKind
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    goal_ref: str | None = None
    plan_ref: str | None = None
    idempotency_ref: str
    authority_decision_ref: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "DurableRunEventAppendRequest":
        for value, field_name in (
            (self.run_ref, "run_ref"),
            (self.goal_ref, "goal_ref"),
            (self.plan_ref, "plan_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
        ):
            if value is not None:
                validate_execution_ref(value, field_name)
        self.safe_summary = _bounded_safe_text(self.safe_summary, "safe_summary")
        self.proof_refs = _validate_refs(self.proof_refs, "proof_refs")
        self.receipt_refs = _validate_refs(self.receipt_refs, "receipt_refs")
        if self.event_kind in {
            DurableRunEventKind.receipt_recorded.value,
            *TERMINAL_RUN_EVENT_KINDS,
        }:
            if not self.proof_refs or not self.receipt_refs:
                raise ValueError("RUN_EVENT_TERMINAL_RECEIPT_PROOF_REQUIRED")
        return self


class DurableRunEvent(BaseModel):
    schema_version: str = RUN_EVENT_SCHEMA_VERSION
    event_ref: str
    run_ref: str
    run_type: AcceptedLocalRunType
    sequence: StrictInt = Field(ge=1)
    recorded_at: datetime
    event_kind: DurableRunEventKind
    safe_summary: str
    proof_refs: list[str]
    receipt_refs: list[str]
    goal_ref: str | None = None
    plan_ref: str | None = None
    idempotency_ref: str
    authority_decision_ref: str
    predecessor_hash_ref: str | None = None
    event_hash_ref: str
    redaction_status: str = "redacted_safe_refs_only"
    raw_payload_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_event(self) -> "DurableRunEvent":
        for value, field_name in (
            (self.event_ref, "event_ref"),
            (self.run_ref, "run_ref"),
            (self.goal_ref, "goal_ref"),
            (self.plan_ref, "plan_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.predecessor_hash_ref, "predecessor_hash_ref"),
            (self.event_hash_ref, "event_hash_ref"),
        ):
            if value is not None:
                validate_execution_ref(value, field_name)
        self.safe_summary = _bounded_safe_text(self.safe_summary, "safe_summary")
        self.proof_refs = _validate_refs(self.proof_refs, "proof_refs")
        self.receipt_refs = _validate_refs(self.receipt_refs, "receipt_refs")
        if self.event_kind in {
            DurableRunEventKind.receipt_recorded.value,
            *TERMINAL_RUN_EVENT_KINDS,
        } and (not self.proof_refs or not self.receipt_refs):
            raise ValueError("RUN_EVENT_TERMINAL_RECEIPT_PROOF_REQUIRED")
        validate_safe_execution_text(self.redaction_status, "redaction_status")
        if self.raw_payload_persisted:
            raise ValueError("RUN_EVENT_RAW_PAYLOAD_PERSISTENCE_DENIED")
        return self


class RunEventIdempotencyTombstone(BaseModel):
    schema_version: str = "run_event_idempotency_tombstone.v1"
    run_ref: str
    idempotency_ref: str
    request_fingerprint_ref: str
    event: DurableRunEvent
    tombstone_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_tombstone(self) -> "RunEventIdempotencyTombstone":
        for value, field_name in (
            (self.run_ref, "run_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.tombstone_hash_ref, "tombstone_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        if (
            self.event.run_ref != self.run_ref
            or self.event.idempotency_ref != self.idempotency_ref
        ):
            raise ValueError("RUN_EVENT_IDEMPOTENCY_TOMBSTONE_BINDING_MISMATCH")
        return self


class RunEventProjectionReservation(BaseModel):
    schema_version: str = "run_event_projection_reservation.v1"
    reservation_ref: str
    operation_idempotency_ref: str
    holder_count: StrictInt = Field(default=1, ge=1, le=1024)
    slot_count: StrictInt = Field(ge=0, le=2)
    allowed_event_key_refs: list[str] = Field(default_factory=list)
    reserved_at: datetime
    expires_at: datetime
    reservation_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_reservation(self) -> "RunEventProjectionReservation":
        validate_execution_ref(self.reservation_ref, "reservation_ref")
        validate_execution_ref(
            self.operation_idempotency_ref,
            "operation_idempotency_ref",
        )
        validate_execution_ref(
            self.reservation_hash_ref,
            "reservation_hash_ref",
        )
        self.allowed_event_key_refs = _validate_refs(
            self.allowed_event_key_refs,
            "allowed_event_key_refs",
        )
        if len(self.allowed_event_key_refs) != self.slot_count:
            if self.allowed_event_key_refs:
                raise ValueError("RUN_EVENT_RESERVATION_ARITY_MISMATCH")
        if self.expires_at <= self.reserved_at:
            raise ValueError("RUN_EVENT_RESERVATION_EXPIRY_INVALID")
        return self


class GoalLifecycleReadModel(BaseModel):
    schema_version: str = "goal_lifecycle_read_model.v1"
    contract_ref: str = GOAL_RUNTIME_CONTRACT_REF
    status: str = "durable_local_proof_backed"
    goals: list[PersistentGoal]
    goal_count: StrictInt = Field(ge=0)
    active_count: StrictInt = Field(ge=0)
    completion_requested_count: StrictInt = Field(ge=0)
    verified_complete_count: StrictInt = Field(ge=0)
    mutation_authority: str = "exact_local_metadata_only"
    runtime_execution_enabled: bool = False
    model_output_authoritative: bool = False
    safe_refs_only: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOAL_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")


class RunEventStreamSummary(BaseModel):
    run_ref: str
    run_type: AcceptedLocalRunType
    first_retained_sequence: StrictInt = Field(ge=1)
    last_sequence: StrictInt = Field(ge=1)
    retained_event_count: StrictInt = Field(ge=1)
    retention_anchor_hash_ref: str | None = None
    terminal_event_kind: DurableRunEventKind | None = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class RunEventReplayReadModel(BaseModel):
    schema_version: str = "durable_run_event_replay.v1"
    contract_ref: str = GOAL_RUNTIME_CONTRACT_REF
    status: RunEventReplayStatus
    run_ref: str
    after_sequence: StrictInt = Field(ge=0)
    next_cursor: StrictInt = Field(ge=0)
    first_retained_sequence: StrictInt | None = Field(default=None, ge=1)
    last_sequence: StrictInt = Field(ge=0)
    retention_anchor_hash_ref: str | None = None
    events: list[DurableRunEvent]
    gap_detected: bool = False
    corruption_detected: bool = False
    duplicate_events_returned: bool = False
    live_transport_enabled: bool = False
    control_messages_accepted: bool = False
    safe_refs_only: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOAL_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class _GoalJournalStore:
    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / "goals.jsonl"
        self._locks = FileSingleWriterLockManager(self.state_dir / ".locks")

    def create(
        self,
        request: GoalCreateRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
    ) -> PersistentGoal:
        validated = GoalCreateRequest.model_validate(request.model_dump())
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        _validate_goal_mutation_approval_binding(
            approval_binding,
            operation="create",
            subject_ref="goal-ref:new",
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=idempotency_ref,
        )
        fingerprint = _sha256_ref(
            "request-fingerprint-ref:goal-create",
            validated.model_dump(mode="json"),
        )
        with self._locks.acquire("goal-journal"):
            entries = self._load_entries()
            replay = self._idempotent_replay(entries, idempotency_ref, fingerprint)
            if replay is not None:
                return replay
            latest = self._latest_by_goal(entries)
            if len(latest) >= MAX_GOALS:
                raise GoalRuntimeError("GOAL_STORE_CAPACITY_EXCEEDED")
            goal_ref = _sha256_ref(
                "goal-ref",
                {
                    "idempotency_ref": idempotency_ref,
                    "objective": validated.objective,
                },
            )
            if goal_ref in latest:
                raise GoalIdempotencyConflictError("GOAL_REF_COLLISION")
            now = utc_now()
            goal = PersistentGoal(
                goal_ref=goal_ref,
                objective=validated.objective,
                desired_outcome=validated.desired_outcome,
                success_criteria=validated.success_criteria,
                constraints=validated.constraints,
                in_scope_resource_refs=validated.in_scope_resource_refs,
                stop_condition=validated.stop_condition,
                state=GoalState.active,
                budget=validated.budget,
                links=validated.links,
                version=1,
                created_at=now,
                updated_at=now,
                evidence_refs=validated.evidence_refs,
            )
            self._append(
                entries,
                operation=GoalJournalOperation.create,
                goal=goal,
                idempotency_ref=idempotency_ref,
                request_fingerprint_ref=fingerprint,
                approval_ref=approval_binding.approval_ref,
                approval_decision_ref=approval_binding.approval_decision_ref,
            )
            return goal.model_copy(deep=True)

    def edit(
        self,
        goal_ref: str,
        request: GoalEditRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
    ) -> PersistentGoal:
        validated = GoalEditRequest.model_validate(request.model_dump())
        _validate_goal_mutation_approval_binding(
            approval_binding,
            operation="edit",
            subject_ref=goal_ref,
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=idempotency_ref,
        )
        return self._mutate(
            goal_ref,
            operation=GoalJournalOperation.edit,
            request_payload=validated.model_dump(mode="json"),
            expected_version=validated.expected_version,
            idempotency_ref=idempotency_ref,
            approval_binding=approval_binding,
            mutate=lambda current: self._edited_goal(current, validated),
        )

    def transition(
        self,
        goal_ref: str,
        request: GoalTransitionRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
        completion_verified: bool = False,
        completion_plan_ref: str | None = None,
    ) -> PersistentGoal:
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        _validate_goal_mutation_approval_binding(
            approval_binding,
            operation=f"transition-{validated.transition}",
            subject_ref=goal_ref,
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=idempotency_ref,
        )
        return self._mutate(
            goal_ref,
            operation=GoalJournalOperation.transition,
            request_payload=validated.model_dump(mode="json"),
            expected_version=validated.expected_version,
            idempotency_ref=idempotency_ref,
            approval_binding=approval_binding,
            mutate=lambda current: self._transitioned_goal(
                current,
                validated,
                completion_verified=completion_verified,
                completion_plan_ref=completion_plan_ref,
            ),
        )

    def replay_transition(
        self,
        goal_ref: str,
        request: GoalTransitionRequest,
        *,
        idempotency_ref: str,
    ) -> PersistentGoal | None:
        """Return an exact prior transition before version-sensitive revalidation."""

        validate_execution_ref(goal_ref, "goal_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        fingerprint = _sha256_ref(
            "request-fingerprint-ref:goal-transition",
            {
                "goal_ref": goal_ref,
                "request": validated.model_dump(mode="json"),
            },
        )
        with self._locks.acquire("goal-journal"):
            return self._idempotent_replay(
                self._load_entries(),
                idempotency_ref,
                fingerprint,
            )

    def transition_entry(
        self,
        goal_ref: str,
        request: GoalTransitionRequest,
        *,
        idempotency_ref: str,
    ) -> GoalJournalEntry | None:
        """Return the exact durable entry for one idempotent transition request."""

        validate_execution_ref(goal_ref, "goal_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        fingerprint = _sha256_ref(
            "request-fingerprint-ref:goal-transition",
            {
                "goal_ref": goal_ref,
                "request": validated.model_dump(mode="json"),
            },
        )
        with self._locks.acquire("goal-journal"):
            for entry in self._load_entries():
                if entry.idempotency_ref != idempotency_ref:
                    continue
                if entry.request_fingerprint_ref != fingerprint:
                    raise GoalIdempotencyConflictError(
                        "GOAL_IDEMPOTENCY_CONFLICT"
                    )
                if (
                    entry.goal_ref != goal_ref
                    or entry.operation != GoalJournalOperation.transition.value
                ):
                    raise GoalRuntimeCorruptionError(
                        "GOAL_TRANSITION_REPLAY_ENTRY_MISMATCH"
                    )
                return entry.model_copy(deep=True)
        return None

    def latest_entry(self, goal_ref: str) -> GoalJournalEntry:
        validate_execution_ref(goal_ref, "goal_ref")
        entries = self._load_entries()
        for entry in reversed(entries):
            if entry.goal_ref == goal_ref:
                return entry.model_copy(deep=True)
        raise GoalNotFoundError("GOAL_NOT_FOUND")

    def latest_verified_completion_entry(
        self,
        goal_ref: str,
    ) -> GoalJournalEntry:
        validate_execution_ref(goal_ref, "goal_ref")
        with self._locks.acquire("goal-journal"):
            for entry in reversed(self._load_entries()):
                if (
                    entry.goal_ref == goal_ref
                    and entry.goal.state
                    == GoalState.verified_complete.value
                ):
                    return entry.model_copy(deep=True)
        raise GoalRuntimeCorruptionError(
            "GOAL_VERIFIED_COMPLETION_ENTRY_MISSING"
        )

    def get(self, goal_ref: str) -> PersistentGoal:
        validate_execution_ref(goal_ref, "goal_ref")
        latest = self._latest_by_goal(self._load_entries())
        if goal_ref not in latest:
            raise GoalNotFoundError("GOAL_NOT_FOUND")
        return latest[goal_ref].model_copy(deep=True)

    def list(self, *, include_cleared: bool = False) -> list[PersistentGoal]:
        goals = list(self._latest_by_goal(self._load_entries()).values())
        goals.sort(key=lambda goal: (goal.updated_at, goal.goal_ref), reverse=True)
        if not include_cleared:
            goals = [
                goal for goal in goals if goal.state != GoalState.cleared.value
            ]
        return [goal.model_copy(deep=True) for goal in goals]

    def read_model(self, *, include_cleared: bool = False) -> GoalLifecycleReadModel:
        goals = self.list(include_cleared=include_cleared)
        return GoalLifecycleReadModel(
            goals=goals,
            goal_count=len(goals),
            active_count=sum(goal.state == GoalState.active.value for goal in goals),
            completion_requested_count=sum(
                goal.state == GoalState.complete_requested.value for goal in goals
            ),
            verified_complete_count=sum(
                goal.state == GoalState.verified_complete.value for goal in goals
            ),
        )

    def _mutate(
        self,
        goal_ref: str,
        *,
        operation: GoalJournalOperation,
        request_payload: dict[str, Any],
        expected_version: int,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
        mutate: Any,
    ) -> PersistentGoal:
        validate_execution_ref(goal_ref, "goal_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        fingerprint = _sha256_ref(
            f"request-fingerprint-ref:goal-{operation.value}",
            {"goal_ref": goal_ref, "request": request_payload},
        )
        with self._locks.acquire("goal-journal"):
            entries = self._load_entries()
            replay = self._idempotent_replay(entries, idempotency_ref, fingerprint)
            if replay is not None:
                return replay
            latest = self._latest_by_goal(entries)
            current = latest.get(goal_ref)
            if current is None:
                raise GoalNotFoundError("GOAL_NOT_FOUND")
            if current.version != expected_version:
                raise GoalVersionConflictError("GOAL_VERSION_CONFLICT")
            updated = mutate(current.model_copy(deep=True))
            self._append(
                entries,
                operation=operation,
                goal=updated,
                idempotency_ref=idempotency_ref,
                request_fingerprint_ref=fingerprint,
                approval_ref=approval_binding.approval_ref,
                approval_decision_ref=approval_binding.approval_decision_ref,
            )
            return updated.model_copy(deep=True)

    @staticmethod
    def _edited_goal(
        current: PersistentGoal, request: GoalEditRequest
    ) -> PersistentGoal:
        if current.state in {
            GoalState.verified_complete.value,
            GoalState.cancelled.value,
            GoalState.cleared.value,
        }:
            raise GoalTransitionDeniedError("GOAL_TERMINAL_EDIT_DENIED")
        updates = {
            field_name: value
            for field_name, value in request.model_dump(
                exclude={"expected_version"}
            ).items()
            if value is not None
        }
        updates.update(version=current.version + 1, updated_at=utc_now())
        return PersistentGoal.model_validate(
            current.model_copy(update=updates).model_dump()
        )

    @staticmethod
    def _transitioned_goal(
        current: PersistentGoal,
        request: GoalTransitionRequest,
        *,
        completion_verified: bool,
        completion_plan_ref: str | None,
    ) -> PersistentGoal:
        allowed: dict[str, set[str]] = {
            GoalState.active.value: {
                GoalTransitionKind.pause.value,
                GoalTransitionKind.block.value,
                GoalTransitionKind.wait.value,
                GoalTransitionKind.cancel.value,
                GoalTransitionKind.clear.value,
                GoalTransitionKind.request_completion.value,
            },
            GoalState.paused.value: {
                GoalTransitionKind.resume.value,
                GoalTransitionKind.cancel.value,
                GoalTransitionKind.clear.value,
            },
            GoalState.blocked.value: {
                GoalTransitionKind.resume.value,
                GoalTransitionKind.wait.value,
                GoalTransitionKind.cancel.value,
                GoalTransitionKind.clear.value,
            },
            GoalState.waiting.value: {
                GoalTransitionKind.resume.value,
                GoalTransitionKind.block.value,
                GoalTransitionKind.cancel.value,
                GoalTransitionKind.clear.value,
            },
            GoalState.complete_requested.value: {
                GoalTransitionKind.verify_completion.value,
                GoalTransitionKind.resume.value,
                GoalTransitionKind.block.value,
                GoalTransitionKind.cancel.value,
                GoalTransitionKind.clear.value,
            },
            GoalState.verified_complete.value: {GoalTransitionKind.clear.value},
            GoalState.cancelled.value: {GoalTransitionKind.clear.value},
            GoalState.cleared.value: set(),
        }
        if request.transition not in allowed[current.state]:
            raise GoalTransitionDeniedError("GOAL_TRANSITION_DENIED")
        if (
            request.transition == GoalTransitionKind.verify_completion.value
            and not completion_verified
        ):
            raise GoalTransitionDeniedError("GOAL_COMPLETION_NOT_VERIFIED")
        target = {
            GoalTransitionKind.pause.value: GoalState.paused.value,
            GoalTransitionKind.resume.value: GoalState.active.value,
            GoalTransitionKind.block.value: GoalState.blocked.value,
            GoalTransitionKind.wait.value: GoalState.waiting.value,
            GoalTransitionKind.cancel.value: GoalState.cancelled.value,
            GoalTransitionKind.clear.value: GoalState.cleared.value,
            GoalTransitionKind.request_completion.value: (
                GoalState.complete_requested.value
            ),
            GoalTransitionKind.verify_completion.value: (
                GoalState.verified_complete.value
            ),
        }[request.transition]
        updates: dict[str, Any] = {
            "state": target,
            "version": current.version + 1,
            "updated_at": utc_now(),
            "evidence_refs": list(
                dict.fromkeys([*current.evidence_refs, *request.evidence_refs])
            ),
        }
        if request.completion_evidence is not None:
            updates.update(
                completion_run_ref=request.completion_evidence.run_ref,
                completion_plan_ref=completion_plan_ref,
                completion_evidence_ref=request.completion_evidence.evidence_ref,
                completion_receipt_ref=request.completion_evidence.receipt_ref,
                completion_proof_ref=request.completion_evidence.proof_ref,
                completion_verifier_ref=request.completion_evidence.verifier_ref,
                evidence_refs=list(
                    dict.fromkeys(
                        [
                            *updates["evidence_refs"],
                            request.completion_evidence.evidence_ref,
                        ]
                    )
                ),
            )
        return PersistentGoal.model_validate(
            current.model_copy(update=updates).model_dump()
        )

    @staticmethod
    def _idempotent_replay(
        entries: list[GoalJournalEntry],
        idempotency_ref: str,
        request_fingerprint_ref: str,
    ) -> PersistentGoal | None:
        for entry in entries:
            if entry.idempotency_ref != idempotency_ref:
                continue
            if entry.request_fingerprint_ref != request_fingerprint_ref:
                raise GoalIdempotencyConflictError("GOAL_IDEMPOTENCY_CONFLICT")
            return entry.goal.model_copy(deep=True)
        return None

    @staticmethod
    def _latest_by_goal(
        entries: list[GoalJournalEntry],
    ) -> dict[str, PersistentGoal]:
        latest: dict[str, PersistentGoal] = {}
        for entry in entries:
            latest[entry.goal_ref] = entry.goal
        return latest

    def _append(
        self,
        entries: list[GoalJournalEntry],
        *,
        operation: GoalJournalOperation,
        goal: PersistentGoal,
        idempotency_ref: str,
        request_fingerprint_ref: str,
        approval_ref: str,
        approval_decision_ref: str,
    ) -> None:
        if len(entries) >= MAX_GOAL_JOURNAL_ENTRIES:
            raise GoalRuntimeError("GOAL_JOURNAL_CAPACITY_EXCEEDED")
        previous = entries[-1].entry_hash_ref if entries else None
        draft = GoalJournalEntry(
            entry_ref=_sha256_ref(
                "goal-journal-entry-ref",
                {
                    "goal_ref": goal.goal_ref,
                    "version": goal.version,
                    "operation": operation.value,
                },
            ),
            operation=operation,
            goal_ref=goal.goal_ref,
            goal_version=goal.version,
            idempotency_ref=idempotency_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            approval_ref=approval_ref,
            approval_decision_ref=approval_decision_ref,
            recorded_at=utc_now(),
            goal=goal,
            previous_entry_hash_ref=previous,
            entry_hash_ref="entry-hash-ref:pending",
        )
        entry = draft.model_copy(
            update={"entry_hash_ref": self._entry_hash(draft)}
        )
        self._write_entries([*entries, entry])

    @staticmethod
    def _entry_hash(entry: GoalJournalEntry) -> str:
        payload = entry.model_dump(mode="json")
        payload.pop("entry_hash_ref", None)
        return _sha256_ref("entry-hash-ref:goal-journal", payload)

    def _load_entries(self) -> list[GoalJournalEntry]:
        if not self.path.exists():
            return []
        try:
            if self.path.stat().st_size > MAX_GOAL_JOURNAL_BYTES:
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_BYTE_CAPACITY_EXCEEDED"
                )
        except OSError as exc:
            raise GoalRuntimeCorruptionError("GOAL_JOURNAL_CORRUPT") from exc
        entries: list[GoalJournalEntry] = []
        previous: str | None = None
        versions: dict[str, int] = {}
        idempotency: dict[str, str] = {}
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
            for raw_line in lines:
                if not raw_line.strip():
                    continue
                entry = GoalJournalEntry.model_validate_json(raw_line)
                if entry.previous_entry_hash_ref != previous:
                    raise GoalRuntimeCorruptionError("GOAL_JOURNAL_HASH_CHAIN_MISMATCH")
                if entry.entry_hash_ref != self._entry_hash(entry):
                    raise GoalRuntimeCorruptionError("GOAL_JOURNAL_ENTRY_HASH_MISMATCH")
                expected_entry_ref = _sha256_ref(
                    "goal-journal-entry-ref",
                    {
                        "goal_ref": entry.goal_ref,
                        "version": entry.goal_version,
                        "operation": entry.operation,
                    },
                )
                if entry.entry_ref != expected_entry_ref:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_ENTRY_REF_BINDING_MISMATCH"
                    )
                expected_version = versions.get(entry.goal_ref, 0) + 1
                if entry.goal_version != expected_version:
                    raise GoalRuntimeCorruptionError("GOAL_JOURNAL_VERSION_GAP")
                known_fingerprint = idempotency.get(entry.idempotency_ref)
                if known_fingerprint is not None:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_DUPLICATE_IDEMPOTENCY_REF"
                    )
                versions[entry.goal_ref] = entry.goal_version
                idempotency[entry.idempotency_ref] = entry.request_fingerprint_ref
                entries.append(entry)
                if len(entries) > MAX_GOAL_JOURNAL_ENTRIES:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_ENTRY_CAPACITY_EXCEEDED"
                    )
                previous = entry.entry_hash_ref
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError("GOAL_JOURNAL_CORRUPT") from exc
        return entries

    def _write_entries(self, entries: list[GoalJournalEntry]) -> None:
        content = "".join(entry.model_dump_json() + "\n" for entry in entries)
        if (
            len(entries) > MAX_GOAL_JOURNAL_ENTRIES
            or len(content.encode("utf-8")) > MAX_GOAL_JOURNAL_BYTES
        ):
            raise GoalRuntimeError("GOAL_JOURNAL_CAPACITY_EXCEEDED")
        _atomic_write(self.path, content)


class _DurableRunEventStore:
    def __init__(
        self,
        state_dir: str | Path,
        *,
        retention_limit: int = DEFAULT_RUN_EVENT_RETENTION,
    ) -> None:
        if not 2 <= retention_limit <= MAX_RUN_EVENT_RETENTION:
            raise ValueError("RUN_EVENT_RETENTION_LIMIT_INVALID")
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / "run_events.jsonl"
        self.idempotency_path = self.state_dir / "run_event_idempotency.jsonl"
        self.reservations_path = (
            self.state_dir / "run_event_projection_reservations.jsonl"
        )
        self.retention_limit = retention_limit
        self._locks = FileSingleWriterLockManager(self.state_dir / ".locks")

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        with self._locks.acquire("run-events"):
            yield

    def append(self, request: DurableRunEventAppendRequest) -> DurableRunEvent:
        validated = DurableRunEventAppendRequest.model_validate(request.model_dump())
        with self.exclusive():
            return self._append_locked(validated)

    def reserve_runtime_projection(
        self,
        existing_record: RuntimeInvocationRecord | None,
        *,
        operation_idempotency_ref: str,
    ) -> str:
        """Durably reserve projection capacity without holding the event lock."""

        validate_execution_ref(
            operation_idempotency_ref,
            "operation_idempotency_ref",
        )
        reservation_ref = _sha256_ref(
            "run-event-reservation-ref",
            {
                "operation_idempotency_ref": operation_idempotency_ref,
            },
        )
        with self.exclusive():
            events = self._load_events()
            tombstones = self._load_idempotency_tombstones(events)
            now = utc_now()
            reservations = {
                ref: reservation
                for ref, reservation in (
                    self._load_projection_reservations().items()
                )
                if reservation.expires_at > now
            }
            missing_key_refs = self._missing_runtime_projection_key_refs(
                existing_record,
                tombstones,
            )
            required_slots = (
                len(missing_key_refs) if missing_key_refs is not None else 2
            )
            existing_reservation = reservations.get(reservation_ref)
            reserved_slots = sum(
                reservation.slot_count
                for ref, reservation in reservations.items()
                if ref != reservation_ref
            )
            if (
                len(tombstones) + reserved_slots + required_slots
                > MAX_RUN_EVENT_IDEMPOTENCY_RECORDS
            ):
                raise GoalRuntimeError(
                    "RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED"
                )
            reservation = self._build_projection_reservation(
                reservation_ref,
                operation_idempotency_ref=operation_idempotency_ref,
                holder_count=(
                    existing_reservation.holder_count + 1
                    if existing_reservation is not None
                    else 1
                ),
                slot_count=required_slots,
                allowed_event_key_refs=missing_key_refs or [],
                reserved_at=now,
            )
            reservations[reservation_ref] = reservation
            self._write_projection_reservations(reservations.values())
        return reservation_ref

    def bind_runtime_projection_reservation(
        self,
        reservation_ref: str,
        record: RuntimeInvocationRecord,
    ) -> None:
        validate_execution_ref(reservation_ref, "reservation_ref")
        loaded_reservations = self._load_projection_reservations()
        now = utc_now()
        reservations = {
            ref: reservation
            for ref, reservation in loaded_reservations.items()
            if reservation.expires_at > now
        }
        if len(reservations) != len(loaded_reservations):
            self._write_projection_reservations(reservations.values())
        reservation = reservations.get(reservation_ref)
        tombstones = self._load_idempotency_tombstones(
            self._load_events()
        )
        missing_key_refs = self._missing_runtime_projection_key_refs(
            record,
            tombstones,
        )
        if missing_key_refs is None:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RECEIPT_REQUIRED"
            )
        if reservation is None:
            if not missing_key_refs:
                return
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RESERVATION_MISSING"
            )
        if len(missing_key_refs) > reservation.slot_count:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RESERVATION_TOO_SMALL"
            )
        reservations[reservation_ref] = self._build_projection_reservation(
            reservation_ref,
            operation_idempotency_ref=reservation.operation_idempotency_ref,
            holder_count=reservation.holder_count,
            slot_count=len(missing_key_refs),
            allowed_event_key_refs=missing_key_refs,
            reserved_at=reservation.reserved_at,
        )
        self._write_projection_reservations(reservations.values())

    def release_runtime_projection_reservation(
        self,
        reservation_ref: str,
    ) -> None:
        validate_execution_ref(reservation_ref, "reservation_ref")
        with self.exclusive():
            reservations = self._load_projection_reservations()
            reservation = reservations.get(reservation_ref)
            if reservation is not None:
                if reservation.holder_count > 1:
                    reservations[reservation_ref] = (
                        self._build_projection_reservation(
                            reservation_ref,
                            operation_idempotency_ref=(
                                reservation.operation_idempotency_ref
                            ),
                            holder_count=reservation.holder_count - 1,
                            slot_count=reservation.slot_count,
                            allowed_event_key_refs=(
                                reservation.allowed_event_key_refs
                            ),
                            reserved_at=reservation.reserved_at,
                        )
                    )
                else:
                    reservations.pop(reservation_ref)
                self._write_projection_reservations(
                    reservations.values()
                )

    def _append_locked(
        self,
        validated: DurableRunEventAppendRequest,
        *,
        reservation_ref: str | None = None,
    ) -> DurableRunEvent:
        events = self._load_events()
        tombstones = self._load_idempotency_tombstones(events)
        loaded_reservations = self._load_projection_reservations()
        reservations = {
            ref: reservation
            for ref, reservation in loaded_reservations.items()
            if reservation.expires_at > utc_now()
        }
        if len(reservations) != len(loaded_reservations):
            self._write_projection_reservations(reservations.values())
        key = (validated.run_ref, validated.idempotency_ref)
        event_key_ref = self._event_key_ref(*key)
        reservation = (
            reservations.get(reservation_ref)
            if reservation_ref is not None
            else None
        )
        expected_fingerprint = self._request_fingerprint(validated)
        prior = tombstones.get(key)
        if prior is not None:
            if prior.request_fingerprint_ref != expected_fingerprint:
                raise GoalIdempotencyConflictError(
                    "RUN_EVENT_IDEMPOTENCY_CONFLICT"
                )
            self._write_idempotency_tombstones(tombstones.values())
            return prior.event.model_copy(deep=True)
        if reservation_ref is not None and (
            reservation is None
            or event_key_ref not in reservation.allowed_event_key_refs
        ):
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RESERVATION_BINDING_MISMATCH"
            )
        reserved_slots = sum(
            item.slot_count for item in reservations.values()
        )
        if (
            reservation is None
            and len(tombstones) + reserved_slots
            >= MAX_RUN_EVENT_IDEMPOTENCY_RECORDS
        ):
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED")

        same_run = [event for event in events if event.run_ref == validated.run_ref]
        if same_run and same_run[-1].event_kind in TERMINAL_RUN_EVENT_KINDS:
            raise GoalTransitionDeniedError("RUN_EVENT_TERMINAL_STREAM_FENCE")
        if same_run and same_run[-1].run_type != validated.run_type:
            raise GoalRuntimeCorruptionError("RUN_EVENT_TYPE_SUBSTITUTION")
        if validated.event_kind == DurableRunEventKind.completion_verified.value:
            receipt_candidates = [
                *same_run,
                *(
                    tombstone.event
                    for tombstone in tombstones.values()
                    if tombstone.event.run_ref == validated.run_ref
                    and tombstone.event not in same_run
                ),
            ]
            if not any(
                event.event_kind == DurableRunEventKind.receipt_recorded.value
                and event.goal_ref == validated.goal_ref
                and set(validated.receipt_refs).issubset(event.receipt_refs)
                and set(validated.proof_refs).issubset(event.proof_refs)
                for event in receipt_candidates
            ):
                raise GoalTransitionDeniedError(
                    "RUN_EVENT_COMPLETION_RECEIPT_NOT_FOUND"
                )
        sequence = same_run[-1].sequence + 1 if same_run else 1
        predecessor = same_run[-1].event_hash_ref if same_run else None
        draft = DurableRunEvent(
            event_ref=_sha256_ref(
                "runtime-run-event-ref",
                {
                    "run_ref": validated.run_ref,
                    "sequence": sequence,
                    "event_kind": validated.event_kind,
                },
            ),
            run_ref=validated.run_ref,
            run_type=validated.run_type,
            sequence=sequence,
            recorded_at=utc_now(),
            event_kind=validated.event_kind,
            safe_summary=validated.safe_summary,
            proof_refs=validated.proof_refs,
            receipt_refs=validated.receipt_refs,
            goal_ref=validated.goal_ref,
            plan_ref=validated.plan_ref,
            idempotency_ref=validated.idempotency_ref,
            authority_decision_ref=validated.authority_decision_ref,
            predecessor_hash_ref=predecessor,
            event_hash_ref="event-hash-ref:pending",
        )
        event = draft.model_copy(
            update={"event_hash_ref": self._event_hash(draft)}
        )
        next_events = self._apply_retention(
            [*events, event], validated.run_ref
        )
        self._write_events(next_events)
        tombstone = self._build_idempotency_tombstone(
            event, expected_fingerprint
        )
        tombstones[key] = tombstone
        self._write_idempotency_tombstones(tombstones.values())
        if reservation is not None and reservation_ref is not None:
            remaining = [
                ref
                for ref in reservation.allowed_event_key_refs
                if ref != event_key_ref
            ]
            if remaining:
                reservations[reservation_ref] = (
                    self._build_projection_reservation(
                        reservation_ref,
                        operation_idempotency_ref=(
                            reservation.operation_idempotency_ref
                        ),
                        holder_count=reservation.holder_count,
                        slot_count=len(remaining),
                        allowed_event_key_refs=remaining,
                        reserved_at=reservation.reserved_at,
                    )
                )
            else:
                reservations.pop(reservation_ref, None)
            self._write_projection_reservations(
                reservations.values()
            )
        return event.model_copy(deep=True)

    def replay(
        self,
        run_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = MAX_REPLAY_EVENTS,
    ) -> RunEventReplayReadModel:
        validate_execution_ref(run_ref, "run_ref")
        if after_sequence < 0:
            raise ValueError("RUN_EVENT_CURSOR_INVALID")
        bounded_limit = max(1, min(int(limit), MAX_REPLAY_EVENTS))
        same_run = [
            event for event in self._load_events() if event.run_ref == run_ref
        ]
        if not same_run:
            return RunEventReplayReadModel(
                status=RunEventReplayStatus.unknown_run,
                run_ref=run_ref,
                after_sequence=after_sequence,
                next_cursor=after_sequence,
                last_sequence=0,
                events=[],
            )
        first = same_run[0].sequence
        last = same_run[-1].sequence
        if after_sequence < first - 1:
            return RunEventReplayReadModel(
                status=RunEventReplayStatus.retention_loss,
                run_ref=run_ref,
                after_sequence=after_sequence,
                next_cursor=first - 1,
                first_retained_sequence=first,
                last_sequence=last,
                retention_anchor_hash_ref=same_run[0].predecessor_hash_ref,
                events=[],
                gap_detected=True,
            )
        if after_sequence > last:
            return RunEventReplayReadModel(
                status=RunEventReplayStatus.stale_cursor,
                run_ref=run_ref,
                after_sequence=after_sequence,
                next_cursor=last,
                first_retained_sequence=first,
                last_sequence=last,
                retention_anchor_hash_ref=same_run[0].predecessor_hash_ref,
                events=[],
                gap_detected=True,
            )
        selected = [
            event for event in same_run if event.sequence > after_sequence
        ][:bounded_limit]
        next_cursor = selected[-1].sequence if selected else after_sequence
        return RunEventReplayReadModel(
            status=RunEventReplayStatus.ok,
            run_ref=run_ref,
            after_sequence=after_sequence,
            next_cursor=next_cursor,
            first_retained_sequence=first,
            last_sequence=last,
            retention_anchor_hash_ref=same_run[0].predecessor_hash_ref,
            events=selected,
        )

    def summaries(self) -> list[RunEventStreamSummary]:
        grouped: dict[str, list[DurableRunEvent]] = {}
        for event in self._load_events():
            grouped.setdefault(event.run_ref, []).append(event)
        summaries = [
            RunEventStreamSummary(
                run_ref=run_ref,
                run_type=events[0].run_type,
                first_retained_sequence=events[0].sequence,
                last_sequence=events[-1].sequence,
                retained_event_count=len(events),
                retention_anchor_hash_ref=events[0].predecessor_hash_ref,
                terminal_event_kind=(
                    events[-1].event_kind
                    if events[-1].event_kind
                    in {
                        DurableRunEventKind.cancelled.value,
                        DurableRunEventKind.completion_verified.value,
                        DurableRunEventKind.failed_terminal.value,
                        DurableRunEventKind.dead_lettered.value,
                    }
                    else None
                ),
            )
            for run_ref, events in grouped.items()
        ]
        summaries.sort(key=lambda item: item.run_ref)
        return summaries

    def retained_events(
        self,
        *,
        run_ref: str | None = None,
        limit: int = MAX_REPLAY_EVENTS,
    ) -> list[DurableRunEvent]:
        if run_ref is not None:
            validate_execution_ref(run_ref, "run_ref")
        bounded_limit = max(1, min(int(limit), MAX_REPLAY_EVENTS))
        events = self._load_events()
        if run_ref is not None:
            events = [event for event in events if event.run_ref == run_ref]
        return [event.model_copy(deep=True) for event in events[-bounded_limit:]]

    def has_completion_evidence(
        self,
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> bool:
        validate_execution_ref(run_ref, "run_ref")
        events = self._load_events()
        tombstones = self._load_idempotency_tombstones(events)
        return self._completion_receipt_event(
            events,
            tombstones,
            run_ref=run_ref,
            receipt_ref=receipt_ref,
            proof_ref=proof_ref,
            goal_ref=goal_ref,
        ) is not None

    def assert_completion_appendable(
        self,
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> DurableRunEvent:
        events = self._load_events()
        tombstones = self._load_idempotency_tombstones(events)
        same_run = [event for event in events if event.run_ref == run_ref]
        matched = self._completion_receipt_event(
            events,
            tombstones,
            run_ref=run_ref,
            receipt_ref=receipt_ref,
            proof_ref=proof_ref,
            goal_ref=goal_ref,
        )
        if matched is None:
            raise GoalTransitionDeniedError(
                "GOAL_COMPLETION_DURABLE_RECEIPT_NOT_FOUND"
            )
        if same_run[-1].event_kind in TERMINAL_RUN_EVENT_KINDS:
            raise GoalTransitionDeniedError(
                "GOAL_COMPLETION_TERMINAL_STREAM_FENCE"
            )
        return matched.model_copy(deep=True)

    @staticmethod
    def _completion_receipt_event(
        events: list[DurableRunEvent],
        tombstones: dict[
            tuple[str, str],
            RunEventIdempotencyTombstone,
        ],
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> DurableRunEvent | None:
        candidates = [
            *events,
            *(
                tombstone.event
                for tombstone in tombstones.values()
                if tombstone.event not in events
            ),
        ]
        return next(
            (
                event
                for event in candidates
                if event.run_ref == run_ref
                and event.goal_ref == goal_ref
                and event.event_kind
                == DurableRunEventKind.receipt_recorded.value
                and receipt_ref in event.receipt_refs
                and proof_ref in event.proof_refs
            ),
            None,
        )

    def run_type(self, run_ref: str) -> AcceptedLocalRunType:
        validate_execution_ref(run_ref, "run_ref")
        for event in self._load_events():
            if event.run_ref == run_ref:
                return AcceptedLocalRunType(event.run_type)
        raise RunEventNotFoundError("RUN_EVENT_STREAM_NOT_FOUND")

    @staticmethod
    def _request_fingerprint(request: DurableRunEventAppendRequest) -> str:
        return _sha256_ref(
            "request-fingerprint-ref:run-event",
            request.model_dump(mode="json"),
        )

    @staticmethod
    def _event_request_payload(event: DurableRunEvent) -> dict[str, Any]:
        return {
            "run_ref": event.run_ref,
            "run_type": event.run_type,
            "event_kind": event.event_kind,
            "safe_summary": event.safe_summary,
            "proof_refs": event.proof_refs,
            "receipt_refs": event.receipt_refs,
            "goal_ref": event.goal_ref,
            "plan_ref": event.plan_ref,
            "idempotency_ref": event.idempotency_ref,
            "authority_decision_ref": event.authority_decision_ref,
        }

    @staticmethod
    def _event_hash(event: DurableRunEvent) -> str:
        payload = event.model_dump(mode="json")
        payload.pop("event_hash_ref", None)
        return _sha256_ref("event-hash-ref:durable-run", payload)

    @staticmethod
    def _tombstone_hash(tombstone: RunEventIdempotencyTombstone) -> str:
        payload = tombstone.model_dump(mode="json")
        payload.pop("tombstone_hash_ref", None)
        return _sha256_ref("tombstone-hash-ref:run-event-idempotency", payload)

    @staticmethod
    def _reservation_hash(
        reservation: RunEventProjectionReservation,
    ) -> str:
        payload = reservation.model_dump(mode="json")
        payload.pop("reservation_hash_ref", None)
        return _sha256_ref(
            "reservation-hash-ref:run-event-projection",
            payload,
        )

    @staticmethod
    def _event_key_ref(run_ref: str, idempotency_ref: str) -> str:
        return _sha256_ref(
            "run-event-key-ref",
            {
                "run_ref": run_ref,
                "idempotency_ref": idempotency_ref,
            },
        )

    def _missing_runtime_projection_key_refs(
        self,
        record: RuntimeInvocationRecord | None,
        tombstones: dict[
            tuple[str, str],
            RunEventIdempotencyTombstone,
        ],
    ) -> list[str] | None:
        if record is None or record.receipt is None:
            return None
        run_ref = record.invocation_ref
        expected_keys = (
            (
                run_ref,
                _sha256_ref(
                    "idempotency-ref:runtime-run-started",
                    {"invocation_ref": run_ref},
                ),
            ),
            (
                run_ref,
                _sha256_ref(
                    "idempotency-ref:runtime-receipt-recorded",
                    {
                        "invocation_ref": run_ref,
                        "receipt_ref": record.receipt.receipt_ref,
                    },
                ),
            ),
        )
        return [
            self._event_key_ref(*key)
            for key in expected_keys
            if key not in tombstones
        ]

    def unprojected_runtime_invocations(
        self,
        records: Iterable[RuntimeInvocationRecord],
    ) -> list[RuntimeInvocationRecord]:
        from ultimate_ai_agent.core.runtime_gateway.contracts import (
            RuntimeInvocationRecord,
            RuntimeInvocationStatus,
        )

        candidates: list[RuntimeInvocationRecord] = []
        with self.exclusive():
            events = self._load_events()
            tombstones = self._load_idempotency_tombstones(events)
            for record in records:
                validated = RuntimeInvocationRecord.model_validate(
                    record.model_dump()
                )
                if (
                    validated.receipt is None
                    or validated.status
                    != RuntimeInvocationStatus.receipt_recorded.value
                ):
                    continue
                missing_key_refs = self._missing_runtime_projection_key_refs(
                    validated,
                    tombstones,
                )
                if missing_key_refs:
                    candidates.append(validated)
        return candidates

    def _build_projection_reservation(
        self,
        reservation_ref: str,
        *,
        operation_idempotency_ref: str,
        holder_count: int = 1,
        slot_count: int,
        allowed_event_key_refs: list[str],
        reserved_at: datetime | None = None,
    ) -> RunEventProjectionReservation:
        effective_reserved_at = reserved_at or utc_now()
        draft = RunEventProjectionReservation(
            reservation_ref=reservation_ref,
            operation_idempotency_ref=operation_idempotency_ref,
            holder_count=holder_count,
            slot_count=slot_count,
            allowed_event_key_refs=allowed_event_key_refs,
            reserved_at=effective_reserved_at,
            expires_at=effective_reserved_at
            + timedelta(
                seconds=RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS
            ),
            reservation_hash_ref="reservation-hash-ref:pending",
        )
        return draft.model_copy(
            update={
                "reservation_hash_ref": self._reservation_hash(draft)
            }
        )

    def _load_projection_reservations(
        self,
    ) -> dict[str, RunEventProjectionReservation]:
        reservations: dict[str, RunEventProjectionReservation] = {}
        try:
            if not self.reservations_path.exists():
                return reservations
            for raw_line in self.reservations_path.read_text(
                encoding="utf-8"
            ).splitlines():
                if not raw_line.strip():
                    continue
                reservation = (
                    RunEventProjectionReservation.model_validate_json(
                        raw_line
                    )
                )
                if reservation.reservation_hash_ref != (
                    self._reservation_hash(reservation)
                ):
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_PROJECTION_RESERVATION_HASH_MISMATCH"
                    )
                expected_reservation_ref = _sha256_ref(
                    "run-event-reservation-ref",
                    {
                        "operation_idempotency_ref": (
                            reservation.operation_idempotency_ref
                        )
                    },
                )
                if reservation.reservation_ref != expected_reservation_ref:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_PROJECTION_RESERVATION_REF_MISMATCH"
                    )
                if reservation.reservation_ref in reservations:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_PROJECTION_RESERVATION_DUPLICATE"
                    )
                reservations[reservation.reservation_ref] = reservation
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RESERVATION_STORE_CORRUPT"
            ) from exc
        return reservations

    def _write_projection_reservations(
        self,
        reservations: Iterable[RunEventProjectionReservation],
    ) -> None:
        content = "".join(
            reservation.model_dump_json() + "\n"
            for reservation in reservations
        )
        _atomic_write(self.reservations_path, content)

    def _build_idempotency_tombstone(
        self,
        event: DurableRunEvent,
        request_fingerprint_ref: str,
    ) -> RunEventIdempotencyTombstone:
        draft = RunEventIdempotencyTombstone(
            run_ref=event.run_ref,
            idempotency_ref=event.idempotency_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            event=event,
            tombstone_hash_ref="tombstone-hash-ref:pending",
        )
        return draft.model_copy(
            update={"tombstone_hash_ref": self._tombstone_hash(draft)}
        )

    def _load_idempotency_tombstones(
        self,
        events: list[DurableRunEvent],
    ) -> dict[tuple[str, str], RunEventIdempotencyTombstone]:
        tombstones: dict[tuple[str, str], RunEventIdempotencyTombstone] = {}
        try:
            if self.idempotency_path.exists():
                for raw_line in self.idempotency_path.read_text(
                    encoding="utf-8"
                ).splitlines():
                    if not raw_line.strip():
                        continue
                    tombstone = RunEventIdempotencyTombstone.model_validate_json(
                        raw_line
                    )
                    if tombstone.tombstone_hash_ref != self._tombstone_hash(
                        tombstone
                    ):
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_IDEMPOTENCY_TOMBSTONE_HASH_MISMATCH"
                        )
                    key = (tombstone.run_ref, tombstone.idempotency_ref)
                    if key in tombstones:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_IDEMPOTENCY_TOMBSTONE_DUPLICATE"
                        )
                    tombstones[key] = tombstone
            for event in events:
                key = (event.run_ref, event.idempotency_ref)
                fingerprint = _sha256_ref(
                    "request-fingerprint-ref:run-event",
                    self._event_request_payload(event),
                )
                known = tombstones.get(key)
                if known is not None:
                    if (
                        known.request_fingerprint_ref != fingerprint
                        or known.event != event
                    ):
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_IDEMPOTENCY_TOMBSTONE_EVENT_MISMATCH"
                        )
                    continue
                tombstones[key] = self._build_idempotency_tombstone(
                    event, fingerprint
                )
            if len(tombstones) > MAX_RUN_EVENT_IDEMPOTENCY_RECORDS:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED"
                )
            self._validate_tombstone_event_history(tombstones.values())
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_IDEMPOTENCY_STORE_CORRUPT"
            ) from exc
        return tombstones

    def _validate_tombstone_event_history(
        self,
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        grouped: dict[str, list[DurableRunEvent]] = {}
        for tombstone in tombstones:
            event = tombstone.event
            if event.event_hash_ref != self._event_hash(event):
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_IDEMPOTENCY_EVENT_HASH_MISMATCH"
                )
            expected_event_ref = _sha256_ref(
                "runtime-run-event-ref",
                {
                    "run_ref": event.run_ref,
                    "sequence": event.sequence,
                    "event_kind": event.event_kind,
                },
            )
            if event.event_ref != expected_event_ref:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_IDEMPOTENCY_EVENT_REF_MISMATCH"
                )
            grouped.setdefault(event.run_ref, []).append(event)
        for same_run in grouped.values():
            same_run.sort(key=lambda event: event.sequence)
            if same_run[0].sequence != 1:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_IDEMPOTENCY_HISTORY_ORIGIN_MISSING"
                )
            for index, event in enumerate(same_run):
                if event.sequence != index + 1:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_HISTORY_SEQUENCE_GAP"
                    )
                if index == 0:
                    if event.predecessor_hash_ref is not None:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_IDEMPOTENCY_HISTORY_PREDECESSOR_INVALID"
                        )
                    continue
                previous = same_run[index - 1]
                if event.predecessor_hash_ref != previous.event_hash_ref:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_HISTORY_HASH_GAP"
                    )
                if event.run_type != previous.run_type:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_HISTORY_TYPE_SUBSTITUTION"
                    )
                if previous.event_kind in TERMINAL_RUN_EVENT_KINDS:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_HISTORY_TERMINAL_FENCE"
                    )

    def _load_events(self) -> list[DurableRunEvent]:
        if not self.path.exists():
            self._assert_no_orphaned_idempotency_history()
            return []
        events: list[DurableRunEvent] = []
        grouped: dict[str, list[DurableRunEvent]] = {}
        idempotency: set[tuple[str, str]] = set()
        try:
            raw_content = self.path.read_text(encoding="utf-8")
            if not raw_content.strip():
                self._assert_no_orphaned_idempotency_history()
                return []
            for raw_line in raw_content.splitlines():
                if not raw_line.strip():
                    continue
                event = DurableRunEvent.model_validate_json(raw_line)
                if event.event_hash_ref != self._event_hash(event):
                    raise GoalRuntimeCorruptionError("RUN_EVENT_HASH_MISMATCH")
                expected_event_ref = _sha256_ref(
                    "runtime-run-event-ref",
                    {
                        "run_ref": event.run_ref,
                        "sequence": event.sequence,
                        "event_kind": event.event_kind,
                    },
                )
                if event.event_ref != expected_event_ref:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_REF_BINDING_MISMATCH"
                    )
                key = (event.run_ref, event.idempotency_ref)
                if key in idempotency:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_DUPLICATE_IDEMPOTENCY_REF"
                    )
                idempotency.add(key)
                grouped.setdefault(event.run_ref, []).append(event)
                events.append(event)
            for same_run in grouped.values():
                for previous, current in zip(same_run, same_run[1:]):
                    if current.sequence != previous.sequence + 1:
                        raise GoalRuntimeCorruptionError("RUN_EVENT_SEQUENCE_GAP")
                    if current.predecessor_hash_ref != previous.event_hash_ref:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_PREDECESSOR_HASH_MISMATCH"
                        )
                    if current.run_type != previous.run_type:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_TYPE_SUBSTITUTION"
                        )
                if same_run[0].sequence == 1:
                    if same_run[0].predecessor_hash_ref is not None:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_FIRST_PREDECESSOR_INVALID"
                        )
                elif same_run[0].predecessor_hash_ref is None:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_RETENTION_ANCHOR_MISSING"
                    )
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError("RUN_EVENT_STORE_CORRUPT") from exc
        return events

    def _assert_no_orphaned_idempotency_history(self) -> None:
        try:
            if (
                self.idempotency_path.exists()
                and self.idempotency_path.read_text(encoding="utf-8").strip()
            ):
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_JOURNAL_MISSING_WITH_IDEMPOTENCY_HISTORY"
                )
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_IDEMPOTENCY_STORE_CORRUPT"
            ) from exc

    def _apply_retention(
        self, events: list[DurableRunEvent], run_ref: str
    ) -> list[DurableRunEvent]:
        same_run = [event for event in events if event.run_ref == run_ref]
        if len(same_run) <= self.retention_limit:
            return events
        keep_refs = {
            event.event_ref for event in same_run[-self.retention_limit :]
        }
        return [
            event
            for event in events
            if event.run_ref != run_ref or event.event_ref in keep_refs
        ]

    def _write_events(self, events: list[DurableRunEvent]) -> None:
        content = "".join(event.model_dump_json() + "\n" for event in events)
        _atomic_write(self.path, content)

    def _write_idempotency_tombstones(
        self,
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        content = "".join(
            tombstone.model_dump_json() + "\n" for tombstone in tombstones
        )
        _atomic_write(self.idempotency_path, content)


class DurableRunEventReader:
    """Read-only facade for durable run evidence."""

    def __init__(self, store: _DurableRunEventStore) -> None:
        self.__store = store

    def replay(
        self,
        run_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = MAX_REPLAY_EVENTS,
    ) -> RunEventReplayReadModel:
        return self.__store.replay(
            run_ref,
            after_sequence=after_sequence,
            limit=limit,
        )

    def summaries(self) -> list[RunEventStreamSummary]:
        return self.__store.summaries()

    def retained_events(
        self,
        *,
        run_ref: str | None = None,
        limit: int = MAX_REPLAY_EVENTS,
    ) -> list[DurableRunEvent]:
        return self.__store.retained_events(run_ref=run_ref, limit=limit)

    def has_completion_evidence(
        self,
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> bool:
        return self.__store.has_completion_evidence(
            run_ref=run_ref,
            receipt_ref=receipt_ref,
            proof_ref=proof_ref,
            goal_ref=goal_ref,
        )

    def run_type(self, run_ref: str) -> AcceptedLocalRunType:
        return self.__store.run_type(run_ref)


class GoalRuntimeService:
    def __init__(
        self,
        state_dir: str | Path,
        *,
        retention_limit: int = DEFAULT_RUN_EVENT_RETENTION,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        state_metadata = os.lstat(self.state_dir)
        if not stat.S_ISDIR(state_metadata.st_mode):
            raise OSError("goal runtime state directory must be a real directory")
        os.chmod(self.state_dir, 0o700)
        self.goals = _GoalJournalStore(self.state_dir)
        self._events = _DurableRunEventStore(
            self.state_dir, retention_limit=retention_limit
        )
        self.events = DurableRunEventReader(self._events)

    @classmethod
    def from_env(cls) -> "GoalRuntimeService":
        configured = os.environ.get(GOAL_RUNTIME_STATE_DIR_ENV, "").strip()
        return cls(
            Path(configured).expanduser()
            if configured
            else DEFAULT_GOAL_RUNTIME_STATE_DIR
        )

    @classmethod
    def for_runtime_store(cls, state_dir: str | Path) -> "GoalRuntimeService":
        configured = os.environ.get(GOAL_RUNTIME_STATE_DIR_ENV, "").strip()
        if configured:
            return cls(Path(configured).expanduser())
        candidate = Path(state_dir)
        if candidate == Path(".uaa") / "runtime-gateway":
            return cls(DEFAULT_GOAL_RUNTIME_STATE_DIR)
        return cls(candidate / "goal_runtime")

    def create_goal(
        self,
        request: GoalCreateRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
    ) -> PersistentGoal:
        self.reconcile_durable_events()
        return self.goals.create(
            request,
            idempotency_ref=idempotency_ref,
            approval_binding=approval_binding,
        )

    def edit_goal(
        self,
        goal_ref: str,
        request: GoalEditRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
    ) -> PersistentGoal:
        self.reconcile_durable_events()
        return self.goals.edit(
            goal_ref,
            request,
            idempotency_ref=idempotency_ref,
            approval_binding=approval_binding,
        )

    def transition_goal(
        self,
        goal_ref: str,
        request: GoalTransitionRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
    ) -> PersistentGoal:
        self.reconcile_durable_events()
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        replayed = self.goals.replay_transition(
            goal_ref,
            validated,
            idempotency_ref=idempotency_ref,
        )
        if replayed is not None:
            if replayed.state == GoalState.verified_complete.value:
                entry = self.goals.transition_entry(
                    goal_ref,
                    validated,
                    idempotency_ref=idempotency_ref,
                )
                if entry is None:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_TRANSITION_REPLAY_ENTRY_MISSING"
                    )
                with self._events.exclusive():
                    self._append_verified_completion_event(
                        replayed,
                        approval_decision_ref=entry.approval_decision_ref,
                    )
            return replayed
        completion_verified = False
        evidence = validated.completion_evidence
        event_lock = (
            self._events.exclusive()
            if evidence is not None
            else nullcontext()
        )
        completion_plan_ref: str | None = None
        with event_lock:
            if evidence is not None:
                current = self.goals.get(goal_ref)
                if evidence.goal_ref != goal_ref:
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_GOAL_REF_MISMATCH"
                    )
                if evidence.goal_version != current.version:
                    raise GoalVersionConflictError(
                        "GOAL_COMPLETION_VERSION_CONFLICT"
                    )
                if evidence.run_ref not in current.links.run_refs:
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_RUN_NOT_LINKED"
                    )
                receipt_event = self._events.assert_completion_appendable(
                    run_ref=evidence.run_ref,
                    receipt_ref=evidence.receipt_ref,
                    proof_ref=evidence.proof_ref,
                    goal_ref=goal_ref,
                )
                completion_plan_ref = receipt_event.plan_ref
                if current.links.plan_refs:
                    if completion_plan_ref is None:
                        raise GoalTransitionDeniedError(
                            "GOAL_COMPLETION_PLAN_BINDING_REQUIRED"
                        )
                    if completion_plan_ref not in current.links.plan_refs:
                        raise GoalTransitionDeniedError(
                            "GOAL_COMPLETION_PLAN_NOT_LINKED"
                        )
                completion_verified = True
            goal = self.goals.transition(
                goal_ref,
                validated,
                idempotency_ref=idempotency_ref,
                approval_binding=approval_binding,
                completion_verified=completion_verified,
                completion_plan_ref=completion_plan_ref,
            )
            if goal.state == GoalState.verified_complete.value:
                self._append_verified_completion_event(
                    goal,
                    approval_decision_ref=approval_binding.approval_decision_ref,
                )
        return goal

    def _reconcile_verified_completion_events(self) -> None:
        with self._events.exclusive():
            for goal in self.goals.list(include_cleared=True):
                completion_bound = all(
                    value is not None
                    for value in (
                        goal.completion_run_ref,
                        goal.completion_receipt_ref,
                        goal.completion_proof_ref,
                        goal.completion_evidence_ref,
                        goal.completion_verifier_ref,
                    )
                )
                if goal.state not in {
                    GoalState.verified_complete.value,
                    GoalState.cleared.value,
                } or not completion_bound:
                    continue
                verified_entry = self.goals.latest_verified_completion_entry(
                    goal.goal_ref
                )
                self._append_verified_completion_event(
                    verified_entry.goal,
                    approval_decision_ref=verified_entry.approval_decision_ref,
                )

    def reconcile_durable_events(self) -> None:
        """Repair deterministic journal-to-event projections on a mutating path."""

        self._reconcile_verified_completion_events()

    def _append_verified_completion_event(
        self,
        goal: PersistentGoal,
        *,
        approval_decision_ref: str,
    ) -> DurableRunEvent:
        if (
            goal.state
            not in {
                GoalState.verified_complete.value,
                GoalState.cleared.value,
            }
            or goal.completion_run_ref is None
            or goal.completion_receipt_ref is None
            or goal.completion_proof_ref is None
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_COMPLETION_EVENT_BINDING_INCOMPLETE"
            )
        return self._events._append_locked(
            DurableRunEventAppendRequest.model_validate(
                {
                    "run_ref": goal.completion_run_ref,
                    "run_type": self._events.run_type(
                        goal.completion_run_ref
                    ),
                    "event_kind": DurableRunEventKind.completion_verified,
                    "safe_summary": (
                        "Deterministic receipt evidence verified the linked "
                        "goal completion."
                    ),
                    "proof_refs": [goal.completion_proof_ref],
                    "receipt_refs": [goal.completion_receipt_ref],
                    "goal_ref": goal.goal_ref,
                    "plan_ref": goal.completion_plan_ref,
                    "idempotency_ref": _sha256_ref(
                        "idempotency-ref:goal-completion-event",
                        {
                            "goal_ref": goal.goal_ref,
                            "goal_version": goal.version,
                        },
                    ),
                    "authority_decision_ref": approval_decision_ref,
                }
            )
        )

    def append_run_event(
        self,
        request: DurableRunEventAppendRequest,
        *,
        approval_binding: GoalMutationApprovalBinding,
    ) -> DurableRunEvent:
        """Append one exact operator-approved metadata event."""

        validated = DurableRunEventAppendRequest.model_validate(request.model_dump())
        if (
            validated.event_kind
            == DurableRunEventKind.completion_verified.value
        ):
            raise GoalTransitionDeniedError(
                "RUN_EVENT_TRUSTED_PRODUCER_REQUIRED"
            )
        _validate_goal_mutation_approval_binding(
            approval_binding,
            operation="append-run-event",
            subject_ref=validated.run_ref,
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=validated.idempotency_ref,
        )
        self.reconcile_durable_events()
        return self._events.append(validated)

    @contextmanager
    def runtime_projection_guard(
        self,
        existing_record: RuntimeInvocationRecord | None,
        *,
        operation_idempotency_ref: str,
    ) -> Iterator[str]:
        """Reserve receipt-projection capacity across one bounded runtime call."""

        self.reconcile_durable_events()
        reservation_ref = self._events.reserve_runtime_projection(
            existing_record,
            operation_idempotency_ref=operation_idempotency_ref,
        )
        try:
            yield reservation_ref
        finally:
            self._events.release_runtime_projection_reservation(
                reservation_ref
            )

    def record_accepted_runtime_invocation(
        self,
        record: RuntimeInvocationRecord,
        *,
        reservation_ref: str | None = None,
    ) -> list[DurableRunEvent]:
        """Project one accepted RuntimeGateway receipt into durable run events."""

        from ultimate_ai_agent.core.runtime_gateway.contracts import (
            RuntimeAuthority,
            RuntimeInvocationRecord,
            RuntimeInvocationStatus,
        )

        validated = RuntimeInvocationRecord.model_validate(record.model_dump())
        receipt = validated.receipt
        if (
            receipt is None
            or validated.status != RuntimeInvocationStatus.receipt_recorded.value
        ):
            return []
        if reservation_ref is None:
            with self.runtime_projection_guard(
                validated,
                operation_idempotency_ref=_sha256_ref(
                    "idempotency-ref:runtime-projection",
                    {"invocation_ref": validated.invocation_ref},
                ),
            ) as created_reservation_ref:
                return self.record_accepted_runtime_invocation(
                    validated,
                    reservation_ref=created_reservation_ref,
                )
        run_type = (
            AcceptedLocalRunType.local_read_task
            if validated.request.requested_authority
            == RuntimeAuthority.local_model.value
            else AcceptedLocalRunType.local_metadata_action
        )
        authority_decision_ref = receipt.policy_decision_ref
        goal_ref = (
            validated.request.mission_ref
            if (validated.request.mission_ref or "").startswith("goal-ref:")
            else None
        )
        plan_ref = (
            validated.request.action_ref
            if (validated.request.action_ref or "").startswith("plan-ref:")
            else None
        )
        proof_refs = list(
            dict.fromkeys(
                [
                    receipt.policy_decision_ref,
                    *receipt.evidence_refs,
                ]
            )
        )
        with self._events.exclusive():
            self._events.bind_runtime_projection_reservation(
                reservation_ref,
                validated,
            )
            started = self._events._append_locked(
                DurableRunEventAppendRequest(
                run_ref=validated.invocation_ref,
                run_type=run_type,
                event_kind=DurableRunEventKind.run_started,
                safe_summary=(
                    "RuntimeGateway accepted the exact local invocation under "
                    "the recorded policy decision."
                ),
                proof_refs=[receipt.policy_decision_ref],
                goal_ref=goal_ref,
                plan_ref=plan_ref,
                idempotency_ref=_sha256_ref(
                    "idempotency-ref:runtime-run-started",
                    {"invocation_ref": validated.invocation_ref},
                ),
                authority_decision_ref=authority_decision_ref,
                ),
                reservation_ref=reservation_ref,
            )
            recorded = self._events._append_locked(
                DurableRunEventAppendRequest(
                run_ref=validated.invocation_ref,
                run_type=run_type,
                event_kind=DurableRunEventKind.receipt_recorded,
                safe_summary=(
                    "RuntimeGateway recorded the accepted local invocation "
                    "receipt with redacted evidence refs."
                ),
                proof_refs=proof_refs,
                receipt_refs=[receipt.receipt_ref],
                goal_ref=goal_ref,
                plan_ref=plan_ref,
                idempotency_ref=_sha256_ref(
                    "idempotency-ref:runtime-receipt-recorded",
                    {
                        "invocation_ref": validated.invocation_ref,
                        "receipt_ref": receipt.receipt_ref,
                    },
                ),
                authority_decision_ref=authority_decision_ref,
                ),
                reservation_ref=reservation_ref,
            )
        return [started, recorded]

    def sync_runtime_invocations(
        self,
        records: Iterable[RuntimeInvocationRecord],
    ) -> list[DurableRunEvent]:
        self.reconcile_durable_events()
        projected: list[DurableRunEvent] = []
        for record in self._events.unprojected_runtime_invocations(records):
            projected.extend(self.record_accepted_runtime_invocation(record))
        return projected


class GoalMutationApprovalBinding(BaseModel):
    schema_version: str = "goal_mutation_approval_binding.v1"
    approval_ref: str
    approval_request_ref: str
    approval_decision_ref: str
    exact_scope_ref: str
    request_fingerprint_ref: str
    operator_actor_ref: str = "operator-ref:local-user"
    approval_validated: bool = True
    standing_authority_granted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "GoalMutationApprovalBinding":
        for value, field_name in (
            (self.approval_ref, "approval_ref"),
            (self.approval_request_ref, "approval_request_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.operator_actor_ref, "operator_actor_ref"),
        ):
            validate_execution_ref(value, field_name)
        if not self.approval_validated or self.standing_authority_granted:
            raise ValueError("GOAL_MUTATION_APPROVAL_POSTURE_INVALID")
        return self


def capture_exact_goal_mutation_approval(
    *,
    operation: str,
    subject_ref: str,
    request_payload: dict[str, Any],
    idempotency_ref: str,
) -> GoalMutationApprovalBinding:
    """Capture one explicit local operator request as an exact, non-standing grant."""

    validate_safe_execution_text(operation, "operation")
    validate_execution_ref(subject_ref, "subject_ref")
    validate_execution_ref(idempotency_ref, "idempotency_ref")
    request_fingerprint_ref = _sha256_ref(
        "request-fingerprint-ref:goal-mutation",
        {
            "operation": operation,
            "subject_ref": subject_ref,
            "request_payload": request_payload,
            "idempotency_ref": idempotency_ref,
        },
    )
    exact_scope_ref = _sha256_ref(
        "exact-scope-ref:goal-mutation",
        {
            "operation": operation,
            "subject_ref": subject_ref,
            "request_fingerprint_ref": request_fingerprint_ref,
        },
    )
    approval_request_ref = _sha256_ref(
        "approval-request-ref:goal-mutation",
        {
            "exact_scope_ref": exact_scope_ref,
            "idempotency_ref": idempotency_ref,
        },
    )
    approval_ref = _sha256_ref(
        "approval-ref:goal-mutation",
        {
            "approval_request_ref": approval_request_ref,
            "exact_scope_ref": exact_scope_ref,
        },
    )
    approval_request = ApprovalRequest(
        approval_request_id=approval_request_ref,
        run_id=_sha256_ref(
            "run-ref:goal-mutation",
            {"exact_scope_ref": exact_scope_ref},
        ),
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=subject_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=f"goal_mutation_{operation}",
        purpose=(
            "Record one exact local proof-backed goal metadata mutation; "
            "runtime execution and standing authority remain disabled."
        ),
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="goal-runtime-exact-local-mutation",
            reason="Goal metadata remains local and redacted.",
            allowed_sinks=["local-goal-journal"],
            forbidden_sinks=["provider", "network", "runtime-execution"],
            requires_redaction=True,
        ),
        resource_refs=[
            subject_ref,
            exact_scope_ref,
            request_fingerprint_ref,
            idempotency_ref,
        ],
        event_ref=_sha256_ref(
            "event-ref:goal-mutation-approval",
            {"approval_request_ref": approval_request_ref},
        ),
        trace_id=approval_request_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref=approval_ref,
    )
    decision = authority.validate_for_request(approval_request, approval_ref)
    if not decision.allowed:
        raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_DENIED")
    return GoalMutationApprovalBinding(
        approval_ref=approval_ref,
        approval_request_ref=approval_request_ref,
        approval_decision_ref=_sha256_ref(
            "approval-decision-ref:goal-mutation",
            {
                "approval_ref": approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "request_fingerprint_ref": request_fingerprint_ref,
            },
        ),
        exact_scope_ref=exact_scope_ref,
        request_fingerprint_ref=request_fingerprint_ref,
    )


def _validate_goal_mutation_approval_binding(
    binding: GoalMutationApprovalBinding,
    *,
    operation: str,
    subject_ref: str,
    request_payload: dict[str, Any],
    idempotency_ref: str,
) -> None:
    validated = GoalMutationApprovalBinding.model_validate(binding.model_dump())
    expected = capture_exact_goal_mutation_approval(
        operation=operation,
        subject_ref=subject_ref,
        request_payload=request_payload,
        idempotency_ref=idempotency_ref,
    )
    if validated != expected:
        raise GoalTransitionDeniedError(
            "GOAL_MUTATION_APPROVAL_BINDING_MISMATCH"
        )


def _atomic_write(path: Path, content: str) -> None:
    temp_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent_metadata = os.lstat(path.parent)
        if not stat.S_ISDIR(parent_metadata.st_mode):
            raise OSError("goal runtime state directory must be a real directory")
        os.chmod(path.parent, 0o700)
        temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(temp_path, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
    except Exception:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
