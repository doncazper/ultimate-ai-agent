from concurrent.futures import ThreadPoolExecutor
import json

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_STATE_DIR_ENV,
    AuthorityActionRequest,
    AuthorityBudgetConflictError,
    AuthorityBudgetCorruptionError,
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetOperation,
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetReservationRequest,
    AuthorityBudgetReceipt,
    AuthorityBudgetSettlementRequest,
    AuthorityBudgetStartRequest,
    AuthorityBudgetStatus,
    AuthorityBudgetStore,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.budgets import (
    _entry_hash_payload,
    _legacy_reservation_request_fingerprint,
    _legacy_settlement_request_fingerprint,
)


def _budget_constraints(
    *,
    operation_limit: int = 2,
    cost_limit_microusd: int = 1_000_000,
) -> list[AuthorityConstraint]:
    return [
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-operation-budget",
            kind=AuthorityConstraintKind.operation_budget,
            maximum=operation_limit,
            safe_summary="Limit this lease to an exact operation count.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-cost-budget",
            kind=AuthorityConstraintKind.cost_budget_microusd,
            maximum=cost_limit_microusd,
            safe_summary="Limit this lease to an integer micro-USD cost budget.",
        ),
    ]


def _action(
    *,
    suffix: str,
    operation_count: int = 1,
    cost_microusd: int = 400_000,
) -> AuthorityActionRequest:
    return AuthorityActionRequest(
        action_ref=f"authority-action-ref:test-budget:{suffix}",
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=operation_count,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=cost_microusd,
            ),
        ],
        safe_summary="Execute one exact budgeted workspace action.",
    )


def _stores(tmp_path, *, operation_limit: int = 2, cost_limit: int = 1_000_000):
    state_dir = tmp_path / "authority"
    lease_store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_local_workspace_session,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.execute]
            },
            authority_constraints=_budget_constraints(
                operation_limit=operation_limit,
                cost_limit_microusd=cost_limit,
            ),
            decision_reason_ref="reason-ref:test-authority-budget-lease",
            safe_summary="Issue one exact budgeted workspace lease.",
        ),
        idempotency_ref="idempotency-ref:test-authority-budget-lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return lease_store, AuthorityBudgetStore(state_dir, lease_store=lease_store), lease


def _reserve_request(
    lease_ref: str,
    *,
    suffix: str,
    operation_count: int = 1,
    cost_microusd: int | None = 400_000,
    action_cost_microusd: int | None = None,
    dispatch_fingerprint_ref: str | None = None,
) -> AuthorityBudgetReservationRequest:
    claimed_cost = (
        cost_microusd if action_cost_microusd is None else action_cost_microusd
    )
    return AuthorityBudgetReservationRequest(
        lease_ref=lease_ref,
        action_request=_action(
            suffix=suffix,
            operation_count=operation_count,
            cost_microusd=claimed_cost or 0,
        ),
        operation_count=operation_count,
        estimated_cost_microusd=cost_microusd,
        cost_estimate_ref=f"cost-estimate-ref:test-budget:{suffix}",
        cost_governor_decision_ref=(f"cost-governor-decision-ref:test-budget:{suffix}"),
        cost_governor_allowed=cost_microusd is not None,
        dispatch_fingerprint_ref=dispatch_fingerprint_ref,
        idempotency_ref=f"idempotency-ref:test-budget-reserve:{suffix}",
        safe_summary="Reserve exact operation and cost capacity before execution.",
    )


def test_budget_constraints_are_evaluated_before_durable_reservation(tmp_path) -> None:
    lease_store, _, lease = _stores(tmp_path)
    allowed = evaluate_authority_request(
        _action(suffix="allowed"),
        lease_store.list_leases(active_only=True),
    )
    over_limit = evaluate_authority_request(
        _action(suffix="over-limit", cost_microusd=1_000_001),
        lease_store.list_leases(active_only=True),
    )

    assert allowed.outcome == AuthorityDecisionOutcome.allow.value
    assert allowed.lease_ref == lease.lease_ref
    assert allowed.applied_constraint_refs == [
        "authority-constraint-ref:test-operation-budget",
        "authority-constraint-ref:test-cost-budget",
    ]
    assert over_limit.outcome == AuthorityDecisionOutcome.deny.value
    assert (
        "reason-ref:authority:constraint-limit-exceeded:cost_budget_microusd"
        in over_limit.reason_refs
    )


