from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority.contracts import authority_state_lock_manager
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchFailureCategory,
    AuthorityDispatchReceipt,
    AuthorityDispatchStatus,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


MISSION_STEP_SCHEMA_VERSION = "uaa-mission-step.v1"
MISSION_STEP_LEDGER_FILE = "mission_step_receipts.jsonl"
MISSION_STEP_LOCK_KEY = "authority-mission-steps"
MISSION_PLAN_MATERIALIZATION_LOCK_KEY = "authority-mission-plan-materialization"
MISSION_STEP_LEDGER_MAX_BYTES = 8 * 1024 * 1024
MISSION_STEP_LEDGER_MAX_RECEIPTS = 10_000


class MissionStepError(RuntimeError):
    pass


class MissionStepConflictError(MissionStepError):
    pass


class MissionStepCorruptionError(MissionStepError):
    pass


class MissionStepStatus(str, Enum):
    pending = "pending"
    approval_wait = "approval_wait"
    retry_pending = "retry_pending"
    claimed = "claimed"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    recovery_required = "recovery_required"
    dependency_blocked = "dependency_blocked"
    fail_fast_halted = "fail_fast_halted"
    dead_lettered = "dead_lettered"


TERMINAL_MISSION_STEP_STATUSES = {
    MissionStepStatus.succeeded.value,
    MissionStepStatus.failed.value,
    MissionStepStatus.cancelled.value,
    MissionStepStatus.recovery_required.value,
    MissionStepStatus.dependency_blocked.value,
    MissionStepStatus.fail_fast_halted.value,
    MissionStepStatus.dead_lettered.value,
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))[:24]}"


class _MissionStepModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class MissionStepPlannedRetryAttempt(_MissionStepModel):
    attempt_no: StrictInt = Field(..., ge=2, le=3)
    dispatch_ref: str
    dispatch_request_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_attempt(self) -> "MissionStepPlannedRetryAttempt":
        validate_task_ref(self.dispatch_ref, "mission_step_retry_dispatch_ref")
        validate_task_ref(
            self.dispatch_request_fingerprint_ref,
            "mission_step_retry_dispatch_fingerprint_ref",
        )
        return self


class MissionStepDefinition(_MissionStepModel):
    schema_version: Literal["uaa-mission-step.v1"] = MISSION_STEP_SCHEMA_VERSION
    mission_ref: str
    run_ref: str
    step_ref: str
    capability_ref: str
    adapter_ref: str
    lease_ref: str
    dependency_step_refs: list[str] = Field(default_factory=list)
    orchestration_plan_ref: str | None = None
    planned_dispatch_ref: str | None = None
    planned_dispatch_request_fingerprint_ref: str | None = None
    max_attempts: StrictInt = Field(default=1, ge=1, le=3)
    retryable_failure_categories: list[AuthorityDispatchFailureCategory] = Field(
        default_factory=list,
        max_length=3,
    )
    retry_backoff_seconds: StrictInt = Field(default=0, ge=0, le=300)
    planned_retry_attempts: list[MissionStepPlannedRetryAttempt] = Field(
        default_factory=list,
        max_length=2,
    )
    deadline: datetime
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_definition(self) -> "MissionStepDefinition":
        for value, name in [
            (self.mission_ref, "mission_ref"),
            (self.run_ref, "run_ref"),
            (self.step_ref, "step_ref"),
            (self.capability_ref, "capability_ref"),
            (self.adapter_ref, "adapter_ref"),
            (self.lease_ref, "lease_ref"),
            *[(ref, "dependency_step_ref") for ref in self.dependency_step_refs],
        ]:
            validate_task_ref(value, name)
        for value, name in [
            (self.orchestration_plan_ref, "mission_step_orchestration_plan_ref"),
            (self.planned_dispatch_ref, "mission_step_planned_dispatch_ref"),
            (
                self.planned_dispatch_request_fingerprint_ref,
                "mission_step_planned_dispatch_request_fingerprint_ref",
            ),
        ]:
            if value is not None:
                validate_task_ref(value, name)
        if self.step_ref in self.dependency_step_refs:
            raise ValueError("MISSION_STEP_SELF_DEPENDENCY_DENIED")
        if len(self.dependency_step_refs) != len(set(self.dependency_step_refs)):
            raise ValueError("MISSION_STEP_DUPLICATE_DEPENDENCY_DENIED")
        planned_values = (
            self.orchestration_plan_ref,
            self.planned_dispatch_ref,
            self.planned_dispatch_request_fingerprint_ref,
        )
        if any(value is not None for value in planned_values) and not all(
            value is not None for value in planned_values
        ):
            raise ValueError("MISSION_STEP_PLANNED_DISPATCH_BINDING_INCOMPLETE")
        if self.deadline.tzinfo is None:
            raise ValueError("MISSION_STEP_DEADLINE_TIMEZONE_REQUIRED")
        if self.max_attempts == 1 and (
            self.retryable_failure_categories or self.planned_retry_attempts
        ):
            raise ValueError("MISSION_STEP_RETRY_POLICY_DISABLED")
        retry_attempt_numbers = [
            attempt.attempt_no for attempt in self.planned_retry_attempts
        ]
        if self.max_attempts > 1 and not self.retryable_failure_categories:
            raise ValueError("MISSION_STEP_RETRY_POLICY_BINDING_REQUIRED")
        if self.orchestration_plan_ref is None and self.planned_retry_attempts:
            raise ValueError("MISSION_STEP_UNBOUND_RETRY_ATTEMPT_FORBIDDEN")
        if self.orchestration_plan_ref is not None and self.max_attempts > 1 and (
            len(self.planned_retry_attempts) != self.max_attempts - 1
            or retry_attempt_numbers != list(range(2, self.max_attempts + 1))
        ):
            raise ValueError("MISSION_STEP_RETRY_ATTEMPT_BINDING_REQUIRED")
        if len(self.retryable_failure_categories) != len(
            set(self.retryable_failure_categories)
        ):
            raise ValueError("MISSION_STEP_DUPLICATE_RETRY_CATEGORY")
        validate_safe_task_text(self.safe_summary, "mission_step_safe_summary")
        return self

    @property
    def fingerprint_ref(self) -> str:
        return _safe_ref("mission-step-fingerprint-ref", _definition_payload(self))


def _definition_payload(definition: MissionStepDefinition) -> dict[str, Any]:
    payload = definition.model_dump(mode="json")
    if definition.max_attempts == 1:
        payload.pop("retryable_failure_categories", None)
        payload.pop("retry_backoff_seconds", None)
        payload.pop("planned_retry_attempts", None)
    elif not definition.planned_retry_attempts:
        payload.pop("planned_retry_attempts", None)
    if definition.orchestration_plan_ref is None:
        payload.pop("orchestration_plan_ref", None)
        payload.pop("planned_dispatch_ref", None)
        payload.pop("planned_dispatch_request_fingerprint_ref", None)
    return payload


