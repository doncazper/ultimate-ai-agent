import pytest

from tests.test_m90_shell_subprocess_hardening_freeze import _request as _m90_request
from ultimate_ai_agent.core.sandbox import build_shell_subprocess_hardening_freeze
from ultimate_ai_agent.core.tools import (
    AutonomousToolExecutionContractPolicy,
    AutonomousToolExecutionContractRequest,
    AutonomousToolExecutionContractStatus,
    build_autonomous_tool_execution_contract,
    validate_autonomous_tool_execution_contract_decision,
    validate_autonomous_tool_execution_contract_policy,
    validate_autonomous_tool_execution_contract_request,
)


def _m90_decision():
    return build_shell_subprocess_hardening_freeze(_m90_request())


def _request(**overrides):
    m90_decision = overrides.pop("shell_subprocess_hardening_freeze_decision", _m90_decision())
    data = {
        "request_ref": "autonomous-tool-execution-contract-request:m91",
        "contract_ref": "autonomous-tool-execution-contract:m91",
        "shell_subprocess_hardening_freeze_decision_ref": m90_decision.decision_ref,
        "emergency_stop_process_kill_safety_decision_ref": (
            m90_decision.emergency_stop_process_kill_safety_decision_ref
        ),
        "command_ref": m90_decision.command_ref,
        "sandbox_spec_ref": m90_decision.sandbox_spec_ref,
        "approval_bundle_ref": m90_decision.approval_bundle_ref,
        "approval_ref": m90_decision.approval_ref,
        "actor_ref": m90_decision.actor_ref,
        "audit_ref": m90_decision.audit_ref,
        "replay_ref": m90_decision.replay_ref,
        "tool_intent_ref": "tool-intent:m91-review-only",
        "tool_runtime_ref": "tool-runtime:m91-contract-only",
        "capability_ref": "capability:m91-autonomous-tool-contract",
        "autonomy_session_ref": "autonomy-session:m91-not-started",
        "safe_execution_scope_ref": "execution-scope:m91-safe-review-only",
        "safe_tool_ref": "tool:m91-review-only-contract",
        "safe_contract_summary": (
            "Define autonomous tool execution contract requirements without enabling execution."
        ),
        "safe_contract_refs": ["contract-ref:m91-no-real-tool-execution"],
        "prior_milestone_refs": [
            "milestone:M53",
            "milestone:M61",
            "milestone:M62",
            "milestone:M63",
            "milestone:M66",
            "milestone:M67",
            "milestone:M68",
            "milestone:M70",
            "milestone:M80",
            "milestone:M90",
        ],
        "shell_subprocess_hardening_freeze_decision": m90_decision,
    }
    data.update(overrides)
    return AutonomousToolExecutionContractRequest(**data)


def test_m91_autonomous_tool_execution_contract_is_review_only() -> None:
    decision = build_autonomous_tool_execution_contract(_request())

    assert decision.status == AutonomousToolExecutionContractStatus.contract_ready_for_review
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.m90_hardening_freeze_revalidated is True
    assert decision.autonomous_tool_execution_contract_defined is True
    assert decision.execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.autonomous_execution_authorized is False
    assert decision.session_start_authorized is False
    assert decision.background_worker_started is False
    assert decision.execution_performed is False
    assert decision.tool_execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_tool_payload is False
    assert decision.receipt_plan.store_raw_provider_payload is False
    assert decision.reason_codes == [
        "M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_REVIEW_ONLY",
        "M91_EXACT_M90_HARDENING_BINDING_REQUIRED",
        "M91_NO_REAL_TOOL_EXECUTION",
        "M91_NO_AUTONOMOUS_SESSION_START",
        "M92_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("autonomous_execution_requested", "AUTONOMOUS_EXECUTION_DENIED"),
        ("session_start_requested", "SESSION_START_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
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
        ("contains_raw_tool_payload", "M91_RAW_TOOL_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M91_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_secret", "SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED"),
    ],
)
def test_m91_denies_execution_authority_and_raw_fields(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomous_tool_execution_contract_request(_request(**{field: True}))


def test_m91_requires_exact_m90_binding() -> None:
    for update, reason in [
        (
            {"shell_subprocess_hardening_freeze_decision_ref": "shell-subprocess-hardening-freeze-decision:other"},
            "M91_M90_HARDENING_BINDING_MISMATCH",
        ),
        ({"command_ref": "command-ref:other"}, "M91_COMMAND_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M91_ACTOR_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m91"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_autonomous_tool_execution_contract(_request(**update))


def test_m91_revalidates_model_copy_mutated_m90_decision() -> None:
    m90_decision = _m90_decision()
    with pytest.raises(ValueError, match="TOOL_EXECUTION_DENIED"):
        build_autonomous_tool_execution_contract(
            _request(
                shell_subprocess_hardening_freeze_decision=m90_decision.model_copy(
                    update={"tool_execution_performed": True}
                )
            )
        )


def test_m91_revalidates_decision_and_receipt_flags() -> None:
    decision = build_autonomous_tool_execution_contract(_request())
    for update, reason in [
        ({"execution_authorized": True}, "EXECUTION_DENIED"),
        ({"tool_execution_authorized": True}, "TOOL_EXECUTION_DENIED"),
        ({"autonomous_execution_authorized": True}, "AUTONOMOUS_EXECUTION_DENIED"),
        ({"session_start_authorized": True}, "SESSION_START_DENIED"),
        ({"background_worker_started": True}, "BACKGROUND_WORKER_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_autonomous_tool_execution_contract_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M91_RAW_TOOL_PAYLOAD_DENIED"):
        validate_autonomous_tool_execution_contract_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_tool_payload": True}
                    )
                }
            )
        )


def test_m91_policy_denies_execution_and_authority_flags() -> None:
    for field, reason in [
        ("autonomous_tool_execution_enabled", "AUTONOMOUS_EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("session_start_enabled", "SESSION_START_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_autonomous_tool_execution_contract_policy(
                AutonomousToolExecutionContractPolicy(**{field: True})
            )