def test_budget_integer_contracts_reject_boolean_and_string_coercion() -> None:
    with pytest.raises(ValueError, match="int_type"):
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-strict-budget",
            kind=AuthorityConstraintKind.operation_budget,
            maximum=True,
            safe_summary="Reject a boolean budget maximum.",
        )
    request_payload = _reserve_request(
        "authority-lease-ref:test-strict-budget",
        suffix="strict-budget",
    ).model_dump(mode="json")
    request_payload["operation_count"] = "1"
    with pytest.raises(ValueError, match="int_type"):
        AuthorityBudgetReservationRequest.model_validate(request_payload)
    request_payload["operation_count"] = 1
    request_payload["cost_governor_allowed"] = "true"
    with pytest.raises(ValueError, match="bool_type"):
        AuthorityBudgetReservationRequest.model_validate(request_payload)


def test_pre_approval_binding_budget_receipt_hash_remains_readable(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    request = _reserve_request(lease.lease_ref, suffix="legacy-hash")
    receipt = budget_store.reserve(request)
    legacy_payload = receipt.model_dump(mode="json")
    for field_name in [
        "approval_ref",
        "approval_validation_ref",
        "approval_required",
        "dispatch_fingerprint_ref",
        "execution_ref",
    ]:
        legacy_payload.pop(field_name)
    legacy_payload["request_fingerprint_ref"] = (
        _legacy_reservation_request_fingerprint(request)
    )
    legacy_payload["entry_hash_ref"] = _entry_hash_payload(legacy_payload)
    budget_store.receipts_path.write_text(
        json.dumps(legacy_payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = budget_store.list_receipts()
    replay = budget_store.reserve(request)

    assert len(loaded) == 1
    assert loaded[0].approval_required is False
    assert loaded[0].approval_ref is None
    assert replay.status == AuthorityBudgetStatus.replayed.value


def test_pre_execution_binding_settlement_replay_remains_compatible(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="legacy-settlement")
    )
    request = AuthorityBudgetSettlementRequest(
        reservation_ref=reservation.reservation_ref,
        idempotency_ref="idempotency-ref:test-budget-settle:legacy",
        actual_operation_count=1,
        actual_cost_microusd=300_000,
        actual_cost_ref="actual-cost-ref:test-budget-settle:legacy",
        execution_status=AuthorityBudgetExecutionStatus.succeeded,
        evidence_refs=["evidence-ref:test-budget-settle:legacy"],
        safe_summary="Replay one settlement written before execution refs existed.",
    )
    budget_store.settle(request)
    payloads = [
        json.loads(line)
        for line in budget_store.receipts_path.read_text(encoding="utf-8").splitlines()
    ]
    settlement_payload = payloads[-1]
    settlement_payload.pop("execution_ref")
    settlement_payload["request_fingerprint_ref"] = (
        _legacy_settlement_request_fingerprint(request)
    )
    settlement_payload["entry_hash_ref"] = _entry_hash_payload(settlement_payload)
    budget_store.receipts_path.write_text(
        "".join(json.dumps(payload, sort_keys=True) + "\n" for payload in payloads),
        encoding="utf-8",
    )

    replay = budget_store.settle(request)

    assert replay.status == AuthorityBudgetStatus.replayed.value
    assert replay.original_status == AuthorityBudgetStatus.settled.value


def test_reserve_settle_and_cumulative_exhaustion_are_durable(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    first_request = _reserve_request(lease.lease_ref, suffix="first")
    first = budget_store.reserve(first_request)
    replay = budget_store.reserve(first_request)
    settled = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=first.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:first",
            actual_operation_count=1,
            actual_cost_microusd=350_000,
            actual_cost_ref="actual-cost-ref:test-budget-settle:first",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget-settle:first"],
            safe_summary="Settle exact actual usage after execution.",
        )
    )
    second = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="second", cost_microusd=650_000)
    )
    overage = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=second.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:second",
            actual_operation_count=1,
            actual_cost_microusd=700_000,
            actual_cost_ref="actual-cost-ref:test-budget-settle:second",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget-settle:second"],
            safe_summary="Record actual usage even when it exceeds reservation.",
        )
    )
    exhausted = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="third", cost_microusd=1)
    )

    assert first.status == AuthorityBudgetStatus.reserved.value
    assert len(first.entry_hash_ref.rsplit(":", 1)[-1]) == 64
    assert first.remaining_operation_count == 1
    assert first.remaining_cost_microusd == 600_000
    assert replay.status == AuthorityBudgetStatus.replayed.value
    assert replay.original_status == AuthorityBudgetStatus.reserved.value
    assert replay.entry_hash_ref != first.entry_hash_ref
    assert settled.status == AuthorityBudgetStatus.settled.value
    assert settled.remaining_cost_microusd == 650_000
    assert second.status == AuthorityBudgetStatus.reserved.value
    assert overage.status == AuthorityBudgetStatus.settled_overage.value
    assert "reason-ref:authority-budget:settlement-overage" in overage.reason_refs
    assert exhausted.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:operation-budget-exhausted" in (
        exhausted.reason_refs
    )
    assert "reason-ref:authority-budget:cost-budget-exhausted" in (
        exhausted.reason_refs
    )
    assert len(budget_store.list_receipts()) == 5

    missing_redactions = first.model_dump(mode="json")
    missing_redactions["redactions_applied"] = []
    with pytest.raises(
        ValueError,
        match="AUTHORITY_BUDGET_REQUIRED_REDACTIONS_MISSING",
    ):
        AuthorityBudgetReceipt.model_validate(missing_redactions)


