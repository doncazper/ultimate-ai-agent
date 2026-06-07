import pytest

from tests.test_m86_shell_approval_gate import _request as _m86_request
from ultimate_ai_agent.core.sandbox import (
    SandboxedCommandAuditReplayPolicy,
    SandboxedCommandAuditReplayRequest,
    SandboxedCommandAuditReplayStatus,
    SandboxedCommandAuditReplayStep,
    build_sandboxed_command_audit_replay,
    build_shell_approval_gate_decision,
    validate_sandboxed_command_audit_replay_decision,
    validate_sandboxed_command_audit_replay_policy,
    validate_sandboxed_command_audit_replay_request,
)


def _m86_decision():
    return build_shell_approval_gate_decision(_m86_request())


def _step(step_ref: str = "sandboxed-command-audit-replay-step:m87-gate") -> SandboxedCommandAuditReplayStep:
    gate = _m86_decision()
    return SandboxedCommandAuditReplayStep(
        step_ref=step_ref,
        event_ref="audit-event:m87-shell-gate-reviewed",
        source_decision_ref=gate.decision_ref,
        safe_summary="Replay view records the M86 shell approval gate review decision only.",
        reason_codes=["M87_REPLAY_VIEW_STEP_ONLY", "M87_NO_COMMAND_EXECUTION"],
    )


def _request(**overrides):
    gate = overrides.pop("shell_approval_gate_decision", _m86_decision())
    replay_steps = overrides.pop("replay_steps", [_step()])
    data = {
        "request_ref": "sandboxed-command-audit-replay-request:m87",
        "replay_view_ref": "sandboxed-command-audit-replay:m87",
        "shell_approval_gate_decision_ref": gate.decision_ref,
        "read_only_command_allowlist_decision_ref": gate.read_only_command_allowlist_decision_ref,
        "approval_bundle_ref": gate.approval_bundle_ref,
        "approval_ref": gate.approval_ref,
        "allowlist_ref": gate.allowlist_ref,
        "command_ref": gate.command_ref,
        "sandbox_spec_ref": gate.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.90.0",
        "actor_ref": gate.actor_ref,
        "audit_ref": "audit:m86-shell-gate",
        "replay_ref": "replay:m86-shell-gate",
        "replay_step_refs": [step.step_ref for step in replay_steps],
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
            "milestone:M84",
            "milestone:M85",
            "milestone:M86",
        ],
        "shell_approval_gate_decision": gate,
        "replay_steps": replay_steps,
        "safe_purpose": "Review a sandboxed command audit replay without running or retrying commands.",
    }
    data.update(overrides)
    return SandboxedCommandAuditReplayRequest(**data)


def test_m87_sandboxed_command_audit_replay_is_replay_view_only() -> None:
    decision = build_sandboxed_command_audit_replay(_request())

    assert decision.status == SandboxedCommandAuditReplayStatus.ready_for_review
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.replay_view_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.shell_approval_gate_decision_revalidated is True
    assert decision.replay_steps_bound is True
    assert decision.command_execution_authorized is False
    assert decision.command_execution_performed is False
    assert decision.shell_execution_authorized is False
    assert decision.shell_execution_performed is False
    assert decision.subprocess_execution_authorized is False
    assert decision.subprocess_execution_performed is False
    assert decision.process_spawn_authorized is False
    assert decision.process_spawn_performed is False
    assert decision.replay_runner_started is False
    assert decision.replay_execution_performed is False
    assert decision.filesystem_mutation_performed is False
    assert decision.network_access_performed is False
    assert decision.tool_execution_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.remote_execution_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_raw_output is False
    assert decision.reason_codes == [
        "M87_SANDBOXED_COMMAND_AUDIT_REPLAY_VIEW_ONLY",
        "M87_EXACT_M86_SHELL_APPROVAL_GATE_BINDING_REQUIRED",
        "M87_SAFE_REPLAY_STEPS_ONLY",
        "M87_NO_REPLAY_RUNNER",
        "M88_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("replay_execution_requested", "M87_REPLAY_EXECUTION_DENIED"),
        ("replay_runner_requested", "M87_REPLAY_RUNNER_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_shell_string", "M87_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M87_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M87_RAW_OUTPUT_DENIED"),
        ("contains_secret", "SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED"),
    ],
)
def test_m87_sandboxed_command_audit_replay_denies_execution_and_raw_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_sandboxed_command_audit_replay_request(_request(**{field: True}))


def test_m87_requires_exact_m86_shell_approval_gate_binding() -> None:
    for update, reason in [
        ({"shell_approval_gate_decision_ref": "shell-approval-gate-decision:other"}, "M87_M86_GATE_DECISION_BINDING_MISMATCH"),
        ({"command_ref": "command-ref:other"}, "M87_COMMAND_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M87_ACTOR_BINDING_MISMATCH"),
        ({"sandbox_spec_ref": "runtime-sandbox-spec:other"}, "M87_SANDBOX_SPEC_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m87"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_sandboxed_command_audit_replay(_request(**update))


def test_m87_requires_exact_replay_step_refs() -> None:
    with pytest.raises(ValueError, match="M87_REPLAY_STEP_REF_BINDING_MISMATCH"):
        build_sandboxed_command_audit_replay(
            _request(replay_step_refs=["sandboxed-command-audit-replay-step:other"])
        )

    step = _step()
    with pytest.raises(ValueError, match="M87_REPLAY_STEP_REF_DUPLICATE"):
        build_sandboxed_command_audit_replay(_request(replay_steps=[step, step]))


def test_m87_revalidates_model_copy_mutated_m86_gate_decision() -> None:
    gate = _m86_decision()
    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_sandboxed_command_audit_replay(
            _request(
                shell_approval_gate_decision=gate.model_copy(
                    update={"shell_execution_authorized": True}
                )
            )
        )


def test_m87_revalidates_replay_step_and_decision_receipt_flags() -> None:
    with pytest.raises(ValueError, match="M87_RAW_OUTPUT_DENIED"):
        build_sandboxed_command_audit_replay(
            _request(replay_steps=[_step().model_copy(update={"contains_raw_output": True})])
        )

    decision = build_sandboxed_command_audit_replay(_request())
    for update, reason in [
        ({"replay_runner_started": True}, "M87_REPLAY_RUNNER_DENIED"),
        ({"replay_execution_performed": True}, "M87_REPLAY_EXECUTION_DENIED"),
        ({"shell_execution_performed": True}, "SHELL_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_sandboxed_command_audit_replay_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M87_RAW_COMMAND_DENIED"):
        validate_sandboxed_command_audit_replay_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_command": True}
                    )
                }
            )
        )


def test_m87_policy_denies_runner_and_authority_flags() -> None:
    for field, reason in [
        ("replay_runner_enabled", "M87_REPLAY_RUNNER_DENIED"),
        ("replay_execution_enabled", "M87_REPLAY_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_sandboxed_command_audit_replay_policy(
                SandboxedCommandAuditReplayPolicy(**{field: True})
            )
