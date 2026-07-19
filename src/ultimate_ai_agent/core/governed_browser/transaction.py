"""Durable prepare-to-settle kernel for exact external actions."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from threading import BoundedSemaphore, RLock
from time import monotonic
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
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
    reason_refs: tuple[str, ...] = Field(default_factory=tuple)

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class BudgetSettlement(BaseModel):
    allowed: bool
    receipt_ref: str | None = None
    reason_refs: tuple[str, ...] = Field(default_factory=tuple)

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


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

    def state_if_exact(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionState | None:
        """Read the state only when the complete request fingerprint still matches."""

        fingerprint = stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            request.model_dump(mode="json"),
        )
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint_ref, state "
                "FROM governed_external_actions WHERE transaction_ref = ?",
                (request.binding.transaction_ref,),
            ).fetchone()
        if row is None:
            return None
        if row[0] != fingerprint:
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT"
            )
        return ExternalActionState(row[1])

    def started_at_if_exact(
        self,
        request: ExternalActionExecutionRequest,
    ) -> datetime | None:
        """Return the durable start time only for the exact active request."""

        fingerprint = stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            request.model_dump(mode="json"),
        )
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint_ref, state, updated_at "
                "FROM governed_external_actions WHERE transaction_ref = ?",
                (request.binding.transaction_ref,),
            ).fetchone()
        if row is None:
            return None
        if row[0] != fingerprint:
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT"
            )
        if row[1] != ExternalActionState.started.value:
            return None
        try:
            started_at = datetime.fromisoformat(row[2])
        except (TypeError, ValueError) as exc:
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_STARTED_AT_INVALID"
            ) from exc
        if started_at.tzinfo is None:
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_STARTED_AT_INVALID"
            )
        return started_at

    def terminal_receipt_by_ref(
        self,
        *,
        transaction_ref: str,
        receipt_ref: str,
    ) -> ExternalActionReceipt | None:
        """Read one exact stored terminal receipt without creating a replay."""

        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT receipt_json FROM governed_external_actions "
                "WHERE transaction_ref = ?",
                (transaction_ref,),
            ).fetchone()
        if row is None or row[0] is None:
            return None
        receipt = ExternalActionReceipt.model_validate_json(row[0])
        payload = {
            "transaction_ref": receipt.transaction_ref,
            "intent_ref": receipt.intent_ref,
            "binding_ref": receipt.binding_ref,
            "state": receipt.state,
            "approval_validation_ref": receipt.approval_validation_ref,
            "authority_decision_ref": receipt.authority_decision_ref,
            "budget_reservation_ref": receipt.budget_reservation_ref,
            "budget_settlement_ref": receipt.budget_settlement_ref,
            "evidence_refs": list(receipt.evidence_refs),
            "reason_refs": list(receipt.reason_refs),
        }
        if receipt.budget_release_ref is not None:
            payload["budget_release_ref"] = receipt.budget_release_ref
        expected_receipt_ref = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            payload,
        )
        if (
            receipt.replayed
            or receipt.transaction_ref != transaction_ref
            or receipt.receipt_ref != receipt_ref
            or receipt.receipt_ref != expected_receipt_ref
        ):
            raise ExternalActionTransactionConflict(
                "GOVERNED_EXTERNAL_ACTION_TERMINAL_RECEIPT_CONFLICT"
            )
        return receipt

    def claim_start(self, request: ExternalActionExecutionRequest) -> bool:
        fingerprint = stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            request.model_dump(mode="json"),
        )
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE governed_external_actions SET state = ?, updated_at = ? "
                "WHERE transaction_ref = ? AND fingerprint_ref = ? AND state = ?",
                (
                    ExternalActionState.started.value,
                    utc_now().isoformat(),
                    request.binding.transaction_ref,
                    fingerprint,
                    ExternalActionState.prepared.value,
                ),
            ).rowcount
            if changed != 1:
                row = connection.execute(
                    "SELECT fingerprint_ref FROM governed_external_actions "
                    "WHERE transaction_ref = ?",
                    (request.binding.transaction_ref,),
                ).fetchone()
                if row is not None and row[0] != fingerprint:
                    connection.rollback()
                    raise ExternalActionTransactionConflict(
                        "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT"
                    )
            connection.commit()
            return changed == 1

    def finish(
        self,
        receipt: ExternalActionReceipt,
        *,
        expected_state: ExternalActionState,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT state, receipt_json FROM governed_external_actions "
                "WHERE transaction_ref = ?",
                (receipt.transaction_ref,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise ExternalActionTransactionConflict(
                    "GOVERNED_EXTERNAL_ACTION_FINISH_WITHOUT_PREPARE"
                )
            if row[1] is not None:
                prior = ExternalActionReceipt.model_validate_json(row[1])
                if prior == receipt:
                    connection.commit()
                    return
                connection.rollback()
                raise ExternalActionTransactionConflict(
                    "GOVERNED_EXTERNAL_ACTION_TERMINAL_RECEIPT_CONFLICT"
                )
            if row[0] != expected_state.value:
                connection.rollback()
                raise ExternalActionTransactionConflict(
                    "GOVERNED_EXTERNAL_ACTION_FINISH_STATE_CONFLICT"
                )
            changed = connection.execute(
                "UPDATE governed_external_actions SET state = ?, receipt_json = ?, "
                "updated_at = ? WHERE transaction_ref = ? AND state = ? "
                "AND receipt_json IS NULL",
                (
                    receipt.state,
                    receipt.model_dump_json(),
                    utc_now().isoformat(),
                    receipt.transaction_ref,
                    expected_state.value,
                ),
            ).rowcount
            if changed != 1:
                connection.rollback()
                raise ExternalActionTransactionConflict(
                    "GOVERNED_EXTERNAL_ACTION_FINISH_STATE_CONFLICT"
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
        dispatch_timeout_seconds: float = 30.0,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if external_mutation_enabled:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REAL_TARGETS_MUST_REMAIN_INACTIVE"
            )
        if (
            isinstance(dispatch_timeout_seconds, bool)
            or not isinstance(dispatch_timeout_seconds, (int, float))
            or not 0 < dispatch_timeout_seconds <= 30
        ):
            raise ValueError("GOVERNED_EXTERNAL_ACTION_DISPATCH_TIMEOUT_INVALID")
        self._store = store
        self._approval_authority = approval_authority
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._budget_gate = budget_gate or DenyByDefaultBudgetGate()
        self._policy = policy_engine or PolicyEngine(default_max_risk=RiskLevel.high)
        self._local_validation_enabled = local_validation_enabled
        self._external_mutation_enabled = False
        self._dispatch_timeout_seconds = float(dispatch_timeout_seconds)
        self._dispatch_slot = BoundedSemaphore(value=1)
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
        # Rebuild an exact immutable internal snapshot before deriving the
        # transaction fingerprint.  Frozen Pydantic models can still contain
        # caller-owned mutable containers; validation severs those aliases and
        # rejects any post-construction drift before durable state is touched.
        request = ExternalActionExecutionRequest.model_validate(
            request.model_dump(mode="json")
        )
        prior_state, prior_receipt = self._store.prepare(request)
        if prior_receipt is not None:
            return prior_receipt.model_copy(update={"replayed": True})
        if prior_state == ExternalActionState.started:
            # Another process or thread may still own the durable start.  A
            # normal execute call must never terminalize work it did not
            # claim; explicit restart recovery is handled separately below.
            return self._build_receipt(
                request,
                ExternalActionState.outcome_ambiguous,
                ["reason-ref:governed-external-action:start-already-claimed"],
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
        try:
            matching_leases = [
                lease
                for lease in self._authority_leases_provider()
                if lease.lease_ref == request.lease_ref
            ]
        except Exception:
            matching_leases = []
        if (
            authority_decision.outcome
            not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }
            or authority_decision.lease_ref != request.lease_ref
            or len(matching_leases) != 1
            or not self._lease_is_exact(matching_leases[0], request)
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
        if (
            not reservation.allowed
            or reservation.reservation_ref is None
            or reservation.receipt_ref is None
        ):
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

        revalidation_reasons = [
            *self._authorization_revalidation_reasons(
                request,
                approval_validation,
            ),
            *self._revalidation_reasons(request),
        ]
        revalidation_reasons = list(dict.fromkeys(revalidation_reasons))
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
            if not release.allowed or release.receipt_ref is None:
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
                budget_release_ref=(
                    release.receipt_ref if release.allowed else None
                ),
            )

        if not self._store.claim_start(request):
            terminal = self._store.replay_if_terminal(request)
            if terminal is not None:
                return terminal
            return self._build_receipt(
                request,
                ExternalActionState.outcome_ambiguous,
                ["reason-ref:governed-external-action:start-claim-conflict"],
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
                budget_reservation_ref=reservation.reservation_ref,
            )

        post_claim_reasons = [
            *self._authorization_revalidation_reasons(
                request,
                approval_validation,
            ),
            *self._revalidation_reasons(request),
        ]
        post_claim_reasons = list(dict.fromkeys(post_claim_reasons))
        if post_claim_reasons:
            return self._finish_started_guard_failure(
                request,
                reservation_ref=reservation.reservation_ref,
                approval_validation_ref=approval_validation_ref,
                authority_decision_ref=authority_decision.decision_ref,
                reason_refs=[
                    "reason-ref:governed-external-action:post-start-revalidation-denied",
                    *post_claim_reasons,
                ],
            )

        dispatch_result, dispatch_reasons = self._bounded_dispatch(request, dispatch)
        post_dispatch_reasons = [
            *self._authorization_revalidation_reasons(
                request,
                approval_validation,
            ),
            *self._revalidation_reasons(request),
        ]
        post_dispatch_reasons = list(dict.fromkeys(post_dispatch_reasons))
        if post_dispatch_reasons:
            dispatch_result = ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.outcome_ambiguous,
                evidence_refs=dispatch_result.evidence_refs,
                verified=False,
            )
            dispatch_reasons.extend(
                [
                    "reason-ref:governed-external-action:post-dispatch-revalidation-denied",
                    *post_dispatch_reasons,
                ]
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
        reasons = list(dict.fromkeys(dispatch_reasons))
        if not settlement.allowed or settlement.receipt_ref is None:
            final_state = ExternalActionState.outcome_ambiguous
            reasons.extend(
                [
                    "reason-ref:governed-external-action:budget-settlement-ambiguous",
                    *settlement.reason_refs,
                ]
            )
        return self._finish(
            request,
            final_state,
            list(dict.fromkeys(reasons)),
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision.decision_ref,
            budget_reservation_ref=reservation.reservation_ref,
            budget_settlement_ref=(
                settlement.receipt_ref if settlement.allowed else None
            ),
            evidence_refs=list(dispatch_result.evidence_refs),
        )

    def _authorization_revalidation_reasons(
        self,
        request: ExternalActionExecutionRequest,
        approval_validation: ApprovalValidationRequest,
    ) -> list[str]:
        reasons: list[str] = []
        try:
            approval_decision = self._approval_authority.validate(approval_validation)
            if not approval_decision.allowed:
                reasons.append(
                    "reason-ref:governed-external-action:approval-changed-before-dispatch"
                )
        except Exception:
            reasons.append(
                "reason-ref:governed-external-action:approval-revalidation-failed"
            )

        try:
            authority_decision = self._approval_authority.evaluate_authority_scope(
                build_external_action_authority_request(request)
            )
            matching_leases = [
                lease
                for lease in self._authority_leases_provider()
                if lease.lease_ref == request.lease_ref
            ]
            if (
                authority_decision.outcome
                not in {
                    AuthorityDecisionOutcome.allow.value,
                    AuthorityDecisionOutcome.ask.value,
                }
                or authority_decision.lease_ref != request.lease_ref
                or len(matching_leases) != 1
                or not self._lease_is_exact(matching_leases[0], request)
            ):
                reasons.append(
                    "reason-ref:governed-external-action:lease-changed-before-dispatch"
                )
        except Exception:
            reasons.append(
                "reason-ref:governed-external-action:authority-revalidation-failed"
            )
        return reasons

    def _bounded_dispatch(
        self,
        request: ExternalActionExecutionRequest,
        dispatch: Callable[
            [ExternalActionExecutionRequest], ExternalActionDispatchResult
        ],
    ) -> tuple[ExternalActionDispatchResult, list[str]]:
        if not self._dispatch_slot.acquire(blocking=False):
            return self._ambiguous_dispatch_result(
                request, "dispatch-capacity-bounded"
            ), [
                "reason-ref:governed-external-action:dispatch-capacity-bounded"
            ]

        dispatch_request = ExternalActionExecutionRequest.model_validate_json(
            request.model_dump_json()
        )
        started = monotonic()
        succeeded = False
        raw_result: object | None = None
        try:
            raw_result = dispatch(dispatch_request)
            succeeded = True
        except BaseException:
            pass
        finally:
            elapsed_seconds = monotonic() - started
            self._dispatch_slot.release()

        # An arbitrary Python callback cannot be safely detached or killed.
        # Observe the deadline only after the callback has stopped so no
        # terminal receipt can claim fail-closed settlement while work remains
        # live in a daemon thread.  Real targets remain inactive; a future live
        # adapter must provide its own bounded, confirmed-stop transport.
        if elapsed_seconds > self._dispatch_timeout_seconds:
            return self._ambiguous_dispatch_result(request, "dispatch-timeout"), [
                "reason-ref:governed-external-action:dispatch-timeout"
            ]
        if not succeeded:
            return self._ambiguous_dispatch_result(request, "dispatch-exception"), [
                "reason-ref:governed-external-action:dispatch-exception"
            ]
        try:
            result = ExternalActionDispatchResult.model_validate(raw_result)
        except Exception:
            return self._ambiguous_dispatch_result(
                request, "dispatch-result-invalid"
            ), [
                "reason-ref:governed-external-action:dispatch-result-invalid"
            ]
        return result, []

    @staticmethod
    def _ambiguous_dispatch_result(
        request: ExternalActionExecutionRequest,
        reason: str,
    ) -> ExternalActionDispatchResult:
        return ExternalActionDispatchResult(
            outcome=ExternalActionDispatchOutcome.outcome_ambiguous,
            evidence_refs=(
                stable_governed_browser_ref(
                    f"evidence-ref:governed-external-action:{reason}",
                    {
                        "reason": reason,
                        "transaction_ref": request.binding.transaction_ref,
                        "intent_ref": request.intent_ref,
                        "binding_ref": request.binding.binding_ref,
                    },
                ),
            ),
            verified=False,
        )

    def _finish_started_guard_failure(
        self,
        request: ExternalActionExecutionRequest,
        *,
        reservation_ref: str,
        approval_validation_ref: str,
        authority_decision_ref: str,
        reason_refs: list[str],
    ) -> ExternalActionReceipt:
        evidence_ref = stable_governed_browser_ref(
            "evidence-ref:governed-external-action:post-start-guard",
            {
                "intent_ref": request.intent_ref,
                "reason_refs": list(dict.fromkeys(reason_refs)),
            },
        )
        try:
            settlement = self._budget_gate.settle(
                request,
                reservation_ref,
                ExternalActionDispatchOutcome.outcome_ambiguous,
                [evidence_ref],
            )
        except Exception:
            settlement = BudgetSettlement(
                allowed=False,
                reason_refs=(
                    "reason-ref:governed-external-action:budget-settlement-failed",
                ),
            )
        reasons = list(dict.fromkeys(reason_refs))
        if not settlement.allowed or settlement.receipt_ref is None:
            reasons.extend(
                [
                    "reason-ref:governed-external-action:budget-settlement-ambiguous",
                    *settlement.reason_refs,
                ]
            )
        return self._finish(
            request,
            ExternalActionState.outcome_ambiguous,
            list(dict.fromkeys(reasons)),
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision_ref,
            budget_reservation_ref=reservation_ref,
            budget_settlement_ref=(
                settlement.receipt_ref if settlement.allowed else None
            ),
            evidence_refs=[evidence_ref],
        )

    def replay_if_terminal(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None:
        """Inspect an exact terminal transaction without creating or claiming it."""

        return self._store.replay_if_terminal(request)

    def recover_if_prior_start(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None:
        """Finish an exact orphaned start as ambiguous before later preflight checks."""

        request = ExternalActionExecutionRequest.model_validate(
            request.model_dump(mode="json")
        )
        started_at = self._store.started_at_if_exact(request)
        if started_at is None:
            return None
        try:
            current_time = self._clock()
        except Exception:
            return None
        if current_time.tzinfo is None:
            return None
        # A normal caller must not mistake a live dispatch owner for a crashed
        # process.  The owner has the bounded dispatch window plus a settlement
        # grace period before restart recovery may conservatively terminalize
        # the orphan as ambiguous.  Recovery never redispatches the action.
        recovery_not_before = started_at + timedelta(
            seconds=self._dispatch_timeout_seconds + 5.0
        )
        if current_time < recovery_not_before:
            return None
        return self._finish(
            request,
            ExternalActionState.outcome_ambiguous,
            ["reason-ref:governed-external-action:prior-start-unsettled"],
        )

    def terminal_receipt_by_ref(
        self,
        *,
        transaction_ref: str,
        receipt_ref: str,
    ) -> ExternalActionReceipt | None:
        """Inspect one exact stored terminal receipt by its bound proof ref."""

        return self._store.terminal_receipt_by_ref(
            transaction_ref=transaction_ref,
            receipt_ref=receipt_ref,
        )

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
        if readiness.observed_origin_ref != binding.origin_ref:
            reasons.append(
                "reason-ref:governed-external-action:observed-origin-mismatch"
            )
        if readiness.observed_recipient_ref != binding.recipient_ref:
            reasons.append(
                "reason-ref:governed-external-action:observed-recipient-mismatch"
            )
        if readiness.observed_field_schema_ref != binding.field_schema_ref:
            reasons.append(
                "reason-ref:governed-external-action:observed-field-schema-mismatch"
            )
        if readiness.observed_transaction_ref != binding.transaction_ref:
            reasons.append(
                "reason-ref:governed-external-action:observed-transaction-mismatch"
            )
        if readiness.observed_artifact_refs != tuple(binding.artifact_refs):
            reasons.append(
                "reason-ref:governed-external-action:observed-artifact-scope-mismatch"
            )
        if readiness.observed_resource_refs != tuple(binding.resource_refs):
            reasons.append(
                "reason-ref:governed-external-action:observed-resource-scope-mismatch"
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
        reasons.extend(readiness.adversarial_signals.reason_refs())
        return list(dict.fromkeys(reasons))

    @staticmethod
    def _lease_is_exact(
        lease: AuthorityLease,
        request: ExternalActionExecutionRequest,
    ) -> bool:
        browser_capabilities = lease.domains.get(AuthorityDomain.browser, [])
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
            and len(lease.domains) == 1
            and len(browser_capabilities) == 1
            and AuthorityCapability(browser_capabilities[0])
            == AuthorityCapability(request.binding.authority_capability)
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
        budget_release_ref: str | None = None,
        budget_settlement_ref: str | None = None,
        evidence_refs: list[str] | None = None,
    ) -> ExternalActionReceipt:
        receipt = self._build_receipt(
            request,
            state,
            reason_refs,
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision_ref,
            budget_reservation_ref=budget_reservation_ref,
            budget_release_ref=budget_release_ref,
            budget_settlement_ref=budget_settlement_ref,
            evidence_refs=evidence_refs,
        )
        expected_state = (
            ExternalActionState.prepared
            if state == ExternalActionState.blocked
            else ExternalActionState.started
        )
        self._store.finish(receipt, expected_state=expected_state)
        return receipt

    @staticmethod
    def _build_receipt(
        request: ExternalActionExecutionRequest,
        state: ExternalActionState,
        reason_refs: list[str],
        *,
        approval_validation_ref: str | None = None,
        authority_decision_ref: str | None = None,
        budget_reservation_ref: str | None = None,
        budget_release_ref: str | None = None,
        budget_settlement_ref: str | None = None,
        evidence_refs: list[str] | None = None,
    ) -> ExternalActionReceipt:
        bounded_reason_refs = list(dict.fromkeys(reason_refs))
        if len(bounded_reason_refs) > 16:
            overflow = bounded_reason_refs[14:]
            bounded_reason_refs = [
                *bounded_reason_refs[:14],
                stable_governed_browser_ref(
                    "reason-ref:governed-external-action:reason-overflow",
                    {
                        "intent_ref": request.intent_ref,
                        "reason_refs": overflow,
                    },
                ),
            ]
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
            "reason_refs": bounded_reason_refs,
        }
        if budget_release_ref is not None:
            payload["budget_release_ref"] = budget_release_ref
        receipt = ExternalActionReceipt(
            receipt_ref=stable_governed_browser_ref(
                "receipt-ref:governed-external-action", payload
            ),
            **payload,
        )
        return receipt
