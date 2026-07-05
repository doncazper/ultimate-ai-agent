import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.execution import (
    StagedOrchestrationCallbackKind,
    StagedOrchestrationCallbackRef,
    StagedOrchestrationPlan,
    StagedOrchestrationReplayStatus,
    StagedOrchestrationStatus,
    build_sample_staged_orchestration_plan,
    build_sample_staged_orchestration_read_model,
    replay_staged_orchestration_checkpoint,
    validate_staged_orchestration_plan,
)


client = TestClient(app)


def _plan_with(**updates: object) -> StagedOrchestrationPlan:
    payload = build_sample_staged_orchestration_plan().model_dump(mode="json")
    payload.update(updates)
    return StagedOrchestrationPlan(**payload)


def test_sample_staged_orchestration_read_model_is_safe_and_waiting() -> None:
    read_model = build_sample_staged_orchestration_read_model()

    assert read_model.backend_owned is True
    assert read_model.plan.status == StagedOrchestrationStatus.waiting.value
    assert read_model.validation.status == "accepted"
    assert read_model.progress.total_stage_count == 3
    assert read_model.progress.total_step_count == 4
    assert read_model.progress.waiting_count == 1
    assert read_model.progress.degraded_count == 1
    assert read_model.progress.skipped_count == 1
    assert read_model.execution_performed is False
    assert read_model.raw_payloads_persisted is False
    assert read_model.control_center_can_mint_authority is False


def test_dependency_validation_rejects_missing_same_stage_future_and_cycle() -> None:
    base = build_sample_staged_orchestration_plan()
    steps = [step.model_dump(mode="json") for step in base.steps]
    steps[0]["depends_on_step_refs"] = ["step-ref:staged-orchestration:approval-wait"]
    steps[1]["depends_on_step_refs"] = ["step-ref:staged-orchestration:missing"]
    steps[2]["depends_on_step_refs"] = ["step-ref:staged-orchestration:approval-wait"]
    steps[3]["depends_on_step_refs"] = ["step-ref:staged-orchestration:recovery-skipped"]
    plan = _plan_with(steps=steps)

    decision = validate_staged_orchestration_plan(plan)

    assert decision.status == "denied"
    assert "reason-ref:staged-orchestration:future-stage-dependency" in decision.reason_codes
    assert "reason-ref:staged-orchestration:missing-dependency" in decision.reason_codes
    assert "reason-ref:staged-orchestration:same-stage-dependency" in decision.reason_codes
    assert "reason-ref:staged-orchestration:dependency-cycle" in decision.reason_codes


def test_degraded_step_requires_handoff() -> None:
    base = build_sample_staged_orchestration_plan()
    plan = _plan_with(degraded_handoffs=[])

    decision = validate_staged_orchestration_plan(plan)

    assert decision.status == "denied"
    assert "reason-ref:staged-orchestration:degraded-handoff-missing" in decision.reason_codes


def test_downstream_of_failed_dependency_must_skip_block_or_degrade() -> None:
    base = build_sample_staged_orchestration_plan()
    steps = [step.model_dump(mode="json") for step in base.steps]
    steps[1]["status"] = StagedOrchestrationStatus.failed.value
    steps[3]["status"] = StagedOrchestrationStatus.pending.value
    plan = _plan_with(steps=steps)

    decision = validate_staged_orchestration_plan(plan)

    assert decision.status == "denied"
    assert "reason-ref:staged-orchestration:downstream-not-skipped" in decision.reason_codes

    steps[3]["status"] = StagedOrchestrationStatus.skipped.value
    fixed = _plan_with(steps=steps)
    fixed_decision = validate_staged_orchestration_plan(fixed)
    assert "reason-ref:staged-orchestration:downstream-not-skipped" not in (
        fixed_decision.reason_codes
    )


def test_checkpoint_replay_is_idempotent_and_conflict_bound() -> None:
    plan = build_sample_staged_orchestration_plan()
    checkpoint = plan.checkpoints[0]

    replay = replay_staged_orchestration_checkpoint(
        plan,
        checkpoint_ref=checkpoint.checkpoint_ref,
        replay_ref=checkpoint.replay_ref,
        fingerprint_ref=checkpoint.fingerprint_ref,
    )
    conflict = replay_staged_orchestration_checkpoint(
        plan,
        checkpoint_ref=checkpoint.checkpoint_ref,
        replay_ref="replay-ref:staged-orchestration:changed",
        fingerprint_ref=checkpoint.fingerprint_ref,
    )

    assert replay.status == StagedOrchestrationReplayStatus.idempotent_replay.value
    assert replay.execution_performed is False
    assert conflict.status == StagedOrchestrationReplayStatus.denied.value
    assert "reason-ref:staged-orchestration:checkpoint-replay-conflict" in conflict.reason_codes


def test_effectful_callback_and_raw_metadata_are_rejected() -> None:
    with pytest.raises(ValidationError):
        StagedOrchestrationCallbackRef(
            callback_ref="callback-ref:staged-orchestration:effectful",
            callback_kind=StagedOrchestrationCallbackKind.existing_authority_lane_required,
            safe_summary="Attempt non-deterministic callback.",
            deterministic=False,
            no_effect=False,
            execution_enabled=True,
        )

    base = build_sample_staged_orchestration_plan()
    steps = [step.model_dump(mode="json") for step in base.steps]
    steps[0]["safe_metadata"] = {"unsafe_marker": "bearer example"}
    with pytest.raises(ValidationError):
        _plan_with(steps=steps)


def test_runtime_cli_inspects_staged_orchestration_safe_json(capsys) -> None:
    exit_code = uaa_runtime.main(["inspect-staged-orchestration", "--json"])

    assert exit_code == 0
    payload = capsys.readouterr().out
    assert "staged_orchestration" in payload
    assert "raw_content_omitted" in payload
    assert "background_autonomy_enabled" in payload


def test_runtime_api_exposes_staged_orchestration_read_model() -> None:
    response = client.get("/api/runtime/staged-orchestration")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["api_ref"] == "GET /api/runtime/staged-orchestration"
    assert data["execution_performed"] is False
    assert data["plan"]["background_autonomy_enabled"] is False
    assert data["validation"]["status"] == "accepted"
