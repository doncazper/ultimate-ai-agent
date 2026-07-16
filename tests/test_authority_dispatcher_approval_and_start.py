from __future__ import annotations

import signal
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
    AuthorityDispatchCancelRequest,
    AuthorityDispatchRequest,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseRevokeRequest,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
    AuthorityDispatchConflictError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    _AtomicStartTerminationGuard,
    _phase_idempotency_ref,
    atomic_start_signal_guard_active,
)
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


def test_atomic_signal_guard_setup_failure_resets_context_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_mask(_how: int, _signals: object) -> set[signal.Signals]:
        raise OSError("injected sigmask failure")

    monkeypatch.setattr(signal, "pthread_sigmask", fail_mask)
    with pytest.raises(OSError, match="injected sigmask failure"):
        with _AtomicStartTerminationGuard():
            pytest.fail("guard entered after sigmask failure")
    assert atomic_start_signal_guard_active() is False


def test_atomic_signal_guard_rollback_failure_still_resets_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_signal = signal.signal
    calls = 0

    def fail_install_and_rollback(
        watched_signal: signal.Signals,
        handler: object,
    ) -> object:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected handler install failure")
        result = original_signal(watched_signal, handler)  # type: ignore[arg-type]
        if calls == 3:
            raise OSError("injected handler rollback failure")
        return result

    monkeypatch.setattr(signal, "signal", fail_install_and_rollback)
    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="AUTHORITY_DISPATCH_ATOMIC_SIGNAL_GUARD_SETUP_UNCERTAIN",
    ):
        with _AtomicStartTerminationGuard():
            pytest.fail("guard entered after handler install failure")
    assert atomic_start_signal_guard_active() is False


def test_declared_failure_cost_cannot_exceed_reserved_estimate(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    root.mkdir()
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    descriptor = _descriptor(filesystem=True).model_copy(
        update={"failure_cost_microusd": 1}
    )

    class PermissiveAdapter:
        def __init__(self) -> None:
            self.descriptor = descriptor
            self.binding_ref = "adapter-binding-ref:test:permissive"
            self.invocation_count = 0

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return []

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            self.invocation_count += 1
            raise AssertionError("failure-cost drift must deny before invocation")

    adapter = PermissiveAdapter()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="failure-cost", filesystem=True)

    result = dispatcher.prepare(request)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert (
        "reason-ref:authority-dispatch:failure-cost-exceeds-reservation"
        in result.receipt.reason_refs
    )
    assert adapter.invocation_count == 0
    assert dispatcher.budget_store.list_receipts() == []


def test_ask_mode_requires_and_binds_exact_local_approval(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.ask_before_changes,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    approval_authority = LocalApprovalAuthority()
    adapter = ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    missing = _request(lease.lease_ref, suffix="missing-approval", filesystem=False)

    denied = dispatcher.dispatch(missing)

    assert denied.receipt.status == AuthorityDispatchStatus.denied.value
    assert "reason-ref:authority-dispatch:approval-missing" in denied.receipt.reason_refs

    pending = _request(lease.lease_ref, suffix="approved", filesystem=False)
    validation_request = _approval(approval_authority, pending)
    approved = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )

    caller_time_payload = approved.model_dump(mode="json")
    caller_time_payload["approval_validation_request"]["current_time"] = (
        utc_now().isoformat()
    )
    with pytest.raises(
        ValueError,
        match="AUTHORITY_DISPATCH_CALLER_APPROVAL_TIME_FORBIDDEN",
    ):
        AuthorityDispatchRequest.model_validate(caller_time_payload)

    result = dispatcher.dispatch(approved)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert result.receipt.approval_required is True
    assert result.receipt.approval_ref == validation_request.approval_ref
    assert result.receipt.approval_validation_ref is not None
    reservation = next(
        receipt
        for receipt in dispatcher.budget_store.list_receipts()
        if receipt.reservation_ref == result.receipt.budget_reservation_ref
        and receipt.status == AuthorityBudgetStatus.reserved.value
    )
    assert reservation.approval_ref == validation_request.approval_ref
    assert reservation.approval_validation_ref == result.receipt.approval_validation_ref


