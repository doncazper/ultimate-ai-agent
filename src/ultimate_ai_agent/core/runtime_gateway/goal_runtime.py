from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
import uuid
from collections.abc import Callable, Iterable
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
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
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
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
GOAL_JOURNAL_SCHEMA_VERSION = "goal_journal.v2"
RUN_EVENT_SCHEMA_VERSION = "durable_run_event.v3"
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
MAX_GOAL_MUTATION_SUBMISSIONS = 64
MAX_GOAL_MUTATION_REJECTION_TOMBSTONES = MAX_GOAL_JOURNAL_ENTRIES
MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES = 16 * 1024 * 1024
MAX_GOAL_MUTATION_SUBMISSION_HEAD_BYTES = 16 * 1024
MAX_GOAL_MUTATION_SUBMISSION_WRITE_INTENT_BYTES = (
    MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES + 64 * 1024
)
MAX_GOAL_MUTATION_APPROVAL_ENTRIES = 4096
MAX_GOAL_MUTATION_APPROVAL_LEDGER_BYTES = 16 * 1024 * 1024
MAX_GOAL_MUTATION_APPROVAL_HEAD_BYTES = 64 * 1024
MAX_GOAL_MUTATION_APPROVAL_APPEND_INTENT_BYTES = 128 * 1024
MAX_EXECUTION_REF_LENGTH = 320
MAX_RUN_EVENT_STORE_BYTES = 16 * 1024 * 1024
MAX_RUN_EVENT_IDEMPOTENCY_BYTES = 32 * 1024 * 1024
MAX_RUN_EVENT_PROJECTION_RESERVATION_BYTES = 16 * 1024 * 1024
MAX_RUN_EVENT_TRUSTED_SOURCE_BYTES = 16 * 1024 * 1024
MAX_RUNTIME_PROJECTION_INCOMPATIBILITIES = 4096
MAX_RUNTIME_PROJECTION_INCOMPATIBILITY_BYTES = 4 * 1024 * 1024
MAX_GOAL_PROVENANCE_ENTRIES = 100
RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS = 120
GOAL_TEXT_REDACTION_POSTURE = "operator_authored_redacted_summary_only"
GOAL_COMPLETION_VERIFIER_REF = "verifier-ref:goal-runtime:criteria-receipt-binding:v1"
GOAL_COMPLETION_EVALUATOR_BLOCKED_REASON_REF = (
    "blocked-authority-ref:goal-runtime:trusted-criterion-evaluator-unavailable"
)
GOAL_EVIDENCE_ROLLUP_PREFIX = "evidence-rollup-ref:goal-runtime:sha256:"
CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX = (
    "evidence-ref:control-center-goal-create-submission:sha256:"
)
CONTROL_CENTER_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX = (
    "evidence-ref:control-center-goal-update-submission:"
)
MAX_RUN_EVENT_PROOF_REFS = (
    1
    + MAX_RUNTIME_RECEIPT_EVIDENCE_REFS
    + (2 * MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS)
)
MAX_RUN_EVENT_RECEIPT_REFS = 1 + MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS
TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES = (
    "idempotency-ref:goal-completion-event",
    "idempotency-ref:runtime-run-started",
    "idempotency-ref:runtime-receipt-recorded",
    "idempotency-ref:runtime-failed-terminal",
)
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


def _is_trusted_core_run_event_idempotency_ref(value: str) -> bool:
    return any(
        value == prefix or value.startswith(f"{prefix}:")
        for prefix in TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES
    )


def _reject_trusted_core_run_event_idempotency_ref(value: str) -> None:
    if _is_trusted_core_run_event_idempotency_ref(value):
        raise GoalTransitionDeniedError(
            "RUN_EVENT_TRUSTED_IDEMPOTENCY_NAMESPACE_RESERVED"
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


_TERMINAL_GOAL_SUBMISSION_REJECTION_CODES = frozenset(
    {
        "GOAL_REQUEST_REF_INVALID",
        "GOAL_STORE_CAPACITY_EXCEEDED",
        "GOAL_JOURNAL_CAPACITY_EXCEEDED",
        "GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE",
        "GOAL_REQUEST_VALIDATION_FAILED",
        "GOAL_MUTATION_APPROVAL_DENIED",
        "GOAL_MUTATION_APPROVAL_REVOKED",
        "GOAL_MUTATION_APPROVAL_EXPIRED",
        "GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
        "GOAL_MUTATION_APPROVAL_BINDING_MISMATCH",
    }
)


def terminal_goal_submission_rejection_reason_ref(
    exc: GoalRuntimeError,
) -> str | None:
    """Return the stable rejection reason for a deterministic terminal failure."""

    code = str(exc) or "GOAL_RUNTIME_VALIDATION_FAILED"
    if (
        not isinstance(
            exc,
            (
                GoalNotFoundError,
                GoalVersionConflictError,
                GoalIdempotencyConflictError,
                GoalTransitionDeniedError,
            ),
        )
        and code not in _TERMINAL_GOAL_SUBMISSION_REJECTION_CODES
    ):
        return None
    return f"reason-ref:goal-mutation-rejected:{code.lower().replace('_', '-')}"


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
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name} contains credential-like material")


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


def _runtime_invocation_source_payload(
    record: RuntimeInvocationRecord,
) -> dict[str, Any]:
    """Return the immutable accepted-invocation provenance envelope.

    Operator safe-disable updates the receipt's current disable posture after
    the terminal receipt is durable. That operational posture must not rewrite
    historical projection provenance, while every other terminal receipt field
    remains content-bound.
    """

    payload = record.model_dump(
        mode="json",
        include={
            "invocation_ref",
            "request",
            "payload_fingerprint_ref",
            "idempotency_ref",
            "created_at",
        },
    )
    payload["receipt"] = (
        record.receipt.model_dump(mode="json", exclude={"safe_disable"})
        if record.receipt is not None
        else None
    )
    return payload


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
    if contains_obvious_secret(candidate):
        raise ValueError("GOAL_SECRET_LIKE_INPUT_DENIED")
    lowered = candidate.casefold()
    if (
        "\n" in candidate
        or "\r" in candidate
        or any(
            ord(character) < 32 or 0x7F <= ord(character) <= 0x9F
            for character in candidate
        )
        or any(marker in lowered for marker in _RAW_CONTENT_MARKERS)
        or lowered.startswith(("summarize ", "translate ", "respond to "))
        or contains_absolute_local_path(candidate)
    ):
        raise ValueError("GOAL_RAW_CONTENT_PERSISTENCE_DENIED")
    return candidate


def _reserved_goal_submission_evidence_refs(
    evidence_refs: list[str] | None,
) -> list[str]:
    return [
        ref
        for ref in (evidence_refs or [])
        if ref.startswith(
            (
                CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX,
                CONTROL_CENTER_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX,
            )
        )
    ]


def _goal_submission_evidence_prefix(
    operation: "GoalMutationSubmissionOperation",
) -> str:
    if operation == "create":
        return CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX
    return f"{CONTROL_CENTER_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX}{operation}:sha256:"


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


def _merge_bounded_goal_evidence_refs(
    existing_refs: Iterable[str],
    new_refs: Iterable[str],
) -> list[str]:
    """Keep the current snapshot bounded while journal entries retain history."""

    merged = list(dict.fromkeys([*existing_refs, *new_refs]))
    if len(merged) <= MAX_GOAL_LIST_ITEMS:
        return merged
    pinned_create_refs = [
        ref
        for ref in merged
        if ref.startswith(CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX)
    ]
    if len(pinned_create_refs) > 1:
        raise ValueError("GOAL_CREATE_SUBMISSION_IDENTITY_CONFLICT")
    prior_rollups = [
        ref for ref in merged if ref.startswith(GOAL_EVIDENCE_ROLLUP_PREFIX)
    ]
    ordinary_refs = [
        ref
        for ref in merged
        if not ref.startswith(GOAL_EVIDENCE_ROLLUP_PREFIX)
        and ref not in pinned_create_refs
    ]
    retained_count = MAX_GOAL_LIST_ITEMS - len(pinned_create_refs) - 1
    retained_refs = ordinary_refs[-retained_count:]
    evicted_refs = ordinary_refs[:-retained_count]
    rollup_ref = _sha256_ref(
        "evidence-rollup-ref:goal-runtime",
        {
            "schema_version": "goal_evidence_rollup.v1",
            "previous_rollup_refs": prior_rollups,
            "evicted_evidence_refs": evicted_refs,
        },
    )
    return [*pinned_create_refs, rollup_ref, *retained_refs]


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
        if (
            sum(
                ref.startswith(CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX)
                for ref in self.evidence_refs
            )
            > 1
        ):
            raise ValueError("GOAL_CREATE_SUBMISSION_IDENTITY_CONFLICT")
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
        if (
            sum(
                ref.startswith(CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX)
                for ref in self.evidence_refs
            )
            > 1
        ):
            raise ValueError("GOAL_CREATE_SUBMISSION_IDENTITY_CONFLICT")
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


GoalMutationSubmissionOperation = Literal["create", "edit", "transition"]


