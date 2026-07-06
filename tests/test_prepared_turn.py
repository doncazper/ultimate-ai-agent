import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.dev import uaa_turn_router
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.decision_router import (
    PreparedTurn,
    PreparedTurnBranch,
    build_sample_prepared_turns,
    prepare_turn,
)


client = TestClient(app)


def test_prepared_turn_direct_answer_has_no_memory_tools_or_execution() -> None:
    turn = prepare_turn(sample_id="diy-desk")

    assert turn.branch == PreparedTurnBranch.answer_directly.value
    assert turn.turn_run_approval_chain is not None
    assert turn.turn_run_approval_chain.current_state == "routed"
    assert turn.turn_run_approval_chain.linkage.approval_ref is None
    assert turn.memory_readiness.status == "memory_not_used"
    assert turn.tool_action_readiness.status == "tool_action_not_used"
    assert turn.route_decision_binding.route_decision_is_approval is False
    assert turn.raw_prompt_persisted is False
    assert turn.raw_model_output_persisted is False
    assert turn.execution_performed is False


def test_prepared_turn_memory_readiness_uses_reviewed_refs_only() -> None:
    turn = prepare_turn(sample_id="office-memory")

    assert turn.branch == PreparedTurnBranch.answer_with_reviewed_memory.value
    assert turn.memory_readiness.ready is True
    assert turn.memory_readiness.review_required is True
    assert turn.memory_readiness.refs == ["memory-ref:prepared-turn:reviewed-context"]
    assert turn.context_injection_performed is False


def test_prepared_turn_tool_action_readiness_is_proposal_only() -> None:
    turn = prepare_turn(sample_id="current-lumber-prices")

    assert turn.branch == PreparedTurnBranch.prepare_tool_or_action.value
    assert turn.tool_action_readiness.status == "proposal_only"
    assert turn.tool_action_readiness.ready is True
    assert "blocked-authority:prepared-turn-no-tool-execution" in (
        turn.tool_action_readiness.blocked_authority_refs
    )
    assert turn.tool_execution_performed is False


def test_prepared_turn_approval_required_has_exact_envelope_posture() -> None:
    turn = prepare_turn(sample_id="order-materials")
    chain = turn.turn_run_approval_chain
    assert chain is not None

    assert turn.branch == PreparedTurnBranch.approval_required.value
    assert turn.tool_action_readiness.status == "approval_required"
    assert turn.route_decision_binding.approval_ref == (
        "approval-ref:prepared-turn:approval_required"
    )
    assert turn.durable_run_ref == chain.linkage.durable_run_ref.ref
    assert chain.linkage.turn_ref is not None
    assert chain.linkage.turn_ref.ref == turn.latest_user_turn_ref
    assert chain.linkage.operator_task_ref == turn.task_ref
    assert chain.linkage.approval_ref is not None
    assert chain.linkage.approval_ref.ref == turn.route_decision_binding.approval_ref
    assert chain.linkage.route_decision_binding_ref is not None
    assert chain.linkage.route_decision_binding_ref.ref == (
        turn.route_decision_binding.binding_ref
    )
    assert chain.current_state == "waiting_for_approval"
    assert chain.transitions[-1].approval_ref is not None
    assert chain.transitions[-1].approval_ref.ref == (
        turn.route_decision_binding.approval_ref
    )
    assert turn.next_actions[0].requires_approval is True
    assert turn.action_execution_performed is False


def test_prepared_turn_blocks_base_answer_bypass_for_payment_action() -> None:
    turn = prepare_turn(sample_id="base-answer-bypass")

    assert turn.branch == PreparedTurnBranch.approval_required.value
    assert turn.selected_turn_contract == "approval_required"
    assert "blocked-authority:prepared-turn-no-action-execution" in (
        turn.blocked_authority_refs
    )


def test_prepared_turn_rejects_raw_persistence_or_execution_flags() -> None:
    payload = prepare_turn(sample_id="diy-desk").model_dump(mode="json")
    payload["raw_prompt_persisted"] = True

    with pytest.raises(ValidationError):
        PreparedTurn(**payload)

    payload = prepare_turn(sample_id="diy-desk").model_dump(mode="json")
    payload["execution_performed"] = True
    with pytest.raises(ValidationError):
        PreparedTurn(**payload)


def test_prepared_turn_sample_set_covers_required_branches() -> None:
    branches = {turn.branch for turn in build_sample_prepared_turns()}

    assert {
        PreparedTurnBranch.answer_directly.value,
        PreparedTurnBranch.answer_with_reviewed_memory.value,
        PreparedTurnBranch.prepare_tool_or_action.value,
        PreparedTurnBranch.approval_required.value,
    }.issubset(branches)


def test_turn_router_cli_prepares_turn_without_raw_prompt(capsys) -> None:
    exit_code = uaa_turn_router.main(["prepare-turn", "--sample", "diy-desk"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "prepared_turn" in output
    assert "raw_prompt_persisted" in output
    assert "How do I build a DIY desk" not in output


def test_runtime_api_exposes_prepared_turn_read_model() -> None:
    response = client.get("/api/runtime/prepared-turn?sample=current-lumber-prices")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["branch"] == "prepare_tool_or_action"
    assert data["api_ref"] == "GET /api/runtime/prepared-turn"
    assert data["raw_prompt_persisted"] is False
    assert data["execution_performed"] is False
