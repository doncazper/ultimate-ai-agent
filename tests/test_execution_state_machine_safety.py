import pytest

from ultimate_ai_agent.core.execution import (
    ExecutionInputTrustLevel,
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


def _step(**overrides) -> ExecutionStep:
    data = {
        "step_id": "execution-step:m30-safety",
        "safe_summary": "Validate safe metadata only.",
        "mode": ExecutionStepMode.no_effect,
        "status": ExecutionStepStatus.ready,
        "input_boundary": ExecutionStepInputBoundary(input_refs=["canonical:m30"]),
    }
    data.update(overrides)
    return ExecutionStep(**data)


def _run(step: ExecutionStep) -> ExecutionRun:
    return ExecutionRun(
        run_id="execution-run:m30-safety",
        source_task_plan_ref="plan:m30-safety",
        steps=[step],
        safe_summary="Safety probe run.",
    )


def _request(**overrides) -> ExecutionTransitionRequest:
    data = {
        "run_id": "execution-run:m30-safety",
        "target_step_id": "execution-step:m30-safety",
        "transition_id": "execution-transition:m30-safety",
        "transition_kind": ExecutionTransitionKind.complete_no_effect_step,
        "replay_key": "replay:m30-safety",
        "safe_summary": "Complete no-effect step.",
    }
    data.update(overrides)
    return ExecutionTransitionRequest(**data)


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        (ExecutionStepMode.task_execution_blocked, "TASK_EXECUTION_DENIED"),
        (ExecutionStepMode.action_execution_blocked, "ACTION_EXECUTION_DENIED"),
        (ExecutionStepMode.tool_execution_blocked, "TOOL_EXECUTION_DENIED"),
        (ExecutionStepMode.file_mutation_blocked, "FILE_MUTATION_DENIED"),
        (ExecutionStepMode.memory_write_blocked, "MEMORY_WRITE_DENIED"),
        (ExecutionStepMode.network_call_blocked, "NETWORK_CALL_DENIED"),
        (ExecutionStepMode.model_call_blocked, "MODEL_CALL_DENIED"),
        (ExecutionStepMode.scheduler_blocked, "SCHEDULER_DENIED"),
        (ExecutionStepMode.background_worker_blocked, "BACKGROUND_WORKER_DENIED"),
    ],
)
def test_effectful_step_modes_are_denied_without_execution(mode, reason):
    decision = evaluate_execution_transition(_run(_step(mode=mode)), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"contains_raw_prompt": True}, "RAW_PROMPT_DENIED"),
        ({"contains_raw_model_output": True}, "RAW_MODEL_OUTPUT_DENIED"),
        ({"contains_raw_file_content": True}, "RAW_FILE_CONTENT_DENIED"),
        ({"contains_raw_transcript": True}, "RAW_TRANSCRIPT_DENIED"),
        ({"contains_secret_like_content": True}, "SECRET_LIKE_INPUT_DENIED"),
        ({"metadata": {"token": "abc123"}}, "SECRET_METADATA_DENIED"),
    ],
)
def test_model_copy_mutated_step_input_boundary_is_revalidated(update, reason):
    step = _step()
    mutated_boundary = step.input_boundary.model_copy(update=update)
    mutated_step = step.model_copy(update={"input_boundary": mutated_boundary})

    decision = evaluate_execution_transition(_run(mutated_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("input_ref", "trust_level", "reason"),
    [
        ("model:m30", ExecutionInputTrustLevel.model_output_blocked, "MODEL_OUTPUT_NOT_EXECUTION_AUTHORITY"),
        ("memory:m30", ExecutionInputTrustLevel.memory_ref, "MEMORY_REF_NOT_EXECUTION_AUTHORITY"),
        ("context-pack:m30", ExecutionInputTrustLevel.context_pack_ref, "CONTEXT_PACK_NOT_EXECUTION_AUTHORITY"),
        ("tool-intent:m27", ExecutionInputTrustLevel.tool_intent_ref, "TOOL_INTENT_NOT_EXECUTION_AUTHORITY"),
        ("approval:m28", ExecutionInputTrustLevel.approval_ref, "APPROVAL_REF_NOT_EXECUTION_AUTHORITY"),
        ("openwebui:m30", ExecutionInputTrustLevel.openwebui_output_blocked, "OPENWEBUI_OUTPUT_NOT_EXECUTION_AUTHORITY"),
        ("control-center:m30", ExecutionInputTrustLevel.control_center_preview_blocked, "CONTROL_CENTER_PREVIEW_NOT_EXECUTION_AUTHORITY"),
        ("random:m30", ExecutionInputTrustLevel.unknown_blocked, "UNKNOWN_INPUT_REF_DENIED"),
    ],
)
def test_non_authoritative_refs_cannot_authorize_execution(input_ref, trust_level, reason):
    boundary = ExecutionStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
    decision = evaluate_execution_transition(_run(_step(input_boundary=boundary)), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


def test_transition_request_execution_flags_are_denied_after_model_copy():
    request = _request().model_copy(
        update={
            "execution_requested": True,
            "auto_run_requested": True,
            "schedule_requested": True,
            "background_worker_requested": True,
            "side_effect_execution_enabled": True,
        }
    )

    decision = evaluate_execution_transition(_run(_step()), request)

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_REQUEST_DENIED" in decision.reason_codes
    assert "AUTO_RUN_DENIED" in decision.reason_codes
    assert "SCHEDULE_DENIED" in decision.reason_codes
    assert "BACKGROUND_WORKER_DENIED" in decision.reason_codes
    assert "SIDE_EFFECT_EXECUTION_DENIED" in decision.reason_codes


def test_hidden_side_effect_metadata_is_denied_after_model_copy():
    step = _step().model_copy(update={"metadata": {"declared_effect": "file_write"}})

    decision = evaluate_execution_transition(_run(step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "HIDDEN_SIDE_EFFECT_DENIED" in decision.reason_codes


def test_blocked_step_cannot_complete_without_safe_transition():
    blocked_step = _step(status=ExecutionStepStatus.blocked)

    decision = evaluate_execution_transition(_run(blocked_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_STEP_BLOCKED_DENIED" in decision.reason_codes


def test_completed_step_cannot_complete_twice():
    completed_step = _step(status=ExecutionStepStatus.completed_no_effect)

    decision = evaluate_execution_transition(_run(completed_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_STEP_ALREADY_COMPLETED_DENIED" in decision.reason_codes