class GoalMutationSubmissionRecord(BaseModel):
    """Backend-owned exact retry envelope for one Control Center mutation."""

    schema_version: Literal["goal_mutation_submission.v1"] = (
        "goal_mutation_submission.v1"
    )
    submission_ref: str
    operation: GoalMutationSubmissionOperation
    goal_ref: str | None = None
    request_payload: dict[str, Any]
    idempotency_ref: str
    submission_evidence_ref: str
    request_fingerprint_ref: str
    recorded_at: datetime
    resolution_status: Literal["pending", "rejected"] = "pending"
    rejection_reason_ref: str | None = None
    resolved_at: datetime | None = None
    record_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_submission(self) -> "GoalMutationSubmissionRecord":
        for value, field_name in (
            (self.submission_ref, "submission_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.submission_evidence_ref, "submission_evidence_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.record_hash_ref, "record_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        if self.operation == "create":
            if self.goal_ref is not None:
                raise ValueError("GOAL_SUBMISSION_CREATE_GOAL_REF_DENIED")
            request = GoalCreateRequest.model_validate(self.request_payload)
        elif self.operation == "edit":
            if self.goal_ref is None:
                raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
            validate_execution_ref(self.goal_ref, "goal_ref")
            request = GoalEditRequest.model_validate(self.request_payload)
        else:
            if self.goal_ref is None:
                raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
            validate_execution_ref(self.goal_ref, "goal_ref")
            request = GoalTransitionRequest.model_validate(self.request_payload)
        matching_refs = _reserved_goal_submission_evidence_refs(request.evidence_refs)
        if matching_refs != [
            self.submission_evidence_ref
        ] or not self.submission_evidence_ref.startswith(
            _goal_submission_evidence_prefix(self.operation)
        ):
            raise ValueError("GOAL_SUBMISSION_EVIDENCE_BINDING_MISMATCH")
        expected_fingerprint = _sha256_ref(
            "request-fingerprint-ref:goal-mutation-submission",
            {
                "submission_ref": self.submission_ref,
                "operation": self.operation,
                "goal_ref": self.goal_ref,
                "request_payload": request.model_dump(mode="json"),
                "idempotency_ref": self.idempotency_ref,
                "submission_evidence_ref": self.submission_evidence_ref,
            },
        )
        if self.request_fingerprint_ref != expected_fingerprint:
            raise ValueError("GOAL_SUBMISSION_REQUEST_FINGERPRINT_MISMATCH")
        expected_record_hash = _sha256_ref(
            "record-hash-ref:goal-mutation-submission",
            {
                "request_fingerprint_ref": self.request_fingerprint_ref,
                "recorded_at": self.recorded_at.isoformat(),
                "resolution_status": self.resolution_status,
                "rejection_reason_ref": self.rejection_reason_ref,
                "resolved_at": (
                    self.resolved_at.isoformat()
                    if self.resolved_at is not None
                    else None
                ),
            },
        )
        if self.record_hash_ref != expected_record_hash:
            raise ValueError("GOAL_SUBMISSION_RECORD_HASH_MISMATCH")
        if self.resolution_status == "rejected":
            if self.rejection_reason_ref is None or self.resolved_at is None:
                raise ValueError("GOAL_SUBMISSION_REJECTION_BINDING_REQUIRED")
            validate_execution_ref(
                self.rejection_reason_ref,
                "rejection_reason_ref",
            )
        elif self.rejection_reason_ref is not None or self.resolved_at is not None:
            raise ValueError("GOAL_SUBMISSION_PENDING_REJECTION_BINDING_DENIED")
        return self


class GoalMutationSubmissionRejectionTombstone(BaseModel):
    """Bounded durable identity for a compacted terminal rejection."""

    schema_version: Literal["goal_mutation_submission_rejection_tombstone.v1"] = (
        "goal_mutation_submission_rejection_tombstone.v1"
    )
    submission_ref: str
    operation: GoalMutationSubmissionOperation
    goal_ref: str | None = None
    idempotency_ref: str
    submission_evidence_ref: str
    request_fingerprint_ref: str
    rejection_reason_ref: str
    resolved_at: datetime
    tombstone_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_tombstone(self) -> "GoalMutationSubmissionRejectionTombstone":
        for value, field_name in (
            (self.submission_ref, "submission_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.submission_evidence_ref, "submission_evidence_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.rejection_reason_ref, "rejection_reason_ref"),
            (self.tombstone_hash_ref, "tombstone_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        if self.operation == "create":
            if self.goal_ref is not None:
                raise ValueError("GOAL_SUBMISSION_CREATE_GOAL_REF_DENIED")
        elif self.goal_ref is None:
            raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
        else:
            validate_execution_ref(self.goal_ref, "goal_ref")
        expected_hash_ref = _sha256_ref(
            "tombstone-hash-ref:goal-mutation-submission-rejection",
            {
                "submission_ref": self.submission_ref,
                "operation": self.operation,
                "goal_ref": self.goal_ref,
                "idempotency_ref": self.idempotency_ref,
                "submission_evidence_ref": self.submission_evidence_ref,
                "request_fingerprint_ref": self.request_fingerprint_ref,
                "rejection_reason_ref": self.rejection_reason_ref,
                "resolved_at": self.resolved_at.isoformat(),
            },
        )
        if self.tombstone_hash_ref != expected_hash_ref:
            raise ValueError("GOAL_SUBMISSION_REJECTION_TOMBSTONE_HASH_MISMATCH")
        return self


class GoalMutationSubmissionState(BaseModel):
    schema_version: Literal["goal_mutation_submission_state.v1"] = (
        "goal_mutation_submission_state.v1"
    )
    records: list[GoalMutationSubmissionRecord] = Field(
        default_factory=list,
        max_length=MAX_GOAL_MUTATION_SUBMISSIONS,
    )
    rejection_tombstones: list[GoalMutationSubmissionRejectionTombstone] = Field(
        default_factory=list,
        max_length=MAX_GOAL_MUTATION_REJECTION_TOMBSTONES,
    )
    state_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_state(self) -> "GoalMutationSubmissionState":
        validate_execution_ref(self.state_hash_ref, "state_hash_ref")
        if len({record.submission_ref for record in self.records}) != len(self.records):
            raise ValueError("GOAL_SUBMISSION_REF_DUPLICATE")
        if len({record.idempotency_ref for record in self.records}) != len(
            self.records
        ):
            raise ValueError("GOAL_SUBMISSION_IDEMPOTENCY_REF_DUPLICATE")
        if len({record.submission_evidence_ref for record in self.records}) != len(
            self.records
        ):
            raise ValueError("GOAL_SUBMISSION_EVIDENCE_REF_DUPLICATE")
        all_submission_refs = [
            *(record.submission_ref for record in self.records),
            *(record.submission_ref for record in self.rejection_tombstones),
        ]
        all_idempotency_refs = [
            *(record.idempotency_ref for record in self.records),
            *(record.idempotency_ref for record in self.rejection_tombstones),
        ]
        all_evidence_refs = [
            *(record.submission_evidence_ref for record in self.records),
            *(record.submission_evidence_ref for record in self.rejection_tombstones),
        ]
        if len(set(all_submission_refs)) != len(all_submission_refs):
            raise ValueError("GOAL_SUBMISSION_REF_DUPLICATE")
        if len(set(all_idempotency_refs)) != len(all_idempotency_refs):
            raise ValueError("GOAL_SUBMISSION_IDEMPOTENCY_REF_DUPLICATE")
        if len(set(all_evidence_refs)) != len(all_evidence_refs):
            raise ValueError("GOAL_SUBMISSION_EVIDENCE_REF_DUPLICATE")
        expected_hash = _sha256_ref(
            "state-hash-ref:goal-mutation-submissions",
            {
                "records": [record.model_dump(mode="json") for record in self.records],
                "rejection_tombstones": [
                    tombstone.model_dump(mode="json")
                    for tombstone in self.rejection_tombstones
                ],
            },
        )
        legacy_hash = _sha256_ref(
            "state-hash-ref:goal-mutation-submissions",
            [record.model_dump(mode="json") for record in self.records],
        )
        if self.state_hash_ref != expected_hash and not (
            not self.rejection_tombstones and self.state_hash_ref == legacy_hash
        ):
            raise ValueError("GOAL_SUBMISSION_STATE_HASH_MISMATCH")
        return self


class GoalMutationSubmissionHeadManifest(BaseModel):
    """Independent monotonic anchor for the exact submission snapshot."""

    schema_version: Literal["goal_mutation_submission_head.v1"] = (
        "goal_mutation_submission_head.v1"
    )
    generation: StrictInt = Field(ge=1)
    state_hash_ref: str
    rejection_anchor_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "GoalMutationSubmissionHeadManifest":
        validate_execution_ref(self.state_hash_ref, "state_hash_ref")
        validate_execution_ref(self.rejection_anchor_ref, "rejection_anchor_ref")
        return self


class GoalMutationSubmissionWriteIntent(BaseModel):
    """Precommit binding for one exact submission snapshot replacement."""

    schema_version: Literal["goal_mutation_submission_write_intent.v1"] = (
        "goal_mutation_submission_write_intent.v1"
    )
    previous_head: GoalMutationSubmissionHeadManifest | None = None
    next_state: GoalMutationSubmissionState
    next_head: GoalMutationSubmissionHeadManifest

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intent(self) -> "GoalMutationSubmissionWriteIntent":
        previous_generation = (
            self.previous_head.generation if self.previous_head is not None else 0
        )
        if (
            self.next_head.generation != previous_generation + 1
            or self.next_head.state_hash_ref != self.next_state.state_hash_ref
        ):
            raise ValueError("GOAL_SUBMISSION_WRITE_INTENT_INVALID")
        return self


class GoalMutationApprovalRecoveryEnvelope(BaseModel):
    schema_version: Literal["goal_mutation_approval_recovery.v1"] = (
        "goal_mutation_approval_recovery.v1"
    )
    posture: Literal[
        "missing",
        "pending",
        "approved",
        "expired",
        "denied",
        "revoked",
    ]
    authoritative_current: bool = True
    approval_request: dict[str, Any] | None = None
    latest_decision: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "GoalMutationApprovalRecoveryEnvelope":
        if not self.authoritative_current:
            raise ValueError("GOAL_MUTATION_APPROVAL_RECOVERY_NOT_CURRENT")
        if self.posture == "missing":
            if self.approval_request is not None or self.latest_decision is not None:
                raise ValueError("GOAL_MUTATION_APPROVAL_RECOVERY_MISSING_INVALID")
            return self
        if self.approval_request is None:
            raise ValueError("GOAL_MUTATION_APPROVAL_RECOVERY_REQUEST_REQUIRED")
        if self.posture in {"approved", "denied", "revoked"}:
            if self.latest_decision is None:
                raise ValueError("GOAL_MUTATION_APPROVAL_RECOVERY_DECISION_REQUIRED")
        return self


class GoalMutationSubmissionRecoveryRecord(BaseModel):
    schema_version: Literal["goal_mutation_submission_recovery.v1"] = (
        "goal_mutation_submission_recovery.v1"
    )
    submission_ref: str
    operation: GoalMutationSubmissionOperation
    goal_ref: str | None = None
    request_payload: dict[str, Any]
    idempotency_ref: str
    submission_evidence_ref: str
    request_fingerprint_ref: str
    recorded_at: datetime
    status: Literal["pending", "committed", "rejected"]
    committed_goal_ref: str | None = None
    rejection_reason_ref: str | None = None
    resolved_at: datetime | None = None
    approval_recovery: GoalMutationApprovalRecoveryEnvelope = Field(
        default_factory=lambda: GoalMutationApprovalRecoveryEnvelope(posture="missing")
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_recovery(self) -> "GoalMutationSubmissionRecoveryRecord":
        validate_execution_ref(self.submission_ref, "submission_ref")
        validate_execution_ref(self.idempotency_ref, "idempotency_ref")
        validate_execution_ref(
            self.submission_evidence_ref,
            "submission_evidence_ref",
        )
        validate_execution_ref(
            self.request_fingerprint_ref,
            "request_fingerprint_ref",
        )
        if self.operation == "create":
            if self.goal_ref is not None:
                raise ValueError("GOAL_SUBMISSION_CREATE_GOAL_REF_DENIED")
            request = GoalCreateRequest.model_validate(self.request_payload)
        elif self.operation == "edit":
            if self.goal_ref is None:
                raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
            validate_execution_ref(self.goal_ref, "goal_ref")
            request = GoalEditRequest.model_validate(self.request_payload)
        else:
            if self.goal_ref is None:
                raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
            validate_execution_ref(self.goal_ref, "goal_ref")
            request = GoalTransitionRequest.model_validate(self.request_payload)
        matching_refs = _reserved_goal_submission_evidence_refs(request.evidence_refs)
        if matching_refs != [
            self.submission_evidence_ref
        ] or not self.submission_evidence_ref.startswith(
            _goal_submission_evidence_prefix(self.operation)
        ):
            raise ValueError("GOAL_SUBMISSION_EVIDENCE_BINDING_MISMATCH")
        if self.status == "committed":
            if self.committed_goal_ref is None:
                raise ValueError("GOAL_SUBMISSION_COMMITTED_GOAL_REF_REQUIRED")
            validate_execution_ref(
                self.committed_goal_ref,
                "committed_goal_ref",
            )
            if self.rejection_reason_ref is not None or self.resolved_at is None:
                raise ValueError("GOAL_SUBMISSION_COMMITTED_REJECTION_BINDING_DENIED")
        elif self.status == "rejected":
            if self.committed_goal_ref is not None:
                raise ValueError("GOAL_SUBMISSION_REJECTED_COMMITTED_REF_DENIED")
            if self.rejection_reason_ref is None or self.resolved_at is None:
                raise ValueError("GOAL_SUBMISSION_REJECTION_BINDING_REQUIRED")
            validate_execution_ref(
                self.rejection_reason_ref,
                "rejection_reason_ref",
            )
        elif (
            self.committed_goal_ref is not None
            or self.rejection_reason_ref is not None
            or self.resolved_at is not None
        ):
            raise ValueError("GOAL_SUBMISSION_PENDING_RESOLUTION_BINDING_DENIED")
        return self


class GoalMutationSubmissionRecoveryReadModel(BaseModel):
    schema_version: Literal["goal_mutation_submission_recovery_read_model.v1"] = (
        "goal_mutation_submission_recovery_read_model.v1"
    )
    records: list[GoalMutationSubmissionRecoveryRecord] = Field(
        default_factory=list,
        max_length=MAX_GOAL_MUTATION_SUBMISSIONS,
    )
    pending_count: StrictInt = Field(ge=0, le=MAX_GOAL_MUTATION_SUBMISSIONS)
    committed_count: StrictInt = Field(ge=0, le=MAX_GOAL_MUTATION_SUBMISSIONS)
    rejected_count: StrictInt = Field(ge=0, le=MAX_GOAL_MUTATION_SUBMISSIONS)
    backend_owned: bool = True
    exact_retry_required: bool = True
    raw_request_content_persisted: bool = False
    redacted_goal_metadata_only: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_counts(self) -> "GoalMutationSubmissionRecoveryReadModel":
        if self.pending_count != sum(
            record.status == "pending" for record in self.records
        ):
            raise ValueError("GOAL_SUBMISSION_PENDING_COUNT_MISMATCH")
        if self.committed_count != sum(
            record.status == "committed" for record in self.records
        ):
            raise ValueError("GOAL_SUBMISSION_COMMITTED_COUNT_MISMATCH")
        if self.rejected_count != sum(
            record.status == "rejected" for record in self.records
        ):
            raise ValueError("GOAL_SUBMISSION_REJECTED_COUNT_MISMATCH")
        if (
            not self.backend_owned
            or not self.exact_retry_required
            or self.raw_request_content_persisted
            or not self.redacted_goal_metadata_only
        ):
            raise ValueError("GOAL_SUBMISSION_RECOVERY_POSTURE_INVALID")
        return self


class GoalJournalEntry(BaseModel):
    schema_version: Literal["goal_journal.v1", "goal_journal.v2"] = (
        GOAL_JOURNAL_SCHEMA_VERSION
    )
    entry_ref: str
    operation: GoalJournalOperation
    goal_ref: str
    goal_version: StrictInt = Field(ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    idempotency_ref: str
    request_fingerprint_ref: str
    goal_submission_fingerprint_ref: str | None = None
    approval_ref: str
    approval_decision_ref: str
    approval_ledger_entry_hash_ref: str | None = None
    approval_request_fingerprint_ref: str | None = None
    approval_exact_scope_ref: str | None = None
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
        if self.approval_ledger_entry_hash_ref is not None:
            validate_execution_ref(
                self.approval_ledger_entry_hash_ref,
                "approval_ledger_entry_hash_ref",
            )
        if self.approval_request_fingerprint_ref is not None:
            validate_execution_ref(
                self.approval_request_fingerprint_ref,
                "approval_request_fingerprint_ref",
            )
        if self.approval_exact_scope_ref is not None:
            validate_execution_ref(
                self.approval_exact_scope_ref,
                "approval_exact_scope_ref",
            )
        approval_ledger_provenance = (
            self.approval_ledger_entry_hash_ref,
            self.approval_request_fingerprint_ref,
            self.approval_exact_scope_ref,
        )
        if self.schema_version == GOAL_JOURNAL_SCHEMA_VERSION:
            if not all(value is not None for value in approval_ledger_provenance):
                raise ValueError("GOAL_JOURNAL_APPROVAL_PROVENANCE_INCOMPLETE")
        elif any(value is not None for value in approval_ledger_provenance):
            raise ValueError("GOAL_JOURNAL_V1_APPROVAL_PROVENANCE_UNSUPPORTED")
        if self.previous_entry_hash_ref is not None:
            validate_execution_ref(
                self.previous_entry_hash_ref, "previous_entry_hash_ref"
            )
        if self.goal_submission_fingerprint_ref is not None:
            validate_execution_ref(
                self.goal_submission_fingerprint_ref,
                "goal_submission_fingerprint_ref",
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
    goal_submission_fingerprint_ref: str | None = None
    approval_ref: str
    approval_decision_ref: str
    approval_ledger_entry_hash_ref: str | None = None
    approval_request_fingerprint_ref: str | None = None
    approval_exact_scope_ref: str | None = None
    transition_reason_ref: str | None = None
    recorded_at: datetime
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_submission_fingerprint(
        self,
    ) -> "GoalMutationProvenanceEntry":
        if self.goal_submission_fingerprint_ref is not None:
            validate_execution_ref(
                self.goal_submission_fingerprint_ref,
                "goal_submission_fingerprint_ref",
            )
        return self

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
    schema_version: Literal[
        "durable_run_event.v1",
        "durable_run_event.v2",
        "durable_run_event.v3",
    ] = RUN_EVENT_SCHEMA_VERSION
    producer_class: Literal["trusted_core", "operator_public_metadata"] | None = None
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
    goal_mutation_approval_ref: str | None = None
    goal_mutation_approval_decision_ref: str | None = None
    goal_mutation_approval_ledger_entry_hash_ref: str | None = None
    trusted_source_record_hash_ref: str | None = None
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
            (self.goal_mutation_approval_ref, "goal_mutation_approval_ref"),
            (
                self.goal_mutation_approval_decision_ref,
                "goal_mutation_approval_decision_ref",
            ),
            (
                self.goal_mutation_approval_ledger_entry_hash_ref,
                "goal_mutation_approval_ledger_entry_hash_ref",
            ),
            (
                self.trusted_source_record_hash_ref,
                "trusted_source_record_hash_ref",
            ),
            (self.predecessor_hash_ref, "predecessor_hash_ref"),
            (self.event_hash_ref, "event_hash_ref"),
        ):
            if value is not None:
                validate_execution_ref(value, field_name)
        approval_provenance = (
            self.goal_mutation_approval_ref,
            self.goal_mutation_approval_decision_ref,
            self.goal_mutation_approval_ledger_entry_hash_ref,
        )
        if self.schema_version == "durable_run_event.v1":
            if self.producer_class is not None or any(
                value is not None for value in approval_provenance
            ):
                raise ValueError("RUN_EVENT_V1_PRODUCER_PROVENANCE_UNSUPPORTED")
        elif self.producer_class == "operator_public_metadata":
            if not all(value is not None for value in approval_provenance):
                raise ValueError("RUN_EVENT_APPROVAL_PROVENANCE_INCOMPLETE")
            if self.trusted_source_record_hash_ref is not None:
                raise ValueError("RUN_EVENT_TRUSTED_PRODUCER_PROVENANCE_INVALID")
        elif self.producer_class == "trusted_core":
            if any(value is not None for value in approval_provenance):
                raise ValueError("RUN_EVENT_TRUSTED_PRODUCER_PROVENANCE_INVALID")
            if (
                self.schema_version == "durable_run_event.v3"
                and self.trusted_source_record_hash_ref is None
            ):
                raise ValueError("RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_REQUIRED")
        else:
            raise ValueError("RUN_EVENT_PRODUCER_CLASS_REQUIRED")
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


TrustedRunEventSourceKind = Literal[
    "runtime_invocation",
    "goal_journal_completion",
    "trusted_core_internal",
]


class TrustedRunEventSourceBinding(BaseModel):
    source_kind: TrustedRunEventSourceKind
    source_ref: str
    source_fingerprint_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "TrustedRunEventSourceBinding":
        validate_execution_ref(self.source_ref, "source_ref")
        validate_execution_ref(
            self.source_fingerprint_ref,
            "source_fingerprint_ref",
        )
        return self


class TrustedRunEventSourceRecord(BaseModel):
    schema_version: Literal["trusted_run_event_source.v1"] = (
        "trusted_run_event_source.v1"
    )
    event_key_ref: str
    request_fingerprint_ref: str
    source_kind: TrustedRunEventSourceKind
    source_ref: str
    source_fingerprint_ref: str
    record_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "TrustedRunEventSourceRecord":
        for value, field_name in (
            (self.event_key_ref, "event_key_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.source_ref, "source_ref"),
            (self.source_fingerprint_ref, "source_fingerprint_ref"),
            (self.record_hash_ref, "record_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        expected = _sha256_ref(
            "record-hash-ref:trusted-run-event-source",
            {
                "event_key_ref": self.event_key_ref,
                "request_fingerprint_ref": self.request_fingerprint_ref,
                "source_kind": self.source_kind,
                "source_ref": self.source_ref,
                "source_fingerprint_ref": self.source_fingerprint_ref,
            },
        )
        if self.record_hash_ref != expected:
            raise ValueError("RUN_EVENT_TRUSTED_SOURCE_HASH_MISMATCH")
        return self


class TrustedRunEventSourceState(BaseModel):
    schema_version: Literal["trusted_run_event_source_state.v1"] = (
        "trusted_run_event_source_state.v1"
    )
    records: list[TrustedRunEventSourceRecord] = Field(
        default_factory=list,
        max_length=MAX_RUN_EVENT_IDEMPOTENCY_RECORDS,
    )
    state_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_state(self) -> "TrustedRunEventSourceState":
        validate_execution_ref(self.state_hash_ref, "state_hash_ref")
        if len({record.event_key_ref for record in self.records}) != len(self.records):
            raise ValueError("RUN_EVENT_TRUSTED_SOURCE_DUPLICATE")
        expected = _sha256_ref(
            "state-hash-ref:trusted-run-event-sources",
            [record.model_dump(mode="json") for record in self.records],
        )
        if self.state_hash_ref != expected:
            raise ValueError("RUN_EVENT_TRUSTED_SOURCE_STATE_HASH_MISMATCH")
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


class RuntimeProjectionIncompatibilityRecord(BaseModel):
    schema_version: Literal["runtime_projection_incompatibility.v1"] = (
        "runtime_projection_incompatibility.v1"
    )
    invocation_ref: str
    mission_ref: str
    payload_fingerprint_ref: str
    receipt_ref: str
    reason_ref: Literal[
        "reason-ref:runtime-projection-incompatible:missing-durable-goal"
    ] = "reason-ref:runtime-projection-incompatible:missing-durable-goal"
    recorded_at: datetime
    record_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeProjectionIncompatibilityRecord":
        for value, field_name in (
            (self.invocation_ref, "invocation_ref"),
            (self.mission_ref, "mission_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.reason_ref, "reason_ref"),
            (self.record_hash_ref, "record_hash_ref"),
        ):
            validate_execution_ref(value, field_name)
        expected_hash = _sha256_ref(
            "record-hash-ref:runtime-projection-incompatibility",
            {
                "invocation_ref": self.invocation_ref,
                "mission_ref": self.mission_ref,
                "payload_fingerprint_ref": self.payload_fingerprint_ref,
                "receipt_ref": self.receipt_ref,
                "reason_ref": self.reason_ref,
                "recorded_at": self.recorded_at.isoformat(),
            },
        )
        if self.record_hash_ref != expected_hash:
            raise ValueError("RUNTIME_PROJECTION_INCOMPATIBILITY_HASH_MISMATCH")
        return self


def _maximum_typed_ref(prefix: str, index: int) -> str:
    stem = f"{prefix}:{index:03d}:"
    return stem + ("x" * (MAX_EXECUTION_REF_LENGTH - len(stem)))


_MAXIMUM_UTF8_TEXT_CHARACTERS = tuple(
    chr(0x10000 + codepoint) for codepoint in range(32)
)


def _maximum_typed_summary(index: int) -> str:
    alphabet = _MAXIMUM_UTF8_TEXT_CHARACTERS
    encoded_index = index
    suffix: list[str] = []
    for _ in range(3):
        suffix.append(alphabet[encoded_index % len(alphabet)])
        encoded_index //= len(alphabet)
    # Each accepted supplementary code point occupies four UTF-8 bytes, which
    # bounds every accepted 1,200-code-point summary while keeping generated
    # list entries distinct without relying on terminal control characters.
    return (alphabet[0] * (MAX_GOAL_TEXT - len(suffix))) + "".join(suffix)


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
        goal_submission_fingerprint_ref=_maximum_typed_ref(
            "request-fingerprint-ref:goal-mutation-submission:max-envelope",
            0,
        ),
        approval_ref=_maximum_typed_ref("approval-ref:max-envelope", 0),
        approval_decision_ref=_maximum_typed_ref(
            "approval-decision-ref:max-envelope",
            0,
        ),
        approval_ledger_entry_hash_ref=_maximum_typed_ref(
            "entry-hash-ref:goal-mutation-approval:max-envelope",
            0,
        ),
        approval_request_fingerprint_ref=_maximum_typed_ref(
            "request-fingerprint-ref:goal-mutation-approval:max-envelope",
            0,
        ),
        approval_exact_scope_ref=_maximum_typed_ref(
            "exact-scope-ref:goal-mutation:max-envelope",
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
        producer_class="operator_public_metadata",
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
        goal_mutation_approval_ref=_maximum_typed_ref(
            "approval-ref:goal-mutation:max-envelope",
            0,
        ),
        goal_mutation_approval_decision_ref=_maximum_typed_ref(
            "approval-decision-ref:goal-mutation:max-envelope",
            0,
        ),
        goal_mutation_approval_ledger_entry_hash_ref=_maximum_typed_ref(
            "entry-hash-ref:goal-mutation-approval:max-envelope",
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
    successful_receipt_recorded: bool = False
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
        goal_submission_fingerprint_ref: str | None = None,
        submission_terminal_guard: Any = None,
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
            guard = (
                submission_terminal_guard(entries)
                if submission_terminal_guard is not None
                else nullcontext()
            )
            with guard:
                replay = self._idempotent_replay(
                    entries,
                    idempotency_ref,
                    fingerprint,
                    goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
                )
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
                    goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
                    approval_ref=approval_binding.approval_ref,
                    approval_decision_ref=approval_binding.approval_decision_ref,
                    approval_ledger_entry_hash_ref=(
                        approval_binding.approval_ledger_entry_hash_ref
                    ),
                    approval_request_fingerprint_ref=(
                        approval_binding.request_fingerprint_ref
                    ),
                    approval_exact_scope_ref=approval_binding.exact_scope_ref,
                )
                return goal.model_copy(deep=True)

    def edit(
        self,
        goal_ref: str,
        request: GoalEditRequest,
        *,
        idempotency_ref: str,
        approval_binding: GoalMutationApprovalBinding,
        goal_submission_fingerprint_ref: str | None = None,
        submission_terminal_guard: Any = None,
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
            goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
            submission_terminal_guard=submission_terminal_guard,
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
        goal_submission_fingerprint_ref: str | None = None,
        submission_terminal_guard: Any = None,
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
            goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
            submission_terminal_guard=submission_terminal_guard,
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
        goal_submission_fingerprint_ref: str | None = None,
    ) -> PersistentGoal | None:
        """Return an exact prior transition before version-sensitive revalidation."""

        validate_execution_ref(goal_ref, "goal_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        entry = self.replay_mutation_entry(
            operation=GoalJournalOperation.transition,
            goal_ref=goal_ref,
            request_payload=validated.model_dump(mode="json"),
            idempotency_ref=idempotency_ref,
            goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
        )
        return entry.goal if entry is not None else None

    def replay_mutation_entry(
        self,
        *,
        operation: GoalJournalOperation,
        goal_ref: str | None,
        request_payload: dict[str, Any],
        idempotency_ref: str,
        goal_submission_fingerprint_ref: str | None = None,
    ) -> GoalJournalEntry | None:
        """Return one exact committed mutation with its durable approval proof."""

        validate_execution_ref(idempotency_ref, "idempotency_ref")
        if operation == GoalJournalOperation.create:
            if goal_ref is not None:
                raise ValueError("GOAL_CREATE_REPLAY_GOAL_REF_DENIED")
            fingerprint_payload: dict[str, Any] = request_payload
        else:
            if goal_ref is None:
                raise ValueError("GOAL_MUTATION_REPLAY_GOAL_REF_REQUIRED")
            validate_execution_ref(goal_ref, "goal_ref")
            fingerprint_payload = {
                "goal_ref": goal_ref,
                "request": request_payload,
            }
        fingerprint = _sha256_ref(
            f"request-fingerprint-ref:goal-{operation.value}",
            fingerprint_payload,
        )
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            entries = self._load_entries(repair_manifest=True)
            for entry in entries:
                if entry.idempotency_ref != idempotency_ref:
                    continue
                if (
                    entry.request_fingerprint_ref != fingerprint
                    or entry.goal_submission_fingerprint_ref
                    != goal_submission_fingerprint_ref
                ):
                    raise GoalIdempotencyConflictError("GOAL_IDEMPOTENCY_CONFLICT")
                if entry.operation != operation.value or (
                    goal_ref is not None and entry.goal_ref != goal_ref
                ):
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_REPLAY_ENTRY_MISMATCH"
                    )
                return entry.model_copy(deep=True)
        return None

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
        goal_submission_fingerprint_ref: str | None = None,
        submission_terminal_guard: Any = None,
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
            guard = (
                submission_terminal_guard(entries)
                if submission_terminal_guard is not None
                else nullcontext()
            )
            with guard:
                replay = self._idempotent_replay(
                    entries,
                    idempotency_ref,
                    fingerprint,
                    goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
                )
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
                    approval_ledger_entry_hash_ref=(
                        approval_binding.approval_ledger_entry_hash_ref
                    ),
                    approval_request_fingerprint_ref=(
                        approval_binding.request_fingerprint_ref
                    ),
                    approval_exact_scope_ref=approval_binding.exact_scope_ref,
                    goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
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
            updates["evidence_refs"] = _merge_bounded_goal_evidence_refs(
                current.evidence_refs,
                request.evidence_refs,
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
                        "evidence_refs": _merge_bounded_goal_evidence_refs(
                            restore_goal.evidence_refs,
                            request.evidence_refs,
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
            "evidence_refs": _merge_bounded_goal_evidence_refs(
                current.evidence_refs,
                request.evidence_refs,
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
                evidence_refs=_merge_bounded_goal_evidence_refs(
                    updates["evidence_refs"],
                    [request.completion_evidence.evidence_ref],
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
        *,
        goal_submission_fingerprint_ref: str | None = None,
    ) -> PersistentGoal | None:
        for entry in entries:
            if entry.idempotency_ref != idempotency_ref:
                continue
            if entry.request_fingerprint_ref != request_fingerprint_ref:
                raise GoalIdempotencyConflictError("GOAL_IDEMPOTENCY_CONFLICT")
            if entry.goal_submission_fingerprint_ref != goal_submission_fingerprint_ref:
                raise GoalIdempotencyConflictError(
                    "GOAL_SUBMISSION_MUTATION_BINDING_MISMATCH"
                )
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
        approval_ledger_entry_hash_ref: str,
        approval_request_fingerprint_ref: str,
        approval_exact_scope_ref: str,
        goal_submission_fingerprint_ref: str | None = None,
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
            goal_submission_fingerprint_ref=goal_submission_fingerprint_ref,
            approval_ref=approval_ref,
            approval_decision_ref=approval_decision_ref,
            approval_ledger_entry_hash_ref=approval_ledger_entry_hash_ref,
            approval_request_fingerprint_ref=approval_request_fingerprint_ref,
            approval_exact_scope_ref=approval_exact_scope_ref,
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
        if payload.get("goal_submission_fingerprint_ref") is None:
            payload.pop("goal_submission_fingerprint_ref", None)
        if payload.get("approval_ledger_entry_hash_ref") is None:
            payload.pop("approval_ledger_entry_hash_ref", None)
        if payload.get("approval_request_fingerprint_ref") is None:
            payload.pop("approval_request_fingerprint_ref", None)
        if payload.get("approval_exact_scope_ref") is None:
            payload.pop("approval_exact_scope_ref", None)
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
    def mutation_entries(self) -> Iterator[list[GoalJournalEntry]]:
        """Load one repair-capable journal generation under the writer lock."""

        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-journal"):
            yield self._load_entries(repair_manifest=True)

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
        return "".join(
            entry.model_dump_json(
                exclude={
                    field_name
                    for field_name, field_value in (
                        (
                            "goal_submission_fingerprint_ref",
                            entry.goal_submission_fingerprint_ref,
                        ),
                        (
                            "approval_ledger_entry_hash_ref",
                            entry.approval_ledger_entry_hash_ref,
                        ),
                        (
                            "approval_request_fingerprint_ref",
                            entry.approval_request_fingerprint_ref,
                        ),
                        (
                            "approval_exact_scope_ref",
                            entry.approval_exact_scope_ref,
                        ),
                    )
                    if field_value is None
                }
            )
            + "\n"
            for entry in entries
        )

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


class _GoalMutationSubmissionStore:
    """Persist exact Control Center retry envelopes before goal mutation."""

    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / "goal_mutation_submissions.json"
        self.head_path = self.state_dir / "goal_mutation_submissions_head.json"
        self.write_intent_path = (
            self.state_dir / "goal_mutation_submissions_write_intent.json"
        )
        self._locks = FileSingleWriterLockManager(self.state_dir / ".locks")

    @staticmethod
    def _state(
        records: list[GoalMutationSubmissionRecord],
        rejection_tombstones: list[GoalMutationSubmissionRejectionTombstone]
        | None = None,
    ) -> GoalMutationSubmissionState:
        tombstones = list(rejection_tombstones or [])
        state_hash_ref = _sha256_ref(
            "state-hash-ref:goal-mutation-submissions",
            {
                "records": [record.model_dump(mode="json") for record in records],
                "rejection_tombstones": [
                    tombstone.model_dump(mode="json") for tombstone in tombstones
                ],
            },
        )
        return GoalMutationSubmissionState(
            records=records,
            rejection_tombstones=tombstones,
            state_hash_ref=state_hash_ref,
        )

    @classmethod
    def _state_content(
        cls,
        records: list[GoalMutationSubmissionRecord],
        rejection_tombstones: list[GoalMutationSubmissionRejectionTombstone]
        | None = None,
    ) -> str:
        return cls._state(records, rejection_tombstones).model_dump_json() + "\n"

    @staticmethod
    def _rejected_record(
        record: GoalMutationSubmissionRecord,
        *,
        rejection_reason_ref: str,
        resolved_at: datetime,
    ) -> GoalMutationSubmissionRecord:
        record_hash_ref = _sha256_ref(
            "record-hash-ref:goal-mutation-submission",
            {
                "request_fingerprint_ref": record.request_fingerprint_ref,
                "recorded_at": record.recorded_at.isoformat(),
                "resolution_status": "rejected",
                "rejection_reason_ref": rejection_reason_ref,
                "resolved_at": resolved_at.isoformat(),
            },
        )
        rejected = record.model_copy(
            update={
                "resolution_status": "rejected",
                "rejection_reason_ref": rejection_reason_ref,
                "resolved_at": resolved_at,
                "record_hash_ref": record_hash_ref,
            }
        )
        return GoalMutationSubmissionRecord.model_validate(
            rejected.model_dump(mode="json")
        )

    @classmethod
    def _worst_case_terminal_records(
        cls,
        records: list[GoalMutationSubmissionRecord],
    ) -> list[GoalMutationSubmissionRecord]:
        maximum_reason_ref = _maximum_typed_ref(
            "reason-ref:goal-mutation-rejected",
            0,
        )
        maximum_resolved_at = datetime.max.replace(tzinfo=utc_now().tzinfo)
        return [
            (
                cls._rejected_record(
                    record,
                    rejection_reason_ref=maximum_reason_ref,
                    resolved_at=maximum_resolved_at,
                )
                if record.resolution_status == "pending"
                else record
            )
            for record in records
        ]

    @staticmethod
    def _rejection_tombstone(
        record: GoalMutationSubmissionRecord,
    ) -> GoalMutationSubmissionRejectionTombstone:
        if (
            record.resolution_status != "rejected"
            or record.rejection_reason_ref is None
            or record.resolved_at is None
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_REJECTION_TOMBSTONE_SOURCE_INVALID"
            )
        tombstone_hash_ref = _sha256_ref(
            "tombstone-hash-ref:goal-mutation-submission-rejection",
            {
                "submission_ref": record.submission_ref,
                "operation": record.operation,
                "goal_ref": record.goal_ref,
                "idempotency_ref": record.idempotency_ref,
                "submission_evidence_ref": record.submission_evidence_ref,
                "request_fingerprint_ref": record.request_fingerprint_ref,
                "rejection_reason_ref": record.rejection_reason_ref,
                "resolved_at": record.resolved_at.isoformat(),
            },
        )
        return GoalMutationSubmissionRejectionTombstone(
            submission_ref=record.submission_ref,
            operation=record.operation,
            goal_ref=record.goal_ref,
            idempotency_ref=record.idempotency_ref,
            submission_evidence_ref=record.submission_evidence_ref,
            request_fingerprint_ref=record.request_fingerprint_ref,
            rejection_reason_ref=record.rejection_reason_ref,
            resolved_at=record.resolved_at,
            tombstone_hash_ref=tombstone_hash_ref,
        )

    @staticmethod
    def _rejection_anchor(
        state: GoalMutationSubmissionState,
    ) -> str:
        return _sha256_ref(
            "rejection-anchor-ref:goal-mutation-submissions",
            sorted(
                [
                    (
                        record.submission_ref,
                        record.request_fingerprint_ref,
                        record.record_hash_ref,
                    )
                    for record in state.records
                    if record.resolution_status == "rejected"
                ]
                + [
                    (
                        tombstone.submission_ref,
                        tombstone.request_fingerprint_ref,
                        tombstone.tombstone_hash_ref,
                    )
                    for tombstone in state.rejection_tombstones
                ]
            ),
        )

    @classmethod
    def _head(
        cls,
        state: GoalMutationSubmissionState,
        *,
        generation: int,
    ) -> GoalMutationSubmissionHeadManifest:
        return GoalMutationSubmissionHeadManifest(
            generation=generation,
            state_hash_ref=state.state_hash_ref,
            rejection_anchor_ref=cls._rejection_anchor(state),
        )

    def _load_head(self) -> GoalMutationSubmissionHeadManifest | None:
        raw = _read_bounded_regular_utf8(
            self.head_path,
            max_bytes=MAX_GOAL_MUTATION_SUBMISSION_HEAD_BYTES,
            missing_ok=True,
            capacity_error="GOAL_SUBMISSION_HEAD_CAPACITY_EXCEEDED",
            corruption_error="GOAL_SUBMISSION_HEAD_CORRUPT",
        )
        if raw is None:
            return None
        try:
            return GoalMutationSubmissionHeadManifest.model_validate_json(raw)
        except (ValueError, TypeError) as exc:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_HEAD_CORRUPT") from exc

    def _load_write_intent(self) -> GoalMutationSubmissionWriteIntent | None:
        raw = _read_bounded_regular_utf8(
            self.write_intent_path,
            max_bytes=MAX_GOAL_MUTATION_SUBMISSION_WRITE_INTENT_BYTES,
            missing_ok=True,
            capacity_error="GOAL_SUBMISSION_WRITE_INTENT_CAPACITY_EXCEEDED",
            corruption_error="GOAL_SUBMISSION_WRITE_INTENT_CORRUPT",
        )
        if raw is None:
            return None
        try:
            intent = GoalMutationSubmissionWriteIntent.model_validate_json(raw)
        except (ValueError, TypeError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_WRITE_INTENT_CORRUPT"
            ) from exc
        if (
            intent.next_head.rejection_anchor_ref
            != self._rejection_anchor(intent.next_state)
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_WRITE_INTENT_MISMATCH"
            )
        return intent

    def _delete_write_intent(self) -> None:
        try:
            self.write_intent_path.unlink(missing_ok=True)
        except OSError as exc:
            raise GoalRuntimeError(
                "GOAL_RUNTIME_STORAGE_UNAVAILABLE"
            ) from exc

    def _install_intent(self, intent: GoalMutationSubmissionWriteIntent) -> None:
        _atomic_write(self.path, intent.next_state.model_dump_json() + "\n")
        _atomic_write(self.head_path, intent.next_head.model_dump_json() + "\n")
        self._delete_write_intent()

    def _load_state(
        self,
        *,
        repair_head: bool = False,
    ) -> GoalMutationSubmissionState:
        intent = self._load_write_intent()
        raw_content = _read_bounded_regular_utf8(
            self.path,
            max_bytes=MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES,
            missing_ok=True,
            capacity_error="GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED",
            corruption_error="GOAL_SUBMISSION_STATE_CORRUPT",
        )
        if raw_content is None:
            head = self._load_head()
            if intent is None:
                if head is not None:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_SUBMISSION_STATE_MISSING_WITH_HEAD"
                    )
                return self._state([])
            if intent.previous_head is not None or head is not None:
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_WRITE_INTENT_STATE_MISMATCH"
                )
            if not repair_head:
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_WRITE_RECOVERY_REQUIRED"
                )
            self._install_intent(intent)
            return intent.next_state.model_copy(deep=True)
        try:
            state = GoalMutationSubmissionState.model_validate_json(raw_content)
        except (ValueError, TypeError) as exc:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_STATE_CORRUPT") from exc
        head = self._load_head()
        if intent is None:
            if head is None:
                raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_HEAD_MISSING")
            if head != self._head(state, generation=head.generation):
                raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_HEAD_MISMATCH")
            return state
        if not repair_head:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_WRITE_RECOVERY_REQUIRED")
        previous_head = intent.previous_head
        if head == previous_head and previous_head is not None:
            previous_state_matches = (
                state.state_hash_ref == previous_head.state_hash_ref
                and self._rejection_anchor(state)
                == previous_head.rejection_anchor_ref
            )
            if previous_state_matches:
                self._install_intent(intent)
                return intent.next_state.model_copy(deep=True)
        if head == previous_head and state == intent.next_state:
            _atomic_write(self.head_path, intent.next_head.model_dump_json() + "\n")
            self._delete_write_intent()
            return intent.next_state.model_copy(deep=True)
        if head == intent.next_head and state == intent.next_state:
            self._delete_write_intent()
            return intent.next_state.model_copy(deep=True)
        raise GoalRuntimeCorruptionError(
            "GOAL_SUBMISSION_WRITE_INTENT_STATE_MISMATCH"
        )

    def _load(self) -> list[GoalMutationSubmissionRecord]:
        state = self._load_state()
        return [record.model_copy(deep=True) for record in state.records]

    def repair_recoverable_write(self) -> None:
        """Finish only an exactly precommitted submission write, if present."""

        try:
            intent_metadata = os.lstat(self.write_intent_path)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
        if not stat.S_ISREG(intent_metadata.st_mode):
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_WRITE_INTENT_CORRUPT"
            )
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-submissions"):
            self._load_state(repair_head=True)

    def _write(
        self,
        records: list[GoalMutationSubmissionRecord],
        rejection_tombstones: list[GoalMutationSubmissionRejectionTombstone]
        | None = None,
    ) -> None:
        content = self._state_content(records, rejection_tombstones)
        if len(content.encode("utf-8")) > MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES:
            raise GoalRuntimeError("GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED")
        terminal_content = self._state_content(
            self._worst_case_terminal_records(records),
            rejection_tombstones,
        )
        if (
            len(terminal_content.encode("utf-8"))
            > MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES
        ):
            raise GoalRuntimeError("GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED")
        current_state = self._load_state(repair_head=True)
        current_head = self._load_head()
        if current_state.records or current_state.rejection_tombstones:
            if current_head is None:
                raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_HEAD_MISSING")
        elif current_head is not None:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_HEAD_MISMATCH")
        next_state = self._state(records, rejection_tombstones)
        next_head = self._head(
            next_state,
            generation=(current_head.generation + 1 if current_head else 1),
        )
        intent = GoalMutationSubmissionWriteIntent(
            previous_head=current_head,
            next_state=next_state,
            next_head=next_head,
        )
        intent_content = intent.model_dump_json() + "\n"
        if (
            len(intent_content.encode("utf-8"))
            > MAX_GOAL_MUTATION_SUBMISSION_WRITE_INTENT_BYTES
        ):
            raise GoalRuntimeError(
                "GOAL_SUBMISSION_WRITE_INTENT_CAPACITY_EXCEEDED"
            )
        _atomic_write(self.write_intent_path, intent_content)
        _atomic_write(self.path, content)
        _atomic_write(self.head_path, next_head.model_dump_json() + "\n")
        self._delete_write_intent()

    @contextmanager
    def consistent_read(self) -> Iterator[None]:
        with _nonmutating_goal_runtime_read_lock(
            self.state_dir / ".locks",
            "goal-submissions",
            generation_paths=(
                self.path,
                self.head_path,
                self.write_intent_path,
            ),
        ):
            yield

    @staticmethod
    def _validated_request(
        operation: GoalMutationSubmissionOperation,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
    ) -> GoalCreateRequest | GoalEditRequest | GoalTransitionRequest:
        if operation == "create":
            return GoalCreateRequest.model_validate(request.model_dump())
        if operation == "edit":
            return GoalEditRequest.model_validate(request.model_dump())
        return GoalTransitionRequest.model_validate(request.model_dump())

    def prepare(
        self,
        *,
        submission_ref: str,
        operation: GoalMutationSubmissionOperation,
        goal_ref: str | None,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
        idempotency_ref: str,
        journal_entries: list[GoalJournalEntry],
    ) -> GoalMutationSubmissionRecord:
        validate_execution_ref(submission_ref, "submission_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        if operation == "create":
            if goal_ref is not None:
                raise ValueError("GOAL_SUBMISSION_CREATE_GOAL_REF_DENIED")
        elif goal_ref is None:
            raise ValueError("GOAL_SUBMISSION_GOAL_REF_REQUIRED")
        else:
            validate_execution_ref(goal_ref, "goal_ref")
        validated = self._validated_request(operation, request)
        payload = validated.model_dump(mode="json")
        matching_evidence_refs = _reserved_goal_submission_evidence_refs(
            validated.evidence_refs
        )
        if len(matching_evidence_refs) != 1 or not matching_evidence_refs[0].startswith(
            _goal_submission_evidence_prefix(operation)
        ):
            raise ValueError("GOAL_SUBMISSION_EVIDENCE_BINDING_REQUIRED")
        submission_evidence_ref = matching_evidence_refs[0]
        request_fingerprint_ref = _sha256_ref(
            "request-fingerprint-ref:goal-mutation-submission",
            {
                "submission_ref": submission_ref,
                "operation": operation,
                "goal_ref": goal_ref,
                "request_payload": payload,
                "idempotency_ref": idempotency_ref,
                "submission_evidence_ref": submission_evidence_ref,
            },
        )
        existing_journal_entry = next(
            (
                entry
                for entry in journal_entries
                if entry.idempotency_ref == idempotency_ref
            ),
            None,
        )
        if (
            existing_journal_entry is not None
            and existing_journal_entry.goal_submission_fingerprint_ref
            != request_fingerprint_ref
        ):
            raise GoalIdempotencyConflictError("GOAL_IDEMPOTENCY_CONFLICT")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-submissions"):
            state = self._load_state(repair_head=True)
            records = [record.model_copy(deep=True) for record in state.records]
            rejection_tombstones = [
                tombstone.model_copy(deep=True)
                for tombstone in state.rejection_tombstones
            ]
            committed_submission_refs = {
                recovery.submission_ref
                for recovery in self.recovery_read_model_from_records(
                    records,
                    journal_entries,
                ).records
                if recovery.status == "committed"
            }
            for tombstone in rejection_tombstones:
                exact_binding = (
                    tombstone.submission_ref == submission_ref
                    and tombstone.operation == operation
                    and tombstone.goal_ref == goal_ref
                    and tombstone.idempotency_ref == idempotency_ref
                    and tombstone.submission_evidence_ref == submission_evidence_ref
                    and tombstone.request_fingerprint_ref == request_fingerprint_ref
                )
                if exact_binding:
                    raise GoalTransitionDeniedError(
                        "GOAL_SUBMISSION_PREVIOUSLY_REJECTED"
                    )
                if (
                    tombstone.submission_ref == submission_ref
                    or tombstone.idempotency_ref == idempotency_ref
                    or tombstone.submission_evidence_ref == submission_evidence_ref
                ):
                    raise GoalIdempotencyConflictError(
                        "GOAL_SUBMISSION_BINDING_CONFLICT"
                    )
            for record in records:
                if record.submission_ref == submission_ref:
                    if (
                        record.request_fingerprint_ref != request_fingerprint_ref
                        or record.idempotency_ref != idempotency_ref
                    ):
                        raise GoalIdempotencyConflictError(
                            "GOAL_SUBMISSION_IDEMPOTENCY_CONFLICT"
                        )
                    if record.resolution_status == "rejected":
                        raise GoalTransitionDeniedError(
                            "GOAL_SUBMISSION_PREVIOUSLY_REJECTED"
                        )
                    return record.model_copy(deep=True)
                if (
                    record.idempotency_ref == idempotency_ref
                    or record.submission_evidence_ref == submission_evidence_ref
                ):
                    raise GoalIdempotencyConflictError(
                        "GOAL_SUBMISSION_BINDING_CONFLICT"
                    )
            if len(records) >= MAX_GOAL_MUTATION_SUBMISSIONS:
                pending_records = [
                    record
                    for record in records
                    if record.resolution_status == "pending"
                    and record.submission_ref not in committed_submission_refs
                ]
                terminal_records = [
                    record
                    for record in records
                    if (
                        record.resolution_status == "rejected"
                        or record.submission_ref in committed_submission_refs
                    )
                ]
                evicted_terminal_records = terminal_records[:-8]
                compacted_tombstones = [
                    self._rejection_tombstone(record)
                    for record in evicted_terminal_records
                    if record.resolution_status == "rejected"
                ]
                if (
                    len(rejection_tombstones) + len(compacted_tombstones)
                    > MAX_GOAL_MUTATION_REJECTION_TOMBSTONES
                ):
                    raise GoalRuntimeError(
                        "GOAL_SUBMISSION_REJECTION_TOMBSTONE_CAPACITY_EXCEEDED"
                    )
                rejection_tombstones.extend(compacted_tombstones)
                records = [
                    *pending_records,
                    *terminal_records[-8:],
                ]
            if len(records) >= MAX_GOAL_MUTATION_SUBMISSIONS:
                raise GoalRuntimeError("GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED")
            recorded_at = utc_now()
            record_hash_ref = _sha256_ref(
                "record-hash-ref:goal-mutation-submission",
                {
                    "request_fingerprint_ref": request_fingerprint_ref,
                    "recorded_at": recorded_at.isoformat(),
                    "resolution_status": "pending",
                    "rejection_reason_ref": None,
                    "resolved_at": None,
                },
            )
            record = GoalMutationSubmissionRecord(
                submission_ref=submission_ref,
                operation=operation,
                goal_ref=goal_ref,
                request_payload=payload,
                idempotency_ref=idempotency_ref,
                submission_evidence_ref=submission_evidence_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                recorded_at=recorded_at,
                record_hash_ref=record_hash_ref,
            )
            records.append(record)
            self._write(records, rejection_tombstones)
            return record.model_copy(deep=True)

    def reject(
        self,
        *,
        submission_ref: str,
        request_fingerprint_ref: str,
        rejection_reason_ref: str,
        journal_entries: list[GoalJournalEntry],
    ) -> GoalMutationSubmissionRecord:
        """Durably resolve one exact prepared submission as terminally rejected."""

        validate_execution_ref(submission_ref, "submission_ref")
        validate_execution_ref(
            request_fingerprint_ref,
            "request_fingerprint_ref",
        )
        validate_execution_ref(rejection_reason_ref, "rejection_reason_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-submissions"):
            return self._reject_locked(
                submission_ref=submission_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                rejection_reason_ref=rejection_reason_ref,
                journal_entries=journal_entries,
            )

    def reject_linked_approval(
        self,
        *,
        spec: GoalMutationApprovalRequestSpec,
        rejection_reason_ref: str,
        journal_entries: list[GoalJournalEntry],
    ) -> GoalMutationSubmissionRecord | None:
        """Converge a linked pending UI submission before terminal approval."""

        if spec.operation == "append-run-event":
            return None
        operation: GoalMutationSubmissionOperation
        if spec.operation == "create":
            operation = "create"
        elif spec.operation == "edit":
            operation = "edit"
        elif spec.operation.startswith("transition-"):
            operation = "transition"
        else:
            raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_OPERATION_INVALID")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-submissions"):
            state = self._load_state(repair_head=True)
            matches = [
                record
                for record in state.records
                if record.idempotency_ref == spec.idempotency_ref
            ]
            if not matches:
                return None
            if len(matches) != 1:
                raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_BINDING_CONFLICT")
            record = matches[0]
            exact_operation = (
                f"transition-{record.request_payload.get('transition')}"
                if operation == "transition"
                else operation
            )
            subject_ref = "goal-ref:new" if operation == "create" else record.goal_ref
            if (
                record.operation != operation
                or subject_ref is None
                or spec.operation != exact_operation
                or spec.subject_ref != subject_ref
                or spec.request_fingerprint_ref
                != _goal_mutation_approval_request_fingerprint_ref(
                    operation=exact_operation,
                    subject_ref=subject_ref,
                    request_payload=record.request_payload,
                    idempotency_ref=record.idempotency_ref,
                )
                or spec.mutation_request_fingerprint_ref
                != _mutation_request_fingerprint_ref(
                    operation=exact_operation,
                    subject_ref=subject_ref,
                    request_payload=record.request_payload,
                )
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_APPROVAL_BINDING_MISMATCH"
                )
            return self._reject_locked(
                submission_ref=record.submission_ref,
                request_fingerprint_ref=record.request_fingerprint_ref,
                rejection_reason_ref=rejection_reason_ref,
                journal_entries=journal_entries,
            )

    def _reject_locked(
        self,
        *,
        submission_ref: str,
        request_fingerprint_ref: str,
        rejection_reason_ref: str,
        journal_entries: list[GoalJournalEntry],
    ) -> GoalMutationSubmissionRecord:
        state = self._load_state(repair_head=True)
        records = [record.model_copy(deep=True) for record in state.records]
        rejection_tombstones = [
            tombstone.model_copy(deep=True) for tombstone in state.rejection_tombstones
        ]
        matching_index = next(
            (
                index
                for index, record in enumerate(records)
                if record.submission_ref == submission_ref
            ),
            None,
        )
        if matching_index is None:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_REJECTION_RECORD_MISSING")
        record = records[matching_index]
        if record.request_fingerprint_ref != request_fingerprint_ref:
            raise GoalIdempotencyConflictError(
                "GOAL_SUBMISSION_REJECTION_FINGERPRINT_CONFLICT"
            )
        recovery = self.recovery_read_model_from_records(
            records,
            journal_entries,
        )
        matching_recovery = next(
            item for item in recovery.records if item.submission_ref == submission_ref
        )
        if matching_recovery.status == "committed":
            return record.model_copy(deep=True)
        if record.resolution_status == "rejected":
            if record.rejection_reason_ref != rejection_reason_ref:
                raise GoalIdempotencyConflictError(
                    "GOAL_SUBMISSION_REJECTION_REASON_CONFLICT"
                )
            return record.model_copy(deep=True)
        rejected = self._rejected_record(
            record,
            rejection_reason_ref=rejection_reason_ref,
            resolved_at=utc_now(),
        )
        records[matching_index] = rejected
        self._write(records, rejection_tombstones)
        return rejected.model_copy(deep=True)

    @contextmanager
    def terminal_commit_guard(
        self,
        *,
        request_fingerprint_ref: str | None,
        idempotency_ref: str,
        journal_entries: list[GoalJournalEntry],
    ) -> Iterator[None]:
        """Hold one prepared submission terminal state stable through commit."""

        if request_fingerprint_ref is None:
            yield
            return
        validate_execution_ref(request_fingerprint_ref, "request_fingerprint_ref")
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        with _normalized_goal_runtime_lock(self._locks, "goal-submissions"):
            records = self._load()
            matching = [
                record
                for record in records
                if record.idempotency_ref == idempotency_ref
                or record.request_fingerprint_ref == request_fingerprint_ref
            ]
            if len(matching) != 1:
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_COMMIT_RECORD_MISSING"
                    if not matching
                    else "GOAL_SUBMISSION_COMMIT_BINDING_DUPLICATE"
                )
            record = matching[0]
            if (
                record.idempotency_ref != idempotency_ref
                or record.request_fingerprint_ref != request_fingerprint_ref
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_COMMIT_BINDING_MISMATCH"
                )
            recovery = self.recovery_read_model_from_records(
                records,
                journal_entries,
            )
            exact_recovery = next(
                item
                for item in recovery.records
                if item.submission_ref == record.submission_ref
            )
            if exact_recovery.status == "rejected":
                raise GoalTransitionDeniedError("GOAL_SUBMISSION_PREVIOUSLY_REJECTED")
            yield

    def mutation_binding_record(
        self,
        *,
        operation: GoalMutationSubmissionOperation,
        goal_ref: str | None,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
        idempotency_ref: str,
    ) -> GoalMutationSubmissionRecord | None:
        """Return the exact prepared envelope for one mutation, if required."""

        validated = self._validated_request(operation, request)
        request_payload = validated.model_dump(mode="json")
        with self.consistent_read():
            records = self._load()
        matches = [
            record for record in records if record.idempotency_ref == idempotency_ref
        ]
        if not matches:
            if any(
                ref.startswith(
                    (
                        CONTROL_CENTER_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX,
                        CONTROL_CENTER_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX,
                    )
                )
                for ref in (validated.evidence_refs or [])
            ):
                raise GoalRuntimeError("GOAL_SUBMISSION_RECORD_REQUIRED")
            return None
        if len(matches) != 1:
            raise GoalRuntimeCorruptionError("GOAL_SUBMISSION_BINDING_DUPLICATE")
        record = matches[0]
        if (
            record.operation != operation
            or record.goal_ref != goal_ref
            or record.request_payload != request_payload
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_MUTATION_BINDING_MISMATCH"
            )
        if record.resolution_status == "rejected":
            raise GoalTransitionDeniedError("GOAL_SUBMISSION_PREVIOUSLY_REJECTED")
        return record.model_copy(deep=True)

    def mutation_binding_fingerprint(
        self,
        *,
        operation: GoalMutationSubmissionOperation,
        goal_ref: str | None,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
        idempotency_ref: str,
    ) -> str | None:
        record = self.mutation_binding_record(
            operation=operation,
            goal_ref=goal_ref,
            request=request,
            idempotency_ref=idempotency_ref,
        )
        return record.request_fingerprint_ref if record is not None else None

    def recovery_read_model(
        self,
        entries: list[GoalJournalEntry],
    ) -> GoalMutationSubmissionRecoveryReadModel:
        with self.consistent_read():
            records = self._load()
        return self.recovery_read_model_from_records(records, entries)

    @staticmethod
    def _goal_journal_request_fingerprint(
        record: GoalMutationSubmissionRecord,
    ) -> str:
        if record.operation == "create":
            return _sha256_ref(
                "request-fingerprint-ref:goal-create",
                record.request_payload,
            )
        return _sha256_ref(
            f"request-fingerprint-ref:goal-{record.operation}",
            {
                "goal_ref": record.goal_ref,
                "request": record.request_payload,
            },
        )

    @classmethod
    def recovery_read_model_from_records(
        cls,
        records: list[GoalMutationSubmissionRecord],
        entries: list[GoalJournalEntry],
        approval_entries: list[GoalMutationApprovalLedgerEntry] | None = None,
    ) -> GoalMutationSubmissionRecoveryReadModel:
        entries_by_idempotency = {entry.idempotency_ref: entry for entry in entries}
        committed_bindings: dict[str, tuple[str, datetime]] = {}
        for record in records:
            entry = entries_by_idempotency.get(record.idempotency_ref)
            if (
                entry is None
                or entry.goal_submission_fingerprint_ref
                != record.request_fingerprint_ref
            ):
                continue
            expected_fingerprint = cls._goal_journal_request_fingerprint(record)
            expected_goal_ref = (
                entry.goal_ref if record.operation == "create" else record.goal_ref
            )
            if (
                entry.operation != record.operation
                or entry.goal_ref != expected_goal_ref
                or entry.request_fingerprint_ref != expected_fingerprint
                or record.submission_evidence_ref not in entry.goal.evidence_refs
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_COMMIT_BINDING_MISMATCH"
                )
            if record.resolution_status == "rejected":
                raise GoalRuntimeCorruptionError(
                    "GOAL_SUBMISSION_REJECTION_COMMIT_CONFLICT"
                )
            committed_bindings[record.submission_ref] = (
                entry.goal_ref,
                entry.recorded_at,
            )
        recovery_records = [
            GoalMutationSubmissionRecoveryRecord(
                submission_ref=record.submission_ref,
                operation=record.operation,
                goal_ref=record.goal_ref,
                request_payload=record.request_payload,
                idempotency_ref=record.idempotency_ref,
                submission_evidence_ref=record.submission_evidence_ref,
                request_fingerprint_ref=record.request_fingerprint_ref,
                recorded_at=record.recorded_at,
                status=(
                    "committed"
                    if record.submission_ref in committed_bindings
                    else record.resolution_status
                ),
                committed_goal_ref=(
                    committed_bindings[record.submission_ref][0]
                    if record.submission_ref in committed_bindings
                    else None
                ),
                rejection_reason_ref=record.rejection_reason_ref,
                resolved_at=(
                    committed_bindings[record.submission_ref][1]
                    if record.submission_ref in committed_bindings
                    else record.resolved_at
                ),
                approval_recovery=cls._approval_recovery_envelope(
                    record,
                    approval_entries or [],
                ),
            )
            for record in records
        ]
        return GoalMutationSubmissionRecoveryReadModel(
            records=recovery_records,
            pending_count=sum(
                record.status == "pending" for record in recovery_records
            ),
            committed_count=sum(
                record.status == "committed" for record in recovery_records
            ),
            rejected_count=sum(
                record.status == "rejected" for record in recovery_records
            ),
        )

    @staticmethod
    def _approval_recovery_envelope(
        record: GoalMutationSubmissionRecord,
        approval_entries: list[GoalMutationApprovalLedgerEntry],
    ) -> GoalMutationApprovalRecoveryEnvelope:
        operation = (
            f"transition-{record.request_payload.get('transition')}"
            if record.operation == "transition"
            else record.operation
        )
        subject_ref = (
            "goal-ref:new" if record.operation == "create" else record.goal_ref
        )
        if subject_ref is None:
            raise GoalRuntimeCorruptionError(
                "GOAL_SUBMISSION_APPROVAL_BINDING_MISMATCH"
            )
        request_fingerprint_ref = _goal_mutation_approval_request_fingerprint_ref(
            operation=operation,
            subject_ref=subject_ref,
            request_payload=record.request_payload,
            idempotency_ref=record.idempotency_ref,
        )
        mutation_request_fingerprint_ref = _mutation_request_fingerprint_ref(
            operation=operation,
            subject_ref=subject_ref,
            request_payload=record.request_payload,
        )
        matches = [
            entry
            for entry in approval_entries
            if (
                entry.spec.operation == operation
                and entry.spec.subject_ref == subject_ref
                and entry.spec.idempotency_ref == record.idempotency_ref
                and entry.spec.request_fingerprint_ref == request_fingerprint_ref
                and entry.spec.mutation_request_fingerprint_ref
                == mutation_request_fingerprint_ref
            )
        ]
        if not matches:
            return GoalMutationApprovalRecoveryEnvelope(posture="missing")
        request_refs = {entry.spec.approval_request_ref for entry in matches}
        if len(request_refs) != 1:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_RECOVERY_AMBIGUOUS"
            )
        latest = matches[-1]
        posture = latest.status
        if posture in {"pending", "approved"} and utc_now() >= latest.spec.expires_at:
            posture = "expired"
        return GoalMutationApprovalRecoveryEnvelope(
            posture=posture,
            approval_request=latest.spec.model_dump(mode="json"),
            latest_decision=(
                latest.model_dump(mode="json") if latest.status != "pending" else None
            ),
        )


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
        self.trusted_sources_path = self.state_dir / "run_event_trusted_sources.json"
        self.reservations_path = (
            self.state_dir / "run_event_projection_reservations.jsonl"
        )
        self.incompatibilities_path = (
            self.state_dir / "runtime_projection_incompatibilities.jsonl"
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
            generation_paths=(
                self.path,
                self.idempotency_path,
                self.trusted_sources_path,
            ),
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
                    tombstones = self._load_idempotency_tombstones(events)
                    self._validate_trusted_sources(
                        [
                            *events,
                            *(item.event for item in tombstones.values()),
                        ]
                    )
                    return events, tombstones
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("RUN_EVENT_GENERATION_UNSTABLE")

    def append(
        self,
        request: DurableRunEventAppendRequest,
        *,
        approval_binding: GoalMutationApprovalBinding | None = None,
        trusted_source: TrustedRunEventSourceBinding | None = None,
    ) -> DurableRunEvent:
        validated = DurableRunEventAppendRequest.model_validate(request.model_dump())
        with self.exclusive():
            return self._append_locked(
                validated,
                approval_binding=approval_binding,
                trusted_source=trusted_source,
            )

    def replay_append(
        self,
        request: DurableRunEventAppendRequest,
    ) -> DurableRunEvent | None:
        """Return one exact prior append without asserting fresh authority."""

        validated = DurableRunEventAppendRequest.model_validate(request.model_dump())
        with self.exclusive():
            events = self._load_events()
            tombstones = self._load_idempotency_tombstones(events)
            prior = tombstones.get((validated.run_ref, validated.idempotency_ref))
            if prior is None:
                return None
            if prior.request_fingerprint_ref != self._request_fingerprint(validated):
                raise GoalIdempotencyConflictError("RUN_EVENT_IDEMPOTENCY_CONFLICT")
            return prior.event.model_copy(deep=True)

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
        approval_binding: GoalMutationApprovalBinding | None = None,
        trusted_source: TrustedRunEventSourceBinding | None = None,
    ) -> DurableRunEvent:
        if approval_binding is not None and trusted_source is not None:
            raise GoalRuntimeCorruptionError("RUN_EVENT_PRODUCER_PROVENANCE_AMBIGUOUS")
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
        source_record: TrustedRunEventSourceRecord | None = None
        trusted_sources = self._load_trusted_sources()
        prior = tombstones.get(key)
        if prior is not None and prior.request_fingerprint_ref != expected_fingerprint:
            raise GoalIdempotencyConflictError("RUN_EVENT_IDEMPOTENCY_CONFLICT")
        if approval_binding is None:
            binding = trusted_source or TrustedRunEventSourceBinding(
                source_kind="trusted_core_internal",
                source_ref=validated.authority_decision_ref,
                source_fingerprint_ref=expected_fingerprint,
            )
            source_record = self._trusted_source_record(
                event_key_ref=event_key_ref,
                request_fingerprint_ref=expected_fingerprint,
                binding=binding,
            )
            existing_source = trusted_sources.get(event_key_ref)
            if existing_source is not None and existing_source != source_record:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH"
                )
            trusted_sources[event_key_ref] = source_record
        if prior is not None:
            if (
                source_record is not None
                and prior.event.trusted_source_record_hash_ref
                != source_record.record_hash_ref
            ):
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH"
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
            producer_class=(
                "operator_public_metadata"
                if approval_binding is not None
                else "trusted_core"
            ),
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
            goal_mutation_approval_ref=(
                approval_binding.approval_ref if approval_binding is not None else None
            ),
            goal_mutation_approval_decision_ref=(
                approval_binding.approval_decision_ref
                if approval_binding is not None
                else None
            ),
            goal_mutation_approval_ledger_entry_hash_ref=(
                approval_binding.approval_ledger_entry_hash_ref
                if approval_binding is not None
                else None
            ),
            trusted_source_record_hash_ref=(
                source_record.record_hash_ref if source_record is not None else None
            ),
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
        if source_record is not None:
            self._write_trusted_sources(trusted_sources.values())
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
        events, tombstones = self._load_consistent_generation()
        return self._summaries_from_events(events, tombstones)

    @staticmethod
    def _summaries_from_events(
        events: list[DurableRunEvent],
        tombstones: dict[
            tuple[str, str],
            RunEventIdempotencyTombstone,
        ],
    ) -> list[RunEventStreamSummary]:
        successful_receipt_run_refs = {
            event.run_ref
            for event in events
            if event.event_kind == DurableRunEventKind.receipt_recorded.value
        }
        successful_receipt_run_refs.update(
            tombstone.run_ref
            for tombstone in tombstones.values()
            if tombstone.event.event_kind == DurableRunEventKind.receipt_recorded.value
        )
        grouped: dict[str, list[DurableRunEvent]] = {}
        for event in events:
            grouped.setdefault(event.run_ref, []).append(event)
        summaries = [
            RunEventStreamSummary(
                run_ref=run_ref,
                run_type=stream_events[0].run_type,
                first_retained_sequence=stream_events[0].sequence,
                last_sequence=stream_events[-1].sequence,
                retained_event_count=len(stream_events),
                retention_anchor_hash_ref=stream_events[0].predecessor_hash_ref,
                successful_receipt_recorded=run_ref in successful_receipt_run_refs,
                terminal_event_kind=(
                    stream_events[-1].event_kind
                    if stream_events[-1].event_kind
                    in {
                        DurableRunEventKind.cancelled.value,
                        DurableRunEventKind.completion_verified.value,
                        DurableRunEventKind.failed_terminal.value,
                        DurableRunEventKind.dead_lettered.value,
                    }
                    else None
                ),
            )
            for run_ref, stream_events in grouped.items()
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
    def _runtime_projection_requests(
        record: RuntimeInvocationRecord,
    ) -> tuple[DurableRunEventAppendRequest, DurableRunEventAppendRequest]:
        """Derive the only two accepted event projections for a runtime receipt."""

        from ultimate_ai_agent.core.runtime_gateway.contracts import RuntimeAuthority

        receipt = record.receipt
        if receipt is None:
            raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_RECEIPT_REQUIRED")
        run_type = (
            AcceptedLocalRunType.local_read_task
            if record.request.requested_authority == RuntimeAuthority.local_model.value
            else AcceptedLocalRunType.local_metadata_action
        )
        goal_ref = (
            record.request.mission_ref
            if (record.request.mission_ref or "").startswith("goal-ref:")
            else None
        )
        plan_ref = (
            record.request.action_ref
            if (record.request.action_ref or "").startswith("plan-ref:")
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
        projection_kind = _runtime_receipt_projection_kind(record)
        projection_idempotency_prefix = (
            TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[2]
            if projection_kind == DurableRunEventKind.receipt_recorded
            else TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[3]
        )
        return (
            DurableRunEventAppendRequest(
                run_ref=record.invocation_ref,
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
                    TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[1],
                    {"invocation_ref": record.invocation_ref},
                ),
                authority_decision_ref=receipt.policy_decision_ref,
            ),
            DurableRunEventAppendRequest(
                run_ref=record.invocation_ref,
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
                        "invocation_ref": record.invocation_ref,
                        "receipt_ref": receipt.receipt_ref,
                    },
                ),
                authority_decision_ref=receipt.policy_decision_ref,
            ),
        )

    @staticmethod
    def _completion_projection_request(
        entry: GoalJournalEntry,
        *,
        run_type: AcceptedLocalRunType,
    ) -> DurableRunEventAppendRequest:
        """Derive the only accepted completion event for a journal entry."""

        goal = entry.goal
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
        return DurableRunEventAppendRequest(
            run_ref=goal.completion_run_ref,
            run_type=run_type,
            event_kind=DurableRunEventKind.completion_verified,
            safe_summary=(
                "Deterministic receipt evidence verified the linked goal completion."
            ),
            proof_refs=list(
                dict.fromkeys(
                    [
                        goal.completion_proof_ref,
                        goal.completion_evidence_ref,
                        *goal.completion_criterion_proof_refs,
                        *(
                            binding.evaluator_receipt_ref
                            for binding in goal.completion_criterion_verifier_bindings
                        ),
                    ]
                )
            ),
            receipt_refs=list(
                dict.fromkeys(
                    [
                        goal.completion_receipt_ref,
                        *(
                            binding.evaluator_receipt_ref
                            for binding in goal.completion_criterion_verifier_bindings
                        ),
                    ]
                )
            ),
            criterion_verifier_bindings=[
                DurableCriterionVerifierBinding.model_validate(
                    binding.model_dump(mode="json")
                )
                for binding in goal.completion_criterion_verifier_bindings
            ],
            goal_ref=goal.goal_ref,
            plan_ref=goal.completion_plan_ref,
            idempotency_ref=_sha256_ref(
                TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[0],
                {
                    "goal_ref": goal.goal_ref,
                    "goal_version": goal.version,
                },
            ),
            authority_decision_ref=entry.approval_decision_ref,
        )

    @staticmethod
    def _event_hash(event: DurableRunEvent) -> str:
        payload = event.model_dump(mode="json")
        payload.pop("event_hash_ref", None)
        if payload.get("producer_class") is None:
            payload.pop("producer_class", None)
        if payload.get("goal_mutation_approval_ref") is None:
            payload.pop("goal_mutation_approval_ref", None)
        if payload.get("goal_mutation_approval_decision_ref") is None:
            payload.pop("goal_mutation_approval_decision_ref", None)
        if payload.get("goal_mutation_approval_ledger_entry_hash_ref") is None:
            payload.pop("goal_mutation_approval_ledger_entry_hash_ref", None)
        if payload.get("trusted_source_record_hash_ref") is None:
            payload.pop("trusted_source_record_hash_ref", None)
        return _sha256_ref("event-hash-ref:durable-run", payload)

    @staticmethod
    def _tombstone_hash(tombstone: RunEventIdempotencyTombstone) -> str:
        payload = tombstone.model_dump(mode="json")
        payload.pop("tombstone_hash_ref", None)
        event_payload = payload["event"]
        if event_payload.get("producer_class") is None:
            event_payload.pop("producer_class", None)
        if event_payload.get("goal_mutation_approval_ref") is None:
            event_payload.pop("goal_mutation_approval_ref", None)
        if event_payload.get("goal_mutation_approval_decision_ref") is None:
            event_payload.pop("goal_mutation_approval_decision_ref", None)
        if event_payload.get("goal_mutation_approval_ledger_entry_hash_ref") is None:
            event_payload.pop(
                "goal_mutation_approval_ledger_entry_hash_ref",
                None,
            )
        if event_payload.get("trusted_source_record_hash_ref") is None:
            event_payload.pop("trusted_source_record_hash_ref", None)
        return _sha256_ref("tombstone-hash-ref:run-event-idempotency", payload)

    @staticmethod
    def _event_serialization_exclude(event: DurableRunEvent) -> set[str]:
        return {
            field_name
            for field_name, field_value in (
                ("producer_class", event.producer_class),
                ("goal_mutation_approval_ref", event.goal_mutation_approval_ref),
                (
                    "goal_mutation_approval_decision_ref",
                    event.goal_mutation_approval_decision_ref,
                ),
                (
                    "goal_mutation_approval_ledger_entry_hash_ref",
                    event.goal_mutation_approval_ledger_entry_hash_ref,
                ),
                (
                    "trusted_source_record_hash_ref",
                    event.trusted_source_record_hash_ref,
                ),
            )
            if field_value is None
        }

    @classmethod
    def _event_json(cls, event: DurableRunEvent) -> str:
        return event.model_dump_json(exclude=cls._event_serialization_exclude(event))

    @classmethod
    def _tombstone_json(cls, tombstone: RunEventIdempotencyTombstone) -> str:
        event_exclude = cls._event_serialization_exclude(tombstone.event)
        return tombstone.model_dump_json(
            exclude={"event": event_exclude} if event_exclude else None
        )

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

    @staticmethod
    def _trusted_source_record(
        *,
        event_key_ref: str,
        request_fingerprint_ref: str,
        binding: TrustedRunEventSourceBinding,
    ) -> TrustedRunEventSourceRecord:
        payload = {
            "event_key_ref": event_key_ref,
            "request_fingerprint_ref": request_fingerprint_ref,
            "source_kind": binding.source_kind,
            "source_ref": binding.source_ref,
            "source_fingerprint_ref": binding.source_fingerprint_ref,
        }
        return TrustedRunEventSourceRecord(
            **payload,
            record_hash_ref=_sha256_ref(
                "record-hash-ref:trusted-run-event-source",
                payload,
            ),
        )

    @staticmethod
    def _trusted_source_state(
        records: Iterable[TrustedRunEventSourceRecord],
    ) -> TrustedRunEventSourceState:
        ordered = sorted(records, key=lambda record: record.event_key_ref)
        return TrustedRunEventSourceState(
            records=ordered,
            state_hash_ref=_sha256_ref(
                "state-hash-ref:trusted-run-event-sources",
                [record.model_dump(mode="json") for record in ordered],
            ),
        )

    def _load_trusted_sources(
        self,
    ) -> dict[str, TrustedRunEventSourceRecord]:
        raw = _read_bounded_regular_utf8(
            self.trusted_sources_path,
            max_bytes=MAX_RUN_EVENT_TRUSTED_SOURCE_BYTES,
            missing_ok=True,
            capacity_error="RUN_EVENT_TRUSTED_SOURCE_CAPACITY_EXCEEDED",
            corruption_error="RUN_EVENT_TRUSTED_SOURCE_STATE_CORRUPT",
        )
        if raw is None:
            return {}
        try:
            state = TrustedRunEventSourceState.model_validate_json(raw)
        except (ValueError, TypeError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_TRUSTED_SOURCE_STATE_CORRUPT"
            ) from exc
        return {
            record.event_key_ref: record.model_copy(deep=True)
            for record in state.records
        }

    def _write_trusted_sources(
        self,
        records: Iterable[TrustedRunEventSourceRecord],
    ) -> None:
        content = self._trusted_source_state(records).model_dump_json() + "\n"
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_TRUSTED_SOURCE_BYTES:
            raise GoalRuntimeError("RUN_EVENT_TRUSTED_SOURCE_CAPACITY_EXCEEDED")
        _atomic_write(self.trusted_sources_path, content)

    def _validate_trusted_sources(
        self,
        events: Iterable[DurableRunEvent],
        *,
        journal_entries: Iterable[GoalJournalEntry] = (),
        runtime_invocation_state_dir: Path | None = None,
    ) -> None:
        sources = self._load_trusted_sources()
        event_list = list(events)
        journal_by_ref = {
            entry.entry_ref: entry for entry in journal_entries
        }
        runtime_store: RuntimeInvocationStore | None = None
        for event in event_list:
            if event.producer_class != "trusted_core":
                continue
            if event.schema_version != "durable_run_event.v3":
                continue
            source = sources.get(
                self._event_key_ref(event.run_ref, event.idempotency_ref)
            )
            if (
                source is None
                or event.trusted_source_record_hash_ref != source.record_hash_ref
                or source.request_fingerprint_ref
                != self._request_fingerprint(
                    DurableRunEventAppendRequest.model_validate(
                        self._event_request_payload(event)
                    )
                )
            ):
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH"
                )
            if source.source_kind == "goal_journal_completion":
                journal_entry = journal_by_ref.get(source.source_ref)
                if (
                    journal_entry is None
                    or journal_entry.entry_hash_ref != source.source_fingerprint_ref
                ):
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH"
                    )
                receipt_events = {
                    candidate.event_ref: candidate
                    for candidate in event_list
                    if (
                        candidate.run_ref
                        == journal_entry.goal.completion_run_ref
                        and candidate.event_kind
                        == DurableRunEventKind.receipt_recorded.value
                        and journal_entry.goal.completion_receipt_ref
                        in candidate.receipt_refs
                        and journal_entry.goal.completion_proof_ref
                        in candidate.proof_refs
                        and [
                            binding.model_dump(mode="json")
                            for binding in candidate.criterion_verifier_bindings
                        ]
                        == [
                            binding.model_dump(mode="json")
                            for binding in (
                                journal_entry.goal
                                .completion_criterion_verifier_bindings
                            )
                        ]
                    )
                }
                if len(receipt_events) != 1:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH"
                    )
                expected_request = self._completion_projection_request(
                    journal_entry,
                    run_type=AcceptedLocalRunType(
                        next(iter(receipt_events.values())).run_type
                    ),
                )
                if (
                    self._request_fingerprint(expected_request)
                    != source.request_fingerprint_ref
                    or expected_request.model_dump(mode="json")
                    != self._event_request_payload(event)
                ):
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH"
                    )
            elif source.source_kind == "runtime_invocation":
                if runtime_invocation_state_dir is None:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_AUTHORITY_UNAVAILABLE"
                    )
                if runtime_store is None:
                    from ultimate_ai_agent.core.runtime_gateway.storage import (
                        RuntimeInvocationStore,
                        RuntimeInvocationStorageError,
                    )

                    runtime_store = RuntimeInvocationStore(
                        runtime_invocation_state_dir
                    )
                try:
                    runtime_record = runtime_store.get_invocation(source.source_ref)
                except (RuntimeInvocationStorageError, ValueError, AttributeError) as exc:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH"
                    ) from exc
                expected_source_fingerprint = _sha256_ref(
                    "source-fingerprint-ref:runtime-invocation",
                    _runtime_invocation_source_payload(runtime_record),
                )
                if expected_source_fingerprint != source.source_fingerprint_ref:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH"
                    )
                expected_requests = self._runtime_projection_requests(runtime_record)
                matching_requests = [
                    request
                    for request in expected_requests
                    if request.idempotency_ref == event.idempotency_ref
                ]
                if (
                    len(matching_requests) != 1
                    or self._request_fingerprint(matching_requests[0])
                    != source.request_fingerprint_ref
                    or matching_requests[0].model_dump(mode="json")
                    != self._event_request_payload(event)
                ):
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH"
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
            TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[2]
            if projection_kind == DurableRunEventKind.receipt_recorded
            else TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[3]
        )
        expected_keys = (
            (
                run_ref,
                _sha256_ref(
                    TRUSTED_CORE_RUN_EVENT_IDEMPOTENCY_PREFIXES[1],
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

    def projection_incompatibilities(
        self,
    ) -> list[RuntimeProjectionIncompatibilityRecord]:
        with _nonmutating_goal_runtime_read_lock(
            self.state_dir / ".locks",
            "runtime-projection-incompatibilities",
            generation_paths=(self.incompatibilities_path,),
        ):
            return self._load_projection_incompatibilities()

    def quarantine_projection_incompatibility(
        self,
        record: RuntimeInvocationRecord,
    ) -> RuntimeProjectionIncompatibilityRecord:
        receipt = record.receipt
        mission_ref = record.request.mission_ref
        if receipt is None or mission_ref is None:
            raise GoalRuntimeCorruptionError(
                "RUNTIME_PROJECTION_INCOMPATIBILITY_BINDING_MISSING"
            )
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(
            self._locks,
            "runtime-projection-incompatibilities",
        ):
            records = self._load_projection_incompatibilities()
            existing = next(
                (
                    item
                    for item in records
                    if item.invocation_ref == record.invocation_ref
                ),
                None,
            )
            if existing is not None:
                if (
                    existing.mission_ref != mission_ref
                    or existing.payload_fingerprint_ref
                    != record.payload_fingerprint_ref
                    or existing.receipt_ref != receipt.receipt_ref
                ):
                    raise GoalRuntimeCorruptionError(
                        "RUNTIME_PROJECTION_INCOMPATIBILITY_BINDING_MISMATCH"
                    )
                return existing.model_copy(deep=True)
            if len(records) >= MAX_RUNTIME_PROJECTION_INCOMPATIBILITIES:
                raise GoalRuntimeError(
                    "RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED"
                )
            recorded_at = utc_now()
            payload = {
                "invocation_ref": record.invocation_ref,
                "mission_ref": mission_ref,
                "payload_fingerprint_ref": record.payload_fingerprint_ref,
                "receipt_ref": receipt.receipt_ref,
                "reason_ref": (
                    "reason-ref:runtime-projection-incompatible:missing-durable-goal"
                ),
                "recorded_at": recorded_at.isoformat(),
            }
            incompatibility = RuntimeProjectionIncompatibilityRecord(
                **payload,
                record_hash_ref=_sha256_ref(
                    "record-hash-ref:runtime-projection-incompatibility",
                    payload,
                ),
            )
            records.append(incompatibility)
            self._write_projection_incompatibilities(records)
            return incompatibility.model_copy(deep=True)

    def _load_projection_incompatibilities(
        self,
    ) -> list[RuntimeProjectionIncompatibilityRecord]:
        raw_content = _read_bounded_regular_utf8(
            self.incompatibilities_path,
            max_bytes=MAX_RUNTIME_PROJECTION_INCOMPATIBILITY_BYTES,
            missing_ok=True,
            capacity_error=("RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED"),
            corruption_error=("RUNTIME_PROJECTION_INCOMPATIBILITY_STORE_CORRUPT"),
        )
        if raw_content is None:
            return []
        try:
            records = [
                RuntimeProjectionIncompatibilityRecord.model_validate_json(line)
                for line in raw_content.splitlines()
                if line.strip()
            ]
        except (TypeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "RUNTIME_PROJECTION_INCOMPATIBILITY_STORE_CORRUPT"
            ) from exc
        if len(records) > MAX_RUNTIME_PROJECTION_INCOMPATIBILITIES:
            raise GoalRuntimeCorruptionError(
                "RUNTIME_PROJECTION_INCOMPATIBILITY_COUNT_EXCEEDED"
            )
        if len({record.invocation_ref for record in records}) != len(records):
            raise GoalRuntimeCorruptionError(
                "RUNTIME_PROJECTION_INCOMPATIBILITY_DUPLICATE"
            )
        return records

    def _write_projection_incompatibilities(
        self,
        records: list[RuntimeProjectionIncompatibilityRecord],
    ) -> None:
        content = "".join(record.model_dump_json() + "\n" for record in records)
        if len(content.encode("utf-8")) > MAX_RUNTIME_PROJECTION_INCOMPATIBILITY_BYTES:
            raise GoalRuntimeError(
                "RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED"
            )
        _atomic_write(self.incompatibilities_path, content)

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
        content = "".join(self._event_json(event) + "\n" for event in events)
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_STORE_BYTES:
            raise GoalRuntimeError("RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED")
        _atomic_write(self.path, content)

    @classmethod
    def _assert_encoded_store_capacity(
        cls,
        events: Iterable[DurableRunEvent],
        tombstones: Iterable[RunEventIdempotencyTombstone],
    ) -> None:
        event_content = "".join(cls._event_json(event) + "\n" for event in events)
        tombstone_content = "".join(
            cls._tombstone_json(tombstone) + "\n" for tombstone in tombstones
        )
        if len(event_content.encode("utf-8")) > MAX_RUN_EVENT_STORE_BYTES:
            raise GoalRuntimeError("RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED")
        if len(tombstone_content.encode("utf-8")) > MAX_RUN_EVENT_IDEMPOTENCY_BYTES:
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED")

    @classmethod
    def _assert_projection_capacity(
        cls,
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
            "".join(cls._event_json(event) + "\n" for event in event_rows).encode(
                "utf-8"
            )
        )
        tombstone_bytes = len(
            "".join(
                cls._tombstone_json(tombstone) + "\n" for tombstone in tombstone_rows
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
            self._tombstone_json(tombstone) + "\n" for tombstone in tombstones
        )
        if len(content.encode("utf-8")) > MAX_RUN_EVENT_IDEMPOTENCY_BYTES:
            raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED")
        _atomic_write(self.idempotency_path, content)


class DurableRunEventReader:
    """Read-only facade for durable run evidence."""

    def __init__(
        self,
        store: _DurableRunEventStore,
        approvals: _GoalMutationApprovalStore,
        goals: _GoalJournalStore,
        runtime_invocation_state_dir: Path | None,
    ) -> None:
        self.__store = store
        self.__approvals = approvals
        self.__goals = goals
        self.__runtime_invocation_state_dir = runtime_invocation_state_dir

    def bind_runtime_invocation_state_dir(self, state_dir: Path) -> None:
        candidate = Path(state_dir)
        if (
            self.__runtime_invocation_state_dir is not None
            and self.__runtime_invocation_state_dir != candidate
        ):
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_TRUSTED_SOURCE_AUTHORITY_STORE_MISMATCH"
            )
        self.__runtime_invocation_state_dir = candidate

    def _validated_generation(
        self,
    ) -> tuple[
        list[DurableRunEvent],
        dict[tuple[str, str], RunEventIdempotencyTombstone],
    ]:
        for _attempt in range(3):
            try:
                with self.__approvals.consistent_read():
                    with self.__goals.consistent_read():
                        with self.__store.consistent_read():
                            approval_entries = self.__approvals._load_entries()
                            journal_entries = self.__goals._load_entries()
                            events = self.__store._load_events()
                            tombstones = self.__store._load_idempotency_tombstones(
                                events
                            )
                            all_events = [
                                *events,
                                *(item.event for item in tombstones.values()),
                            ]
                            self.__store._validate_trusted_sources(
                                all_events,
                                journal_entries=journal_entries,
                                runtime_invocation_state_dir=(
                                    self.__runtime_invocation_state_dir
                                ),
                            )
                            self.__approvals.validate_event_provenance(
                                approval_entries,
                                all_events,
                            )
                            return events, tombstones
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("RUN_EVENT_APPROVAL_GENERATION_UNSTABLE")

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
        events, _tombstones = self._validated_generation()
        return self.__store._replay_from_events(
            events,
            run_ref=run_ref,
            after_sequence=after_sequence,
            limit=bounded_limit,
        )

    def summaries(self) -> list[RunEventStreamSummary]:
        events, tombstones = self._validated_generation()
        return self.__store._summaries_from_events(events, tombstones)

    def retained_events(
        self,
        *,
        run_ref: str | None = None,
        limit: int = MAX_REPLAY_EVENTS,
    ) -> list[DurableRunEvent]:
        if run_ref is not None:
            validate_execution_ref(run_ref, "run_ref")
        bounded_limit = max(1, min(int(limit), MAX_REPLAY_EVENTS))
        events, _tombstones = self._validated_generation()
        return self.__store._retained_from_events(
            events,
            run_ref=run_ref,
            limit=bounded_limit,
        )

    def has_completion_evidence(
        self,
        *,
        run_ref: str,
        receipt_ref: str,
        proof_ref: str,
        goal_ref: str,
    ) -> bool:
        validate_execution_ref(run_ref, "run_ref")
        events, tombstones = self._validated_generation()
        return (
            self.__store._completion_receipt_event(
                events,
                tombstones,
                run_ref=run_ref,
                receipt_ref=receipt_ref,
                proof_ref=proof_ref,
                goal_ref=goal_ref,
            )
            is not None
        )

    def run_type(self, run_ref: str) -> AcceptedLocalRunType:
        validate_execution_ref(run_ref, "run_ref")
        events, _tombstones = self._validated_generation()
        for event in events:
            if event.run_ref == run_ref:
                return AcceptedLocalRunType(event.run_type)
        raise RunEventNotFoundError("RUN_EVENT_STREAM_NOT_FOUND")

    def projection_incompatibilities(
        self,
    ) -> list[RuntimeProjectionIncompatibilityRecord]:
        return self.__store.projection_incompatibilities()


class GoalRuntimeService:
    def __init__(
        self,
        state_dir: str | Path,
        *,
        retention_limit: int = DEFAULT_RUN_EVENT_RETENTION,
        runtime_invocation_state_dir: str | Path | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.runtime_invocation_state_dir = (
            Path(runtime_invocation_state_dir)
            if runtime_invocation_state_dir is not None
            else None
        )
        _validate_goal_runtime_state_dir_for_read(self.state_dir)
        self.goals = _GoalJournalStore(self.state_dir)
        self._submissions = _GoalMutationSubmissionStore(self.state_dir)
        self._approvals = _GoalMutationApprovalStore(self.state_dir)
        self._events = _DurableRunEventStore(
            self.state_dir, retention_limit=retention_limit
        )
        self.events = DurableRunEventReader(
            self._events,
            self._approvals,
            self.goals,
            self.runtime_invocation_state_dir,
        )

    def bind_runtime_invocation_store(
        self,
        invocation_store: RuntimeInvocationStore,
    ) -> None:
        raw_state_dir = getattr(invocation_store, "state_dir", None)
        if raw_state_dir is None:
            if self.runtime_invocation_state_dir is None:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_TRUSTED_SOURCE_AUTHORITY_UNAVAILABLE"
                )
            return
        candidate = Path(raw_state_dir)
        if (
            self.runtime_invocation_state_dir is not None
            and self.runtime_invocation_state_dir != candidate
        ):
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_TRUSTED_SOURCE_AUTHORITY_STORE_MISMATCH"
            )
        self.runtime_invocation_state_dir = candidate
        self.events.bind_runtime_invocation_state_dir(candidate)

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
        candidate = Path(state_dir)
        if configured:
            return cls(
                Path(configured).expanduser(),
                runtime_invocation_state_dir=candidate,
            )
        if candidate == Path(".uaa") / "runtime-gateway":
            return cls(
                DEFAULT_GOAL_RUNTIME_STATE_DIR,
                runtime_invocation_state_dir=candidate,
            )
        return cls(
            candidate / "goal_runtime",
            runtime_invocation_state_dir=candidate,
        )

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
        GoalMutationSubmissionRecoveryReadModel,
    ]:
        """Repair, then read, projections from one canonical generation.

        The lock order is always approvals, goal-journal, run-events, then
        submissions, matching the canonical writer dependency order. Missing
        first-generation lock files retain bounded optimistic-generation
        checks implemented by the non-mutating read lock. Existing durable
        producer records are reconciled before the pinned aggregate snapshot;
        absent stores remain non-initializing.
        """

        if run_ref is not None:
            validate_execution_ref(run_ref, "run_ref")
        if after_sequence < 0:
            raise ValueError("RUN_EVENT_CURSOR_INVALID")
        bounded_limit = max(1, min(int(limit), MAX_REPLAY_EVENTS))
        self._submissions.repair_recoverable_write()
        self._approvals.repair_recoverable_append()
        self._converge_expired_goal_mutation_approvals()
        if self.runtime_invocation_state_dir is not None:
            from ultimate_ai_agent.core.runtime_gateway.storage import (
                RuntimeInvocationStore,
            )

            runtime_store = RuntimeInvocationStore(
                self.runtime_invocation_state_dir
            )
            if _path_generation(runtime_store.path)[0]:
                self.sync_runtime_invocations(
                    runtime_store.list_invocations_locked(),
                    invocation_store=runtime_store,
                )
        if any(
            _path_generation(path)[0]
            for path in (
                self.goals.path,
                self.goals.head_path,
                self.goals.genesis_intent_path,
            )
        ):
            self.reconcile_durable_events()
        for _attempt in range(3):
            try:
                with self._approvals.consistent_read():
                    with self.goals.consistent_read():
                        with self._events.consistent_read():
                            with self._submissions.consistent_read():
                                approval_entries = self._approvals._load_entries()
                                events = self._events._load_events()
                                tombstones = self._events._load_idempotency_tombstones(
                                    events
                                )
                                entries = self.goals._load_entries()
                                self._events._validate_trusted_sources(
                                    [
                                        *events,
                                        *(item.event for item in tombstones.values()),
                                    ],
                                    journal_entries=entries,
                                    runtime_invocation_state_dir=(
                                        self.runtime_invocation_state_dir
                                    ),
                                )
                                submission_records = self._submissions._load()
                                self._approvals.validate_goal_provenance(
                                    approval_entries,
                                    entries,
                                )
                                self._approvals.validate_event_provenance(
                                    approval_entries,
                                    [
                                        *events,
                                        *(item.event for item in tombstones.values()),
                                    ],
                                )
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
                                goal_lifecycle = self.goals._read_model_from_entries(
                                    entries,
                                    include_cleared=True,
                                )
                                return (
                                    replay,
                                    retained,
                                    self._events._summaries_from_events(
                                        events,
                                        tombstones,
                                    ),
                                    goal_lifecycle,
                                    (
                                        self._submissions.recovery_read_model_from_records(
                                            submission_records,
                                            entries,
                                            approval_entries,
                                        )
                                    ),
                                )
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_RUNTIME_AGGREGATE_GENERATION_UNSTABLE")

    def _converge_expired_goal_mutation_approvals(self) -> int:
        """Resolve expired approval/submission truth before a shared snapshot."""

        def reject_linked_submission(
            spec: GoalMutationApprovalRequestSpec,
            reason_ref: str,
        ) -> None:
            with self.goals.mutation_entries() as journal_entries:
                self._submissions.reject_linked_approval(
                    spec=spec,
                    rejection_reason_ref=reason_ref,
                    journal_entries=journal_entries,
                )

        return self._approvals.expire_pending(
            before_terminal_append=reject_linked_submission,
        )

    def goal_lifecycle_read_model(
        self,
        *,
        include_cleared: bool = False,
    ) -> GoalLifecycleReadModel:
        """Read goals with the exact approval ledger generation validated."""

        self._approvals.repair_recoverable_append()
        for _attempt in range(3):
            try:
                with self._approvals.consistent_read():
                    with self.goals.consistent_read():
                        approval_entries = self._approvals._load_entries()
                        journal_entries = self.goals._load_entries()
                        self._approvals.validate_goal_provenance(
                            approval_entries,
                            journal_entries,
                        )
                        return self.goals._read_model_from_entries(
                            journal_entries,
                            include_cleared=include_cleared,
                        )
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_GENERATION_UNSTABLE")

    def goal_with_provenance(
        self,
        goal_ref: str,
        *,
        limit: int = MAX_GOAL_PROVENANCE_ENTRIES,
    ) -> tuple[PersistentGoal, GoalMutationProvenanceReadModel]:
        """Read one goal and its mutation history with approval provenance."""

        validate_execution_ref(goal_ref, "goal_ref")
        bounded_limit = max(1, min(int(limit), MAX_GOAL_PROVENANCE_ENTRIES))
        for _attempt in range(3):
            try:
                with self._approvals.consistent_read():
                    with self.goals.consistent_read():
                        approval_entries = self._approvals._load_entries()
                        journal_entries = self.goals._load_entries()
                        self._approvals.validate_goal_provenance(
                            approval_entries,
                            journal_entries,
                        )
                        matching = [
                            entry
                            for entry in journal_entries
                            if entry.goal_ref == goal_ref
                        ]
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
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_GENERATION_UNSTABLE")

    def record_goal_mutation_submission(
        self,
        *,
        submission_ref: str,
        operation: GoalMutationSubmissionOperation,
        goal_ref: str | None,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
        idempotency_ref: str,
    ) -> GoalMutationSubmissionRecord:
        with self.goals.mutation_entries() as journal_entries:
            return self._submissions.prepare(
                submission_ref=submission_ref,
                operation=operation,
                goal_ref=goal_ref,
                request=request,
                idempotency_ref=idempotency_ref,
                journal_entries=journal_entries,
            )

    @staticmethod
    def _approval_operation_and_subject(
        *,
        operation: GoalMutationSubmissionOperation | Literal["append-run-event"],
        goal_ref: str | None,
        request: (
            GoalCreateRequest
            | GoalEditRequest
            | GoalTransitionRequest
            | DurableRunEventAppendRequest
        ),
    ) -> tuple[str, str, dict[str, Any]]:
        if operation == "create":
            if goal_ref is not None:
                raise ValueError("GOAL_MUTATION_APPROVAL_CREATE_GOAL_REF_DENIED")
            validated = GoalCreateRequest.model_validate(request.model_dump())
            return "create", "goal-ref:new", validated.model_dump(mode="json")
        if operation == "edit":
            if goal_ref is None:
                raise ValueError("GOAL_MUTATION_APPROVAL_GOAL_REF_REQUIRED")
            validate_execution_ref(goal_ref, "goal_ref")
            validated = GoalEditRequest.model_validate(request.model_dump())
            return "edit", goal_ref, validated.model_dump(mode="json")
        if operation == "transition":
            if goal_ref is None:
                raise ValueError("GOAL_MUTATION_APPROVAL_GOAL_REF_REQUIRED")
            validate_execution_ref(goal_ref, "goal_ref")
            validated = GoalTransitionRequest.model_validate(request.model_dump())
            return (
                f"transition-{validated.transition}",
                goal_ref,
                validated.model_dump(mode="json"),
            )
        if goal_ref is not None:
            raise ValueError("RUN_EVENT_APPROVAL_GOAL_REF_DENIED")
        validated_event = DurableRunEventAppendRequest.model_validate(
            request.model_dump()
        )
        return (
            "append-run-event",
            validated_event.run_ref,
            validated_event.model_dump(mode="json"),
        )

    def prepare_goal_mutation_approval(
        self,
        *,
        operation: GoalMutationSubmissionOperation | Literal["append-run-event"],
        goal_ref: str | None,
        request: (
            GoalCreateRequest
            | GoalEditRequest
            | GoalTransitionRequest
            | DurableRunEventAppendRequest
        ),
        idempotency_ref: str,
        ttl_minutes: int = 30,
    ) -> GoalMutationApprovalRequestSpec:
        """Persist one exact pending approval request without granting it."""

        exact_operation, subject_ref, request_payload = (
            self._approval_operation_and_subject(
                operation=operation,
                goal_ref=goal_ref,
                request=request,
            )
        )
        if exact_operation == "append-run-event":
            _reject_trusted_core_run_event_idempotency_ref(idempotency_ref)
            _reject_trusted_core_run_event_idempotency_ref(
                DurableRunEventAppendRequest.model_validate(
                    request_payload
                ).idempotency_ref
            )
        return self._approvals.prepare(
            operation=exact_operation,
            subject_ref=subject_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
            ttl_minutes=ttl_minutes,
        )

    def decide_goal_mutation_approval(
        self,
        *,
        approval_request_ref: str,
        decision: Literal["approve", "deny"],
        decision_reason_ref: str,
    ) -> GoalMutationApprovalLedgerEntry:
        """Record one explicit operator approval or denial."""

        def converge_submission(
            spec: GoalMutationApprovalRequestSpec,
            reason_ref: str,
        ) -> None:
            with self.goals.mutation_entries() as journal_entries:
                self._submissions.reject_linked_approval(
                    spec=spec,
                    rejection_reason_ref=reason_ref,
                    journal_entries=journal_entries,
                )

        return self._approvals.decide(
            approval_request_ref=approval_request_ref,
            decision=decision,
            decision_reason_ref=decision_reason_ref,
            before_terminal_append=(
                converge_submission if decision == "deny" else None
            ),
        )

    def revoke_goal_mutation_approval(
        self,
        *,
        approval_ref: str,
        decision_reason_ref: str,
    ) -> GoalMutationApprovalLedgerEntry:
        """Revoke one exact approval without affecting any other request."""

        def converge_submission(
            spec: GoalMutationApprovalRequestSpec,
            reason_ref: str,
        ) -> None:
            with self.goals.mutation_entries() as journal_entries:
                self._submissions.reject_linked_approval(
                    spec=spec,
                    rejection_reason_ref=reason_ref,
                    journal_entries=journal_entries,
                )

        return self._approvals.revoke(
            approval_ref=approval_ref,
            decision_reason_ref=decision_reason_ref,
            before_terminal_append=converge_submission,
        )

    def reject_goal_mutation_submission(
        self,
        *,
        submission_ref: str,
        request_fingerprint_ref: str,
        rejection_reason_ref: str,
    ) -> GoalMutationSubmissionRecord:
        with self.goals.mutation_entries() as journal_entries:
            return self._submissions.reject(
                submission_ref=submission_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                rejection_reason_ref=rejection_reason_ref,
                journal_entries=journal_entries,
            )

    def goal_mutation_submission_record_for_request(
        self,
        *,
        operation: GoalMutationSubmissionOperation,
        goal_ref: str | None,
        request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest,
        idempotency_ref: str,
    ) -> GoalMutationSubmissionRecord | None:
        """Inspect the exact backend-owned envelope used by a CLI retry."""

        return self._submissions.mutation_binding_record(
            operation=operation,
            goal_ref=goal_ref,
            request=request,
            idempotency_ref=idempotency_ref,
        )

    def assert_runtime_mission_goal_exists(self, mission_ref: str | None) -> None:
        """Fail closed before execution when a mission claims a durable goal."""

        if mission_ref is None or not mission_ref.startswith("goal-ref:"):
            return
        validate_execution_ref(mission_ref, "mission_ref")
        for _attempt in range(3):
            try:
                with self._approvals.consistent_read():
                    with self.goals.consistent_read():
                        approval_entries = self._approvals._load_entries()
                        journal_entries = self.goals._load_entries()
                        self._approvals.validate_goal_provenance(
                            approval_entries,
                            journal_entries,
                        )
                        if mission_ref not in self.goals._latest_by_goal(
                            journal_entries
                        ):
                            raise GoalNotFoundError("GOAL_NOT_FOUND")
                        return
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_GENERATION_UNSTABLE")

    @contextmanager
    def runtime_mission_execution_guard(
        self,
        mission_ref: str | None,
        *,
        allow_committed_replay: bool = False,
        committed_replay_lookup: Callable[[], bool] | None = None,
    ) -> Iterator[None]:
        """Pin one runnable goal generation across an adapter dispatch.

        Exact committed runtime replays may outlive the goal's runnable state,
        but a new adapter dispatch is admitted only while the durable goal is
        active. The caller must complete projection reconciliation and capacity
        reservation before entering this context. Canonical exclusive approval
        then journal locks preserve the admission decision through adapter
        execution without a shared-to-exclusive lock upgrade.
        """

        if mission_ref is None or not mission_ref.startswith("goal-ref:"):
            yield
            return
        validate_execution_ref(mission_ref, "mission_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(
            self._approvals._locks,  # noqa: SLF001
            "goal-approvals",
        ):
            with _normalized_goal_runtime_lock(
                self.goals._locks,  # noqa: SLF001
                "goal-journal",
            ):
                approval_entries = self._approvals._load_entries(repair_manifest=True)
                journal_entries = self.goals._load_entries(repair_manifest=True)
                self._approvals.validate_goal_provenance(
                    approval_entries,
                    journal_entries,
                )
                current = self.goals._latest_by_goal(journal_entries).get(mission_ref)
                if current is None:
                    raise GoalNotFoundError("GOAL_NOT_FOUND")
                committed_replay_available = allow_committed_replay
                if (
                    not committed_replay_available
                    and committed_replay_lookup is not None
                ):
                    committed_replay_available = committed_replay_lookup()
                if (
                    not committed_replay_available
                    and current.state != GoalState.active.value
                ):
                    raise GoalTransitionDeniedError("GOAL_MISSION_NOT_RUNNABLE")
                yield

    def create_goal(
        self,
        request: GoalCreateRequest,
        *,
        idempotency_ref: str,
        approval_ref: str,
    ) -> tuple[PersistentGoal, GoalMutationApprovalBinding]:
        validated = GoalCreateRequest.model_validate(request.model_dump())
        request_payload = validated.model_dump(mode="json")
        submission_fingerprint_ref = self._submissions.mutation_binding_fingerprint(
            operation="create",
            goal_ref=None,
            request=validated,
            idempotency_ref=idempotency_ref,
        )
        with self._approvals.validated_goal_mutation(
            approval_ref=approval_ref,
            operation="create",
            subject_ref="goal-ref:new",
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
            committed_lookup=lambda: self.goals.replay_mutation_entry(
                operation=GoalJournalOperation.create,
                goal_ref=None,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
            ),
        ) as (approval_binding, committed_entry):
            if committed_entry is not None:
                return committed_entry.goal.model_copy(deep=True), approval_binding
            self.reconcile_durable_events()
            goal = self.goals.create(
                validated,
                idempotency_ref=idempotency_ref,
                approval_binding=approval_binding,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
                submission_terminal_guard=lambda entries: (
                    self._submissions.terminal_commit_guard(
                        request_fingerprint_ref=submission_fingerprint_ref,
                        idempotency_ref=idempotency_ref,
                        journal_entries=entries,
                    )
                ),
            )
            return goal, approval_binding

    def edit_goal(
        self,
        goal_ref: str,
        request: GoalEditRequest,
        *,
        idempotency_ref: str,
        approval_ref: str,
    ) -> tuple[PersistentGoal, GoalMutationApprovalBinding]:
        validated = GoalEditRequest.model_validate(request.model_dump())
        request_payload = validated.model_dump(mode="json")
        submission_fingerprint_ref = self._submissions.mutation_binding_fingerprint(
            operation="edit",
            goal_ref=goal_ref,
            request=validated,
            idempotency_ref=idempotency_ref,
        )
        with self._approvals.validated_goal_mutation(
            approval_ref=approval_ref,
            operation="edit",
            subject_ref=goal_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
            committed_lookup=lambda: self.goals.replay_mutation_entry(
                operation=GoalJournalOperation.edit,
                goal_ref=goal_ref,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
            ),
        ) as (approval_binding, committed_entry):
            if committed_entry is not None:
                return committed_entry.goal.model_copy(deep=True), approval_binding
            self.reconcile_durable_events()
            goal = self.goals.edit(
                goal_ref,
                validated,
                idempotency_ref=idempotency_ref,
                approval_binding=approval_binding,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
                submission_terminal_guard=lambda entries: (
                    self._submissions.terminal_commit_guard(
                        request_fingerprint_ref=submission_fingerprint_ref,
                        idempotency_ref=idempotency_ref,
                        journal_entries=entries,
                    )
                ),
            )
            return goal, approval_binding

    def transition_goal(
        self,
        goal_ref: str,
        request: GoalTransitionRequest,
        *,
        idempotency_ref: str,
        approval_ref: str,
    ) -> tuple[PersistentGoal, GoalMutationApprovalBinding]:
        validated = GoalTransitionRequest.model_validate(request.model_dump())
        request_payload = validated.model_dump(mode="json")
        approval_operation = f"transition-{validated.transition}"
        submission_fingerprint_ref = self._submissions.mutation_binding_fingerprint(
            operation="transition",
            goal_ref=goal_ref,
            request=validated,
            idempotency_ref=idempotency_ref,
        )
        with self._approvals.validated_goal_mutation(
            approval_ref=approval_ref,
            operation=approval_operation,
            subject_ref=goal_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
            committed_lookup=lambda: self.goals.replay_mutation_entry(
                operation=GoalJournalOperation.transition,
                goal_ref=goal_ref,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
            ),
        ) as (approval_binding, committed_entry):
            if committed_entry is not None:
                replayed = committed_entry.goal.model_copy(deep=True)
                if (
                    validated.transition == GoalTransitionKind.verify_completion.value
                    and replayed.state == GoalState.verified_complete.value
                ):
                    self.reconcile_durable_events()
                return replayed, approval_binding
            self.reconcile_durable_events()
            replayed = self.goals.replay_transition(
                goal_ref,
                validated,
                idempotency_ref=idempotency_ref,
                goal_submission_fingerprint_ref=submission_fingerprint_ref,
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
                    self.reconcile_durable_events()
                return replayed, approval_binding
            completion_verified = False
            evidence = validated.completion_evidence
            journal_lock = (
                _normalized_goal_runtime_lock(
                    self.goals._locks,
                    "goal-journal",
                )
                if evidence is not None
                else nullcontext()
            )
            event_lock = (
                self._events.exclusive() if evidence is not None else nullcontext()
            )
            completion_plan_ref: str | None = None
            completion_criterion_verifier_bindings: list[
                RuntimeCriterionVerificationBinding
            ] = []
            with journal_lock, event_lock:
                if evidence is not None:
                    journal_entries = self.goals._load_entries(
                        repair_manifest=True
                    )
                    current = self.goals._latest_by_goal(  # noqa: SLF001
                        journal_entries
                    ).get(goal_ref)
                    if current is None:
                        raise GoalNotFoundError("GOAL_NOT_FOUND")
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
                    approval_entries = self._approvals._load_entries()
                    retained_events = self._events._load_events()
                    retained_tombstones = self._events._load_idempotency_tombstones(
                        retained_events
                    )
                    self._events._validate_trusted_sources(
                        [
                            *retained_events,
                            *(
                                tombstone.event
                                for tombstone in retained_tombstones.values()
                            ),
                        ],
                        journal_entries=journal_entries,
                        runtime_invocation_state_dir=(
                            self.runtime_invocation_state_dir
                        ),
                    )
                    self._approvals.validate_event_provenance(
                        approval_entries,
                        [
                            *retained_events,
                            *(
                                tombstone.event
                                for tombstone in retained_tombstones.values()
                            ),
                        ],
                    )
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
                    goal_submission_fingerprint_ref=submission_fingerprint_ref,
                    submission_terminal_guard=lambda entries: (
                        self._submissions.terminal_commit_guard(
                            request_fingerprint_ref=submission_fingerprint_ref,
                            idempotency_ref=idempotency_ref,
                            journal_entries=entries,
                        )
                    ),
                )
                if (
                    validated.transition == GoalTransitionKind.verify_completion.value
                    and goal.state == GoalState.verified_complete.value
                ):
                    source_matches = [
                        entry
                        for entry in self.goals._load_entries(  # noqa: SLF001
                            repair_manifest=True
                        )
                        if (
                            entry.goal_ref == goal.goal_ref
                            and entry.goal.version == goal.version
                        )
                    ]
                    if len(source_matches) != 1:
                        raise GoalRuntimeCorruptionError(
                            "GOAL_COMPLETION_SOURCE_ENTRY_MISSING"
                        )
                    self._append_verified_completion_event(
                        source_matches[0],
                        approval_decision_ref=(approval_binding.approval_decision_ref),
                    )
            return goal, approval_binding

    def _reconcile_verified_completion_events_approval_held(
        self,
        approval_entries: list[GoalMutationApprovalLedgerEntry],
    ) -> None:
        """Repair completion projections under approval -> journal -> event locks."""

        with _normalized_goal_runtime_lock(self.goals._locks, "goal-journal"):
            journal_entries = self.goals._load_entries(repair_manifest=True)
            self._approvals.validate_goal_provenance(
                approval_entries,
                journal_entries,
            )
            latest_goals = self.goals._latest_by_goal(journal_entries)  # noqa: SLF001
            previous_states: dict[str, str] = {}
            verified_entries: dict[str, GoalJournalEntry] = {}
            for entry in journal_entries:
                if (
                    previous_states.get(entry.goal_ref)
                    == GoalState.complete_requested.value
                    and entry.goal.state == GoalState.verified_complete.value
                ):
                    verified_entries[entry.goal_ref] = entry
                previous_states[entry.goal_ref] = entry.goal.state

            with self._events.exclusive():
                events = self._events._load_events()
                tombstones = self._events._load_idempotency_tombstones(events)
                self._events._validate_trusted_sources(
                    [
                        *events,
                        *(item.event for item in tombstones.values()),
                    ],
                    journal_entries=journal_entries,
                    runtime_invocation_state_dir=(
                        self.runtime_invocation_state_dir
                    ),
                )
                self._approvals.validate_event_provenance(
                    approval_entries,
                    [
                        *events,
                        *(item.event for item in tombstones.values()),
                    ],
                )
                for goal in latest_goals.values():
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
                    verified_entry = verified_entries.get(goal.goal_ref)
                    if verified_entry is None:
                        raise GoalRuntimeCorruptionError(
                            "GOAL_VERIFIED_COMPLETION_ENTRY_MISSING"
                        )
                    self._append_verified_completion_event(
                        verified_entry,
                        approval_decision_ref=(verified_entry.approval_decision_ref),
                    )

    def reconcile_durable_events(self) -> None:
        """Repair journal projections under the canonical approval lock order."""

        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(
            self._approvals._locks,
            "goal-approvals",
        ):
            approval_entries = self._approvals._load_entries(repair_manifest=True)
            self._reconcile_verified_completion_events_approval_held(approval_entries)

    def _append_verified_completion_event(
        self,
        goal_or_entry: PersistentGoal | GoalJournalEntry,
        *,
        approval_decision_ref: str,
    ) -> DurableRunEvent:
        if isinstance(goal_or_entry, GoalJournalEntry):
            source_entry = goal_or_entry
            goal = source_entry.goal
        else:
            goal = goal_or_entry
            source_matches = [
                entry
                for entry in self.goals._load_consistent_entries()
                if (
                    entry.goal_ref == goal.goal_ref
                    and entry.goal.version == goal.version
                )
            ]
            if len(source_matches) != 1:
                raise GoalRuntimeCorruptionError("GOAL_COMPLETION_SOURCE_ENTRY_MISSING")
            source_entry = source_matches[0]
        if approval_decision_ref != source_entry.approval_decision_ref:
            raise GoalRuntimeCorruptionError(
                "GOAL_COMPLETION_APPROVAL_PROVENANCE_MISMATCH"
            )
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
        retained_run_events = [
            event
            for event in self._events._load_events()
            if event.run_ref == goal.completion_run_ref
        ]
        if not retained_run_events:
            raise GoalRuntimeCorruptionError("RUN_EVENT_STREAM_NOT_FOUND")
        run_type = AcceptedLocalRunType(retained_run_events[-1].run_type)
        return self._events._append_locked(
            self._events._completion_projection_request(
                source_entry,
                run_type=run_type,
            ),
            trusted_source=TrustedRunEventSourceBinding(
                source_kind="goal_journal_completion",
                source_ref=source_entry.entry_ref,
                source_fingerprint_ref=source_entry.entry_hash_ref,
            ),
        )

    def append_run_event(
        self,
        request: DurableRunEventAppendRequest,
        *,
        approval_ref: str,
    ) -> DurableRunEvent:
        """Append one exact operator-approved metadata event."""

        validated = DurableRunEventAppendRequest.model_validate(request.model_dump())
        _reject_trusted_core_run_event_idempotency_ref(validated.idempotency_ref)
        if validated.event_kind in {
            DurableRunEventKind.receipt_recorded.value,
            *TERMINAL_RUN_EVENT_KINDS,
        }:
            raise GoalTransitionDeniedError("RUN_EVENT_TRUSTED_PRODUCER_REQUIRED")
        with self._approvals.validated_event_mutation(
            approval_ref=approval_ref,
            request=validated,
            committed_lookup=lambda: self._events.replay_append(validated),
        ) as (approval_binding, committed_event):
            if committed_event is not None:
                return committed_event
            self.reconcile_durable_events()
            return self._events.append(
                validated,
                approval_binding=approval_binding,
            )

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
            RuntimeInvocationStatus,
        )

        self.bind_runtime_invocation_store(invocation_store)
        validated = self._durable_runtime_invocation(
            record,
            invocation_store=invocation_store,
        )
        self.assert_runtime_mission_goal_exists(validated.request.mission_ref)
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
        started_request, recorded_request = (
            self._events._runtime_projection_requests(validated)
        )
        trusted_source = TrustedRunEventSourceBinding(
            source_kind="runtime_invocation",
            source_ref=validated.invocation_ref,
            source_fingerprint_ref=_sha256_ref(
                "source-fingerprint-ref:runtime-invocation",
                _runtime_invocation_source_payload(validated),
            ),
        )
        with self._events.exclusive():
            self._events.bind_runtime_projection_reservation(
                reservation_ref,
                validated,
            )
            started = self._events._append_locked(
                started_request,
                reservation_ref=reservation_ref,
                trusted_source=trusted_source,
            )
            recorded = self._events._append_locked(
                recorded_request,
                reservation_ref=reservation_ref,
                trusted_source=trusted_source,
            )
        return [started, recorded]

    @staticmethod
    def _durable_runtime_invocation(
        record: RuntimeInvocationRecord,
        *,
        invocation_store: RuntimeInvocationStore,
    ) -> RuntimeInvocationRecord:
        from ultimate_ai_agent.core.runtime_gateway.contracts import (
            RuntimeInvocationRecord,
        )
        from ultimate_ai_agent.core.runtime_gateway.storage import (
            RuntimeInvocationStorageError,
        )

        candidate = RuntimeInvocationRecord.model_validate(record.model_dump())
        try:
            stored_record = invocation_store.get_invocation(candidate.invocation_ref)
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
        if durable_record.invocation_ref != candidate.invocation_ref:
            raise GoalRuntimeCorruptionError(
                "RUN_EVENT_DURABLE_INVOCATION_REF_MISMATCH"
            )
        return durable_record

    def sync_runtime_invocations(
        self,
        records: Iterable[RuntimeInvocationRecord],
        *,
        invocation_store: RuntimeInvocationStore,
    ) -> list[DurableRunEvent]:
        self.bind_runtime_invocation_store(invocation_store)
        self.reconcile_durable_events()
        projected: list[DurableRunEvent] = []
        quarantined_invocation_refs = {
            record.invocation_ref
            for record in self._events.projection_incompatibilities()
        }
        for record in self._events.unprojected_runtime_invocations(records):
            durable_record = self._durable_runtime_invocation(
                record,
                invocation_store=invocation_store,
            )
            if record.invocation_ref in quarantined_invocation_refs:
                self._events.quarantine_projection_incompatibility(durable_record)
                continue
            try:
                projected.extend(
                    self.record_accepted_runtime_invocation(
                        durable_record,
                        invocation_store=invocation_store,
                    )
                )
            except GoalNotFoundError:
                # Historical opaque goal-shaped missions predate the durable goal
                # journal. Quarantine their exact durable receipt so later syncs do
                # not retry silently; new executions retain the strict preflight.
                try:
                    self._events.quarantine_projection_incompatibility(durable_record)
                except GoalRuntimeError as exc:
                    if (
                        str(exc)
                        != "RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED"
                    ):
                        raise
                continue
        return projected


