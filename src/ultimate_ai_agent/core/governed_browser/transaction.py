"""Durable prepare-to-settle kernel for exact external actions."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.authority import (
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityLease,
)
from ultimate_ai_agent.core.authority.budget_contracts import (
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetStatus,
)
from ultimate_ai_agent.core.authority.budgets import (
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetReservationRequest,
    AuthorityBudgetSettlementRequest,
    AuthorityBudgetStore,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel,
)
from ultimate_ai_agent.core.capabilities.models import TaskEnvelope
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReadiness,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    build_external_action_approval_request,
    build_external_action_authority_request,
    build_external_action_capability_manifest,
    stable_governed_browser_ref,
)


class ExternalActionTransactionConflict(RuntimeError):
    pass


class BudgetReservation(BaseModel):
    allowed: bool
    reservation_ref: str | None = None
    receipt_ref: str | None = None
    reason_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class BudgetSettlement(BaseModel):
    allowed: bool
    receipt_ref: str | None = None
    reason_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ExternalActionBudgetGate(Protocol):
    def reserve(
        self,
        request: ExternalActionExecutionRequest,
        approval: ApprovalValidationRequest,
    ) -> BudgetReservation: ...

    def release(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        reason_ref: str,
    ) -> BudgetSettlement: ...

    def settle(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        outcome: ExternalActionDispatchOutcome,
        evidence_refs: list[str],
    ) -> BudgetSettlement: ...


class DenyByDefaultBudgetGate:
    def reserve(
        self,
        request: ExternalActionExecutionRequest,
        approval: ApprovalValidationRequest,
    ) -> BudgetReservation:
        del request, approval
        return BudgetReservation(
            allowed=False,
            reason_refs=["reason-ref:governed-external-action:budget-gate-missing"],
        )

    def release(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        reason_ref: str,
    ) -> BudgetSettlement:
        del request, reservation_ref, reason_ref
        return BudgetSettlement(allowed=False)

    def settle(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        outcome: ExternalActionDispatchOutcome,
        evidence_refs: list[str],
    ) -> BudgetSettlement:
        del request, reservation_ref, outcome, evidence_refs
        return BudgetSettlement(allowed=False)


class AuthorityBudgetStoreGate:
    """Exact adapter to the shared authority budget ledger."""

    def __init__(
        self,
        store: AuthorityBudgetStore,
        approval_authority: LocalApprovalAuthority,
    ) -> None:
        self._store = store
        self._approval_authority = approval_authority

    def reserve(
        self,
        request: ExternalActionExecutionRequest,
        approval: ApprovalValidationRequest,
    ) -> BudgetReservation:
        action = build_external_action_authority_request(request)
        receipt = self._store.reserve(
            AuthorityBudgetReservationRequest(
                lease_ref=request.lease_ref,
                action_request=action,
                operation_count=1,
                estimated_cost_microusd=0,
                cost_estimate_ref=stable_governed_browser_ref(
                    "cost-estimate-ref:governed-external-action",
                    {"intent_ref": request.intent_ref, "cost_microusd": 0},
                ),
                cost_governor_decision_ref=stable_governed_browser_ref(
                    "cost-governor-decision-ref:governed-external-action",
                    {"intent_ref": request.intent_ref, "allowed": True},
                ),
                cost_governor_allowed=True,
                approval_required=True,
                approval_validation_request=approval,
                idempotency_ref=stable_governed_browser_ref(
                    "idempotency-ref:governed-external-action:budget-reserve",
                    {"idempotency_ref": request.idempotency_ref},
                ),
                safe_summary="Reserve one exact zero-cost external-action operation.",
            ),
            approval_validator=self._approval_authority.validate,
        )
        allowed = receipt.status in {
            AuthorityBudgetStatus.reserved.value,
            AuthorityBudgetStatus.replayed.value,
        }
        return BudgetReservation(
            allowed=allowed,
            reservation_ref=receipt.reservation_ref,
            receipt_ref=receipt.receipt_ref,
            reason_refs=list(receipt.reason_refs),
        )

    def release(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        reason_ref: str,
    ) -> BudgetSettlement:
        receipt = self._store.release(
            AuthorityBudgetReleaseRequest(
                reservation_ref=reservation_ref,
                idempotency_ref=stable_governed_browser_ref(
                    "idempotency-ref:governed-external-action:budget-release",
                    {"idempotency_ref": request.idempotency_ref},
                ),
                reason_ref=reason_ref,
                execution_started=False,
                safe_summary="Release an unused external-action reservation.",
            )
        )
        return BudgetSettlement(
            allowed=receipt.status
            in {
                AuthorityBudgetStatus.released.value,
                AuthorityBudgetStatus.replayed.value,
            },
            receipt_ref=receipt.receipt_ref,
            reason_refs=list(receipt.reason_refs),
        )

    def settle(
        self,
        request: ExternalActionExecutionRequest,
        reservation_ref: str,
        outcome: ExternalActionDispatchOutcome,
        evidence_refs: list[str],
    ) -> BudgetSettlement:
        receipt = self._store.settle(
            AuthorityBudgetSettlementRequest(
                reservation_ref=reservation_ref,
                idempotency_ref=stable_governed_browser_ref(
                    "idempotency-ref:governed-external-action:budget-settle",
                    {"idempotency_ref": request.idempotency_ref},
                ),
                actual_operation_count=1,
                actual_cost_microusd=0,
                actual_cost_ref=stable_governed_browser_ref(
                    "actual-cost-ref:governed-external-action",
                    {"intent_ref": request.intent_ref, "cost_microusd": 0},
                ),
                execution_status=(
                    AuthorityBudgetExecutionStatus.succeeded
                    if outcome == ExternalActionDispatchOutcome.succeeded
                    else AuthorityBudgetExecutionStatus.failed
                ),
                evidence_refs=evidence_refs,
                safe_summary="Settle one exact external-action operation.",
            )
        )
        return BudgetSettlement(
            allowed=receipt.status
            in {
                AuthorityBudgetStatus.settled.value,
                AuthorityBudgetStatus.replayed.value,
            },
            receipt_ref=receipt.receipt_ref,
            reason_refs=list(receipt.reason_refs),
        )


class ExternalActionTransactionStore:
    """SQLite ledger containing safe refs and content-free receipts only."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governed_external_actions (
                    transaction_ref TEXT PRIMARY KEY,
                    fingerprint_ref TEXT NOT NULL,
                    state TEXT NOT NULL,
                    receipt_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def prepare(
        self,
        request: ExternalActionExecutionRequest,
    ) -> tuple[ExternalActionState, ExternalActionReceipt | None]:
        fingerprint = stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            request.model_dump(mode="json"),
        )
        now = utc_now().isoformat()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT fingerprint_ref, state, receipt_json "
                "FROM governed_external_actions WHERE transaction_ref = ?",
                (request.binding.transaction_ref,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO governed_external_actions VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        request.binding.transaction_ref,
                        fingerprint,
                        ExternalActionState.prepared.value,
                        None,
                        now,
                        now,
                    ),
                )
                connection.commit()
                return ExternalActionState.prepared, None
            if row[0] != fingerprint:
                connection.rollback()
                raise ExternalActionTransactionConflict(
                    "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT"
                )
            connection.commit()
            receipt = (
                ExternalActionReceipt.model_validate_json(row[2]) if row[2] else None
            )
            return ExternalActionState(row[1]), receipt

    def replay_if_terminal(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None:
        """Return an exact stored terminal receipt without claiming a transaction."""

        fingerprint = stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            request.model_dump(mode="json"),
        )
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint_ref, receipt_json "
                "FROM governed_external_actions WHERE transaction_ref = ?",
                (request.binding.transaction_ref,),
            ).fetchone()
        if row is None:
            return None
        if row[0] != fingerprint:
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT"
            )
        if row[1] is None:
            return None
        receipt = ExternalActionReceipt.model_validate_json(row[1])
        return receipt.model_copy(update={"replayed": True})

    def claim_start(self, transaction_ref: str) -> bool:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE governed_external_actions SET state = ?, updated_at = ? "
                "WHERE transaction_ref = ? AND state = ?",
                (
                    ExternalActionState.started.value,
                    utc_now().isoformat(),
                    transaction_ref,
                    ExternalActionState.prepared.value,
                ),
            ).rowcount
            connection.commit()
            return changed == 1

    def finish(self, receipt: ExternalActionReceipt) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE governed_external_actions SET state = ?, receipt_json = ?, "
                "updated_at = ? WHERE transaction_ref = ?",
                (
                    receipt.state,
                    receipt.model_dump_json(),
                    utc_now().isoformat(),
                    receipt.transaction_ref,
                ),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)


