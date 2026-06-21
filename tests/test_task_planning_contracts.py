from typing import Any
from ultimate_ai_agent.core.planning import (
    PlanInputTrustLevel,
    TaskGoal,
    TaskPlan,
    TaskPlanDecisionStatus,
    TaskRiskLevel,
    TaskStep,
    TaskStepInputBoundary,
    TaskStepKind,
    build_task_planning_manifest,
    evaluate_task_plan,
)


def _safe_step(**overrides: Any) -> Any:
    data = {
        "step_id": "step:m29-review",
        "step_kind": TaskStepKind.review_metadata,
        "safe_summary": "Review safe metadata refs.",
        "input_boundary": TaskStepInputBoundary(input_refs=["canonical:m29"]),
        "declared_risk_level": TaskRiskLevel.low,
    }
    data.update(overrides)
    return TaskStep(**data)


def _safe_plan(**overrides: Any) -> Any:
    data = {
        "plan_id": "plan:m29-safe",
        "goal": TaskGoal(goal_id="goal:m29-safe", safe_summary="Plan a safe review workflow."),
        "steps": [_safe_step()],
        "safe_summary": "A deterministic review-only task plan.",
    }
    data.update(overrides)
    return TaskPlan(**data)


def test_default_manifest_is_non_executing_contract_only() -> None:
    manifest = build_task_planning_manifest(baseline_version="0.33.0")

    assert manifest.planning_enabled is True
    assert manifest.task_execution_enabled is False
    assert manifest.auto_run_enabled is False
    assert manifest.scheduler_enabled is False
    assert manifest.tool_execution_enabled is False
    assert manifest.action_execution_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.network_call_enabled is False
    assert manifest.model_provider_call_enabled is False
    assert manifest.backend_task_routes_added is False
    assert manifest.production_authority_enabled is False


def test_safe_task_plan_is_valid_for_review_only_without_execution() -> None:
    decision = evaluate_task_plan(_safe_plan())

    assert decision.status == TaskPlanDecisionStatus.valid_for_review
    assert decision.valid_for_review is True
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert decision.scheduler_registered is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is False
    assert decision.receipt_plan.raw_content_stored is False
    assert "TASK_PLAN_VALID_FOR_REVIEW" in decision.reason_codes


def test_safe_plan_revalidates_model_copy_before_allowing_review() -> None:
    plan = _safe_plan()
    mutated = plan.model_copy(update={"safe_summary": "contains token=abc123"})

    decision = evaluate_task_plan(mutated)

    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert "TASK_PLAN_REVALIDATION_FAILED" in decision.reason_codes


def test_model_output_source_cannot_be_task_input_authority() -> None:
    boundary = TaskStepInputBoundary(
        input_refs=["model:m29"],
        input_trust_level=PlanInputTrustLevel.model_output_blocked,
    )
    decision = evaluate_task_plan(_safe_plan(steps=[_safe_step(input_boundary=boundary)]))

    assert decision.valid_for_review is False
    assert "MODEL_OUTPUT_NOT_PLAN_AUTHORITY" in decision.reason_codes