class GoalMutationApprovalBinding(BaseModel):
    schema_version: str = "goal_mutation_approval_binding.v1"
    approval_ref: str
    approval_request_ref: str
    approval_decision_ref: str
    approval_ledger_entry_hash_ref: str
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
            (
                self.approval_ledger_entry_hash_ref,
                "approval_ledger_entry_hash_ref",
            ),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.operator_actor_ref, "operator_actor_ref"),
        ):
            validate_execution_ref(value, field_name)
        if not self.approval_validated or self.standing_authority_granted:
            raise ValueError("GOAL_MUTATION_APPROVAL_POSTURE_INVALID")
        return self


class GoalMutationApprovalRequestSpec(BaseModel):
    """Deterministic, non-authorizing description of one exact mutation."""

    schema_version: Literal["goal_mutation_approval_request.v2"] = (
        "goal_mutation_approval_request.v2"
    )
    operation: str
    subject_ref: str
    idempotency_ref: str
    request_fingerprint_ref: str
    mutation_request_fingerprint_ref: str
    exact_scope_ref: str
    approval_request_ref: str
    approval_ref: str
    operator_actor_ref: str = "operator-ref:local-user"
    requested_at: datetime
    expires_at: datetime

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_spec(self) -> "GoalMutationApprovalRequestSpec":
        validate_safe_execution_text(self.operation, "operation")
        for value, field_name in (
            (self.subject_ref, "subject_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (
                self.mutation_request_fingerprint_ref,
                "mutation_request_fingerprint_ref",
            ),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.approval_request_ref, "approval_request_ref"),
            (self.approval_ref, "approval_ref"),
            (self.operator_actor_ref, "operator_actor_ref"),
        ):
            validate_execution_ref(value, field_name)
        if self.expires_at <= self.requested_at:
            raise ValueError("GOAL_MUTATION_APPROVAL_EXPIRY_INVALID")
        return self


