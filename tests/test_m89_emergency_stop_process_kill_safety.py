from typing import Any
import pytest

from tests.test_m88_mutating_command_proposal import _request as _m88_request
from ultimate_ai_agent.core.sandbox import (
    EmergencyStopProcessKillSafetyPolicy,
    EmergencyStopProcessKillSafetyRequest,
    EmergencyStopProcessKillSafetyStatus,
    build_emergency_stop_process_kill_safety,
    build_mutating_command_proposal,
    validate_emergency_stop_process_kill_safety_decision,
    validate_emergency_stop_process_kill_safety_policy,
    validate_emergency_stop_process_kill_safety_request,
)


def _m88_decision() -> Any:
    return build_mutating_command_proposal(_m88_request())


def _request(**overrides: Any) -> Any:
    proposal = overrides.pop("mutating_command_proposal_decision", _m88_decision())
    data = {
        "request_ref": "emergency-stop-process-kill-safety-request:m89",
        "emergency_stop_safety_ref": "emergency-stop-safety:m89",
        "process_kill_safety_ref": "process-kill-safety:m89",
        "mutating_command_proposal_decision_ref": proposal.decision_ref,
        "sandboxed_command_audit_replay_decision_ref": proposal.sandboxed_command_audit_replay_decision_ref,
        "shell_approval_gate_decision_ref": proposal.shell_approval_gate_decision_ref,
        "approval_bundle_ref": proposal.approval_bundle_ref,
        "approval_ref": proposal.approval_ref,
        "command_ref": proposal.command_ref,
        "sandbox_spec_ref": proposal.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.92.0",
        "actor_ref": proposal.actor_ref,
        "audit_ref": proposal.audit_ref,
        "replay_ref": proposal.replay_ref,
        "mutation_intent_ref": proposal.mutation_intent_ref,
        "mutation_scope_ref": proposal.mutation_scope_ref,
        "safe_target_process_ref": "process-target-ref:m89-safe-ref",
        "safe_emergency_scope_ref": "emergency-scope-ref:m89-safe-ref",
        "safe_stop_summary": "Review emergency stop and process kill safety as safe metadata only.",
        "safe_reason_refs": ["safety-reason-ref:m89-review-only"],
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
        ],
        "mutating_command_proposal_decision": proposal,
    }
    data.update(overrides)
    return EmergencyStopProcessKillSafetyRequest(**data)


def test_m89_emergency_stop_process_kill_safety_is_review_only() -> None:
    decision = build_emergency_stop_process_kill_safety(_request())

    assert decision.status == EmergencyStopProcessKillSafetyStatus.reviewed_for_safety
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.mutating_command_proposal_decision_revalidated is True
    assert decision.process_target_ref_bound is True
    assert decision.emergency_scope_ref_bound is True
    assert decision.emergency_stop_authorized is False
    assert decision.emergency_stop_performed is False
    assert decision.process_kill_authorized is False
    assert decision.process_kill_performed is False
    assert decision.process_signal_authorized is False
    assert decision.process_signal_performed is False
    assert decision.command_execution_performed is False
    assert decision.subprocess_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.process_spawn_performed is False
    assert decision.filesystem_mutation_performed is False
    assert decision.network_access_performed is False
    assert decision.tool_execution_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.remote_execution_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.background_worker_started is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_process_target_ref_only is True
    assert decision.receipt_plan.store_raw_pid is False
    assert decision.receipt_plan.store_raw_signal is False
    assert decision.reason_codes == [
        "M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_REVIEW_ONLY",
        "M89_EXACT_M88_MUTATING_PROPOSAL_BINDING_REQUIRED",
        "M89_SAFE_PROCESS_TARGET_REF_REQUIRED",
        "M89_NO_PROCESS_KILL_EXECUTION",
        "M90_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("emergency_stop_requested", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
        ("process_kill_requested", "M89_PROCESS_KILL_DENIED"),
        ("process_signal_requested", "M89_PROCESS_SIGNAL_DENIED"),
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
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
        ("contains_pid", "M89_RAW_PID_DENIED"),
        ("contains_raw_signal", "M89_RAW_SIGNAL_DENIED"),
        ("contains_shell_string", "M89_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M89_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M89_RAW_OUTPUT_DENIED"),
        ("contains_secret", "SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED"),
    ],
)
def test_m89_denies_process_kill_execution_and_raw_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_emergency_stop_process_kill_safety_request(_request(**{field: True}))


def test_m89_requires_exact_m88_binding() -> None:
    for update, reason in [
        (
            {"mutating_command_proposal_decision_ref": "mutating-command-proposal-decision:other"},
            "M89_M88_MUTATING_PROPOSAL_BINDING_MISMATCH",
        ),
        ({"command_ref": "command-ref:other"}, "M89_COMMAND_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M89_ACTOR_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m89"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_emergency_stop_process_kill_safety(_request(**update))


def test_m89_requires_safe_target_scope_and_reason_refs() -> None:
    for update, reason in [
        ({"safe_target_process_ref": "process-target-ref:other"}, "M89_PROCESS_TARGET_BINDING_MISMATCH"),
        ({"safe_emergency_scope_ref": "emergency-scope-ref:other"}, "M89_EMERGENCY_SCOPE_BINDING_MISMATCH"),
        ({"safe_reason_refs": []}, "M89_SAFE_REASON_REFS_REQUIRED"),
        (
            {"safe_reason_refs": ["safety-reason-ref:m89-review-only", "safety-reason-ref:m89-review-only"]},
            "M89_SAFE_REASON_REF_DUPLICATE",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_emergency_stop_process_kill_safety(_request(**update))


def test_m89_revalidates_model_copy_mutated_m88_decision() -> None:
    proposal = _m88_decision()
    with pytest.raises(ValueError, match="FILESYSTEM_MUTATION_DENIED"):
        build_emergency_stop_process_kill_safety(
            _request(
                mutating_command_proposal_decision=proposal.model_copy(
                    update={"filesystem_mutation_authorized": True}
                )
            )
        )


def test_m89_revalidates_decision_and_receipt_flags() -> None:
    decision = build_emergency_stop_process_kill_safety(_request())
    for update, reason in [
        ({"emergency_stop_authorized": True}, "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
        ({"process_kill_authorized": True}, "M89_PROCESS_KILL_DENIED"),
        ({"process_kill_performed": True}, "M89_PROCESS_KILL_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_emergency_stop_process_kill_safety_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M89_RAW_PID_DENIED"):
        validate_emergency_stop_process_kill_safety_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_pid": True}
                    )
                }
            )
        )


def test_m89_policy_denies_execution_kill_and_authority_flags() -> None:
    for field, reason in [
        ("emergency_stop_execution_enabled", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
        ("process_kill_enabled", "M89_PROCESS_KILL_DENIED"),
        ("process_signal_enabled", "M89_PROCESS_SIGNAL_DENIED"),
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_emergency_stop_process_kill_safety_policy(
                EmergencyStopProcessKillSafetyPolicy(**{field: True})
            )