def test_release_frees_unexecuted_reservation_capacity(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="release-first")
    )
    released = budget_store.release(
        AuthorityBudgetReleaseRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-release:first",
            reason_ref="reason-ref:test-budget-not-executed",
            safe_summary="Release capacity because execution did not start.",
        )
    )
    replacement = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="release-replacement",
            operation_count=2,
            cost_microusd=1_000_000,
        )
    )

    assert released.status == AuthorityBudgetStatus.released.value
    assert released.execution_performed_by_budget_store is False
    assert replacement.status == AuthorityBudgetStatus.reserved.value
    assert replacement.remaining_operation_count == 0
    assert replacement.remaining_cost_microusd == 0


def test_dispatch_start_claim_blocks_release_and_binds_settlement(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    dispatch_fingerprint_ref = "request-fingerprint-ref:test-budget:start-claim"
    execution_ref = "authority-dispatch-execution-ref:test-budget:start-claim"
    reservation = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="start-claim",
            dispatch_fingerprint_ref=dispatch_fingerprint_ref,
        )
    )
    start_request = AuthorityBudgetStartRequest(
        reservation_ref=reservation.reservation_ref,
        idempotency_ref="idempotency-ref:test-budget-start:start-claim",
        dispatch_fingerprint_ref=dispatch_fingerprint_ref,
        execution_ref=execution_ref,
        safe_summary="Bind this reservation to one durable adapter start.",
    )
    assert not hasattr(budget_store, "start")

    premature = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:before-start",
            actual_operation_count=1,
            actual_cost_microusd=300_000,
            actual_cost_ref="actual-cost-ref:test-budget:before-start",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget:before-start"],
            safe_summary="Deny dispatch-bound settlement before durable start.",
        )
    )
    started = budget_store._start_dispatch(start_request)
    replay = budget_store._start_dispatch(start_request)
    release = budget_store.release(
        AuthorityBudgetReleaseRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-release:after-start",
            reason_ref="reason-ref:test-budget-release-after-start",
            safe_summary="Attempt to release capacity after durable start.",
        )
    )
    competing = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:start-claim",
            execution_ref=execution_ref,
            actual_operation_count=1,
            actual_cost_microusd=1,
            actual_cost_ref="actual-cost-ref:test-budget:competing-owner",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget:competing-owner"],
            safe_summary="Reject settlement outside the owning dispatcher.",
        )
    )
    mismatched = budget_store._settle_dispatch(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:mismatched-start",
            execution_ref="authority-dispatch-execution-ref:test-budget:other",
            actual_operation_count=1,
            actual_cost_microusd=300_000,
            actual_cost_ref="actual-cost-ref:test-budget:mismatched-start",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget:mismatched-start"],
            safe_summary="Reject settlement from a different execution binding.",
        )
    )
    settled = budget_store._settle_dispatch(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:start-claim",
            execution_ref=execution_ref,
            actual_operation_count=1,
            actual_cost_microusd=300_000,
            actual_cost_ref="actual-cost-ref:test-budget:start-claim",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-budget:start-claim"],
            safe_summary="Settle the exact execution bound at durable start.",
        )
    )

    assert premature.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:dispatch-start-required" in (
        premature.reason_refs
    )
    assert started.status == AuthorityBudgetStatus.started.value
    assert started.execution_ref == execution_ref
    assert replay.status == AuthorityBudgetStatus.replayed.value
    assert replay.original_status == AuthorityBudgetStatus.started.value
    assert release.status == AuthorityBudgetStatus.denied.value
    assert competing.status == AuthorityBudgetStatus.denied.value
    assert competing.idempotency_ref != (
        "idempotency-ref:test-budget-settle:start-claim"
    )
    assert "reason-ref:authority-budget:dispatch-owner-required" in (
        competing.reason_refs
    )
    assert mismatched.status == AuthorityBudgetStatus.denied.value
    assert (
        "reason-ref:authority-budget:execution-binding-mismatch"
        in mismatched.reason_refs
    )
    assert settled.status == AuthorityBudgetStatus.settled.value
    assert settled.execution_ref == execution_ref


