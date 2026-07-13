from pathlib import Path

import pytest

from tests.test_founder_loop_attention_workflow import (
    TODAY_ITEM_REF,
    _workflow_fixture,
)
from ultimate_ai_agent.core.control_center.founder_loop_attention_workflow import (
    FounderLoopAttentionWorkflowStatus,
    _attention_action_definition_ref,
)


def test_status_fails_closed_when_terminal_evidence_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-status-evidence",
    )
    prepared = workflow.prepare(request)
    approval_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:status-evidence",
    )
    workflow.execute(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approval_ref=approval_ref,
        owner_ref="mission-owner-ref:founder-loop-attention:status-evidence",
    )
    monkeypatch.setattr(
        workflow.mission_service.orchestrator.completion_store,
        "list_manifests",
        lambda: [],
    )

    status = workflow.verified_status(TODAY_ITEM_REF)

    assert status.action.status == "receipt_recorded"
    assert status.execution_performed is None
    assert status.execution_truth_status == "completion_or_dispatch_evidence_unknown"
    assert status.recovery_required is True
    assert status.exact_approval_required is True


@pytest.mark.parametrize(
    ("field_name", "substituted_ref"),
    [
        ("plan_ref", "plan-ref:founder-loop-attention:substituted"),
        ("run_ref", "run-ref:founder-loop-attention:substituted"),
    ],
)
def test_terminal_replay_rejects_cross_plan_or_run_completion_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    substituted_ref: str,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix=f"attention-terminal-substitution-{field_name}",
    )
    prepared = workflow.prepare(request)
    approval_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref=(
            f"approval-ref:founder-loop-attention:substitution-{field_name}"
        ),
    )
    workflow.execute(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approval_ref=approval_ref,
        owner_ref=f"mission-owner-ref:founder-loop-attention:{field_name}",
    )
    store = workflow.mission_service.orchestrator.completion_store
    manifest = store.list_manifests()[0]
    monkeypatch.setattr(
        store,
        "list_manifests",
        lambda: [manifest.model_copy(update={field_name: substituted_ref})],
    )
    receipt_count = len(
        workflow.mission_service.orchestrator.runner.dispatcher.list_receipts()
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_TERMINAL_BINDING_DRIFT",
    ):
        workflow.execute(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approval_ref=approval_ref,
            owner_ref=f"mission-owner-ref:founder-loop-attention:{field_name}:replay",
        )

    assert (
        len(workflow.mission_service.orchestrator.runner.dispatcher.list_receipts())
        == receipt_count
    )


def test_terminal_approval_drift_never_creates_a_new_grant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow, repository, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-terminal-approval-drift",
    )
    prepared = workflow.prepare(request)
    approval_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:terminal-drift",
    )
    workflow.execute(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approval_ref=approval_ref,
        owner_ref="mission-owner-ref:founder-loop-attention:terminal-drift",
    )
    action = workflow.action_status(TODAY_ITEM_REF)
    target = workflow.mission_service.targets[prepared.target_ref]
    evidence_refs = [
        ref
        for ref in action.evidence_refs
        if not ref.startswith("action-definition-ref:founder-loop-attention:")
    ]
    without_approval = action.model_copy(
        update={"audit_refs": [], "evidence_refs": evidence_refs}
    )
    definition_ref = _attention_action_definition_ref(
        action=without_approval,
        target_ref=target.target_ref,
        path_ref=target.path_ref,
    )
    repository.upsert_action(
        without_approval.model_copy(
            update={"evidence_refs": [*evidence_refs, definition_ref]}
        )
    )
    authority = workflow.mission_service.approval_authority
    grant_called = False

    def unexpected_grant(*_args: object, **_kwargs: object) -> None:
        nonlocal grant_called
        grant_called = True

    monkeypatch.setattr(authority, "list_grants", lambda: [])
    monkeypatch.setattr(authority, "grant", unexpected_grant)

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_TERMINAL_APPROVAL_BINDING_DRIFT",
    ):
        workflow.grant_exact_approval(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref="approval-ref:founder-loop-attention:replacement",
        )

    assert grant_called is False


def test_execute_does_not_return_success_without_terminal_evidence_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-execute-evidence-boundary",
    )
    prepared = workflow.prepare(request)
    approval_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:execute-evidence-boundary",
    )
    unavailable_status = FounderLoopAttentionWorkflowStatus(
        action=workflow.action_status(TODAY_ITEM_REF),
        execution_performed=None,
        exact_approval_required=True,
        recovery_required=True,
        execution_truth_status="completion_or_dispatch_evidence_unknown",
        approval_truth_status="recorded_approval_not_current",
    )
    monkeypatch.setattr(
        workflow, "verified_status", lambda _item_ref: unavailable_status
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_TERMINAL_EVIDENCE_UNVERIFIED",
    ):
        workflow.execute(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approval_ref=approval_ref,
            owner_ref=(
                "mission-owner-ref:founder-loop-attention:execute-evidence-boundary"
            ),
        )

    status = workflow.verified_status(TODAY_ITEM_REF)
    assert status.execution_performed is None
    assert status.recovery_required is True
