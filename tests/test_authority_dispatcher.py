from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from ultimate_ai_agent.core.approvals import ApprovalRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityBudgetStatus,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchCancelRequest,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchConflictError,
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    _entry_hash as _dispatch_entry_hash,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    NOOP_TOOL_NAME,
    NOOP_TOOL_REF,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
)


FILESYSTEM_ADAPTER_REF = "authority-adapter-ref:filesystem-metadata-v1"
FILESYSTEM_CAPABILITY_REF = "authority-capability-ref:filesystem-metadata-v1"
NOOP_ADAPTER_REF = "authority-adapter-ref:governed-noop-v1"
NOOP_CAPABILITY_REF = "authority-capability-ref:governed-noop-v1"


def _constraints(*, operation_limit: int = 4) -> list[AuthorityConstraint]:
    return [
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-dispatch-operations",
            kind=AuthorityConstraintKind.operation_budget,
            maximum=operation_limit,
            safe_summary="Limit governed dispatcher operations.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-dispatch-cost",
            kind=AuthorityConstraintKind.cost_budget_microusd,
            maximum=1,
            safe_summary="Limit governed dispatcher cost to a zero-cost adapter lane.",
        ),
    ]


def _lease(
    state_dir: Path,
    *,
    mode: TrustMode,
    domain: AuthorityDomain,
    capability: AuthorityCapability,
) -> tuple[AuthorityLeaseStore, Any]:
    store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=mode,
            requested_domains={domain: [capability]},
            authority_constraints=_constraints(),
            decision_reason_ref="reason-ref:test-authority-dispatch-lease",
            safe_summary="Issue an exact governed dispatcher test lease.",
        ),
        idempotency_ref=(
            f"idempotency-ref:test-dispatch-lease:{mode.value}:{domain.value}"
        ),
    )
    assert lease is not None
    assert receipt.status == "issued"
    return store, lease


def _descriptor(*, filesystem: bool) -> AuthorityDispatchAdapterDescriptor:
    if filesystem:
        return AuthorityDispatchAdapterDescriptor(
            adapter_ref=FILESYSTEM_ADAPTER_REF,
            domain=AuthorityDomain.files,
            capability=AuthorityCapability.read,
            capability_ref=FILESYSTEM_CAPABILITY_REF,
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            rollback_ref="rollback-ref:filesystem-metadata-no-mutation",
            safe_disable_ref="safe-disable-ref:filesystem-metadata-adapter",
            safe_summary="Read bounded metadata from an injected safe filesystem root.",
        )
    return AuthorityDispatchAdapterDescriptor(
        adapter_ref=NOOP_ADAPTER_REF,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
        capability_ref=NOOP_CAPABILITY_REF,
        tool_ref=NOOP_TOOL_REF,
        approval_required=True,
        rollback_ref="rollback-ref:governed-noop-no-effect",
        safe_disable_ref="safe-disable-ref:governed-noop-adapter",
        safe_summary="Execute a deterministic no-effect adapter behind exact approval.",
    )


def _action(
    *,
    suffix: str,
    filesystem: bool,
) -> AuthorityActionRequest:
    return AuthorityActionRequest(
        action_ref=f"authority-action-ref:test-dispatch:{suffix}",
        domain=(AuthorityDomain.files if filesystem else AuthorityDomain.workspace),
        capability=(AuthorityCapability.read if filesystem else AuthorityCapability.execute),
        capability_ref=(FILESYSTEM_CAPABILITY_REF if filesystem else NOOP_CAPABILITY_REF),
        adapter_ref=(FILESYSTEM_ADAPTER_REF if filesystem else NOOP_ADAPTER_REF),
        resource_refs=[f"resource-ref:test-dispatch:{suffix}"],
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=1,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
        ],
        safe_summary="Perform one exact zero-cost governed dispatch action.",
    )


def _request(
    lease_ref: str,
    *,
    suffix: str,
    filesystem: bool,
    approval_validation_request: Any | None = None,
) -> AuthorityDispatchRequest:
    dispatch_ref = f"authority-dispatch-ref:test:{suffix}"
    idempotency_ref = f"idempotency-ref:test-dispatch:{suffix}"
    run_ref = f"run-ref:test-dispatch:{suffix}"
    cost_estimate = CostEstimate(
        estimate_id=f"cost-estimate:test-dispatch:{suffix}",
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
    )
    cost_budgets = [
        CostBudget(
            budget_id=f"cost-budget:test-dispatch:{suffix}",
            scope=BudgetScope.run,
            scope_id=run_ref,
            max_cost_usd=1,
            max_total_tokens=1,
        )
    ]
    if filesystem:
        tool_request = ToolInvocationRequest(
            invocation_id=dispatch_ref,
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            tool_name=FILESYSTEM_METADATA_TOOL_NAME,
            invocation_kind=ToolInvocationKind.filesystem_metadata,
            replay_key=idempotency_ref,
            safe_summary="Inspect bounded metadata under an injected safe root.",
            input_refs=[f"input-ref:test-dispatch:{suffix}"],
            metadata={
                "root_ref": "safe-root:test-authority",
                "relative_path": "notes/report.md",
            },
        )
    else:
        tool_request = ToolInvocationRequest(
            invocation_id=dispatch_ref,
            tool_ref=NOOP_TOOL_REF,
            tool_name=NOOP_TOOL_NAME,
            invocation_kind=ToolInvocationKind.noop,
            replay_key=idempotency_ref,
            safe_summary="Execute a deterministic no-effect governed invocation.",
            input_refs=[f"input-ref:test-dispatch:{suffix}"],
        )
    return AuthorityDispatchRequest(
        dispatch_ref=dispatch_ref,
        run_ref=run_ref,
        idempotency_ref=idempotency_ref,
        lease_ref=lease_ref,
        adapter_ref=(FILESYSTEM_ADAPTER_REF if filesystem else NOOP_ADAPTER_REF),
        action_request=_action(suffix=suffix, filesystem=filesystem),
        tool_invocation_request=tool_request.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=cost_estimate,
        cost_budgets=cost_budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(cost_estimate),
        cost_governor_decision_ref=build_authority_dispatch_cost_governor_decision_ref(
            cost_estimate,
            cost_budgets,
        ),
        cost_governor_allowed=True,
        approval_validation_request=approval_validation_request,
        safe_summary="Run one exact governed dispatcher request.",
    )


