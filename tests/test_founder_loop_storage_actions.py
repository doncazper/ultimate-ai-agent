from pathlib import Path
import json

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    action_approval_request,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_POSTURE_REF,
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.memory import MemoryReviewDecisionRequest
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)
from ultimate_ai_agent.core.storage.founder_loop import FounderLoopActionRecord


def _approval_grant_for_request(approval_request, approval_ref: str):
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local-test-reviewer",
        approval_ref=approval_ref,
    )


def _approve_local_task_seed_action(repo: FounderLoopRepository) -> dict[str, object]:
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:test-local-task-action-approval"
    )
    approval_request = action_approval_request(
        item_ref=str(action["item_ref"]),
        actor_context=request.actor_context,
        risk_class=str(action["risk_class"]),
        resource_refs=[
            str(action["item_ref"]),
            str(action["action_envelope_ref"]),
            str(action["action_scope_ref"]),
            str(action["action_approval_requirement_ref"]),
        ],
    )
    grant = _approval_grant_for_request(
        approval_request,
        "approval-ref:test-local-task-action-approve",
    )
    receipt = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            approval_ref=grant.approval_ref,
            approval_grants=[grant],
            decision_reason_ref="decision-reason-ref:test-local-task-action-approval",
        ),
        idempotency_key_ref="idempotency-ref:test-local-task-action-approval",
    )
    assert receipt["status"] == "approved"
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def test_action_inbox_backend_owned_approval_makes_local_task_lane_eligible(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    approval_receipt = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:test-backend-owned-local-task-approval"
        ),
        idempotency_key_ref="idempotency-ref:test-backend-owned-local-task-approval",
    )

    assert approval_receipt["status"] == "approved"
    assert approval_receipt["approval_status"] == "approved"
    assert approval_receipt["approval_ref"].startswith(
        "approval-ref:founder-loop-action:"
    )
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert action["action_group_id"] == "approved_local_task_lane"
    assert action["local_task_commit_eligible"] is True
    assert action["local_task_commit_approval_ref"] == approval_receipt["approval_ref"]
    assert action["receipt_visibility"]["decision_receipt_ref"] == approval_receipt[
        "receipt_ref"
    ]


def _local_task_commit_request_for_action(
    action: dict[str, object],
    *,
    approval_ref: str | None = None,
    metadata_refs: list[str] | None = None,
) -> FounderLoopLocalTaskCommitRequest:
    trusted_approval_ref = approval_ref or str(action["local_task_commit_approval_ref"])
    return FounderLoopLocalTaskCommitRequest(
        approval_ref=trusted_approval_ref,
        decision_reason_ref="decision-reason-ref:test-local-task-commit",
        metadata_refs=metadata_refs or ["metadata-ref:test-local-task-commit"],
    )