def test_unknown_cost_claim_drift_and_idempotency_drift_fail_closed(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    unknown = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="unknown", cost_microusd=None)
    )
    mismatch = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="mismatch",
            cost_microusd=100,
            action_cost_microusd=99,
        )
    )
    request = _reserve_request(lease.lease_ref, suffix="conflict", cost_microusd=10)
    reserved = budget_store.reserve(request)

    assert unknown.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:estimated-cost-unknown" in unknown.reason_refs
    assert "reason-ref:authority-budget:cost-governor-denied" in unknown.reason_refs
    assert mismatch.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:cost-claim-mismatch" in mismatch.reason_refs
    assert reserved.status == AuthorityBudgetStatus.reserved.value
    with pytest.raises(
        AuthorityBudgetConflictError,
        match="AUTHORITY_BUDGET_IDEMPOTENCY_CONFLICT",
    ):
        budget_store.reserve(request.model_copy(update={"estimated_cost_microusd": 11}))


def test_unresolved_actual_cost_blocks_future_reservations(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="unresolved-first")
    )
    unresolved = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-budget-settle:unresolved",
            actual_operation_count=1,
            actual_cost_microusd=None,
            execution_status=AuthorityBudgetExecutionStatus.failed,
            evidence_refs=["evidence-ref:test-budget-cost-unresolved"],
            safe_summary="Record unresolved actual cost after a failed attempt.",
        )
    )
    blocked = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="unresolved-second", cost_microusd=1)
    )
    read_model = budget_store.build_read_model()

    assert unresolved.status == AuthorityBudgetStatus.settled_cost_unresolved.value
    assert blocked.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:actual-cost-unresolved" in blocked.reason_refs
    assert read_model.lease_summaries[0].unresolved_cost is True
    assert read_model.lease_summaries[0].exhausted is True
    assert read_model.execution_performed is False


def test_operation_overage_is_recorded_and_blocks_future_capacity(tmp_path) -> None:
    _, budget_store, lease = _stores(
        tmp_path,
        operation_limit=2,
        cost_limit=1_000,
    )
    reservation = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="operation-overage",
            operation_count=1,
            cost_microusd=100,
        )
    )
    overage = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-operation-overage",
            actual_operation_count=3,
            actual_cost_microusd=100,
            actual_cost_ref="actual-cost-ref:test-operation-overage",
            execution_status=AuthorityBudgetExecutionStatus.failed,
            evidence_refs=["evidence-ref:test-operation-overage"],
            safe_summary="Record an operation-count overage after execution.",
        )
    )
    blocked = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="after-operation-overage",
            cost_microusd=1,
        )
    )

    assert overage.status == AuthorityBudgetStatus.settled_overage.value
    assert "reason-ref:authority-budget:operation-reservation-overage" in (
        overage.reason_refs
    )
    assert "reason-ref:authority-budget:settlement-overage" in overage.reason_refs
    assert blocked.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:operation-budget-exhausted" in (
        blocked.reason_refs
    )