class GovernedExternalActionKernel:
    """Fail-closed, at-most-once execution kernel with no automatic retries."""

    def __init__(
        self,
        *,
        store: ExternalActionTransactionStore,
        approval_authority: LocalApprovalAuthority,
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
        readiness_provider: Callable[
            [ExternalActionExecutionRequest], ExternalActionReadiness
        ],
        budget_gate: ExternalActionBudgetGate | None = None,
        policy_engine: PolicyEngine | None = None,
        local_validation_enabled: bool = False,
        external_mutation_enabled: bool = False,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if external_mutation_enabled:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REAL_TARGETS_MUST_REMAIN_INACTIVE"
            )
        self._store = store
        self._approval_authority = approval_authority
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._budget_gate = budget_gate or DenyByDefaultBudgetGate()
        self._policy = policy_engine or PolicyEngine(default_max_risk=RiskLevel.high)
        self._local_validation_enabled = local_validation_enabled
        self._external_mutation_enabled = False
        self._clock = clock
        self._manifest = build_external_action_capability_manifest()

    def execute(
        self,
        request: ExternalActionExecutionRequest,
        *,
        dispatch: Callable[
            [ExternalActionExecutionRequest], ExternalActionDispatchResult
        ],
    ) -> ExternalActionReceipt:
        prior_state, prior_receipt = self._store.prepare(request)
        if prior_receipt is not None:
            return prior_receipt.model_copy(update={"replayed": True})
        if prior_state == ExternalActionState.started:
            return self._finish(
                request,
                ExternalActionState.outcome_ambiguous,
                ["reason-ref:governed-external-action:prior-start-unsettled"],
            )

        activation_reasons = self._activation_reasons(request)
        if activation_reasons:
            return self._finish(
                request, ExternalActionState.blocked, activation_reasons
            )

        try:
            policy_reasons = self._policy_reasons(request)
        except Exception:
            policy_reasons = [
                "reason-ref:governed-external-action:policy-evaluation-failed"
            ]
        if policy_reasons:
            return self._finish(request, ExternalActionState.blocked, policy_reasons)

        approval_request = build_external_action_approval_request(request)
        approval_validation = approval_request.to_validation_request(
            request.approval_ref
        )
        try:
            approval_decision = self._approval_authority.validate(approval_validation)
        except Exception:
            return self._finish(
                request,
                ExternalActionState.blocked,
                ["reason-ref:governed-external-action:approval-validation-failed"],
            )
        approval_validation_ref = stable_governed_browser_ref(
            "approval-validation-ref:governed-external-action",
            approval_decision.model_dump(mode="json"),
        )
        if not approval_decision.allowed:
            return self._finish(
                request,
                ExternalActionState.blocked,
                [
                    "reason-ref:governed-external-action:approval-invalid",
                    *[
                        stable_governed_browser_ref(
                            "approval-reason-ref:governed-external-action",
                            {"code": code},
                        )
                        for code in approval_decision.reason_codes
                    ],
                ],
                approval_validation_ref=approval_validation_ref,
            )

        action = build_external_action_authority_request(request)
        try:
            authority_decision = self._approval_authority.evaluate_authority_scope(
                action
            )
        except Exception:
            return self._finish(
                request,
                ExternalActionState.blocked,
                ["reason-ref:governed-external-action:authority-evaluation-failed"],
                approval_validation_ref=approval_validation_ref,
            )
        exact_lease = next(
            (
                lease
                for lease in self._authority_leases_provider()
                if lease.lease_ref == request.lease_ref
            ),
            None,
        )
        if (
            authority_decision.outcome
            not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }
            or authority_decision.lease_ref != request.lease_ref
            or exact_lease is None
            or not self._lease_is_exact(exact_lease, request)
        ):
            return self._finish(
                request,
                ExternalActionState.blocked,
                ["reason-ref:governed-external-action:exact-lease-required"],
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
            )

        try:
            reservation = self._budget_gate.reserve(request, approval_validation)
        except Exception:
            reservation = BudgetReservation(
                allowed=False,
                reason_refs=[
                    "reason-ref:governed-external-action:budget-reservation-failed"
                ],
            )
        if not reservation.allowed or reservation.reservation_ref is None:
            return self._finish(
                request,
                ExternalActionState.blocked,
                [
                    "reason-ref:governed-external-action:budget-reservation-denied",
                    *reservation.reason_refs,
                ],
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
            )

        revalidation_reasons = self._revalidation_reasons(request)
        if revalidation_reasons:
            try:
                release = self._budget_gate.release(
                    request,
                    reservation.reservation_ref,
                    "reason-ref:governed-external-action:revalidation-denied",
                )
            except Exception:
                release = BudgetSettlement(
                    allowed=False,
                    reason_refs=[
                        "reason-ref:governed-external-action:budget-release-failed"
                    ],
                )
            if not release.allowed:
                revalidation_reasons.extend(
                    [
                        "reason-ref:governed-external-action:budget-release-unconfirmed",
                        *release.reason_refs,
                    ]
                )
            return self._finish(
                request,
                ExternalActionState.blocked,
                revalidation_reasons,
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
                budget_reservation_ref=reservation.reservation_ref,
            )

        if not self._store.claim_start(request.binding.transaction_ref):
            return self._finish(
                request,
                ExternalActionState.outcome_ambiguous,
                ["reason-ref:governed-external-action:start-claim-conflict"],
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
                budget_reservation_ref=reservation.reservation_ref,
            )

        try:
            dispatch_result = ExternalActionDispatchResult.model_validate(
                dispatch(request)
            )
        except Exception:
            dispatch_result = ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.outcome_ambiguous,
                evidence_refs=[
                    stable_governed_browser_ref(
                        "evidence-ref:governed-external-action:dispatch-exception",
                        {"intent_ref": request.intent_ref},
                    )
                ],
                verified=False,
            )

        try:
            settlement = self._budget_gate.settle(
                request,
                reservation.reservation_ref,
                ExternalActionDispatchOutcome(dispatch_result.outcome),
                list(dispatch_result.evidence_refs),
            )
        except Exception:
            settlement = BudgetSettlement(
                allowed=False,
                reason_refs=[
                    "reason-ref:governed-external-action:budget-settlement-failed"
                ],
            )
        final_state = ExternalActionState(dispatch_result.outcome)
        reasons: list[str] = []
        if not settlement.allowed:
            final_state = ExternalActionState.outcome_ambiguous
            reasons = [
                "reason-ref:governed-external-action:budget-settlement-ambiguous",
                *settlement.reason_refs,
            ]
        return self._finish(
            request,
            final_state,
            reasons,
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision.decision_ref,
            budget_reservation_ref=reservation.reservation_ref,
            budget_settlement_ref=settlement.receipt_ref,
            evidence_refs=list(dispatch_result.evidence_refs),
        )

    def replay_if_terminal(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None:
        """Inspect an exact terminal transaction without creating or claiming it."""

        return self._store.replay_if_terminal(request)

    def _activation_reasons(self, request: ExternalActionExecutionRequest) -> list[str]:
        if request.binding.target_kind == ExternalActionTargetKind.external.value:
            return ["reason-ref:governed-external-action:real-targets-inactive"]
        if not self._local_validation_enabled:
            return ["reason-ref:governed-external-action:local-validation-disabled"]
        if self._external_mutation_enabled:
            return ["reason-ref:governed-external-action:invalid-activation-state"]
        return []

    def _policy_reasons(self, request: ExternalActionExecutionRequest) -> list[str]:
        task = TaskEnvelope(
            task_id=request.task_ref,
            user_request="Validate one exact governed external-action transaction.",
            objective="Produce a content-free at-most-once transaction receipt.",
            scope=[self._manifest.id],
            out_of_scope=[
                "real external targets",
                "standing browser authority",
                "automatic retries",
            ],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[],
            acceptance_criteria=["Return safe refs and exact outcome state only."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={
                "binding_ref": request.binding.binding_ref,
                "idempotency_key": request.idempotency_ref,
            },
        )
        decision = self._policy.can_execute(
            self._manifest,
            task,
            {
                "max_risk_level": RiskLevel.high.value,
                "coordination_mode": CoordinationMode.workflow_node.value,
                "external_side_effect": True,
                "approval_available": True,
            },
        )
        if (
            decision.status != PolicyDecisionStatus.approval_required.value
            or not decision.requires_approval
        ):
            return ["reason-ref:governed-external-action:policy-denied"]
        return []

    def _revalidation_reasons(
        self, request: ExternalActionExecutionRequest
    ) -> list[str]:
        try:
            now = self._clock()
        except Exception:
            return ["reason-ref:governed-external-action:trusted-clock-failed"]
        if not hasattr(now, "tzinfo") or now.tzinfo is None:
            return ["reason-ref:governed-external-action:trusted-clock-invalid"]
        binding = request.binding
        reasons: list[str] = []
        if now >= binding.start_deadline:
            reasons.append("reason-ref:governed-external-action:deadline-expired")
        if not binding.human_present:
            reasons.append(
                "reason-ref:governed-external-action:human-presence-required"
            )
        try:
            readiness = ExternalActionReadiness.model_validate(
                self._readiness_provider(request)
            )
        except Exception:
            return ["reason-ref:governed-external-action:readiness-invalid"]
        if readiness.binding_ref != binding.binding_ref:
            reasons.append(
                "reason-ref:governed-external-action:readiness-binding-mismatch"
            )
        if readiness.page_snapshot_ref != binding.page_snapshot_ref:
            reasons.append("reason-ref:governed-external-action:snapshot-changed")
        if (
            readiness.status != "ready"
            or readiness.observed_at > now
            or readiness.expires_at <= now
            or readiness.expires_at > binding.start_deadline
            or not readiness.broker_integrity_verified
            or not readiness.external_mutation_enabled
        ):
            reasons.append("reason-ref:governed-external-action:readiness-fail-closed")
        if readiness.safe_disable_active:
            reasons.append("reason-ref:governed-external-action:safe-disable-active")
        if readiness.kill_switch_engaged:
            reasons.append("reason-ref:governed-external-action:kill-switch-engaged")
        return list(dict.fromkeys(reasons))

    @staticmethod
    def _lease_is_exact(
        lease: AuthorityLease,
        request: ExternalActionExecutionRequest,
    ) -> bool:
        resource_constraints = [
            constraint
            for constraint in lease.authority_constraints
            if constraint.kind == AuthorityConstraintKind.resource_refs.value
        ]
        operation_constraints = [
            constraint
            for constraint in lease.authority_constraints
            if constraint.kind == AuthorityConstraintKind.operation_budget.value
        ]
        cost_constraints = [
            constraint
            for constraint in lease.authority_constraints
            if constraint.kind == AuthorityConstraintKind.cost_budget_microusd.value
        ]
        return (
            lease.is_active()
            and len(resource_constraints) == 1
            and set(resource_constraints[0].allowed_refs)
            == set(request.binding.exact_resource_refs())
            and len(resource_constraints[0].allowed_refs)
            == len(request.binding.exact_resource_refs())
            and len(operation_constraints) == 1
            and operation_constraints[0].maximum == 1
            and len(cost_constraints) == 1
            and cost_constraints[0].maximum == 1
        )

    def _finish(
        self,
        request: ExternalActionExecutionRequest,
        state: ExternalActionState,
        reason_refs: list[str],
        *,
        approval_validation_ref: str | None = None,
        authority_decision_ref: str | None = None,
        budget_reservation_ref: str | None = None,
        budget_settlement_ref: str | None = None,
        evidence_refs: list[str] | None = None,
    ) -> ExternalActionReceipt:
        payload = {
            "transaction_ref": request.binding.transaction_ref,
            "intent_ref": request.intent_ref,
            "binding_ref": request.binding.binding_ref,
            "state": state.value,
            "approval_validation_ref": approval_validation_ref,
            "authority_decision_ref": authority_decision_ref,
            "budget_reservation_ref": budget_reservation_ref,
            "budget_settlement_ref": budget_settlement_ref,
            "evidence_refs": evidence_refs or [],
            "reason_refs": list(dict.fromkeys(reason_refs)),
        }
        receipt = ExternalActionReceipt(
            receipt_ref=stable_governed_browser_ref(
                "receipt-ref:governed-external-action", payload
            ),
            **payload,
        )
        self._store.finish(receipt)
        return receipt
