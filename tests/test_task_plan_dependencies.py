from typing import Any
from ultimate_ai_agent.core.planning import (
    TaskDependency,
    TaskGoal,
    TaskPlan,
    TaskPlanDecisionStatus,
    TaskRiskLevel,
    TaskStep,
    TaskStepInputBoundary,
    TaskStepKind,
    evaluate_task_plan,
)


def _step(step_id: str, depends_on: Any | None = None) -> Any:
    return TaskStep(
        step_id=step_id,
        step_kind=TaskStepKind.review_metadata,
        safe_summary=f"Review {step_id}.",
        input_boundary=TaskStepInputBoundary(input_refs=["canonical:m29"]),
        declared_risk_level=TaskRiskLevel.low,
        depends_on=depends_on or [],
    )


def _plan(steps: Any, dependencies: Any | None = None) -> Any:
    return TaskPlan(
        plan_id="plan:m29-deps",
        goal=TaskGoal(goal_id="goal:m29-deps", safe_summary="Plan deterministic dependencies."),
        steps=steps,
        dependencies=dependencies or [],
        safe_summary="Dependency graph plan.",
    )


def test_duplicate_step_ids_are_denied() -> None:
    decision = evaluate_task_plan(_plan([_step("step:m29-a"), _step("step:m29-a")]))

    assert decision.status == TaskPlanDecisionStatus.denied
    assert "DUPLICATE_STEP_ID_DENIED" in decision.reason_codes


def test_missing_dependency_is_denied() -> None:
    decision = evaluate_task_plan(_plan([_step("step:m29-a", depends_on=["step:m29-missing"])]))

    assert decision.valid_for_review is False
    assert "MISSING_DEPENDENCY_STEP_DENIED" in decision.reason_codes


def test_dependency_cycle_is_denied() -> None:
    decision = evaluate_task_plan(
        _plan(
            [
                _step("step:m29-a", depends_on=["step:m29-b"]),
                _step("step:m29-b", depends_on=["step:m29-a"]),
            ]
        )
    )

    assert decision.valid_for_review is False
    assert "DEPENDENCY_CYCLE_DENIED" in decision.reason_codes


def test_self_dependency_is_denied() -> None:
    decision = evaluate_task_plan(_plan([_step("step:m29-a", depends_on=["step:m29-a"])]))

    assert decision.valid_for_review is False
    assert "DEPENDENCY_CYCLE_DENIED" in decision.reason_codes


def test_indirect_dependency_cycle_is_denied() -> None:
    decision = evaluate_task_plan(
        _plan(
            [
                _step("step:m29-a", depends_on=["step:m29-c"]),
                _step("step:m29-b", depends_on=["step:m29-a"]),
                _step("step:m29-c", depends_on=["step:m29-b"]),
            ]
        )
    )

    assert decision.valid_for_review is False
    assert "DEPENDENCY_CYCLE_DENIED" in decision.reason_codes


def test_explicit_dependency_edges_are_validated() -> None:
    decision = evaluate_task_plan(
        _plan(
            [_step("step:m29-a"), _step("step:m29-b")],
            dependencies=[
                TaskDependency(
                    dependency_id="dependency:m29-a-before-b",
                    before_step_id="step:m29-a",
                    after_step_id="step:m29-b",
                )
            ],
        )
    )

    assert decision.valid_for_review is True
    assert "TASK_PLAN_VALID_FOR_REVIEW" in decision.reason_codes
