from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from ultimate_ai_agent.core.authority import (
    AuthorityBudgetStatus,
    AuthorityCapability,
    AuthorityDispatchCancelRequest,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
    AuthorityDomain,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchConflictError,
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
)
from ultimate_ai_agent.core.tools.runtime import (
    FilesystemSafeRoot,
)

from tests.test_authority_dispatcher import (
    FILESYSTEM_ROOT_REF,
    _descriptor,
    _lease,
    _request,
)

def test_unclaimed_replayed_reservation_is_released_after_conflict(
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
    orphaned = _request(lease.lease_ref, suffix="orphaned-race", filesystem=True)
    append = dispatcher._append

    def crash_before_prepared(receipt: Any) -> None:
        raise RuntimeError("simulated crash after budget reserve")

    dispatcher._append = crash_before_prepared  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.prepare(orphaned)
    dispatcher._append = append  # type: ignore[method-assign]

    conflicting_payload = orphaned.model_dump(mode="json")
    conflicting_payload["idempotency_ref"] = (
        "idempotency-ref:test-dispatch:orphaned-race-winner"
    )
    conflicting_payload["tool_invocation_request"]["replay_key"] = (
        conflicting_payload["idempotency_ref"]
    )
    conflicting = AuthorityDispatchRequest.model_validate(conflicting_payload)
    replayed_waiting = threading.Event()
    winner_claimed = threading.Event()
    reservation_statuses: dict[int, str] = {}
    statuses_lock = threading.Lock()
    reserve = dispatcher.budget_store.reserve

    def synchronized_reserve(*args: Any, **kwargs: Any) -> Any:
        receipt = reserve(*args, **kwargs)
        with statuses_lock:
            reservation_statuses[threading.get_ident()] = receipt.status
        if receipt.status == AuthorityBudgetStatus.replayed.value:
            replayed_waiting.set()
            assert winner_claimed.wait(timeout=5)
        else:
            assert receipt.status == AuthorityBudgetStatus.reserved.value
            assert replayed_waiting.wait(timeout=5)
        return receipt

    dispatcher.budget_store.reserve = synchronized_reserve  # type: ignore[method-assign]

    def prepare(request: AuthorityDispatchRequest) -> AuthorityDispatchResult | None:
        try:
            return dispatcher.prepare(request)
        except AuthorityDispatchConflictError:
            return None
        finally:
            with statuses_lock:
                status = reservation_statuses.get(threading.get_ident())
            if status == AuthorityBudgetStatus.reserved.value:
                winner_claimed.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, [orphaned, conflicting]))

    prepared = next(result for result in results if result is not None)
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

    assert sum(result is None for result in results) == 1
    assert prepared.receipt.idempotency_ref == conflicting.idempotency_ref
    assert len(released_refs) == 1
    assert prepared.receipt.budget_reservation_ref in reserved_refs - released_refs
    assert len(reserved_refs - released_refs) == 1


def test_missing_adapter_after_prepare_cancels_with_prepared_bindings(
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
    request = _request(lease.lease_ref, suffix="missing-adapter", filesystem=True)
    prepared = dispatcher.prepare(request)
    dispatcher.adapters.clear()

    result = dispatcher.execute(request)
    receipts = dispatcher.list_receipts()

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert [receipt.status for receipt in receipts] == [
        AuthorityDispatchStatus.prepared.value,
        AuthorityDispatchStatus.cancellation_pending.value,
        AuthorityDispatchStatus.cancelled_before_start.value,
    ]
    assert all(
        receipt.capability_ref == prepared.receipt.capability_ref
        and receipt.rollback_ref == prepared.receipt.rollback_ref
        and receipt.safe_disable_ref == prepared.receipt.safe_disable_ref
        for receipt in receipts
    )
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.released.value,
    ]