class MissionStepReceipt(_MissionStepModel):
    schema_version: Literal["uaa-mission-step.v1"] = MISSION_STEP_SCHEMA_VERSION
    sequence: StrictInt = Field(..., ge=1)
    receipt_ref: str
    entry_hash_ref: str
    previous_entry_hash_ref: str | None = None
    definition: MissionStepDefinition
    definition_fingerprint_ref: str
    status: MissionStepStatus
    generation: StrictInt = Field(default=0, ge=0)
    attempt_no: StrictInt = Field(default=1, ge=1, le=3)
    owner_ref: str | None = None
    claim_ref: str | None = None
    claim_expires_at: datetime | None = None
    dispatch_ref: str | None = None
    dispatch_request_fingerprint_ref: str | None = None
    dispatch_receipt_ref: str | None = None
    dispatch_entry_hash_ref: str | None = None
    approval_request_ref: str | None = None
    approval_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    retry_not_before: datetime | None = None
    failure_category: AuthorityDispatchFailureCategory | None = None
    blocked_dependency_step_ref: str | None = None
    halted_by_step_ref: str | None = None
    reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utc_now)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_receipt(self) -> "MissionStepReceipt":
        for value, name in [
            (self.receipt_ref, "mission_step_receipt_ref"),
            (self.entry_hash_ref, "mission_step_entry_hash_ref"),
            (self.previous_entry_hash_ref, "mission_step_previous_hash_ref"),
            (self.definition_fingerprint_ref, "mission_step_fingerprint_ref"),
            (self.owner_ref, "mission_step_owner_ref"),
            (self.claim_ref, "mission_step_claim_ref"),
            (self.dispatch_ref, "mission_step_dispatch_ref"),
            (
                self.dispatch_request_fingerprint_ref,
                "mission_step_dispatch_request_fingerprint_ref",
            ),
            (self.dispatch_receipt_ref, "mission_step_dispatch_receipt_ref"),
            (self.dispatch_entry_hash_ref, "mission_step_dispatch_entry_hash_ref"),
            (self.approval_request_ref, "mission_step_approval_request_ref"),
            (self.approval_ref, "mission_step_approval_ref"),
            (
                self.approval_scope_fingerprint_ref,
                "mission_step_approval_scope_fingerprint_ref",
            ),
            (
                self.blocked_dependency_step_ref,
                "mission_step_blocked_dependency_ref",
            ),
            (self.halted_by_step_ref, "mission_step_halted_by_step_ref"),
            *[(ref, "mission_step_reason_ref") for ref in self.reason_refs],
            *[(ref, "mission_step_evidence_ref") for ref in self.evidence_refs],
        ]:
            if value is not None:
                validate_task_ref(value, name)
        validate_safe_task_text(self.safe_summary, "mission_step_safe_summary")
        claimed = self.status == MissionStepStatus.claimed.value
        if claimed != bool(self.owner_ref and self.claim_ref and self.claim_expires_at):
            raise ValueError("MISSION_STEP_CLAIM_POSTURE_INVALID")
        if self.status in TERMINAL_MISSION_STEP_STATUSES and not self.reason_refs:
            raise ValueError("MISSION_STEP_TERMINAL_REASON_REQUIRED")
        dependency_blocked = self.status == MissionStepStatus.dependency_blocked.value
        if dependency_blocked != (self.blocked_dependency_step_ref is not None):
            raise ValueError("MISSION_STEP_DEPENDENCY_BLOCK_BINDING_INVALID")
        fail_fast_halted = self.status == MissionStepStatus.fail_fast_halted.value
        if fail_fast_halted != (self.halted_by_step_ref is not None):
            raise ValueError("MISSION_STEP_FAIL_FAST_HALT_BINDING_INVALID")
        approval_refs = (
            self.approval_request_ref,
            self.approval_ref,
            self.approval_scope_fingerprint_ref,
        )
        if any(approval_refs) and not all(approval_refs):
            raise ValueError("MISSION_STEP_APPROVAL_BINDING_INCOMPLETE")
        if self.status == MissionStepStatus.approval_wait.value and not all(
            approval_refs
        ):
            raise ValueError("MISSION_STEP_APPROVAL_WAIT_BINDING_REQUIRED")
        retry_pending = self.status == MissionStepStatus.retry_pending.value
        if retry_pending != bool(
            self.retry_not_before is not None and self.failure_category is not None
        ):
            raise ValueError("MISSION_STEP_RETRY_PENDING_BINDING_INVALID")
        if self.retry_not_before is not None and self.retry_not_before.tzinfo is None:
            raise ValueError("MISSION_STEP_RETRY_TIMEZONE_REQUIRED")
        if self.attempt_no > self.definition.max_attempts:
            raise ValueError("MISSION_STEP_ATTEMPT_LIMIT_EXCEEDED")
        if self.definition_fingerprint_ref != self.definition.fingerprint_ref:
            raise ValueError("MISSION_STEP_DEFINITION_FINGERPRINT_INVALID")
        return self


class MissionStepReadModel(_MissionStepModel):
    step_ref: str
    status: MissionStepStatus
    generation: StrictInt
    attempt_no: StrictInt
    owner_ref: str | None
    claim_ref: str | None
    claim_expires_at: datetime | None
    dispatch_ref: str | None
    dispatch_request_fingerprint_ref: str | None
    dispatch_receipt_ref: str | None
    dispatch_entry_hash_ref: str | None
    approval_request_ref: str | None = None
    approval_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    retry_not_before: datetime | None = None
    failure_category: AuthorityDispatchFailureCategory | None = None
    blocked_dependency_step_ref: str | None = None
    halted_by_step_ref: str | None = None
    reason_refs: list[str]
    evidence_refs: list[str]
    receipt_ref: str
    execution_authority_granted: Literal[False] = False
    autonomous_retry_enabled: bool = False


class MissionStepOrchestrationContext(_MissionStepModel):
    plan_ref: str
    plan_fingerprint_ref: str
    plan_receipt_ref: str
    ordered_step_refs: list[str] = Field(..., min_length=1, max_length=16)

    @model_validator(mode="after")
    def validate_context(self) -> "MissionStepOrchestrationContext":
        for value, name in [
            (self.plan_ref, "mission_step_plan_ref"),
            (self.plan_fingerprint_ref, "mission_step_plan_fingerprint_ref"),
            (self.plan_receipt_ref, "mission_step_plan_receipt_ref"),
            *[(ref, "mission_step_plan_member_ref") for ref in self.ordered_step_refs],
        ]:
            validate_task_ref(value, name)
        if len(self.ordered_step_refs) != len(set(self.ordered_step_refs)):
            raise ValueError("MISSION_STEP_PLAN_CONTEXT_DUPLICATE_STEP")
        return self


class _MissionStepInspectionSource(_MissionStepModel):
    mission_ref: str
    run_ref: str
    step_ref: str
    capability_ref: str
    adapter_ref: str
    lease_ref: str
    dependency_step_refs: list[str]
    deadline: datetime
    status: MissionStepStatus
    generation: StrictInt
    attempt_no: StrictInt
    owner_ref: str | None
    claim_ref: str | None
    claim_expires_at: datetime | None
    dispatch_ref: str | None
    dispatch_request_fingerprint_ref: str | None
    dispatch_receipt_ref: str | None
    approval_request_ref: str | None
    approval_ref: str | None
    approval_scope_fingerprint_ref: str | None
    retry_not_before: datetime | None
    failure_category: AuthorityDispatchFailureCategory | None
    reason_refs: list[str]
    evidence_refs: list[str]
    receipt_ref: str
    checked_at: datetime


def _entry_hash(receipt: MissionStepReceipt) -> str:
    payload = receipt.model_dump(mode="json", exclude={"entry_hash_ref"})
    payload["definition"] = _definition_payload(receipt.definition)
    if receipt.blocked_dependency_step_ref is None:
        payload.pop("blocked_dependency_step_ref", None)
    if receipt.halted_by_step_ref is None:
        payload.pop("halted_by_step_ref", None)
    if receipt.retry_not_before is None:
        payload.pop("retry_not_before", None)
    if receipt.failure_category is None:
        payload.pop("failure_category", None)
    return _safe_ref(
        "mission-step-entry-hash-ref",
        payload,
    )


DispatchReceiptResolver = Callable[[str], AuthorityDispatchReceipt | None]
PlanBindingResolver = Callable[
    [MissionStepDefinition], MissionStepOrchestrationContext | None
]


