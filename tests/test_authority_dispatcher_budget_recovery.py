from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetStatus,
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetSettlementRequest,
    AuthorityCapability,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseRevokeRequest,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchConflictError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    _phase_idempotency_ref,
)
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

def test_dispatch_bound_budget_cannot_settle_before_start(tmp_path: Path) -> None:
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="settle-before-start", filesystem=True)
    prepared = dispatcher.prepare(request)

    premature = dispatcher.budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=prepared.receipt.budget_reservation_ref or "",
            idempotency_ref="idempotency-ref:test-settle-before-start",
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref="actual-cost-ref:test-settle-before-start",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-settle-before-start"],
            safe_summary="Deny fabricated settlement before adapter start.",
        )
    )
    result = dispatcher.execute(request)

    assert premature.status == AuthorityBudgetStatus.denied.value
    assert (
        "reason-ref:authority-budget:dispatch-start-required"
        in premature.reason_refs
    )
    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value


def test_existing_out_of_band_release_completes_terminal_cancellation(
    tmp_path: Path,
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="released-before-execute", filesystem=True)
    prepared = dispatcher.prepare(request)
    released = dispatcher.budget_store.release(
        AuthorityBudgetReleaseRequest(
            reservation_ref=prepared.receipt.budget_reservation_ref or "",
            idempotency_ref="idempotency-ref:test-release-before-execute",
            reason_ref="reason-ref:test-release-before-execute",
            safe_summary="Release reserved capacity before dispatcher execution.",
        )
    )

    result = dispatcher.execute(request)

    assert released.status == AuthorityBudgetStatus.released.value
    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.budget_release_receipt_ref == released.receipt_ref
    assert result.adapter_result is None
    assert [receipt.status for receipt in dispatcher.list_receipts()] == [
        AuthorityDispatchStatus.prepared.value,
        AuthorityDispatchStatus.cancellation_pending.value,
        AuthorityDispatchStatus.cancelled_before_start.value,
    ]


def test_budget_start_claim_replays_after_crash_before_dispatch_start(
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="start-claim-crash", filesystem=True)
    dispatcher.prepare(request)
    append = dispatcher._append

    def crash_before_dispatch_start(receipt: Any) -> None:
        if receipt.status == AuthorityDispatchStatus.started.value:
            raise RuntimeError("simulated crash after budget start claim")
        append(receipt)

    dispatcher._append = crash_before_dispatch_start  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash after budget start claim"):
        dispatcher.execute(request)
    dispatcher._append = append  # type: ignore[method-assign]

    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.started.value,
        AuthorityBudgetStatus.settled.value,
    ]


def test_concurrent_conflict_releases_losing_fresh_reservation(tmp_path: Path) -> None:
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
                root_ref="safe-root:test-authority",
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
    first = _request(lease.lease_ref, suffix="race-conflict", filesystem=True)
    second_payload = first.model_dump(mode="json")
    second_payload["idempotency_ref"] = "idempotency-ref:test-dispatch:race-loser"
    second_payload["tool_invocation_request"]["replay_key"] = second_payload[
        "idempotency_ref"
    ]
    second = AuthorityDispatchRequest.model_validate(second_payload)
    barrier = threading.Barrier(2)
    reserve = dispatcher.budget_store.reserve

    def synchronized_reserve(*args: Any, **kwargs: Any) -> Any:
        receipt = reserve(*args, **kwargs)
        barrier.wait(timeout=5)
        return receipt

    dispatcher.budget_store.reserve = synchronized_reserve  # type: ignore[method-assign]

    def prepare(request: AuthorityDispatchRequest) -> AuthorityDispatchResult | None:
        try:
            return dispatcher.prepare(request)
        except AuthorityDispatchConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, [first, second]))

    assert sum(result is None for result in results) == 1
    prepared = next(result for result in results if result is not None)
    budget_receipts = dispatcher.budget_store.list_receipts()
    active_reservation_refs = {
        receipt.reservation_ref
        for receipt in budget_receipts
        if receipt.status == AuthorityBudgetStatus.reserved.value
    } - {
        receipt.reservation_ref
        for receipt in budget_receipts
        if receipt.status == AuthorityBudgetStatus.released.value
    }

    assert prepared.receipt.budget_reservation_ref in active_reservation_refs
    assert len(active_reservation_refs) == 1
    assert [receipt.status for receipt in budget_receipts].count(
        AuthorityBudgetStatus.released.value
    ) == 1


