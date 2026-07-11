from __future__ import annotations

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
    AuthorityDispatchRequest,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
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
from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    NOOP_TOOL_NAME,
    NOOP_TOOL_REF,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    filesystem_safe_path_ref,
)


FILESYSTEM_ADAPTER_REF = "authority-adapter-ref:filesystem-metadata-v1"
FILESYSTEM_CAPABILITY_REF = "authority-capability-ref:filesystem-metadata-v1"
NOOP_ADAPTER_REF = "authority-adapter-ref:governed-noop-v1"
NOOP_CAPABILITY_REF = "authority-capability-ref:governed-noop-v1"
FILESYSTEM_ROOT_REF = "safe-root:test-authority"
FILESYSTEM_PATH_REF = filesystem_safe_path_ref(
    FILESYSTEM_ROOT_REF, "notes/report.md"
)


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
    authority_constraints: list[AuthorityConstraint] | None = None,
) -> tuple[AuthorityLeaseStore, Any]:
    store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=mode,
            requested_domains={domain: [capability]},
            authority_constraints=(
                authority_constraints
                if authority_constraints is not None
                else _constraints()
            ),
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
        resource_refs=[
            f"resource-ref:test-dispatch:{suffix}",
            *(
                [FILESYSTEM_ROOT_REF, FILESYSTEM_PATH_REF]
                if filesystem
                else []
            ),
        ],
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=1,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
            *(
                [
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.path_refs,
                        refs=[FILESYSTEM_PATH_REF],
                    )
                ]
                if filesystem
                else []
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
                "root_ref": FILESYSTEM_ROOT_REF,
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


def test_tool_runtime_dispatch_bridge_rejects_unscoped_tool() -> None:
    descriptor = _descriptor(filesystem=True).model_copy(
        update={"tool_ref": "tool-ref:unscoped-runtime-tool"}
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_DISPATCH_TOOL_NOT_ALLOWLISTED",
    ):
        ToolRuntimeAuthorityDispatchAdapter(descriptor)


def test_dispatcher_rejects_tool_relabelled_into_another_authority_domain(
    tmp_path: Path,
) -> None:
    descriptor = _descriptor(filesystem=True).model_copy(
        update={
            "domain": AuthorityDomain.email,
            "capability": AuthorityCapability.observe,
        }
    )

    class RelabelledAdapter:
        binding_ref = "adapter-binding-ref:test:relabelled"

        def __init__(self) -> None:
            self.descriptor = descriptor

        def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
            return []

        def invoke(self, request: AuthorityDispatchRequest) -> Any:
            raise AssertionError("cross-domain tool binding must never invoke")

    with pytest.raises(
        ValueError,
        match="AUTHORITY_DISPATCH_TOOL_AUTHORITY_BINDING_INVALID",
    ):
        AuthorityDispatcher(tmp_path / "authority", adapters=[RelabelledAdapter()])


def test_tool_runtime_adapter_binding_owns_implementation_and_manifest() -> None:
    descriptor = _descriptor(filesystem=False)
    adapter = ToolRuntimeAuthorityDispatchAdapter(descriptor)
    original_binding = adapter.binding_ref

    descriptor.safe_summary = "Caller-mutated descriptor summary."
    returned = adapter.descriptor
    returned.safe_summary = "Mutated returned descriptor summary."

    assert adapter.binding_ref == original_binding
    assert adapter.descriptor.safe_summary not in {
        descriptor.safe_summary,
        returned.safe_summary,
    }
    assert ToolRuntimeAuthorityDispatchAdapter.IMPLEMENTATION_REF.startswith(
        "adapter-implementation-ref:"
    )


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
    assert result.adapter_result.safe_output["safe_path_ref"] == FILESYSTEM_PATH_REF
    assert replay.replayed is True
    assert replay.receipt.receipt_ref == result.receipt.receipt_ref
    assert len(dispatcher.list_receipts()) == 3
    budget_receipts = dispatcher.budget_store.list_receipts()
    assert [receipt.status for receipt in budget_receipts] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.started.value,
        AuthorityBudgetStatus.settled.value,
    ]
    durable_text = dispatcher.receipts_path.read_text(encoding="utf-8")
    assert raw_body not in durable_text
    assert str(root) not in durable_text
    read_model = dispatcher.build_read_model()
    assert read_model.receipt_count == 3
    assert read_model.recovery_required_dispatch_refs == []


def test_tool_runtime_policy_denial_happens_before_reservation_or_start(
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
        suffix="runtime-preflight-denial",
        filesystem=True,
    )
    payload = request.model_dump(mode="json")
    payload["tool_invocation_request"]["metadata"]["include_raw_content"] = True

    result = dispatcher.dispatch(AuthorityDispatchRequest.model_validate(payload))

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert result.receipt.execution_started is False
    assert result.receipt.adapter_invocation_performed is False
    assert (
        "reason-ref:authority-dispatch:tool-runtime-preflight-denied"
        in result.receipt.reason_refs
    )
    assert dispatcher.budget_store.list_receipts() == []


