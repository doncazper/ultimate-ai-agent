from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.control_center.founder_loop_mission import (
    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
    FounderLoopFilesystemMissionRequest,
    FounderLoopFilesystemMissionService,
    FounderLoopFilesystemTarget,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import (
    FilesystemSafeRoot,
    filesystem_opaque_path_ref,
)


def _service_fixture(tmp_path: Path, *, suffix: str):
    state_dir = tmp_path / "authority"
    root_path = tmp_path / "repository-root"
    (root_path / "docs").mkdir(parents=True)
    (root_path / "docs" / "README.md").write_text(
        "private content must never persist",
        encoding="utf-8",
    )
    root_ref = f"safe-root:founder-loop:{suffix}"
    target_ref = f"target-ref:founder-loop:{suffix}"
    path_ref = filesystem_opaque_path_ref(root_ref, "docs/README.md")
    target = FounderLoopFilesystemTarget(
        target_ref=target_ref,
        root_ref=root_ref,
        relative_path="docs/README.md",
        path_ref=path_ref,
        safe_label="Canonical documentation artifact",
    )
    lease_store = AuthorityLeaseStore(state_dir)
    mission_ref = f"mission-ref:founder-loop:{suffix}"
    lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=mission_ref,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=f"constraint-ref:founder-loop:{suffix}:resources",
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=[
                        FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
                        FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                        target_ref,
                        root_ref,
                        path_ref,
                        mission_ref,
                    ],
                    safe_summary="Allow only the exact Founder Loop lane resources.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"constraint-ref:founder-loop:{suffix}:path",
                    kind=AuthorityConstraintKind.path_refs,
                    allowed_refs=[path_ref],
                    safe_summary="Allow only the predeclared metadata path ref.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"constraint-ref:founder-loop:{suffix}:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Allow one metadata operation for this mission.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"constraint-ref:founder-loop:{suffix}:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Bound this zero-cost mission to one micro-unit ceiling.",
                ),
            ],
            decision_reason_ref=f"reason-ref:founder-loop:{suffix}:lease",
            safe_summary="Issue one exact metadata-only mission lease.",
        ),
        idempotency_ref=f"idempotency-ref:founder-loop:{suffix}:lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    approval_authority = LocalApprovalAuthority()
    readiness = {"status": "ready"}
    service = FounderLoopFilesystemMissionService(
        state_dir=state_dir,
        root=FilesystemSafeRoot(
            root_ref=root_ref,
            root_path=root_path,
            safe_label="Founder Loop repository root",
        ),
        targets=(target,),
        lease_store=lease_store,
        approval_authority=approval_authority,
        readiness=lambda: readiness["status"],  # type: ignore[return-value]
    )
    request = FounderLoopFilesystemMissionRequest(
        operator_request_ref=f"operator-request-ref:founder-loop:{suffix}",
        intent_ref=f"intent-ref:founder-loop:{suffix}",
        plan_lineage_ref=f"plan-lineage-ref:founder-loop:{suffix}",
        plan_revision_ref=f"plan-revision-ref:founder-loop:{suffix}:1",
        proposal_ref=f"action-proposal-ref:founder-loop:{suffix}",
        mission_ref=mission_ref,
        run_ref=f"run-ref:founder-loop:{suffix}",
        plan_ref=f"mission-plan-ref:founder-loop:{suffix}",
        step_ref=f"mission-step-ref:founder-loop:{suffix}:1",
        target_ref=target_ref,
        lease_ref=lease.lease_ref,
        start_deadline=utc_now() + timedelta(minutes=10),
        safe_goal_summary="Inspect metadata for the selected repository artifact.",
    )
    return (
        service,
        approval_authority,
        lease_store,
        lease,
        request,
        readiness,
        root_path,
    )


def test_founder_loop_metadata_mission_completes_end_to_end_with_review_candidate(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, root_path = _service_fixture(
        tmp_path,
        suffix="success",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:success",
    )

    result = service.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:success",
    )
    replay = service.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:success-replay",
    )

    assert result.intent_truth.authority_posture == "non_authoritative_review_truth"
    assert result.plan_revision.authority_posture == "non_authoritative_plan_truth"
    assert result.proposal.policy_posture == "approval_required"
    assert result.proposal.execution_authorized is False
    assert result.orchestration.status == "succeeded"
    assert result.orchestration.invoked_step_count == 1
    assert result.completion.completion_ref == replay.completion.completion_ref
    assert result.completion.approval_refs == (grant.approval_ref,)
    assert result.completion.budget_bindings[0].actual_cost_microusd == 0
    assert result.memory_candidate.review_status == "review_required"
    assert result.memory_candidate.recall_only is True
    assert result.memory_candidate.accepted_as_truth is False
    assert result.memory_candidate.memory_write_performed is False
    assert result.authority_minted_by_facade is False
    assert result.raw_path_persisted is False
    assert len(service.orchestrator.completion_store.list_manifests()) == 1
    persisted = "\n".join(
        path.read_text(encoding="utf-8")
        for path in service.orchestrator.step_store.state_dir.rglob("*")
        if path.is_file()
    )
    assert str(root_path) not in persisted
    assert "docs/README.md" not in persisted
    assert "private content must never persist" not in persisted


