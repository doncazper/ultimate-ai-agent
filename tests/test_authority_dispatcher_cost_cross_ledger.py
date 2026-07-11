from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetStatus,
    AuthorityBudgetReceipt,
    AuthorityBudgetStore,
    AuthorityCapability,
    AuthorityDispatchRequest,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    _budget_release_idempotency_ref,
    _entry_hash as _dispatch_entry_hash,
    _phase_idempotency_ref,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.authority.budgets import (
    _entry_hash_payload as _budget_entry_hash_payload,
)
from ultimate_ai_agent.core.costs import CostBudget, CostEstimate
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import (
    FilesystemSafeRoot,
)

from tests.test_authority_dispatcher import (
    FILESYSTEM_ROOT_REF,
    _approval,
    _descriptor,
    _lease,
    _request,
)

@pytest.mark.parametrize(
    ("nonfinite_field", "reason_ref", "cost_governor_allowed"),
    [
        (
            "estimate",
            "reason-ref:authority-dispatch:cost-estimate-nonfinite",
            False,
        ),
        (
            "budget",
            "reason-ref:authority-dispatch:cost-budget-nonfinite",
            True,
        ),
    ],
)
def test_nonfinite_cost_inputs_are_denied_without_conversion_failure(
    tmp_path: Path,
    nonfinite_field: str,
    reason_ref: str,
    cost_governor_allowed: bool,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    root.mkdir()
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[
            ToolRuntimeAuthorityDispatchAdapter(
                _descriptor(filesystem=True),
                safe_roots=[
                    FilesystemSafeRoot(
                        root_ref="safe-root:test-authority",
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="nonfinite-cost", filesystem=True)
    estimate_payload = request.cost_estimate.model_dump(mode="json")
    budget_payloads = [
        budget.model_dump(mode="json") for budget in request.cost_budgets
    ]
    if nonfinite_field == "estimate":
        estimate_payload.update(
            {
                "estimated_cost_usd": float("inf"),
                "estimated_token_cost_usd": float("inf"),
            }
        )
    else:
        budget_payloads[0]["max_cost_usd"] = float("inf")
    estimate = CostEstimate.model_validate(estimate_payload)
    budgets = [CostBudget.model_validate(payload) for payload in budget_payloads]
    payload = request.model_dump(mode="json")
    payload.update(
        {
            "cost_estimate": estimate.model_dump(mode="json"),
            "cost_budgets": [budget.model_dump(mode="json") for budget in budgets],
            "cost_estimate_ref": build_authority_dispatch_cost_estimate_ref(estimate),
            "cost_governor_decision_ref": (
                build_authority_dispatch_cost_governor_decision_ref(
                    estimate, budgets
                )
            ),
            "cost_governor_allowed": cost_governor_allowed,
        }
    )
    nonfinite = AuthorityDispatchRequest.model_validate(payload)

    result = dispatcher.prepare(nonfinite)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert reason_ref in result.receipt.reason_refs
    assert dispatcher.budget_store.list_receipts() == []


def test_correctly_rehashed_execution_binding_drift_fails_closed(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("bounded", encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[
            ToolRuntimeAuthorityDispatchAdapter(
                _descriptor(filesystem=True),
                safe_roots=[
                    FilesystemSafeRoot(
                        root_ref="safe-root:test-authority",
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="semantic-tamper", filesystem=True)
    dispatcher.dispatch(request)
    payloads = [
        json.loads(line)
        for line in dispatcher.receipts_path.read_text(encoding="utf-8").splitlines()
    ]
    terminal_payload = {
        **payloads[-1],
        "execution_ref": "authority-dispatch-execution-ref:tampered",
        "entry_hash_ref": "entry-hash-ref:authority-dispatch:pending",
    }
    terminal = dispatcher.list_receipts()[-1].model_validate(terminal_payload)
    payloads[-1] = {
        **terminal.model_dump(mode="json"),
        "entry_hash_ref": _dispatch_entry_hash(terminal),
    }
    dispatcher.receipts_path.write_text(
        "".join(json.dumps(payload, sort_keys=True) + "\n" for payload in payloads),
        encoding="utf-8",
    )

    with pytest.raises(
        AuthorityDispatchCorruptionError,
        match="AUTHORITY_DISPATCH_EXECUTION_BINDING_MISMATCH",
    ):
        dispatcher.list_receipts()


def test_approval_revocation_is_serialized_with_durable_dispatch_start(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.ask_before_changes,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    approval_authority = LocalApprovalAuthority()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    pending = _request(
        lease.lease_ref,
        suffix="approval-start-serialization",
        filesystem=False,
    )
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    dispatcher.prepare(request)
    validation_finished = threading.Event()
    allow_start = threading.Event()
    revoke_entered = threading.Event()
    revoke_finished = threading.Event()
    validate = approval_authority.validate
    revoke = approval_authority.revoke

    def paused_validation(validation: Any) -> Any:
        decision = validate(validation)
        validation_finished.set()
        assert allow_start.wait(5)
        return decision

    def concurrent_revoke() -> Any:
        revoke_entered.set()
        revoked = revoke(
            validation_request.approval_ref,
            "Operator raced revocation with a durable start claim.",
        )
        revoke_finished.set()
        return revoked

    approval_authority.validate = paused_validation  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=2) as pool:
        execution = pool.submit(dispatcher.execute, request)
        assert validation_finished.wait(5)
        revocation = pool.submit(concurrent_revoke)
        assert revoke_entered.wait(5)
        assert not revoke_finished.wait(0.1)
        allow_start.set()
        result = execution.result(timeout=5)
        revoked = revocation.result(timeout=5)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert revoked.status == "revoked"


def test_dispatcher_rejects_budget_store_with_a_different_lease_source(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    lease_store = AuthorityLeaseStore(state_dir)
    mismatched_budget_store = AuthorityBudgetStore(
        state_dir,
        lease_store=AuthorityLeaseStore(tmp_path / "other-authority"),
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_DISPATCH_BUDGET_LEASE_STORE_MISMATCH",
    ):
        AuthorityDispatcher(
            state_dir,
            adapters=[],
            lease_store=lease_store,
            budget_store=mismatched_budget_store,
        )


def test_expired_cost_budget_after_slow_approval_cancels_before_start(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.ask_before_changes,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    approval_authority = LocalApprovalAuthority()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    pending = _request(
        lease.lease_ref,
        suffix="cost-expiry-at-start",
        filesystem=False,
    )
    expiring_budgets = [
        budget.model_copy(update={"expires_at": utc_now() + timedelta(seconds=1)})
        for budget in pending.cost_budgets
    ]
    pending = pending.model_copy(
        update={
            "cost_budgets": expiring_budgets,
            "cost_governor_decision_ref": (
                build_authority_dispatch_cost_governor_decision_ref(
                    pending.cost_estimate, expiring_budgets
                )
            ),
        }
    )
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    dispatcher.prepare(request)
    validation_finished = threading.Event()
    allow_start = threading.Event()
    validate = approval_authority.validate

    def paused_validation(validation: Any) -> Any:
        decision = validate(validation)
        validation_finished.set()
        assert allow_start.wait(5)
        return decision

    approval_authority.validate = paused_validation  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=1) as pool:
        execution = pool.submit(dispatcher.execute, request)
        assert validation_finished.wait(5)
        while utc_now() <= expiring_budgets[0].expires_at:
            time.sleep(0.01)
        allow_start.set()
        result = execution.result(timeout=5)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:cost-budget-expired"
        in result.receipt.reason_refs
    )
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]


def test_approval_expiry_during_prestart_work_cancels_before_start(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.ask_before_changes,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    approval_authority = LocalApprovalAuthority()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    pending = _request(
        lease.lease_ref,
        suffix="approval-expiry-at-start",
        filesystem=False,
    )
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    dispatcher.prepare(request)
    grant = approval_authority.get_grant(validation_request.approval_ref)
    assert grant is not None
    expires_at = utc_now() + timedelta(seconds=0.2)
    approval_authority.load_grant_for_validation(
        grant.model_copy(update={"expires_at": expires_at})
    )
    validate = approval_authority.validate

    def validation_delayed_past_expiry(validation: Any) -> Any:
        decision = validate(validation)
        assert decision.allowed
        while utc_now() <= expires_at:
            time.sleep(0.01)
        return decision

    approval_authority.validate = (  # type: ignore[method-assign]
        validation_delayed_past_expiry
    )

    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:prestart-approval-invalid"
        in result.receipt.reason_refs
    )


def test_cross_ledger_reservation_binding_drift_cancels_fail_closed(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("bounded", encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    other_lease = lease.model_copy(
        update={"lease_ref": "authority-lease-ref:test-cross-ledger-other"}
    )
    lease_store._write_leases([lease, other_lease])
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[
            ToolRuntimeAuthorityDispatchAdapter(
                _descriptor(filesystem=True),
                safe_roots=[
                    FilesystemSafeRoot(
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(
        lease.lease_ref,
        suffix="cross-ledger-binding",
        filesystem=True,
    )
    dispatcher.prepare(request)
    payload = json.loads(dispatcher.budget_store.receipts_path.read_text())
    payload["lease_ref"] = other_lease.lease_ref
    payload["entry_hash_ref"] = _budget_entry_hash_payload(payload)
    AuthorityBudgetReceipt.model_validate(payload)
    dispatcher.budget_store.receipts_path.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:prestart-budget-binding-drift"
        in result.receipt.reason_refs
    )
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]


def test_orphaned_budget_start_is_rolled_back_when_dispatch_never_started(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("bounded", encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref=FILESYSTEM_ROOT_REF,
                root_path=root,
                safe_label="Test dispatch safe root",
            )
        ],
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(
        lease.lease_ref,
        suffix="orphaned-budget-start",
        filesystem=True,
    )
    prepared = dispatcher.prepare(request)
    append = dispatcher._append

    def crash_before_dispatch_start(receipt: Any) -> None:
        if receipt.status == AuthorityDispatchStatus.started.value:
            raise RuntimeError("simulated crash before dispatch start receipt")
        append(receipt)

    dispatcher._append = crash_before_dispatch_start  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.execute(request)
    dispatcher._append = append  # type: ignore[method-assign]
    lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref="reason-ref:test-orphaned-budget-start-revoked",
            safe_summary="Revoke authority after the orphaned budget start claim.",
        ),
        idempotency_ref="idempotency-ref:test-orphaned-budget-start-revoked",
    )
    pending = prepared.receipt.model_copy(
        update={
            "cancellation_idempotency_ref": _phase_idempotency_ref(
                request, "prestart-policy-release"
            )
        }
    )
    public_release = dispatcher.budget_store.release(
        AuthorityBudgetReleaseRequest(
            reservation_ref=prepared.receipt.budget_reservation_ref or "",
            idempotency_ref=_budget_release_idempotency_ref(pending),
            reason_ref="reason-ref:authority-dispatch:prestart-authority-invalid",
            safe_summary="Release governed dispatch capacity before adapter start.",
        )
    )

    result = dispatcher.execute(request)
    budget_receipts = dispatcher.budget_store.list_receipts()
    budget_summary = dispatcher.budget_store.build_read_model().lease_summaries[0]

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert public_release.status == AuthorityBudgetStatus.denied.value
    assert public_release.idempotency_ref != _budget_release_idempotency_ref(pending)
    assert result.receipt.execution_started is False
    assert result.adapter_result is None
    assert [receipt.status for receipt in budget_receipts] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.started.value,
        AuthorityBudgetStatus.denied.value,
        AuthorityBudgetStatus.released.value,
    ]
    assert budget_receipts[-1].execution_ref == budget_receipts[-3].execution_ref
    assert budget_summary.active_reservation_count == 0
    assert budget_summary.allocated_operation_count == 0
    assert [receipt.status for receipt in dispatcher.list_receipts()] == [
        AuthorityDispatchStatus.prepared.value,
        AuthorityDispatchStatus.cancellation_pending.value,
        AuthorityDispatchStatus.cancelled_before_start.value,
    ]