def test_policy_required_approval_is_distinct_from_adapter_posture(
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
    descriptor = _descriptor(filesystem=False).model_copy(
        update={"approval_required": False}
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[ToolRuntimeAuthorityDispatchAdapter(descriptor)],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    pending = _request(
        lease.lease_ref,
        suffix="policy-only-approval",
        filesystem=False,
    )
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )

    result = dispatcher.dispatch(request)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert result.receipt.approval_required is True
    assert result.receipt.adapter_approval_required is False
    assert result.receipt.approval_ref == validation_request.approval_ref


def test_exact_approval_cannot_replay_action_under_new_dispatch_identity(
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
    pending = _request(lease.lease_ref, suffix="approval-single-action", filesystem=False)
    validation_request = _approval(approval_authority, pending)
    approved = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    first = dispatcher.dispatch(approved)
    replay_payload = approved.model_dump(mode="json")
    replay_payload.update(
        {
            "dispatch_ref": "authority-dispatch-ref:test:approval-cloned-envelope",
            "idempotency_ref": (
                "idempotency-ref:test-dispatch:approval-cloned-envelope"
            ),
        }
    )
    replay_payload["tool_invocation_request"].update(
        {
            "invocation_id": replay_payload["dispatch_ref"],
            "replay_key": replay_payload["idempotency_ref"],
        }
    )
    replay = AuthorityDispatchRequest.model_validate(replay_payload)

    with pytest.raises(
        AuthorityDispatchConflictError,
        match="AUTHORITY_DISPATCH_IDEMPOTENCY_CONFLICT",
    ):
        dispatcher.dispatch(replay)

    assert first.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert len(dispatcher.list_receipts()) == 3
    assert len(dispatcher.budget_store.list_receipts()) == 3


def test_out_of_scope_approval_denies_without_adapter_start(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.ask_before_changes,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    approval_authority = LocalApprovalAuthority()
    adapter = ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
        approval_authority=approval_authority,
    )
    pending = _request(lease.lease_ref, suffix="wrong-scope", filesystem=False)
    validation_request = _approval(
        approval_authority,
        pending,
        resource_refs=["resource-ref:test-dispatch:wrong-scope"],
    )
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )

    result = dispatcher.dispatch(request)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert (
        "reason-ref:authority-budget:approval-resource-mismatch"
        in result.receipt.reason_refs
    )
    assert result.receipt.execution_started is False
    assert len(dispatcher.list_receipts()) == 1


def test_prestart_cancellation_releases_capacity_without_execution(tmp_path: Path) -> None:
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
    request = _request(lease.lease_ref, suffix="cancel", filesystem=True)
    prepared = dispatcher.prepare(request)

    cancelled = dispatcher.cancel(
        AuthorityDispatchCancelRequest(
            dispatch_ref=request.dispatch_ref,
            idempotency_ref="idempotency-ref:test-dispatch-cancel",
            reason_ref="reason-ref:test-dispatch-operator-cancelled",
            safe_summary="Cancel this prepared dispatch before adapter start.",
        )
    )
    replay = dispatcher.execute(request)

    assert prepared.receipt.status == AuthorityDispatchStatus.prepared.value
    assert cancelled.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert cancelled.receipt.execution_started is False
    assert cancelled.receipt.adapter_invocation_performed is False
    assert cancelled.receipt.budget_release_receipt_ref is not None
    assert replay.replayed is True
    assert replay.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert [receipt.status for receipt in dispatcher.budget_store.list_receipts()] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]
    with pytest.raises(
        AuthorityDispatchConflictError,
        match="AUTHORITY_DISPATCH_CANCELLATION_IDEMPOTENCY_CONFLICT",
    ):
        dispatcher.cancel(
            AuthorityDispatchCancelRequest(
                dispatch_ref=request.dispatch_ref,
                idempotency_ref="idempotency-ref:test-dispatch-cancel-conflict",
                reason_ref="reason-ref:test-dispatch-different-cancellation",
                safe_summary="Attempt a conflicting cancellation replay.",
            )
        )


def test_budget_release_idempotency_is_namespaced_per_dispatch(tmp_path: Path) -> None:
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
    first = _request(lease.lease_ref, suffix="cancel-shared-first", filesystem=True)
    second = _request(lease.lease_ref, suffix="cancel-shared-second", filesystem=True)
    dispatcher.prepare(first)
    dispatcher.prepare(second)
    shared_idempotency_ref = "idempotency-ref:test-dispatch:shared-cancellation"
    shared_reason_ref = "reason-ref:test-dispatch:shared-cancellation"

    results = [
        dispatcher.cancel(
            AuthorityDispatchCancelRequest(
                dispatch_ref=request.dispatch_ref,
                idempotency_ref=shared_idempotency_ref,
                reason_ref=shared_reason_ref,
                safe_summary="Cancel one exact prepared dispatch with a shared caller key.",
            )
        )
        for request in [first, second]
    ]
    release_receipts = [
        receipt
        for receipt in dispatcher.budget_store.list_receipts()
        if receipt.status == AuthorityBudgetStatus.released.value
    ]

    assert all(
        result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
        for result in results
    )
    assert len(release_receipts) == 2
    assert len({receipt.idempotency_ref for receipt in release_receipts}) == 2