GoalMutationApprovalDecisionStatus = Literal[
    "pending",
    "approved",
    "denied",
    "revoked",
    "expired",
]


def build_goal_mutation_approval_decision_idempotency_ref(
    approval_request_ref: str,
) -> str:
    """Return the one standard-header idempotency ref for a decision."""

    validate_execution_ref(approval_request_ref, "approval_request_ref")
    return f"idempotency-ref:goal-approval-decision:{approval_request_ref}"


def build_goal_mutation_approval_revoke_idempotency_ref(
    approval_ref: str,
) -> str:
    """Return the one standard-header idempotency ref for a revocation."""

    validate_execution_ref(approval_ref, "approval_ref")
    return f"idempotency-ref:goal-approval-revoke:{approval_ref}"


class GoalMutationApprovalLedgerEntry(BaseModel):
    """One append-only, hash-chained approval request or decision."""

    schema_version: Literal["goal_mutation_approval_ledger.v2"] = (
        "goal_mutation_approval_ledger.v2"
    )
    spec: GoalMutationApprovalRequestSpec
    status: GoalMutationApprovalDecisionStatus
    approval_grant: ApprovalGrant | None = None
    decision_reason_ref: str | None = None
    decision_actor_ref: str | None = None
    decided_at: datetime | None = None
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "GoalMutationApprovalLedgerEntry":
        validate_execution_ref(self.entry_hash_ref, "entry_hash_ref")
        if self.previous_entry_hash_ref is not None:
            validate_execution_ref(
                self.previous_entry_hash_ref,
                "previous_entry_hash_ref",
            )
        if self.decision_reason_ref is not None:
            validate_execution_ref(self.decision_reason_ref, "decision_reason_ref")
        if self.decision_actor_ref is not None:
            validate_execution_ref(self.decision_actor_ref, "decision_actor_ref")
        if self.status == "pending":
            if (
                self.approval_grant is not None
                or self.decision_reason_ref is not None
                or self.decision_actor_ref is not None
                or self.decided_at is not None
            ):
                raise ValueError("GOAL_MUTATION_APPROVAL_PENDING_DECISION_DENIED")
        elif self.status == "approved":
            if (
                self.approval_grant is None
                or self.approval_grant.status != "granted"
                or self.decided_at is None
                or self.decision_reason_ref is None
                or self.decision_actor_ref is None
            ):
                raise ValueError("GOAL_MUTATION_APPROVAL_GRANT_REQUIRED")
        elif self.status in {"denied", "expired"}:
            if (
                self.approval_grant is not None
                or self.decided_at is None
                or self.decision_reason_ref is None
                or self.decision_actor_ref is None
            ):
                raise ValueError("GOAL_MUTATION_APPROVAL_DENIAL_BINDING_REQUIRED")
        elif (
            self.approval_grant is None
            or self.approval_grant.status != "revoked"
            or self.approval_grant.revoked_at is None
            or self.decided_at is None
            or self.decision_reason_ref is None
            or self.decision_actor_ref is None
        ):
            raise ValueError("GOAL_MUTATION_APPROVAL_REVOCATION_BINDING_REQUIRED")
        if self.approval_grant is not None:
            if (
                self.approval_grant.approval_ref != self.spec.approval_ref
                or self.approval_grant.approval_request_id
                != self.spec.approval_request_ref
                or self.approval_grant.subject_id != self.spec.subject_ref
                or self.approval_grant.granted_to_actor_id
                != self.spec.operator_actor_ref
                or self.approval_grant.approved_by_actor_id != self.decision_actor_ref
                or self.approval_grant.expires_at != self.spec.expires_at
            ):
                raise ValueError("GOAL_MUTATION_APPROVAL_GRANT_BINDING_MISMATCH")
        return self