def test_adapter_binding_drift_after_prepare_cancels_before_invocation(
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
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[delegate],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="adapter-drift", filesystem=True)
    prepared = dispatcher.prepare(request)

    class DriftedAdapter:
        descriptor = delegate.descriptor.model_copy(
            update={"rollback_ref": "rollback-ref:drifted-after-prepare"}
        )
        binding_ref = delegate.binding_ref

        def __init__(self) -> None:
            self.invocation_count = 0

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return delegate.validate_request(request)

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            self.invocation_count += 1
            return delegate.invoke(request)

    drifted = DriftedAdapter()
    dispatcher.adapters[request.adapter_ref] = drifted

    result = dispatcher.execute(request)
    receipts = dispatcher.list_receipts()

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert drifted.invocation_count == 0
    assert (
        "reason-ref:authority-dispatch:prestart-adapter-binding-drift"
        in result.receipt.reason_refs
    )
    assert all(
        receipt.rollback_ref == prepared.receipt.rollback_ref for receipt in receipts
    )


def test_safe_root_mapping_drift_after_prepare_cancels_before_invocation(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    first_root = tmp_path / "first-root"
    second_root = tmp_path / "second-root"
    for root, body in [(first_root, "first"), (second_root, "second-content")]:
        (root / "notes").mkdir(parents=True)
        (root / "notes" / "report.md").write_text(body, encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )

    def adapter(root: Path) -> ToolRuntimeAuthorityDispatchAdapter:
        return ToolRuntimeAuthorityDispatchAdapter(
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
        adapters=[adapter(first_root)],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="safe-root-drift", filesystem=True)
    prepared = dispatcher.prepare(request)
    restarted = AuthorityDispatcher(
        state_dir,
        adapters=[adapter(second_root)],
        lease_store=lease_store,
    )

    result = restarted.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value
    assert result.receipt.adapter_binding_ref == prepared.receipt.adapter_binding_ref
    assert (
        "reason-ref:authority-dispatch:prestart-adapter-binding-drift"
        in result.receipt.reason_refs
    )
    assert result.adapter_result is None


def test_safe_root_snapshot_cannot_be_mutated_after_prepare(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    first_root = tmp_path / "first-root"
    second_root = tmp_path / "second-root"
    for root, body in [(first_root, "first"), (second_root, "second-content")]:
        (root / "notes").mkdir(parents=True)
        (root / "notes" / "report.md").write_text(body, encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    safe_root = FilesystemSafeRoot(
        root_ref=FILESYSTEM_ROOT_REF,
        root_path=first_root,
        safe_label="Test dispatch safe root",
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[safe_root],
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="safe-root-snapshot", filesystem=True)
    dispatcher.prepare(request)

    safe_root.root_path = second_root
    exposed_snapshot = adapter.safe_roots[0]
    exposed_snapshot.root_path = second_root
    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert result.adapter_result is not None
    assert result.adapter_result.safe_output["size_bytes"] == len("first")


def test_recent_dispatches_follow_latest_ledger_position(tmp_path: Path) -> None:
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
    first = _request(lease.lease_ref, suffix="recent-first", filesystem=True)
    second = _request(lease.lease_ref, suffix="recent-second", filesystem=True)

    dispatcher.prepare(first)
    dispatcher.dispatch(second)
    dispatcher.execute(first)

    read_model = dispatcher.build_read_model(recent_limit=1)

    assert [receipt.dispatch_ref for receipt in read_model.latest_receipts] == [
        first.dispatch_ref
    ]


def test_mismatched_adapter_execution_ref_is_settled_as_failure(tmp_path: Path) -> None:
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
                root_ref="safe-root:test-authority",
                root_path=root,
                safe_label="Test dispatch safe root",
            )
        ],
    )

    class MismatchedExecutionRefAdapter:
        descriptor = delegate.descriptor
        binding_ref = delegate.binding_ref

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return delegate.validate_request(request)

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            result = delegate.invoke(request)
            return result.model_copy(
                update={
                    "execution_ref": "authority-dispatch-execution-ref:mismatched"
                }
            )

    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[MismatchedExecutionRefAdapter()],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="mismatched-ref", filesystem=True)

    result = dispatcher.dispatch(request)
    receipts = dispatcher.list_receipts()

    assert result.receipt.status == AuthorityDispatchStatus.failed.value
    assert result.adapter_result is not None
    assert result.adapter_result.succeeded is False
    assert result.receipt.execution_ref == receipts[-2].execution_ref
    assert result.receipt.output_refs == []
    assert len(receipts) == 3