def test_reservation_overage_below_lease_ceiling_still_fails_closed(
    tmp_path,
) -> None:
    _, budget_store, lease = _stores(
        tmp_path,
        operation_limit=3,
        cost_limit=1_000,
    )
    reservation = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="below-ceiling-overage",
            cost_microusd=100,
        )
    )
    overage = budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-below-ceiling-overage",
            actual_operation_count=1,
            actual_cost_microusd=200,
            actual_cost_ref="actual-cost-ref:test-below-ceiling-overage",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-below-ceiling-overage"],
            safe_summary="Record reservation overage below the lease ceiling.",
        )
    )
    blocked = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="after-below-ceiling-overage",
            cost_microusd=1,
        )
    )
    summary = budget_store.build_read_model().lease_summaries[0]

    assert overage.status == AuthorityBudgetStatus.settled_overage.value
    assert blocked.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:settlement-overage-unreviewed" in (
        blocked.reason_refs
    )
    assert summary.unreviewed_overage is True
    assert summary.exhausted is True
    assert summary.reservation_available is False


def test_zero_cost_reservation_cannot_bypass_exhausted_cost_ceiling(tmp_path) -> None:
    _, budget_store, lease = _stores(
        tmp_path,
        operation_limit=2,
        cost_limit=0,
    )

    denied = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="zero-cost-exhausted",
            cost_microusd=0,
        )
    )

    assert denied.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:cost-budget-exhausted" in (denied.reason_refs)


def test_settlement_contract_requires_evidence() -> None:
    with pytest.raises(ValueError, match="evidence_refs"):
        AuthorityBudgetSettlementRequest(
            reservation_ref="authority-budget-reservation-ref:test-no-evidence",
            idempotency_ref="idempotency-ref:test-settlement-no-evidence",
            actual_operation_count=1,
            actual_cost_microusd=1,
            actual_cost_ref="actual-cost-ref:test-settlement-no-evidence",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=[],
            safe_summary="Reject settlement without evidence refs.",
        )


def test_reservation_rechecks_kill_switch_and_revocation(
    tmp_path,
    monkeypatch,
) -> None:
    lease_store, budget_store, lease = _stores(tmp_path)
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "1")
    kill_denied = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="kill-switch")
    )
    kill_summary = budget_store.build_read_model().lease_summaries[0]
    monkeypatch.delenv(AUTHORITY_LEASE_KILL_SWITCH_ENV)
    revoked, revoke_receipt = lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref="reason-ref:test-budget-revoke",
            safe_summary="Revoke the budgeted test lease.",
        ),
        idempotency_ref="idempotency-ref:test-budget-revoke",
    )
    revoke_denied = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="revoked")
    )

    assert kill_denied.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:kill-switch-engaged" in kill_denied.reason_refs
    assert kill_summary.kill_switch_engaged is True
    assert kill_summary.reservation_available is False
    assert "reason-ref:authority-budget:kill-switch-engaged" in (
        kill_summary.blocked_reason_refs
    )
    assert revoked is not None
    assert revoke_receipt.status == "revoked"
    assert revoke_denied.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:lease-binding-mismatch" in (
        revoke_denied.reason_refs
    )
    summary = budget_store.build_read_model().lease_summaries[0]
    assert summary.lease_active is False
    assert summary.reservation_available is False
    assert "reason-ref:authority-budget:lease-inactive" in (summary.blocked_reason_refs)


def test_concurrent_reservations_cannot_oversubscribe_budget(tmp_path) -> None:
    _, budget_store, lease = _stores(
        tmp_path,
        operation_limit=1,
        cost_limit=100,
    )

    def reserve(index: int):
        return AuthorityBudgetStore(budget_store.state_dir).reserve(
            _reserve_request(
                lease.lease_ref,
                suffix=f"concurrent-{index}",
                cost_microusd=100,
            )
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(executor.map(reserve, range(8)))

    assert (
        sum(item.status == AuthorityBudgetStatus.reserved.value for item in receipts)
        == 1
    )
    assert (
        sum(item.status == AuthorityBudgetStatus.denied.value for item in receipts) == 7
    )
    summary = budget_store.build_read_model().lease_summaries[0]
    assert summary.allocated_operation_count == 1
    assert summary.allocated_cost_microusd == 100


def test_concurrent_lease_issues_preserve_every_atomic_update(tmp_path) -> None:
    state_dir = tmp_path / "authority"

    def issue(index: int):
        return issue_authority_lease_with_test_approval(
            AuthorityLeaseStore(state_dir),
            AuthorityLeaseIssueRequest(
                mode=TrustMode.full_local_workspace_session,
                requested_domains={
                    AuthorityDomain.workspace: [AuthorityCapability.execute]
                },
                authority_constraints=_budget_constraints(),
                decision_reason_ref=f"reason-ref:test-concurrent-lease:{index}",
                safe_summary="Issue one atomic concurrent authority lease.",
            ),
            idempotency_ref=f"idempotency-ref:test-concurrent-lease:{index}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(issue, range(8)))

    assert all(lease is not None for lease, _ in results)
    assert all(receipt.status == "issued" for _, receipt in results)
    assert len(AuthorityLeaseStore(state_dir).list_leases()) == 8
    assert len(AuthorityLeaseStore(state_dir).list_receipts(limit=20)) == 8


def test_reservation_evaluates_only_the_exact_requested_active_lease(tmp_path) -> None:
    lease_store, budget_store, first_lease = _stores(tmp_path)
    second_lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_local_workspace_session,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.execute]
            },
            authority_constraints=_budget_constraints(),
            decision_reason_ref="reason-ref:test-second-budget-lease",
            safe_summary="Issue a second exact budgeted workspace lease.",
        ),
        idempotency_ref="idempotency-ref:test-second-budget-lease",
    )
    assert second_lease is not None
    assert receipt.status == "issued"
    assert first_lease.lease_ref != second_lease.lease_ref

    reservation = budget_store.reserve(
        _reserve_request(second_lease.lease_ref, suffix="second-exact-lease")
    )

    assert reservation.status == AuthorityBudgetStatus.reserved.value
    assert reservation.lease_ref == second_lease.lease_ref


