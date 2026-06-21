from typing import Any
import pytest

from ultimate_ai_agent.core.execution import (
    DurableRunCorruptionError,
    DurableRunRecord,
    DurableRunState,
    DurableRunTransitionKind,
    DurableRunTransitionRequest,
    DurableRunTransitionStatus,
    ExecutionInputTrustLevel,
    ExecutionRun,
    ExecutionStep,
    ExecutionStepInputBoundary,
    ExecutionStepMode,
    ExecutionStepStatus,
    ExecutionTransitionKind,
    ExecutionTransitionRequest,
    ExecutionTransitionStatus,
    apply_durable_run_transition,
    build_durable_run_snapshot,
    evaluate_execution_transition,
    evaluate_durable_run_transition,
    restore_durable_run_snapshot,
)


def _step(**overrides: Any) -> ExecutionStep:
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


def _request(**overrides: Any) -> ExecutionTransitionRequest:
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


def _durable_record(**overrides: Any) -> DurableRunRecord:
    data = {
        "run_id": "durable-run:p1-010",
        "source_ref": "plan:p1-010",
        "safe_summary": "Durable run contract summary.",
    }
    data.update(overrides)
    return DurableRunRecord(**data)


def _durable_request(
    transition_kind: DurableRunTransitionKind = DurableRunTransitionKind.mark_ready,
    suffix: str = "ready",
    **overrides: Any,
) -> Any:
    data = {
        "run_id": "durable-run:p1-010",
        "transition_id": f"durable-transition:p1-010-{suffix}",
        "transition_kind": transition_kind,
        "idempotency_key": f"idempotency:p1-010-{suffix}",
        "actor_ref": "actor:p1-010-reviewer",
        "audit_ref": f"audit:p1-010-{suffix}",
        "receipt_ref": f"receipt:p1-010-{suffix}",
        "replay_ref": f"replay:p1-010-{suffix}",
        "rollback_ref": f"rollback:p1-010-{suffix}",
        "safe_summary": "State-only durable run contract transition.",
        "evidence_refs": [f"evidence:p1-010-{suffix}"],
    }
    data.update(overrides)
    return DurableRunTransitionRequest(**data)


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
def test_effectful_step_modes_are_denied_without_execution(mode: str, reason: str) -> None:
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
def test_model_copy_mutated_step_input_boundary_is_revalidated(update: Any, reason: str) -> None:
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
def test_non_authoritative_refs_cannot_authorize_execution(input_ref: Any, trust_level: Any, reason: str) -> None:
    boundary = ExecutionStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
    decision = evaluate_execution_transition(_run(_step(input_boundary=boundary)), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


def test_transition_request_execution_flags_are_denied_after_model_copy() -> None:
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


def test_hidden_side_effect_metadata_is_denied_after_model_copy() -> None:
    step = _step().model_copy(update={"metadata": {"declared_effect": "file_write"}})

    decision = evaluate_execution_transition(_run(step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "HIDDEN_SIDE_EFFECT_DENIED" in decision.reason_codes


def test_blocked_step_cannot_complete_without_safe_transition() -> None:
    blocked_step = _step(status=ExecutionStepStatus.blocked)

    decision = evaluate_execution_transition(_run(blocked_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_STEP_BLOCKED_DENIED" in decision.reason_codes


def test_completed_step_cannot_complete_twice() -> None:
    completed_step = _step(status=ExecutionStepStatus.completed_no_effect)

    decision = evaluate_execution_transition(_run(completed_step), _request())

    assert decision.status == ExecutionTransitionStatus.denied
    assert decision.execution_performed is False
    assert "EXECUTION_STEP_ALREADY_COMPLETED_DENIED" in decision.reason_codes


def test_durable_run_invalid_transition_is_denied_without_state_change() -> None:
    record = _durable_record()
    request = _durable_request(DurableRunTransitionKind.pause, "pause-from-created")

    decision = evaluate_durable_run_transition(record, request)

    assert decision.status == DurableRunTransitionStatus.denied
    assert decision.previous_state == DurableRunState.created
    assert decision.next_state == DurableRunState.created
    assert decision.execution_performed is False
    assert "DURABLE_RUN_INVALID_TRANSITION_DENIED" in decision.reason_codes


def test_durable_run_duplicate_mutation_attempt_is_blocked_by_idempotency() -> None:
    record = _durable_record()
    request = _durable_request()

    first = apply_durable_run_transition(record, request)
    second = apply_durable_run_transition(first.record, request)

    assert first.decision.status == DurableRunTransitionStatus.accepted
    assert first.record.state == DurableRunState.ready
    assert second.decision.status == DurableRunTransitionStatus.denied
    assert second.record.state == DurableRunState.ready
    assert "DURABLE_RUN_IDEMPOTENCY_REPLAY_DENIED" in second.decision.reason_codes


@pytest.mark.parametrize(
    ("initial_state", "transition_kind", "suffix", "expected_state", "extra", "expected_next"),
    [
        (
            DurableRunState.running,
            DurableRunTransitionKind.pause,
            "pause-lifecycle",
            DurableRunState.running,
            {},
            DurableRunState.paused,
        ),
        (
            DurableRunState.paused,
            DurableRunTransitionKind.resume,
            "resume-lifecycle",
            DurableRunState.paused,
            {},
            DurableRunState.running,
        ),
        (
            DurableRunState.running,
            DurableRunTransitionKind.cancel,
            "cancel-lifecycle",
            DurableRunState.running,
            {},
            DurableRunState.cancelled,
        ),
        (
            DurableRunState.failed,
            DurableRunTransitionKind.retry,
            "retry-lifecycle",
            DurableRunState.failed,
            {},
            DurableRunState.retry_pending,
        ),
        (
            DurableRunState.blocked,
            DurableRunTransitionKind.dead_letter,
            "dead-letter-lifecycle",
            DurableRunState.blocked,
            {"failure_ref": "failure:p1-026-dead-letter"},
            DurableRunState.dead_lettered,
        ),
        (
            DurableRunState.running,
            DurableRunTransitionKind.recover_after_restart,
            "restart-lifecycle",
            DurableRunState.running,
            {"restart_ref": "restart:p1-026-recovery"},
            DurableRunState.restart_recovery,
        ),
    ],
)
def test_durable_run_lifecycle_transitions_are_explicit_and_safe(
    initial_state: Any,
    transition_kind: Any,
    suffix: str,
    expected_state: Any,
    extra: Any,
    expected_next: Any,
) -> None:
    record = _durable_record(state=initial_state)
    request = _durable_request(
        transition_kind,
        suffix,
        expected_state=expected_state,
        **extra,
    )

    result = apply_durable_run_transition(record, request)

    assert result.decision.status == DurableRunTransitionStatus.accepted
    assert result.decision.authority_boundary_ref == "authority-boundary:durable-run-state-only"
    assert result.decision.execution_performed is False
    assert result.record.state == expected_next
    assert result.record.generation == record.generation + 1
    assert result.record.idempotency_records[-1].idempotency_key == request.idempotency_key
    assert result.record.idempotency_records[-1].lifecycle_action is True


def test_durable_run_lifecycle_repeat_is_idempotent_without_second_mutation() -> None:
    record = _durable_record(state=DurableRunState.running)
    request = _durable_request(
        DurableRunTransitionKind.pause,
        "pause-idempotent",
        expected_state=DurableRunState.running,
    )

    first = apply_durable_run_transition(record, request)
    second = apply_durable_run_transition(first.record, request)

    assert first.decision.status == DurableRunTransitionStatus.accepted
    assert first.record.state == DurableRunState.paused
    assert second.decision.status == DurableRunTransitionStatus.idempotent_replay
    assert second.decision.idempotent_replay is True
    assert second.decision.reason_codes == ["DURABLE_RUN_LIFECYCLE_IDEMPOTENT_REPLAY"]
    assert second.record == first.record
    assert second.record.generation == 1


def test_durable_run_lifecycle_reused_idempotency_with_different_request_is_denied() -> None:
    record = _durable_record(state=DurableRunState.running)
    first_request = _durable_request(
        DurableRunTransitionKind.pause,
        "pause-conflict",
        expected_state=DurableRunState.running,
    )
    first = apply_durable_run_transition(record, first_request)
    conflicting_request = _durable_request(
        DurableRunTransitionKind.resume,
        "resume-conflict",
        idempotency_key=first_request.idempotency_key,
        expected_state=DurableRunState.paused,
    )

    second = apply_durable_run_transition(first.record, conflicting_request)

    assert first.decision.status == DurableRunTransitionStatus.accepted
    assert second.decision.status == DurableRunTransitionStatus.denied
    assert second.record == first.record
    assert "DURABLE_RUN_IDEMPOTENCY_CONFLICT_DENIED" in second.decision.reason_codes


def test_durable_run_tampered_idempotency_record_run_ref_is_denied() -> None:
    record = _durable_record(state=DurableRunState.running)
    request = _durable_request(
        DurableRunTransitionKind.pause,
        "pause-tamper",
        expected_state=DurableRunState.running,
    )
    first = apply_durable_run_transition(record, request)
    tampered_records = [
        item.model_copy(update={"run_id": "durable-run:p1-026-other"})
        for item in first.record.idempotency_records
    ]
    tampered = first.record.model_copy(update={"idempotency_records": tampered_records})
    repeat = evaluate_durable_run_transition(tampered, request)

    assert repeat.status == DurableRunTransitionStatus.denied
    assert "DURABLE_RUN_RECORD_REVALIDATION_FAILED" in repeat.reason_codes


def test_durable_run_lifecycle_stale_expected_state_is_denied() -> None:
    record = _durable_record(state=DurableRunState.paused)
    request = _durable_request(
        DurableRunTransitionKind.pause,
        "pause-stale",
        expected_state=DurableRunState.running,
    )

    decision = evaluate_durable_run_transition(record, request)

    assert decision.status == DurableRunTransitionStatus.denied
    assert decision.stale_request is True
    assert "DURABLE_RUN_STALE_STATE_DENIED" in decision.reason_codes


def test_durable_run_dead_letter_requires_failure_ref_and_keeps_failure_visible() -> None:
    record = _durable_record(state=DurableRunState.blocked)
    missing_failure = _durable_request(
        DurableRunTransitionKind.dead_letter,
        "dead-letter-missing-failure",
        expected_state=DurableRunState.blocked,
    )
    valid = _durable_request(
        DurableRunTransitionKind.dead_letter,
        "dead-letter-visible",
        expected_state=DurableRunState.blocked,
        failure_ref="failure:p1-026-visible",
    )

    denied = evaluate_durable_run_transition(record, missing_failure)
    accepted = apply_durable_run_transition(record, valid)

    assert denied.status == DurableRunTransitionStatus.denied
    assert "DURABLE_RUN_DEAD_LETTER_REF_REQUIRED" in denied.reason_codes
    assert accepted.decision.status == DurableRunTransitionStatus.accepted
    assert accepted.record.state == DurableRunState.dead_lettered
    assert accepted.record.failure_refs == ["failure:p1-026-visible"]


def test_durable_run_repeated_cancel_is_idempotent_even_after_terminal_state() -> None:
    record = _durable_record(state=DurableRunState.running)
    request = _durable_request(
        DurableRunTransitionKind.cancel,
        "cancel-idempotent-terminal",
        expected_state=DurableRunState.running,
    )

    first = apply_durable_run_transition(record, request)
    second = apply_durable_run_transition(first.record, request)

    assert first.record.state == DurableRunState.cancelled
    assert second.decision.status == DurableRunTransitionStatus.idempotent_replay
    assert "DURABLE_RUN_TERMINAL_STATE_DENIED" not in second.decision.reason_codes
    assert second.record == first.record


def test_durable_run_replay_ref_reuse_is_denied() -> None:
    record = _durable_record(state=DurableRunState.ready, replay_refs=["replay:p1-010-reused"])
    request = _durable_request(
        DurableRunTransitionKind.start,
        "start",
        replay_ref="replay:p1-010-reused",
    )

    decision = evaluate_durable_run_transition(record, request)

    assert decision.status == DurableRunTransitionStatus.denied
    assert decision.execution_performed is False
    assert "DURABLE_RUN_REPLAY_REF_REUSE_DENIED" in decision.reason_codes


def test_durable_run_evidence_remains_redacted_refs_only() -> None:
    result = apply_durable_run_transition(_durable_record(), _durable_request())
    serialized = result.record.model_dump_json().lower()

    assert result.decision.status == DurableRunTransitionStatus.accepted
    assert result.record.evidence_refs == ["evidence:p1-010-ready"]
    assert result.record.audit_refs == ["audit:p1-010-ready"]
    assert result.record.receipt_refs == ["receipt:p1-010-ready"]
    for forbidden in ["prompt", "response", "provider_payload", "local_path", "hostname"]:
        assert forbidden not in serialized


def test_durable_run_restart_recovery_and_snapshot_hash_are_visible() -> None:
    record = _durable_record(state=DurableRunState.running, generation=3)
    request = _durable_request(
        DurableRunTransitionKind.recover_after_restart,
        "restart-recovery",
        restart_ref="restart:p1-010-recovery",
    )

    result = apply_durable_run_transition(record, request)
    snapshot = build_durable_run_snapshot(result.record)
    restored = restore_durable_run_snapshot(snapshot)
    tampered = snapshot.model_dump()
    tampered["record"]["generation"] = 99

    assert result.decision.status == DurableRunTransitionStatus.accepted
    assert result.record.state == DurableRunState.restart_recovery
    assert result.record.generation == 4
    assert result.record.restart_refs == ["restart:p1-010-recovery"]
    assert restored == result.record
    with pytest.raises(DurableRunCorruptionError, match="DURABLE_RUN_SNAPSHOT_HASH_MISMATCH"):
        restore_durable_run_snapshot(tampered)


def test_durable_run_failure_transition_requires_failure_ref() -> None:
    record = _durable_record(state=DurableRunState.running)
    request = _durable_request(DurableRunTransitionKind.fail, "fail")

    decision = evaluate_durable_run_transition(record, request)

    assert decision.status == DurableRunTransitionStatus.denied
    assert "DURABLE_RUN_FAILURE_REF_REQUIRED" in decision.reason_codes


def test_durable_run_authority_flags_are_denied_after_model_copy() -> None:
    record = _durable_record()
    request = _durable_request().model_copy(
        update={
            "execution_requested": True,
            "auto_run_requested": True,
            "schedule_requested": True,
            "background_worker_requested": True,
            "side_effect_execution_enabled": True,
        }
    )

    decision = evaluate_durable_run_transition(record, request)

    assert decision.status == DurableRunTransitionStatus.denied
    assert decision.execution_performed is False
    assert "DURABLE_RUN_EXECUTION_REQUEST_DENIED" in decision.reason_codes
    assert "DURABLE_RUN_AUTO_RUN_DENIED" in decision.reason_codes
    assert "DURABLE_RUN_SCHEDULE_DENIED" in decision.reason_codes
    assert "DURABLE_RUN_BACKGROUND_WORKER_DENIED" in decision.reason_codes
    assert "DURABLE_RUN_SIDE_EFFECT_EXECUTION_DENIED" in decision.reason_codes