def test_action_inbox_local_task_commit_requires_exact_approval_and_records_evidence(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    action = _approve_local_task_seed_action(repo)
    assert action["action_kind"] == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    assert action["local_task_commit_eligible"] is True
    assert (
        action["local_task_safe_disable_ref"]
        == FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
    )
    assert action["local_task_rollback_ref"] == FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
    assert action["local_task_safe_disable_active"] is False
    assert action["local_task_safe_disable_posture_ref"] == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF
    )
    assert action["local_task_rollback_execution_enabled"] is False
    assert action["local_task_rollback_blocker_refs"] == [
        FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF
    ]
    assert action["local_task_safe_disable_posture"]["backend_owned"] is True

    missing_approval = FounderLoopLocalTaskCommitRequest(
        approval_ref="approval-ref:test-local-task-missing"
    )
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED",
    ):
        repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=missing_approval,
            idempotency_key_ref="idempotency-ref:test-local-task-missing",
        )

    request = _local_task_commit_request_for_action(action)
    receipt = repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=request,
        idempotency_key_ref="idempotency-ref:test-local-task-commit",
    )

    assert receipt["contract_ref"] == FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
    assert receipt["action_kind"] == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    assert receipt["status"] == "local_task_created"
    assert receipt["local_task_created"] is True
    assert receipt["safe_disable_ref"] == FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
    assert receipt["rollback_ref"] == FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
    assert receipt["safe_disable_posture_ref"] == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF
    )
    assert receipt["safe_disable_enabled"] is True
    assert receipt["rollback_execution_enabled"] is False
    assert receipt["rollback_blocker_refs"] == [
        FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF
    ]
    assert receipt["connector_write_performed"] is False
    assert receipt["shell_subprocess_execution_performed"] is False
    assert receipt["model_provider_authority_used"] is False
    assert receipt["memory_write_performed"] is False
    assert receipt["context_injection_performed"] is False
    assert receipt["external_side_effect_performed"] is False
    assert receipt["raw_content_stored"] is False
    assert set(FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS).issubset(
        set(receipt["blocked_state_refs"])
    )

    latest = repo.latest_action_receipt("local-task-create-scorecard")
    assert latest is not None
    assert latest["receipt_ref"] == receipt["receipt_ref"]
    status = repo.storage_status()
    assert status["counts"]["local_tasks"] == 1
    assert status["counts"]["local_task_commit_receipts"] == 1

    with pytest.raises(
        FounderLoopStorageDuplicateError,
        match="FOUNDER_LOOP_LOCAL_TASK_IDEMPOTENCY_CONFLICT",
    ):
        repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=_local_task_commit_request_for_action(
                action,
                metadata_refs=["metadata-ref:test-local-task-commit-conflict"],
            ),
            idempotency_key_ref="idempotency-ref:test-local-task-commit",
        )

    replay = repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=request,
        idempotency_key_ref="idempotency-ref:test-local-task-commit",
    )
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == receipt["receipt_ref"]

    with pytest.raises(
        FounderLoopStorageDuplicateError,
        match="FOUNDER_LOOP_LOCAL_TASK_ALREADY_COMMITTED",
    ):
        repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=_local_task_commit_request_for_action(
                action,
                approval_ref="approval-ref:test-local-task-second",
            ),
            idempotency_key_ref="idempotency-ref:test-local-task-second",
        )

    committed_action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert committed_action["local_task_commit_eligible"] is False
    assert committed_action["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    assert committed_action["local_task_ref"] == receipt["local_task_ref"]
    assert committed_action["local_task_safe_disable_posture"]["backend_owned"] is True
    assert committed_action["local_task_safe_disable_active"] is False
    assert committed_action["local_task_rollback_execution_enabled"] is False
    receipt_visibility = committed_action["receipt_visibility"]
    assert receipt_visibility["backend_owned"] is True
    assert receipt_visibility["decision_receipt_ref"].startswith(
        "receipt:founder-loop-action:"
    )
    assert receipt_visibility["local_task_ref"] == receipt["local_task_ref"]
    assert receipt_visibility["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    assert (
        receipt_visibility["evidence_timeline_event_ref"]
        == receipt["evidence_timeline_event_ref"]
    )
    assert receipt_visibility["replay_posture"] == "idempotency_replay_available"
    assert (
        receipt_visibility["conflict_posture"]
        == "conflicting_idempotency_payload_rejected"
    )
    assert committed_action["action_group_id"] == "receipt_recorded"
    assert receipt_visibility["replay_posture"] == "idempotency_replay_available"
    assert (
        receipt_visibility["conflict_posture"]
        == "conflicting_idempotency_payload_rejected"
    )

    timeline = repo.evidence_timeline()
    assert "local_task_created" in timeline["event_types"]
    local_task_events = [
        event
        for event in timeline["events"]
        if event["event_type"] == "local_task_created"
    ]
    assert local_task_events
    assert local_task_events[0]["receipt_refs"] == [receipt["receipt_ref"]]


def test_action_inbox_local_task_commit_denies_when_safe_disabled(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    _approve_local_task_seed_action(repo)

    posture = repo._disable_local_task_create_lane_for_test(
        disabled_reason_refs=["safe-disable-reason:test-local-task-disabled"],
    )
    assert posture["local_task_commits_enabled"] is False
    assert posture["safe_disable_active"] is True
    assert posture["safe_disable_posture_ref"] == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_POSTURE_REF
    )
    assert (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
        in posture["blocked_state_refs"]
    )

    disabled_action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert disabled_action["local_task_commit_eligible"] is False
    assert disabled_action["local_task_safe_disable_active"] is True
    assert (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
        in disabled_action["local_task_commit_blocked_reasons"]
    )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED",
    ):
        repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=_local_task_commit_request_for_action(disabled_action),
            idempotency_key_ref="idempotency-ref:test-local-task-safe-disabled",
        )

    status = repo.storage_status()
    assert status["counts"]["local_tasks"] == 0
    assert status["counts"]["local_task_commit_receipts"] == 0


