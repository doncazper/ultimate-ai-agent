from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
import uuid
from collections.abc import Iterable
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.execution.validation import (
    contains_absolute_local_path,
    validate_execution_ref as _validate_execution_ref,
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
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS,
    MAX_RUNTIME_GOAL_VERSION,
    MAX_RUNTIME_RECEIPT_EVIDENCE_REFS,
    RuntimeCriterionVerificationBinding,
)
from ultimate_ai_agent.core.time import utc_now

if TYPE_CHECKING:
    from ultimate_ai_agent.core.runtime_gateway.contracts import RuntimeInvocationRecord
    from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStore


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
MAX_GOAL_JOURNAL_HEAD_BYTES = 64 * 1024
MAX_EXECUTION_REF_LENGTH = 320
MAX_RUN_EVENT_STORE_BYTES = 16 * 1024 * 1024
MAX_RUN_EVENT_IDEMPOTENCY_BYTES = 32 * 1024 * 1024
MAX_RUN_EVENT_PROJECTION_RESERVATION_BYTES = 16 * 1024 * 1024
MAX_GOAL_PROVENANCE_ENTRIES = 100
RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS = 120
GOAL_TEXT_REDACTION_POSTURE = "operator_authored_redacted_summary_only"
GOAL_COMPLETION_VERIFIER_REF = "verifier-ref:goal-runtime:criteria-receipt-binding:v1"
GOAL_COMPLETION_EVALUATOR_BLOCKED_REASON_REF = (
    "blocked-authority-ref:goal-runtime:trusted-criterion-evaluator-unavailable"
)
MAX_RUN_EVENT_PROOF_REFS = (
    1
    + MAX_RUNTIME_RECEIPT_EVIDENCE_REFS
    + (2 * MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS)
)
MAX_RUN_EVENT_RECEIPT_REFS = 1 + MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS
_RAW_CONTENT_MARKERS = (
    "prompt:",
    "response:",
    "transcript:",
    "system:",
    "developer:",
    "assistant:",
    "user:",
    "tool:",
    "model:",
    "<|system|>",
    "<|developer|>",
    "<|user|>",
    "<|assistant|>",
    "<|tool|>",
)


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


class _GoalRuntimeGenerationChanged(RuntimeError):
    """Internal signal for a bounded optimistic read retry."""


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
    restore = "restore"
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


def build_goal_completion_evidence_ref(
    goal: "PersistentGoal",
    *,
    run_ref: str,
    receipt_ref: str,
    proof_ref: str,
    criterion_verifier_bindings: list["DurableCriterionVerifierBinding"],
    plan_ref: str | None,
) -> str:
    """Bind the built-in verifier result to exact durable goal/run evidence."""

    return _sha256_ref(
        "evidence-ref:goal-completion-verification",
        {
            "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
            "goal_ref": goal.goal_ref,
            "goal_version": goal.version,
            "success_criteria": goal.success_criteria,
            "run_ref": run_ref,
            "receipt_ref": receipt_ref,
            "proof_ref": proof_ref,
            "criterion_verifier_bindings": [
                binding.model_dump(mode="json")
                for binding in criterion_verifier_bindings
            ],
            "plan_ref": plan_ref,
        },
    )


def validate_execution_ref(value: str, field_name: str) -> None:
    """Apply the shared ref grammar plus this store's encoded-size bound."""

    if len(value) > MAX_EXECUTION_REF_LENGTH:
        raise ValueError(f"{field_name} exceeds the bounded ref length")
    _validate_execution_ref(value, field_name)


def _runtime_receipt_projection_kind(
    record: RuntimeInvocationRecord,
) -> DurableRunEventKind:
    receipt = record.receipt
    if receipt is None:
        return DurableRunEventKind.failed_terminal
    if receipt.invocation_status != "receipt_recorded":
        return DurableRunEventKind.failed_terminal
    model_metadata = receipt.model_receipt_metadata
    if model_metadata is not None:
        successful = (
            receipt.model_call_performed
            and receipt.execution_performed
            and receipt.adapter_execution_performed
            and model_metadata.response_received
            and model_metadata.status_code is not None
            and 200 <= model_metadata.status_code < 300
            and model_metadata.error_category is None
            and not model_metadata.attempt_outcome_unknown
        )
        return (
            DurableRunEventKind.receipt_recorded
            if successful
            else DurableRunEventKind.failed_terminal
        )
    command_metadata = receipt.command_receipt_metadata
    if command_metadata is not None:
        successful = (
            receipt.command_execution_performed
            and receipt.execution_performed
            and receipt.adapter_execution_performed
            and command_metadata.command_execution_attempted
            and command_metadata.exit_code == 0
            and not command_metadata.timed_out
            and command_metadata.error_category is None
        )
        return (
            DurableRunEventKind.receipt_recorded
            if successful
            else DurableRunEventKind.failed_terminal
        )
    return DurableRunEventKind.failed_terminal


def _bounded_safe_text(value: str, field_name: str) -> str:
    candidate = value.strip()
    if not candidate or len(candidate) > MAX_GOAL_TEXT:
        raise ValueError(
            f"{field_name} must be between 1 and {MAX_GOAL_TEXT} characters"
        )
    validate_safe_execution_text(candidate, field_name)
    return candidate


def _bounded_redacted_summary(value: str, field_name: str) -> str:
    if isinstance(value, str) and contains_absolute_local_path(value.strip()):
        raise ValueError("GOAL_RAW_CONTENT_PERSISTENCE_DENIED")
    candidate = _bounded_safe_text(value, field_name)
    lowered = candidate.casefold()
    if (
        "\n" in candidate
        or "\r" in candidate
        or any(marker in lowered for marker in _RAW_CONTENT_MARKERS)
        or lowered.startswith(("summarize ", "translate ", "respond to "))
        or contains_absolute_local_path(candidate)
    ):
        raise ValueError("GOAL_RAW_CONTENT_PERSISTENCE_DENIED")
    return candidate


def build_goal_criterion_ref(
    goal: "PersistentGoal",
    *,
    criterion_index: int,
    criterion_summary: str,
) -> str:
    """Return the stable identifier a trusted evaluator must bind."""

    return _sha256_ref(
        "criterion-ref:goal-runtime",
        {
            "goal_ref": goal.goal_ref,
            "goal_version": goal.version,
            "criterion_index": criterion_index,
            "criterion_summary": criterion_summary,
        },
    )


def _validate_refs(
    refs: Iterable[str],
    field_name: str,
    *,
    max_items: int = MAX_GOAL_LIST_ITEMS,
) -> list[str]:
    values = list(dict.fromkeys(refs))
    if len(values) > max_items:
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


def _validate_redacted_summaries(values: Iterable[str], field_name: str) -> list[str]:
    items = list(dict.fromkeys(value.strip() for value in values))
    if len(items) > MAX_GOAL_LIST_ITEMS:
        raise ValueError(f"{field_name} exceeds the bounded item limit")
    for item in items:
        _bounded_redacted_summary(item, field_name)
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
        self.work_board_refs = _validate_refs(self.work_board_refs, "work_board_refs")
        return self


class GoalCreateRequest(BaseModel):
    text_redaction_posture: Literal["operator_authored_redacted_summary_only"]
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
        self.objective = _bounded_redacted_summary(self.objective, "objective")
        self.desired_outcome = _bounded_redacted_summary(
            self.desired_outcome, "desired_outcome"
        )
        self.stop_condition = _bounded_redacted_summary(
            self.stop_condition, "stop_condition"
        )
        self.success_criteria = _validate_redacted_summaries(
            self.success_criteria, "success_criteria"
        )
        self.constraints = _validate_redacted_summaries(self.constraints, "constraints")
        self.in_scope_resource_refs = _validate_refs(
            self.in_scope_resource_refs, "in_scope_resource_refs"
        )
        self.evidence_refs = _validate_refs(self.evidence_refs, "evidence_refs")
        return self


class GoalEditRequest(BaseModel):
    expected_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    text_redaction_posture: (
        Literal["operator_authored_redacted_summary_only"] | None
    ) = None
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
        text_fields_present = any(
            getattr(self, field_name) is not None
            for field_name in (
                "objective",
                "desired_outcome",
                "success_criteria",
                "constraints",
                "stop_condition",
            )
        )
        if text_fields_present and self.text_redaction_posture is None:
            raise ValueError("GOAL_TEXT_REDACTION_POSTURE_REQUIRED")
        if not text_fields_present and self.text_redaction_posture is not None:
            raise ValueError("GOAL_TEXT_REDACTION_POSTURE_NOT_ALLOWED")
        if self.objective is not None:
            self.objective = _bounded_redacted_summary(self.objective, "objective")
        if self.desired_outcome is not None:
            self.desired_outcome = _bounded_redacted_summary(
                self.desired_outcome, "desired_outcome"
            )
        if self.stop_condition is not None:
            self.stop_condition = _bounded_redacted_summary(
                self.stop_condition, "stop_condition"
            )
        if self.success_criteria is not None:
            self.success_criteria = _validate_redacted_summaries(
                self.success_criteria, "success_criteria"
            )
            if not self.success_criteria:
                raise ValueError("GOAL_SUCCESS_CRITERIA_REQUIRED")
        if self.constraints is not None:
            self.constraints = _validate_redacted_summaries(
                self.constraints, "constraints"
            )
        if self.in_scope_resource_refs is not None:
            self.in_scope_resource_refs = _validate_refs(
                self.in_scope_resource_refs, "in_scope_resource_refs"
            )
        if self.evidence_refs is not None:
            self.evidence_refs = _validate_refs(self.evidence_refs, "evidence_refs")
        return self


class GoalCompletionEvidence(BaseModel):
    goal_ref: str
    goal_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    run_ref: str
    receipt_ref: str
    proof_ref: str
    criterion_proof_refs: list[str]
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
        self.criterion_proof_refs = _validate_refs(
            self.criterion_proof_refs,
            "criterion_proof_refs",
        )
        if not self.criterion_proof_refs:
            raise ValueError("GOAL_COMPLETION_CRITERION_PROOFS_REQUIRED")
        return self


