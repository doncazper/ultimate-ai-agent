from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)

AUTHORITY_BUDGET_RECEIPTS_FILE = "authority_budget_receipts.jsonl"


class AuthorityBudgetConflictError(RuntimeError):
    """Raised when budget idempotency or ledger history is inconsistent."""


class AuthorityBudgetCorruptionError(RuntimeError):
    """Raised when the append-first budget receipt chain is invalid."""


class _AuthorityBudgetModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class AuthorityBudgetReservationRequest(_AuthorityBudgetModel):
    lease_ref: str = Field(..., min_length=1)
    action_request: AuthorityActionRequest
    operation_count: int = Field(default=1, ge=1)
    estimated_cost_microusd: int | None = Field(default=None, ge=0)
    cost_estimate_ref: str = Field(..., min_length=1)
    cost_governor_decision_ref: str = Field(..., min_length=1)
    cost_governor_allowed: bool
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
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


class AuthorityBudgetSettlementRequest(_AuthorityBudgetModel):
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    actual_operation_count: int = Field(default=1, ge=1)
    actual_cost_microusd: int | None = Field(default=None, ge=0)
    actual_cost_ref: str | None = None
    execution_status: AuthorityBudgetExecutionStatus
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetSettlementRequest":
        validate_task_ref(self.reservation_ref, "authority_budget_reservation_ref")
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        if self.actual_cost_ref is not None:
            validate_task_ref(self.actual_cost_ref, "authority_budget_actual_cost_ref")
        if (self.actual_cost_microusd is None) != (self.actual_cost_ref is None):
            raise ValueError("AUTHORITY_BUDGET_ACTUAL_COST_REF_MUST_MATCH_COST")
        for ref in self.evidence_refs:
            validate_task_ref(ref, "authority_budget_evidence_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


class AuthorityBudgetReleaseRequest(_AuthorityBudgetModel):
    reservation_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    reason_ref: str = Field(..., min_length=1)
    execution_started: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityBudgetReleaseRequest":
        validate_task_ref(self.reservation_ref, "authority_budget_reservation_ref")
        validate_task_ref(self.idempotency_ref, "authority_budget_idempotency_ref")
        validate_task_ref(self.reason_ref, "authority_budget_release_reason_ref")
        validate_safe_task_text(self.safe_summary, "authority_budget_summary")
        return self


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _request_fingerprint(
    operation: AuthorityBudgetOperation,
    request: AuthorityBudgetReservationRequest
    | AuthorityBudgetSettlementRequest
    | AuthorityBudgetReleaseRequest,
) -> str:
    return _stable_ref(
        "request-fingerprint-ref:authority-budget",
        {"operation": operation.value, "request": request.model_dump(mode="json")},
    )


def _entry_hash(receipt: AuthorityBudgetReceipt) -> str:
    return _stable_ref(
        "entry-hash-ref:authority-budget",
        receipt.model_dump(mode="json", exclude={"entry_hash_ref"}),
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
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._load_receipts()

    def reserve(
        self,
        request: AuthorityBudgetReservationRequest,
    ) -> AuthorityBudgetReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            replay = self._replay_or_conflict(
                receipts,
                AuthorityBudgetOperation.reserve,
                request.idempotency_ref,
                _request_fingerprint(AuthorityBudgetOperation.reserve, request),
            )
            if replay is not None:
                return replay
            leases = self.lease_store._list_leases(active_only=True)
            decision = evaluate_authority_request(request.action_request, leases)
            lease = next(
                (item for item in leases if item.lease_ref == request.lease_ref),
                None,
            )
            reason_refs: list[str] = []
            if decision.outcome != AuthorityDecisionOutcome.allow.value:
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
            next_operations = usage["operations"] + request.operation_count
            next_cost = usage["cost"] + (request.estimated_cost_microusd or 0)
            if operation_limit is not None and next_operations > operation_limit:
                reason_refs.append(
                    "reason-ref:authority-budget:operation-budget-exhausted"
                )
            if cost_limit is not None and next_cost > cost_limit:
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

    def settle(
        self,
        request: AuthorityBudgetSettlementRequest,
    ) -> AuthorityBudgetReceipt:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            fingerprint = _request_fingerprint(AuthorityBudgetOperation.settle, request)
            replay = self._replay_or_conflict(
                receipts,
                AuthorityBudgetOperation.settle,
                request.idempotency_ref,
                fingerprint,
            )
            if replay is not None:
                return replay
            state = self._reservation_state(receipts, request.reservation_ref)
            if state is None or state["status"] != AuthorityBudgetStatus.reserved.value:
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
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
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
            if state is None or state["status"] != AuthorityBudgetStatus.reserved.value:
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
                safe_summary="Authority budget reservation released before execution.",
            )
            self._append(receipt)
            return receipt

    def build_read_model(self, *, recent_limit: int = 12) -> AuthorityBudgetReadModel:
        if recent_limit < 0:
            raise ValueError("AUTHORITY_BUDGET_RECENT_LIMIT_NONNEGATIVE_REQUIRED")
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._build_read_model(recent_limit=recent_limit)

    def _build_read_model(self, *, recent_limit: int) -> AuthorityBudgetReadModel:
        receipts = self._load_receipts()
        leases = self.lease_store._list_leases(active_only=False)
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
            exhausted = bool(
                operation_limit is None
                or cost_limit is None
                or operation_limit is not None
                and usage["operations"] >= operation_limit
                or cost_limit is not None
                and usage["cost"] >= cost_limit
                or usage["unresolved_cost"]
            )
            if exhausted:
                blocked_refs.append("reason-ref:authority-budget:budget-exhausted")
            summaries.append(
                AuthorityBudgetLeaseSummary(
                    lease_ref=lease.lease_ref,
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
                    exhausted=exhausted,
                    blocked_reason_refs=list(dict.fromkeys(blocked_refs)),
                )
            )
        return AuthorityBudgetReadModel(
            lease_summaries=summaries,
            recent_receipts=receipts[-max(0, recent_limit) :] if recent_limit else [],
            receipt_count=len(receipts),
        )

    def _load_receipts(self) -> list[AuthorityBudgetReceipt]:
        if not self.receipts_path.exists():
            return []
        receipts: list[AuthorityBudgetReceipt] = []
        previous_hash: str | None = None
        idempotency_refs: set[str] = set()
        with self.receipts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    receipt = AuthorityBudgetReceipt(**json.loads(line))
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
                if receipt.entry_hash_ref != _entry_hash(receipt):
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_ENTRY_HASH_MISMATCH"
                    )
                if receipt.idempotency_ref in idempotency_refs:
                    raise AuthorityBudgetCorruptionError(
                        "AUTHORITY_BUDGET_DUPLICATE_IDEMPOTENCY_HISTORY"
                    )
                idempotency_refs.add(receipt.idempotency_ref)
                receipts.append(receipt)
                previous_hash = receipt.entry_hash_ref
        return receipts

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
    ) -> AuthorityBudgetReceipt | None:
        existing = next(
            (item for item in receipts if item.idempotency_ref == idempotency_ref),
            None,
        )
        if existing is None:
            return None
        if (
            existing.operation != operation.value
            or existing.request_fingerprint_ref != fingerprint_ref
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
                    "reserved_operations": receipt.reserved_operation_count,
                    "reserved_cost": receipt.reserved_cost_microusd,
                    "actual_operations": None,
                    "actual_cost": None,
                }
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
        for reservation_ref in reservation_refs:
            if reservation_ref == exclude_reservation_ref:
                continue
            state = self._reservation_state(receipts, reservation_ref)
            if state is None:
                continue
            if state["status"] == AuthorityBudgetStatus.reserved.value:
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
        return {
            "operations": operations,
            "cost": cost,
            "active_count": active_count,
            "settled_count": settled_count,
            "unresolved_cost": unresolved_cost,
        }

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