class GoalMutationApprovalHeadManifest(BaseModel):
    """Independent anchor for the exact terminal approval-ledger generation."""

    schema_version: Literal["goal_mutation_approval_head.v1"] = (
        "goal_mutation_approval_head.v1"
    )
    entry_count: StrictInt = Field(
        ge=1,
        le=MAX_GOAL_MUTATION_APPROVAL_ENTRIES,
    )
    head_entry_hash_ref: str
    request_state_set_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "GoalMutationApprovalHeadManifest":
        validate_execution_ref(self.head_entry_hash_ref, "head_entry_hash_ref")
        validate_execution_ref(
            self.request_state_set_hash_ref,
            "request_state_set_hash_ref",
        )
        return self


class GoalMutationApprovalAppendIntent(BaseModel):
    """Durable precommit binding for one exact approval-ledger append."""

    schema_version: Literal["goal_mutation_approval_append_intent.v1"] = (
        "goal_mutation_approval_append_intent.v1"
    )
    previous_head_manifest: GoalMutationApprovalHeadManifest | None = None
    next_entry: GoalMutationApprovalLedgerEntry
    next_head_manifest: GoalMutationApprovalHeadManifest
    ledger_content_hash_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intent(self) -> "GoalMutationApprovalAppendIntent":
        validate_execution_ref(
            self.ledger_content_hash_ref,
            "ledger_content_hash_ref",
        )
        previous_count = (
            self.previous_head_manifest.entry_count
            if self.previous_head_manifest is not None
            else 0
        )
        previous_hash = (
            self.previous_head_manifest.head_entry_hash_ref
            if self.previous_head_manifest is not None
            else None
        )
        if (
            self.next_entry.previous_entry_hash_ref != previous_hash
            or self.next_head_manifest.entry_count != previous_count + 1
            or self.next_head_manifest.head_entry_hash_ref
            != self.next_entry.entry_hash_ref
        ):
            raise ValueError("GOAL_MUTATION_APPROVAL_APPEND_INTENT_INVALID")
        if self.previous_head_manifest is None and self.next_entry.status != "pending":
            raise ValueError("GOAL_MUTATION_APPROVAL_APPEND_INTENT_INVALID")
        return self