class MissionStepStore:
    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / MISSION_STEP_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))
        self._clock = clock
        self._dispatch_receipt_resolver: DispatchReceiptResolver | None = None
        self._plan_binding_resolver: PlanBindingResolver | None = None

    def current_time(self) -> datetime:
        current = self._clock()
        if current.tzinfo is None:
            raise ValueError("MISSION_STEP_TRUSTED_CLOCK_TIMEZONE_REQUIRED")
        return current

    def _bind_dispatch_receipt_resolver(
        self,
        resolver: DispatchReceiptResolver,
    ) -> None:
        if self._dispatch_receipt_resolver is not None:
            raise ValueError("MISSION_STEP_DISPATCH_RESOLVER_ALREADY_BOUND")
        self._dispatch_receipt_resolver = resolver

    def _bind_plan_binding_resolver(self, resolver: PlanBindingResolver) -> None:
        if self._plan_binding_resolver is not None:
            raise ValueError("MISSION_STEP_PLAN_RESOLVER_ALREADY_BOUND")
        self._plan_binding_resolver = resolver

    def create(self, definition: MissionStepDefinition) -> MissionStepReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            with self.lock_manager.acquire(MISSION_PLAN_MATERIALIZATION_LOCK_KEY):
                self._require_plan_binding(definition)
                with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
                    receipts = self._load()
                    return self._create_from_loaded(receipts, definition)

    def _preflight_definitions_under_orchestration_lock(
        self,
        definitions: list[MissionStepDefinition],
    ) -> None:
        """Validate a complete batch while the caller holds authority state."""

        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            for definition in definitions:
                existing = self._latest(receipts, definition.step_ref)
                if (
                    existing is not None
                    and existing.definition_fingerprint_ref
                    != definition.fingerprint_ref
                ):
                    raise MissionStepConflictError("MISSION_STEP_DEFINITION_CONFLICT")

    def _materialize_definitions_under_orchestration_lock(
        self,
        definitions: list[MissionStepDefinition],
    ) -> list[MissionStepReceipt]:
        """Create an accepted plan's definitions as one conflict-checked batch."""

        for definition in definitions:
            self._require_plan_binding(definition)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            for definition in definitions:
                existing = self._latest(receipts, definition.step_ref)
                if (
                    existing is not None
                    and existing.definition_fingerprint_ref
                    != definition.fingerprint_ref
                ):
                    raise MissionStepConflictError("MISSION_STEP_DEFINITION_CONFLICT")
            created: list[MissionStepReceipt] = []
            for definition in definitions:
                receipt = self._create_from_loaded(receipts, definition)
                created.append(receipt)
                if receipt.sequence == len(receipts) + 1:
                    receipts.append(receipt)
            return created

    def _create_from_loaded(
        self,
        receipts: list[MissionStepReceipt],
        definition: MissionStepDefinition,
    ) -> MissionStepReceipt:
        existing = self._latest(receipts, definition.step_ref)
        if existing is not None:
            if existing.definition_fingerprint_ref != definition.fingerprint_ref:
                raise MissionStepConflictError("MISSION_STEP_DEFINITION_CONFLICT")
            return existing
        receipt = self._build(
            receipts,
            definition=definition,
            status=MissionStepStatus.pending,
            generation=0,
            checked_at=self.current_time(),
            safe_summary="Mission step is pending a fenced owner claim.",
        )
        self._append(receipt)
        return receipt

    def _require_plan_binding(
        self,
        definition: MissionStepDefinition,
    ) -> MissionStepOrchestrationContext | None:
        if self._plan_binding_resolver is None:
            if definition.orchestration_plan_ref is not None:
                raise MissionStepConflictError(
                    "MISSION_STEP_ACCEPTED_PLAN_BINDING_REQUIRED"
                )
            return None
        resolved = self._plan_binding_resolver(definition)
        if definition.orchestration_plan_ref is None:
            if resolved is not None:
                raise MissionStepConflictError(
                    "MISSION_STEP_REF_RESERVED_BY_ACCEPTED_PLAN"
                )
            return None
        if resolved is None:
            raise MissionStepConflictError(
                "MISSION_STEP_ACCEPTED_PLAN_BINDING_REQUIRED"
            )
        return resolved

    def claim(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        ttl_seconds: int,
        dispatch_ref: str | None = None,
        dispatch_request_fingerprint_ref: str | None = None,
        orchestration_context: MissionStepOrchestrationContext | None = None,
    ) -> MissionStepReceipt:
        validate_task_ref(owner_ref, "mission_step_owner_ref")
        if (dispatch_ref is None) != (dispatch_request_fingerprint_ref is None):
            raise ValueError("MISSION_STEP_DISPATCH_INTENT_INCOMPLETE")
        if dispatch_ref is not None:
            validate_task_ref(dispatch_ref, "mission_step_dispatch_ref")
            validate_task_ref(
                dispatch_request_fingerprint_ref or "",
                "mission_step_dispatch_request_fingerprint_ref",
            )
        self._validate_ttl(ttl_seconds)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            resolved_context = self._require_plan_binding(latest.definition)
            if latest.definition.orchestration_plan_ref is not None:
                if (
                    orchestration_context is None
                    or resolved_context is None
                    or orchestration_context != resolved_context
                ):
                    raise MissionStepConflictError(
                        "MISSION_STEP_ORCHESTRATION_CONTEXT_REQUIRED"
                    )
                for plan_step_ref in resolved_context.ordered_step_refs:
                    plan_step = self._require_latest(receipts, plan_step_ref)
                    if (
                        plan_step.definition.orchestration_plan_ref
                        != latest.definition.orchestration_plan_ref
                    ):
                        raise MissionStepConflictError(
                            "MISSION_STEP_PLAN_MEMBERSHIP_INVALID"
                        )
                    self._require_plan_binding(plan_step.definition)
                    if (
                        plan_step.definition.step_ref != latest.definition.step_ref
                        and plan_step.status in TERMINAL_MISSION_STEP_STATUSES
                        and plan_step.status != MissionStepStatus.succeeded.value
                    ):
                        raise MissionStepConflictError("MISSION_STEP_FAIL_FAST_ACTIVE")
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline <= current:
                if latest.dispatch_ref is not None:
                    durable = (
                        self._dispatch_receipt_resolver(latest.dispatch_ref)
                        if self._dispatch_receipt_resolver is not None
                        else None
                    )
                    if durable is not None:
                        durable = self._validate_durable_dispatch(latest, durable)
                        if durable.status == AuthorityDispatchStatus.prepared.value:
                            raise MissionStepConflictError(
                                "MISSION_STEP_PREPARED_DEADLINE_EXPIRED"
                            )
                        status, reason_ref = self._expired_dispatch_posture(durable)
                        bind_terminal = status != MissionStepStatus.recovery_required
                        receipt = self._build_from(
                            receipts,
                            latest,
                            status=status,
                            generation=latest.generation,
                            dispatch_ref=latest.dispatch_ref,
                            dispatch_request_fingerprint_ref=(
                                latest.dispatch_request_fingerprint_ref
                            ),
                            dispatch_receipt_ref=(
                                durable.receipt_ref if bind_terminal else None
                            ),
                            dispatch_entry_hash_ref=(
                                durable.entry_hash_ref if bind_terminal else None
                            ),
                            reason_refs=[reason_ref, *durable.reason_refs],
                            evidence_refs=self._dispatch_evidence_refs(durable),
                            checked_at=current,
                            safe_summary=(
                                "Mission step reconciled durable dispatch truth "
                                "after deadline."
                            ),
                        )
                        self._append(receipt)
                        return receipt
                    return self._terminal_locked(
                        receipts,
                        latest,
                        MissionStepStatus.recovery_required,
                        reason_ref=(
                            "reason-ref:mission-step:deadline-expired-dispatch-unresolved"
                        ),
                        safe_summary=(
                            "Mission step deadline expired with unresolved dispatch truth."
                        ),
                        checked_at=current,
                    )
                return self._terminal_locked(
                    receipts,
                    latest,
                    MissionStepStatus.failed,
                    reason_ref="reason-ref:mission-step:deadline-expired",
                    safe_summary="Mission step deadline expired before claim.",
                    checked_at=current,
                )
            retry_claim = latest.status == MissionStepStatus.retry_pending.value
            if retry_claim and (
                latest.retry_not_before is None
                or latest.retry_not_before > current
            ):
                raise MissionStepConflictError("MISSION_STEP_RETRY_BACKOFF_ACTIVE")
            if latest.dispatch_ref is not None and not retry_claim and (
                dispatch_ref != latest.dispatch_ref
                or dispatch_request_fingerprint_ref
                != latest.dispatch_request_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT"
                )
            next_attempt_no = latest.attempt_no + 1 if retry_claim else latest.attempt_no
            planned_dispatch_ref = latest.definition.planned_dispatch_ref
            planned_fingerprint_ref = (
                latest.definition.planned_dispatch_request_fingerprint_ref
            )
            if next_attempt_no > 1:
                planned_attempt = next(
                    (
                        attempt
                        for attempt in latest.definition.planned_retry_attempts
                        if attempt.attempt_no == next_attempt_no
                    ),
                    None,
                )
                if planned_attempt is None:
                    raise MissionStepConflictError(
                        "MISSION_STEP_RETRY_ATTEMPT_NOT_PLANNED"
                    )
                planned_dispatch_ref = planned_attempt.dispatch_ref
                planned_fingerprint_ref = (
                    planned_attempt.dispatch_request_fingerprint_ref
                )
            if planned_dispatch_ref is not None and (
                dispatch_ref != planned_dispatch_ref
                or dispatch_request_fingerprint_ref != planned_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_PLANNED_DISPATCH_FINGERPRINT_CONFLICT"
                )
            if (
                latest.status == MissionStepStatus.claimed.value
                and latest.claim_expires_at is not None
                and latest.claim_expires_at > current
            ):
                raise MissionStepConflictError("MISSION_STEP_ALREADY_CLAIMED")
            for dependency in latest.definition.dependency_step_refs:
                dep = self._latest(receipts, dependency)
                if (
                    dep is None
                    or dep.status != MissionStepStatus.succeeded.value
                    or dep.definition.mission_ref != latest.definition.mission_ref
                    or dep.definition.run_ref != latest.definition.run_ref
                    or dep.definition.orchestration_plan_ref
                    != latest.definition.orchestration_plan_ref
                ):
                    raise MissionStepConflictError("MISSION_STEP_DEPENDENCY_NOT_READY")
                self._require_plan_binding(dep.definition)
            generation = latest.generation + 1
            claim_ref = _safe_ref(
                "mission-step-claim-ref",
                {
                    "step_ref": step_ref,
                    "owner_ref": owner_ref,
                    "generation": generation,
                },
            )
            expires = min(
                current + timedelta(seconds=ttl_seconds),
                latest.definition.deadline,
            )
            bound_dispatch_ref = dispatch_ref if retry_claim else latest.dispatch_ref or dispatch_ref
            bound_fingerprint_ref = (
                dispatch_request_fingerprint_ref
                if retry_claim
                else latest.dispatch_request_fingerprint_ref
                or dispatch_request_fingerprint_ref
            )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                attempt_no=next_attempt_no,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=expires,
                dispatch_ref=bound_dispatch_ref,
                dispatch_request_fingerprint_ref=bound_fingerprint_ref,
                checked_at=current,
                safe_summary="Mission step ownership was fenced and claimed.",
            )
            self._append(receipt)
            return receipt

    def heartbeat(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        ttl_seconds: int,
    ) -> MissionStepReceipt:
        self._validate_ttl(ttl_seconds)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            expires = min(
                current + timedelta(seconds=ttl_seconds),
                latest.definition.deadline,
            )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=expires,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                checked_at=current,
                safe_summary="Mission step owner heartbeat renewed the fenced claim.",
            )
            self._append(receipt)
            return receipt

    def record_dispatch_intent(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        dispatch_ref: str,
        dispatch_request_fingerprint_ref: str,
    ) -> MissionStepReceipt:
        validate_task_ref(dispatch_ref, "mission_step_dispatch_ref")
        validate_task_ref(
            dispatch_request_fingerprint_ref,
            "mission_step_dispatch_request_fingerprint_ref",
        )
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            if latest.dispatch_ref is not None and latest.dispatch_ref != dispatch_ref:
                raise MissionStepConflictError("MISSION_STEP_DISPATCH_INTENT_CONFLICT")
            if (
                latest.dispatch_request_fingerprint_ref is not None
                and latest.dispatch_request_fingerprint_ref
                != dispatch_request_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=latest.claim_expires_at,
                dispatch_ref=dispatch_ref,
                dispatch_request_fingerprint_ref=dispatch_request_fingerprint_ref,
                checked_at=current,
                safe_summary="Mission step recorded one immutable dispatch intent.",
            )
            self._append(receipt)
            return receipt

    def complete(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        status: MissionStepStatus,
        reason_refs: list[str],
        evidence_refs: list[str] | None = None,
        dispatch_receipt: AuthorityDispatchReceipt | None = None,
    ) -> MissionStepReceipt:
        if status.value not in TERMINAL_MISSION_STEP_STATUSES:
            raise ValueError("MISSION_STEP_TERMINAL_STATUS_REQUIRED")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            dispatch_receipt_ref = None
            dispatch_entry_hash_ref = None
            if status == MissionStepStatus.succeeded:
                dispatch_receipt = self._validate_succeeded_dispatch(
                    latest,
                    dispatch_receipt,
                )
            elif latest.dispatch_ref is not None:
                if dispatch_receipt is None:
                    if not (
                        status == MissionStepStatus.recovery_required
                        and reason_refs
                        == ["reason-ref:mission-step:dispatch-reconciliation-failed"]
                    ):
                        raise MissionStepConflictError(
                            "MISSION_STEP_TERMINAL_DISPATCH_EVIDENCE_REQUIRED"
                        )
                else:
                    dispatch_receipt = self._validate_durable_dispatch(
                        latest,
                        dispatch_receipt,
                    )
                    expected_statuses = {
                        MissionStepStatus.failed: {
                            AuthorityDispatchStatus.failed.value,
                            AuthorityDispatchStatus.denied.value,
                            AuthorityDispatchStatus.cancelled_before_start.value,
                        },
                        MissionStepStatus.cancelled: {
                            AuthorityDispatchStatus.cancelled_before_start.value,
                        },
                        MissionStepStatus.recovery_required: {
                            AuthorityDispatchStatus.started.value,
                            AuthorityDispatchStatus.cancellation_pending.value,
                        },
                        MissionStepStatus.dead_lettered: {
                            AuthorityDispatchStatus.failed.value,
                        },
                    }[status]
                    if dispatch_receipt.status not in expected_statuses:
                        raise MissionStepConflictError(
                            "MISSION_STEP_TERMINAL_DISPATCH_STATUS_INVALID"
                        )
            if dispatch_receipt is not None:
                dispatch_receipt_ref = dispatch_receipt.receipt_ref
                dispatch_entry_hash_ref = dispatch_receipt.entry_hash_ref
            receipt = self._build_from(
                receipts,
                latest,
                status=status,
                generation=generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                dispatch_receipt_ref=dispatch_receipt_ref,
                dispatch_entry_hash_ref=dispatch_entry_hash_ref,
                reason_refs=reason_refs,
                evidence_refs=evidence_refs or [],
                checked_at=current,
                safe_summary="Mission step reached a durable terminal posture.",
            )
            self._append(receipt)
            return receipt

    def schedule_retry(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        failure_category: AuthorityDispatchFailureCategory,
        dispatch_receipt: AuthorityDispatchReceipt,
        evidence_refs: list[str],
    ) -> MissionStepReceipt:
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            if latest.attempt_no >= latest.definition.max_attempts:
                raise MissionStepConflictError("MISSION_STEP_RETRY_LIMIT_EXHAUSTED")
            if (
                failure_category.value
                not in latest.definition.retryable_failure_categories
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_FAILURE_CATEGORY_NOT_RETRYABLE"
                )
            durable = self._validate_durable_dispatch(latest, dispatch_receipt)
            if (
                durable.status != AuthorityDispatchStatus.failed.value
                or durable.failure_category != failure_category.value
                or durable.budget_settlement_receipt_ref is None
                or not durable.adapter_invocation_performed
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_RETRY_DISPATCH_EVIDENCE_INVALID"
                )
            retry_not_before = current + timedelta(
                seconds=latest.definition.retry_backoff_seconds
            )
            if retry_not_before >= latest.definition.deadline:
                raise MissionStepConflictError(
                    "MISSION_STEP_RETRY_DEADLINE_EXHAUSTED"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.retry_pending,
                generation=latest.generation,
                attempt_no=latest.attempt_no,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                dispatch_receipt_ref=durable.receipt_ref,
                dispatch_entry_hash_ref=durable.entry_hash_ref,
                retry_not_before=retry_not_before,
                failure_category=failure_category,
                reason_refs=["reason-ref:mission-step:retry-scheduled"],
                evidence_refs=list(dict.fromkeys(evidence_refs)),
                checked_at=current,
                safe_summary=(
                    "Mission step released its claim for a bounded retry."
                ),
            )
            self._append(receipt)
            return receipt

    def record_approval_wait(
        self,
        step_ref: str,
        *,
        approval_request_ref: str,
        approval_ref: str,
        approval_scope_fingerprint_ref: str,
        reason_refs: list[str],
    ) -> MissionStepReceipt:
        for value, field_name in [
            (step_ref, "mission_step_ref"),
            (approval_request_ref, "mission_step_approval_request_ref"),
            (approval_ref, "mission_step_approval_ref"),
            (
                approval_scope_fingerprint_ref,
                "mission_step_approval_scope_fingerprint_ref",
            ),
            *[(ref, "mission_step_reason_ref") for ref in reason_refs],
        ]:
            validate_task_ref(value, field_name)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status == MissionStepStatus.approval_wait.value:
                expected = (
                    approval_request_ref,
                    approval_ref,
                    approval_scope_fingerprint_ref,
                )
                actual = (
                    latest.approval_request_ref,
                    latest.approval_ref,
                    latest.approval_scope_fingerprint_ref,
                )
                if actual != expected:
                    raise MissionStepConflictError(
                        "MISSION_STEP_APPROVAL_WAIT_SCOPE_CONFLICT"
                    )
                return latest
            if latest.status != MissionStepStatus.pending.value:
                raise MissionStepConflictError(
                    "MISSION_STEP_APPROVAL_WAIT_REQUIRES_PENDING"
                )
            current = self.current_time()
            if latest.definition.deadline <= current:
                receipt = self._build_from(
                    receipts,
                    latest,
                    status=MissionStepStatus.failed,
                    generation=latest.generation,
                    reason_refs=["reason-ref:mission-step:deadline-expired"],
                    checked_at=current,
                    safe_summary=(
                        "Mission step deadline expired before approval wait."
                    ),
                )
                self._append(receipt)
                return receipt
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.approval_wait,
                generation=latest.generation,
                approval_request_ref=approval_request_ref,
                approval_ref=approval_ref,
                approval_scope_fingerprint_ref=approval_scope_fingerprint_ref,
                reason_refs=list(dict.fromkeys(reason_refs)),
                checked_at=current,
                safe_summary=(
                    "Mission step is waiting without a claim or budget reservation."
                ),
            )
            self._append(receipt)
            return receipt

    def resume_approval_wait(
        self,
        step_ref: str,
        *,
        approval_ref: str,
        approval_scope_fingerprint_ref: str,
        validation_evidence_ref: str,
        idempotency_ref: str | None = None,
    ) -> MissionStepReceipt:
        for value, field_name in [
            (step_ref, "mission_step_ref"),
            (approval_ref, "mission_step_approval_ref"),
            (
                approval_scope_fingerprint_ref,
                "mission_step_approval_scope_fingerprint_ref",
            ),
            (validation_evidence_ref, "mission_step_approval_validation_ref"),
            (idempotency_ref, "mission_step_approval_idempotency_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status != MissionStepStatus.approval_wait.value:
                raise MissionStepConflictError(
                    "MISSION_STEP_APPROVAL_RESUME_REQUIRES_WAIT"
                )
            if (
                latest.approval_ref != approval_ref
                or latest.approval_scope_fingerprint_ref
                != approval_scope_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_APPROVAL_RESUME_SCOPE_CONFLICT"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.pending,
                generation=latest.generation,
                approval_request_ref=latest.approval_request_ref,
                approval_ref=latest.approval_ref,
                approval_scope_fingerprint_ref=(
                    latest.approval_scope_fingerprint_ref
                ),
                reason_refs=["reason-ref:mission-step:approval-freshly-validated"],
                evidence_refs=[
                    validation_evidence_ref,
                    *([idempotency_ref] if idempotency_ref is not None else []),
                ],
                checked_at=self.current_time(),
                safe_summary=(
                    "Mission step left approval wait after fresh exact validation."
                ),
            )
            self._append(receipt)
            return receipt

    def fail_approval_wait(
        self,
        step_ref: str,
        *,
        reason_ref: str,
        evidence_refs: list[str] | None = None,
    ) -> MissionStepReceipt:
        validate_task_ref(step_ref, "mission_step_ref")
        validate_task_ref(reason_ref, "mission_step_reason_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status != MissionStepStatus.approval_wait.value:
                raise MissionStepConflictError(
                    "MISSION_STEP_APPROVAL_FAILURE_REQUIRES_WAIT"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.failed,
                generation=latest.generation,
                approval_request_ref=latest.approval_request_ref,
                approval_ref=latest.approval_ref,
                approval_scope_fingerprint_ref=(
                    latest.approval_scope_fingerprint_ref
                ),
                reason_refs=[reason_ref],
                evidence_refs=evidence_refs or [],
                checked_at=self.current_time(),
                safe_summary="Mission approval wait failed closed before dispatch.",
            )
            self._append(receipt)
            return receipt

    def fail_before_dispatch(
        self,
        step_ref: str,
        *,
        reason_ref: str,
        evidence_refs: list[str] | None = None,
        approval_request_ref: str | None = None,
        approval_ref: str | None = None,
        approval_scope_fingerprint_ref: str | None = None,
    ) -> MissionStepReceipt:
        validate_task_ref(step_ref, "mission_step_ref")
        validate_task_ref(reason_ref, "mission_step_reason_ref")
        for value, field_name in [
            (approval_request_ref, "mission_step_approval_request_ref"),
            (approval_ref, "mission_step_approval_ref"),
            (
                approval_scope_fingerprint_ref,
                "mission_step_approval_scope_fingerprint_ref",
            ),
            *[(ref, "mission_step_evidence_ref") for ref in evidence_refs or []],
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        approval_binding = (
            approval_request_ref,
            approval_ref,
            approval_scope_fingerprint_ref,
        )
        if any(approval_binding) and not all(approval_binding):
            approval_request_ref = None
            approval_ref = None
            approval_scope_fingerprint_ref = None
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.status not in {
                MissionStepStatus.pending.value,
                MissionStepStatus.approval_wait.value,
            }:
                raise MissionStepConflictError(
                    "MISSION_STEP_PRE_DISPATCH_FAILURE_STATE_INVALID"
                )
            if latest.dispatch_ref is not None:
                raise MissionStepConflictError(
                    "MISSION_STEP_PRE_DISPATCH_FAILURE_DISPATCH_FORBIDDEN"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.failed,
                generation=latest.generation,
                approval_request_ref=(
                    approval_request_ref or latest.approval_request_ref
                ),
                approval_ref=approval_ref or latest.approval_ref,
                approval_scope_fingerprint_ref=(
                    approval_scope_fingerprint_ref
                    or latest.approval_scope_fingerprint_ref
                ),
                reason_refs=[reason_ref],
                evidence_refs=evidence_refs or [],
                checked_at=self.current_time(),
                safe_summary="Mission step failed closed before dispatch preparation.",
            )
            self._append(receipt)
            return receipt

    def expire_deadline(
        self,
        step_ref: str,
        *,
        evidence_refs: list[str] | None = None,
    ) -> MissionStepReceipt:
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline > current:
                raise MissionStepConflictError("MISSION_STEP_DEADLINE_NOT_EXPIRED")
            if latest.dispatch_ref is not None:
                raise MissionStepConflictError(
                    "MISSION_STEP_DEADLINE_DISPATCH_RECONCILIATION_REQUIRED"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.failed,
                generation=latest.generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                approval_request_ref=latest.approval_request_ref,
                approval_ref=latest.approval_ref,
                approval_scope_fingerprint_ref=(
                    latest.approval_scope_fingerprint_ref
                ),
                reason_refs=["reason-ref:mission-step:deadline-expired"],
                evidence_refs=evidence_refs or [],
                checked_at=current,
                safe_summary="Mission step deadline expired before dispatch start.",
            )
            self._append(receipt)
            return receipt

    def reconcile_expired_dispatch(
        self,
        step_ref: str,
        *,
        dispatch_receipt: AuthorityDispatchReceipt,
        evidence_refs: list[str],
    ) -> MissionStepReceipt:
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline > current:
                raise MissionStepConflictError("MISSION_STEP_DEADLINE_NOT_EXPIRED")
            durable = self._validate_durable_dispatch(latest, dispatch_receipt)
            status, reason_ref = self._expired_dispatch_posture(durable)
            bind_terminal = status != MissionStepStatus.recovery_required
            receipt = self._build_from(
                receipts,
                latest,
                status=status,
                generation=latest.generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                dispatch_receipt_ref=(durable.receipt_ref if bind_terminal else None),
                dispatch_entry_hash_ref=(
                    durable.entry_hash_ref if bind_terminal else None
                ),
                reason_refs=[reason_ref, *durable.reason_refs],
                evidence_refs=evidence_refs,
                checked_at=current,
                safe_summary=(
                    "Mission step reconciled durable dispatch truth after deadline."
                ),
            )
            self._append(receipt)
            return receipt

    def block_from_terminal_dependency(
        self,
        step_ref: str,
        *,
        dependency_step_ref: str,
    ) -> MissionStepReceipt:
        validate_task_ref(step_ref, "mission_step_ref")
        validate_task_ref(dependency_step_ref, "mission_step_dependency_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.status != MissionStepStatus.pending.value:
                raise MissionStepConflictError(
                    "MISSION_STEP_DEPENDENCY_BLOCK_REQUIRES_PENDING"
                )
            if dependency_step_ref not in latest.definition.dependency_step_refs:
                raise MissionStepConflictError("MISSION_STEP_DEPENDENCY_NOT_DECLARED")
            dependency = self._require_latest(receipts, dependency_step_ref)
            if (
                dependency.definition.mission_ref != latest.definition.mission_ref
                or dependency.definition.run_ref != latest.definition.run_ref
                or latest.definition.orchestration_plan_ref is None
                or dependency.definition.orchestration_plan_ref
                != latest.definition.orchestration_plan_ref
            ):
                raise MissionStepConflictError("MISSION_STEP_DEPENDENCY_SCOPE_MISMATCH")
            self._require_plan_binding(latest.definition)
            self._require_plan_binding(dependency.definition)
            if (
                dependency.status not in TERMINAL_MISSION_STEP_STATUSES
                or dependency.status == MissionStepStatus.succeeded.value
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_DEPENDENCY_TERMINAL_FAILURE_REQUIRED"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.dependency_blocked,
                generation=latest.generation,
                blocked_dependency_step_ref=dependency_step_ref,
                reason_refs=["reason-ref:mission-step:dependency-terminal"],
                evidence_refs=[dependency.receipt_ref, dependency.entry_hash_ref],
                checked_at=self.current_time(),
                safe_summary=(
                    "Mission step is blocked by a durable terminal dependency."
                ),
            )
            self._append(receipt)
            return receipt

    def halt_from_fail_fast_terminal(
        self,
        step_ref: str,
        *,
        terminal_step_ref: str,
    ) -> MissionStepReceipt:
        """Durably close unscheduled work after fail-fast has activated."""

        validate_task_ref(step_ref, "mission_step_ref")
        validate_task_ref(terminal_step_ref, "mission_step_terminal_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.status != MissionStepStatus.pending.value:
                raise MissionStepConflictError(
                    "MISSION_STEP_FAIL_FAST_HALT_REQUIRES_PENDING"
                )
            terminal = self._require_latest(receipts, terminal_step_ref)
            if (
                terminal.definition.mission_ref != latest.definition.mission_ref
                or terminal.definition.run_ref != latest.definition.run_ref
                or latest.definition.orchestration_plan_ref is None
                or terminal.definition.orchestration_plan_ref
                != latest.definition.orchestration_plan_ref
            ):
                raise MissionStepConflictError("MISSION_STEP_FAIL_FAST_SCOPE_MISMATCH")
            self._require_plan_binding(latest.definition)
            self._require_plan_binding(terminal.definition)
            if (
                terminal.status not in TERMINAL_MISSION_STEP_STATUSES
                or terminal.status == MissionStepStatus.succeeded.value
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_FAIL_FAST_TERMINAL_FAILURE_REQUIRED"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.fail_fast_halted,
                generation=latest.generation,
                halted_by_step_ref=terminal_step_ref,
                reason_refs=["reason-ref:mission-step:fail-fast-halted"],
                evidence_refs=[terminal.receipt_ref, terminal.entry_hash_ref],
                checked_at=self.current_time(),
                safe_summary="Mission step was not scheduled after durable fail-fast activation.",
            )
            self._append(receipt)
            return receipt

    def read(self, step_ref: str) -> MissionStepReadModel:
        validate_task_ref(step_ref, "mission_step_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            latest = self._require_latest(self._load(), step_ref)
        return self._read_model_from_receipt(latest)

    def snapshot(
        self,
        step_refs: list[str],
    ) -> tuple[list[MissionStepReadModel], dict[str, MissionStepReceipt]]:
        for step_ref in step_refs:
            validate_task_ref(step_ref, "mission_step_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            receipts = self._load()
            latest = {
                step_ref: self._require_latest(receipts, step_ref)
                for step_ref in step_refs
            }
        return (
            [self._read_model_from_receipt(latest[step_ref]) for step_ref in step_refs],
            latest,
        )

    @staticmethod
    def _read_model_from_receipt(latest: MissionStepReceipt) -> MissionStepReadModel:
        return MissionStepReadModel(
            step_ref=latest.definition.step_ref,
            status=latest.status,
            generation=latest.generation,
            attempt_no=latest.attempt_no,
            owner_ref=latest.owner_ref,
            claim_ref=latest.claim_ref,
            claim_expires_at=latest.claim_expires_at,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            dispatch_receipt_ref=latest.dispatch_receipt_ref,
            approval_request_ref=latest.approval_request_ref,
            approval_ref=latest.approval_ref,
            approval_scope_fingerprint_ref=(
                latest.approval_scope_fingerprint_ref
            ),
            retry_not_before=latest.retry_not_before,
            failure_category=latest.failure_category,
            dispatch_entry_hash_ref=latest.dispatch_entry_hash_ref,
            blocked_dependency_step_ref=latest.blocked_dependency_step_ref,
            halted_by_step_ref=latest.halted_by_step_ref,
            reason_refs=latest.reason_refs,
            evidence_refs=latest.evidence_refs,
            receipt_ref=latest.receipt_ref,
            autonomous_retry_enabled=latest.definition.max_attempts > 1,
        )

    def _read_inspection_source(self, step_ref: str) -> _MissionStepInspectionSource:
        validate_task_ref(step_ref, "mission_step_ref")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            latest = self._require_latest(self._load(), step_ref)
        return _MissionStepInspectionSource(
            mission_ref=latest.definition.mission_ref,
            run_ref=latest.definition.run_ref,
            step_ref=latest.definition.step_ref,
            capability_ref=latest.definition.capability_ref,
            adapter_ref=latest.definition.adapter_ref,
            lease_ref=latest.definition.lease_ref,
            dependency_step_refs=list(latest.definition.dependency_step_refs),
            deadline=latest.definition.deadline,
            status=latest.status,
            generation=latest.generation,
            attempt_no=latest.attempt_no,
            owner_ref=latest.owner_ref,
            claim_ref=latest.claim_ref,
            claim_expires_at=latest.claim_expires_at,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            dispatch_receipt_ref=latest.dispatch_receipt_ref,
            approval_request_ref=latest.approval_request_ref,
            approval_ref=latest.approval_ref,
            approval_scope_fingerprint_ref=(
                latest.approval_scope_fingerprint_ref
            ),
            retry_not_before=latest.retry_not_before,
            failure_category=latest.failure_category,
            reason_refs=list(latest.reason_refs),
            evidence_refs=list(latest.evidence_refs),
            receipt_ref=latest.receipt_ref,
            checked_at=latest.checked_at,
        )

    def receipts(self) -> list[MissionStepReceipt]:
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_STEP_LOCK_KEY),
        ):
            return self._load()

    def _terminal_locked(
        self,
        receipts: list[MissionStepReceipt],
        latest: MissionStepReceipt,
        status: MissionStepStatus,
        *,
        reason_ref: str,
        safe_summary: str,
        checked_at: datetime,
    ) -> MissionStepReceipt:
        receipt = self._build_from(
            receipts,
            latest,
            status=status,
            generation=latest.generation,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            reason_refs=[reason_ref],
            checked_at=checked_at,
            safe_summary=safe_summary,
        )
        self._append(receipt)
        return receipt

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if ttl_seconds < 1 or ttl_seconds > 300:
            raise ValueError("MISSION_STEP_CLAIM_TTL_INVALID")

    def _validate_succeeded_dispatch(
        self,
        latest: MissionStepReceipt,
        supplied: AuthorityDispatchReceipt | None,
    ) -> AuthorityDispatchReceipt:
        if supplied is None:
            raise MissionStepConflictError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_EVIDENCE_REQUIRED"
            )
        durable = self._validate_durable_dispatch(latest, supplied)
        if (
            durable.status != AuthorityDispatchStatus.succeeded.value
            or not durable.execution_started
            or not durable.adapter_invocation_performed
            or durable.budget_settlement_receipt_ref is None
        ):
            raise MissionStepConflictError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_BINDING_INVALID"
            )
        return durable

    def _validate_durable_dispatch(
        self,
        latest: MissionStepReceipt,
        supplied: AuthorityDispatchReceipt,
    ) -> AuthorityDispatchReceipt:
        if (
            latest.dispatch_ref is None
            or latest.dispatch_request_fingerprint_ref is None
            or self._dispatch_receipt_resolver is None
        ):
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_EVIDENCE_REQUIRED")
        durable = self._dispatch_receipt_resolver(latest.dispatch_ref)
        if durable is None or durable != supplied:
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_NOT_DURABLE")
        if (
            durable.dispatch_ref != latest.dispatch_ref
            or durable.request_fingerprint_ref
            != latest.dispatch_request_fingerprint_ref
            or durable.run_ref != latest.definition.run_ref
            or durable.lease_ref != latest.definition.lease_ref
            or durable.adapter_ref != latest.definition.adapter_ref
            or durable.capability_ref != latest.definition.capability_ref
        ):
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        expected_dispatch_ref = latest.definition.planned_dispatch_ref
        expected_fingerprint_ref = (
            latest.definition.planned_dispatch_request_fingerprint_ref
        )
        if latest.attempt_no > 1:
            planned_attempt = next(
                (
                    attempt
                    for attempt in latest.definition.planned_retry_attempts
                    if attempt.attempt_no == latest.attempt_no
                ),
                None,
            )
            if planned_attempt is None:
                raise MissionStepConflictError(
                    "MISSION_STEP_RETRY_ATTEMPT_NOT_PLANNED"
                )
            expected_dispatch_ref = planned_attempt.dispatch_ref
            expected_fingerprint_ref = (
                planned_attempt.dispatch_request_fingerprint_ref
            )
        if latest.definition.orchestration_plan_ref is not None and (
            latest.dispatch_ref != expected_dispatch_ref
            or latest.dispatch_request_fingerprint_ref != expected_fingerprint_ref
            or durable.start_deadline != latest.definition.deadline
        ):
            raise MissionStepConflictError(
                "MISSION_STEP_ORCHESTRATION_DISPATCH_BINDING_INVALID"
            )
        return durable

    @staticmethod
    def _expired_dispatch_posture(
        receipt: AuthorityDispatchReceipt,
    ) -> tuple[MissionStepStatus, str]:
        if receipt.status == AuthorityDispatchStatus.succeeded.value:
            return MissionStepStatus.succeeded, "reason-ref:mission-step:succeeded"
        if receipt.status in {
            AuthorityDispatchStatus.failed.value,
            AuthorityDispatchStatus.denied.value,
        }:
            return MissionStepStatus.failed, "reason-ref:mission-step:dispatch-failed"
        if receipt.status == AuthorityDispatchStatus.cancelled_before_start.value:
            return (
                MissionStepStatus.failed,
                "reason-ref:mission-step:deadline-expired-before-dispatch",
            )
        return (
            MissionStepStatus.recovery_required,
            "reason-ref:mission-step:dispatch-recovery-required",
        )

    @staticmethod
    def _dispatch_evidence_refs(
        receipt: AuthorityDispatchReceipt,
    ) -> list[str]:
        values = [
            receipt.receipt_ref,
            receipt.entry_hash_ref,
            receipt.authority_decision_ref,
            receipt.authority_policy_receipt_ref,
            receipt.approval_validation_ref,
            receipt.budget_reservation_receipt_ref,
            receipt.budget_start_receipt_ref,
            receipt.budget_settlement_receipt_ref,
            receipt.budget_release_receipt_ref,
            receipt.execution_ref,
            *receipt.evidence_refs,
            *receipt.output_refs,
        ]
        return list(dict.fromkeys(value for value in values if value is not None))

    def _require_owned(
        self,
        receipts: list[MissionStepReceipt],
        step_ref: str,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        current: datetime,
    ) -> MissionStepReceipt:
        latest = self._require_latest(receipts, step_ref)
        if (
            latest.status != MissionStepStatus.claimed.value
            or latest.owner_ref != owner_ref
            or latest.claim_ref != claim_ref
            or latest.generation != generation
        ):
            raise MissionStepConflictError("MISSION_STEP_STALE_FENCE")
        if latest.claim_expires_at is None or latest.claim_expires_at <= current:
            raise MissionStepConflictError("MISSION_STEP_CLAIM_EXPIRED")
        return latest

    @staticmethod
    def _latest(
        receipts: list[MissionStepReceipt], step_ref: str
    ) -> MissionStepReceipt | None:
        return next(
            (
                item
                for item in reversed(receipts)
                if item.definition.step_ref == step_ref
            ),
            None,
        )

    def _require_latest(
        self, receipts: list[MissionStepReceipt], step_ref: str
    ) -> MissionStepReceipt:
        latest = self._latest(receipts, step_ref)
        if latest is None:
            raise KeyError("MISSION_STEP_UNKNOWN")
        return latest

    def _build(
        self,
        receipts: list[MissionStepReceipt],
        *,
        definition: MissionStepDefinition,
        status: MissionStepStatus,
        generation: int,
        safe_summary: str,
        **updates: Any,
    ) -> MissionStepReceipt:
        sequence = len(receipts) + 1
        payload = dict(
            schema_version=MISSION_STEP_SCHEMA_VERSION,
            sequence=sequence,
            receipt_ref=f"mission-step-receipt-ref:{sequence}",
            entry_hash_ref="mission-step-entry-hash-ref:pending",
            previous_entry_hash_ref=receipts[-1].entry_hash_ref if receipts else None,
            definition=definition,
            definition_fingerprint_ref=definition.fingerprint_ref,
            status=status,
            generation=generation,
            safe_summary=safe_summary,
            **updates,
        )
        receipt = MissionStepReceipt.model_validate(payload)
        receipt = receipt.model_copy(update={"entry_hash_ref": _entry_hash(receipt)})
        self._validate_history_receipt(
            receipt,
            self._latest(receipts, definition.step_ref),
        )
        return receipt

    def _build_from(
        self,
        receipts: list[MissionStepReceipt],
        latest: MissionStepReceipt,
        **updates: Any,
    ) -> MissionStepReceipt:
        updates.setdefault("attempt_no", latest.attempt_no)
        return self._build(receipts, definition=latest.definition, **updates)

    def _append(self, receipt: MissionStepReceipt) -> None:
        if receipt.sequence > MISSION_STEP_LEDGER_MAX_RECEIPTS:
            raise MissionStepCorruptionError(
                "MISSION_STEP_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        self.receipts_path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (receipt.model_dump_json() + "\n").encode("utf-8")
        flags = (
            os.O_RDWR
            | os.O_APPEND
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(self.receipts_path, flags, 0o600)
        except OSError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_LEDGER_WRITE_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size + len(encoded) > MISSION_STEP_LEDGER_MAX_BYTES
            ):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_SIZE_OR_TYPE_INVALID"
                )
            existing_payload = os.pread(descriptor, metadata.st_size, 0)
            existing = self._decode(existing_payload)
            expected_previous = existing[-1].entry_hash_ref if existing else None
            if (
                receipt.sequence != len(existing) + 1
                or receipt.previous_entry_hash_ref != expected_previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_APPEND_BINDING_INVALID"
                )
            self._validate_history_receipt(
                receipt,
                self._latest(existing, receipt.definition.step_ref),
            )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("mission step append failed")
                view = view[written:]
            os.fsync(descriptor)
            new_file = metadata.st_size == 0
        except OSError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            os.close(descriptor)
        if new_file:
            directory_fd = os.open(self.receipts_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def _load(self) -> list[MissionStepReceipt]:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(self.receipts_path, flags)
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_READ_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_REGULAR_FILE_REQUIRED"
                )
            if metadata.st_size > MISSION_STEP_LEDGER_MAX_BYTES:
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                payload = stream.read(MISSION_STEP_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
        if len(payload) > MISSION_STEP_LEDGER_MAX_BYTES:
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_SIZE_LIMIT_EXCEEDED")
        return self._decode(payload)

    def _decode(self, payload: bytes) -> list[MissionStepReceipt]:
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_INVALID") from exc
        if len(lines) > MISSION_STEP_LEDGER_MAX_RECEIPTS:
            raise MissionStepCorruptionError(
                "MISSION_STEP_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        receipts = [
            MissionStepReceipt.model_validate_json(line)
            for line in lines
            if line.strip()
        ]
        previous: str | None = None
        latest_by_step: dict[str, MissionStepReceipt] = {}
        for index, receipt in enumerate(receipts, 1):
            if (
                receipt.sequence != index
                or receipt.previous_entry_hash_ref != previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionStepCorruptionError("MISSION_STEP_HASH_CHAIN_INVALID")
            prior = latest_by_step.get(receipt.definition.step_ref)
            self._validate_history_receipt(receipt, prior)
            if receipt.status == MissionStepStatus.dependency_blocked.value:
                self._validate_persisted_dependency_block(
                    receipt,
                    latest_by_step,
                )
            if receipt.status == MissionStepStatus.fail_fast_halted.value:
                self._validate_persisted_fail_fast_halt(receipt, latest_by_step)
            latest_by_step[receipt.definition.step_ref] = receipt
            previous = receipt.entry_hash_ref
        return receipts

    def _validate_history_receipt(
        self,
        receipt: MissionStepReceipt,
        prior: MissionStepReceipt | None,
    ) -> None:
        if receipt.checked_at.tzinfo is None:
            raise MissionStepCorruptionError("MISSION_STEP_CHECKED_AT_INVALID")
        if (receipt.dispatch_ref is None) != (
            receipt.dispatch_request_fingerprint_ref is None
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        if (receipt.dispatch_receipt_ref is None) != (
            receipt.dispatch_entry_hash_ref is None
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_DISPATCH_RECEIPT_BINDING_INVALID"
            )
        if receipt.status == MissionStepStatus.claimed.value:
            assert receipt.claim_expires_at is not None
            if (
                receipt.claim_expires_at.tzinfo is None
                or receipt.claim_expires_at <= receipt.checked_at
                or receipt.claim_expires_at > receipt.definition.deadline
                or receipt.claim_expires_at
                > receipt.checked_at + timedelta(seconds=300)
            ):
                raise MissionStepCorruptionError("MISSION_STEP_CLAIM_EXPIRY_INVALID")
        if prior is None:
            if (
                receipt.status != MissionStepStatus.pending.value
                or receipt.generation != 0
                or receipt.dispatch_ref is not None
                or receipt.approval_request_ref is not None
                or receipt.approval_ref is not None
                or receipt.approval_scope_fingerprint_ref is not None
                or receipt.reason_refs
                or receipt.evidence_refs
            ):
                raise MissionStepCorruptionError("MISSION_STEP_INITIAL_STATE_INVALID")
            return
        if (
            prior.definition_fingerprint_ref != receipt.definition_fingerprint_ref
            or prior.status in TERMINAL_MISSION_STEP_STATUSES
            or receipt.checked_at < prior.checked_at
        ):
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if prior.dispatch_ref is not None and prior.status != MissionStepStatus.retry_pending.value and (
            receipt.dispatch_ref != prior.dispatch_ref
            or receipt.dispatch_request_fingerprint_ref
            != prior.dispatch_request_fingerprint_ref
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        if (
            prior.status != MissionStepStatus.retry_pending.value
            and receipt.attempt_no != prior.attempt_no
        ):
            raise MissionStepCorruptionError("MISSION_STEP_ATTEMPT_NUMBER_INVALID")
        if prior.status == MissionStepStatus.pending.value:
            allowed = (
                receipt.status == MissionStepStatus.claimed.value
                and receipt.generation == prior.generation + 1
            ) or (
                receipt.status
                in {
                    MissionStepStatus.approval_wait.value,
                    MissionStepStatus.failed.value,
                    MissionStepStatus.dependency_blocked.value,
                    MissionStepStatus.fail_fast_halted.value,
                }
                and receipt.generation == prior.generation
            )
            if not allowed:
                raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        elif prior.status == MissionStepStatus.approval_wait.value:
            if (
                receipt.status
                not in {
                    MissionStepStatus.pending.value,
                    MissionStepStatus.failed.value,
                }
                or receipt.generation != prior.generation
                or receipt.dispatch_ref is not None
            ):
                raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
            approval_binding = (
                receipt.approval_request_ref,
                receipt.approval_ref,
                receipt.approval_scope_fingerprint_ref,
            )
            prior_approval_binding = (
                prior.approval_request_ref,
                prior.approval_ref,
                prior.approval_scope_fingerprint_ref,
            )
            if approval_binding != prior_approval_binding:
                raise MissionStepCorruptionError(
                    "MISSION_STEP_APPROVAL_BINDING_CHANGED"
                )
            if receipt.status == MissionStepStatus.pending.value and (
                receipt.reason_refs
                != ["reason-ref:mission-step:approval-freshly-validated"]
                or len(
                    [
                        ref
                        for ref in receipt.evidence_refs
                        if ref.startswith("approval-validation-ref:")
                    ]
                )
                != 1
            ):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_APPROVAL_RESUME_EVIDENCE_INVALID"
                )
        elif prior.status == MissionStepStatus.claimed.value:
            self._validate_claimed_transition(receipt, prior)
        elif prior.status == MissionStepStatus.retry_pending.value:
            if (
                receipt.status != MissionStepStatus.claimed.value
                or receipt.generation != prior.generation + 1
                or receipt.attempt_no != prior.attempt_no + 1
                or prior.retry_not_before is None
                or receipt.checked_at < prior.retry_not_before
            ):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_RETRY_CLAIM_TRANSITION_INVALID"
                )
        else:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if receipt.dispatch_receipt_ref is not None:
            self._validate_persisted_dispatch(receipt)
        if receipt.status == MissionStepStatus.succeeded.value:
            self._validate_persisted_success(receipt)

    def _validate_persisted_dependency_block(
        self,
        receipt: MissionStepReceipt,
        latest_by_step: dict[str, MissionStepReceipt],
    ) -> None:
        dependency_ref = receipt.blocked_dependency_step_ref
        dependency = latest_by_step.get(dependency_ref or "")
        if (
            dependency_ref not in receipt.definition.dependency_step_refs
            or dependency is None
            or dependency.definition.mission_ref != receipt.definition.mission_ref
            or dependency.definition.run_ref != receipt.definition.run_ref
            or receipt.definition.orchestration_plan_ref is None
            or dependency.definition.orchestration_plan_ref
            != receipt.definition.orchestration_plan_ref
            or dependency.status not in TERMINAL_MISSION_STEP_STATUSES
            or dependency.status == MissionStepStatus.succeeded.value
            or "reason-ref:mission-step:dependency-terminal" not in receipt.reason_refs
            or dependency.receipt_ref not in receipt.evidence_refs
            or dependency.entry_hash_ref not in receipt.evidence_refs
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_DEPENDENCY_BLOCK_EVIDENCE_INVALID"
            )
        try:
            self._require_plan_binding(receipt.definition)
            self._require_plan_binding(dependency.definition)
        except MissionStepConflictError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_DEPENDENCY_BLOCK_PLAN_BINDING_INVALID"
            ) from exc

    def _validate_persisted_fail_fast_halt(
        self,
        receipt: MissionStepReceipt,
        latest_by_step: dict[str, MissionStepReceipt],
    ) -> None:
        terminal = latest_by_step.get(receipt.halted_by_step_ref or "")
        if (
            terminal is None
            or terminal.definition.mission_ref != receipt.definition.mission_ref
            or terminal.definition.run_ref != receipt.definition.run_ref
            or receipt.definition.orchestration_plan_ref is None
            or terminal.definition.orchestration_plan_ref
            != receipt.definition.orchestration_plan_ref
            or terminal.status not in TERMINAL_MISSION_STEP_STATUSES
            or terminal.status == MissionStepStatus.succeeded.value
            or "reason-ref:mission-step:fail-fast-halted" not in receipt.reason_refs
            or terminal.receipt_ref not in receipt.evidence_refs
            or terminal.entry_hash_ref not in receipt.evidence_refs
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_FAIL_FAST_HALT_EVIDENCE_INVALID"
            )
        try:
            self._require_plan_binding(receipt.definition)
            self._require_plan_binding(terminal.definition)
        except MissionStepConflictError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_FAIL_FAST_HALT_PLAN_BINDING_INVALID"
            ) from exc

    def _validate_claimed_transition(
        self,
        receipt: MissionStepReceipt,
        prior: MissionStepReceipt,
    ) -> None:
        if receipt.generation == prior.generation + 1:
            if (
                receipt.status != MissionStepStatus.claimed.value
                or prior.claim_expires_at is None
                or prior.claim_expires_at > receipt.checked_at
                or receipt.dispatch_ref != prior.dispatch_ref
                or receipt.dispatch_request_fingerprint_ref
                != prior.dispatch_request_fingerprint_ref
            ):
                raise MissionStepCorruptionError("MISSION_STEP_FENCE_ADVANCE_INVALID")
            return
        if receipt.generation != prior.generation:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if receipt.status == MissionStepStatus.claimed.value:
            if (
                receipt.owner_ref != prior.owner_ref
                or receipt.claim_ref != prior.claim_ref
                or receipt.claim_expires_at is None
                or prior.claim_expires_at is None
                or receipt.claim_expires_at < prior.claim_expires_at
            ):
                raise MissionStepCorruptionError("MISSION_STEP_CLAIM_BINDING_INVALID")
            return
        if receipt.status == MissionStepStatus.retry_pending.value:
            if (
                receipt.attempt_no != prior.attempt_no
                or receipt.retry_not_before is None
                or receipt.retry_not_before < receipt.checked_at
                or receipt.failure_category is None
                or receipt.dispatch_receipt_ref is None
            ):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_RETRY_PENDING_TRANSITION_INVALID"
                )
            return
        if receipt.status not in TERMINAL_MISSION_STEP_STATUSES:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")

    def _validate_persisted_success(self, receipt: MissionStepReceipt) -> None:
        if (
            receipt.dispatch_ref is None
            or receipt.dispatch_request_fingerprint_ref is None
            or receipt.dispatch_receipt_ref is None
            or receipt.dispatch_entry_hash_ref is None
            or receipt.dispatch_receipt_ref not in receipt.evidence_refs
            or receipt.dispatch_entry_hash_ref not in receipt.evidence_refs
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_EVIDENCE_INVALID"
            )
        self._validate_persisted_dispatch(receipt)

    def _validate_persisted_dispatch(self, receipt: MissionStepReceipt) -> None:
        if (
            receipt.dispatch_ref is None
            or receipt.dispatch_receipt_ref is None
            or receipt.dispatch_entry_hash_ref is None
            or receipt.dispatch_receipt_ref not in receipt.evidence_refs
            or receipt.dispatch_entry_hash_ref not in receipt.evidence_refs
            or self._dispatch_receipt_resolver is None
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_EVIDENCE_INVALID")
        durable = self._dispatch_receipt_resolver(receipt.dispatch_ref)
        if (
            durable is None
            or durable.receipt_ref != receipt.dispatch_receipt_ref
            or durable.entry_hash_ref != receipt.dispatch_entry_hash_ref
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_NOT_DURABLE"
            )
        try:
            self._validate_durable_dispatch(receipt, durable)
            if receipt.status == MissionStepStatus.succeeded.value:
                self._validate_succeeded_dispatch(receipt, durable)
            expected_statuses = {
                MissionStepStatus.failed.value: {
                    AuthorityDispatchStatus.failed.value,
                    AuthorityDispatchStatus.denied.value,
                    AuthorityDispatchStatus.cancelled_before_start.value,
                },
                MissionStepStatus.cancelled.value: {
                    AuthorityDispatchStatus.cancelled_before_start.value,
                },
                MissionStepStatus.recovery_required.value: {
                    AuthorityDispatchStatus.started.value,
                    AuthorityDispatchStatus.cancellation_pending.value,
                },
                MissionStepStatus.dead_lettered.value: {
                    AuthorityDispatchStatus.failed.value,
                },
            }.get(receipt.status)
            if (
                expected_statuses is not None
                and durable.status not in expected_statuses
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_TERMINAL_DISPATCH_STATUS_INVALID"
                )
        except MissionStepConflictError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_BINDING_INVALID"
            ) from exc