def test_budget_hash_chain_tampering_is_detected(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    budget_store.reserve(_reserve_request(lease.lease_ref, suffix="tamper"))
    payload = json.loads(budget_store.receipts_path.read_text(encoding="utf-8"))
    payload["reserved_operation_count"] = 2
    budget_store.receipts_path.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        AuthorityBudgetCorruptionError,
        match="AUTHORITY_BUDGET_ENTRY_HASH_MISMATCH",
    ):
        budget_store.list_receipts()


def test_correctly_hashed_impossible_reservation_transition_is_detected(
    tmp_path,
) -> None:
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="impossible-transition")
    )
    budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref="idempotency-ref:test-impossible-transition-settle",
            actual_operation_count=1,
            actual_cost_microusd=100,
            actual_cost_ref="actual-cost-ref:test-impossible-transition",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-impossible-transition"],
            safe_summary="Settle before injecting an impossible release transition.",
        )
    )
    receipts = budget_store.list_receipts()
    impossible_release = budget_store._build_receipt(
        operation=AuthorityBudgetOperation.release,
        status=AuthorityBudgetStatus.released,
        reservation_ref=reservation.reservation_ref,
        idempotency_ref="idempotency-ref:test-impossible-transition-release",
        request_fingerprint_ref=(
            "request-fingerprint-ref:authority-budget:test-impossible-transition"
        ),
        previous_entry_hash_ref=receipts[-1].entry_hash_ref,
        lease_ref=reservation.lease_ref,
        action_ref=reservation.action_ref,
        cost_estimate_ref=reservation.cost_estimate_ref,
        cost_governor_decision_ref=reservation.cost_governor_decision_ref,
        cost_governor_allowed=reservation.cost_governor_allowed,
        reserved_operation_count=reservation.reserved_operation_count,
        reserved_cost_microusd=reservation.reserved_cost_microusd,
        reason_refs=["reason-ref:test-impossible-transition-release"],
        safe_summary="Inject one correctly hashed but impossible release transition.",
    )
    budget_store._append(impossible_release)

    with pytest.raises(
        AuthorityBudgetCorruptionError,
        match="AUTHORITY_BUDGET_INVALID_RESERVATION_TRANSITION",
    ):
        budget_store.list_receipts()


