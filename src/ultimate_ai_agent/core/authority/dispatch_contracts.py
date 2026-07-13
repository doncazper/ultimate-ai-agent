from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_REDACTIONS,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDomain,
)
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


AUTHORITY_DISPATCH_SCHEMA_VERSION = "uaa-authority-dispatch.v1"


class AuthorityDispatchStatus(str, Enum):
    prepared = "prepared"
    cancellation_pending = "cancellation_pending"
    started = "started"
    succeeded = "succeeded"
    failed = "failed"
    denied = "denied"
    cancelled_before_start = "cancelled_before_start"


class AuthorityDispatchFailureCategory(str, Enum):
    transient_adapter_error = "transient_adapter_error"
    resource_temporarily_unavailable = "resource_temporarily_unavailable"
    permanent_adapter_error = "permanent_adapter_error"


class _AuthorityDispatchModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class AuthorityDispatchAdapterDescriptor(_AuthorityDispatchModel):
    adapter_ref: str
    domain: AuthorityDomain
    capability: AuthorityCapability
    capability_ref: str
    tool_ref: str
    approval_required: StrictBool = False
    atomic_start_required: StrictBool = False
    operation_count: StrictInt = Field(default=1, ge=1)
    estimated_cost_microusd: StrictInt = Field(default=0, ge=0)
    failure_cost_microusd: StrictInt | None = Field(default=0, ge=0)
    cancellation_before_start_supported: Literal[True] = True
    cancellation_after_start_supported: Literal[False] = False
    idempotent_replay_supported: StrictBool = False
    rollback_ref: str
    safe_disable_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_descriptor(self) -> "AuthorityDispatchAdapterDescriptor":
        for value, field_name in [
            (self.adapter_ref, "authority_dispatch_adapter_ref"),
            (self.capability_ref, "authority_dispatch_capability_ref"),
            (self.tool_ref, "authority_dispatch_tool_ref"),
            (self.rollback_ref, "authority_dispatch_rollback_ref"),
            (self.safe_disable_ref, "authority_dispatch_safe_disable_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(str(self.domain), "authority_dispatch_domain")
        validate_safe_task_text(str(self.capability), "authority_dispatch_capability")
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        return self


class AuthorityDispatchRequest(_AuthorityDispatchModel):
    dispatch_ref: str
    run_ref: str
    idempotency_ref: str
    lease_ref: str
    adapter_ref: str
    action_request: AuthorityActionRequest
    tool_invocation_request: dict[str, Any]
    operation_count: StrictInt = Field(default=1, ge=1)
    estimated_cost_microusd: StrictInt | None = Field(default=0, ge=0)
    cost_estimate: CostEstimate
    cost_budgets: list[CostBudget] = Field(..., min_length=1)
    cost_estimate_ref: str
    cost_governor_decision_ref: str
    cost_governor_allowed: StrictBool
    approval_validation_request: ApprovalValidationRequest | None = None
    start_deadline: datetime | None = None
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityDispatchRequest":
        for value, field_name in [
            (self.dispatch_ref, "authority_dispatch_ref"),
            (self.run_ref, "authority_dispatch_run_ref"),
            (self.idempotency_ref, "authority_dispatch_idempotency_ref"),
            (self.lease_ref, "authority_dispatch_lease_ref"),
            (self.adapter_ref, "authority_dispatch_adapter_ref"),
            (self.cost_estimate_ref, "authority_dispatch_cost_estimate_ref"),
            (
                self.cost_governor_decision_ref,
                "authority_dispatch_cost_governor_decision_ref",
            ),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        if self.start_deadline is not None and self.start_deadline.tzinfo is None:
            raise ValueError("AUTHORITY_DISPATCH_START_DEADLINE_TIMEZONE_REQUIRED")
        if self.action_request.adapter_ref != self.adapter_ref:
            raise ValueError("AUTHORITY_DISPATCH_ACTION_ADAPTER_MISMATCH")
        tool_ref = self.tool_invocation_request.get("tool_ref")
        if not isinstance(tool_ref, str):
            raise ValueError("AUTHORITY_DISPATCH_TOOL_REF_REQUIRED")
        validate_task_ref(tool_ref, "authority_dispatch_tool_ref")
        tool_summary = self.tool_invocation_request.get("safe_summary")
        if not isinstance(tool_summary, str):
            raise ValueError("AUTHORITY_DISPATCH_TOOL_SUMMARY_REQUIRED")
        validate_safe_task_text(tool_summary, "authority_dispatch_tool_summary")
        if self.tool_invocation_request.get("invocation_id") != self.dispatch_ref:
            raise ValueError("AUTHORITY_DISPATCH_INVOCATION_REF_MISMATCH")
        if self.tool_invocation_request.get("replay_key") != self.idempotency_ref:
            raise ValueError("AUTHORITY_DISPATCH_REPLAY_KEY_MISMATCH")
        if self.tool_invocation_request.get("approval_ref") is not None:
            raise ValueError("AUTHORITY_DISPATCH_TOOL_APPROVAL_REF_FORBIDDEN")
        if self.tool_invocation_request.get("authority_refs"):
            raise ValueError("AUTHORITY_DISPATCH_TOOL_AUTHORITY_REFS_FORBIDDEN")
        if self.approval_validation_request is not None and (
            self.approval_validation_request.run_id != self.run_ref
        ):
            raise ValueError("AUTHORITY_DISPATCH_APPROVAL_RUN_MISMATCH")
        if (
            self.approval_validation_request is not None
            and self.approval_validation_request.current_time is not None
        ):
            raise ValueError("AUTHORITY_DISPATCH_CALLER_APPROVAL_TIME_FORBIDDEN")
        return self


class AuthorityDispatchWorkerClaimFence(_AuthorityDispatchModel):
    job_ref: str
    worker_ref: str
    job_claim_ref: str
    job_generation: StrictInt = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_fence(self) -> "AuthorityDispatchWorkerClaimFence":
        for value in (self.job_ref, self.worker_ref, self.job_claim_ref):
            validate_task_ref(value, "authority_dispatch_worker_claim_fence_ref")
        return self


class AuthorityDispatchExecutionFence(AuthorityDispatchWorkerClaimFence):
    step_ref: str
    step_claim_ref: str
    step_generation: StrictInt = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_execution_fence(self) -> "AuthorityDispatchExecutionFence":
        validate_task_ref(self.step_ref, "authority_dispatch_step_fence_ref")
        validate_task_ref(
            self.step_claim_ref,
            "authority_dispatch_step_claim_fence_ref",
        )
        return self


class AuthorityDispatchCancelRequest(_AuthorityDispatchModel):
    dispatch_ref: str
    idempotency_ref: str
    reason_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityDispatchCancelRequest":
        for value, field_name in [
            (self.dispatch_ref, "authority_dispatch_ref"),
            (self.idempotency_ref, "authority_dispatch_cancel_idempotency_ref"),
            (self.reason_ref, "authority_dispatch_cancel_reason_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        return self


class AuthorityDispatchAdapterResult(_AuthorityDispatchModel):
    execution_ref: str
    succeeded: StrictBool
    failure_category: AuthorityDispatchFailureCategory | None = None
    actual_operation_count: StrictInt = Field(default=1, ge=1)
    actual_cost_microusd: StrictInt | None = Field(default=0, ge=0)
    actual_cost_ref: str | None = None
    evidence_refs: list[str] = Field(..., min_length=1)
    output_refs: list[str] = Field(default_factory=list)
    safe_output: dict[str, Any] = Field(default_factory=dict)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    raw_paths_included: Literal[False] = False
    raw_prompt_included: Literal[False] = False
    raw_response_included: Literal[False] = False
    raw_provider_payload_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "AuthorityDispatchAdapterResult":
        for value, field_name in [
            (self.execution_ref, "authority_dispatch_execution_ref"),
            (self.actual_cost_ref, "authority_dispatch_actual_cost_ref"),
            *[(ref, "authority_dispatch_evidence_ref") for ref in self.evidence_refs],
            *[(ref, "authority_dispatch_output_ref") for ref in self.output_refs],
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        if (self.actual_cost_microusd is None) != (self.actual_cost_ref is None):
            raise ValueError("AUTHORITY_DISPATCH_ACTUAL_COST_BINDING_INVALID")
        validate_safe_task_payload(self.safe_output, "authority_dispatch_safe_output")
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        if self.succeeded and self.failure_category is not None:
            raise ValueError("AUTHORITY_DISPATCH_SUCCESS_FAILURE_CATEGORY_FORBIDDEN")
        return self


class AuthorityDispatchReceipt(_AuthorityDispatchModel):
    schema_version: Literal["uaa-authority-dispatch.v1"] = (
        AUTHORITY_DISPATCH_SCHEMA_VERSION
    )
    status: AuthorityDispatchStatus
    receipt_ref: str
    dispatch_ref: str
    run_ref: str
    idempotency_ref: str
    request_fingerprint_ref: str
    start_deadline: datetime | None = None
    start_validated_at: datetime | None = None
    lease_ref: str
    action_ref: str
    adapter_ref: str
    adapter_binding_ref: str | None
    capability_ref: str
    provider_ref: str | None = None
    target_binding_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    authority_decision_ref: str | None = None
    authority_policy_receipt_ref: str | None = None
    approval_required: StrictBool = False
    adapter_approval_required: StrictBool = False
    atomic_start_required: StrictBool = False
    approval_ref: str | None = None
    approval_validation_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_reservation_receipt_ref: str | None = None
    budget_start_receipt_ref: str | None = None
    budget_settlement_receipt_ref: str | None = None
    budget_release_receipt_ref: str | None = None
    cancellation_idempotency_ref: str | None = None
    cancellation_reason_ref: str | None = None
    execution_ref: str | None = None
    execution_fence_ref: str | None = None
    execution_started: StrictBool = False
    adapter_start_attempted: StrictBool = False
    runtime_start_confirmed: StrictBool = False
    input_committed: StrictBool = False
    adapter_invocation_performed: StrictBool = False
    result_collection_performed: StrictBool = False
    actual_operation_count: StrictInt | None = Field(default=None, ge=1)
    actual_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    actual_cost_ref: str | None = None
    failure_category: AuthorityDispatchFailureCategory | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    rollback_ref: str
    safe_disable_ref: str
    audit_ref: str
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=520)
    raw_paths_included: Literal[False] = False
    raw_prompt_included: Literal[False] = False
    raw_response_included: Literal[False] = False
    raw_provider_payload_included: Literal[False] = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> "AuthorityDispatchReceipt":
        refs = [
            self.receipt_ref,
            self.dispatch_ref,
            self.run_ref,
            self.idempotency_ref,
            self.request_fingerprint_ref,
            self.lease_ref,
            self.action_ref,
            self.adapter_ref,
            self.adapter_binding_ref,
            self.capability_ref,
            self.provider_ref,
            self.target_binding_ref,
            self.approval_scope_fingerprint_ref,
            self.authority_decision_ref,
            self.authority_policy_receipt_ref,
            self.approval_ref,
            self.approval_validation_ref,
            self.budget_reservation_ref,
            self.budget_reservation_receipt_ref,
            self.budget_start_receipt_ref,
            self.budget_settlement_receipt_ref,
            self.budget_release_receipt_ref,
            self.cancellation_idempotency_ref,
            self.cancellation_reason_ref,
            self.execution_ref,
            self.execution_fence_ref,
            self.actual_cost_ref,
            self.rollback_ref,
            self.safe_disable_ref,
            self.audit_ref,
            self.previous_entry_hash_ref,
            self.entry_hash_ref,
            *self.evidence_refs,
            *self.output_refs,
            *self.reason_refs,
        ]
        for ref in refs:
            if ref is not None:
                validate_task_ref(ref, "authority_dispatch_receipt_ref")
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        if self.start_deadline is not None and self.start_deadline.tzinfo is None:
            raise ValueError("AUTHORITY_DISPATCH_START_DEADLINE_TIMEZONE_REQUIRED")
        if (
            self.start_validated_at is not None
            and self.start_validated_at.tzinfo is None
        ):
            raise ValueError("AUTHORITY_DISPATCH_START_VALIDATION_TIMEZONE_REQUIRED")
        if not set(AUTHORITY_STATE_REDACTIONS).issubset(self.redactions_applied):
            raise ValueError("AUTHORITY_DISPATCH_REQUIRED_REDACTIONS_MISSING")
        if (
            self.approval_required
            and self.status
            not in {
                AuthorityDispatchStatus.denied.value,
            }
            and (not self.approval_ref or not self.approval_validation_ref)
        ):
            raise ValueError("AUTHORITY_DISPATCH_REQUIRED_APPROVAL_BINDING_MISSING")
        if self.adapter_approval_required and not self.approval_required:
            raise ValueError("AUTHORITY_DISPATCH_ADAPTER_APPROVAL_POSTURE_INVALID")
        if self.input_committed and not self.runtime_start_confirmed:
            raise ValueError("AUTHORITY_DISPATCH_INPUT_COMMIT_REQUIRES_RUNTIME_START")
        if self.result_collection_performed and not self.adapter_invocation_performed:
            raise ValueError("AUTHORITY_DISPATCH_COLLECTION_REQUIRES_INVOCATION")
        if self.status == AuthorityDispatchStatus.denied.value:
            if (
                self.execution_started
                or self.adapter_start_attempted
                or self.adapter_invocation_performed
                or self.result_collection_performed
                or not self.reason_refs
            ):
                raise ValueError("AUTHORITY_DISPATCH_DENIAL_POSTURE_INVALID")
        elif (
            not self.adapter_binding_ref
            or not self.budget_reservation_ref
            or not self.budget_reservation_receipt_ref
        ):
            raise ValueError("AUTHORITY_DISPATCH_BUDGET_RESERVATION_BINDING_REQUIRED")
        if self.status in {
            AuthorityDispatchStatus.prepared.value,
            AuthorityDispatchStatus.cancellation_pending.value,
            AuthorityDispatchStatus.cancelled_before_start.value,
        } and (
            self.execution_started
            or self.adapter_start_attempted
            or self.runtime_start_confirmed
            or self.input_committed
            or self.adapter_invocation_performed
            or self.result_collection_performed
        ):
            raise ValueError("AUTHORITY_DISPATCH_PRESTART_EXECUTION_FORBIDDEN")
        if self.status in {
            AuthorityDispatchStatus.cancellation_pending.value,
            AuthorityDispatchStatus.cancelled_before_start.value,
        } and (
            not self.cancellation_idempotency_ref or not self.cancellation_reason_ref
        ):
            raise ValueError("AUTHORITY_DISPATCH_CANCELLATION_BINDING_REQUIRED")
        if self.status == AuthorityDispatchStatus.cancelled_before_start.value and (
            not self.budget_release_receipt_ref or not self.reason_refs
        ):
            raise ValueError("AUTHORITY_DISPATCH_CANCELLATION_RELEASE_REQUIRED")
        if self.status == AuthorityDispatchStatus.started.value and (
            not self.execution_started
            or self.adapter_invocation_performed
            or not self.execution_ref
            or not self.budget_start_receipt_ref
            or (self.start_deadline is not None and self.start_validated_at is None)
        ):
            raise ValueError("AUTHORITY_DISPATCH_STARTED_POSTURE_INVALID")
        if (
            self.status == AuthorityDispatchStatus.started.value
            and not self.atomic_start_required
            and (self.runtime_start_confirmed or self.input_committed)
        ):
            raise ValueError(
                "AUTHORITY_DISPATCH_NONATOMIC_START_CONFIRMATION_FORBIDDEN"
            )
        if self.status in {
            AuthorityDispatchStatus.succeeded.value,
            AuthorityDispatchStatus.failed.value,
        } and (
            not self.execution_started
            or not self.execution_ref
            or not self.budget_start_receipt_ref
            or not self.budget_settlement_receipt_ref
            or self.actual_operation_count is None
            or not self.evidence_refs
            or (self.start_deadline is not None and self.start_validated_at is None)
        ):
            raise ValueError("AUTHORITY_DISPATCH_TERMINAL_EVIDENCE_REQUIRED")
        if self.status == AuthorityDispatchStatus.succeeded.value and (
            not self.adapter_invocation_performed
            or (self.atomic_start_required and not self.result_collection_performed)
        ):
            raise ValueError("AUTHORITY_DISPATCH_SUCCESS_INVOCATION_EVIDENCE_REQUIRED")
        if (
            self.status == AuthorityDispatchStatus.failed.value
            and not self.adapter_invocation_performed
            and not (
                self.atomic_start_required
                and self.adapter_start_attempted
                and not self.runtime_start_confirmed
                and not self.input_committed
                and not self.result_collection_performed
            )
        ):
            raise ValueError("AUTHORITY_DISPATCH_FAILURE_INVOCATION_POSTURE_INVALID")
        if (
            self.status == AuthorityDispatchStatus.succeeded.value
            and self.atomic_start_required
            and (not self.runtime_start_confirmed or not self.input_committed)
        ):
            raise ValueError("AUTHORITY_DISPATCH_ATOMIC_START_CONFIRMATION_REQUIRED")
        if not self.execution_started and self.start_validated_at is not None:
            raise ValueError("AUTHORITY_DISPATCH_PRESTART_VALIDATION_TIME_FORBIDDEN")
        if (
            self.start_deadline is not None
            and self.start_validated_at is not None
            and self.start_validated_at >= self.start_deadline
        ):
            raise ValueError("AUTHORITY_DISPATCH_START_AFTER_DEADLINE_FORBIDDEN")
        if (self.actual_cost_microusd is None) != (self.actual_cost_ref is None):
            raise ValueError("AUTHORITY_DISPATCH_ACTUAL_COST_BINDING_INVALID")
        if (
            self.status == AuthorityDispatchStatus.succeeded.value
            and self.failure_category is not None
        ):
            raise ValueError("AUTHORITY_DISPATCH_SUCCESS_FAILURE_CATEGORY_FORBIDDEN")
        return self


class AuthorityDispatchResult(_AuthorityDispatchModel):
    receipt: AuthorityDispatchReceipt
    replayed: StrictBool = False
    recovery_required: StrictBool = False
    adapter_result: AuthorityDispatchAdapterResult | None = None

    @model_validator(mode="after")
    def validate_result(self) -> "AuthorityDispatchResult":
        if self.recovery_required != (
            self.receipt.status
            in {
                AuthorityDispatchStatus.started.value,
                AuthorityDispatchStatus.cancellation_pending.value,
            }
        ):
            raise ValueError("AUTHORITY_DISPATCH_RECOVERY_POSTURE_INVALID")
        if self.adapter_result is not None and self.receipt.status not in {
            AuthorityDispatchStatus.succeeded.value,
            AuthorityDispatchStatus.failed.value,
        }:
            raise ValueError("AUTHORITY_DISPATCH_ADAPTER_RESULT_TERMINAL_ONLY")
        return self


class AuthorityDispatchReadModel(_AuthorityDispatchModel):
    schema_version: Literal["uaa-authority-dispatch-read-model.v1"] = (
        "uaa-authority-dispatch-read-model.v1"
    )
    ledger_ref: str = "ledger-ref:authority-dispatch-receipts"
    latest_receipts: list[AuthorityDispatchReceipt] = Field(default_factory=list)
    receipt_count: StrictInt = Field(default=0, ge=0)
    recovery_required_dispatch_refs: list[str] = Field(default_factory=list)
    execution_performed: Literal[False] = False
    mutation_available_from_read_model: Literal[False] = False
    safe_summary: str = (
        "Governed dispatch posture is derived from append-first receipts."
    )

    @model_validator(mode="after")
    def validate_read_model(self) -> "AuthorityDispatchReadModel":
        validate_task_ref(self.ledger_ref, "authority_dispatch_ledger_ref")
        for ref in self.recovery_required_dispatch_refs:
            validate_task_ref(ref, "authority_dispatch_recovery_ref")
        validate_safe_task_text(self.safe_summary, "authority_dispatch_summary")
        if self.receipt_count < len(self.latest_receipts):
            raise ValueError("AUTHORITY_DISPATCH_RECEIPT_COUNT_INVALID")
        return self