def test_action_inbox_groups_items_by_backend_contract_state(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    inbox = repo.actions_inbox()
    groups = {group["group_id"]: group for group in inbox["action_groups"]}
    assert list(groups) == [
        "ready_for_decision",
        "approved_local_task_lane",
        "blocked_by_authority",
        "expired_stale",
        "receipt_recorded",
        "proposal_only_no_execution_path",
    ]
    assert groups["ready_for_decision"]["count"] == 1
    assert groups["blocked_by_authority"]["count"] == 1
    health_recommendation_count = sum(
        1
        for item in inbox["items"]
        if item.get("action_kind") == "self_heal_recommendation"
    )
    assert health_recommendation_count == 4
    assert groups["proposal_only_no_execution_path"]["count"] == (
        4 + health_recommendation_count
    )
    by_ref = {item["item_ref"]: item for item in inbox["items"]}
    for item in inbox["items"]:
        envelope = item["approval_envelope"]
        assert envelope["schema_version"] == "founder_loop_action_approval_envelope.v1"
        assert envelope["contract_ref"] == (
            "contract-ref:founder-loop-action-approval-envelope:v1"
        )
        assert envelope["source"] == "python_core_action_inbox_read_model"
        assert envelope["backend_owned"] is True
        assert envelope["action_kind"] == item.get("action_kind", "review_only")
        assert envelope["risk_class"] == item["risk_class"]
        assert envelope["side_effect_class"] == item["side_effect_class"]
        assert envelope["expected_receipt_refs"]
        assert envelope["blocked_authority_refs"]
        assert envelope["evidence_refs"]
        serialized = json.dumps(envelope, sort_keys=True).lower()
        assert "raw_prompt" not in serialized
        assert "raw_response" not in serialized
        assert "credential" not in serialized
        visibility = item["receipt_visibility"]
        assert (
            visibility["schema_version"] == "founder_loop_action_receipt_visibility.v1"
        )
        assert visibility["contract_ref"] == (
            "contract-ref:founder-loop-action-receipt-visibility:v1"
        )
        assert visibility["source"] == "python_core_action_inbox_read_model"
        assert visibility["backend_owned"] is True
        assert visibility["decision_receipt_ref"]
        assert visibility["local_task_ref"]
        assert visibility["local_task_commit_receipt_ref"]
        assert visibility["evidence_timeline_event_ref"]
        assert visibility["replay_posture"]
        assert visibility["conflict_posture"]
        serialized_visibility = json.dumps(visibility, sort_keys=True).lower()
        assert "raw_prompt" not in serialized_visibility
        assert "raw_response" not in serialized_visibility
        assert "credential" not in serialized_visibility
    assert (
        by_ref["founder-action:local-task-create-scorecard"]["action_group_id"]
        == "ready_for_decision"
    )
    assert (
        by_ref["founder-action:setup-assistant-hardening"]["action_group_id"]
        == "blocked_by_authority"
    )
    assert (
        by_ref["founder-action:morning-briefing-skeleton"]["action_group_id"]
        == "proposal_only_no_execution_path"
    )
    briefing_envelope = by_ref["founder-action:morning-briefing-skeleton"][
        "approval_envelope"
    ]
    assert briefing_envelope["approval_requirement"] == "not_applicable"
    assert (
        "blocked-state:no-action-execution"
        in briefing_envelope["blocked_authority_refs"]
    )

    approved = _approve_local_task_seed_action(repo)
    assert approved["action_group_id"] == "approved_local_task_lane"
    assert approved["action_group_label"] == "Approved local task lane"
    assert approved["approval_envelope"]["action_kind"] == "local_task_create"
    assert (
        "blocked-state:no-connector-write"
        in approved["approval_envelope"]["blocked_authority_refs"]
    )
    assert approved["receipt_visibility"]["decision_receipt_ref"].startswith(
        "receipt:founder-loop-action:"
    )
    assert approved["receipt_visibility"]["local_task_ref"] == "pending"
    assert approved["receipt_visibility"]["local_task_commit_receipt_ref"] == "pending"
    assert (
        approved["receipt_visibility"]["replay_posture"]
        == "decision_idempotency_replay_available"
    )
    assert (
        approved["receipt_visibility"]["conflict_posture"]
        == "decision_conflicting_idempotency_payload_rejected"
    )

    receipt = repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=_local_task_commit_request_for_action(approved),
        idempotency_key_ref="idempotency-ref:test-local-task-group-commit",
    )
    committed = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert committed["action_group_id"] == "receipt_recorded"
    assert committed["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    visibility = committed["receipt_visibility"]
    assert visibility["decision_receipt_ref"].startswith("receipt:founder-loop-action:")
    assert visibility["local_task_ref"] == receipt["local_task_ref"]
    assert visibility["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    assert (
        visibility["evidence_timeline_event_ref"]
        == receipt["evidence_timeline_event_ref"]
    )
    assert visibility["replay_posture"] == "idempotency_replay_available"
    assert visibility["conflict_posture"] == "conflicting_idempotency_payload_rejected"
    assert visibility["missing_field_states"] == ["none"]

    repo.upsert_action(
        FounderLoopActionRecord(
            item_ref="founder-action:expired-demo",
            title="Expired demo action",
            safe_summary="Expired safe-ref action used to verify lane grouping.",
            surface="Actions",
            priority="medium",
            risk_class="medium",
            status="expired",
            side_effect_class="validation_only",
            approval_required=True,
            approval_envelope_ref="approval-envelope:founder-loop:expired-demo",
            state_change_contract_ref="contract-ref:founder-loop:expired-demo",
            state_change_readiness="blocked_expired_state",
            stale_state="expired_evidence_window",
            expires_at="2026-01-01T00:00:00+00:00",
            rollback_ref="rollback-plan:founder-loop:expired-demo",
            safe_disable_ref="safe-disable:founder-loop:expired-demo",
            next_safe_action="Recheck evidence refs before any later decision.",
        )
    )
    expired = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:expired-demo"
    )
    assert expired["action_group_id"] == "expired_stale"


