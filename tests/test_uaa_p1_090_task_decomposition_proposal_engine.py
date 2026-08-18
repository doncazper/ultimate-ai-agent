from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.storage.founder_loop import FounderLoopStorageError
from ultimate_ai_agent.core.task_decomposition.proposals import (
    TASK_DECOMPOSITION_ACTION_KIND,
    TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF,
    TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS,
    TaskDecompositionProposal,
    TaskDecompositionRequest,
    TaskDecompositionReviewEnvelope,
    build_task_decomposition_review_envelope,
    task_decomposition_action_items,
    task_decomposition_read_model_for_plan,
)


def _request() -> TaskDecompositionRequest:
    return TaskDecompositionRequest(
        request_ref="task-decomposition-request:test",
        original_request_ref="operator-request:test",
        original_request_safe_summary=(
            "Implement a review-only task proposal from bounded safe refs."
        ),
        source_refs=["source-ref:operator-request:test"],
        evidence_refs=["evidence-ref:operator-request:test"],
        ambiguity_refs=["ambiguity-ref:operator-request:scope"],
        missing_evidence_refs=["missing-evidence-ref:operator-request:acceptance"],
        operator_goal_refs=["operator-goal-ref:task-decomposition:test"],
    )


def _assert_no_effect_flags(payload: dict[str, object]) -> None:
    assert payload["review_only"] is True
    assert payload["proposal_only"] is True
    assert payload["runtime_authority_granted"] is False
    assert payload["execution_authorized"] is False
    assert payload["execution_performed"] is False
    assert payload["task_execution_enabled"] is False
    assert payload["task_execution_performed"] is False
    assert payload["workflow_execution_enabled"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["action_execution_performed"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["tool_execution_performed"] is False
    assert payload["memory_write_authorized"] is False
    assert payload["memory_write_performed"] is False
    assert payload["context_injection_authorized"] is False
    assert payload["context_injection_performed"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["connector_write_performed"] is False
    assert payload["shell_subprocess_execution_enabled"] is False
    assert payload["shell_subprocess_execution_performed"] is False
    assert payload["browser_network_enabled"] is False
    assert payload["browser_network_performed"] is False
    assert payload["model_provider_authority_allowed"] is False
    assert payload["model_provider_call_performed"] is False
    assert payload["production_authority_enabled"] is False
    assert payload["no_model_call_performed"] is True
    assert payload["no_tool_execution_performed"] is True
    assert payload["no_action_execution_performed"] is True
    assert payload["no_workflow_execution_performed"] is True
    assert payload["no_memory_write_performed"] is True
    assert payload["no_context_injection_performed"] is True
    assert payload["no_connector_write_performed"] is True
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_included"] is False


def test_task_decomposition_request_builds_review_only_proposal() -> None:
    envelope = build_task_decomposition_review_envelope(_request())
    proposal = envelope.proposals[0]

    assert envelope.contract_ref == TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    assert envelope.decision_receipt_only is True
    assert envelope.separate_approval_required is True
    assert envelope.review_actions == ["approve", "defer", "reject"]
    assert proposal.proposal_ref == "task-decomposition-proposal:task-decomposition-request-test"
    assert proposal.proposed_steps
    assert {step.title for step in proposal.proposed_steps} >= {
        "Confirm requested outcome",
        "Ask for clarification",
        "Bind evidence and blockers",
        "Draft plan proposal",
        "Prepare Action Inbox proposal refs",
    }
    assert proposal.dependencies
    assert proposal.ambiguity_refs == ["ambiguity-ref:operator-request:scope"]
    assert proposal.missing_evidence_refs == [
        "missing-evidence-ref:operator-request:acceptance"
    ]
    assert proposal.suggested_action_inbox_proposal_refs
    assert proposal.required_approvals
    assert proposal.why_proposed
    assert set(proposal.what_this_affects) >= {
        "surface-ref:today",
        "surface-ref:plans",
        "surface-ref:actions",
        "surface-ref:evidence",
    }
    assert set(TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS) <= set(
        proposal.blocked_authority_refs
    )
    _assert_no_effect_flags(proposal.model_dump(mode="json"))
    _assert_no_effect_flags(envelope.model_dump(mode="json"))


def test_task_decomposition_rejects_authority_flags() -> None:
    with pytest.raises(ValidationError, match="tool_execution_allowed"):
        TaskDecompositionRequest(
            request_ref="task-decomposition-request:bad",
            original_request_ref="operator-request:bad",
            original_request_safe_summary="Unsafe request.",
            source_refs=["source-ref:operator-request:bad"],
            tool_execution_allowed=True,
        )

    envelope = build_task_decomposition_review_envelope(_request())
    proposal_payload = envelope.proposals[0].model_dump(mode="json")
    proposal_payload["memory_write_authorized"] = True
    with pytest.raises(ValidationError, match="memory_write_authorized"):
        TaskDecompositionProposal(**proposal_payload)

    envelope_payload = envelope.model_dump(mode="json")
    envelope_payload["action_execution_enabled"] = True
    with pytest.raises(ValidationError, match="action_execution_enabled"):
        TaskDecompositionReviewEnvelope(**envelope_payload)


def test_task_decomposition_action_items_are_proposal_only() -> None:
    envelope = build_task_decomposition_review_envelope(_request())
    items = task_decomposition_action_items(envelope)

    assert len(items) == 1
    item = items[0]
    assert item["action_kind"] == TASK_DECOMPOSITION_ACTION_KIND
    if "action_group_id" in item:
        assert item["action_group_id"] == "proposal_only_no_execution_path"
    assert item["approval_required"] is False
    assert item["approval_envelope_status"] == "not_required_proposal_only"
    assert item["state_change_contract_ref"] is None
    assert item["state_change_readiness"] == "proposal_only_no_execution_path"
    assert item["task_decomposition_review_only"] is True
    assert item["task_decomposition_proposal_only"] is True
    assert item["task_decomposition_execution_performed"] is False
    assert item["task_decomposition_runtime_authority_granted"] is False
    assert item["task_decomposition_execution_authorized"] is False
    assert item["task_decomposition_action_execution_enabled"] is False
    assert item["task_decomposition_tool_execution_enabled"] is False
    assert item["task_decomposition_workflow_execution_enabled"] is False
    assert item["task_decomposition_memory_write_authorized"] is False
    assert item["task_decomposition_context_injection_authorized"] is False
    assert item["task_decomposition_connector_write_enabled"] is False
    assert item["task_decomposition_shell_subprocess_execution_enabled"] is False
    assert item["task_decomposition_browser_network_enabled"] is False
    assert item["task_decomposition_model_provider_authority_allowed"] is False
    assert item["task_decomposition_production_authority_enabled"] is False


def test_task_decomposition_plan_read_model_is_deterministic() -> None:
    first = task_decomposition_read_model_for_plan(
        "plan-summary:test",
        title="Review task proposal",
        safe_summary="Build a review-only plan proposal from safe refs.",
        evidence_refs=["evidence-ref:plan:test"],
    )
    second = task_decomposition_read_model_for_plan(
        "plan-summary:test",
        title="Review task proposal",
        safe_summary="Build a review-only plan proposal from safe refs.",
        evidence_refs=["evidence-ref:plan:test"],
    )

    assert first == second
    assert first["task_decomposition_contract_ref"] == (
        TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    )
    assert first["task_decomposition_steps"]
    assert first["task_decomposition_suggested_action_inbox_proposal_refs"]
    assert first["task_decomposition_review_only"] is True
    assert first["task_decomposition_proposal_only"] is True
    assert first["task_decomposition_execution_authorized"] is False
    assert first["task_decomposition_memory_write_authorized"] is False
    assert first["task_decomposition_context_injection_authorized"] is False
    assert first["task_decomposition_model_provider_authority_allowed"] is False


def test_founder_loop_bridges_task_decomposition_to_plans_and_action_inbox(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["task_decomposition_proposal_contract_ref"] == (
        TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    )
    assert today["task_decomposition_proposal_count"] == len(today["plans"])
    assert today["task_decomposition_authority_posture"]["review_only"] is True
    assert today["task_decomposition_authority_posture"][
        "action_execution_enabled"
    ] is False

    for plan in today["plans"]:
        assert plan["task_decomposition_contract_ref"] == (
            TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
        )
        assert plan["task_decomposition_review_only"] is True
        assert plan["task_decomposition_proposal_only"] is True
        assert plan["task_decomposition_execution_authorized"] is False
        assert plan["task_decomposition_memory_write_authorized"] is False
        assert plan["task_decomposition_context_injection_authorized"] is False
        assert plan["task_decomposition_model_provider_authority_allowed"] is False
        assert plan["task_decomposition_steps"]

    task_items = [
        item
        for item in inbox["items"]
        if item.get("action_kind") == TASK_DECOMPOSITION_ACTION_KIND
    ]
    assert task_items
    assert inbox["task_decomposition_action_proposals"] == task_items
    assert inbox["task_decomposition_proposal_summary"]["proposal_count"] == len(
        task_items
    )
    for item in task_items:
        assert item["action_group_id"] == "proposal_only_no_execution_path"
        assert item["approval_required"] is False
        assert item["local_task_commit_eligible"] is False
        assert item["receipt_visibility"]["local_task_ref"] == "not_applicable"
        assert item["task_decomposition_review_only"] is True
        assert item["task_decomposition_proposal_only"] is True
        assert item["task_decomposition_execution_authorized"] is False
        assert item["task_decomposition_action_execution_enabled"] is False
        assert item["task_decomposition_memory_write_authorized"] is False
        assert item["task_decomposition_context_injection_authorized"] is False
        assert item["task_decomposition_model_provider_authority_allowed"] is False


def test_task_decomposition_generated_items_do_not_record_action_decisions(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    task_item = next(
        item
        for item in repo.actions_inbox()["items"]
        if item.get("action_kind") == TASK_DECOMPOSITION_ACTION_KIND
    )

    with pytest.raises(FounderLoopStorageError, match="FOUNDER_LOOP_ACTION_NOT_FOUND"):
        repo.record_action_decision(
            action_id=task_item["item_ref"],
            decision="approve",
            request=FounderLoopActionDecisionRequest(
                expected_revision_ref=str(task_item["action_revision_ref"]),
                decision_reason_ref="decision-reason-ref:task-decomposition:test"
            ),
            idempotency_key_ref="idempotency-ref:task-decomposition:test",
        )