class GoalMutationApprovalDecisionRequest(BaseModel):
    decision: Literal["approve", "deny"]
    decision_reason_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "GoalMutationApprovalDecisionRequest":
        validate_execution_ref(self.decision_reason_ref, "decision_reason_ref")
        return self


class GoalMutationApprovalRevokeRequest(BaseModel):
    approval_ref: str
    decision_reason_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "GoalMutationApprovalRevokeRequest":
        validate_execution_ref(self.approval_ref, "approval_ref")
        validate_execution_ref(self.decision_reason_ref, "decision_reason_ref")
        return self


def _goal_mutation_approval_request_fingerprint_ref(
    *,
    operation: str,
    subject_ref: str,
    request_payload: dict[str, Any],
    idempotency_ref: str,
) -> str:
    validate_safe_execution_text(operation, "operation")
    validate_execution_ref(subject_ref, "subject_ref")
    validate_execution_ref(idempotency_ref, "idempotency_ref")
    return _sha256_ref(
        "request-fingerprint-ref:goal-mutation",
        {
            "operation": operation,
            "subject_ref": subject_ref,
            "request_payload": request_payload,
            "idempotency_ref": idempotency_ref,
        },
    )


def _mutation_request_fingerprint_ref(
    *,
    operation: str,
    subject_ref: str,
    request_payload: dict[str, Any],
) -> str:
    """Bind the approval ledger to the exact durable mutation fingerprint."""

    if operation == "create":
        return _sha256_ref(
            "request-fingerprint-ref:goal-create",
            request_payload,
        )
    if operation == "edit":
        return _sha256_ref(
            "request-fingerprint-ref:goal-edit",
            {"goal_ref": subject_ref, "request": request_payload},
        )
    if operation.startswith("transition-"):
        return _sha256_ref(
            "request-fingerprint-ref:goal-transition",
            {"goal_ref": subject_ref, "request": request_payload},
        )
    if operation == "append-run-event":
        return _sha256_ref(
            "request-fingerprint-ref:run-event",
            request_payload,
        )
    raise ValueError("GOAL_MUTATION_APPROVAL_OPERATION_INVALID")


