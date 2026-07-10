from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_REDACTIONS,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


AUTHORITY_BUDGET_SCHEMA_VERSION = "uaa-authority-budget-ledger.v1"


class AuthorityBudgetOperation(str, Enum):
    reserve = "reserve"
    settle = "settle"
    release = "release"


class AuthorityBudgetStatus(str, Enum):
    reserved = "reserved"
    settled = "settled"
    settled_overage = "settled_overage"
    settled_cost_unresolved = "settled_cost_unresolved"
    released = "released"
    denied = "denied"
    replayed = "replayed"


class AuthorityBudgetExecutionStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    cancelled_after_start = "cancelled_after_start"


class _AuthorityBudgetContract(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class AuthorityBudgetReceipt(_AuthorityBudgetContract):
    schema_version: Literal["uaa-authority-budget-ledger.v1"] = (
        AUTHORITY_BUDGET_SCHEMA_VERSION
    )
    operation: AuthorityBudgetOperation
    status: AuthorityBudgetStatus
    original_status: AuthorityBudgetStatus | None = None
    receipt_ref: str = Field(..., min_length=1)
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    request_fingerprint_ref: str = Field(..., min_length=1)
    lease_ref: str | None = None
    action_ref: str | None = None
    authority_decision_ref: str | None = None
    authority_policy_receipt_ref: str | None = None
    cost_estimate_ref: str | None = None
    cost_governor_decision_ref: str | None = None
    cost_governor_allowed: StrictBool = False
    reserved_operation_count: StrictInt = Field(default=0, ge=0)
    reserved_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    actual_operation_count: StrictInt | None = Field(default=None, ge=0)
    actual_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    actual_cost_ref: str | None = None
    remaining_operation_count: StrictInt | None = Field(default=None, ge=0)
    remaining_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    execution_status: AuthorityBudgetExecutionStatus | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    audit_ref: str = Field(..., min_length=1)
    rollback_ref: str = "rollback-ref:authority-budget-release-before-execution"
    safe_disable_ref: str = "safe-disable-ref:authority-budget-deny-new-reservations"
    kill_switch_ref: str = "kill-switch-ref:authority-lease-local"
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    execution_performed_by_budget_store: StrictBool = False
    raw_paths_included: StrictBool = False
    raw_prompt_included: StrictBool = False
    raw_response_included: StrictBool = False
    raw_provider_payload_included: StrictBool = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> "AuthorityBudgetReceipt":
        for value, field_name in [
            (self.receipt_ref, "authority_budget_receipt_ref"),
            (self.reservation_ref, "authority_budget_reservation_ref"),
            (self.idempotency_ref, "authority_budget_idempotency_ref"),
            (self.request_fingerprint_ref, "authority_budget_request_fingerprint_ref"),
            (self.lease_ref, "authority_budget_lease_ref"),
            (self.action_ref, "authority_budget_action_ref"),
            (self.authority_decision_ref, "authority_budget_decision_ref"),
            (
                self.authority_policy_receipt_ref,
                "authority_budget_policy_receipt_ref",
            ),
            (self.cost_estimate_ref, "authority_budget_cost_estimate_ref"),
            (
                self.cost_governor_decision_ref,
                "authority_budget_cost_governor_decision_ref",
            ),
            (self.actual_cost_ref, "authority_budget_actual_cost_ref"),
            (self.audit_ref, "authority_budget_audit_ref"),
            (self.rollback_ref, "authority_budget_rollback_ref"),
            (self.safe_disable_ref, "authority_budget_safe_disable_ref"),
            (self.kill_switch_ref, "authority_budget_kill_switch_ref"),
            (self.previous_entry_hash_ref, "authority_budget_previous_hash_ref"),
            (self.entry_hash_ref, "authority_budget_entry_hash_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for ref in [*self.evidence_refs, *self.reason_refs]:
            validate_task_ref(ref, "authority_budget_safe_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_budget_redaction")
        if not set(AUTHORITY_STATE_REDACTIONS).issubset(self.redactions_applied):
            raise ValueError("AUTHORITY_BUDGET_REQUIRED_REDACTIONS_MISSING")
        if self.execution_performed_by_budget_store:
            raise ValueError("AUTHORITY_BUDGET_STORE_MUST_NOT_EXECUTE")
        if any(
            [
                self.raw_paths_included,
                self.raw_prompt_included,
                self.raw_response_included,
                self.raw_provider_payload_included,
            ]
        ):
            raise ValueError("AUTHORITY_BUDGET_RECEIPT_MUST_BE_REDACTED")
        if (
            self.status == AuthorityBudgetStatus.replayed.value
            and not self.original_status
        ):
            raise ValueError("AUTHORITY_BUDGET_REPLAY_ORIGINAL_STATUS_REQUIRED")
        if (
            self.status != AuthorityBudgetStatus.replayed.value
            and self.original_status is not None
        ):
            raise ValueError("AUTHORITY_BUDGET_ORIGINAL_STATUS_ONLY_FOR_REPLAY")
        if self.original_status == AuthorityBudgetStatus.replayed.value:
            raise ValueError("AUTHORITY_BUDGET_NESTED_REPLAY_FORBIDDEN")
        semantic_status = self.original_status or self.status
        allowed_statuses = {
            AuthorityBudgetOperation.reserve.value: {
                AuthorityBudgetStatus.reserved.value,
                AuthorityBudgetStatus.denied.value,
            },
            AuthorityBudgetOperation.settle.value: {
                AuthorityBudgetStatus.settled.value,
                AuthorityBudgetStatus.settled_overage.value,
                AuthorityBudgetStatus.settled_cost_unresolved.value,
                AuthorityBudgetStatus.denied.value,
            },
            AuthorityBudgetOperation.release.value: {
                AuthorityBudgetStatus.released.value,
                AuthorityBudgetStatus.denied.value,
            },
        }
        if semantic_status not in allowed_statuses[self.operation]:
            raise ValueError("AUTHORITY_BUDGET_OPERATION_STATUS_INVALID")
        if self.operation == AuthorityBudgetOperation.reserve.value and (
            not self.lease_ref
            or not self.action_ref
            or not self.authority_decision_ref
            or not self.cost_estimate_ref
            or not self.cost_governor_decision_ref
        ):
            raise ValueError("AUTHORITY_BUDGET_RESERVE_BINDING_REQUIRED")
        if semantic_status == AuthorityBudgetStatus.denied.value:
            if not self.reason_refs:
                raise ValueError("AUTHORITY_BUDGET_DENIAL_REASON_REQUIRED")
            if (
                any(
                    value is not None
                    for value in [
                        self.reserved_cost_microusd,
                        self.actual_operation_count,
                        self.actual_cost_microusd,
                        self.actual_cost_ref,
                        self.execution_status,
                    ]
                )
                or self.reserved_operation_count != 0
            ):
                raise ValueError("AUTHORITY_BUDGET_DENIAL_MUST_NOT_CONSUME")
        elif (
            not self.lease_ref
            or not self.action_ref
            or not self.cost_estimate_ref
            or not self.cost_governor_decision_ref
            or not self.cost_governor_allowed
        ):
            raise ValueError("AUTHORITY_BUDGET_ACTIVE_RECEIPT_BINDING_REQUIRED")
        elif self.reserved_operation_count < 1 or self.reserved_cost_microusd is None:
            raise ValueError("AUTHORITY_BUDGET_RESERVATION_VALUES_REQUIRED")
        elif semantic_status == AuthorityBudgetStatus.reserved.value:
            if (
                not self.authority_decision_ref
                or not self.authority_policy_receipt_ref
                or self.actual_operation_count is not None
                or self.actual_cost_microusd is not None
                or self.actual_cost_ref is not None
                or self.execution_status is not None
            ):
                raise ValueError("AUTHORITY_BUDGET_RESERVATION_BINDING_INVALID")
        elif semantic_status == AuthorityBudgetStatus.released.value:
            if not self.reason_refs:
                raise ValueError("AUTHORITY_BUDGET_RELEASE_REASON_REQUIRED")
            if (
                self.actual_operation_count is not None
                or self.actual_cost_microusd is not None
                or self.actual_cost_ref is not None
                or self.execution_status is not None
            ):
                raise ValueError("AUTHORITY_BUDGET_RELEASE_MUST_PRECEDE_EXECUTION")
        elif (
            self.actual_operation_count is None
            or self.actual_operation_count < 1
            or self.execution_status is None
            or not self.evidence_refs
        ):
            raise ValueError("AUTHORITY_BUDGET_SETTLEMENT_ACTUALS_REQUIRED")
        elif (
            semantic_status == AuthorityBudgetStatus.settled_cost_unresolved.value
            and (
                self.actual_cost_microusd is not None
                or self.actual_cost_ref is not None
            )
        ) or (
            semantic_status != AuthorityBudgetStatus.settled_cost_unresolved.value
            and (self.actual_cost_microusd is None or self.actual_cost_ref is None)
        ):
            raise ValueError("AUTHORITY_BUDGET_SETTLEMENT_COST_STATUS_INVALID")
        if (
            semantic_status == AuthorityBudgetStatus.settled_overage.value
            and "reason-ref:authority-budget:settlement-overage" not in self.reason_refs
        ):
            raise ValueError("AUTHORITY_BUDGET_OVERAGE_REASON_REQUIRED")
        if (
            semantic_status == AuthorityBudgetStatus.settled_cost_unresolved.value
            and "reason-ref:authority-budget:actual-cost-unresolved"
            not in self.reason_refs
        ):
            raise ValueError("AUTHORITY_BUDGET_UNRESOLVED_COST_REASON_REQUIRED")
        return self


class AuthorityBudgetLeaseSummary(_AuthorityBudgetContract):
    lease_ref: str
    operation_limit: StrictInt | None = Field(default=None, ge=0)
    cost_limit_microusd: StrictInt | None = Field(default=None, ge=0)
    allocated_operation_count: StrictInt = Field(default=0, ge=0)
    allocated_cost_microusd: StrictInt = Field(default=0, ge=0)
    remaining_operation_count: StrictInt | None = Field(default=None, ge=0)
    remaining_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    active_reservation_count: StrictInt = Field(default=0, ge=0)
    settled_reservation_count: StrictInt = Field(default=0, ge=0)
    unresolved_cost: StrictBool = False
    exhausted: StrictBool = False
    blocked_reason_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_summary(self) -> "AuthorityBudgetLeaseSummary":
        validate_task_ref(self.lease_ref, "authority_budget_lease_ref")
        for ref in self.blocked_reason_refs:
            validate_task_ref(ref, "authority_budget_reason_ref")
        for limit, allocated, remaining in [
            (
                self.operation_limit,
                self.allocated_operation_count,
                self.remaining_operation_count,
            ),
            (
                self.cost_limit_microusd,
                self.allocated_cost_microusd,
                self.remaining_cost_microusd,
            ),
        ]:
            expected_remaining = None if limit is None else max(0, limit - allocated)
            if remaining != expected_remaining:
                raise ValueError("AUTHORITY_BUDGET_REMAINING_CAPACITY_INVALID")
        expected_exhausted = bool(
            self.operation_limit is None
            or self.cost_limit_microusd is None
            or self.allocated_operation_count >= self.operation_limit
            or self.allocated_cost_microusd >= self.cost_limit_microusd
            or self.unresolved_cost
        )
        if self.exhausted != expected_exhausted:
            raise ValueError("AUTHORITY_BUDGET_EXHAUSTED_POSTURE_INVALID")
        if self.exhausted and (
            "reason-ref:authority-budget:budget-exhausted"
            not in self.blocked_reason_refs
        ):
            raise ValueError("AUTHORITY_BUDGET_EXHAUSTED_REASON_REQUIRED")
        return self


class AuthorityBudgetReadModel(_AuthorityBudgetContract):
    schema_version: Literal["uaa-authority-budget-read-model.v1"] = (
        "uaa-authority-budget-read-model.v1"
    )
    ledger_ref: str = "ledger-ref:authority-budget-receipts"
    lease_summaries: list[AuthorityBudgetLeaseSummary] = Field(default_factory=list)
    recent_receipts: list[AuthorityBudgetReceipt] = Field(default_factory=list)
    receipt_count: StrictInt = Field(default=0, ge=0)
    execution_performed: StrictBool = False
    mutation_available_from_read_model: StrictBool = False
    safe_summary: str = (
        "Authority budget posture is derived from append-first safe-ref receipts."
    )

    @model_validator(mode="after")
    def validate_read_model(self) -> "AuthorityBudgetReadModel":
        validate_task_ref(self.ledger_ref, "authority_budget_ledger_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        if self.execution_performed or self.mutation_available_from_read_model:
            raise ValueError("AUTHORITY_BUDGET_READ_MODEL_MUST_NOT_MUTATE")
        if self.receipt_count < len(self.recent_receipts):
            raise ValueError("AUTHORITY_BUDGET_RECEIPT_COUNT_INVALID")
        return self