def test_cancellation_claim_crash_is_visible_and_retryable(tmp_path: Path) -> None:
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
    request = _request(lease.lease_ref, suffix="cancel-recovery", filesystem=True)
    prepared = dispatcher.prepare(request)
    cancel_request = AuthorityDispatchCancelRequest(
        dispatch_ref=request.dispatch_ref,
        idempotency_ref="idempotency-ref:test-dispatch-cancel-recovery",
        reason_ref="reason-ref:test-dispatch-cancel-recovery",
        safe_summary="Resume a cancellation claimed before a simulated crash.",
    )
    with dispatcher.lock_manager.acquire("authority-state"):
        receipts = dispatcher._load_receipts()
        pending = dispatcher._build_receipt_from_existing(
            prepared.receipt,
            status=AuthorityDispatchStatus.cancellation_pending,
            previous_entry_hash_ref=receipts[-1].entry_hash_ref,
            cancellation_idempotency_ref=cancel_request.idempotency_ref,
            cancellation_reason_ref=cancel_request.reason_ref,
            reason_refs=[cancel_request.reason_ref],
            safe_summary="Cancellation claimed before simulated process interruption.",
        )
        dispatcher._append(pending)

    read_model = dispatcher.build_read_model()
    execution_retry = dispatcher.execute(request)
    cancelled = dispatcher.cancel(cancel_request)

    assert prepared.receipt.created_at < pending.created_at
    assert read_model.recovery_required_dispatch_refs == [request.dispatch_ref]
    assert execution_retry.recovery_required is True
    assert cancelled.receipt.status == AuthorityDispatchStatus.cancelled_before_start.value


def test_dispatch_idempotency_conflicts_and_hash_tampering_fail_closed(tmp_path: Path) -> None:
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
    request = _request(lease.lease_ref, suffix="conflict", filesystem=True)
    dispatcher.prepare(request)
    conflicting_payload = request.model_dump(mode="json")
    conflicting_payload["safe_summary"] = "A different request under the same idempotency ref."

    with pytest.raises(
        AuthorityDispatchConflictError,
        match="AUTHORITY_DISPATCH_IDEMPOTENCY_CONFLICT",
    ):
        dispatcher.prepare(AuthorityDispatchRequest.model_validate(conflicting_payload))

    lines = dispatcher.receipts_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["safe_summary"] = "Tampered durable dispatch receipt."
    dispatcher.receipts_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(
        AuthorityDispatchCorruptionError,
        match="AUTHORITY_DISPATCH_ENTRY_HASH_MISMATCH",
    ):
        dispatcher.list_receipts()


def test_fresh_dispatch_read_model_does_not_create_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    dispatcher = AuthorityDispatcher(state_dir, adapters=[])

    read_model = dispatcher.build_read_model()

    assert read_model.receipt_count == 0
    assert read_model.latest_receipts == []
    assert not state_dir.exists()


@pytest.mark.parametrize(
    ("mutation", "reason_ref"),
    [
        (
            "posture",
            "reason-ref:authority-dispatch:cost-governor-posture-mismatch",
        ),
        (
            "estimate_ref",
            "reason-ref:authority-dispatch:cost-estimate-ref-mismatch",
        ),
        (
            "amount",
            "reason-ref:authority-dispatch:cost-estimate-amount-mismatch",
        ),
        (
            "run_scope",
            "reason-ref:authority-dispatch:run-cost-budget-scope-mismatch",
        ),
    ],
)
def test_dispatch_recomputes_cost_governor_and_rejects_caller_binding_drift(
    tmp_path: Path,
    mutation: str,
    reason_ref: str,
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
    request = _request(lease.lease_ref, suffix="cost-drift", filesystem=True)
    drifted_payload = request.model_dump(mode="json")
    if mutation == "posture":
        drifted_payload["cost_governor_allowed"] = False
    elif mutation == "estimate_ref":
        drifted_payload["cost_estimate_ref"] = "cost-estimate-ref:caller-drift"
    elif mutation == "amount":
        drifted_payload["estimated_cost_microusd"] = 1
    else:
        drifted_payload["cost_budgets"][0]["scope_id"] = "run-ref:wrong-scope"
    drifted = AuthorityDispatchRequest.model_validate(drifted_payload)

    result = dispatcher.prepare(drifted)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert reason_ref in result.receipt.reason_refs
    assert dispatcher.budget_store.list_receipts() == []
