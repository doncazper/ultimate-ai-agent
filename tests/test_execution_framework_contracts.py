from typing import Any
from ultimate_ai_agent.core.execution import (
    ExecutionRun,
    ExecutionRunStatus,
    ExecutionStep,
    ExecutionStepInputBoundary,
    ExecutionStepMode,
    ExecutionStepStatus,
    ExecutionTransitionKind,
    ExecutionTransitionRequest,
    ExecutionTransitionStatus,
    build_execution_framework_manifest,
    evaluate_execution_transition,
)


def _step(step_id: str = "execution-step:m30-a", **overrides: Any) -> ExecutionStep:
    data = {
        "step_id": step_id,
        "safe_summary": "Validate safe metadata only.",
        "mode": ExecutionStepMode.no_effect,
        "status": ExecutionStepStatus.ready,
        "input_boundary": ExecutionStepInputBoundary(input_refs=["canonical:m30"]),
    }
    data.update(overrides)
    return ExecutionStep(**data)


def _run(*steps: ExecutionStep, **overrides: Any) -> ExecutionRun:
    data = {
        "run_id": "execution-run:m30-safe",
        "source_task_plan_ref": "plan:m30-safe",
        "steps": list(steps) or [_step()],
        "safe_summary": "Side-effect-safe execution-state-machine preview.",
    }
    data.update(overrides)
    return ExecutionRun(**data)


def _request(
    target_step_id: str = "execution-step:m30-a",
    replay_key: str = "replay:m30-a",
    **overrides: Any,
) -> ExecutionTransitionRequest:
    data = {
        "run_id": "execution-run:m30-safe",
        "target_step_id": target_step_id,
        "transition_id": f"execution-transition:{replay_key.split(':', 1)[-1]}",
        "transition_kind": ExecutionTransitionKind.complete_no_effect_step,
        "replay_key": replay_key,
        "safe_summary": "Complete a no-effect validation step.",
    }
    data.update(overrides)
    return ExecutionTransitionRequest(**data)


def test_default_manifest_is_state_machine_only_and_non_executing() -> None:
    manifest = build_execution_framework_manifest(baseline_version="0.34.0")

    assert manifest.execution_state_machine_enabled is True
    assert manifest.real_task_execution_enabled is False
    assert manifest.action_execution_enabled is False
    assert manifest.tool_execution_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.network_call_enabled is False
    assert manifest.model_provider_call_enabled is False
    assert manifest.scheduler_enabled is False
    assert manifest.background_worker_enabled is False
    assert manifest.backend_execution_routes_added is False
    assert manifest.production_authority_enabled is False


def test_safe_no_effect_step_can_advance_without_execution() -> None:
    decision = evaluate_execution_transition(_run(), _request())

    assert decision.status == ExecutionTransitionStatus.approved_no_effect_transition
    assert decision.run_status == ExecutionRunStatus.running_no_effect
    assert decision.step_status == ExecutionStepStatus.completed_no_effect
    assert decision.execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is False
    assert "EXECUTION_TRANSITION_ALLOWED_NO_EFFECT" in decision.reason_codes


def test_dependencies_must_be_completed_before_step_advances() -> None:
    first = _step("execution-step:m30-a")
    second = _step("execution-step:m30-b", status=ExecutionStepStatus.pending, depends_on=["execution-step:m30-a"])
    decision = evaluate_execution_transition(_run(first, second), _request(target_step_id="execution-step:m30-b"))

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_DEPENDENCY_UNMET_DENIED" in decision.reason_codes


def test_completed_dependency_allows_next_no_effect_step() -> None:
    first = _step("execution-step:m30-a", status=ExecutionStepStatus.completed_no_effect)
    second = _step("execution-step:m30-b", depends_on=["execution-step:m30-a"])
    decision = evaluate_execution_transition(
        _run(first, second),
        _request(target_step_id="execution-step:m30-b", replay_key="replay:m30-b"),
    )

    assert decision.status == ExecutionTransitionStatus.approved_no_effect_transition
    assert decision.step_status == ExecutionStepStatus.completed_no_effect
    assert decision.execution_performed is False


def test_replay_key_reuse_is_denied() -> None:
    run = _run(replay_keys_seen=["replay:m30-a"])

    decision = evaluate_execution_transition(run, _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_REPLAY_DENIED" in decision.reason_codes


def test_transition_id_reuse_is_denied() -> None:
    run = _run(transition_ids_seen=["execution-transition:m30-a"])

    decision = evaluate_execution_transition(run, _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_TRANSITION_REPLAY_DENIED" in decision.reason_codes


def test_complete_requires_ready_step_status() -> None:
    pending_step = _step(status=ExecutionStepStatus.pending)

    decision = evaluate_execution_transition(_run(pending_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_STEP_NOT_READY_DENIED" in decision.reason_codes


def test_run_cannot_finalize_until_all_steps_complete() -> None:
    decision = evaluate_execution_transition(
        _run(),
        _request(
            target_step_id=None,
            replay_key="replay:m30-finalize-blocked",
            transition_id="execution-transition:m30-finalize-blocked",
            transition_kind=ExecutionTransitionKind.finalize_no_effect_run,
        ),
    )

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_RUN_FINALIZE_INCOMPLETE_DENIED" in decision.reason_codes


def test_run_can_finalize_after_all_steps_complete_without_execution() -> None:
    decision = evaluate_execution_transition(
        _run(_step(status=ExecutionStepStatus.completed_no_effect)),
        _request(
            target_step_id=None,
            replay_key="replay:m30-finalize",
            transition_id="execution-transition:m30-finalize",
            transition_kind=ExecutionTransitionKind.finalize_no_effect_run,
        ),
    )

    assert decision.status == ExecutionTransitionStatus.approved_no_effect_transition
    assert decision.run_status == ExecutionRunStatus.completed_no_effect
    assert decision.execution_performed is False
    assert "EXECUTION_RUN_FINALIZED_NO_EFFECT" in decision.reason_codes
