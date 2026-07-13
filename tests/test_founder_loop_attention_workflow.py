from pathlib import Path

import pytest

from ultimate_ai_agent.core.authority import AuthorityLeaseRevokeRequest
from ultimate_ai_agent.core.control_center.founder_loop_attention_workflow import (
    FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF,
    FounderLoopAttentionWorkflow,
    FounderLoopAttentionWorkflowRequest,
    FounderLoopAttentionWorkflowStatus,
    _attention_action_definition_ref,
    attention_execution_owner_ref,
    attention_workflow_operator_request_ref,
)
from ultimate_ai_agent.core.storage.founder_loop import FounderLoopRepository
from ultimate_ai_agent.core.storage.founder_loop_exact_action import (
    FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,
)
from tests.test_founder_loop_filesystem_mission import _service_fixture


TODAY_ITEM_REF = FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF
WORKFLOW_REF = "founder-loop-attention-workflow:test"


def test_execution_owner_ref_binds_proposal_and_idempotency() -> None:
    first = attention_execution_owner_ref(
        proposal_ref="action-proposal-ref:founder-loop-attention:test",
        idempotency_ref="idempotency-ref:founder-loop-attention:first",
    )
    replay = attention_execution_owner_ref(
        proposal_ref="action-proposal-ref:founder-loop-attention:test",
        idempotency_ref="idempotency-ref:founder-loop-attention:first",
    )
    changed = attention_execution_owner_ref(
        proposal_ref="action-proposal-ref:founder-loop-attention:test",
        idempotency_ref="idempotency-ref:founder-loop-attention:changed",
    )

    assert replay == first
    assert changed != first
    assert first.startswith("mission-owner-ref:founder-loop-attention:sha256:")


def _workflow_fixture(tmp_path: Path, *, suffix: str, review_sources: bool = True):
    service, _, _, _, mission_request, _, root_path = _service_fixture(
        tmp_path,
        suffix=suffix,
    )
    repository = FounderLoopRepository(tmp_path / "founder-loop")
    action = next(
        item
        for item in repository.list_action_inbox(limit=20)
        if item["item_ref"] == TODAY_ITEM_REF
    )
    target = service.targets[mission_request.target_ref]
    source_refs = tuple(
        sorted(
            {
                TODAY_ITEM_REF,
                target.target_ref,
                target.path_ref,
                *action["evidence_refs"],
            }
        )
    )
    workflow = FounderLoopAttentionWorkflow(
        repository=repository,
        mission_service=service,
    )
    source_review_receipt_ref = (
        "source-review-receipt-ref:founder-loop-attention:missing"
    )
    if review_sources:
        source_review_receipt_ref = workflow.review_source_refs(
            today_item_ref=TODAY_ITEM_REF,
            inspected_source_refs=source_refs,
            idempotency_ref=f"idempotency-ref:attention-inspection:{suffix}",
            mission_ref=mission_request.mission_ref,
            lease_ref=mission_request.lease_ref,
        ).source_review_receipt_ref
    operator_request_ref = attention_workflow_operator_request_ref(
        workflow_ref=WORKFLOW_REF,
        today_item_ref=TODAY_ITEM_REF,
        inspected_source_refs=source_refs,
        source_review_receipt_ref=source_review_receipt_ref,
        proposal_ref=mission_request.proposal_ref,
        target_ref=mission_request.target_ref,
    )
    request = FounderLoopAttentionWorkflowRequest(
        workflow_ref=WORKFLOW_REF,
        today_item_ref=TODAY_ITEM_REF,
        inspected_source_refs=source_refs,
        source_review_receipt_ref=source_review_receipt_ref,
        mission_request=mission_request.model_copy(
            update={"operator_request_ref": operator_request_ref}
        ),
    )
    return (
        workflow,
        repository,
        request,
        root_path,
    )