class GoalTransitionRequest(BaseModel):
    expected_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
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
    schema_version: Literal["persistent_goal.v1"] = "persistent_goal.v1"
    contract_ref: Literal["contract-ref:proof-backed-goals-durable-events:v1"] = (
        GOAL_RUNTIME_CONTRACT_REF
    )
    goal_ref: str
    text_redaction_posture: Literal["operator_authored_redacted_summary_only"] = (
        GOAL_TEXT_REDACTION_POSTURE
    )
    objective: str
    desired_outcome: str
    success_criteria: list[str]
    constraints: list[str]
    in_scope_resource_refs: list[str]
    stop_condition: str
    state: GoalState
    budget: GoalBudget
    links: GoalLinks
    version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    created_at: datetime
    updated_at: datetime
    evidence_refs: list[str]
    completion_run_ref: str | None = None
    completion_plan_ref: str | None = None
    completion_evidence_ref: str | None = None
    completion_receipt_ref: str | None = None
    completion_proof_ref: str | None = None
    completion_criterion_proof_refs: list[str] = Field(default_factory=list)
    completion_source_goal_version: StrictInt | None = Field(
        default=None,
        ge=1,
        le=MAX_RUNTIME_GOAL_VERSION,
    )
    completion_criterion_verifier_bindings: list[
        RuntimeCriterionVerificationBinding
    ] = Field(default_factory=list, max_length=MAX_GOAL_LIST_ITEMS)
    completion_verifier_ref: str | None = None
    safe_refs_only: bool = True
    model_output_authoritative: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_goal(self) -> "PersistentGoal":
        validate_execution_ref(self.goal_ref, "goal_ref")
        self.objective = _bounded_redacted_summary(self.objective, "objective")
        self.desired_outcome = _bounded_redacted_summary(
            self.desired_outcome, "desired_outcome"
        )
        self.stop_condition = _bounded_redacted_summary(
            self.stop_condition, "stop_condition"
        )
        self.success_criteria = _validate_redacted_summaries(
            self.success_criteria, "success_criteria"
        )
        self.constraints = _validate_redacted_summaries(self.constraints, "constraints")
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
        self.completion_criterion_proof_refs = _validate_refs(
            self.completion_criterion_proof_refs,
            "completion_criterion_proof_refs",
        )
        binding_keys = {
            (binding.goal_ref, binding.goal_version, binding.criterion_ref)
            for binding in self.completion_criterion_verifier_bindings
        }
        if len(binding_keys) != len(self.completion_criterion_verifier_bindings):
            raise ValueError("GOAL_COMPLETION_CRITERION_BINDING_DUPLICATE")
        required_completion_refs = (
            self.completion_run_ref,
            self.completion_evidence_ref,
            self.completion_receipt_ref,
            self.completion_proof_ref,
            self.completion_verifier_ref,
            self.completion_source_goal_version,
        )
        has_any_completion_ref = any(
            value is not None
            for value in (
                *required_completion_refs,
                self.completion_plan_ref,
            )
        )
        if self.completion_plan_ref is not None:
            if self.completion_plan_ref not in self.links.plan_refs:
                raise ValueError("GOAL_COMPLETION_PLAN_NOT_LINKED")
        if self.state == GoalState.verified_complete.value:
            if any(value is None for value in required_completion_refs):
                raise ValueError("GOAL_VERIFIED_COMPLETION_PROOF_REQUIRED")
            if self.links.plan_refs and self.completion_plan_ref is None:
                raise ValueError("GOAL_COMPLETION_PLAN_BINDING_REQUIRED")
            if len(self.completion_criterion_proof_refs) != len(self.success_criteria):
                raise ValueError("GOAL_COMPLETION_CRITERION_PROOF_ARITY_MISMATCH")
            self._validate_completion_bindings()
        elif self.state == GoalState.cleared.value and has_any_completion_ref:
            if any(value is None for value in required_completion_refs):
                raise ValueError("GOAL_CLEARED_COMPLETION_PROOF_INCOMPLETE")
            if self.links.plan_refs and self.completion_plan_ref is None:
                raise ValueError("GOAL_COMPLETION_PLAN_BINDING_REQUIRED")
            if len(self.completion_criterion_proof_refs) != len(self.success_criteria):
                raise ValueError("GOAL_COMPLETION_CRITERION_PROOF_ARITY_MISMATCH")
            self._validate_completion_bindings()
        elif has_any_completion_ref:
            raise ValueError("GOAL_UNVERIFIED_COMPLETION_PROOF_DENIED")
        elif (
            self.completion_criterion_proof_refs
            or self.completion_criterion_verifier_bindings
        ):
            raise ValueError("GOAL_UNVERIFIED_COMPLETION_PROOF_DENIED")
        if not self.safe_refs_only or self.model_output_authoritative:
            raise ValueError("GOAL_UNSAFE_AUTHORITY_POSTURE")
        return self

    def _validate_completion_bindings(self) -> None:
        if self.completion_source_goal_version is None:
            raise ValueError("GOAL_COMPLETION_SOURCE_VERSION_REQUIRED")
        if len(self.completion_criterion_verifier_bindings) != len(
            self.success_criteria
        ):
            raise ValueError("GOAL_COMPLETION_CRITERION_BINDING_ARITY_MISMATCH")
        expected_criterion_refs = [
            _sha256_ref(
                "criterion-ref:goal-runtime",
                {
                    "goal_ref": self.goal_ref,
                    "goal_version": self.completion_source_goal_version,
                    "criterion_index": index,
                    "criterion_summary": criterion,
                },
            )
            for index, criterion in enumerate(self.success_criteria)
        ]
        for expected_ref, expected_proof_ref, binding in zip(
            expected_criterion_refs,
            self.completion_criterion_proof_refs,
            self.completion_criterion_verifier_bindings,
            strict=True,
        ):
            if (
                binding.goal_ref != self.goal_ref
                or binding.goal_version != self.completion_source_goal_version
                or binding.criterion_ref != expected_ref
                or binding.proof_ref != expected_proof_ref
                or binding.verifier_ref != self.completion_verifier_ref
            ):
                raise ValueError("GOAL_COMPLETION_CRITERION_BINDING_MISMATCH")
        expected_evidence_ref = _sha256_ref(
            "evidence-ref:goal-completion-verification",
            {
                "verifier_ref": self.completion_verifier_ref,
                "goal_ref": self.goal_ref,
                "goal_version": self.completion_source_goal_version,
                "success_criteria": self.success_criteria,
                "run_ref": self.completion_run_ref,
                "receipt_ref": self.completion_receipt_ref,
                "proof_ref": self.completion_proof_ref,
                "criterion_verifier_bindings": [
                    binding.model_dump(mode="json")
                    for binding in self.completion_criterion_verifier_bindings
                ],
                "plan_ref": self.completion_plan_ref,
            },
        )
        if self.completion_evidence_ref != expected_evidence_ref:
            raise ValueError("GOAL_COMPLETION_CRITERION_BINDING_EVIDENCE_MISMATCH")


class GoalJournalEntry(BaseModel):
    schema_version: Literal["goal_journal.v1"] = GOAL_JOURNAL_SCHEMA_VERSION
    entry_ref: str
    operation: GoalJournalOperation
    goal_ref: str
    goal_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    idempotency_ref: str
    request_fingerprint_ref: str
    approval_ref: str
    approval_decision_ref: str
    transition_reason_ref: str | None = None
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
        if self.transition_reason_ref is not None:
            validate_execution_ref(self.transition_reason_ref, "transition_reason_ref")
        if (
            self.goal.goal_ref != self.goal_ref
            or self.goal.version != self.goal_version
        ):
            raise ValueError("GOAL_JOURNAL_SNAPSHOT_BINDING_MISMATCH")
        return self


class GoalMutationProvenanceEntry(BaseModel):
    schema_version: str = "goal_mutation_provenance_entry.v1"
    entry_ref: str
    operation: GoalJournalOperation
    goal_ref: str
    goal_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    idempotency_ref: str
    request_fingerprint_ref: str
    approval_ref: str
    approval_decision_ref: str
    transition_reason_ref: str | None = None
    recorded_at: datetime
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @classmethod
    def from_journal_entry(
        cls, entry: GoalJournalEntry
    ) -> "GoalMutationProvenanceEntry":
        return cls.model_validate(
            entry.model_dump(
                mode="json",
                exclude={"goal"},
            )
        )


class GoalMutationProvenanceReadModel(BaseModel):
    schema_version: str = "goal_mutation_provenance_read_model.v1"
    contract_ref: str = GOAL_RUNTIME_CONTRACT_REF
    goal_ref: str
    entries: list[GoalMutationProvenanceEntry]
    entry_count: StrictInt = Field(ge=1, le=MAX_GOAL_PROVENANCE_ENTRIES)
    bounded_history: bool = True
    raw_request_payload_persisted: bool = False
    raw_goal_content_repeated: bool = False
    safe_refs_only: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOAL_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")


class GoalJournalHeadManifest(BaseModel):
    schema_version: Literal["goal_journal_head.v1"] = "goal_journal_head.v1"
    entry_count: StrictInt = Field(ge=1, le=MAX_GOAL_JOURNAL_ENTRIES)
    head_entry_hash_ref: str
    idempotency_set_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "GoalJournalHeadManifest":
        validate_execution_ref(self.head_entry_hash_ref, "head_entry_hash_ref")
        validate_execution_ref(
            self.idempotency_set_hash_ref,
            "idempotency_set_hash_ref",
        )
        return self


class GoalJournalGenesisIntent(BaseModel):
    """Independently durable binding for the exact first journal generation."""

    schema_version: Literal["goal_journal_genesis_intent.v1"] = (
        "goal_journal_genesis_intent.v1"
    )
    entry: GoalJournalEntry
    head_manifest: GoalJournalHeadManifest
    journal_content_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intent(self) -> "GoalJournalGenesisIntent":
        validate_execution_ref(
            self.journal_content_hash_ref,
            "journal_content_hash_ref",
        )
        if self.head_manifest.entry_count != 1:
            raise ValueError("GOAL_JOURNAL_GENESIS_INTENT_ARITY_INVALID")
        if self.head_manifest.head_entry_hash_ref != self.entry.entry_hash_ref:
            raise ValueError("GOAL_JOURNAL_GENESIS_INTENT_HEAD_MISMATCH")
        return self


