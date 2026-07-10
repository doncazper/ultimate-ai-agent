from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_BUDGET_RECEIPTS_FILE,
)
from ultimate_ai_agent.core.authority.contracts import (
    AUTHORITY_STATE_LOCK_KEY,
    AuthorityActionRequest,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityLease,
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
    authority_state_dir,
    authority_state_lock_manager,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.budget_contracts import (
    AUTHORITY_BUDGET_SCHEMA_VERSION as AUTHORITY_BUDGET_SCHEMA_VERSION,
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetLeaseSummary,
    AuthorityBudgetOperation,
    AuthorityBudgetReadModel,
    AuthorityBudgetReceipt,
    AuthorityBudgetStatus,
)
from ultimate_ai_agent.core.approvals.decisions import (
    ApprovalValidationDecision,
    ApprovalValidationRequest,
)
from ultimate_ai_agent.core.approvals.enums import ApprovalSubjectType
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)


class AuthorityBudgetConflictError(RuntimeError):
    """Raised when budget idempotency or ledger history is inconsistent."""


class AuthorityBudgetCorruptionError(RuntimeError):
    """Raised when the append-first budget receipt chain is invalid."""


class _AuthorityBudgetModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class AuthorityBudgetReservationRequest(_AuthorityBudgetModel):
    lease_ref: str = Field(..., min_length=1)
    action_request: AuthorityActionRequest
    operation_count: StrictInt = Field(default=1, ge=1)
    estimated_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    cost_estimate_ref: str = Field(..., min_length=1)
    cost_governor_decision_ref: str = Field(..., min_length=1)
    cost_governor_allowed: StrictBool
    approval_required: StrictBool = False
    approval_validation_request: ApprovalValidationRequest | None = None
    dispatch_fingerprint_ref: str | None = None
    idempotency_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetReservationRequest":
        validate_task_ref(self.lease_ref, "authority_budget_lease_ref")
        validate_task_ref(self.cost_estimate_ref, "authority_budget_cost_estimate_ref")
        validate_task_ref(
            self.cost_governor_decision_ref,
            "authority_budget_cost_governor_decision_ref",
        )
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        if self.dispatch_fingerprint_ref is not None:
            validate_task_ref(
                self.dispatch_fingerprint_ref,
                "authority_budget_dispatch_fingerprint_ref",
            )
        if self.approval_required and self.approval_validation_request is None:
            raise ValueError("AUTHORITY_BUDGET_APPROVAL_VALIDATION_REQUEST_REQUIRED")
        if self.approval_validation_request is not None:
            validate_task_ref(
                self.approval_validation_request.approval_ref,
                "authority_budget_approval_ref",
            )
            validate_task_ref(
                self.approval_validation_request.run_id,
                "authority_budget_approval_run_ref",
            )
            if self.approval_validation_request.current_time is not None:
                raise ValueError("AUTHORITY_BUDGET_CALLER_APPROVAL_TIME_FORBIDDEN")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


AuthorityBudgetApprovalValidator = Callable[
    [ApprovalValidationRequest], ApprovalValidationDecision
]