def test_attention_workflow_refreshes_today_after_exact_receipt(tmp_path: Path) -> None:
    workflow, repository, request, root_path = _workflow_fixture(
        tmp_path,
        suffix="attention-success",
    )
    required_source_refs = workflow.required_source_refs(TODAY_ITEM_REF)
    prepared = workflow.prepare(request)
    assert workflow.required_source_refs(TODAY_ITEM_REF) == required_source_refs
    approval_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:success",
    )
    assert workflow.required_source_refs(TODAY_ITEM_REF) == required_source_refs

    result = workflow.execute(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approval_ref=approval_ref,
        owner_ref="mission-owner-ref:founder-loop-attention:success",
    )
    replay = workflow.execute(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approval_ref=approval_ref,
        owner_ref="mission-owner-ref:founder-loop-attention:replay",
    )
    prepare_replay = workflow.prepare(request)
    assert workflow.required_source_refs(TODAY_ITEM_REF) == required_source_refs

    today = repository.today_summary(limit=20)
    action = next(
        item for item in today["actions"] if item["item_ref"] == TODAY_ITEM_REF
    )
    assert prepared.status == "awaiting_exact_approval"
    assert action["status"] == "receipt_recorded"
    assert action["item_ref"] == FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF
    assert action["title"] == "Inspect canonical repository overview metadata"
    assert action["action_kind"] == "exact_filesystem_metadata_inspection"
    assert action["state_change_contract_ref"] == (
        FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF
    )
    assert action["state_change_readiness"] == "exact_metadata_inspection_completed"
    assert request.source_review_receipt_ref in action["receipt_refs"]
    assert result.completion_ref in action["receipt_refs"]
    assert result.memory_candidate_ref is None
    assert result.memory_candidate_created is False
    assert result.backend_today_refreshed is True
    assert result.execution_path_ref.endswith(
        "mission-orchestrator-runner-dispatcher-adapter"
    )
    assert replay.completion_ref == result.completion_ref
    assert replay.terminal_replay is True
    assert prepare_replay == prepared
    assert not any(
        item.get("safe_summary", "").startswith("A completed exact metadata inspection")
        for item in today["memory_review_queue"]
    )
    assert str(root_path).encode("utf-8") not in repository.db_path.read_bytes()
    assert b"docs/README.md" not in repository.db_path.read_bytes()
    setup_action = next(
        item
        for item in repository.list_action_inbox(limit=20)
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    assert setup_action["status"] == "review_ready"
    assert setup_action["action_kind"] == "review_only"


def test_prepare_replays_exact_durable_result_without_current_lease(
    tmp_path: Path,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-prepare-replay",
    )
    prepared = workflow.prepare(request)
    workflow.mission_service.lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=request.mission_request.lease_ref,
            decision_reason_ref="reason-ref:attention:prepare-replay-revoked",
            safe_summary="Revoke after the prepared response became durable.",
        ),
        idempotency_ref="idempotency-ref:attention:prepare-replay-revoked",
    )

    replay = workflow.prepare(request)

    assert replay == prepared
    assert len(workflow.mission_service._proposal_store._load()) == 1  # noqa: SLF001


def test_prepare_replay_rejects_changed_request(tmp_path: Path) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-prepare-conflict",
    )
    workflow.prepare(request)
    changed = request.model_copy(
        update={
            "mission_request": request.mission_request.model_copy(
                update={"run_ref": "run-ref:attention:prepare-conflict-changed"}
            )
        }
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_PREPARE_REPLAY_CONFLICT",
    ):
        workflow.prepare(changed)

    assert len(workflow.mission_service._proposal_store._load()) == 1  # noqa: SLF001


def test_second_approval_identifier_replays_the_single_exact_grant(
    tmp_path: Path,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-approval-singleton",
    )
    prepared = workflow.prepare(request)
    original_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:singleton-original",
    )
    assert workflow.prepare(request) == prepared

    replayed_ref = workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop-attention:singleton-second",
    )

    approval_refs = [
        ref
        for ref in workflow.action_status(TODAY_ITEM_REF).audit_refs
        if ref.startswith("approval-ref:founder-loop-attention:")
    ]
    assert replayed_ref == original_ref
    assert len(workflow.mission_service.approval_authority.list_grants()) == 1
    assert approval_refs == [original_ref]
    assert workflow.verified_status(TODAY_ITEM_REF).approval_truth_status != (
        "approval_evidence_ambiguous"
    )


