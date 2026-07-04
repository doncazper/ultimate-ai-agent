from pathlib import Path


ARCHITECTURE_DOC = Path("docs/architecture/TURN_CONTRACT_ROUTER.md")


def test_phase_two_preflight_plan_preserves_lane_names_and_boundaries() -> None:
    text = ARCHITECTURE_DOC.read_text(encoding="utf-8")

    for lane_name in (
        "intent_lane",
        "risk_action_lane",
        "memory_trigger_lane",
        "memory_relevance_lane",
        "tool_manifest_lane",
        "answer_profile_lane",
        "direct_answer_draft",
    ):
        assert f"`{lane_name}`" in text

    assert "Parallelize sensing." in text
    assert "Centralize authority." in text
    assert "Serialize execution." in text
    assert "Do not execute side effects during preflight." in text
    assert "not as execution authority" in text


def test_phase_two_preflight_plan_remains_planning_only() -> None:
    text = ARCHITECTURE_DOC.read_text(encoding="utf-8")

    assert "Status: planning only" in text
    assert "No parallel runtime behavior is implemented" in text
    assert "No live provider/model call" in text
    assert "No tool execution" in text
    assert "No memory content retrieval" in text
    assert "No connector write" in text
