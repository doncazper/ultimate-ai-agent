import hashlib
import json
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.execution import (
    ExecutionStepMode,
    StagedOrchestrationApprovedRuntimeCommandBinding,
    StagedOrchestrationCallbackKind,
    StagedOrchestrationCallbackRef,
    StagedOrchestrationPlan,
    StagedOrchestrationStage,
    StagedOrchestrationReplayStatus,
    StagedOrchestrationStatus,
    StagedOrchestrationStep,
    build_sample_staged_orchestration_plan,
    build_sample_staged_orchestration_read_model,
    build_staged_orchestration_read_model,
    execute_approved_runtime_command_step,
    replay_staged_orchestration_checkpoint,
    validate_staged_orchestration_plan,
)
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    RuntimeApprovalBindingRequest,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeInvocationStore,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.time import utc_now


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def _plan_with(**updates: object) -> StagedOrchestrationPlan:
    payload = build_sample_staged_orchestration_plan().model_dump(mode="json")
    payload.update(updates)
    return StagedOrchestrationPlan(**payload)


def _hash_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _approved_runtime_command_request(
    intent: str = "focused_pytest",
) -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent=intent,
        requested_profile="operator-approved",
        target_refs=["test-ref:staged-orchestration-runtime-command"],
        safe_summary="Run exact approved staged orchestration runtime command lane.",
    )


def _approve_runtime_command(
    store: RuntimeInvocationStore,
    request: RuntimeCommandExecutionRequest,
):
    command_intent = str(getattr(request.intent, "value", request.intent))
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref=(
            f"idempotency-ref:staged-orchestration-runtime-create-{command_intent}"
        ),
    )
    exact_scope_ref = _hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "payload_fingerprint_ref": created.record.payload_fingerprint_ref,
            "policy_decision_ref": created.record.policy_decision.policy_decision_ref,
            "requested_authority": created.record.request.requested_authority,
        },
    )
    approval_ref = _hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "requested_authority": created.record.request.requested_authority,
            "requested_profile": created.record.request.requested_profile,
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": command_intent,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": created.record.payload_fingerprint_ref,
            "policy_decision_ref": created.record.policy_decision.policy_decision_ref,
        },
    )
    action_envelope_ref = _hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision="approve",
            action_envelope_ref=action_envelope_ref,
            exact_scope_ref=exact_scope_ref,
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent=command_intent,
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Action Inbox approved exact staged orchestration runtime lane.",
        ),
        idempotency_ref=(
            f"idempotency-ref:staged-orchestration-runtime-approve-{command_intent}"
        ),
    )


