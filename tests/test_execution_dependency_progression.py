from ultimate_ai_agent.core.execution import (
    ExecutionRun,
    ExecutionStep,
    ExecutionStepInputBoundary,
    ExecutionStepMode,
    ExecutionStepStatus,
    ExecutionTransitionKind,
    ExecutionTransitionRequest,
    ExecutionTransitionStatus,
    evaluate_execution_transition,
)


def _step(step_id, depends_on=None, **overrides):
    data = {
        "step_id": step_id,
        "safe_summary": f"Validate {step_id}.",
        "mode": ExecutionStepMode.no_effect,
        "status": ExecutionStepStatus.ready,
        "input_boundary": ExecutionStepInputBoundary(input_refs=["canonical:m30"]),
        "depends_on": depends_on or [],
    }
    data.update(overrides)
    return ExecutionStep(
        **data,
    )


def _run(steps):
    return ExecutionRun(
        run_id="execution-run:m30-deps",
        source_task_plan_ref="plan:m30-deps",
        steps=steps,
        safe_summary="Dependency-aware no-effect run.",
    )


def _request(target_step_id="execution-step:m30-a"):
    return ExecutionTransitionRequest(
        run_id="execution-run:m30-deps",
        target_step_id=target_step_id,
        transition_id=f"execution-transition:{target_step_id.split(':', 1)[-1]}",
        transition_kind=ExecutionTransitionKind.complete_no_effect_step,
        replay_key=f"replay:{target_step_id}",
        safe_summary="Advance dependency-safe step.",
    )


def test_duplicate_step_ids_are_denied():
    decision = evaluate_execution_transition(
        _run([_step("execution-step:m30-a"), _step("execution-step:m30-a")]),
        _request("execution-step:m30-a"),
    )

    assert decision.status == ExecutionTransitionStatus.denied
    assert "DUPLICATE_EXECUTION_STEP_ID_DENIED" in decision.reason_codes


def test_missing_dependency_is_denied():
    decision = evaluate_execution_transition(
        _run([_step("execution-step:m30-a", depends_on=["execution-step:m30-missing"])]),
        _request("execution-step:m30-a"),
    )

    assert decision.status == ExecutionTransitionStatus.denied
    assert "MISSING_EXECUTION_DEPENDENCY_DENIED" in decision.reason_codes


def test_self_dependency_is_denied():
    decision = evaluate_execution_transition(
        _run([_step("execution-step:m30-a", depends_on=["execution-step:m30-a"])]),
        _request("execution-step:m30-a"),
    )

    assert decision.status == ExecutionTransitionStatus.denied
    assert "EXECUTION_DEPENDENCY_CYCLE_DENIED" in decision.reason_codes


def test_indirect_cycle_is_denied():
    decision = evaluate_execution_transition(
        _run(
            [
                _step("execution-step:m30-a", depends_on=["execution-step:m30-c"]),
                _step("execution-step:m30-b", depends_on=["execution-step:m30-a"]),
                _step("execution-step:m30-c", depends_on=["execution-step:m30-b"]),
            ]
        ),
        _request("execution-step:m30-a"),
    )

    assert decision.status == ExecutionTransitionStatus.denied
    assert "EXECUTION_DEPENDENCY_CYCLE_DENIED" in decision.reason_codes


def test_deterministic_next_step_order_uses_dependency_and_step_id():
    steps = [
        _step("execution-step:m30-c", depends_on=["execution-step:m30-a"]),
        _step("execution-step:m30-b"),
        _step("execution-step:m30-a", status=ExecutionStepStatus.completed_no_effect),
    ]
    run = _run(steps)

    assert [step.step_id for step in run.ready_steps()] == [
        "execution-step:m30-b",
        "execution-step:m30-c",
    ]