def test_correctly_hashed_overage_misclassification_is_detected(tmp_path) -> None:
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(
            lease.lease_ref,
            suffix="misclassified-overage",
            cost_microusd=100,
        )
    )
    misclassified = budget_store._build_receipt(
        operation=AuthorityBudgetOperation.settle,
        status=AuthorityBudgetStatus.settled,
        reservation_ref=reservation.reservation_ref,
        idempotency_ref="idempotency-ref:test-misclassified-overage",
        request_fingerprint_ref=(
            "request-fingerprint-ref:authority-budget:test-misclassified-overage"
        ),
        previous_entry_hash_ref=reservation.entry_hash_ref,
        lease_ref=reservation.lease_ref,
        action_ref=reservation.action_ref,
        cost_estimate_ref=reservation.cost_estimate_ref,
        cost_governor_decision_ref=reservation.cost_governor_decision_ref,
        cost_governor_allowed=reservation.cost_governor_allowed,
        reserved_operation_count=reservation.reserved_operation_count,
        reserved_cost_microusd=reservation.reserved_cost_microusd,
        actual_operation_count=1,
        actual_cost_microusd=200,
        actual_cost_ref="actual-cost-ref:test-misclassified-overage",
        execution_status=AuthorityBudgetExecutionStatus.succeeded,
        evidence_refs=["evidence-ref:test-misclassified-overage"],
        safe_summary="Inject one correctly hashed misclassified overage.",
    )
    budget_store._append(misclassified)

    with pytest.raises(
        AuthorityBudgetCorruptionError,
        match="AUTHORITY_BUDGET_SETTLEMENT_STATUS_MISMATCH",
    ):
        budget_store.list_receipts()


def test_release_contract_rejects_started_execution() -> None:
    with pytest.raises(
        ValueError,
        match="AUTHORITY_BUDGET_RELEASE_EXECUTION_ALREADY_STARTED",
    ):
        AuthorityBudgetReleaseRequest(
            reservation_ref="authority-budget-reservation-ref:test-started",
            idempotency_ref="idempotency-ref:test-budget-release:started",
            reason_ref="reason-ref:test-budget-release-started",
            execution_started=True,
            safe_summary="Reject release because execution already started.",
        )


def test_partial_budget_constraint_is_visible_but_not_reservable(tmp_path) -> None:
    state_dir = tmp_path / "authority"
    lease_store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_local_workspace_session,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.execute]
            },
            authority_constraints=_budget_constraints()[:1],
            decision_reason_ref="reason-ref:test-partial-budget-lease",
            safe_summary="Issue one lease with an intentionally partial budget.",
        ),
        idempotency_ref="idempotency-ref:test-partial-budget-lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    budget_store = AuthorityBudgetStore(state_dir, lease_store=lease_store)

    denied = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="partial-budget")
    )
    summary = budget_store.build_read_model().lease_summaries[0]

    assert denied.status == AuthorityBudgetStatus.denied.value
    assert "reason-ref:authority-budget:cost-budget-missing" in denied.reason_refs
    assert summary.exhausted is True
    assert "reason-ref:authority-budget:cost-budget-missing" in (
        summary.blocked_reason_refs
    )
    assert "reason-ref:authority-budget:budget-exhausted" in (
        summary.blocked_reason_refs
    )


def test_budget_posture_projects_through_state_api_and_json_cli(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))
    _, budget_store, lease = _stores(tmp_path)
    reservation = budget_store.reserve(
        _reserve_request(lease.lease_ref, suffix="operator-projection")
    )

    state_model = AuthorityLeaseStore().build_state_read_model()
    assert state_model.authority_budget.receipt_count == 1
    assert state_model.authority_budget.lease_summaries[0].lease_active is True
    assert state_model.authority_budget.lease_summaries[0].reservation_available is True
    assert state_model.authority_budget.recent_receipts[0].receipt_ref == (
        reservation.receipt_ref
    )

    api_response = TestClient(app).get("/api/runtime/authority-state")
    assert api_response.status_code == 200
    api_budget = api_response.json()["data"]["authority_budget"]
    assert api_budget["receipt_count"] == 1
    assert api_budget["lease_summaries"][0]["remaining_operation_count"] == 1

    assert uaa_runtime.main(["inspect-authority-state", "--json"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    cli_budget = cli_payload["authority_state_read_model"]["authority_budget"]
    assert cli_budget == api_budget
    assert cli_budget["execution_performed"] is False


def test_fresh_authority_inspection_does_not_create_state_directory(
    tmp_path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "absent-authority-state"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))
    lease_store = AuthorityLeaseStore()
    budget_store = AuthorityBudgetStore()

    assert lease_store.list_leases() == []
    assert lease_store.list_receipts() == []
    assert budget_store.list_receipts() == []
    state_model = lease_store.build_state_read_model()
    budget_model = budget_store.build_read_model()

    assert state_model.authority_budget.receipt_count == 0
    assert budget_model.receipt_count == 0
    assert not state_dir.exists()

    api_response = TestClient(app).get("/api/runtime/authority-state")
    assert api_response.status_code == 200
    assert api_response.json()["data"]["authority_budget"]["receipt_count"] == 0
    assert not state_dir.exists()
