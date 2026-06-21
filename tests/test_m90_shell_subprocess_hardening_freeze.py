from typing import Any
import pytest

from tests.test_m89_emergency_stop_process_kill_safety import _request as _m89_request
from ultimate_ai_agent.core.sandbox import (
    ShellSubprocessHardeningFreezePolicy,
    ShellSubprocessHardeningFreezeRequest,
    ShellSubprocessHardeningFreezeStatus,
    build_emergency_stop_process_kill_safety,
    build_shell_subprocess_hardening_freeze,
    validate_shell_subprocess_hardening_freeze_decision,
    validate_shell_subprocess_hardening_freeze_policy,
    validate_shell_subprocess_hardening_freeze_request,
)


def _m89_decision() -> Any:
    return build_emergency_stop_process_kill_safety(_m89_request())


def _request(**overrides: Any) -> Any:
    m89_decision = overrides.pop("emergency_stop_process_kill_safety_decision", _m89_decision())
    data = {
        "request_ref": "shell-subprocess-hardening-freeze-request:m90",
        "hardening_freeze_ref": "shell-subprocess-hardening-freeze:m90",
        "emergency_stop_process_kill_safety_decision_ref": m89_decision.decision_ref,
        "mutating_command_proposal_decision_ref": m89_decision.mutating_command_proposal_decision_ref,
        "sandboxed_command_audit_replay_decision_ref": m89_decision.sandboxed_command_audit_replay_decision_ref,
        "shell_approval_gate_decision_ref": m89_decision.shell_approval_gate_decision_ref,
        "approval_bundle_ref": m89_decision.approval_bundle_ref,
        "approval_ref": m89_decision.approval_ref,
        "command_ref": m89_decision.command_ref,
        "sandbox_spec_ref": m89_decision.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.93.0",
        "actor_ref": m89_decision.actor_ref,
        "audit_ref": m89_decision.audit_ref,
        "replay_ref": m89_decision.replay_ref,
        "mutation_intent_ref": m89_decision.mutation_intent_ref,
        "mutation_scope_ref": m89_decision.mutation_scope_ref,
        "safe_target_process_ref": m89_decision.safe_target_process_ref,
        "safe_emergency_scope_ref": m89_decision.safe_emergency_scope_ref,
        "safe_freeze_summary": "Freeze shell, subprocess, process, and emergency boundaries as review-only metadata.",
        "safe_hardening_refs": ["hardening-ref:m90-shell-subprocess-freeze"],
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
            "milestone:M87",
            "milestone:M88",
            "milestone:M89",
        ],
        "emergency_stop_process_kill_safety_decision": m89_decision,
    }
    data.update(overrides)
    return ShellSubprocessHardeningFreezeRequest(**data)


def test_m90_shell_subprocess_hardening_freeze_is_review_only() -> None:
    decision = build_shell_subprocess_hardening_freeze(_request())

    assert decision.status == ShellSubprocessHardeningFreezeStatus.frozen_for_review
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.freeze_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.m89_safety_decision_revalidated is True
    assert decision.shell_boundary_frozen is True
    assert decision.subprocess_boundary_frozen is True
    assert decision.process_spawn_boundary_frozen is True
    assert decision.emergency_stop_boundary_frozen is True
    assert decision.command_execution_authorized is False
    assert decision.shell_execution_authorized is False
    assert decision.subprocess_execution_authorized is False
    assert decision.process_spawn_authorized is False
    assert decision.emergency_stop_authorized is False
    assert decision.process_kill_authorized is False
    assert decision.process_signal_authorized is False
    assert decision.command_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.subprocess_execution_performed is False
    assert decision.process_spawn_performed is False
    assert decision.emergency_stop_performed is False
    assert decision.process_kill_performed is False
    assert decision.process_signal_performed is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_shell_string is False
    assert decision.receipt_plan.store_raw_pid is False
    assert decision.reason_codes == [
        "M90_SHELL_SUBPROCESS_HARDENING_FREEZE_REVIEW_ONLY",
        "M90_EXACT_M89_SAFETY_BINDING_REQUIRED",
        "M90_NO_SHELL_SUBPROCESS_EXECUTION",
        "M90_NO_PROCESS_OR_EMERGENCY_EXECUTION",
        "M91_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("emergency_stop_requested", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
        ("process_kill_requested", "M90_PROCESS_KILL_DENIED"),
        ("process_signal_requested", "M90_PROCESS_SIGNAL_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_shell_string", "M90_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M90_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M90_RAW_OUTPUT_DENIED"),
        ("contains_pid", "M90_RAW_PID_DENIED"),
        ("contains_raw_signal", "M90_RAW_SIGNAL_DENIED"),
        ("contains_secret", "SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED"),
    ],
)
def test_m90_denies_execution_and_raw_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_shell_subprocess_hardening_freeze_request(_request(**{field: True}))


def test_m90_requires_exact_m89_binding() -> None:
    for update, reason in [
        (
            {"emergency_stop_process_kill_safety_decision_ref": "emergency-stop-process-kill-safety-decision:other"},
            "M90_M89_SAFETY_BINDING_MISMATCH",
        ),
        ({"command_ref": "command-ref:other"}, "M90_COMMAND_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M90_ACTOR_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m90"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_shell_subprocess_hardening_freeze(_request(**update))


def test_m90_revalidates_model_copy_mutated_m89_decision() -> None:
    m89_decision = _m89_decision()
    with pytest.raises(ValueError, match="M89_PROCESS_KILL_DENIED"):
        build_shell_subprocess_hardening_freeze(
            _request(
                emergency_stop_process_kill_safety_decision=m89_decision.model_copy(
                    update={"process_kill_authorized": True}
                )
            )
        )


def test_m90_revalidates_decision_and_receipt_flags() -> None:
    decision = build_shell_subprocess_hardening_freeze(_request())
    for update, reason in [
        ({"command_execution_authorized": True}, "COMMAND_EXECUTION_DENIED"),
        ({"shell_execution_authorized": True}, "SHELL_EXECUTION_DENIED"),
        ({"subprocess_execution_performed": True}, "SUBPROCESS_EXECUTION_DENIED"),
        ({"process_spawn_authorized": True}, "PROCESS_SPAWN_DENIED"),
        ({"emergency_stop_authorized": True}, "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
        ({"process_kill_performed": True}, "M90_PROCESS_KILL_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_shell_subprocess_hardening_freeze_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M90_SHELL_STRING_DENIED"):
        validate_shell_subprocess_hardening_freeze_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_shell_string": True}
                    )
                }
            )
        )


def test_m90_policy_denies_execution_and_authority_flags() -> None:
    for field, reason in [
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
        ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
        ("emergency_stop_execution_enabled", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
        ("process_kill_enabled", "M90_PROCESS_KILL_DENIED"),
        ("process_signal_enabled", "M90_PROCESS_SIGNAL_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_shell_subprocess_hardening_freeze_policy(
                ShellSubprocessHardeningFreezePolicy(**{field: True})
            )


def test_m90_docs_and_next_milestone_boundary_are_exposed() -> None:
    decision = build_shell_subprocess_hardening_freeze(_request())

    assert "M91_REMAINS_FUTURE" in decision.reason_codes
    assert "M90_NO_SHELL_SUBPROCESS_EXECUTION" in decision.reason_codes
    assert "shell" in decision.safe_summary.lower()
    assert "subprocess" in decision.safe_summary.lower()