def test_concurrent_approval_identifiers_create_at_most_one_grant(
    tmp_path: Path,
) -> None:
    import threading

    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-approval-concurrent",
    )
    prepared = workflow.prepare(request)
    outcomes: list[str] = []

    def approve(suffix: str) -> None:
        outcomes.append(
            workflow.grant_exact_approval(
                workflow_ref=request.workflow_ref,
                today_item_ref=request.today_item_ref,
                inspected_source_refs=request.inspected_source_refs,
                source_review_receipt_ref=request.source_review_receipt_ref,
                proposal_ref=prepared.proposal_ref,
                approved_by_actor_ref="operator-ref:local-user",
                approval_ref=f"approval-ref:founder-loop-attention:{suffix}",
            )
        )

    threads = [
        threading.Thread(target=approve, args=("concurrent-one",)),
        threading.Thread(target=approve, args=("concurrent-two",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert len(outcomes) == 2
    assert len(set(outcomes)) == 1
    assert len(workflow.mission_service.approval_authority.list_grants()) == 1


def test_attention_workflow_source_inspection_requires_current_exact_lease(
    tmp_path: Path,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-inspection-lease",
        review_sources=False,
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED",
    ):
        workflow.review_source_refs(
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            idempotency_ref="idempotency-ref:attention-inspection:no-lease",
            mission_ref=request.mission_request.mission_ref,
            lease_ref="authority-lease:attention-inspection:missing",
        )

    assert workflow.action_status(TODAY_ITEM_REF).status == "review_ready"


def test_attention_workflow_rejects_uninspected_or_changed_sources(
    tmp_path: Path,
) -> None:
    workflow, repository, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-source-binding",
    )
    changed = request.model_copy(
        update={"inspected_source_refs": request.inspected_source_refs[:-1]}
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_SOURCE_BINDING_REQUIRED",
    ):
        workflow.prepare(changed)

    action = next(
        item
        for item in repository.list_action_inbox(limit=20)
        if item["item_ref"] == TODAY_ITEM_REF
    )
    assert action["status"] == "source_refs_reviewed"
    assert (
        workflow.mission_service.prepared_proposal(request.mission_request.proposal_ref)
        is None
    )


def test_attention_workflow_rechecks_lease_before_prepare_and_approval(
    tmp_path: Path,
) -> None:
    prepare_workflow, _, prepare_request, _ = _workflow_fixture(
        tmp_path / "prepare",
        suffix="attention-revoked-before-prepare",
    )
    prepare_workflow.mission_service.lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=prepare_request.mission_request.lease_ref,
            decision_reason_ref="reason-ref:attention:revoke-before-prepare",
            safe_summary="Revoke the exact lease before workflow preparation.",
        ),
        idempotency_ref="idempotency-ref:attention:revoke-before-prepare",
    )
    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED",
    ):
        prepare_workflow.prepare(prepare_request)
    assert (
        prepare_workflow.action_status(TODAY_ITEM_REF).status == "source_refs_reviewed"
    )

    approval_workflow, _, approval_request, _ = _workflow_fixture(
        tmp_path / "approval",
        suffix="attention-revoked-before-approval",
    )
    prepared = approval_workflow.prepare(approval_request)
    approval_workflow.mission_service.lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=approval_request.mission_request.lease_ref,
            decision_reason_ref="reason-ref:attention:revoke-before-approval",
            safe_summary="Revoke the exact lease before workflow approval.",
        ),
        idempotency_ref="idempotency-ref:attention:revoke-before-approval",
    )
    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED",
    ):
        approval_workflow.grant_exact_approval(
            workflow_ref=approval_request.workflow_ref,
            today_item_ref=approval_request.today_item_ref,
            inspected_source_refs=approval_request.inspected_source_refs,
            source_review_receipt_ref=approval_request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref="approval-ref:founder-loop-attention:revoked-lease",
        )
    assert approval_workflow.action_status(TODAY_ITEM_REF).status == (
        "awaiting_exact_approval"
    )


def test_attention_workflow_approval_identifier_alone_cannot_execute(
    tmp_path: Path,
) -> None:
    workflow, repository, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-approval",
    )
    prepared = workflow.prepare(request)

    with pytest.raises(ValueError, match="FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE"):
        workflow.execute(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approval_ref="approval-ref:founder-loop-attention:identifier-only",
            owner_ref="mission-owner-ref:founder-loop-attention:identifier-only",
        )

    action = next(
        item
        for item in repository.list_action_inbox(limit=20)
        if item["item_ref"] == TODAY_ITEM_REF
    )
    assert action["status"] == "awaiting_exact_approval"
    assert action["state_change_readiness"] == "exact_metadata_mission_prepared"
    assert not any(
        ref.startswith("mission-completion-ref:") for ref in action["receipt_refs"]
    )
    assert not workflow.mission_service.orchestrator.completion_store.list_manifests()


