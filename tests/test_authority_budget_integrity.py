from concurrent.futures import ThreadPoolExecutor
import json

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_STATE_DIR_ENV,
    AuthorityBudgetCorruptionError,
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetOperation,
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetSettlementRequest,
    AuthorityBudgetStatus,
    AuthorityBudgetStore,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)

from tests.test_authority_budgets import (
    _budget_constraints,
    _reserve_request,
    _stores,
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