def test_approval_identifier_alone_does_not_authorize_founder_loop_mission(
    tmp_path: Path,
) -> None:
    service, _, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="approval-identifier",
    )
    prepared = service.prepare(request)

    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE"):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref="approval-ref:founder-loop:identifier-only",
            owner_ref="mission-owner-ref:founder-loop:identifier-only",
        )
    assert not service.orchestrator.completion_store.list_manifests()
    assert not any(
        receipt.adapter_invocation_performed
        for receipt in service.orchestrator.runner.dispatcher.list_receipts()
    )


@pytest.mark.parametrize("blocked_status", ["safe_disabled", "unknown"])
def test_safe_disable_and_unknown_readiness_fail_before_mission_mutation(
    tmp_path: Path,
    blocked_status: str,
) -> None:
    service, approval_authority, _, _, request, readiness, _ = _service_fixture(
        tmp_path,
        suffix=f"readiness-{blocked_status}",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref=f"approval-ref:founder-loop:{blocked_status}",
    )
    readiness["status"] = blocked_status

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_STRUCTURAL_PREFLIGHT_DENIED",
    ):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref=f"mission-owner-ref:founder-loop:{blocked_status}",
        )
    assert not service.orchestrator.plan_store.list_receipts()
    assert not service.orchestrator.runner.dispatcher.list_receipts()


def test_caller_cannot_select_an_unregistered_filesystem_target(tmp_path: Path) -> None:
    service, _, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="unknown-target",
    )
    changed = request.model_copy(
        update={"target_ref": "target-ref:founder-loop:not-registered"}
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_FILESYSTEM_TARGET_NOT_PREDECLARED",
    ):
        service.prepare(changed)


def test_repository_root_identity_drift_fails_closed_before_start(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, root_path = _service_fixture(
        tmp_path,
        suffix="root-drift",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:root-drift",
    )
    moved = root_path.with_name("repository-root-original")
    root_path.rename(moved)
    root_path.mkdir()

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_STRUCTURAL_PREFLIGHT_DENIED",
    ):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:root-drift",
        )
    assert not service.orchestrator.plan_store.list_receipts()


def test_revoked_lease_and_kill_switch_block_before_adapter_start(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service, approval_authority, lease_store, lease, request, _, _ = _service_fixture(
        tmp_path,
        suffix="lease-revoked",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:lease-revoked",
    )
    lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref="reason-ref:founder-loop:lease-revoked",
            safe_summary="Revoke the exact metadata mission lease.",
        ),
        idempotency_ref="idempotency-ref:founder-loop:lease-revoked",
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_POLICY_PREFLIGHT_DENIED",
    ):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:lease-revoked",
        )
    assert not service.orchestrator.runner.dispatcher.list_receipts()

    second = _service_fixture(tmp_path / "kill", suffix="kill-switch")
    kill_service, kill_approval, _, _, kill_request, _, _ = second
    kill_prepared = kill_service.prepare(kill_request)
    kill_grant = kill_approval.grant(
        kill_prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:kill-switch",
    )
    monkeypatch.setenv("UAA_AUTHORITY_LEASE_KILL_SWITCH", "1")
    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_POLICY_PREFLIGHT_DENIED",
    ):
        kill_service.execute(
            proposal_ref=kill_prepared.proposal.proposal_ref,
            approval_ref=kill_grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:kill-switch",
        )
    assert not kill_service.orchestrator.runner.dispatcher.list_receipts()


def test_revoked_action_approval_blocks_without_adapter_invocation(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="approval-revoked",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:approval-revoked",
    )
    approval_authority.revoke(
        grant.approval_ref,
        "Operator revoked the exact metadata mission approval.",
    )

    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE"):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:approval-revoked",
        )
    assert not any(
        receipt.adapter_invocation_performed
        for receipt in service.orchestrator.runner.dispatcher.list_receipts()
    )


