import pytest

from ultimate_ai_agent.core.planning import (
    TaskGoal,
    TaskPlan,
    TaskPlanDecisionStatus,
    TaskPlanningRequest,
    TaskRiskLevel,
    TaskStep,
    TaskStepInputBoundary,
    TaskStepKind,
    evaluate_task_plan,
)


def _step(step_kind=TaskStepKind.review_metadata, risk=TaskRiskLevel.low, **overrides):
    data = {
        "step_id": f"step:m29-{step_kind.value.replace('_', '-')}",
        "step_kind": step_kind,
        "safe_summary": "Review metadata only.",
        "input_boundary": TaskStepInputBoundary(input_refs=["canonical:m29"]),
        "declared_risk_level": risk,
    }
    data.update(overrides)
    return TaskStep(**data)


def _plan(**overrides):
    data = {
        "plan_id": "plan:m29-no-exec",
        "goal": TaskGoal(goal_id="goal:m29-no-exec", safe_summary="Plan without execution."),
        "steps": [_step()],
        "safe_summary": "No-execution plan.",
    }
    data.update(overrides)
    return TaskPlan(**data)


@pytest.mark.parametrize(
    ("request_update", "reason"),
    [
        ({"execution_requested": True}, "TASK_EXECUTION_REQUEST_DENIED"),
        ({"auto_run_requested": True}, "TASK_AUTO_RUN_DENIED"),
        ({"schedule_requested": True}, "TASK_SCHEDULER_DENIED"),
    ],
)
def test_request_execution_auto_run_and_scheduler_are_denied(request_update, reason):
    request = TaskPlanningRequest(plan=_plan()).model_copy(update=request_update)
    decision = evaluate_task_plan(request)

    assert decision.status == TaskPlanDecisionStatus.denied
    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert decision.scheduler_registered is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    "step_kind",
    [
        TaskStepKind.tool_execution_planned,
        TaskStepKind.action_execution_planned,
        TaskStepKind.file_mutation_planned,
        TaskStepKind.memory_write_planned,
        TaskStepKind.network_call_planned,
        TaskStepKind.model_call_planned,
        TaskStepKind.browser_action_planned,
        TaskStepKind.mobile_device_action_planned,
        TaskStepKind.remote_execution_planned,
        TaskStepKind.plugin_enablement_planned,
        TaskStepKind.shell_execution_blocked,
    ],
)
def test_effectful_or_executing_steps_are_denied_without_running(step_kind):
    decision = evaluate_task_plan(_plan(steps=[_step(step_kind=step_kind, risk=TaskRiskLevel.high)]))

    assert decision.valid_for_review is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert "TASK_STEP_EXECUTION_DENIED" in decision.reason_codes


def test_risk_downgrade_by_caller_metadata_is_denied():
    step = _step(step_kind=TaskStepKind.file_mutation_planned, risk=TaskRiskLevel.low)
    decision = evaluate_task_plan(_plan(steps=[step]))

    assert decision.valid_for_review is False
    assert "TASK_RISK_DOWNGRADE_DENIED" in decision.reason_codes


def test_receipt_plan_cannot_claim_execution_or_raw_storage():
    decision = evaluate_task_plan(_plan())
    receipt = decision.receipt_plan.model_copy(update={"execution_performed": True})

    with pytest.raises(ValueError):
        receipt.model_validate(receipt.model_dump())

    raw_receipt = decision.receipt_plan.model_copy(update={"raw_content_stored": True})
    with pytest.raises(ValueError):
        raw_receipt.model_validate(raw_receipt.model_dump())


def test_manifest_explicitly_disables_background_workers():
    from ultimate_ai_agent.core.planning import build_task_planning_manifest

    manifest = build_task_planning_manifest(baseline_version="0.33.1")

    assert manifest.background_worker_enabled is False