class AuthorityBudgetSettlementRequest(_AuthorityBudgetModel):
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    execution_ref: str | None = None
    actual_operation_count: StrictInt = Field(default=1, ge=1)
    actual_cost_microusd: StrictInt | None = Field(default=None, ge=0)
    actual_cost_ref: str | None = None
    execution_status: AuthorityBudgetExecutionStatus
    evidence_refs: list[str] = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetSettlementRequest":
        validate_task_ref(self.reservation_ref, "authority_budget_reservation_ref")
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        if self.execution_ref is not None:
            validate_task_ref(self.execution_ref, "authority_budget_execution_ref")
        if self.actual_cost_ref is not None:
            validate_task_ref(self.actual_cost_ref, "authority_budget_actual_cost_ref")
        if (self.actual_cost_microusd is None) != (self.actual_cost_ref is None):
            raise ValueError("AUTHORITY_BUDGET_ACTUAL_COST_REF_MUST_MATCH_COST")
        for ref in self.evidence_refs:
            validate_task_ref(ref, "authority_budget_evidence_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


class AuthorityBudgetStartRequest(_AuthorityBudgetModel):
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    dispatch_fingerprint_ref: str = Field(..., min_length=1)
    execution_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetStartRequest":
        validate_task_ref(self.reservation_ref, "authority_budget_reservation_ref")
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        validate_task_ref(
            self.dispatch_fingerprint_ref,
            "authority_budget_dispatch_fingerprint_ref",
        )
        validate_task_ref(self.execution_ref, "authority_budget_execution_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


class AuthorityBudgetReleaseRequest(_AuthorityBudgetModel):
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    reason_ref: str = Field(..., min_length=1)
    execution_started: StrictBool = False
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetReleaseRequest":
        validate_task_ref(self.reservation_ref, "authority_budget_reservation_ref")
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        validate_task_ref(self.reason_ref, "authority_budget_release_reason_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        if self.execution_started:
            raise ValueError("AUTHORITY_BUDGET_RELEASE_EXECUTION_ALREADY_STARTED")
        return self


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _request_fingerprint(
    operation: AuthorityBudgetOperation,
    request: AuthorityBudgetReservationRequest
    | AuthorityBudgetStartRequest
    | AuthorityBudgetSettlementRequest
    | AuthorityBudgetReleaseRequest,
) -> str:
    return _stable_ref(
        "request-fingerprint-ref:authority-budget",
        {"operation": operation.value, "request": request.model_dump(mode="json")},
    )


def _legacy_reservation_request_fingerprint(
    request: AuthorityBudgetReservationRequest,
) -> str | None:
    if (
        request.approval_required
        or request.approval_validation_request is not None
        or request.dispatch_fingerprint_ref is not None
    ):
        return None
    return _stable_ref(
        "request-fingerprint-ref:authority-budget",
        {
            "operation": AuthorityBudgetOperation.reserve.value,
            "request": request.model_dump(
                mode="json",
                exclude={
                    "approval_required",
                    "approval_validation_request",
                    "dispatch_fingerprint_ref",
                },
            ),
        },
    )


def _legacy_settlement_request_fingerprint(
    request: AuthorityBudgetSettlementRequest,
) -> str | None:
    if request.execution_ref is not None:
        return None
    return _stable_ref(
        "request-fingerprint-ref:authority-budget",
        {
            "operation": AuthorityBudgetOperation.settle.value,
            "request": request.model_dump(mode="json", exclude={"execution_ref"}),
        },
    )


def _entry_hash(receipt: AuthorityBudgetReceipt) -> str:
    return _stable_ref(
        "entry-hash-ref:authority-budget",
        receipt.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


def _entry_hash_payload(payload: dict[str, Any]) -> str:
    return _stable_ref(
        "entry-hash-ref:authority-budget",
        {key: value for key, value in payload.items() if key != "entry_hash_ref"},
    )


def _constraint_maximum(
    lease: AuthorityLease, kind: AuthorityConstraintKind
) -> int | None:
    for constraint in lease.authority_constraints:
        if constraint.kind == kind.value:
            return constraint.maximum
    return None


def _claim_value(
    action: AuthorityActionRequest, kind: AuthorityConstraintKind
) -> int | None:
    for claim in action.constraint_claims:
        if claim.kind == kind.value:
            return claim.value
    return None


class AuthorityBudgetStore:
    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        lease_store: AuthorityLeaseStore | None = None,
    ) -> None:
        self.state_dir = state_dir or authority_state_dir()
        self.receipts_path = self.state_dir / AUTHORITY_BUDGET_RECEIPTS_FILE
        self.lease_store = lease_store or AuthorityLeaseStore(self.state_dir)
        self.lock_manager = authority_state_lock_manager(str(self.state_dir.resolve()))

    def list_receipts(self) -> list[AuthorityBudgetReceipt]:
        if not self.receipts_path.exists():
            return []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._load_receipts()

    def reserve(
        self,
        request: AuthorityBudgetReservationRequest,
        *,
        approval_validator: AuthorityBudgetApprovalValidator | None = None,
    ) -> AuthorityBudgetReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            replay = self._replay_or_conflict(
                receipts,
                AuthorityBudgetOperation.reserve,
                request.idempotency_ref,
                _request_fingerprint(AuthorityBudgetOperation.reserve, request),
                compatible_fingerprint_refs={
                    fingerprint
                    for fingerprint in [
                        _legacy_reservation_request_fingerprint(request)
                    ]
                    if fingerprint is not None
                },
            )
            if replay is not None:
                return replay
            leases = self.lease_store._list_leases(active_only=True)
            lease = next(
                (item for item in leases if item.lease_ref == request.lease_ref),
                None,
            )
            decision = evaluate_authority_request(
                request.action_request,
                [lease] if lease is not None else [],
            )
            reason_refs: list[str] = []
            approval_required = bool(
                request.approval_required
                or decision.outcome == AuthorityDecisionOutcome.ask.value
            )
            approval_ref: str | None = None
            approval_validation_ref: str | None = None
            approval_allowed = not approval_required
            if request.approval_validation_request is not None:
                approval_ref = request.approval_validation_request.approval_ref
            if approval_required or request.approval_validation_request is not None:
                approval_reasons = self._approval_reason_refs(
                    request,
                    approval_validator=approval_validator,
                )
                reason_refs.extend(approval_reasons[0])
                approval_validation_ref = approval_reasons[1]
                approval_allowed = not approval_reasons[0]
            policy_allowed = decision.outcome == AuthorityDecisionOutcome.allow.value or (
                decision.outcome == AuthorityDecisionOutcome.ask.value
                and approval_allowed
            )
            if not policy_allowed:
                reason_refs.append("reason-ref:authority-budget:policy-not-allow")
            if decision.lease_ref != request.lease_ref or lease is None:
                reason_refs.append("reason-ref:authority-budget:lease-binding-mismatch")
            if authority_lease_kill_switch_engaged():
                reason_refs.append("reason-ref:authority-budget:kill-switch-engaged")

            operation_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.operation_budget)
                if lease is not None
                else None
            )
            cost_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.cost_budget_microusd)
                if lease is not None
                else None
            )
            if operation_limit is None:
                reason_refs.append(
                    "reason-ref:authority-budget:operation-budget-missing"
                )
            if cost_limit is None:
                reason_refs.append("reason-ref:authority-budget:cost-budget-missing")
            if request.estimated_cost_microusd is None:
                reason_refs.append("reason-ref:authority-budget:estimated-cost-unknown")
            if not request.cost_governor_allowed:
                reason_refs.append("reason-ref:authority-budget:cost-governor-denied")
            if (
                _claim_value(
                    request.action_request,
                    AuthorityConstraintKind.operation_budget,
                )
                != request.operation_count
            ):
                reason_refs.append(
                    "reason-ref:authority-budget:operation-claim-mismatch"
                )
            if (
                _claim_value(
                    request.action_request,
                    AuthorityConstraintKind.cost_budget_microusd,
                )
                != request.estimated_cost_microusd
            ):
                reason_refs.append("reason-ref:authority-budget:cost-claim-mismatch")

            usage = self._usage_for_lease(receipts, request.lease_ref)
            if usage["unresolved_cost"]:
                reason_refs.append("reason-ref:authority-budget:actual-cost-unresolved")
            if usage["unreviewed_overage"]:
                reason_refs.append(
                    "reason-ref:authority-budget:settlement-overage-unreviewed"
                )
            next_operations = usage["operations"] + request.operation_count
            next_cost = usage["cost"] + (request.estimated_cost_microusd or 0)
            if operation_limit is not None and next_operations > operation_limit:
                reason_refs.append(
                    "reason-ref:authority-budget:operation-budget-exhausted"
                )
            if cost_limit is not None and (
                usage["cost"] >= cost_limit or next_cost > cost_limit
            ):
                reason_refs.append("reason-ref:authority-budget:cost-budget-exhausted")

            status = (
                AuthorityBudgetStatus.denied
                if reason_refs
                else AuthorityBudgetStatus.reserved
            )
            fingerprint = _request_fingerprint(
                AuthorityBudgetOperation.reserve, request
            )
            reservation_ref = _stable_ref(
                "authority-budget-reservation-ref",
                {
                    "idempotency_ref": request.idempotency_ref,
                    "fingerprint": fingerprint,
                },
            )
            receipt = self._build_receipt(
                operation=AuthorityBudgetOperation.reserve,
                status=status,
                reservation_ref=reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                previous_entry_hash_ref=(
                    receipts[-1].entry_hash_ref if receipts else None
                ),
                lease_ref=request.lease_ref,
                action_ref=request.action_request.action_ref,
                authority_decision_ref=decision.decision_ref,
                authority_policy_receipt_ref=decision.receipt_ref,
                approval_ref=approval_ref,
                approval_validation_ref=approval_validation_ref,
                approval_required=approval_required,
                dispatch_fingerprint_ref=request.dispatch_fingerprint_ref,
                cost_estimate_ref=request.cost_estimate_ref,
                cost_governor_decision_ref=request.cost_governor_decision_ref,
                cost_governor_allowed=request.cost_governor_allowed,
                reserved_operation_count=(
                    request.operation_count
                    if status == AuthorityBudgetStatus.reserved
                    else 0
                ),
                reserved_cost_microusd=(
                    request.estimated_cost_microusd
                    if status == AuthorityBudgetStatus.reserved
                    else None
                ),
                remaining_operation_count=(
                    max(0, operation_limit - next_operations)
                    if status == AuthorityBudgetStatus.reserved
                    and operation_limit is not None
                    else None
                ),
                remaining_cost_microusd=(
                    max(0, cost_limit - next_cost)
                    if status == AuthorityBudgetStatus.reserved
                    and cost_limit is not None
                    else None
                ),
                reason_refs=list(dict.fromkeys(reason_refs)),
                safe_summary=(
                    "Authority budget reserved exact operation and cost capacity."
                    if status == AuthorityBudgetStatus.reserved
                    else "Authority budget reservation denied without execution."
                ),
            )
            self._append(receipt)
            return receipt

    def _start_dispatch(
        self,
        request: AuthorityBudgetStartRequest,
    ) -> AuthorityBudgetReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._start_locked(request)

    def _start_locked(
        self,
        request: AuthorityBudgetStartRequest,
    ) -> AuthorityBudgetReceipt:
        receipts = self._load_receipts()
        fingerprint = _request_fingerprint(AuthorityBudgetOperation.start, request)
        replay = self._replay_or_conflict(
            receipts,
            AuthorityBudgetOperation.start,
            request.idempotency_ref,
            fingerprint,
        )
        if replay is not None:
            return replay
        state = self._reservation_state(receipts, request.reservation_ref)
        if state is None or state["status"] != AuthorityBudgetStatus.reserved.value:
            receipt = self._denied_followup_receipt(
                receipts,
                operation=AuthorityBudgetOperation.start,
                reservation_ref=request.reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                reason_ref="reason-ref:authority-budget:reservation-not-active",
            )
            self._append(receipt)
            return receipt
        if (
            state["dispatch_fingerprint_ref"] is None
            or state["dispatch_fingerprint_ref"] != request.dispatch_fingerprint_ref
        ):
            receipt = self._denied_followup_receipt(
                receipts,
                operation=AuthorityBudgetOperation.start,
                reservation_ref=request.reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                reason_ref="reason-ref:authority-budget:dispatch-start-binding-mismatch",
            )
            self._append(receipt)
            return receipt
        lease = self.lease_store._lease_by_ref(state["lease_ref"])
        if lease is None or not lease.is_active() or authority_lease_kill_switch_engaged():
            receipt = self._denied_followup_receipt(
                receipts,
                operation=AuthorityBudgetOperation.start,
                reservation_ref=request.reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                reason_ref="reason-ref:authority-budget:dispatch-start-authority-inactive",
            )
            self._append(receipt)
            return receipt
        receipt = self._build_receipt(
            operation=AuthorityBudgetOperation.start,
            status=AuthorityBudgetStatus.started,
            reservation_ref=request.reservation_ref,
            idempotency_ref=request.idempotency_ref,
            request_fingerprint_ref=fingerprint,
            previous_entry_hash_ref=receipts[-1].entry_hash_ref,
            lease_ref=state["lease_ref"],
            action_ref=state["action_ref"],
            approval_ref=state["approval_ref"],
            approval_validation_ref=state["approval_validation_ref"],
            approval_required=state["approval_required"],
            dispatch_fingerprint_ref=state["dispatch_fingerprint_ref"],
            execution_ref=request.execution_ref,
            cost_estimate_ref=state["cost_estimate_ref"],
            cost_governor_decision_ref=state["cost_governor_decision_ref"],
            cost_governor_allowed=state["cost_governor_allowed"],
            reserved_operation_count=state["reserved_operations"],
            reserved_cost_microusd=state["reserved_cost"],
            safe_summary="Authority budget reservation bound to durable adapter start.",
        )
        self._append(receipt)
        return receipt

    def settle(
        self,
        request: AuthorityBudgetSettlementRequest,
    ) -> AuthorityBudgetReceipt:
        return self._settle(request, dispatcher_owned=False)

    def _settle_dispatch(
        self,
        request: AuthorityBudgetSettlementRequest,
    ) -> AuthorityBudgetReceipt:
        return self._settle(request, dispatcher_owned=True)

    def _settle(
        self,
        request: AuthorityBudgetSettlementRequest,
        *,
        dispatcher_owned: bool,
    ) -> AuthorityBudgetReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            state = self._reservation_state(receipts, request.reservation_ref)
            if (
                state is not None
                and state["dispatch_fingerprint_ref"] is not None
                and state["status"]
                in {
                    AuthorityBudgetStatus.reserved.value,
                    AuthorityBudgetStatus.started.value,
                }
                and not dispatcher_owned
            ):
                denial_idempotency_ref = _stable_ref(
                    "idempotency-ref:authority-budget-public-settle-denial",
                    {
                        "reservation_ref": request.reservation_ref,
                        "caller_idempotency_ref": request.idempotency_ref,
                    },
                )
                denial_fingerprint = _stable_ref(
                    "request-fingerprint-ref:authority-budget-public-settle-denial",
                    request.model_dump(mode="json"),
                )
                replay = self._replay_or_conflict(
                    receipts,
                    AuthorityBudgetOperation.settle,
                    denial_idempotency_ref,
                    denial_fingerprint,
                )
                if replay is not None:
                    return replay
                receipt = self._denied_followup_receipt(
                    receipts,
                    operation=AuthorityBudgetOperation.settle,
                    reservation_ref=request.reservation_ref,
                    idempotency_ref=denial_idempotency_ref,
                    request_fingerprint_ref=denial_fingerprint,
                    reason_ref=(
                        "reason-ref:authority-budget:dispatch-start-required"
                        if state["status"] == AuthorityBudgetStatus.reserved.value
                        else "reason-ref:authority-budget:dispatch-owner-required"
                    ),
                )
                self._append(receipt)
                return receipt
            fingerprint = _request_fingerprint(AuthorityBudgetOperation.settle, request)
            replay = self._replay_or_conflict(
                receipts,
                AuthorityBudgetOperation.settle,
                request.idempotency_ref,
                fingerprint,
                compatible_fingerprint_refs={
                    compatible
                    for compatible in [
                        _legacy_settlement_request_fingerprint(request)
                    ]
                    if compatible is not None
                },
            )
            if replay is not None:
                return replay
            state = self._reservation_state(receipts, request.reservation_ref)
            if state is None or state["status"] not in {
                AuthorityBudgetStatus.reserved.value,
                AuthorityBudgetStatus.started.value,
            }:
                receipt = self._denied_followup_receipt(
                    receipts,
                    operation=AuthorityBudgetOperation.settle,
                    reservation_ref=request.reservation_ref,
                    idempotency_ref=request.idempotency_ref,
                    request_fingerprint_ref=fingerprint,
                    reason_ref="reason-ref:authority-budget:reservation-not-active",
                )
                self._append(receipt)
                return receipt
            if (
                state["dispatch_fingerprint_ref"] is not None
                and state["status"] != AuthorityBudgetStatus.started.value
            ):
                receipt = self._denied_followup_receipt(
                    receipts,
                    operation=AuthorityBudgetOperation.settle,
                    reservation_ref=request.reservation_ref,
                    idempotency_ref=request.idempotency_ref,
                    request_fingerprint_ref=fingerprint,
                    reason_ref="reason-ref:authority-budget:dispatch-start-required",
                )
                self._append(receipt)
                return receipt
            if request.execution_ref != state["execution_ref"]:
                receipt = self._denied_followup_receipt(
                    receipts,
                    operation=AuthorityBudgetOperation.settle,
                    reservation_ref=request.reservation_ref,
                    idempotency_ref=request.idempotency_ref,
                    request_fingerprint_ref=fingerprint,
                    reason_ref="reason-ref:authority-budget:execution-binding-mismatch",
                )
                self._append(receipt)
                return receipt

            lease = self.lease_store._lease_by_ref(state["lease_ref"])
            operation_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.operation_budget)
                if lease is not None
                else None
            )
            cost_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.cost_budget_microusd)
                if lease is not None
                else None
            )
            usage_without = self._usage_for_lease(
                receipts,
                state["lease_ref"],
                exclude_reservation_ref=request.reservation_ref,
            )
            next_operations = (
                usage_without["operations"] + request.actual_operation_count
            )
            next_cost = usage_without["cost"] + (request.actual_cost_microusd or 0)
            reason_refs: list[str] = []
            if lease is None or not lease.is_active():
                reason_refs.append(
                    "reason-ref:authority-budget:settlement-after-lease-inactive"
                )
            if authority_lease_kill_switch_engaged():
                reason_refs.append(
                    "reason-ref:authority-budget:settlement-after-kill-switch"
                )
            if request.actual_operation_count > state["reserved_operations"]:
                reason_refs.append(
                    "reason-ref:authority-budget:operation-reservation-overage"
                )
            if request.actual_cost_microusd is None:
                status = AuthorityBudgetStatus.settled_cost_unresolved
                reason_refs.append("reason-ref:authority-budget:actual-cost-unresolved")
            elif (
                request.actual_operation_count > state["reserved_operations"]
                or request.actual_cost_microusd > (state["reserved_cost"] or 0)
                or operation_limit is not None
                and next_operations > operation_limit
                or cost_limit is not None
                and next_cost > cost_limit
            ):
                status = AuthorityBudgetStatus.settled_overage
                reason_refs.append("reason-ref:authority-budget:settlement-overage")
            else:
                status = AuthorityBudgetStatus.settled
            receipt = self._build_receipt(
                operation=AuthorityBudgetOperation.settle,
                status=status,
                reservation_ref=request.reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                lease_ref=state["lease_ref"],
                action_ref=state["action_ref"],
                approval_ref=state["approval_ref"],
                approval_validation_ref=state["approval_validation_ref"],
                approval_required=state["approval_required"],
                dispatch_fingerprint_ref=state["dispatch_fingerprint_ref"],
                execution_ref=state["execution_ref"],
                cost_estimate_ref=state["cost_estimate_ref"],
                cost_governor_decision_ref=state["cost_governor_decision_ref"],
                cost_governor_allowed=state["cost_governor_allowed"],
                reserved_operation_count=state["reserved_operations"],
                reserved_cost_microusd=state["reserved_cost"],
                actual_operation_count=request.actual_operation_count,
                actual_cost_microusd=request.actual_cost_microusd,
                actual_cost_ref=request.actual_cost_ref,
                remaining_operation_count=(
                    max(0, operation_limit - next_operations)
                    if operation_limit is not None
                    else None
                ),
                remaining_cost_microusd=(
                    max(0, cost_limit - next_cost) if cost_limit is not None else None
                ),
                execution_status=request.execution_status,
                evidence_refs=request.evidence_refs,
                reason_refs=reason_refs,
                safe_summary=(
                    "Authority budget settlement recorded an unresolved actual cost."
                    if status == AuthorityBudgetStatus.settled_cost_unresolved
                    else "Authority budget settlement recorded actual operation and cost usage."
                ),
            )
            self._append(receipt)
            return receipt

    def release(
        self,
        request: AuthorityBudgetReleaseRequest,
    ) -> AuthorityBudgetReceipt:
        return self._release(request, lock_held=False)

    def _release(
        self,
        request: AuthorityBudgetReleaseRequest,
        *,
        lock_held: bool,
        started_dispatch_fingerprint_ref: str | None = None,
        started_execution_ref: str | None = None,
    ) -> AuthorityBudgetReceipt:
        lock_context = (
            nullcontext()
            if lock_held
            else self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY)
        )
        with lock_context:
            receipts = self._load_receipts()
            fingerprint = _request_fingerprint(
                AuthorityBudgetOperation.release, request
            )
            replay = self._replay_or_conflict(
                receipts,
                AuthorityBudgetOperation.release,
                request.idempotency_ref,
                fingerprint,
            )
            if replay is not None:
                return replay
            state = self._reservation_state(receipts, request.reservation_ref)
            started_dispatch_rollback = bool(
                state is not None
                and state["status"] == AuthorityBudgetStatus.started.value
                and started_dispatch_fingerprint_ref is not None
                and started_execution_ref is not None
                and state["dispatch_fingerprint_ref"]
                == started_dispatch_fingerprint_ref
                and state["execution_ref"] == started_execution_ref
            )
            if state is None or (
                state["status"] != AuthorityBudgetStatus.reserved.value
                and not started_dispatch_rollback
            ):
                receipt = self._denied_followup_receipt(
                    receipts,
                    operation=AuthorityBudgetOperation.release,
                    reservation_ref=request.reservation_ref,
                    idempotency_ref=request.idempotency_ref,
                    request_fingerprint_ref=fingerprint,
                    reason_ref="reason-ref:authority-budget:reservation-not-active",
                )
                self._append(receipt)
                return receipt
            usage = self._usage_for_lease(
                receipts,
                state["lease_ref"],
                exclude_reservation_ref=request.reservation_ref,
            )
            lease = self.lease_store._lease_by_ref(state["lease_ref"])
            operation_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.operation_budget)
                if lease is not None
                else None
            )
            cost_limit = (
                _constraint_maximum(lease, AuthorityConstraintKind.cost_budget_microusd)
                if lease is not None
                else None
            )
            receipt = self._build_receipt(
                operation=AuthorityBudgetOperation.release,
                status=AuthorityBudgetStatus.released,
                reservation_ref=request.reservation_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                lease_ref=state["lease_ref"],
                action_ref=state["action_ref"],
                approval_ref=state["approval_ref"],
                approval_validation_ref=state["approval_validation_ref"],
                approval_required=state["approval_required"],
                dispatch_fingerprint_ref=state["dispatch_fingerprint_ref"],
                execution_ref=(
                    state["execution_ref"] if started_dispatch_rollback else None
                ),
                cost_estimate_ref=state["cost_estimate_ref"],
                cost_governor_decision_ref=state["cost_governor_decision_ref"],
                cost_governor_allowed=state["cost_governor_allowed"],
                reserved_operation_count=state["reserved_operations"],
                reserved_cost_microusd=state["reserved_cost"],
                remaining_operation_count=(
                    max(0, operation_limit - usage["operations"])
                    if operation_limit is not None
                    else None
                ),
                remaining_cost_microusd=(
                    max(0, cost_limit - usage["cost"])
                    if cost_limit is not None
                    else None
                ),
                reason_refs=[request.reason_ref],
                safe_summary=(
                    "Authority budget start claim rolled back before adapter invocation."
                    if started_dispatch_rollback
                    else "Authority budget reservation released before execution."
                ),
            )
            self._append(receipt)
            return receipt

    def _release_locked(
        self,
        request: AuthorityBudgetReleaseRequest,
    ) -> AuthorityBudgetReceipt:
        return self._release(request, lock_held=True)

    def _release_started_dispatch(
        self,
        request: AuthorityBudgetReleaseRequest,
        *,
        dispatch_fingerprint_ref: str,
        execution_ref: str,
    ) -> AuthorityBudgetReceipt:
        """Roll back a dispatch start claim proven not to have reached invocation."""

        return self._release(
            request,
            lock_held=False,
            started_dispatch_fingerprint_ref=dispatch_fingerprint_ref,
            started_execution_ref=execution_ref,
        )

    def build_read_model(self, *, recent_limit: int = 12) -> AuthorityBudgetReadModel:
        if recent_limit < 0:
            raise ValueError("AUTHORITY_BUDGET_RECENT_LIMIT_NONNEGATIVE_REQUIRED")
        if (
            not self.receipts_path.exists()
            and not self.lease_store.leases_path.exists()
        ):
            return AuthorityBudgetReadModel(
                kill_switch_engaged=authority_lease_kill_switch_engaged()
            )
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._build_read_model(recent_limit=recent_limit)

    def _build_read_model(self, *, recent_limit: int) -> AuthorityBudgetReadModel:
        receipts = self._load_receipts()
        leases = self.lease_store._list_leases(active_only=False)
        kill_switch_engaged = authority_lease_kill_switch_engaged()
        summaries: list[AuthorityBudgetLeaseSummary] = []
        for lease in leases:
            operation_limit = _constraint_maximum(
                lease, AuthorityConstraintKind.operation_budget
            )
            cost_limit = _constraint_maximum(
                lease, AuthorityConstraintKind.cost_budget_microusd
            )
            if operation_limit is None and cost_limit is None:
                continue
            usage = self._usage_for_lease(receipts, lease.lease_ref)
            blocked_refs: list[str] = []
            lease_active = lease.is_active()
            if not lease_active:
                blocked_refs.append("reason-ref:authority-budget:lease-inactive")
            if kill_switch_engaged:
                blocked_refs.append("reason-ref:authority-budget:kill-switch-engaged")
            if operation_limit is None:
                blocked_refs.append(
                    "reason-ref:authority-budget:operation-budget-missing"
                )
            if cost_limit is None:
                blocked_refs.append("reason-ref:authority-budget:cost-budget-missing")
            if usage["unresolved_cost"]:
                blocked_refs.append(
                    "reason-ref:authority-budget:actual-cost-unresolved"
                )
            if usage["unreviewed_overage"]:
                blocked_refs.append(
                    "reason-ref:authority-budget:settlement-overage-unreviewed"
                )
            exhausted = bool(
                operation_limit is None
                or cost_limit is None
                or operation_limit is not None
                and usage["operations"] >= operation_limit
                or cost_limit is not None
                and usage["cost"] >= cost_limit
                or usage["unresolved_cost"]
                or usage["unreviewed_overage"]
            )
            if exhausted:
                blocked_refs.append("reason-ref:authority-budget:budget-exhausted")
            summaries.append(
                AuthorityBudgetLeaseSummary(
                    lease_ref=lease.lease_ref,
                    lease_active=lease_active,
                    kill_switch_engaged=kill_switch_engaged,
                    reservation_available=(
                        lease_active and not kill_switch_engaged and not exhausted
                    ),
                    operation_limit=operation_limit,
                    cost_limit_microusd=cost_limit,
                    allocated_operation_count=usage["operations"],
                    allocated_cost_microusd=usage["cost"],
                    remaining_operation_count=(
                        max(0, operation_limit - usage["operations"])
                        if operation_limit is not None
                        else None
                    ),
                    remaining_cost_microusd=(
                        max(0, cost_limit - usage["cost"])
                        if cost_limit is not None
                        else None
                    ),
                    active_reservation_count=usage["active_count"],
                    settled_reservation_count=usage["settled_count"],
                    unresolved_cost=usage["unresolved_cost"],
                    unreviewed_overage=usage["unreviewed_overage"],
                    exhausted=exhausted,
                    blocked_reason_refs=list(dict.fromkeys(blocked_refs)),
                )
            )
        return AuthorityBudgetReadModel(
            lease_summaries=summaries,
            recent_receipts=receipts[-max(0, recent_limit) :] if recent_limit else [],
            receipt_count=len(receipts),
            kill_switch_engaged=kill_switch_engaged,
        )

    def _load_receipts(self) -> list[AuthorityBudgetReceipt]:
        if not self.receipts_path.exists():
            return []
        receipts: list[AuthorityBudgetReceipt] = []
        previous_hash: str | None = None
        idempotency_refs: set[str] = set()
        reservation_states: dict[str, dict[str, Any]] = {}
        with self.receipts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    receipt = AuthorityBudgetReceipt(**payload)
                except Exception as exc:
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_RECEIPT_INVALID"
                    ) from exc
                if receipt.status == AuthorityBudgetStatus.replayed.value:
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_REPLAY_MUST_NOT_BE_PERSISTED"
                    )
                if receipt.previous_entry_hash_ref != previous_hash:
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_HASH_CHAIN_PREVIOUS_MISMATCH"
                    )
                if receipt.entry_hash_ref != _entry_hash_payload(payload):
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_ENTRY_HASH_MISMATCH"
                    )
                if receipt.idempotency_ref in idempotency_refs:
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_DUPLICATE_IDEMPOTENCY_HISTORY"
                    )
                self._validate_history_transition(receipt, reservation_states)
                idempotency_refs.add(receipt.idempotency_ref)
                receipts.append(receipt)
                previous_hash = receipt.entry_hash_ref
        return receipts

    def _validate_history_transition(
        self,
        receipt: AuthorityBudgetReceipt,
        reservation_states: dict[str, dict[str, Any]],
    ) -> None:
        if receipt.operation == AuthorityBudgetOperation.reserve.value:
            if receipt.reservation_ref in reservation_states:
                raise AuthorityBudgetCorruptionError(
                    "AUTHORITY_BUDGET_DUPLICATE_RESERVATION_HISTORY"
                )
            reservation_states[receipt.reservation_ref] = {
                "status": receipt.status,
                "lease_ref": receipt.lease_ref,
                "action_ref": receipt.action_ref,
                "cost_estimate_ref": receipt.cost_estimate_ref,
                "cost_governor_decision_ref": receipt.cost_governor_decision_ref,
                "cost_governor_allowed": receipt.cost_governor_allowed,
                "approval_ref": receipt.approval_ref,
                "approval_validation_ref": receipt.approval_validation_ref,
                "approval_required": receipt.approval_required,
                "dispatch_fingerprint_ref": receipt.dispatch_fingerprint_ref,
                "execution_ref": receipt.execution_ref,
                "reserved_operation_count": receipt.reserved_operation_count,
                "reserved_cost_microusd": receipt.reserved_cost_microusd,
            }
            return
        if receipt.status == AuthorityBudgetStatus.denied.value:
            return
        state = reservation_states.get(receipt.reservation_ref)
        allowed_previous_statuses = {
            AuthorityBudgetOperation.start.value: {
                AuthorityBudgetStatus.reserved.value,
            },
            AuthorityBudgetOperation.settle.value: {
                AuthorityBudgetStatus.reserved.value,
                AuthorityBudgetStatus.started.value,
            },
            AuthorityBudgetOperation.release.value: {
                AuthorityBudgetStatus.reserved.value,
            },
        }
        if (
            receipt.operation == AuthorityBudgetOperation.release.value
            and receipt.execution_ref is not None
        ):
            allowed_previous_statuses[AuthorityBudgetOperation.release.value] = {
                AuthorityBudgetStatus.started.value,
            }
        if (
            receipt.operation == AuthorityBudgetOperation.settle.value
            and state is not None
            and state["dispatch_fingerprint_ref"] is not None
        ):
            allowed_previous_statuses[AuthorityBudgetOperation.settle.value] = {
                AuthorityBudgetStatus.started.value,
            }
        if state is None or state["status"] not in allowed_previous_statuses.get(
            receipt.operation, set()
        ):
            raise AuthorityBudgetCorruptionError(
                "AUTHORITY_BUDGET_INVALID_RESERVATION_TRANSITION"
            )
        for field_name in [
            "lease_ref",
            "action_ref",
            "cost_estimate_ref",
            "cost_governor_decision_ref",
            "cost_governor_allowed",
            "approval_ref",
            "approval_validation_ref",
            "approval_required",
            "dispatch_fingerprint_ref",
            "reserved_operation_count",
            "reserved_cost_microusd",
        ]:
            if getattr(receipt, field_name) != state[field_name]:
                raise AuthorityBudgetCorruptionError(
                    "AUTHORITY_BUDGET_FOLLOWUP_BINDING_MISMATCH"
                )
        if receipt.operation == AuthorityBudgetOperation.start.value:
            if not receipt.execution_ref or state["execution_ref"] is not None:
                raise AuthorityBudgetCorruptionError(
                    "AUTHORITY_BUDGET_START_BINDING_MISMATCH"
                )
        elif receipt.execution_ref != state["execution_ref"]:
            raise AuthorityBudgetCorruptionError(
                "AUTHORITY_BUDGET_EXECUTION_BINDING_MISMATCH"
            )
        if receipt.operation == AuthorityBudgetOperation.settle.value:
            operation_overage = (
                receipt.actual_operation_count is not None
                and receipt.actual_operation_count > state["reserved_operation_count"]
            )
            cost_overage = (
                receipt.actual_cost_microusd is not None
                and state["reserved_cost_microusd"] is not None
                and receipt.actual_cost_microusd > state["reserved_cost_microusd"]
            )
            if (
                operation_overage
                and receipt.status
                not in {
                    AuthorityBudgetStatus.settled_overage.value,
                    AuthorityBudgetStatus.settled_cost_unresolved.value,
                }
            ) or (
                cost_overage
                and receipt.status != AuthorityBudgetStatus.settled_overage.value
            ):
                raise AuthorityBudgetCorruptionError(
                    "AUTHORITY_BUDGET_SETTLEMENT_STATUS_MISMATCH"
                )
        state["status"] = receipt.status
        state["execution_ref"] = receipt.execution_ref

    def _append(self, receipt: AuthorityBudgetReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        new_file = not self.receipts_path.exists()
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(receipt.model_dump(mode="json"), sort_keys=True) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        if new_file:
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def _replay_or_conflict(
        self,
        receipts: list[AuthorityBudgetReceipt],
        operation: AuthorityBudgetOperation,
        idempotency_ref: str,
        fingerprint_ref: str,
        compatible_fingerprint_refs: set[str] | None = None,
    ) -> AuthorityBudgetReceipt | None:
        existing = next(
            (item for item in receipts if item.idempotency_ref == idempotency_ref),
            None,
        )
        if existing is None:
            return None
        if (
            existing.operation != operation.value
            or existing.request_fingerprint_ref
            not in {fingerprint_ref, *(compatible_fingerprint_refs or set())}
        ):
            raise AuthorityBudgetConflictError("AUTHORITY_BUDGET_IDEMPOTENCY_CONFLICT")
        replay = AuthorityBudgetReceipt.model_validate(
            {
                **existing.model_dump(mode="json"),
                "status": AuthorityBudgetStatus.replayed.value,
                "original_status": existing.status,
            }
        )
        return AuthorityBudgetReceipt.model_validate(
            {
                **replay.model_dump(mode="json"),
                "entry_hash_ref": _entry_hash(replay),
            }
        )

    def _reservation_state(
        self,
        receipts: list[AuthorityBudgetReceipt],
        reservation_ref: str,
    ) -> dict[str, Any] | None:
        state: dict[str, Any] | None = None
        for receipt in receipts:
            if receipt.reservation_ref != reservation_ref:
                continue
            if (
                receipt.operation == AuthorityBudgetOperation.reserve.value
                and receipt.status == AuthorityBudgetStatus.reserved.value
            ):
                state = {
                    "status": receipt.status,
                    "lease_ref": receipt.lease_ref,
                    "action_ref": receipt.action_ref,
                    "cost_estimate_ref": receipt.cost_estimate_ref,
                    "cost_governor_decision_ref": receipt.cost_governor_decision_ref,
                    "cost_governor_allowed": receipt.cost_governor_allowed,
                    "approval_ref": receipt.approval_ref,
                    "approval_validation_ref": receipt.approval_validation_ref,
                    "approval_required": receipt.approval_required,
                    "dispatch_fingerprint_ref": receipt.dispatch_fingerprint_ref,
                    "execution_ref": receipt.execution_ref,
                    "reserved_operations": receipt.reserved_operation_count,
                    "reserved_cost": receipt.reserved_cost_microusd,
                    "actual_operations": None,
                    "actual_cost": None,
                }
            elif (
                state is not None
                and receipt.operation == AuthorityBudgetOperation.start.value
                and receipt.status == AuthorityBudgetStatus.started.value
            ):
                state.update(
                    {
                        "status": receipt.status,
                        "execution_ref": receipt.execution_ref,
                    }
                )
            elif (
                state is not None
                and receipt.operation
                in {
                    AuthorityBudgetOperation.settle.value,
                    AuthorityBudgetOperation.release.value,
                }
                and receipt.status != AuthorityBudgetStatus.denied.value
            ):
                state.update(
                    {
                        "status": receipt.status,
                        "actual_operations": receipt.actual_operation_count,
                        "actual_cost": receipt.actual_cost_microusd,
                    }
                )
        return state

    def _usage_for_lease(
        self,
        receipts: list[AuthorityBudgetReceipt],
        lease_ref: str,
        *,
        exclude_reservation_ref: str | None = None,
    ) -> dict[str, Any]:
        reservation_refs = {
            receipt.reservation_ref
            for receipt in receipts
            if receipt.lease_ref == lease_ref
            and receipt.status == AuthorityBudgetStatus.reserved.value
        }
        operations = 0
        cost = 0
        active_count = 0
        settled_count = 0
        unresolved_cost = False
        unreviewed_overage = False
        for reservation_ref in reservation_refs:
            if reservation_ref == exclude_reservation_ref:
                continue
            state = self._reservation_state(receipts, reservation_ref)
            if state is None:
                continue
            if state["status"] in {
                AuthorityBudgetStatus.reserved.value,
                AuthorityBudgetStatus.started.value,
            }:
                operations += state["reserved_operations"]
                cost += state["reserved_cost"] or 0
                active_count += 1
            elif state["status"] in {
                AuthorityBudgetStatus.settled.value,
                AuthorityBudgetStatus.settled_overage.value,
                AuthorityBudgetStatus.settled_cost_unresolved.value,
            }:
                operations += state["actual_operations"] or 0
                cost += state["actual_cost"] or 0
                settled_count += 1
                unresolved_cost = unresolved_cost or (
                    state["status"]
                    == AuthorityBudgetStatus.settled_cost_unresolved.value
                )
                unreviewed_overage = unreviewed_overage or (
                    state["status"] == AuthorityBudgetStatus.settled_overage.value
                )
        return {
            "operations": operations,
            "cost": cost,
            "active_count": active_count,
            "settled_count": settled_count,
            "unresolved_cost": unresolved_cost,
            "unreviewed_overage": unreviewed_overage,
        }

    def _approval_reason_refs(
        self,
        request: AuthorityBudgetReservationRequest,
        *,
        approval_validator: AuthorityBudgetApprovalValidator | None,
    ) -> tuple[list[str], str | None]:
        validation_request = request.approval_validation_request
        if validation_request is None:
            return ["reason-ref:authority-budget:approval-missing"], None
        action = request.action_request
        expected_resource_refs = {
            request.lease_ref,
            *action.resource_refs,
        }
        if action.adapter_ref is not None:
            expected_resource_refs.add(action.adapter_ref)
        reasons: list[str] = []
        if validation_request.subject_type != ApprovalSubjectType.tool_request.value:
            reasons.append("reason-ref:authority-budget:approval-subject-type-mismatch")
        if validation_request.subject_id != action.action_ref:
            reasons.append("reason-ref:authority-budget:approval-subject-mismatch")
        if validation_request.requested_action != action.action_ref:
            reasons.append("reason-ref:authority-budget:approval-action-mismatch")
        if set(validation_request.resource_refs) != expected_resource_refs:
            reasons.append("reason-ref:authority-budget:approval-resource-mismatch")
        if approval_validator is None:
            reasons.append("reason-ref:authority-budget:approval-validator-missing")
            return reasons, None
        if reasons:
            return reasons, None
        try:
            decision = approval_validator(validation_request)
        except Exception:
            return ["reason-ref:authority-budget:approval-validator-failed"], None
        validation_ref = _stable_ref(
            "approval-validation-ref:authority-budget",
            {
                "approval_ref": validation_request.approval_ref,
                "action_ref": action.action_ref,
                "allowed": decision.allowed,
                "matched_grant_ref": decision.matched_grant_ref,
                "reason_codes": decision.reason_codes,
                "status": decision.status,
            },
        )
        if (
            not decision.allowed
            or decision.matched_grant_ref != validation_request.approval_ref
        ):
            reasons.append("reason-ref:authority-budget:approval-not-valid")
        return reasons, validation_ref

    def _denied_followup_receipt(
        self,
        receipts: list[AuthorityBudgetReceipt],
        *,
        operation: AuthorityBudgetOperation,
        reservation_ref: str,
        idempotency_ref: str,
        request_fingerprint_ref: str,
        reason_ref: str,
    ) -> AuthorityBudgetReceipt:
        return self._build_receipt(
            operation=operation,
            status=AuthorityBudgetStatus.denied,
            reservation_ref=reservation_ref,
            idempotency_ref=idempotency_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            previous_entry_hash_ref=(receipts[-1].entry_hash_ref if receipts else None),
            reason_refs=[reason_ref],
            safe_summary="Authority budget follow-up denied without execution.",
        )

    def _build_receipt(
        self,
        *,
        operation: AuthorityBudgetOperation,
        status: AuthorityBudgetStatus,
        reservation_ref: str,
        idempotency_ref: str,
        request_fingerprint_ref: str,
        previous_entry_hash_ref: str | None,
        safe_summary: str,
        **updates: Any,
    ) -> AuthorityBudgetReceipt:
        base = AuthorityBudgetReceipt(
            operation=operation,
            status=status,
            receipt_ref=_stable_ref(
                "receipt-ref:authority-budget",
                {
                    "operation": operation.value,
                    "idempotency_ref": idempotency_ref,
                    "fingerprint": request_fingerprint_ref,
                },
            ),
            reservation_ref=reservation_ref,
            idempotency_ref=idempotency_ref,
            request_fingerprint_ref=request_fingerprint_ref,
            audit_ref=_stable_ref(
                "audit-ref:authority-budget",
                {"operation": operation.value, "idempotency_ref": idempotency_ref},
            ),
            previous_entry_hash_ref=previous_entry_hash_ref,
            entry_hash_ref="entry-hash-ref:authority-budget:pending",
            safe_summary=safe_summary,
            **updates,
        )
        return AuthorityBudgetReceipt.model_validate(
            {
                **base.model_dump(mode="json"),
                "entry_hash_ref": _entry_hash(base),
            }
        )