def test_terminal_replay_reports_historical_start_validation_not_fresh_authority(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="terminal-replay-truth",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:terminal-replay-truth",
    )
    first = service.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:terminal-replay-truth:first",
    )
    approval_authority.revoke(
        grant.approval_ref,
        "Revoke after the exact terminal result was recorded.",
    )
    replay = service.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:terminal-replay-truth:replay",
    )

    assert first.terminal_replay is False
    assert replay.terminal_replay is True
    assert replay.orchestration.replayed_step_count == 1
    assert replay.recorded_start_approval_validated is True
    assert replay.recorded_start_policy_rechecked is True
    assert replay.replay_mints_current_authority is False


def test_mission_operation_budget_exhaustion_blocks_second_plan(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="budget-exhaustion",
    )
    first = service.prepare(request)
    first_grant = approval_authority.grant(
        first.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:budget-exhaustion:first",
    )
    service.execute(
        proposal_ref=first.proposal.proposal_ref,
        approval_ref=first_grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:budget-exhaustion:first",
    )
    second_request = request.model_copy(
        update={
            "operator_request_ref": "operator-request-ref:founder-loop:budget-second",
            "intent_ref": "intent-ref:founder-loop:budget-second",
            "plan_lineage_ref": "plan-lineage-ref:founder-loop:budget-second",
            "plan_revision_ref": "plan-revision-ref:founder-loop:budget-second:1",
            "proposal_ref": "action-proposal-ref:founder-loop:budget-second",
            "run_ref": "run-ref:founder-loop:budget-second",
            "plan_ref": "mission-plan-ref:founder-loop:budget-second",
            "step_ref": "mission-step-ref:founder-loop:budget-second:1",
        }
    )
    second = service.prepare(second_request)
    second_grant = approval_authority.grant(
        second.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:budget-exhaustion:second",
    )

    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE"):
        service.execute(
            proposal_ref=second.proposal.proposal_ref,
            approval_ref=second_grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:budget-exhaustion:second",
        )
    assert (
        sum(
            receipt.adapter_invocation_performed
            for receipt in service.orchestrator.runner.dispatcher.list_receipts()
        )
        == 1
    )
    assert len(service.orchestrator.completion_store.list_manifests()) == 1


def test_policy_evidence_is_bound_to_exact_target_and_path(tmp_path: Path) -> None:
    service, _, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="policy-scope",
    )
    prepared = service.prepare(request)
    internal = service._prepared[prepared.proposal.proposal_ref]  # noqa: SLF001
    original = internal.orchestration_request.steps[0].request
    changed_action = original.action_request.model_copy(
        update={
            "resource_refs": [
                "target-ref:founder-loop:changed" if ref == request.target_ref else ref
                for ref in original.action_request.resource_refs
            ],
            "constraints": {
                **original.action_request.constraints,
                "target_ref": "target-ref:founder-loop:changed",
            },
        }
    )
    changed_tool = {
        **original.tool_invocation_request,
        "metadata": {
            **original.tool_invocation_request["metadata"],
            "relative_path": "docs/OTHER.md",
        },
    }
    changed = original.model_copy(
        update={
            "action_request": changed_action,
            "tool_invocation_request": changed_tool,
        }
    )

    assert service._lane_adapter._policy_decision_ref(original) != (  # noqa: SLF001
        service._lane_adapter._policy_decision_ref(changed)  # noqa: SLF001
    )


def test_conflicting_prepare_does_not_poison_original_approval_request(
    tmp_path: Path,
) -> None:
    service, approval_authority, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="prepare-conflict",
    )
    original = service.prepare(request)
    changed = request.model_copy(
        update={
            "intent_ref": "intent-ref:founder-loop:prepare-conflict:changed",
            "safe_goal_summary": "Inspect the same target under changed intent truth.",
        }
    )
    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_PROPOSAL_CONFLICT"):
        service.prepare(changed)

    grant = approval_authority.grant(
        original.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:prepare-conflict",
    )
    result = service.execute(
        proposal_ref=original.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:prepare-conflict",
    )
    assert result.orchestration.status == "succeeded"


def test_root_substitution_inside_adapter_invoke_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, approval_authority, _, _, request, _, root_path = _service_fixture(
        tmp_path,
        suffix="root-invoke-drift",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:root-invoke-drift",
    )
    runtime = service._lane_adapter._inner._runtime_adapter  # noqa: SLF001
    original_invoke = runtime.invoke

    def replace_root_then_invoke(*args, **kwargs):
        moved = root_path.with_name("repository-root-approved")
        root_path.rename(moved)
        (root_path / "docs").mkdir(parents=True)
        (root_path / "docs" / "README.md").write_text(
            "replacement content",
            encoding="utf-8",
        )
        return original_invoke(*args, **kwargs)

    monkeypatch.setattr(runtime, "invoke", replace_root_then_invoke)
    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE"):
        service.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:root-invoke-drift",
        )
    assert not service.orchestrator.completion_store.list_manifests()
