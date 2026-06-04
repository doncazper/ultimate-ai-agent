import pytest

from ultimate_ai_agent.core.planning import (
    PlanInputTrustLevel,
    TaskGoal,
    TaskPlan,
    TaskPlanDecisionStatus,
    TaskRiskLevel,
    TaskStep,
    TaskStepInputBoundary,
    TaskStepKind,
    evaluate_task_plan,
)


def _step(**overrides):
    data = {
        "step_id": "step:m29-validate",
        "step_kind": TaskStepKind.review_metadata,
        "safe_summary": "Review safe refs.",
        "input_boundary": TaskStepInputBoundary(input_refs=["canonical:m29"]),
        "declared_risk_level": TaskRiskLevel.low,
    }
    data.update(overrides)
    return TaskStep(**data)


def _plan(**overrides):
    data = {
        "plan_id": "plan:m29-validate",
        "goal": TaskGoal(goal_id="goal:m29-validate", safe_summary="Plan a safe review."),
        "steps": [_step()],
        "safe_summary": "Review-only plan.",
    }
    data.update(overrides)
    return TaskPlan(**data)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"contains_raw_prompt": True}, "RAW_PROMPT_DENIED"),
        ({"contains_raw_model_output": True}, "RAW_MODEL_OUTPUT_DENIED"),
        ({"contains_raw_file_content": True}, "RAW_FILE_CONTENT_DENIED"),
        ({"contains_raw_transcript": True}, "RAW_TRANSCRIPT_DENIED"),
        ({"contains_secret_like_content": True}, "SECRET_LIKE_INPUT_DENIED"),
        ({"metadata": {"token": "abc123"}}, "SECRET_METADATA_DENIED"),
        ({"metadata_refs": ["secret:m29"]}, "SECRET_METADATA_DENIED"),
    ],
)
def test_model_copy_mutated_input_boundary_is_revalidated(update, reason):
    step = _step(input_boundary=TaskStepInputBoundary(input_refs=["canonical:m29"]))
    mutated_boundary = step.input_boundary.model_copy(update=update)
    mutated_step = step.model_copy(update={"input_boundary": mutated_boundary})

    decision = evaluate_task_plan(_plan(steps=[mutated_step]))

    assert decision.status == TaskPlanDecisionStatus.denied
    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("input_ref", "trust_level", "reason"),
    [
        ("model:m29", PlanInputTrustLevel.model_output_blocked, "MODEL_OUTPUT_NOT_PLAN_AUTHORITY"),
        ("memory:m29", PlanInputTrustLevel.memory_ref, "MEMORY_REF_NOT_PLAN_AUTHORITY"),
        ("context-pack:m29", PlanInputTrustLevel.context_pack_ref, "CONTEXT_PACK_NOT_PLAN_AUTHORITY"),
        ("tool-intent:m27", PlanInputTrustLevel.tool_intent_ref, "TOOL_INTENT_NOT_PLAN_AUTHORITY"),
        ("approval:m28", PlanInputTrustLevel.approval_ref, "APPROVAL_REF_NOT_TASK_AUTHORITY"),
    ],
)
def test_non_authoritative_refs_cannot_authorize_plans(input_ref, trust_level, reason):
    boundary = TaskStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
    decision = evaluate_task_plan(_plan(steps=[_step(input_boundary=boundary)]))

    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert reason in decision.reason_codes


def test_approval_ref_alone_and_test_refs_are_denied():
    arbitrary = evaluate_task_plan(_plan(approval_ref="approval:m28-arbitrary"))
    test_ref = evaluate_task_plan(_plan(approval_ref="approval_test_m29"))

    assert arbitrary.valid_for_review is False
    assert "APPROVAL_REF_NOT_TASK_AUTHORITY" in arbitrary.reason_codes
    assert test_ref.valid_for_review is False
    assert "APPROVAL_TEST_REF_DENIED" in test_ref.reason_codes