def test_attention_workflow_requires_durable_source_review_receipt(
    tmp_path: Path,
) -> None:
    workflow, repository, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-inspection-required",
        review_sources=False,
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_RECEIPT_REQUIRED",
    ):
        workflow.prepare(request)

    action = workflow.action_status(TODAY_ITEM_REF)
    assert action.status == "review_ready"
    assert not any(
        ref.startswith("source-review-receipt-ref:") for ref in action.receipt_refs
    )
    assert not workflow.mission_service.orchestrator.plan_store.list_receipts()
    assert repository.today_summary(limit=20)["actions"]


def test_attention_workflow_rejects_unrelated_action_items(tmp_path: Path) -> None:
    workflow, _, _, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-unrelated-item",
    )
    with pytest.raises(ValueError, match="FOUNDER_LOOP_ATTENTION_ITEM_NOT_ELIGIBLE"):
        workflow.required_source_refs("founder-action:setup-assistant-hardening")


def test_revoked_approval_cannot_be_restored_by_idempotent_replay(
    tmp_path: Path,
) -> None:
    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-revoked-approval",
    )
    prepared = workflow.prepare(request)
    approval_ref = "approval-ref:founder-loop-attention:revoked-replay"
    workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref=approval_ref,
    )
    workflow.mission_service.approval_authority.revoke(
        approval_ref,
        "operator revoked exact approval",
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_DENIED",
    ):
        workflow.grant_exact_approval(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref=approval_ref,
        )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_DENIED",
    ):
        workflow.grant_exact_approval(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref="approval-ref:founder-loop-attention:revoked-replacement",
        )


def test_approval_replay_waits_for_revocation_critical_section(
    tmp_path: Path,
) -> None:
    import threading

    workflow, _, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-atomic-revocation",
    )
    prepared = workflow.prepare(request)
    approval_ref = "approval-ref:founder-loop-attention:atomic-revocation"
    workflow.grant_exact_approval(
        workflow_ref=request.workflow_ref,
        today_item_ref=request.today_item_ref,
        inspected_source_refs=request.inspected_source_refs,
        source_review_receipt_ref=request.source_review_receipt_ref,
        proposal_ref=prepared.proposal_ref,
        approved_by_actor_ref="operator-ref:local-user",
        approval_ref=approval_ref,
    )
    outcome: list[str] = []

    def replay() -> None:
        try:
            workflow.grant_exact_approval(
                workflow_ref=request.workflow_ref,
                today_item_ref=request.today_item_ref,
                inspected_source_refs=request.inspected_source_refs,
                source_review_receipt_ref=request.source_review_receipt_ref,
                proposal_ref=prepared.proposal_ref,
                approved_by_actor_ref="operator-ref:local-user",
                approval_ref=approval_ref,
            )
        except ValueError as exc:
            outcome.append(str(exc))

    authority = workflow.mission_service.approval_authority
    with authority.hold_validation_lock():
        thread = threading.Thread(target=replay)
        thread.start()
        authority.revoke(approval_ref, "operator revoked during replay")
    thread.join(timeout=2)

    assert outcome == ["FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_DENIED"]
    assert authority.get_grant(approval_ref).status == "revoked"


def test_action_definition_drift_blocks_approval(tmp_path: Path) -> None:
    workflow, repository, request, _ = _workflow_fixture(
        tmp_path,
        suffix="attention-action-drift",
    )
    prepared = workflow.prepare(request)
    action = workflow.action_status(TODAY_ITEM_REF)
    repository.upsert_action(
        action.model_copy(
            update={
                "evidence_refs": [
                    *action.evidence_refs,
                    "evidence-ref:founder-loop:unexpected-drift",
                ]
            }
        )
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_ATTENTION_ACTION_DEFINITION_DRIFT",
    ):
        workflow.grant_exact_approval(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=prepared.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref="approval-ref:founder-loop-attention:drift",
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
    assert status.execution_truth_status == ("completion_or_dispatch_evidence_unknown")
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