def _execute_request_for(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    return RuntimeExecuteRequest(
        approval_ref=record.action_inbox_envelope.approval_ref,
        action_envelope_ref=record.action_inbox_envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        safe_summary="Execute exact approved staged orchestration runtime command.",
    )


def _runtime_command_plan(record) -> StagedOrchestrationPlan:
    assert record.action_inbox_envelope is not None
    command_intent = str(
        getattr(
            record.action_inbox_envelope.command_intent,
            "value",
            record.action_inbox_envelope.command_intent,
        )
    )
    binding = StagedOrchestrationApprovedRuntimeCommandBinding(
        binding_ref=f"runtime-binding-ref:staged-orchestration:{command_intent.replace('_', '-')}",
        runtime_invocation_ref=record.invocation_ref,
        runtime_action_envelope_ref=record.action_inbox_envelope.action_envelope_ref,
        runtime_approval_ref=record.action_inbox_envelope.approval_ref,
        runtime_exact_scope_ref=record.action_inbox_envelope.exact_scope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        command_intent=command_intent,
        safe_summary="Bind one approved utility runtime command to one orchestration step.",
    )
    stage = StagedOrchestrationStage(
        stage_ref="stage-ref:staged-orchestration:runtime-command",
        sequence=1,
        safe_summary="Execute one exact approved runtime command step.",
        status=StagedOrchestrationStatus.waiting,
        step_refs=["step-ref:staged-orchestration:runtime-command"],
        evidence_refs=["evidence-ref:staged-orchestration:runtime-command"],
    )
    step = StagedOrchestrationStep(
        step_ref="step-ref:staged-orchestration:runtime-command",
        stage_ref=stage.stage_ref,
        safe_summary="Execute the approved utility runtime command through RuntimeGateway.",
        status=StagedOrchestrationStatus.waiting,
        mode=ExecutionStepMode.approved_runtime_command,
        policy_ref="policy-ref:staged-orchestration:approved-runtime-command",
        approval_posture_ref="approval-posture-ref:staged-orchestration:exact-runtime-command",
        evidence_refs=["evidence-ref:staged-orchestration:runtime-command"],
        runtime_command_binding=binding,
        execution_ready=True,
    )
    return StagedOrchestrationPlan(
        plan_ref="plan-ref:staged-orchestration:runtime-command",
        run_ref="run-ref:staged-orchestration:runtime-command",
        turn_run_approval_chain_ref="chain-ref:staged-orchestration:runtime-command",
        route_decision_binding_ref="route-binding-ref:staged-orchestration:runtime-command",
        safe_summary="Staged orchestration plan with one approved runtime command step.",
        status=StagedOrchestrationStatus.waiting,
        stages=[stage],
        steps=[step],
        evidence_refs=["evidence-ref:staged-orchestration:runtime-command"],
        receipt_refs=["receipt-ref:staged-orchestration:runtime-command-planned"],
        no_effect=False,
        approved_runtime_command_execution_enabled=True,
    )


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


@pytest.mark.parametrize(
    ("intent", "expected_argv_suffix"),
    [
        (
            "focused_pytest",
            ("-m", "pytest", "tests/test_governed_runtime_contracts.py", "-q"),
        ),
        ("repo_verifier", ("scripts/verify_documentation_integrity.py",)),
        ("frontend_check", ("frontend-check",)),
    ],
)
def test_approved_runtime_command_step_executes_through_runtime_gateway(
    tmp_path: Path,
    intent: str,
    expected_argv_suffix: tuple[str, ...],
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=5,
            output_bytes=b"redacted staged orchestration output marker",
        )

    store = RuntimeInvocationStore(tmp_path)
    request = _approved_runtime_command_request(intent=intent)
    approved = _approve_runtime_command(store, request)
    approved_request = request.model_copy(
        update={"approval_ref": approved.action_inbox_envelope.approval_ref}
    )
    plan = _runtime_command_plan(approved)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = execute_approved_runtime_command_step(
        plan,
        step_ref="step-ref:staged-orchestration:runtime-command",
        gateway=gateway,
        command_request=approved_request,
        execute_request=_execute_request_for(approved),
        idempotency_ref=f"idempotency-ref:staged-orchestration-runtime-execute-{intent}",
    )
    read_model = build_staged_orchestration_read_model(plan)

    assert result.status == StagedOrchestrationStatus.completed.value
    assert result.command_intent == intent
    assert result.execution_performed is True
    assert result.command_execution_performed is True
    assert result.output_summary_returned is True
    assert result.output_persisted is False
    assert result.raw_payloads_persisted is False
    assert result.receipt_ref is not None
    assert len(calls) == 1
    observed_argv = calls[0]["argv"]
    assert isinstance(observed_argv, tuple)
    assert observed_argv[-len(expected_argv_suffix) :] == expected_argv_suffix
    assert read_model.approved_runtime_command_execution_enabled is True
    assert read_model.execution_performed is False
    assert read_model.runtime_execution_performed_by_read_model is False

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "redacted staged orchestration output marker" not in persisted


def test_runtime_command_step_rejects_unpromoted_intent(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    request = _approved_runtime_command_request()
    approved = _approve_runtime_command(store, request)
    payload = _runtime_command_plan(approved).model_dump(mode="json")
    payload["steps"][0]["runtime_command_binding"]["command_intent"] = "git_status"

    with pytest.raises(ValidationError):
        StagedOrchestrationPlan(**payload)


def test_runtime_command_step_without_plan_enablement_is_rejected(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    request = _approved_runtime_command_request()
    approved = _approve_runtime_command(store, request)
    payload = _runtime_command_plan(approved).model_dump(mode="json")
    payload["approved_runtime_command_execution_enabled"] = False

    with pytest.raises(ValidationError):
        StagedOrchestrationPlan(**payload)


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