def _approval(
    authority: LocalApprovalAuthority,
    request: AuthorityDispatchRequest,
    *,
    resource_refs: list[str] | None = None,
) -> Any:
    approval_request = authority.create_request(
        ApprovalRequest(
            approval_request_id=f"approval-request-ref:test-dispatch:{request.dispatch_ref.rsplit(':', 1)[-1]}",
            run_id=request.run_ref,
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=request.action_request.action_ref,
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="operator-ref:test-dispatch",
                authority_source=AuthoritySource.explicit_user_request,
            ),
            requested_action=request.action_request.action_ref,
            purpose="Approve one exact governed dispatcher action.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.system_internal,
                source="authority_dispatch_test",
                requires_redaction=True,
            ),
            resource_refs=(
                resource_refs
                if resource_refs is not None
                else [
                    request.lease_ref,
                    request.adapter_ref,
                    *request.action_request.resource_refs,
                ]
            ),
        )
    )
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:test-dispatch-approver",
        approval_ref=(
            f"approval-ref:test-dispatch:{request.dispatch_ref.rsplit(':', 1)[-1]}"
        ),
    )
    return approval_request.to_validation_request(grant.approval_ref)


def test_filesystem_metadata_dispatch_is_useful_durable_and_redacted(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    target = root / "notes" / "report.md"
    target.parent.mkdir(parents=True)
    raw_body = "raw body must never enter durable dispatcher evidence"
    target.write_text(raw_body, encoding="utf-8")
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
    request = _request(lease.lease_ref, suffix="metadata", filesystem=True)

    result = dispatcher.dispatch(request)
    replay = dispatcher.dispatch(request)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert result.adapter_result is not None
    assert result.adapter_result.safe_output["exists"] is True
    assert result.adapter_result.safe_output["path_kind"] == "file"
    assert result.adapter_result.safe_output["size_bytes"] == len(raw_body)
    assert result.adapter_result.safe_output["safe_path_ref"].endswith(
        "/notes/report.md"
    )
    assert replay.replayed is True
    assert replay.receipt.receipt_ref == result.receipt.receipt_ref
    assert len(dispatcher.list_receipts()) == 3
    budget_receipts = dispatcher.budget_store.list_receipts()
    assert [receipt.status for receipt in budget_receipts] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.settled.value,
    ]
    durable_text = dispatcher.receipts_path.read_text(encoding="utf-8")
    assert raw_body not in durable_text
    assert str(root) not in durable_text
    read_model = dispatcher.build_read_model()
    assert read_model.receipt_count == 3
    assert read_model.recovery_required_dispatch_refs == []


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
    assert cancelled.receipt.adapter_execution_performed is False
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
    assert len(dispatcher.budget_store.list_receipts()) == 2


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


def test_concurrent_budget_replay_does_not_release_winner_reservation(
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
    first = _request(lease.lease_ref, suffix="shared-reservation", filesystem=True)
    second_payload = first.model_dump(mode="json")
    second_payload["tool_invocation_request"]["metadata"]["relative_path"] = (
        "notes/alternate.md"
    )
    second = AuthorityDispatchRequest.model_validate(second_payload)
    fresh_reserved = threading.Event()
    replay_claimed = threading.Event()
    reservation_statuses: dict[int, str] = {}
    statuses_lock = threading.Lock()
    reserve = dispatcher.budget_store.reserve

    def synchronized_reserve(*args: Any, **kwargs: Any) -> Any:
        receipt = reserve(*args, **kwargs)
        with statuses_lock:
            reservation_statuses[threading.get_ident()] = receipt.status
        if receipt.status == AuthorityBudgetStatus.reserved.value:
            fresh_reserved.set()
            assert replay_claimed.wait(timeout=5)
        else:
            assert receipt.status == AuthorityBudgetStatus.replayed.value
            assert fresh_reserved.wait(timeout=5)
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
            if status == AuthorityBudgetStatus.replayed.value:
                replay_claimed.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, [first, second]))

    prepared = next(result for result in results if result is not None)
    budget_receipts = dispatcher.budget_store.list_receipts()

    assert sum(result is None for result in results) == 1
    assert [receipt.status for receipt in budget_receipts] == [
        AuthorityBudgetStatus.reserved.value
    ]
    assert (
        prepared.receipt.budget_reservation_ref
        == budget_receipts[0].reservation_ref
    )


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