def test_memory_context_packs_derive_from_reviewed_l3_refs_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    empty_context_packs = repo.memory_context_pack_proposals()
    assert empty_context_packs["context_pack_count"] == 0
    assert empty_context_packs["source_l3_representation_count"] == 0
    assert empty_context_packs["proposal_only"] is True
    assert empty_context_packs["derived_from_reviewed_memory_only"] is True
    assert empty_context_packs["context_injection_authorized"] is False
    assert empty_context_packs["provider_model_call_performed"] is False
    assert empty_context_packs["connector_write_authorized"] is False

    candidate = repo.list_memory_review_queue(limit=1)[0]
    receipt = repo.record_memory_review_decision(
        candidate_ref=str(candidate["review_ref"]),
        decision="accept",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="reviewer-ref:test-context-pack-operator",
            source_refs=["source-ref:test-context-pack-review"],
            evidence_refs=["evidence-ref:test-context-pack-review"],
            metadata_refs=["metadata-ref:test-context-pack-review"],
        ),
        idempotency_key_ref="idempotency-ref:test-context-pack-accept",
    )

    l1_index = repo.memory_l1_hot_index()
    l2_index = repo.memory_l2_factual_graph_temporal_index()
    l3_index = repo.memory_l3_identity_session_preference_index()
    context_packs = repo.memory_context_pack_proposals()

    assert receipt["reviewed_recall_record_ref"].startswith("memory-record-ref:")
    assert l1_index["indexed_record_count"] == 1
    assert l2_index["fact_count"] >= 1
    assert l3_index["item_count"] >= 1
    assert context_packs["context_pack_count"] == 1
    assert context_packs["source_l1_preview_count"] == 1
    assert context_packs["source_l3_representation_count"] == 1
    assert context_packs["phase6_1_internal_action_proposal_status"] == (
        "implemented_internal_action_proposal_only_execution_blocked"
    )

    proposal = context_packs["proposals"][0]
    assert proposal["proposal_only"] is True
    assert proposal["review_required"] is True
    assert proposal["source_memory_record_refs"] == [
        receipt["reviewed_recall_record_ref"]
    ]
    assert proposal["l1_preview_refs"]
    assert proposal["l2_projection_refs"]
    assert proposal["l3_representation_refs"]
    assert (
        "inclusion-reason-ref:context-pack-reviewed-l3-representation-proposal"
        in proposal["inclusion_reason_refs"]
    )
    assert (
        "blocked-state:context-pack-no-hidden-context-injection"
        in proposal["blocked_state_refs"]
    )
    assert (
        "blocked-state:context-pack-no-connector-writes"
        in proposal["blocked_state_refs"]
    )
    assert proposal["context_injection_authorized"] is False
    assert proposal["automatic_context_injection_authorized"] is False
    assert proposal["prompt_context_written"] is False
    assert proposal["model_provider_authority_allowed"] is False
    assert proposal["connector_write_authorized"] is False
    assert proposal["automatic_action_execution_authorized"] is False
    assert proposal["phase6_execution_hooks_enabled"] is False
    assert proposal["raw_content_stored"] is False