def test_revocation_between_prepare_and_start_cancels_fail_closed(tmp_path: Path) -> None:
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
    request = _request(lease.lease_ref, suffix="revoke", filesystem=True)
    dispatcher.prepare(request)
    lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref="reason-ref:test-dispatch-revoked-before-start",
            safe_summary="Revoke the dispatch lease before adapter start.",
        ),
        idempotency_ref="idempotency-ref:test-dispatch-revoke-before-start",
    )

    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:prestart-authority-invalid"
        in result.receipt.reason_refs
    )


def test_approval_revocation_between_prepare_and_start_cancels_fail_closed(
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
    pending = _request(lease.lease_ref, suffix="approval-revoke", filesystem=False)
    validation_request = _approval(approval_authority, pending)
    request = pending.model_copy(
        update={"approval_validation_request": validation_request}
    )
    prepared = dispatcher.prepare(request)
    approval_authority.revoke(
        validation_request.approval_ref,
        "Operator revoked approval before adapter start.",
    )

    result = dispatcher.execute(request)

    assert prepared.receipt.status == AuthorityDispatchStatus.prepared.value
    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.execution_started is False
    assert (
        "reason-ref:authority-dispatch:prestart-approval-invalid"
        in result.receipt.reason_refs
    )


def test_concurrent_dispatch_replay_invokes_adapter_exactly_once(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("bounded content", encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    delegate = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref="safe-root:test-authority",
                root_path=root,
                safe_label="Test dispatch safe root",
            )
        ],
    )

    class CountingAdapter:
        descriptor = delegate.descriptor
        binding_ref = delegate.binding_ref

        def __init__(self) -> None:
            self.invocation_count = 0
            self._lock = threading.Lock()

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return delegate.validate_request(request)

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            with self._lock:
                self.invocation_count += 1
            return delegate.invoke(request)

    adapter = CountingAdapter()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="concurrent", filesystem=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: dispatcher.dispatch(request), range(4)))

    assert adapter.invocation_count == 1
    assert any(
        result.receipt.status == AuthorityDispatchStatus.succeeded.value
        for result in results
    )
    assert len(dispatcher.list_receipts()) == 3
    assert len(dispatcher.budget_store.list_receipts()) == 3


def test_budget_release_cannot_race_durable_adapter_start(tmp_path: Path) -> None:
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
    delegate = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref=FILESYSTEM_ROOT_REF,
                root_path=root,
                safe_label="Test dispatch safe root",
            )
        ],
    )
    entered = threading.Event()
    proceed = threading.Event()

    class BlockingAdapter:
        descriptor = delegate.descriptor
        binding_ref = delegate.binding_ref

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return delegate.validate_request(request)

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            entered.set()
            assert proceed.wait(timeout=5)
            return delegate.invoke(request)

    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[BlockingAdapter()],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="release-after-start", filesystem=True)
    prepared = dispatcher.prepare(request)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(dispatcher.execute, request)
        assert entered.wait(timeout=5)
        started = dispatcher.list_receipts()[-1]
        competing_settlement = dispatcher.budget_store.settle(
            AuthorityBudgetSettlementRequest(
                reservation_ref=prepared.receipt.budget_reservation_ref or "",
                idempotency_ref=_phase_idempotency_ref(request, "budget-settle"),
                execution_ref=started.execution_ref,
                actual_operation_count=1,
                actual_cost_microusd=0,
                actual_cost_ref="actual-cost-ref:test-competing-settlement",
                execution_status=AuthorityBudgetExecutionStatus.succeeded,
                evidence_refs=["evidence-ref:test-competing-settlement"],
                safe_summary="Reject settlement outside the owning dispatcher.",
            )
        )
        release = dispatcher.budget_store.release(
            AuthorityBudgetReleaseRequest(
                reservation_ref=prepared.receipt.budget_reservation_ref or "",
                idempotency_ref="idempotency-ref:test-release-after-start",
                reason_ref="reason-ref:test-release-after-start",
                safe_summary="Attempt release after durable adapter start.",
            )
        )
        proceed.set()
        result = future.result(timeout=5)

    assert competing_settlement.status == AuthorityBudgetStatus.denied.value
    assert competing_settlement.idempotency_ref != _phase_idempotency_ref(
        request, "budget-settle"
    )
    assert "reason-ref:authority-budget:dispatch-owner-required" in (
        competing_settlement.reason_refs
    )
    assert release.status == AuthorityBudgetStatus.denied.value
    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.started.value,
        AuthorityBudgetStatus.denied.value,
        AuthorityBudgetStatus.denied.value,
        AuthorityBudgetStatus.settled.value,
    ]