class DurableCriterionVerifierBinding(BaseModel):
    """Criterion proof and evaluator provenance copied from a trusted receipt."""

    goal_ref: str
    goal_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    criterion_ref: str
    proof_ref: str
    verifier_ref: str
    evaluator_receipt_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "DurableCriterionVerifierBinding":
        for value, field_name in (
            (self.goal_ref, "goal_ref"),
            (self.criterion_ref, "criterion_ref"),
            (self.proof_ref, "proof_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.evaluator_receipt_ref, "evaluator_receipt_ref"),
        ):
            validate_execution_ref(value, field_name)
        return self


class DurableRunEventAppendRequest(BaseModel):
    run_ref: str
    run_type: AcceptedLocalRunType
    event_kind: DurableRunEventKind
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    criterion_verifier_bindings: list[DurableCriterionVerifierBinding] = Field(
        default_factory=list
    )
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
        self.safe_summary = _bounded_redacted_summary(
            self.safe_summary,
            "safe_summary",
        )
        self.proof_refs = _validate_refs(
            self.proof_refs,
            "proof_refs",
            max_items=MAX_RUN_EVENT_PROOF_REFS,
        )
        self.receipt_refs = _validate_refs(
            self.receipt_refs,
            "receipt_refs",
            max_items=MAX_RUN_EVENT_RECEIPT_REFS,
        )
        if len(self.criterion_verifier_bindings) > MAX_GOAL_LIST_ITEMS:
            raise ValueError("RUN_EVENT_CRITERION_BINDING_LIMIT_EXCEEDED")
        binding_keys = {
            (binding.goal_ref, binding.goal_version, binding.criterion_ref)
            for binding in self.criterion_verifier_bindings
        }
        if len(binding_keys) != len(self.criterion_verifier_bindings):
            raise ValueError("RUN_EVENT_CRITERION_BINDING_DUPLICATE")
        if self.criterion_verifier_bindings and self.event_kind not in {
            DurableRunEventKind.receipt_recorded.value,
            DurableRunEventKind.completion_verified.value,
        }:
            raise ValueError("RUN_EVENT_CRITERION_BINDING_KIND_INVALID")
        if (
            self.event_kind == DurableRunEventKind.goal_linked.value
            and self.goal_ref is None
        ):
            raise ValueError("RUN_EVENT_GOAL_REF_REQUIRED")
        if (
            self.event_kind == DurableRunEventKind.plan_linked.value
            and self.plan_ref is None
        ):
            raise ValueError("RUN_EVENT_PLAN_REF_REQUIRED")
        if self.event_kind in {
            DurableRunEventKind.receipt_recorded.value,
            *TERMINAL_RUN_EVENT_KINDS,
        }:
            if not self.proof_refs or not self.receipt_refs:
                raise ValueError("RUN_EVENT_TERMINAL_RECEIPT_PROOF_REQUIRED")
        return self


class DurableRunEvent(BaseModel):
    schema_version: Literal["durable_run_event.v1"] = RUN_EVENT_SCHEMA_VERSION
    event_ref: str
    run_ref: str
    run_type: AcceptedLocalRunType
    sequence: StrictInt = Field(
        ge=1,
        le=MAX_RUN_EVENT_IDEMPOTENCY_RECORDS,
    )
    recorded_at: datetime
    event_kind: DurableRunEventKind
    safe_summary: str
    proof_refs: list[str]
    receipt_refs: list[str]
    criterion_verifier_bindings: list[DurableCriterionVerifierBinding] = Field(
        default_factory=list
    )
    goal_ref: str | None = None
    plan_ref: str | None = None
    idempotency_ref: str
    authority_decision_ref: str
    predecessor_hash_ref: str | None = None
    event_hash_ref: str
    redaction_status: Literal["redacted_safe_refs_only"] = "redacted_safe_refs_only"
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
        self.safe_summary = _bounded_redacted_summary(
            self.safe_summary,
            "safe_summary",
        )
        self.proof_refs = _validate_refs(
            self.proof_refs,
            "proof_refs",
            max_items=MAX_RUN_EVENT_PROOF_REFS,
        )
        self.receipt_refs = _validate_refs(
            self.receipt_refs,
            "receipt_refs",
            max_items=MAX_RUN_EVENT_RECEIPT_REFS,
        )
        if len(self.criterion_verifier_bindings) > MAX_GOAL_LIST_ITEMS:
            raise ValueError("RUN_EVENT_CRITERION_BINDING_LIMIT_EXCEEDED")
        binding_keys = {
            (binding.goal_ref, binding.goal_version, binding.criterion_ref)
            for binding in self.criterion_verifier_bindings
        }
        if len(binding_keys) != len(self.criterion_verifier_bindings):
            raise ValueError("RUN_EVENT_CRITERION_BINDING_DUPLICATE")
        if self.criterion_verifier_bindings and self.event_kind not in {
            DurableRunEventKind.receipt_recorded.value,
            DurableRunEventKind.completion_verified.value,
        }:
            raise ValueError("RUN_EVENT_CRITERION_BINDING_KIND_INVALID")
        if (
            self.event_kind == DurableRunEventKind.goal_linked.value
            and self.goal_ref is None
        ):
            raise ValueError("RUN_EVENT_GOAL_REF_REQUIRED")
        if (
            self.event_kind == DurableRunEventKind.plan_linked.value
            and self.plan_ref is None
        ):
            raise ValueError("RUN_EVENT_PLAN_REF_REQUIRED")
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
    schema_version: Literal["run_event_idempotency_tombstone.v1"] = (
        "run_event_idempotency_tombstone.v1"
    )
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


def _maximum_typed_ref(prefix: str, index: int) -> str:
    stem = f"{prefix}:{index:03d}:"
    return stem + ("x" * (MAX_EXECUTION_REF_LENGTH - len(stem)))


def _maximum_typed_summary(index: int) -> str:
    suffix = f"{index:04d}"
    return ("x" * (MAX_GOAL_TEXT - len(suffix))) + suffix


def _maximum_goal_genesis_intent() -> GoalJournalGenesisIntent:
    goal_ref = _maximum_typed_ref("goal-ref:max-envelope", 0)
    now = datetime.max.replace(tzinfo=utc_now().tzinfo)
    goal = PersistentGoal(
        goal_ref=goal_ref,
        text_redaction_posture=GOAL_TEXT_REDACTION_POSTURE,
        objective=_maximum_typed_summary(0),
        desired_outcome=_maximum_typed_summary(1),
        success_criteria=[
            _maximum_typed_summary(index + 2) for index in range(MAX_GOAL_LIST_ITEMS)
        ],
        constraints=[
            _maximum_typed_summary(index + 100) for index in range(MAX_GOAL_LIST_ITEMS)
        ],
        in_scope_resource_refs=[
            _maximum_typed_ref("resource-ref:max-envelope", index)
            for index in range(MAX_GOAL_LIST_ITEMS)
        ],
        stop_condition=_maximum_typed_summary(999),
        state=GoalState.active,
        budget=GoalBudget(
            operation_limit=10_000,
            cost_budget_microusd=10_000_000_000,
            deadline_at=now,
        ),
        links=GoalLinks(
            plan_refs=[
                _maximum_typed_ref("plan-ref:max-envelope", index)
                for index in range(MAX_GOAL_LIST_ITEMS)
            ],
            run_refs=[
                _maximum_typed_ref("run-ref:max-envelope", index)
                for index in range(MAX_GOAL_LIST_ITEMS)
            ],
            action_inbox_refs=[
                _maximum_typed_ref("action-inbox-ref:max-envelope", index)
                for index in range(MAX_GOAL_LIST_ITEMS)
            ],
            work_board_refs=[
                _maximum_typed_ref("work-board-ref:max-envelope", index)
                for index in range(MAX_GOAL_LIST_ITEMS)
            ],
        ),
        version=1,
        created_at=now,
        updated_at=now,
        evidence_refs=[
            _maximum_typed_ref("evidence-ref:max-envelope", index)
            for index in range(MAX_GOAL_LIST_ITEMS)
        ],
    )
    entry_hash_ref = _maximum_typed_ref("entry-hash-ref:max-envelope", 0)
    entry = GoalJournalEntry(
        entry_ref=_maximum_typed_ref("goal-journal-entry-ref:max-envelope", 0),
        operation=GoalJournalOperation.create,
        goal_ref=goal_ref,
        goal_version=1,
        idempotency_ref=_maximum_typed_ref("idempotency-ref:max-envelope", 0),
        request_fingerprint_ref=_maximum_typed_ref(
            "request-fingerprint-ref:max-envelope",
            0,
        ),
        approval_ref=_maximum_typed_ref("approval-ref:max-envelope", 0),
        approval_decision_ref=_maximum_typed_ref(
            "approval-decision-ref:max-envelope",
            0,
        ),
        recorded_at=now,
        goal=goal,
        entry_hash_ref=entry_hash_ref,
    )
    return GoalJournalGenesisIntent(
        entry=entry,
        head_manifest=GoalJournalHeadManifest(
            entry_count=1,
            head_entry_hash_ref=entry_hash_ref,
            idempotency_set_hash_ref=_maximum_typed_ref(
                "idempotency-set-hash-ref:max-envelope",
                0,
            ),
        ),
        journal_content_hash_ref=_maximum_typed_ref(
            "journal-content-hash-ref:max-envelope",
            0,
        ),
    )


def _maximum_run_event_envelopes() -> tuple[
    DurableRunEvent,
    RunEventIdempotencyTombstone,
]:
    now = datetime.max.replace(tzinfo=utc_now().tzinfo)
    goal_ref = _maximum_typed_ref("goal-ref:max-envelope", 0)
    bindings = [
        DurableCriterionVerifierBinding(
            goal_ref=goal_ref,
            goal_version=MAX_RUNTIME_GOAL_VERSION,
            criterion_ref=_maximum_typed_ref(
                "criterion-ref:max-envelope",
                index,
            ),
            proof_ref=_maximum_typed_ref("proof-ref:max-envelope-binding", index),
            verifier_ref=_maximum_typed_ref("verifier-ref:max-envelope", index),
            evaluator_receipt_ref=_maximum_typed_ref(
                "evaluator-receipt-ref:max-envelope",
                index,
            ),
        )
        for index in range(MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS)
    ]
    event = DurableRunEvent(
        event_ref=_maximum_typed_ref("run-event-ref:max-envelope", 0),
        run_ref=_maximum_typed_ref("run-ref:max-envelope", 0),
        run_type=AcceptedLocalRunType.local_metadata_action,
        sequence=MAX_RUN_EVENT_IDEMPOTENCY_RECORDS,
        recorded_at=now,
        event_kind=DurableRunEventKind.receipt_recorded,
        safe_summary=_maximum_typed_summary(0),
        proof_refs=[
            _maximum_typed_ref("proof-ref:max-envelope", index)
            for index in range(MAX_RUN_EVENT_PROOF_REFS)
        ],
        receipt_refs=[
            _maximum_typed_ref("receipt-ref:max-envelope", index)
            for index in range(MAX_RUN_EVENT_RECEIPT_REFS)
        ],
        criterion_verifier_bindings=bindings,
        goal_ref=goal_ref,
        plan_ref=_maximum_typed_ref("plan-ref:max-envelope", 0),
        idempotency_ref=_maximum_typed_ref("idempotency-ref:max-envelope", 0),
        authority_decision_ref=_maximum_typed_ref(
            "authority-decision-ref:max-envelope",
            0,
        ),
        predecessor_hash_ref=_maximum_typed_ref(
            "predecessor-hash-ref:max-envelope",
            0,
        ),
        event_hash_ref=_maximum_typed_ref("event-hash-ref:max-envelope", 0),
    )
    tombstone = RunEventIdempotencyTombstone(
        run_ref=event.run_ref,
        idempotency_ref=event.idempotency_ref,
        request_fingerprint_ref=_maximum_typed_ref(
            "request-fingerprint-ref:max-envelope",
            0,
        ),
        event=event,
        tombstone_hash_ref=_maximum_typed_ref(
            "tombstone-hash-ref:max-envelope",
            0,
        ),
    )
    return event, tombstone


_MAXIMUM_GOAL_GENESIS_INTENT = _maximum_goal_genesis_intent()
MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES = len(
    (_MAXIMUM_GOAL_GENESIS_INTENT.model_dump_json() + "\n").encode("utf-8")
)
_MAXIMUM_RUN_EVENT, _MAXIMUM_RUN_EVENT_TOMBSTONE = _maximum_run_event_envelopes()
MAX_RESERVED_RUN_EVENT_BYTES = len(
    (_MAXIMUM_RUN_EVENT.model_dump_json() + "\n").encode("utf-8")
)
MAX_RESERVED_RUN_EVENT_TOMBSTONE_BYTES = len(
    (_MAXIMUM_RUN_EVENT_TOMBSTONE.model_dump_json() + "\n").encode("utf-8")
)


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
    completion_verification_state: Literal[
        "blocked_missing_trusted_criterion_evaluator"
    ] = "blocked_missing_trusted_criterion_evaluator"
    completion_verification_available: bool = False
    completion_verification_blocked_reason_ref: str = (
        GOAL_COMPLETION_EVALUATOR_BLOCKED_REASON_REF
    )
    runtime_execution_enabled: bool = False
    model_output_authoritative: bool = False
    safe_refs_only: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOAL_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_completion_posture(self) -> "GoalLifecycleReadModel":
        validate_execution_ref(
            self.completion_verification_blocked_reason_ref,
            "completion_verification_blocked_reason_ref",
        )
        if self.completion_verification_available:
            raise ValueError("GOAL_COMPLETION_EVALUATOR_AUTHORITY_NOT_GRANTED")
        return self


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
        self.head_path = self.state_dir / "goal_journal_head.json"
        self.genesis_intent_path = self.state_dir / "goal_journal_genesis_intent.json"
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
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            entries = self._load_entries(repair_manifest=True)
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
                text_redaction_posture=validated.text_redaction_posture,
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
            mutate=lambda current, _entries: self._edited_goal(
                current,
                validated,
            ),
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
        completion_criterion_verifier_bindings: list[
            RuntimeCriterionVerificationBinding
        ]
        | None = None,
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
            transition_reason_ref=validated.reason_ref,
            mutate=lambda current, entries: self._transitioned_goal(
                current,
                validated,
                completion_verified=completion_verified,
                completion_plan_ref=completion_plan_ref,
                completion_criterion_verifier_bindings=(
                    completion_criterion_verifier_bindings or []
                ),
                restore_goal=(
                    self._goal_before_latest_clear(entries, goal_ref)
                    if validated.transition == GoalTransitionKind.restore.value
                    else None
                ),
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
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            return self._idempotent_replay(
                self._load_entries(repair_manifest=True),
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
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            for entry in self._load_entries(repair_manifest=True):
                if entry.idempotency_ref != idempotency_ref:
                    continue
                if entry.request_fingerprint_ref != fingerprint:
                    raise GoalIdempotencyConflictError("GOAL_IDEMPOTENCY_CONFLICT")
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
        entries = self._load_consistent_entries()
        for entry in reversed(entries):
            if entry.goal_ref == goal_ref:
                return entry.model_copy(deep=True)
        raise GoalNotFoundError("GOAL_NOT_FOUND")

    def mutation_provenance(
        self,
        goal_ref: str,
        *,
        limit: int = MAX_GOAL_PROVENANCE_ENTRIES,
    ) -> GoalMutationProvenanceReadModel:
        validate_execution_ref(goal_ref, "goal_ref")
        bounded_limit = max(1, min(int(limit), MAX_GOAL_PROVENANCE_ENTRIES))
        matching = [
            entry
            for entry in self._load_consistent_entries()
            if entry.goal_ref == goal_ref
        ]
        if not matching:
            raise GoalNotFoundError("GOAL_NOT_FOUND")
        entries = [
            GoalMutationProvenanceEntry.from_journal_entry(entry)
            for entry in matching[-bounded_limit:]
        ]
        return GoalMutationProvenanceReadModel(
            goal_ref=goal_ref,
            entries=entries,
            entry_count=len(entries),
        )

    def goal_with_provenance(
        self,
        goal_ref: str,
        *,
        limit: int = MAX_GOAL_PROVENANCE_ENTRIES,
    ) -> tuple[PersistentGoal, GoalMutationProvenanceReadModel]:
        validate_execution_ref(goal_ref, "goal_ref")
        bounded_limit = max(1, min(int(limit), MAX_GOAL_PROVENANCE_ENTRIES))
        all_entries = self._load_consistent_entries()
        matching = [entry for entry in all_entries if entry.goal_ref == goal_ref]
        if not matching:
            raise GoalNotFoundError("GOAL_NOT_FOUND")
        provenance_entries = [
            GoalMutationProvenanceEntry.from_journal_entry(entry)
            for entry in matching[-bounded_limit:]
        ]
        return (
            matching[-1].goal.model_copy(deep=True),
            GoalMutationProvenanceReadModel(
                goal_ref=goal_ref,
                entries=provenance_entries,
                entry_count=len(provenance_entries),
            ),
        )

    def latest_verified_completion_entry(
        self,
        goal_ref: str,
    ) -> GoalJournalEntry:
        validate_execution_ref(goal_ref, "goal_ref")
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            previous_state: str | None = None
            candidate: GoalJournalEntry | None = None
            for entry in self._load_entries(repair_manifest=True):
                if entry.goal_ref != goal_ref:
                    continue
                if (
                    previous_state == GoalState.complete_requested.value
                    and entry.goal.state == GoalState.verified_complete.value
                ):
                    candidate = entry
                previous_state = entry.goal.state
            if candidate is not None:
                return candidate.model_copy(deep=True)
        raise GoalRuntimeCorruptionError("GOAL_VERIFIED_COMPLETION_ENTRY_MISSING")

    def get(self, goal_ref: str) -> PersistentGoal:
        validate_execution_ref(goal_ref, "goal_ref")
        latest = self._latest_by_goal(self._load_consistent_entries())
        if goal_ref not in latest:
            raise GoalNotFoundError("GOAL_NOT_FOUND")
        return latest[goal_ref].model_copy(deep=True)

    def list(self, *, include_cleared: bool = False) -> list[PersistentGoal]:
        goals = list(self._latest_by_goal(self._load_consistent_entries()).values())
        goals.sort(key=lambda goal: (goal.updated_at, goal.goal_ref), reverse=True)
        if not include_cleared:
            goals = [goal for goal in goals if goal.state != GoalState.cleared.value]
        return [goal.model_copy(deep=True) for goal in goals]

    def read_model(self, *, include_cleared: bool = False) -> GoalLifecycleReadModel:
        return self._read_model_from_entries(
            self._load_consistent_entries(),
            include_cleared=include_cleared,
        )

    def _read_model_from_entries(
        self,
        entries: list[GoalJournalEntry],
        *,
        include_cleared: bool,
    ) -> GoalLifecycleReadModel:
        goals = list(self._latest_by_goal(entries).values())
        goals.sort(key=lambda goal: (goal.updated_at, goal.goal_ref), reverse=True)
        if not include_cleared:
            goals = [goal for goal in goals if goal.state != GoalState.cleared.value]
        goals = [goal.model_copy(deep=True) for goal in goals]
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
        transition_reason_ref: str | None = None,
        mutate: Any,
    ) -> PersistentGoal:
        validate_execution_ref(goal_ref, "goal_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        fingerprint = _sha256_ref(
            f"request-fingerprint-ref:goal-{operation.value}",
            {"goal_ref": goal_ref, "request": request_payload},
        )
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            entries = self._load_entries(repair_manifest=True)
            replay = self._idempotent_replay(entries, idempotency_ref, fingerprint)
            if replay is not None:
                return replay
            latest = self._latest_by_goal(entries)
            current = latest.get(goal_ref)
            if current is None:
                raise GoalNotFoundError("GOAL_NOT_FOUND")
            if current.version != expected_version:
                raise GoalVersionConflictError("GOAL_VERSION_CONFLICT")
            updated = mutate(current.model_copy(deep=True), entries)
            self._append(
                entries,
                operation=operation,
                goal=updated,
                idempotency_ref=idempotency_ref,
                request_fingerprint_ref=fingerprint,
                approval_ref=approval_binding.approval_ref,
                approval_decision_ref=approval_binding.approval_decision_ref,
                transition_reason_ref=transition_reason_ref,
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
        if request.evidence_refs is not None:
            updates["evidence_refs"] = list(
                dict.fromkeys([*current.evidence_refs, *request.evidence_refs])
            )
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
        completion_criterion_verifier_bindings: list[
            RuntimeCriterionVerificationBinding
        ],
        restore_goal: PersistentGoal | None,
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
            GoalState.cleared.value: {GoalTransitionKind.restore.value},
        }
        if request.transition not in allowed[current.state]:
            raise GoalTransitionDeniedError("GOAL_TRANSITION_DENIED")
        if (
            request.transition == GoalTransitionKind.verify_completion.value
            and not completion_verified
        ):
            raise GoalTransitionDeniedError("GOAL_COMPLETION_NOT_VERIFIED")
        if request.transition == GoalTransitionKind.restore.value:
            if restore_goal is None:
                raise GoalRuntimeCorruptionError("GOAL_RESTORE_SNAPSHOT_MISSING")
            return PersistentGoal.model_validate(
                restore_goal.model_copy(
                    update={
                        "version": current.version + 1,
                        "updated_at": utc_now(),
                        "evidence_refs": list(
                            dict.fromkeys(
                                [
                                    *restore_goal.evidence_refs,
                                    *request.evidence_refs,
                                ]
                            )
                        ),
                    }
                ).model_dump()
            )
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
                completion_criterion_proof_refs=(
                    request.completion_evidence.criterion_proof_refs
                ),
                completion_source_goal_version=request.completion_evidence.goal_version,
                completion_criterion_verifier_bindings=(
                    completion_criterion_verifier_bindings
                ),
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
    def _goal_before_latest_clear(
        entries: list[GoalJournalEntry],
        goal_ref: str,
    ) -> PersistentGoal:
        matching = [entry for entry in entries if entry.goal_ref == goal_ref]
        if len(matching) < 2 or (matching[-1].goal.state != GoalState.cleared.value):
            raise GoalRuntimeCorruptionError("GOAL_RESTORE_SNAPSHOT_MISSING")
        for entry in reversed(matching[:-1]):
            if entry.goal.state != GoalState.cleared.value:
                return entry.goal.model_copy(deep=True)
        raise GoalRuntimeCorruptionError("GOAL_RESTORE_SNAPSHOT_MISSING")

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
        transition_reason_ref: str | None = None,
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
            transition_reason_ref=transition_reason_ref,
            recorded_at=utc_now(),
            goal=goal,
            previous_entry_hash_ref=previous,
            entry_hash_ref="entry-hash-ref:pending",
        )
        entry = draft.model_copy(update={"entry_hash_ref": self._entry_hash(draft)})
        self._write_entries([*entries, entry])

    @staticmethod
    def _entry_hash(entry: GoalJournalEntry) -> str:
        payload = entry.model_dump(mode="json")
        payload.pop("entry_hash_ref", None)
        if payload.get("transition_reason_ref") is None:
            payload.pop("transition_reason_ref", None)
        return _sha256_ref("entry-hash-ref:goal-journal", payload)

    def _load_entries(
        self,
        *,
        repair_manifest: bool = False,
    ) -> list[GoalJournalEntry]:
        genesis_intent = self._load_genesis_intent()
        raw_content = _read_bounded_regular_utf8(
            self.path,
            max_bytes=MAX_GOAL_JOURNAL_BYTES,
            missing_ok=True,
            capacity_error="GOAL_JOURNAL_BYTE_CAPACITY_EXCEEDED",
            corruption_error="GOAL_JOURNAL_CORRUPT",
        )
        if raw_content is None:
            if genesis_intent is not None:
                if self._load_head_manifest() is not None:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_GENESIS_INTENT_STATE_MISMATCH"
                    )
                if not repair_manifest:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_GENESIS_RECOVERY_REQUIRED"
                    )
                self._install_genesis_intent(genesis_intent)
                return [genesis_intent.entry.model_copy(deep=True)]
            if self._load_head_manifest() is not None:
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_MISSING_WITH_HEAD_MANIFEST"
                )
            return []
        entries: list[GoalJournalEntry] = []
        previous: str | None = None
        versions: dict[str, int] = {}
        idempotency: dict[str, str] = {}
        try:
            if not raw_content.strip():
                raise GoalRuntimeCorruptionError("GOAL_JOURNAL_EMPTY_ROLLBACK")
            lines = raw_content.splitlines()
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
        manifest = self._load_head_manifest()
        if manifest is None:
            if (
                genesis_intent is not None
                and len(entries) == 1
                and genesis_intent.entry == entries[0]
                and genesis_intent.head_manifest == self._build_head_manifest(entries)
                and genesis_intent.journal_content_hash_ref
                == self._journal_content_hash(entries)
            ):
                if repair_manifest:
                    self._write_head_manifest(genesis_intent.head_manifest)
                    self._delete_genesis_intent()
                return entries
            raise GoalRuntimeCorruptionError("GOAL_JOURNAL_HEAD_MANIFEST_MISSING")
        exact_manifest = self._build_head_manifest(entries)
        if manifest == exact_manifest:
            if genesis_intent is not None:
                if (
                    len(entries) != 1
                    or genesis_intent.entry != entries[0]
                    or genesis_intent.head_manifest != exact_manifest
                    or genesis_intent.journal_content_hash_ref
                    != self._journal_content_hash(entries)
                ):
                    raise GoalRuntimeCorruptionError(
                        "GOAL_JOURNAL_GENESIS_INTENT_STATE_MISMATCH"
                    )
                if repair_manifest:
                    self._delete_genesis_intent()
            return entries
        if len(entries) == manifest.entry_count + 1:
            previous_manifest = self._build_head_manifest(entries[:-1])
            if manifest == previous_manifest:
                if repair_manifest:
                    self._write_head_manifest(exact_manifest)
                return entries
        raise GoalRuntimeCorruptionError("GOAL_JOURNAL_HEAD_MANIFEST_MISMATCH")

    def _load_consistent_entries(self) -> list[GoalJournalEntry]:
        for _attempt in range(3):
            try:
                with self.consistent_read():
                    return self._load_entries()
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_JOURNAL_GENERATION_UNSTABLE")

    @contextmanager
    def consistent_read(self) -> Iterator[None]:
        with _nonmutating_goal_runtime_read_lock(
            self.state_dir / ".locks",
            "goal-journal",
            generation_paths=(
                self.path,
                self.head_path,
                self.genesis_intent_path,
            ),
        ):
            yield

    def _load_genesis_intent(self) -> GoalJournalGenesisIntent | None:
        raw_content = _read_bounded_regular_utf8(
            self.genesis_intent_path,
            max_bytes=MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES,
            missing_ok=True,
            capacity_error="GOAL_JOURNAL_GENESIS_INTENT_CAPACITY_EXCEEDED",
            corruption_error="GOAL_JOURNAL_GENESIS_INTENT_CORRUPT",
        )
        if raw_content is None:
            return None
        try:
            if not raw_content.strip():
                raise GoalRuntimeCorruptionError("GOAL_JOURNAL_GENESIS_INTENT_EMPTY")
            intent = GoalJournalGenesisIntent.model_validate_json(raw_content)
            if (
                intent.entry.previous_entry_hash_ref is not None
                or intent.entry.goal_version != 1
                or intent.entry.goal.version != 1
                or intent.entry.operation != GoalJournalOperation.create.value
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_GENESIS_INTENT_ENTRY_BINDING_MISMATCH"
                )
            expected_entry_ref = _sha256_ref(
                "goal-journal-entry-ref",
                {
                    "goal_ref": intent.entry.goal_ref,
                    "version": intent.entry.goal_version,
                    "operation": intent.entry.operation,
                },
            )
            if intent.entry.entry_ref != expected_entry_ref:
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_GENESIS_INTENT_ENTRY_BINDING_MISMATCH"
                )
            if intent.entry.entry_hash_ref != self._entry_hash(intent.entry):
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_GENESIS_INTENT_ENTRY_HASH_MISMATCH"
                )
            expected_manifest = self._build_head_manifest([intent.entry])
            if intent.head_manifest != expected_manifest:
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_GENESIS_INTENT_HEAD_MISMATCH"
                )
            if intent.journal_content_hash_ref != self._journal_content_hash(
                [intent.entry]
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_JOURNAL_GENESIS_INTENT_CONTENT_MISMATCH"
                )
            return intent
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_JOURNAL_GENESIS_INTENT_CORRUPT"
            ) from exc

    def _load_head_manifest(self) -> GoalJournalHeadManifest | None:
        raw_content = _read_bounded_regular_utf8(
            self.head_path,
            max_bytes=MAX_GOAL_JOURNAL_HEAD_BYTES,
            missing_ok=True,
            capacity_error="GOAL_JOURNAL_HEAD_MANIFEST_CAPACITY_EXCEEDED",
            corruption_error="GOAL_JOURNAL_HEAD_MANIFEST_CORRUPT",
        )
        if raw_content is None:
            return None
        try:
            if not raw_content.strip():
                raise GoalRuntimeCorruptionError("GOAL_JOURNAL_HEAD_MANIFEST_EMPTY")
            return GoalJournalHeadManifest.model_validate_json(raw_content)
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_JOURNAL_HEAD_MANIFEST_CORRUPT"
            ) from exc

    @staticmethod
    def _build_head_manifest(
        entries: list[GoalJournalEntry],
    ) -> GoalJournalHeadManifest:
        if not entries:
            raise GoalRuntimeCorruptionError("GOAL_JOURNAL_HEAD_MANIFEST_EMPTY")
        return GoalJournalHeadManifest(
            entry_count=len(entries),
            head_entry_hash_ref=entries[-1].entry_hash_ref,
            idempotency_set_hash_ref=_sha256_ref(
                "idempotency-set-hash-ref:goal-journal",
                sorted(
                    (
                        entry.idempotency_ref,
                        entry.request_fingerprint_ref,
                    )
                    for entry in entries
                ),
            ),
        )

    def _write_head_manifest(self, manifest: GoalJournalHeadManifest) -> None:
        content = manifest.model_dump_json() + "\n"
        if len(content.encode("utf-8")) > MAX_GOAL_JOURNAL_HEAD_BYTES:
            raise GoalRuntimeError("GOAL_JOURNAL_HEAD_MANIFEST_CAPACITY_EXCEEDED")
        _atomic_write(self.head_path, content)

    @staticmethod
    def _journal_content(entries: list[GoalJournalEntry]) -> str:
        return "".join(entry.model_dump_json() + "\n" for entry in entries)

    @classmethod
    def _journal_content_hash(cls, entries: list[GoalJournalEntry]) -> str:
        return _sha256_ref(
            "journal-content-hash-ref:goal-journal",
            cls._journal_content(entries),
        )

    def _write_genesis_intent(self, intent: GoalJournalGenesisIntent) -> None:
        content = intent.model_dump_json() + "\n"
        if len(content.encode("utf-8")) > MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES:
            raise GoalRuntimeError("GOAL_JOURNAL_GENESIS_INTENT_CAPACITY_EXCEEDED")
        _atomic_write(self.genesis_intent_path, content)

    def _delete_genesis_intent(self) -> None:
        try:
            self.genesis_intent_path.unlink(missing_ok=True)
        except OSError as exc:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc

    def _install_genesis_intent(self, intent: GoalJournalGenesisIntent) -> None:
        _atomic_write(self.path, self._journal_content([intent.entry]))
        self._write_head_manifest(intent.head_manifest)
        self._delete_genesis_intent()

    def _write_entries(self, entries: list[GoalJournalEntry]) -> None:
        content = self._journal_content(entries)
        if (
            len(entries) > MAX_GOAL_JOURNAL_ENTRIES
            or len(content.encode("utf-8")) > MAX_GOAL_JOURNAL_BYTES
        ):
            raise GoalRuntimeError("GOAL_JOURNAL_CAPACITY_EXCEEDED")
        first_generation = (
            len(entries) == 1
            and not _path_generation(self.path)[0]
            and not _path_generation(self.head_path)[0]
        )
        if first_generation:
            manifest = self._build_head_manifest(entries)
            intent = GoalJournalGenesisIntent(
                entry=entries[0],
                head_manifest=manifest,
                journal_content_hash_ref=self._journal_content_hash(entries),
            )
            self._write_genesis_intent(intent)
            self._install_genesis_intent(intent)
            return
        _atomic_write(self.path, content)
        self._write_head_manifest(self._build_head_manifest(entries))


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
        self._lock_state = threading.local()

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "run-events"):
            depth = getattr(self._lock_state, "exclusive_depth", 0)
            self._lock_state.exclusive_depth = depth + 1
            try:
                yield
            finally:
                self._lock_state.exclusive_depth = depth

    @contextmanager
    def consistent_read(self) -> Iterator[None]:
        if getattr(self._lock_state, "exclusive_depth", 0):
            yield
            return
        with _nonmutating_goal_runtime_read_lock(
            self.state_dir / ".locks",
            "run-events",
            generation_paths=(self.path, self.idempotency_path),
        ):
            yield

    def _load_consistent_generation(
        self,
    ) -> tuple[
        list[DurableRunEvent],
        dict[tuple[str, str], RunEventIdempotencyTombstone],
    ]:
        for _attempt in range(3):
            try:
                with self.consistent_read():
                    events = self._load_events()
                    return events, self._load_idempotency_tombstones(events)
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("RUN_EVENT_GENERATION_UNSTABLE")

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
                for ref, reservation in (self._load_projection_reservations().items())
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
            self._assert_projection_capacity(
                events,
                tombstones.values(),
                required_slots=reserved_slots + required_slots,
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
        tombstones = self._load_idempotency_tombstones(self._load_events())
        missing_key_refs = self._missing_runtime_projection_key_refs(
            record,
            tombstones,
        )
        if missing_key_refs is None:
            raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_RECEIPT_REQUIRED")
        if reservation is None:
            if not missing_key_refs:
                return
            raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_RESERVATION_MISSING")
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
                    reservations[reservation_ref] = self._build_projection_reservation(
                        reservation_ref,
                        operation_idempotency_ref=(
                            reservation.operation_idempotency_ref
                        ),
                        holder_count=reservation.holder_count - 1,
                        slot_count=reservation.slot_count,
                        allowed_event_key_refs=(reservation.allowed_event_key_refs),
                        reserved_at=reservation.reserved_at,
                    )
                else:
                    reservations.pop(reservation_ref)
                self._write_projection_reservations(reservations.values())

    def _append_locked(
        self,
        validated: DurableRunEventAppendRequest,
        *,
        reservation_ref: str | None = None,
    ) -> DurableRunEvent:
        events = self._load_events()
        persisted_tombstones = self._load_persisted_idempotency_tombstones()
        tombstones = self._load_idempotency_tombstones(events)
        if tombstones != persisted_tombstones:
            # A prior append may have installed the event journal immediately
            # before a process loss. Close that single recoverable generation
            # before installing any different event so repeated interruptions
            # can never advance the journal two generations past provenance.
            self._write_idempotency_tombstones(tombstones.values())
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
            reservations.get(reservation_ref) if reservation_ref is not None else None
        )
        expected_fingerprint = self._request_fingerprint(validated)
        prior = tombstones.get(key)
        if prior is not None:
            if prior.request_fingerprint_ref != expected_fingerprint:
                raise GoalIdempotencyConflictError("RUN_EVENT_IDEMPOTENCY_CONFLICT")
            self._write_idempotency_tombstones(tombstones.values())
            return prior.event.model_copy(deep=True)
        if reservation_ref is not None and (
            reservation is None
            or event_key_ref not in reservation.allowed_event_key_refs
        ):
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_PROJECTION_RESERVATION_BINDING_MISMATCH"
            )
        reserved_slots = sum(item.slot_count for item in reservations.values())
        if (
            reservation is None
            and len(tombstones) + reserved_slots >= MAX_RUN_EVENT_IDEMPOTENCY_RECORDS
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
                and validated.receipt_refs[0] in event.receipt_refs
                and validated.proof_refs[0] in event.proof_refs
                and event.criterion_verifier_bindings
                == validated.criterion_verifier_bindings
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
            criterion_verifier_bindings=validated.criterion_verifier_bindings,
            goal_ref=validated.goal_ref,
            plan_ref=validated.plan_ref,
            idempotency_ref=validated.idempotency_ref,
            authority_decision_ref=validated.authority_decision_ref,
            predecessor_hash_ref=predecessor,
            event_hash_ref="event-hash-ref:pending",
        )
        event = draft.model_copy(update={"event_hash_ref": self._event_hash(draft)})
        next_events = self._apply_retention([*events, event], validated.run_ref)
        tombstone = self._build_idempotency_tombstone(event, expected_fingerprint)
        tombstones[key] = tombstone
        remaining_reserved_slots = reserved_slots - (
            1 if reservation is not None else 0
        )
        self._assert_projection_capacity(
            next_events,
            tombstones.values(),
            required_slots=remaining_reserved_slots,
        )
        self._write_events(next_events)
        self._write_idempotency_tombstones(tombstones.values())
        if reservation is not None and reservation_ref is not None:
            remaining = [
                ref
                for ref in reservation.allowed_event_key_refs
                if ref != event_key_ref
            ]
            if remaining:
                reservations[reservation_ref] = self._build_projection_reservation(
                    reservation_ref,
                    operation_idempotency_ref=(reservation.operation_idempotency_ref),
                    holder_count=reservation.holder_count,
                    slot_count=len(remaining),
                    allowed_event_key_refs=remaining,
                    reserved_at=reservation.reserved_at,
                )
            else:
                reservations.pop(reservation_ref, None)
            self._write_projection_reservations(reservations.values())
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
        events, _tombstones = self._load_consistent_generation()
        return self._replay_from_events(
            events,
            run_ref=run_ref,
            after_sequence=after_sequence,
            limit=bounded_limit,
        )

    @staticmethod
    def _replay_from_events(
        events: list[DurableRunEvent],
        *,
        run_ref: str,
        after_sequence: int,
        limit: int,
    ) -> RunEventReplayReadModel:
        same_run = [event for event in events if event.run_ref == run_ref]
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
        selected = [event for event in same_run if event.sequence > after_sequence][
            :limit
        ]
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
        events, _tombstones = self._load_consistent_generation()
        return self._summaries_from_events(events)

    @staticmethod
    def _summaries_from_events(
        events: list[DurableRunEvent],
    ) -> list[RunEventStreamSummary]:
        grouped: dict[str, list[DurableRunEvent]] = {}
        for event in events:
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
        events, _tombstones = self._load_consistent_generation()
        return self._retained_from_events(
            events,
            run_ref=run_ref,
            limit=bounded_limit,
        )

    @staticmethod
    def _retained_from_events(
        events: list[DurableRunEvent],
        *,
        run_ref: str | None,
        limit: int,
    ) -> list[DurableRunEvent]:
        if run_ref is not None:
            events = [event for event in events if event.run_ref == run_ref]
        return [event.model_copy(deep=True) for event in events[-limit:]]

    def has_completion_evidence(
        self,
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> bool:
        validate_execution_ref(run_ref, "run_ref")
        events, tombstones = self._load_consistent_generation()
        return (
            self._completion_receipt_event(
                events,
                tombstones,
                run_ref=run_ref,
                receipt_ref=receipt_ref,
                proof_ref=proof_ref,
                goal_ref=goal_ref,
            )
            is not None
        )

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
            raise GoalTransitionDeniedError("GOAL_COMPLETION_DURABLE_RECEIPT_NOT_FOUND")
        if same_run[-1].event_kind in TERMINAL_RUN_EVENT_KINDS:
            raise GoalTransitionDeniedError("GOAL_COMPLETION_TERMINAL_STREAM_FENCE")
        active_reservations = [
            reservation
            for reservation in self._load_projection_reservations().values()
            if reservation.expires_at > utc_now()
        ]
        self._assert_projection_capacity(
            events,
            tombstones.values(),
            required_slots=(
                1 + sum(reservation.slot_count for reservation in active_reservations)
            ),
            event_byte_credit=self._completion_retention_byte_credit(
                events,
                run_ref,
            ),
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
        matching = [
            event
            for event in candidates
            if event.run_ref == run_ref
            and event.goal_ref == goal_ref
            and event.event_kind == DurableRunEventKind.receipt_recorded.value
            and receipt_ref in event.receipt_refs
            and proof_ref in event.proof_refs
        ]
        return max(matching, key=lambda event: event.sequence, default=None)

    def run_type(self, run_ref: str) -> AcceptedLocalRunType:
        validate_execution_ref(run_ref, "run_ref")
        events, _tombstones = self._load_consistent_generation()
        for event in events:
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
            "criterion_verifier_bindings": [
                binding.model_dump(mode="json")
                for binding in event.criterion_verifier_bindings
            ],
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
        projection_kind = _runtime_receipt_projection_kind(record)
        projection_idempotency_prefix = (
            "idempotency-ref:runtime-receipt-recorded"
            if projection_kind == DurableRunEventKind.receipt_recorded
            else "idempotency-ref:runtime-failed-terminal"
        )
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
                    projection_idempotency_prefix,
                    {
                        "invocation_ref": run_ref,
                        "receipt_ref": record.receipt.receipt_ref,
                    },
                ),
            ),
        )
        return [
            self._event_key_ref(*key) for key in expected_keys if key not in tombstones
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
                validated = RuntimeInvocationRecord.model_validate(record.model_dump())
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
            + timedelta(seconds=RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS),
            reservation_hash_ref="reservation-hash-ref:pending",
        )
        return draft.model_copy(
            update={"reservation_hash_ref": self._reservation_hash(draft)}
        )

    def _load_projection_reservations(
        self,
    ) -> dict[str, RunEventProjectionReservation]:
        reservations: dict[str, RunEventProjectionReservation] = {}
        raw_content = _read_bounded_regular_utf8(
            self.reservations_path,
            max_bytes=MAX_RUN_EVENT_PROJECTION_RESERVATION_BYTES,
            missing_ok=True,
            capacity_error="RUN_EVENT_PROJECTION_RESERVATION_STORE_CAPACITY_EXCEEDED",
            corruption_error="RUN_EVENT_PROJECTION_RESERVATION_STORE_CORRUPT",
        )
        if raw_content is None:
            return reservations
        try:
            for raw_line in raw_content.splitlines():
                if not raw_line.strip():
                    continue
                reservation = RunEventProjectionReservation.model_validate_json(
                    raw_line
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
            reservation.model_dump_json() + "\n" for reservation in reservations
        )
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_PROJECTION_RESERVATION_BYTES:
            raise GoalRuntimeError(
                "RUN_EVENT_PROJECTION_RESERVATION_STORE_CAPACITY_EXCEEDED"
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
        tombstones = self._load_persisted_idempotency_tombstones()
        try:
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
                tombstones[key] = self._build_idempotency_tombstone(event, fingerprint)
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

    def _load_persisted_idempotency_tombstones(
        self,
    ) -> dict[tuple[str, str], RunEventIdempotencyTombstone]:
        tombstones: dict[tuple[str, str], RunEventIdempotencyTombstone] = {}
        raw_content = _read_bounded_regular_utf8(
            self.idempotency_path,
            max_bytes=MAX_RUN_EVENT_IDEMPOTENCY_BYTES,
            missing_ok=True,
            capacity_error="RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED",
            corruption_error="RUN_EVENT_IDEMPOTENCY_STORE_CORRUPT",
        )
        if raw_content is None:
            return tombstones
        try:
            for raw_line in raw_content.splitlines():
                if not raw_line.strip():
                    continue
                tombstone = RunEventIdempotencyTombstone.model_validate_json(raw_line)
                if tombstone.tombstone_hash_ref != self._tombstone_hash(tombstone):
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_TOMBSTONE_HASH_MISMATCH"
                    )
                key = (tombstone.run_ref, tombstone.idempotency_ref)
                if key in tombstones:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_IDEMPOTENCY_TOMBSTONE_DUPLICATE"
                    )
                tombstones[key] = tombstone
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
        raw_content = _read_bounded_regular_utf8(
            self.path,
            max_bytes=MAX_RUN_EVENT_STORE_BYTES,
            missing_ok=True,
            capacity_error="RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED",
            corruption_error="RUN_EVENT_STORE_CORRUPT",
        )
        if raw_content is None:
            self._assert_no_orphaned_idempotency_history()
            return []
        events: list[DurableRunEvent] = []
        grouped: dict[str, list[DurableRunEvent]] = {}
        idempotency: set[tuple[str, str]] = set()
        try:
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
                    raise GoalRuntimeCorruptionError("RUN_EVENT_REF_BINDING_MISMATCH")
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
                        raise GoalRuntimeCorruptionError("RUN_EVENT_TYPE_SUBSTITUTION")
                if same_run[0].sequence == 1:
                    if same_run[0].predecessor_hash_ref is not None:
                        raise GoalRuntimeCorruptionError(
                            "RUN_EVENT_FIRST_PREDECESSOR_INVALID"
                        )
                elif same_run[0].predecessor_hash_ref is None:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_RETENTION_ANCHOR_MISSING"
                    )
            self._assert_retained_suffix_matches_tombstones(
                events,
                self._load_persisted_idempotency_tombstones().values(),
            )
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError("RUN_EVENT_STORE_CORRUPT") from exc
        return events

    def _assert_retained_suffix_matches_tombstones(
        self,
        events: list[DurableRunEvent],
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        retained_by_run: dict[str, list[DurableRunEvent]] = {}
        accepted_by_run: dict[str, list[DurableRunEvent]] = {}
        for event in events:
            retained_by_run.setdefault(event.run_ref, []).append(event)
        for tombstone in tombstones:
            accepted_by_run.setdefault(tombstone.run_ref, []).append(tombstone.event)
        for run_ref, accepted in accepted_by_run.items():
            accepted.sort(key=lambda event: event.sequence)
            retained = retained_by_run.get(run_ref, [])
            if not retained:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_JOURNAL_RETAINED_SUFFIX_MISMATCH"
                )
            accepted_last_sequence = accepted[-1].sequence
            retained_last_sequence = retained[-1].sequence
            journal_ahead_by = retained_last_sequence - accepted_last_sequence
            if journal_ahead_by not in {0, 1}:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_JOURNAL_RETAINED_SUFFIX_MISMATCH"
                )
            expected_accepted_count = min(
                len(accepted),
                self.retention_limit - journal_ahead_by,
            )
            expected_accepted_suffix = accepted[-expected_accepted_count:]
            retained_accepted_suffix = [
                event for event in retained if event.sequence <= accepted_last_sequence
            ]
            if retained_accepted_suffix != expected_accepted_suffix:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_JOURNAL_RETAINED_SUFFIX_MISMATCH"
                )
            if journal_ahead_by == 1 and (
                len(retained) != len(retained_accepted_suffix) + 1
                or retained[-1].sequence != accepted_last_sequence + 1
            ):
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_JOURNAL_RETAINED_SUFFIX_MISMATCH"
                )

    def _assert_no_orphaned_idempotency_history(self) -> None:
        raw_content = _read_bounded_regular_utf8(
            self.idempotency_path,
            max_bytes=MAX_RUN_EVENT_IDEMPOTENCY_BYTES,
            missing_ok=True,
            capacity_error="RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED",
            corruption_error="RUN_EVENT_IDEMPOTENCY_STORE_CORRUPT",
        )
        if raw_content is not None and raw_content.strip():
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_JOURNAL_MISSING_WITH_IDEMPOTENCY_HISTORY"
            )

    def _apply_retention(
        self, events: list[DurableRunEvent], run_ref: str
    ) -> list[DurableRunEvent]:
        same_run = [event for event in events if event.run_ref == run_ref]
        if len(same_run) <= self.retention_limit:
            return events
        keep_refs = {event.event_ref for event in same_run[-self.retention_limit :]}
        return [
            event
            for event in events
            if event.run_ref != run_ref or event.event_ref in keep_refs
        ]

    def _write_events(self, events: list[DurableRunEvent]) -> None:
        content = "".join(event.model_dump_json() + "\n" for event in events)
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_STORE_BYTES:
            raise GoalRuntimeError("RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED")
        _atomic_write(self.path, content)

    @staticmethod
    def _assert_encoded_store_capacity(
        events: Iterable[DurableRunEvent],
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        event_content = "".join(event.model_dump_json() + "\n" for event in events)
        tombstone_content = "".join(
            tombstone.model_dump_json() + "\n" for tombstone in tombstones
        )
        if len(event_content.encode("utf-8")) > MAX_RUN_EVENT_STORE_BYTES:
            raise GoalRuntimeError("RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED")
        if len(tombstone_content.encode("utf-8")) > MAX_RUN_EVENT_IDEMPOTENCY_BYTES:
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED")

    @staticmethod
    def _assert_projection_capacity(
        events: Iterable[DurableRunEvent],
        tombstones: Iterable[RunEventIdempotencyTombstone],
        *,
        required_slots: int,
        event_byte_credit: int = 0,
    ) -> None:
        """Reserve worst-case encoded space before any runtime or goal mutation."""

        event_rows = list(events)
        tombstone_rows = list(tombstones)
        if len(tombstone_rows) + required_slots > MAX_RUN_EVENT_IDEMPOTENCY_RECORDS:
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED")
        event_bytes = len(
            "".join(event.model_dump_json() + "\n" for event in event_rows).encode(
                "utf-8"
            )
        )
        tombstone_bytes = len(
            "".join(
                tombstone.model_dump_json() + "\n" for tombstone in tombstone_rows
            ).encode("utf-8")
        )
        if (
            event_bytes
            + max(
                0,
                required_slots * MAX_RESERVED_RUN_EVENT_BYTES - event_byte_credit,
            )
            > MAX_RUN_EVENT_STORE_BYTES
        ):
            raise GoalRuntimeError("RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED")
        if (
            tombstone_bytes + required_slots * MAX_RESERVED_RUN_EVENT_TOMBSTONE_BYTES
            > MAX_RUN_EVENT_IDEMPOTENCY_BYTES
        ):
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED")

    def _completion_retention_byte_credit(
        self,
        events: Iterable[DurableRunEvent],
        run_ref: str,
    ) -> int:
        same_run = [event for event in events if event.run_ref == run_ref]
        if len(same_run) < self.retention_limit:
            return 0
        return len((same_run[0].model_dump_json() + "\n").encode("utf-8"))

    def _write_idempotency_tombstones(
        self,
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        content = "".join(
            tombstone.model_dump_json() + "\n" for tombstone in tombstones
        )
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_IDEMPOTENCY_BYTES:
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED")
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
        _validate_goal_runtime_state_dir_for_read(self.state_dir)
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

    def aggregate_read_snapshot(
        self,
        *,
        run_ref: str | None,
        after_sequence: int,
        limit: int,
    ) -> tuple[
        RunEventReplayReadModel | None,
        list[DurableRunEvent],
        list[RunEventStreamSummary],
        GoalLifecycleReadModel,
    ]:
        """Read the event and goal projections from one canonical generation.

        The lock order is always run-events then goal-journal, matching the
        only mutation that spans both stores. Missing first-generation lock
        files retain the bounded optimistic-generation checks implemented by
        the non-mutating read lock.
        """

        if run_ref is not None:
            validate_execution_ref(run_ref, "run_ref")
        if after_sequence < 0:
            raise ValueError("RUN_EVENT_CURSOR_INVALID")
        bounded_limit = max(1, min(int(limit), MAX_REPLAY_EVENTS))
        for _attempt in range(3):
            try:
                with self._events.consistent_read():
                    with self.goals.consistent_read():
                        events = self._events._load_events()
                        self._events._load_idempotency_tombstones(events)
                        entries = self.goals._load_entries()
                        replay = (
                            self._events._replay_from_events(
                                events,
                                run_ref=run_ref,
                                after_sequence=after_sequence,
                                limit=bounded_limit,
                            )
                            if run_ref is not None
                            else None
                        )
                        retained = (
                            replay.events
                            if replay is not None
                            else self._events._retained_from_events(
                                events,
                                run_ref=None,
                                limit=bounded_limit,
                            )
                        )
                        return (
                            replay,
                            retained,
                            self._events._summaries_from_events(events),
                            self.goals._read_model_from_entries(
                                entries,
                                include_cleared=True,
                            ),
                        )
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_RUNTIME_AGGREGATE_GENERATION_UNSTABLE")

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
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        _validate_goal_mutation_approval_binding(
            approval_binding,
            operation=f"transition-{validated.transition}",
            subject_ref=goal_ref,
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=idempotency_ref,
        )
        self.reconcile_durable_events()
        replayed = self.goals.replay_transition(
            goal_ref,
            validated,
            idempotency_ref=idempotency_ref,
        )
        if replayed is not None:
            if (
                validated.transition == GoalTransitionKind.verify_completion.value
                and replayed.state == GoalState.verified_complete.value
            ):
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
        event_lock = self._events.exclusive() if evidence is not None else nullcontext()
        completion_plan_ref: str | None = None
        completion_criterion_verifier_bindings: list[
            RuntimeCriterionVerificationBinding
        ] = []
        with event_lock:
            if evidence is not None:
                current = self.goals.get(goal_ref)
                if evidence.goal_ref != goal_ref:
                    raise GoalTransitionDeniedError("GOAL_COMPLETION_GOAL_REF_MISMATCH")
                if evidence.goal_version != current.version:
                    raise GoalVersionConflictError("GOAL_COMPLETION_VERSION_CONFLICT")
                if evidence.run_ref not in current.links.run_refs:
                    raise GoalTransitionDeniedError("GOAL_COMPLETION_RUN_NOT_LINKED")
                receipt_event = self._events.assert_completion_appendable(
                    run_ref=evidence.run_ref,
                    receipt_ref=evidence.receipt_ref,
                    proof_ref=evidence.proof_ref,
                    goal_ref=goal_ref,
                )
                expected_criterion_refs = [
                    build_goal_criterion_ref(
                        current,
                        criterion_index=index,
                        criterion_summary=criterion,
                    )
                    for index, criterion in enumerate(current.success_criteria)
                ]
                matching_bindings = {
                    binding.criterion_ref: binding
                    for binding in receipt_event.criterion_verifier_bindings
                    if binding.goal_ref == current.goal_ref
                    and binding.goal_version == current.version
                }
                if set(matching_bindings) != set(expected_criterion_refs):
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_CRITERION_VERIFIER_BINDING_MISMATCH"
                    )
                ordered_bindings = [
                    matching_bindings[criterion_ref]
                    for criterion_ref in expected_criterion_refs
                ]
                if any(
                    binding.verifier_ref != GOAL_COMPLETION_VERIFIER_REF
                    or binding.proof_ref not in receipt_event.proof_refs
                    or binding.evaluator_receipt_ref not in receipt_event.proof_refs
                    for binding in ordered_bindings
                ):
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_CRITERION_VERIFIER_NOT_TRUSTED"
                    )
                derived_criterion_proof_refs = [
                    binding.proof_ref for binding in ordered_bindings
                ]
                if evidence.criterion_proof_refs != derived_criterion_proof_refs:
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_CRITERION_PROOF_BINDING_MISMATCH"
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
                if evidence.verifier_ref != GOAL_COMPLETION_VERIFIER_REF:
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_VERIFIER_NOT_TRUSTED"
                    )
                expected_evidence_ref = build_goal_completion_evidence_ref(
                    current,
                    run_ref=evidence.run_ref,
                    receipt_ref=evidence.receipt_ref,
                    proof_ref=evidence.proof_ref,
                    criterion_verifier_bindings=ordered_bindings,
                    plan_ref=completion_plan_ref,
                )
                if evidence.evidence_ref != expected_evidence_ref:
                    raise GoalTransitionDeniedError(
                        "GOAL_COMPLETION_VERIFIER_BINDING_MISMATCH"
                    )
                completion_verified = True
                completion_criterion_verifier_bindings = [
                    RuntimeCriterionVerificationBinding.model_validate(
                        binding.model_dump(mode="json")
                    )
                    for binding in ordered_bindings
                ]
            goal = self.goals.transition(
                goal_ref,
                validated,
                idempotency_ref=idempotency_ref,
                approval_binding=approval_binding,
                completion_verified=completion_verified,
                completion_plan_ref=completion_plan_ref,
                completion_criterion_verifier_bindings=(
                    completion_criterion_verifier_bindings
                ),
            )
            if (
                validated.transition == GoalTransitionKind.verify_completion.value
                and goal.state == GoalState.verified_complete.value
            ):
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
                        goal.completion_source_goal_version,
                    )
                ) and (
                    len(goal.completion_criterion_proof_refs)
                    == len(goal.success_criteria)
                    == len(goal.completion_criterion_verifier_bindings)
                )
                if (
                    goal.state
                    not in {
                        GoalState.verified_complete.value,
                        GoalState.cleared.value,
                    }
                    or not completion_bound
                ):
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

        with _normalized_goal_runtime_lock(self.goals._locks, "goal-journal"):
            self.goals._load_entries(repair_manifest=True)
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
            or goal.completion_evidence_ref is None
            or goal.completion_verifier_ref is None
            or goal.completion_source_goal_version is None
            or not (
                len(goal.completion_criterion_proof_refs)
                == len(goal.success_criteria)
                == len(goal.completion_criterion_verifier_bindings)
            )
        ):
            raise GoalRuntimeCorruptionError("GOAL_COMPLETION_EVENT_BINDING_INCOMPLETE")
        return self._events._append_locked(
            DurableRunEventAppendRequest.model_validate(
                {
                    "run_ref": goal.completion_run_ref,
                    "run_type": self._events.run_type(goal.completion_run_ref),
                    "event_kind": DurableRunEventKind.completion_verified,
                    "safe_summary": (
                        "Deterministic receipt evidence verified the linked "
                        "goal completion."
                    ),
                    "proof_refs": list(
                        dict.fromkeys(
                            [
                                goal.completion_proof_ref,
                                goal.completion_evidence_ref,
                                *goal.completion_criterion_proof_refs,
                                *(
                                    binding.evaluator_receipt_ref
                                    for binding in (
                                        goal.completion_criterion_verifier_bindings
                                    )
                                ),
                            ]
                        )
                    ),
                    "receipt_refs": list(
                        dict.fromkeys(
                            [
                                goal.completion_receipt_ref,
                                *(
                                    binding.evaluator_receipt_ref
                                    for binding in (
                                        goal.completion_criterion_verifier_bindings
                                    )
                                ),
                            ]
                        )
                    ),
                    "criterion_verifier_bindings": [
                        DurableCriterionVerifierBinding.model_validate(
                            binding.model_dump(mode="json")
                        )
                        for binding in goal.completion_criterion_verifier_bindings
                    ],
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
        if validated.event_kind in {
            DurableRunEventKind.receipt_recorded.value,
            *TERMINAL_RUN_EVENT_KINDS,
        }:
            raise GoalTransitionDeniedError("RUN_EVENT_TRUSTED_PRODUCER_REQUIRED")
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
            self._events.release_runtime_projection_reservation(reservation_ref)

    def record_accepted_runtime_invocation(
        self,
        record: RuntimeInvocationRecord,
        *,
        invocation_store: RuntimeInvocationStore,
        reservation_ref: str | None = None,
    ) -> list[DurableRunEvent]:
        """Project one accepted RuntimeGateway receipt into durable run events."""

        from ultimate_ai_agent.core.runtime_gateway.contracts import (
            RuntimeAuthority,
            RuntimeInvocationRecord,
            RuntimeInvocationStatus,
        )
        from ultimate_ai_agent.core.runtime_gateway.storage import (
            RuntimeInvocationStorageError,
        )

        validated = RuntimeInvocationRecord.model_validate(record.model_dump())
        try:
            stored_record = invocation_store.get_invocation(validated.invocation_ref)
        except RuntimeInvocationStorageError as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_DURABLE_INVOCATION_NOT_FOUND"
            ) from exc
        try:
            durable_record = RuntimeInvocationRecord.model_validate(
                stored_record.model_dump()
            )
        except (AttributeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_DURABLE_INVOCATION_INVALID"
            ) from exc
        if durable_record.invocation_ref != validated.invocation_ref:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_DURABLE_INVOCATION_REF_MISMATCH"
            )
        validated = durable_record
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
                    invocation_store=invocation_store,
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
                    *(
                        binding.proof_ref
                        for binding in receipt.criterion_verification_bindings
                    ),
                    *(
                        binding.evaluator_receipt_ref
                        for binding in receipt.criterion_verification_bindings
                    ),
                ]
            )
        )
        projection_kind = _runtime_receipt_projection_kind(validated)
        projection_idempotency_prefix = (
            "idempotency-ref:runtime-receipt-recorded"
            if projection_kind == DurableRunEventKind.receipt_recorded
            else "idempotency-ref:runtime-failed-terminal"
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
                    event_kind=projection_kind,
                    safe_summary=(
                        "RuntimeGateway recorded the successful accepted local "
                        "invocation receipt with redacted evidence refs."
                        if projection_kind == DurableRunEventKind.receipt_recorded
                        else (
                            "RuntimeGateway recorded the unsuccessful local "
                            "invocation as a proof-backed terminal failure."
                        )
                    ),
                    proof_refs=proof_refs,
                    receipt_refs=[receipt.receipt_ref],
                    criterion_verifier_bindings=[
                        DurableCriterionVerifierBinding.model_validate(
                            binding.model_dump(mode="json")
                        )
                        for binding in receipt.criterion_verification_bindings
                    ],
                    goal_ref=goal_ref,
                    plan_ref=plan_ref,
                    idempotency_ref=_sha256_ref(
                        projection_idempotency_prefix,
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
        *,
        invocation_store: RuntimeInvocationStore,
    ) -> list[DurableRunEvent]:
        self.reconcile_durable_events()
        projected: list[DurableRunEvent] = []
        for record in self._events.unprojected_runtime_invocations(records):
            projected.extend(
                self.record_accepted_runtime_invocation(
                    record,
                    invocation_store=invocation_store,
                )
            )
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
        raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_BINDING_MISMATCH")


def _initialize_goal_runtime_state_dir(state_dir: Path) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        state_metadata = os.lstat(state_dir)
        if not stat.S_ISDIR(state_metadata.st_mode):
            raise OSError("goal runtime state directory must be a real directory")
        os.chmod(state_dir, 0o700)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc


def _validate_goal_runtime_state_dir_for_read(state_dir: Path) -> None:
    try:
        state_metadata = os.lstat(state_dir)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
    if not stat.S_ISDIR(state_metadata.st_mode):
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")


@contextmanager
def _normalized_goal_runtime_lock(
    manager: FileSingleWriterLockManager,
    writer_key: str,
) -> Iterator[None]:
    entered = False
    try:
        with manager.acquire(writer_key):
            entered = True
            yield
    except OSError as exc:
        if not entered:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
        raise


@contextmanager
def _nonmutating_goal_runtime_read_lock(
    lock_dir: Path,
    writer_key: str,
    *,
    generation_paths: tuple[Path, ...] = (),
) -> Iterator[None]:
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in writer_key)
    lock_path = lock_dir / f"{safe_name}.lock"
    if not _path_generation(lock_path)[0]:
        before = tuple(
            _path_generation(path) for path in (*generation_paths, lock_path)
        )
        try:
            yield
        finally:
            after = tuple(
                _path_generation(path) for path in (*generation_paths, lock_path)
            )
            if after != before:
                raise _GoalRuntimeGenerationChanged
        return
    descriptor: int | None = None
    try:
        descriptor = os.open(
            lock_path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(lock_path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise OSError("goal runtime read lock must be a regular file")
        try:
            import fcntl
        except ImportError:
            fcntl = None
        if fcntl is not None:
            fcntl.flock(descriptor, fcntl.LOCK_SH)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_bounded_regular_utf8(
    path: Path,
    *,
    max_bytes: int,
    missing_ok: bool,
    capacity_error: str,
    corruption_error: str,
) -> str | None:
    """Read one immutable regular-file identity without following links."""

    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except FileNotFoundError:
        if missing_ok:
            return None
        raise GoalRuntimeCorruptionError(corruption_error) from None
    except OSError as exc:
        raise GoalRuntimeCorruptionError(corruption_error) from exc

    try:
        opened = os.fstat(descriptor)
        linked = os.lstat(path)
        opened_identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(linked.st_mode)
            or opened.st_nlink != 1
            or linked.st_nlink != 1
            or opened_identity != (linked.st_dev, linked.st_ino)
        ):
            raise GoalRuntimeCorruptionError(corruption_error)
        if opened.st_size > max_bytes:
            raise GoalRuntimeCorruptionError(capacity_error)

        content = bytearray()
        while len(content) <= max_bytes:
            chunk = os.read(
                descriptor,
                min(64 * 1024, max_bytes + 1 - len(content)),
            )
            if not chunk:
                break
            content.extend(chunk)
        if len(content) > max_bytes:
            raise GoalRuntimeCorruptionError(capacity_error)

        closed_over = os.fstat(descriptor)
        still_linked = os.lstat(path)
        if (
            not stat.S_ISREG(closed_over.st_mode)
            or not stat.S_ISREG(still_linked.st_mode)
            or closed_over.st_nlink != 1
            or still_linked.st_nlink != 1
            or (closed_over.st_dev, closed_over.st_ino) != opened_identity
            or (still_linked.st_dev, still_linked.st_ino) != opened_identity
            or (
                closed_over.st_size,
                closed_over.st_mtime_ns,
                closed_over.st_ctime_ns,
            )
            != (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
        ):
            raise GoalRuntimeCorruptionError(corruption_error)
        return bytes(content).decode("utf-8")
    except GoalRuntimeCorruptionError:
        raise
    except (OSError, UnicodeError) as exc:
        raise GoalRuntimeCorruptionError(corruption_error) from exc
    finally:
        os.close(descriptor)


def _path_generation(path: Path) -> tuple[bool, int, int, int, int]:
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        return (False, 0, 0, 0, 0)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
    return (
        True,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
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