def test_action_inbox_local_task_commit_rejects_unsupported_action_kind(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.upsert_action(
        FounderLoopActionRecord(
            item_ref="founder-action:unsupported-local-task",
            title="Unsupported local action",
            safe_summary=(
                "Approved review-only action should not enter the local task lane."
            ),
            surface="Actions",
            priority="medium",
            risk_class="medium",
            status="approved",
            action_kind="review_only",
            side_effect_class="local_dev_workspace_only",
            evidence_refs=["evidence-ref:test-unsupported-local-task"],
        )
    )
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:unsupported-local-task"
    )
    request = FounderLoopLocalTaskCommitRequest(
        approval_ref="approval-ref:test-unsupported-local-task"
    )

    assert action["local_task_commit_eligible"] is False
    assert (
        "blocked-state:unsupported-action-kind"
        in action["local_task_commit_blocked_reasons"]
    )
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_UNSUPPORTED_ACTION_KIND",
    ):
        repo.commit_local_task(
            action_id="unsupported-local-task",
            request=request,
            idempotency_key_ref="idempotency-ref:test-unsupported-local-task",
        )


def test_action_inbox_local_task_commit_rejects_expired_backend_approval(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    action = _approve_local_task_seed_action(repo)
    repo._execute(
        """
        UPDATE action_inbox
        SET expires_at = ?, stale_state = ?
        WHERE item_ref = ?
        """,
        (
            "2020-01-01T00:00:00+00:00",
            "fresh_exact_scope_local_task_commit_window",
            action["item_ref"],
        ),
    )

    expired_action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert expired_action["local_task_commit_eligible"] is False
    assert (
        "blocked-state:local-task-approval-expired"
        in expired_action["local_task_commit_blocked_reasons"]
    )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED",
    ):
        repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=_local_task_commit_request_for_action(expired_action),
            idempotency_key_ref="idempotency-ref:test-local-task-expired",
        )