@pytest.mark.parametrize(
    ("target_field", "target_value", "reason_ref"),
    [
        (
            "root_ref",
            "safe-root:test-other",
            "reason-ref:authority-dispatch:filesystem-root-unbound",
        ),
        (
            "relative_path",
            "notes/other.md",
            "reason-ref:authority-dispatch:filesystem-path-unbound",
        ),
    ],
)
def test_filesystem_target_must_match_action_and_lease_claims(
    tmp_path: Path,
    target_field: str,
    target_value: str,
    reason_ref: str,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    other_root = tmp_path / "other-safe-root"
    (root / "notes").mkdir(parents=True)
    (other_root / "notes").mkdir(parents=True)
    resource_ref = "resource-ref:test-dispatch:target-binding"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
        authority_constraints=[
            *_constraints(),
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:test-dispatch-resources",
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=[
                    resource_ref,
                    FILESYSTEM_ROOT_REF,
                    FILESYSTEM_PATH_REF,
                ],
                safe_summary="Allow one exact filesystem root resource.",
            ),
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:test-dispatch-paths",
                kind=AuthorityConstraintKind.path_refs,
                allowed_refs=[FILESYSTEM_PATH_REF],
                safe_summary="Allow one exact normalized filesystem path.",
            ),
        ],
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
                        safe_label="Allowed dispatch safe root",
                    ),
                    FilesystemSafeRoot(
                        root_ref="safe-root:test-other",
                        root_path=other_root,
                        safe_label="Other injected safe root",
                    ),
                ],
            )
        ],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="target-binding", filesystem=True)
    payload = request.model_dump(mode="json")
    payload["tool_invocation_request"]["metadata"][target_field] = target_value
    drifted = AuthorityDispatchRequest.model_validate(payload)

    result = dispatcher.prepare(drifted)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert reason_ref in result.receipt.reason_refs
    assert dispatcher.budget_store.list_receipts() == []


def test_filesystem_path_resource_is_bound_to_exact_approval(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    alternate_path_ref = filesystem_safe_path_ref(
        FILESYSTEM_ROOT_REF, "notes/other.md"
    )
    resource_ref = "resource-ref:test-dispatch:approval-target"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
        authority_constraints=[
            *_constraints(),
            AuthorityConstraint(
                constraint_ref=(
                    "authority-constraint-ref:test-dispatch-approval-resources"
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=[
                    resource_ref,
                    FILESYSTEM_ROOT_REF,
                    FILESYSTEM_PATH_REF,
                    alternate_path_ref,
                ],
                safe_summary="Allow two exact filesystem targets for approval proof.",
            ),
            AuthorityConstraint(
                constraint_ref="authority-constraint-ref:test-dispatch-approval-paths",
                kind=AuthorityConstraintKind.path_refs,
                allowed_refs=[FILESYSTEM_PATH_REF, alternate_path_ref],
                safe_summary="Allow two exact normalized paths for approval proof.",
            ),
        ],
    )
    approval_authority = LocalApprovalAuthority()
    descriptor = _descriptor(filesystem=True).model_copy(
        update={"approval_required": True}
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[
            ToolRuntimeAuthorityDispatchAdapter(
                descriptor,
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
        approval_authority=approval_authority,
    )
    pending = _request(lease.lease_ref, suffix="approval-target", filesystem=True)
    validation_request = _approval(approval_authority, pending)
    payload = pending.model_dump(mode="json")
    payload["approval_validation_request"] = validation_request.model_dump(mode="json")
    payload["action_request"]["resource_refs"] = [
        alternate_path_ref if ref == FILESYSTEM_PATH_REF else ref
        for ref in payload["action_request"]["resource_refs"]
    ]
    for claim in payload["action_request"]["constraint_claims"]:
        if claim["kind"] == AuthorityConstraintKind.path_refs.value:
            claim["refs"] = [alternate_path_ref]
    payload["tool_invocation_request"]["metadata"]["relative_path"] = (
        "notes/other.md"
    )
    drifted = AuthorityDispatchRequest.model_validate(payload)

    result = dispatcher.prepare(drifted)
    budget_receipts = dispatcher.budget_store.list_receipts()

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert (
        "reason-ref:authority-budget:approval-resource-mismatch"
        in result.receipt.reason_refs
    )
    assert [receipt.status for receipt in budget_receipts] == [
        AuthorityBudgetStatus.denied.value
    ]
