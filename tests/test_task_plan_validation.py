from typing import Any
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


def _step(**overrides: Any) -> Any:
    data = {
        "step_id": "step:m29-validate",
        "step_kind": TaskStepKind.review_metadata,
        "safe_summary": "Review safe refs.",
        "input_boundary": TaskStepInputBoundary(input_refs=["canonical:m29"]),
        "declared_risk_level": TaskRiskLevel.low,
    }
    data.update(overrides)
    return TaskStep(**data)


def _plan(**overrides: Any) -> Any:
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
def test_model_copy_mutated_input_boundary_is_revalidated(update: Any, reason: str) -> None:
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
        ("openwebui:m29", PlanInputTrustLevel.openwebui_output_blocked, "OPENWEBUI_OUTPUT_NOT_PLAN_AUTHORITY"),
        ("control-center:m29", PlanInputTrustLevel.unknown_blocked, "UNKNOWN_INPUT_REF_DENIED"),
    ],
)
def test_non_authoritative_refs_cannot_authorize_plans(input_ref: Any, trust_level: Any, reason: str) -> None:
    boundary = TaskStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
    decision = evaluate_task_plan(_plan(steps=[_step(input_boundary=boundary)]))

    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert reason in decision.reason_codes


def test_approval_ref_alone_and_test_refs_are_denied() -> None:
    arbitrary = evaluate_task_plan(_plan(approval_ref="approval:m28-arbitrary"))
    test_ref = evaluate_task_plan(_plan(approval_ref="approval_test_m29"))

    assert arbitrary.valid_for_review is False
    assert "APPROVAL_REF_NOT_TASK_AUTHORITY" in arbitrary.reason_codes
    assert test_ref.valid_for_review is False
    assert "APPROVAL_TEST_REF_DENIED" in test_ref.reason_codes


def test_hidden_side_effect_metadata_is_denied_for_safe_step_kind() -> None:
    step = _step(
        step_kind=TaskStepKind.review_metadata,
        declared_risk_level=TaskRiskLevel.low,
        metadata={"side_effect": "file_write"},
    )

    decision = evaluate_task_plan(_plan(steps=[step]))

    assert decision.valid_for_review is False
    assert "TASK_HIDDEN_SIDE_EFFECT_DENIED" in decision.reason_codes
    assert "TASK_RISK_DOWNGRADE_DENIED" in decision.reason_codes


def test_safe_plan_reports_derived_plan_risk_from_steps() -> None:
    low = _step(step_id="step:m29-low", declared_risk_level=TaskRiskLevel.low)
    medium = _step(step_id="step:m29-medium", declared_risk_level=TaskRiskLevel.medium)

    decision = evaluate_task_plan(_plan(steps=[low, medium]))

    assert decision.valid_for_review is True
    assert decision.derived_plan_risk_level == TaskRiskLevel.medium
    assert decision.receipt_plan.derived_plan_risk_level == TaskRiskLevel.medium