def build_exact_goal_mutation_approval_request_spec(
    *,
    operation: str,
    subject_ref: str,
    request_payload: dict[str, Any],
    idempotency_ref: str,
    requested_at: datetime,
    expires_at: datetime,
) -> GoalMutationApprovalRequestSpec:
    """Build the exact request identity without granting or validating it."""

    request_fingerprint_ref = _goal_mutation_approval_request_fingerprint_ref(
        operation=operation,
        subject_ref=subject_ref,
        request_payload=request_payload,
        idempotency_ref=idempotency_ref,
    )
    mutation_request_fingerprint_ref = _mutation_request_fingerprint_ref(
        operation=operation,
        subject_ref=subject_ref,
        request_payload=request_payload,
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
    return GoalMutationApprovalRequestSpec(
        operation=operation,
        subject_ref=subject_ref,
        idempotency_ref=idempotency_ref,
        request_fingerprint_ref=request_fingerprint_ref,
        mutation_request_fingerprint_ref=mutation_request_fingerprint_ref,
        exact_scope_ref=exact_scope_ref,
        approval_request_ref=approval_request_ref,
        approval_ref=approval_ref,
        requested_at=requested_at,
        expires_at=expires_at,
    )


def build_exact_goal_mutation_approval_request(
    spec: GoalMutationApprovalRequestSpec,
) -> ApprovalRequest:
    """Project one deterministic spec into the canonical approval contract."""

    return ApprovalRequest(
        approval_request_id=spec.approval_request_ref,
        run_id=_sha256_ref(
            "run-ref:goal-mutation",
            {"exact_scope_ref": spec.exact_scope_ref},
        ),
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=spec.subject_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id=spec.operator_actor_ref,
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=f"goal_mutation_{spec.operation}",
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
            spec.subject_ref,
            spec.exact_scope_ref,
            spec.request_fingerprint_ref,
            spec.mutation_request_fingerprint_ref,
            spec.idempotency_ref,
        ],
        event_ref=_sha256_ref(
            "event-ref:goal-mutation-approval",
            {"approval_request_ref": spec.approval_request_ref},
        ),
        trace_id=spec.approval_request_ref,
        created_at=spec.requested_at,
        expires_at=spec.expires_at,
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
    request_fingerprint_ref = _goal_mutation_approval_request_fingerprint_ref(
        operation=operation,
        subject_ref=subject_ref,
        request_payload=request_payload,
        idempotency_ref=idempotency_ref,
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
    if (
        validated.approval_ref != approval_ref
        or validated.approval_request_ref != approval_request_ref
        or validated.exact_scope_ref != exact_scope_ref
        or validated.request_fingerprint_ref != request_fingerprint_ref
        or validated.approval_decision_ref
        != _sha256_ref(
            "approval-decision-ref:goal-mutation",
            {
                "approval_ref": approval_ref,
                "ledger_entry_hash_ref": (validated.approval_ledger_entry_hash_ref),
                "status": "approved",
            },
        )
    ):
        raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_BINDING_MISMATCH")


class _GoalMutationApprovalStore:
    """Append-only exact approval request and decision ledger."""

    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / "goal_mutation_approvals.jsonl"
        self.head_path = self.state_dir / "goal_mutation_approvals_head.json"
        self.append_intent_path = (
            self.state_dir / "goal_mutation_approvals_append_intent.json"
        )
        self._locks = FileSingleWriterLockManager(self.state_dir / ".locks")

    @staticmethod
    def _entry_hash(entry: GoalMutationApprovalLedgerEntry) -> str:
        payload = entry.model_dump(mode="json")
        payload.pop("entry_hash_ref", None)
        return _sha256_ref("entry-hash-ref:goal-mutation-approval", payload)

    def _load_entries(
        self,
        *,
        repair_manifest: bool = False,
    ) -> list[GoalMutationApprovalLedgerEntry]:
        append_intent = self._load_append_intent()
        raw_content = _read_bounded_regular_utf8(
            self.path,
            max_bytes=MAX_GOAL_MUTATION_APPROVAL_LEDGER_BYTES,
            missing_ok=True,
            capacity_error="GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED",
            corruption_error="GOAL_MUTATION_APPROVAL_LEDGER_CORRUPT",
        )
        if raw_content is None:
            manifest = self._load_head_manifest()
            if append_intent is not None:
                if (
                    append_intent.previous_head_manifest is not None
                    or manifest is not None
                ):
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH"
                    )
                if not repair_manifest:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_APPEND_RECOVERY_REQUIRED"
                    )
                self._install_append_intent(append_intent)
                return [append_intent.next_entry.model_copy(deep=True)]
            if manifest is not None:
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_LEDGER_MISSING_WITH_HEAD"
                )
            return []
        if not raw_content.strip():
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_LEDGER_EMPTY_ROLLBACK"
            )
        entries: list[GoalMutationApprovalLedgerEntry] = []
        previous: str | None = None
        latest: dict[str, GoalMutationApprovalLedgerEntry] = {}
        approval_refs: dict[str, str] = {}
        try:
            for raw_line in raw_content.splitlines():
                if not raw_line.strip():
                    continue
                entry = GoalMutationApprovalLedgerEntry.model_validate_json(raw_line)
                if entry.previous_entry_hash_ref != previous:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_HASH_CHAIN_MISMATCH"
                    )
                if entry.entry_hash_ref != self._entry_hash(entry):
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_ENTRY_HASH_MISMATCH"
                    )
                request_ref = entry.spec.approval_request_ref
                known_request = approval_refs.get(entry.spec.approval_ref)
                if known_request is not None and known_request != request_ref:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_REF_AMBIGUOUS"
                    )
                approval_refs[entry.spec.approval_ref] = request_ref
                prior = latest.get(request_ref)
                if prior is None:
                    if entry.status != "pending":
                        raise GoalRuntimeCorruptionError(
                            "GOAL_MUTATION_APPROVAL_PREPARE_MISSING"
                        )
                else:
                    if entry.spec != prior.spec:
                        raise GoalRuntimeCorruptionError(
                            "GOAL_MUTATION_APPROVAL_REQUEST_BINDING_MISMATCH"
                        )
                    allowed = {
                        "pending": {"approved", "denied", "expired"},
                        "approved": {"revoked", "expired"},
                        "denied": set(),
                        "revoked": set(),
                        "expired": set(),
                    }[prior.status]
                    if entry.status not in allowed:
                        raise GoalRuntimeCorruptionError(
                            "GOAL_MUTATION_APPROVAL_DECISION_SEQUENCE_INVALID"
                        )
                latest[request_ref] = entry
                entries.append(entry)
                if len(entries) > MAX_GOAL_MUTATION_APPROVAL_ENTRIES:
                    raise GoalRuntimeCorruptionError(
                        "GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED"
                    )
                previous = entry.entry_hash_ref
        except GoalRuntimeCorruptionError:
            raise
        except (UnicodeError, ValueError, TypeError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_LEDGER_CORRUPT"
            ) from exc
        self._assert_terminal_capacity(entries)
        manifest = self._load_head_manifest()
        exact_manifest = self._build_head_manifest(entries)
        if append_intent is None:
            if manifest == exact_manifest:
                return entries
            code = (
                "GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISSING"
                if manifest is None
                else "GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISMATCH"
            )
            raise GoalRuntimeCorruptionError(code)
        if not repair_manifest:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_RECOVERY_REQUIRED"
            )
        previous_manifest = append_intent.previous_head_manifest
        next_entries: list[GoalMutationApprovalLedgerEntry]
        if manifest == previous_manifest and exact_manifest == previous_manifest:
            next_entries = [*entries, append_intent.next_entry]
        elif (
            manifest == previous_manifest
            and len(entries)
            == (
                previous_manifest.entry_count + 1
                if previous_manifest is not None
                else 1
            )
            and entries[-1] == append_intent.next_entry
        ):
            next_entries = entries
        elif (
            manifest == append_intent.next_head_manifest
            and exact_manifest == append_intent.next_head_manifest
            and entries[-1] == append_intent.next_entry
        ):
            next_entries = entries
        elif (
            manifest is None
            and previous_manifest is None
            and entries == [append_intent.next_entry]
        ):
            next_entries = entries
        else:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH"
            )
        self._assert_terminal_capacity(next_entries)
        if (
            self._build_head_manifest(next_entries) != append_intent.next_head_manifest
            or self._ledger_content_hash(next_entries)
            != append_intent.ledger_content_hash_ref
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH"
            )
        if entries != next_entries:
            _atomic_write(self.path, self._ledger_content(next_entries))
        self._write_head_manifest(append_intent.next_head_manifest)
        self._delete_append_intent()
        return [entry.model_copy(deep=True) for entry in next_entries]

    @contextmanager
    def consistent_read(self) -> Iterator[None]:
        with _nonmutating_goal_runtime_read_lock(
            self.state_dir / ".locks",
            "goal-approvals",
            generation_paths=(
                self.path,
                self.head_path,
                self.append_intent_path,
            ),
        ):
            yield

    def _load_consistent_entries(self) -> list[GoalMutationApprovalLedgerEntry]:
        for _attempt in range(3):
            try:
                with self.consistent_read():
                    return self._load_entries()
            except _GoalRuntimeGenerationChanged:
                continue
        raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_GENERATION_UNSTABLE")

    def repair_recoverable_append(self) -> None:
        """Finish only an exactly precommitted approval append, if present."""

        try:
            intent_metadata = os.lstat(self.append_intent_path)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise GoalRuntimeError(
                "GOAL_RUNTIME_STORAGE_UNAVAILABLE"
            ) from exc
        if not stat.S_ISREG(intent_metadata.st_mode):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_CORRUPT"
            )
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            self._load_entries(repair_manifest=True)

    def _append(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        *,
        spec: GoalMutationApprovalRequestSpec,
        status: GoalMutationApprovalDecisionStatus,
        approval_grant: ApprovalGrant | None = None,
        decision_reason_ref: str | None = None,
        decision_actor_ref: str | None = None,
        decided_at: datetime | None = None,
    ) -> GoalMutationApprovalLedgerEntry:
        entry = self._build_entry(
            entries,
            spec=spec,
            status=status,
            approval_grant=approval_grant,
            decision_reason_ref=decision_reason_ref,
            decision_actor_ref=decision_actor_ref,
            decided_at=decided_at,
        )
        next_entries = [*entries, entry]
        self._assert_terminal_capacity(next_entries)
        self._write_entries(next_entries)
        return entry.model_copy(deep=True)

    @classmethod
    def _build_entry(
        cls,
        entries: list[GoalMutationApprovalLedgerEntry],
        *,
        spec: GoalMutationApprovalRequestSpec,
        status: GoalMutationApprovalDecisionStatus,
        approval_grant: ApprovalGrant | None = None,
        decision_reason_ref: str | None = None,
        decision_actor_ref: str | None = None,
        decided_at: datetime | None = None,
    ) -> GoalMutationApprovalLedgerEntry:
        draft = GoalMutationApprovalLedgerEntry(
            spec=spec,
            status=status,
            approval_grant=approval_grant,
            decision_reason_ref=decision_reason_ref,
            decision_actor_ref=decision_actor_ref,
            decided_at=decided_at,
            previous_entry_hash_ref=(entries[-1].entry_hash_ref if entries else None),
            entry_hash_ref="entry-hash-ref:pending",
        )
        return draft.model_copy(update={"entry_hash_ref": cls._entry_hash(draft)})

    @staticmethod
    def _ledger_content(
        entries: Iterable[GoalMutationApprovalLedgerEntry],
    ) -> str:
        return "".join(entry.model_dump_json() + "\n" for entry in entries)

    @classmethod
    def _ledger_content_hash(
        cls,
        entries: list[GoalMutationApprovalLedgerEntry],
    ) -> str:
        return _sha256_ref(
            "ledger-content-hash-ref:goal-mutation-approvals",
            cls._ledger_content(entries),
        )

    @staticmethod
    def _build_head_manifest(
        entries: list[GoalMutationApprovalLedgerEntry],
    ) -> GoalMutationApprovalHeadManifest:
        if not entries:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_EMPTY"
            )
        latest: dict[str, GoalMutationApprovalLedgerEntry] = {}
        for entry in entries:
            latest[entry.spec.approval_request_ref] = entry
        return GoalMutationApprovalHeadManifest(
            entry_count=len(entries),
            head_entry_hash_ref=entries[-1].entry_hash_ref,
            request_state_set_hash_ref=_sha256_ref(
                "request-state-set-hash-ref:goal-mutation-approvals",
                sorted(
                    (
                        request_ref,
                        entry.status,
                        entry.entry_hash_ref,
                    )
                    for request_ref, entry in latest.items()
                ),
            ),
        )

    def _load_head_manifest(
        self,
    ) -> GoalMutationApprovalHeadManifest | None:
        raw_content = _read_bounded_regular_utf8(
            self.head_path,
            max_bytes=MAX_GOAL_MUTATION_APPROVAL_HEAD_BYTES,
            missing_ok=True,
            capacity_error="GOAL_MUTATION_APPROVAL_HEAD_CAPACITY_EXCEEDED",
            corruption_error="GOAL_MUTATION_APPROVAL_HEAD_CORRUPT",
        )
        if raw_content is None:
            return None
        try:
            if not raw_content.strip():
                raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_HEAD_EMPTY")
            return GoalMutationApprovalHeadManifest.model_validate_json(raw_content)
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_HEAD_CORRUPT"
            ) from exc

    def _load_append_intent(
        self,
    ) -> GoalMutationApprovalAppendIntent | None:
        raw_content = _read_bounded_regular_utf8(
            self.append_intent_path,
            max_bytes=MAX_GOAL_MUTATION_APPROVAL_APPEND_INTENT_BYTES,
            missing_ok=True,
            capacity_error=("GOAL_MUTATION_APPROVAL_APPEND_INTENT_CAPACITY_EXCEEDED"),
            corruption_error="GOAL_MUTATION_APPROVAL_APPEND_INTENT_CORRUPT",
        )
        if raw_content is None:
            return None
        try:
            if not raw_content.strip():
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_APPEND_INTENT_EMPTY"
                )
            intent = GoalMutationApprovalAppendIntent.model_validate_json(raw_content)
            if intent.next_entry.entry_hash_ref != self._entry_hash(intent.next_entry):
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_APPEND_INTENT_MISMATCH"
                )
            return intent
        except GoalRuntimeCorruptionError:
            raise
        except (OSError, UnicodeError, ValueError) as exc:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_CORRUPT"
            ) from exc

    def _write_head_manifest(
        self,
        manifest: GoalMutationApprovalHeadManifest,
    ) -> None:
        content = manifest.model_dump_json() + "\n"
        if len(content.encode("utf-8")) > MAX_GOAL_MUTATION_APPROVAL_HEAD_BYTES:
            raise GoalRuntimeError("GOAL_MUTATION_APPROVAL_HEAD_CAPACITY_EXCEEDED")
        _atomic_write(self.head_path, content)

    def _write_append_intent(
        self,
        intent: GoalMutationApprovalAppendIntent,
    ) -> None:
        content = intent.model_dump_json() + "\n"
        if (
            len(content.encode("utf-8"))
            > MAX_GOAL_MUTATION_APPROVAL_APPEND_INTENT_BYTES
        ):
            raise GoalRuntimeError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_CAPACITY_EXCEEDED"
            )
        _atomic_write(self.append_intent_path, content)

    def _delete_append_intent(self) -> None:
        try:
            self.append_intent_path.unlink(missing_ok=True)
        except OSError as exc:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc

    def _install_append_intent(
        self,
        intent: GoalMutationApprovalAppendIntent,
    ) -> None:
        if intent.previous_head_manifest is not None:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH"
            )
        entries = [intent.next_entry]
        if (
            self._build_head_manifest(entries) != intent.next_head_manifest
            or self._ledger_content_hash(entries) != intent.ledger_content_hash_ref
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH"
            )
        _atomic_write(self.path, self._ledger_content(entries))
        self._write_head_manifest(intent.next_head_manifest)
        self._delete_append_intent()

    def _write_entries(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
    ) -> None:
        content = self._ledger_content(entries)
        if (
            len(entries) > MAX_GOAL_MUTATION_APPROVAL_ENTRIES
            or len(content.encode("utf-8")) > MAX_GOAL_MUTATION_APPROVAL_LEDGER_BYTES
        ):
            raise GoalRuntimeError("GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED")
        if not entries:
            raise GoalRuntimeCorruptionError("GOAL_MUTATION_APPROVAL_LEDGER_EMPTY")
        previous_entries = entries[:-1]
        previous_manifest = (
            self._build_head_manifest(previous_entries) if previous_entries else None
        )
        intent = GoalMutationApprovalAppendIntent(
            previous_head_manifest=previous_manifest,
            next_entry=entries[-1],
            next_head_manifest=self._build_head_manifest(entries),
            ledger_content_hash_ref=self._ledger_content_hash(entries),
        )
        self._write_append_intent(intent)
        _atomic_write(self.path, content)
        self._write_head_manifest(intent.next_head_manifest)
        self._delete_append_intent()

    @classmethod
    def _maximum_revocation_entry(
        cls,
        approved: GoalMutationApprovalLedgerEntry,
        *,
        previous_entry_hash_ref: str,
        index: int,
    ) -> GoalMutationApprovalLedgerEntry:
        if approved.status != "approved" or approved.approval_grant is None:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID"
            )
        decision_reason_ref = _maximum_typed_ref(
            "reason-ref:goal-approval-revocation",
            index,
        )
        decision_actor_ref = approved.approval_grant.approved_by_actor_id
        decided_at = datetime.max.replace(tzinfo=utc_now().tzinfo)
        revoked_grant = ApprovalGrant.model_validate(
            {
                **approved.approval_grant.model_dump(mode="python"),
                "status": "revoked",
                "revoked_at": decided_at,
                "metadata": {
                    **approved.approval_grant.metadata,
                    "revocation_reason_ref": decision_reason_ref,
                },
            }
        )
        draft = GoalMutationApprovalLedgerEntry(
            spec=approved.spec,
            status="revoked",
            approval_grant=revoked_grant,
            decision_reason_ref=decision_reason_ref,
            decision_actor_ref=decision_actor_ref,
            decided_at=decided_at,
            previous_entry_hash_ref=previous_entry_hash_ref,
            entry_hash_ref="entry-hash-ref:pending",
        )
        return draft.model_copy(update={"entry_hash_ref": cls._entry_hash(draft)})

    @classmethod
    def _maximum_approval_entry(
        cls,
        pending: GoalMutationApprovalLedgerEntry,
        *,
        previous_entry_hash_ref: str,
        index: int,
    ) -> GoalMutationApprovalLedgerEntry:
        if pending.status != "pending":
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID"
            )
        decision_actor_ref = _maximum_typed_ref(
            "operator-ref:goal-approval-decision",
            index,
        )
        decision_reason_ref = _maximum_typed_ref(
            "reason-ref:goal-approval-decision",
            index,
        )
        decided_at = pending.spec.requested_at
        authority = LocalApprovalAuthority()
        approval_request = authority.create_request(
            build_exact_goal_mutation_approval_request(pending.spec)
        )
        raw_grant = authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id=decision_actor_ref,
            expires_at=pending.spec.expires_at,
            approval_ref=pending.spec.approval_ref,
        )
        grant = ApprovalGrant.model_validate(
            {
                **raw_grant.model_dump(mode="python"),
                "created_at": decided_at,
            }
        )
        draft = GoalMutationApprovalLedgerEntry(
            spec=pending.spec,
            status="approved",
            approval_grant=grant,
            decision_reason_ref=decision_reason_ref,
            decision_actor_ref=decision_actor_ref,
            decided_at=decided_at,
            previous_entry_hash_ref=previous_entry_hash_ref,
            entry_hash_ref="entry-hash-ref:pending",
        )
        return draft.model_copy(update={"entry_hash_ref": cls._entry_hash(draft)})

    @classmethod
    def _assert_terminal_capacity(
        cls,
        entries: list[GoalMutationApprovalLedgerEntry],
    ) -> None:
        latest: dict[str, GoalMutationApprovalLedgerEntry] = {}
        for entry in entries:
            latest[entry.spec.approval_request_ref] = entry
        projected = list(entries)
        for index, current in enumerate(latest.values()):
            approved = current
            if current.status == "pending":
                approved = cls._maximum_approval_entry(
                    current,
                    previous_entry_hash_ref=projected[-1].entry_hash_ref,
                    index=index,
                )
                projected.append(approved)
            if approved.status != "approved":
                continue
            projected.append(
                cls._maximum_revocation_entry(
                    approved,
                    previous_entry_hash_ref=projected[-1].entry_hash_ref,
                    index=index,
                )
            )
        if (
            len(projected) > MAX_GOAL_MUTATION_APPROVAL_ENTRIES
            or len(cls._ledger_content(projected).encode("utf-8"))
            > MAX_GOAL_MUTATION_APPROVAL_LEDGER_BYTES
        ):
            raise GoalRuntimeError("GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED")

    @staticmethod
    def _latest(
        entries: list[GoalMutationApprovalLedgerEntry],
        *,
        approval_request_ref: str | None = None,
        approval_ref: str | None = None,
    ) -> GoalMutationApprovalLedgerEntry | None:
        matches = [
            entry
            for entry in entries
            if (
                approval_request_ref is not None
                and entry.spec.approval_request_ref == approval_request_ref
            )
            or (approval_ref is not None and entry.spec.approval_ref == approval_ref)
        ]
        return matches[-1].model_copy(deep=True) if matches else None

    @staticmethod
    def _binding_from_approved_entry(
        entry: GoalMutationApprovalLedgerEntry,
    ) -> GoalMutationApprovalBinding:
        if entry.status != "approved" or entry.approval_grant is None:
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID")
        if entry.decided_at is None:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID"
            )
        approval_request = build_exact_goal_mutation_approval_request(entry.spec)
        grant = entry.approval_grant
        expected_grant = ApprovalGrant(
            approval_ref=entry.spec.approval_ref,
            approval_request_id=approval_request.approval_request_id,
            run_id=approval_request.run_id,
            subject_type=approval_request.subject_type,
            subject_id=approval_request.subject_id,
            granted_to_actor_id=approval_request.actor_context.actor_id,
            approved_by_actor_id=entry.decision_actor_ref,
            approved_actions=[approval_request.requested_action],
            approved_resource_refs=approval_request.resource_refs,
            risk_level=approval_request.risk_level,
            data_classification=approval_request.data_classification,
            purpose=approval_request.purpose,
            status="granted",
            created_at=entry.decided_at,
            expires_at=approval_request.expires_at,
            event_ref=approval_request.event_ref,
            trace_id=approval_request.trace_id,
            metadata={"approval_mode": "local_dev"},
        )
        if grant.model_dump(mode="json") != expected_grant.model_dump(mode="json"):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID"
            )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        authority.load_grant_for_validation(grant)
        decision = authority.validate_at_trusted_time(
            approval_request.to_validation_request(entry.spec.approval_ref),
            current_time=entry.decided_at,
        )
        if not decision.allowed:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID"
            )
        return GoalMutationApprovalBinding(
            approval_ref=entry.spec.approval_ref,
            approval_request_ref=entry.spec.approval_request_ref,
            approval_decision_ref=_sha256_ref(
                "approval-decision-ref:goal-mutation",
                {
                    "approval_ref": entry.spec.approval_ref,
                    "ledger_entry_hash_ref": entry.entry_hash_ref,
                    "status": entry.status,
                },
            ),
            approval_ledger_entry_hash_ref=entry.entry_hash_ref,
            exact_scope_ref=entry.spec.exact_scope_ref,
            request_fingerprint_ref=entry.spec.request_fingerprint_ref,
        )

    def _validated_committed_goal_binding(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        journal_entry: GoalJournalEntry,
        *,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
    ) -> GoalMutationApprovalBinding:
        ledger_hash_ref = journal_entry.approval_ledger_entry_hash_ref
        if ledger_hash_ref is None:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_MISSING"
            )
        approval_entry = next(
            (entry for entry in entries if entry.entry_hash_ref == ledger_hash_ref),
            None,
        )
        if approval_entry is None:
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_MISSING"
            )
        binding = self._binding_from_approved_entry(approval_entry)
        _validate_goal_mutation_approval_binding(
            binding,
            operation=operation,
            subject_ref=subject_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
        )
        if (
            journal_entry.approval_ref != binding.approval_ref
            or journal_entry.approval_decision_ref != binding.approval_decision_ref
            or approval_entry.spec.mutation_request_fingerprint_ref
            != journal_entry.request_fingerprint_ref
        ):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_PROVENANCE_MISMATCH"
            )
        return binding

    def _validated_committed_event_binding(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        event: DurableRunEvent,
        *,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
    ) -> GoalMutationApprovalBinding:
        ledger_hash_ref = event.goal_mutation_approval_ledger_entry_hash_ref
        if (
            event.goal_mutation_approval_ref is None
            or event.goal_mutation_approval_decision_ref is None
            or ledger_hash_ref is None
        ):
            raise GoalRuntimeCorruptionError("RUN_EVENT_APPROVAL_PROVENANCE_MISSING")
        approval_entry = next(
            (entry for entry in entries if entry.entry_hash_ref == ledger_hash_ref),
            None,
        )
        if approval_entry is None:
            raise GoalRuntimeCorruptionError("RUN_EVENT_APPROVAL_PROVENANCE_MISSING")
        binding = self._binding_from_approved_entry(approval_entry)
        _validate_goal_mutation_approval_binding(
            binding,
            operation=operation,
            subject_ref=subject_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
        )
        if (
            event.goal_mutation_approval_ref != binding.approval_ref
            or event.goal_mutation_approval_decision_ref
            != binding.approval_decision_ref
            or approval_entry.spec.mutation_request_fingerprint_ref
            != _mutation_request_fingerprint_ref(
                operation=operation,
                subject_ref=subject_ref,
                request_payload=request_payload,
            )
        ):
            raise GoalRuntimeCorruptionError("RUN_EVENT_APPROVAL_PROVENANCE_MISMATCH")
        return binding

    def validate_goal_provenance(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        journal_entries: Iterable[GoalJournalEntry],
    ) -> None:
        """Validate every committed goal against its exact approval decision."""

        by_hash = {entry.entry_hash_ref: entry for entry in entries}
        for journal_entry in journal_entries:
            ledger_hash_ref = journal_entry.approval_ledger_entry_hash_ref
            if ledger_hash_ref is None:
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_PROVENANCE_MISSING"
                )
            approval_entry = by_hash.get(ledger_hash_ref)
            if approval_entry is None:
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_PROVENANCE_MISSING"
                )
            binding = self._binding_from_approved_entry(approval_entry)
            expected_operation = {
                GoalJournalOperation.create.value: "create",
                GoalJournalOperation.edit.value: "edit",
            }.get(journal_entry.operation)
            operation_matches = (
                approval_entry.spec.operation == expected_operation
                if expected_operation is not None
                else approval_entry.spec.operation.startswith("transition-")
            )
            expected_subject = (
                "goal-ref:new"
                if journal_entry.operation == GoalJournalOperation.create.value
                else journal_entry.goal_ref
            )
            if (
                not operation_matches
                or approval_entry.spec.subject_ref != expected_subject
                or approval_entry.spec.idempotency_ref != journal_entry.idempotency_ref
                or approval_entry.spec.mutation_request_fingerprint_ref
                != journal_entry.request_fingerprint_ref
                or journal_entry.approval_request_fingerprint_ref
                != approval_entry.spec.request_fingerprint_ref
                or journal_entry.approval_exact_scope_ref
                != approval_entry.spec.exact_scope_ref
                or journal_entry.approval_ref != binding.approval_ref
                or journal_entry.approval_decision_ref != binding.approval_decision_ref
            ):
                raise GoalRuntimeCorruptionError(
                    "GOAL_MUTATION_APPROVAL_PROVENANCE_MISMATCH"
                )

    def validate_event_provenance(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        events: Iterable[DurableRunEvent],
    ) -> None:
        """Validate the durable producer class and exact public approval proof."""

        seen: set[str] = set()
        for event in events:
            if event.event_ref in seen:
                continue
            seen.add(event.event_ref)
            request_payload = _DurableRunEventStore._event_request_payload(event)
            scoped_approval_entries = [
                entry
                for entry in entries
                if entry.status == "approved"
                and entry.spec.operation == "append-run-event"
                and entry.spec.subject_ref == event.run_ref
                and entry.spec.idempotency_ref == event.idempotency_ref
            ]
            if event.schema_version == "durable_run_event.v1":
                # Public metadata append did not exist in the v1 event epoch.
                # The model rejects producer/approval fields on this legacy
                # schema, so it remains a bounded trusted-Core compatibility
                # record rather than an authority-bearing public event.
                if scoped_approval_entries:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_PRODUCER_CLASS_SUBSTITUTION"
                    )
                continue
            if event.producer_class == "trusted_core":
                if scoped_approval_entries:
                    raise GoalRuntimeCorruptionError(
                        "RUN_EVENT_PRODUCER_CLASS_SUBSTITUTION"
                    )
                continue
            if event.producer_class != "operator_public_metadata":
                raise GoalRuntimeCorruptionError("RUN_EVENT_PRODUCER_CLASS_INVALID")
            if event.event_kind in {
                DurableRunEventKind.receipt_recorded.value,
                *TERMINAL_RUN_EVENT_KINDS,
            }:
                raise GoalRuntimeCorruptionError(
                    "RUN_EVENT_PUBLIC_PRODUCER_KIND_INVALID"
                )
            self._validated_committed_event_binding(
                entries,
                event,
                operation="append-run-event",
                subject_ref=event.run_ref,
                request_payload=request_payload,
                idempotency_ref=event.idempotency_ref,
            )

    def _validated_current_binding(
        self,
        entries: list[GoalMutationApprovalLedgerEntry],
        *,
        approval_ref: str,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
    ) -> GoalMutationApprovalBinding:
        current = self._latest(entries, approval_ref=approval_ref)
        if current is None:
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_UNKNOWN")
        expected_fingerprint = _goal_mutation_approval_request_fingerprint_ref(
            operation=operation,
            subject_ref=subject_ref,
            request_payload=request_payload,
            idempotency_ref=idempotency_ref,
        )
        if (
            current.spec.operation != operation
            or current.spec.subject_ref != subject_ref
            or current.spec.idempotency_ref != idempotency_ref
            or current.spec.request_fingerprint_ref != expected_fingerprint
        ):
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH")
        if current.status == "denied":
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_DENIED")
        if current.status == "revoked":
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_REVOKED")
        if current.status == "expired":
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_EXPIRED")
        if current.status != "approved" or current.approval_grant is None:
            raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_REQUIRED")
        approval_request = build_exact_goal_mutation_approval_request(current.spec)
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        authority.load_grant_for_validation(current.approval_grant)
        decision = authority.validate_at_trusted_time(
            approval_request.to_validation_request(approval_ref),
            current_time=utc_now(),
        )
        if not decision.allowed:
            code = (
                "GOAL_MUTATION_APPROVAL_EXPIRED"
                if "APPROVAL_EXPIRED" in decision.reason_codes
                else "GOAL_MUTATION_APPROVAL_DENIED"
            )
            raise GoalTransitionDeniedError(code)
        return self._binding_from_approved_entry(current)

    @contextmanager
    def validated_goal_mutation(
        self,
        *,
        approval_ref: str,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
        committed_lookup: Any,
    ) -> Iterator[tuple[GoalMutationApprovalBinding, GoalJournalEntry | None]]:
        """Replay committed truth or hold approval truth through a new commit."""

        validate_execution_ref(approval_ref, "approval_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            committed_entry = committed_lookup()
            if committed_entry is not None:
                binding = self._validated_committed_goal_binding(
                    entries,
                    committed_entry,
                    operation=operation,
                    subject_ref=subject_ref,
                    request_payload=request_payload,
                    idempotency_ref=idempotency_ref,
                )
                if approval_ref != binding.approval_ref:
                    raise GoalTransitionDeniedError(
                        "GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH"
                    )
                yield binding, committed_entry
                return
            binding = self._validated_current_binding(
                entries,
                approval_ref=approval_ref,
                operation=operation,
                subject_ref=subject_ref,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
            )
            yield binding, None

    @contextmanager
    def validated_event_mutation(
        self,
        *,
        approval_ref: str,
        request: DurableRunEventAppendRequest,
        committed_lookup: Any,
    ) -> Iterator[tuple[GoalMutationApprovalBinding, DurableRunEvent | None]]:
        """Replay an approved append or hold approval truth for a new event."""

        validate_execution_ref(approval_ref, "approval_ref")
        request_payload = request.model_dump(mode="json")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            committed_event = committed_lookup()
            if committed_event is not None:
                binding = self._validated_committed_event_binding(
                    entries,
                    committed_event,
                    operation="append-run-event",
                    subject_ref=request.run_ref,
                    request_payload=request_payload,
                    idempotency_ref=request.idempotency_ref,
                )
                if approval_ref != binding.approval_ref:
                    raise GoalTransitionDeniedError(
                        "GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH"
                    )
                yield binding, committed_event
                return
            binding = self._validated_current_binding(
                entries,
                approval_ref=approval_ref,
                operation="append-run-event",
                subject_ref=request.run_ref,
                request_payload=request_payload,
                idempotency_ref=request.idempotency_ref,
            )
            yield binding, None

    def prepare(
        self,
        *,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
        ttl_minutes: int = 30,
    ) -> GoalMutationApprovalRequestSpec:
        if ttl_minutes < 5 or ttl_minutes > 60:
            raise ValueError("GOAL_MUTATION_APPROVAL_TTL_INVALID")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            now = utc_now()
            provisional = build_exact_goal_mutation_approval_request_spec(
                operation=operation,
                subject_ref=subject_ref,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
                requested_at=now,
                expires_at=now + timedelta(minutes=ttl_minutes),
            )
            existing = self._latest(
                entries,
                approval_request_ref=provisional.approval_request_ref,
            )
            if existing is not None:
                expected_fingerprint = _goal_mutation_approval_request_fingerprint_ref(
                    operation=operation,
                    subject_ref=subject_ref,
                    request_payload=request_payload,
                    idempotency_ref=idempotency_ref,
                )
                if (
                    existing.spec.operation != operation
                    or existing.spec.subject_ref != subject_ref
                    or existing.spec.idempotency_ref != idempotency_ref
                    or existing.spec.request_fingerprint_ref != expected_fingerprint
                ):
                    raise GoalIdempotencyConflictError(
                        "GOAL_MUTATION_APPROVAL_REQUEST_CONFLICT"
                    )
                return existing.spec.model_copy(deep=True)
            return self._append(
                entries,
                spec=provisional,
                status="pending",
            ).spec

    def decide(
        self,
        *,
        approval_request_ref: str,
        decision: Literal["approve", "deny"],
        decision_reason_ref: str,
        actor_ref: str = "operator-ref:local-user",
        before_terminal_append: (
            Callable[[GoalMutationApprovalRequestSpec, str], None] | None
        ) = None,
    ) -> GoalMutationApprovalLedgerEntry:
        validate_execution_ref(approval_request_ref, "approval_request_ref")
        validate_execution_ref(decision_reason_ref, "decision_reason_ref")
        validate_execution_ref(actor_ref, "actor_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            current = self._latest(
                entries,
                approval_request_ref=approval_request_ref,
            )
            if current is None:
                raise GoalNotFoundError("GOAL_MUTATION_APPROVAL_REQUEST_NOT_FOUND")
            if current.status != "pending":
                if (
                    current.status
                    == ("approved" if decision == "approve" else "denied")
                    and current.decision_reason_ref == decision_reason_ref
                    and current.decision_actor_ref == actor_ref
                ):
                    if (
                        current.status == "denied"
                        and before_terminal_append is not None
                    ):
                        before_terminal_append(
                            current.spec,
                            decision_reason_ref,
                        )
                    return current
                raise GoalIdempotencyConflictError(
                    "GOAL_MUTATION_APPROVAL_DECISION_CONFLICT"
                )
            decided_at = utc_now()
            if decided_at >= current.spec.expires_at:
                raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_EXPIRED")
            if decision == "deny":
                draft = self._build_entry(
                    entries,
                    spec=current.spec,
                    status="denied",
                    decision_reason_ref=decision_reason_ref,
                    decision_actor_ref=actor_ref,
                    decided_at=decided_at,
                )
                self._assert_terminal_capacity([*entries, draft])
                if before_terminal_append is not None:
                    before_terminal_append(
                        current.spec,
                        decision_reason_ref,
                    )
                return self._append(
                    entries,
                    spec=current.spec,
                    status="denied",
                    decision_reason_ref=decision_reason_ref,
                    decision_actor_ref=actor_ref,
                    decided_at=decided_at,
                )
            authority = LocalApprovalAuthority()
            approval_request = authority.create_request(
                build_exact_goal_mutation_approval_request(current.spec)
            )
            raw_grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id=actor_ref,
                expires_at=current.spec.expires_at,
                approval_ref=current.spec.approval_ref,
            )
            grant = ApprovalGrant.model_validate(
                {
                    **raw_grant.model_dump(mode="python"),
                    "created_at": decided_at,
                }
            )
            return self._append(
                entries,
                spec=current.spec,
                status="approved",
                approval_grant=grant,
                decision_reason_ref=decision_reason_ref,
                decision_actor_ref=actor_ref,
                decided_at=decided_at,
            )

    def expire_pending(
        self,
        *,
        before_terminal_append: Callable[
            [GoalMutationApprovalRequestSpec, str],
            None,
        ],
    ) -> int:
        """Durably reject each exact linked submission whose request expired."""

        reason_ref = "reason-ref:goal-mutation-rejected:approval-expired"
        actor_ref = "operator-ref:goal-runtime-expiration-recovery"
        try:
            ledger_metadata = os.lstat(self.path)
        except FileNotFoundError:
            return 0
        except OSError as exc:
            raise GoalRuntimeError(
                "GOAL_RUNTIME_STORAGE_UNAVAILABLE"
            ) from exc
        if not stat.S_ISREG(ledger_metadata.st_mode):
            raise GoalRuntimeCorruptionError(
                "GOAL_MUTATION_APPROVAL_LEDGER_CORRUPT"
            )
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            latest: dict[str, GoalMutationApprovalLedgerEntry] = {}
            for entry in entries:
                latest[entry.spec.approval_request_ref] = entry
            now = utc_now()
            expired = [
                entry
                for entry in latest.values()
                if entry.status in {"pending", "approved"}
                and now >= entry.spec.expires_at
            ]
            for current in expired:
                before_terminal_append(current.spec, reason_ref)
                appended = self._append(
                    entries,
                    spec=current.spec,
                    status="expired",
                    decision_reason_ref=reason_ref,
                    decision_actor_ref=actor_ref,
                    decided_at=now,
                )
                entries = [*entries, appended]
            return len(expired)

    def revoke(
        self,
        *,
        approval_ref: str,
        decision_reason_ref: str,
        actor_ref: str = "operator-ref:local-user",
        before_terminal_append: (
            Callable[[GoalMutationApprovalRequestSpec, str], None] | None
        ) = None,
    ) -> GoalMutationApprovalLedgerEntry:
        validate_execution_ref(approval_ref, "approval_ref")
        validate_execution_ref(decision_reason_ref, "decision_reason_ref")
        validate_execution_ref(actor_ref, "actor_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            current = self._latest(entries, approval_ref=approval_ref)
            if current is None:
                raise GoalNotFoundError("GOAL_MUTATION_APPROVAL_REQUEST_NOT_FOUND")
            if current.status == "revoked":
                if (
                    current.decision_reason_ref == decision_reason_ref
                    and current.decision_actor_ref == actor_ref
                ):
                    if before_terminal_append is not None:
                        before_terminal_append(
                            current.spec,
                            decision_reason_ref,
                        )
                    return current
                raise GoalIdempotencyConflictError(
                    "GOAL_MUTATION_APPROVAL_REVOCATION_CONFLICT"
                )
            if current.status != "approved" or current.approval_grant is None:
                raise GoalTransitionDeniedError("GOAL_MUTATION_APPROVAL_NOT_REVOCABLE")
            revoked_at = utc_now()
            authority = LocalApprovalAuthority()
            authority.load_grant_for_validation(current.approval_grant)
            grant = authority.apply_revocation_tombstone(
                approval_ref,
                reason_ref=decision_reason_ref,
                revoked_at=revoked_at,
            )
            draft = self._build_entry(
                entries,
                spec=current.spec,
                status="revoked",
                approval_grant=grant,
                decision_reason_ref=decision_reason_ref,
                decision_actor_ref=actor_ref,
                decided_at=revoked_at,
            )
            self._assert_terminal_capacity([*entries, draft])
            if before_terminal_append is not None:
                before_terminal_append(
                    current.spec,
                    decision_reason_ref,
                )
            return self._append(
                entries,
                spec=current.spec,
                status="revoked",
                approval_grant=grant,
                decision_reason_ref=decision_reason_ref,
                decision_actor_ref=actor_ref,
                decided_at=revoked_at,
            )

    @contextmanager
    def validated_mutation(
        self,
        *,
        approval_ref: str,
        operation: str,
        subject_ref: str,
        request_payload: dict[str, Any],
        idempotency_ref: str,
    ) -> Iterator[GoalMutationApprovalBinding]:
        """Hold approval truth stable across the exact journal mutation claim."""

        validate_execution_ref(approval_ref, "approval_ref")
        _initialize_goal_runtime_state_dir(self.state_dir)
        with _normalized_goal_runtime_lock(self._locks, "goal-approvals"):
            entries = self._load_entries(repair_manifest=True)
            yield self._validated_current_binding(
                entries,
                approval_ref=approval_ref,
                operation=operation,
                subject_ref=subject_ref,
                request_payload=request_payload,
                idempotency_ref=idempotency_ref,
            )


def _initialize_goal_runtime_state_dir(state_dir: Path) -> None:
    try:
        identity = _goal_runtime_state_dir_chain_identity(state_dir, create=True)
        if identity is None:
            raise OSError("goal runtime state directory was not created")
        _bind_goal_runtime_state_dir_identity(state_dir, identity)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc


def _validate_goal_runtime_state_dir_for_read(state_dir: Path) -> None:
    try:
        identity = _goal_runtime_state_dir_chain_identity(state_dir, create=False)
        _bind_goal_runtime_state_dir_identity(state_dir, identity)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc


_GOAL_RUNTIME_STATE_DIR_IDENTITIES: dict[str, tuple[int, int]] = {}
_GOAL_RUNTIME_STATE_DIR_IDENTITIES_LOCK = threading.RLock()


def _goal_runtime_state_dir_key(state_dir: Path) -> str:
    return os.path.abspath(os.fspath(state_dir))


def _goal_runtime_state_dir_chain_identity(
    state_dir: Path,
    *,
    create: bool,
) -> tuple[int, int] | None:
    """Open every state-root component without following ancestor links."""

    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("goal runtime state directory guard unavailable")
    absolute = Path(_goal_runtime_state_dir_key(state_dir))
    if absolute == Path(absolute.anchor):
        raise OSError("goal runtime state directory cannot be a filesystem root")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise OSError("goal runtime state directory component is invalid")
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
            raise OSError("goal runtime state directory identity mismatch")
        if create:
            os.fchmod(descriptor, 0o700)
        return identity
    finally:
        os.close(descriptor)


def _bind_goal_runtime_state_dir_identity(
    state_dir: Path,
    identity: tuple[int, int] | None,
) -> None:
    key = _goal_runtime_state_dir_key(state_dir)
    with _GOAL_RUNTIME_STATE_DIR_IDENTITIES_LOCK:
        expected = _GOAL_RUNTIME_STATE_DIR_IDENTITIES.get(key)
        if identity is None:
            if expected is not None:
                raise OSError("goal runtime state directory disappeared")
            return
        if expected is not None and expected != identity:
            raise OSError("goal runtime state directory identity changed")
        _GOAL_RUNTIME_STATE_DIR_IDENTITIES.setdefault(key, identity)


@contextmanager
def _normalized_goal_runtime_lock(
    manager: FileSingleWriterLockManager,
    writer_key: str,
) -> Iterator[None]:
    entered = False
    try:
        _validate_goal_runtime_state_dir_for_read(manager.lock_dir.parent)
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
    _validate_goal_runtime_state_dir_for_read(lock_dir.parent)
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

    _validate_goal_runtime_state_dir_for_read(path.parent)
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
    temporary_name: str | None = None
    directory_fd: int | None = None
    descriptor: int | None = None
    try:
        _initialize_goal_runtime_state_dir(path.parent)
        directory_fd = os.open(
            _goal_runtime_state_dir_key(path.parent),
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        opened_parent = os.fstat(directory_fd)
        _bind_goal_runtime_state_dir_identity(
            path.parent,
            (opened_parent.st_dev, opened_parent.st_ino),
        )
        temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(
            temporary_name,
            flags,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_name = None
        installed_fd = os.open(
            path.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory_fd,
        )
        try:
            os.fchmod(installed_fd, 0o600)
        finally:
            os.close(installed_fd)
        _validate_goal_runtime_state_dir_for_read(path.parent)
        os.fsync(directory_fd)
    except OSError as exc:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None and directory_fd is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            os.close(directory_fd)