def test_crash_recovery_budget_replay_binds_full_dispatch_fingerprint(
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    original = _request(
        lease.lease_ref,
        suffix="crash-fingerprint",
        filesystem=True,
    )
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated crash before prepared receipt")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.prepare(original)
    dispatcher._append = append  # type: ignore[method-assign]
    drifted_payload = original.model_dump(mode="json")
    drifted_payload["tool_invocation_request"]["input_refs"] = [
        "input-ref:test-dispatch:changed-after-crash"
    ]
    drifted = AuthorityDispatchRequest.model_validate(drifted_payload)

    with pytest.raises(
        AuthorityDispatchConflictError,
        match="AUTHORITY_DISPATCH_BUDGET_BINDING_CONFLICT",
    ):
        dispatcher.prepare(drifted)

    recovered = dispatcher.prepare(original)
    budget_receipts = dispatcher.budget_store.list_receipts()

    assert recovered.receipt.status == AuthorityDispatchStatus.prepared.value
    assert recovered.receipt.request_fingerprint_ref == budget_receipts[
        0
    ].dispatch_fingerprint_ref
    assert len(budget_receipts) == 1
    assert len(dispatcher.list_receipts()) == 1


def test_crash_orphan_revalidates_revoked_lease_before_recovery(
    tmp_path: Path,
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
        suffix="orphan-revoked-before-recovery",
        filesystem=True,
    )
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated crash after orphan reservation")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.prepare(request)
    dispatcher._append = append  # type: ignore[method-assign]
    lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref=(
                "reason-ref:test-dispatch-orphan-revoked-before-recovery"
            ),
            safe_summary="Revoke the lease before orphan reservation recovery.",
        ),
        idempotency_ref=(
            "idempotency-ref:test-dispatch-orphan-revoked-before-recovery"
        ),
    )

    denied = dispatcher.prepare(request)

    assert denied.receipt.status == AuthorityDispatchStatus.denied.value
    assert denied.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:reservation-recovery-invalid"
        in denied.receipt.reason_refs
    )
    assert (
        "reason-ref:authority-dispatch:prestart-authority-invalid"
        in denied.receipt.reason_refs
    )
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]
    assert [receipt.status for receipt in dispatcher.list_receipts()] == [
        AuthorityDispatchStatus.denied.value
    ]


def test_crash_orphan_revalidates_revoked_approval_before_recovery(
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
        suffix="orphan-approval-revoked-before-recovery",
        filesystem=False,
    )
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated crash after approved orphan reservation")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.prepare(request)
    dispatcher._append = append  # type: ignore[method-assign]
    approval_authority.revoke(
        validation_request.approval_ref,
        "Operator revoked approval before orphan reservation recovery.",
    )

    denied = dispatcher.prepare(request)

    assert denied.receipt.status == AuthorityDispatchStatus.denied.value
    assert denied.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:reservation-recovery-invalid"
        in denied.receipt.reason_refs
    )
    assert (
        "reason-ref:authority-dispatch:prestart-approval-invalid"
        in denied.receipt.reason_refs
    )
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]


def test_early_denial_releases_crash_orphan_before_terminal_receipt(
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="orphan-before-denial", filesystem=True)
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated crash before prepared denial recovery")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.prepare(request)
    dispatcher._append = append  # type: ignore[method-assign]
    reservation = dispatcher.budget_store.list_receipts()[0]
    premature = dispatcher.budget_store.settle(
        AuthorityBudgetSettlementRequest(
            reservation_ref=reservation.reservation_ref,
            idempotency_ref=_phase_idempotency_ref(request, "budget-settle"),
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref="actual-cost-ref:test-orphan-before-denial",
            execution_status=AuthorityBudgetExecutionStatus.succeeded,
            evidence_refs=["evidence-ref:test-orphan-before-denial"],
            safe_summary="Deny settlement while the crash orphan remains unclaimed.",
        )
    )
    dispatcher.adapters.clear()

    denied = dispatcher.prepare(request)

    assert denied.receipt.status == AuthorityDispatchStatus.denied.value
    assert premature.status == AuthorityBudgetStatus.denied.value
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.denied.value,
        AuthorityBudgetStatus.released.value,
    ]


def test_early_action_conflict_releases_sequential_crash_orphan(
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
                        root_ref=FILESYSTEM_ROOT_REF,
                        root_path=root,
                        safe_label="Test dispatch safe root",
                    )
                ],
            )
        ],
        lease_store=lease_store,
    )
    orphaned = _request(
        lease.lease_ref,
        suffix="early-conflict-orphan",
        filesystem=True,
    )
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated sequential crash after reserve")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated sequential crash"):
        dispatcher.prepare(orphaned)
    dispatcher._append = append  # type: ignore[method-assign]
    winner_payload = orphaned.model_dump(mode="json")
    winner_payload.update(
        {
            "dispatch_ref": "authority-dispatch-ref:test:early-conflict-winner",
            "idempotency_ref": (
                "idempotency-ref:test-dispatch:early-conflict-winner"
            ),
        }
    )
    winner_payload["tool_invocation_request"].update(
        {
            "invocation_id": winner_payload["dispatch_ref"],
            "replay_key": winner_payload["idempotency_ref"],
        }
    )
    winner = AuthorityDispatchRequest.model_validate(winner_payload)
    prepared = dispatcher.prepare(winner)

    with pytest.raises(
        AuthorityDispatchConflictError,
        match="AUTHORITY_DISPATCH_IDEMPOTENCY_CONFLICT",
    ):
        dispatcher.prepare(orphaned)

    budget_receipts = dispatcher.budget_store.list_receipts()
    released_refs = {
        receipt.reservation_ref
        for receipt in budget_receipts
        if receipt.status == AuthorityBudgetStatus.released.value
    }
    reserved_refs = {
        receipt.reservation_ref
        for receipt in budget_receipts
        if receipt.status == AuthorityBudgetStatus.reserved.value
    }

    assert prepared.receipt.status == AuthorityDispatchStatus.prepared.value
    assert len(released_refs) == 1
    assert prepared.receipt.budget_reservation_ref in reserved_refs - released_refs
    assert len(reserved_refs - released_refs) == 1
