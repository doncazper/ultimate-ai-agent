import pytest

from tests.test_m69_low_risk_autonomous_dry_run import _record as _m69_record
from tests.test_m91_autonomous_tool_execution_contract import _request as _m91_request
from ultimate_ai_agent.core.tools import build_autonomous_tool_execution_contract
from ultimate_ai_agent.core.autonomy import (
    LowRiskToolAutonomySingleSessionPolicy,
    LowRiskToolAutonomySingleSessionRequest,
    LowRiskToolAutonomySingleSessionStatus,
    build_low_risk_tool_autonomy_single_session_decision,
    validate_low_risk_tool_autonomy_single_session_decision,
    validate_low_risk_tool_autonomy_single_session_policy,
    validate_low_risk_tool_autonomy_single_session_request,
)


def _m91_decision():
    return build_autonomous_tool_execution_contract(_m91_request())


def _request(**overrides):
    m91_decision = overrides.pop("m91_contract_decision", _m91_decision())
    dry_run_record = overrides.pop("low_risk_dry_run_record", _m69_record())
    data = {
        "request_ref": "low-risk-tool-autonomy-single-session-request:m92",
        "single_session_ref": "autonomy-single-session:m92-review-only",
        "m91_contract_decision_ref": m91_decision.decision_ref,
        "low_risk_dry_run_record_ref": dry_run_record.record_ref,
        "actor_ref": m91_decision.actor_ref,
        "approval_ref": m91_decision.approval_ref,
        "tool_intent_ref": m91_decision.tool_intent_ref,
        "tool_runtime_ref": m91_decision.tool_runtime_ref,
        "capability_ref": m91_decision.capability_ref,
        "safe_tool_ref": m91_decision.safe_tool_ref,
        "safe_execution_scope_ref": m91_decision.safe_execution_scope_ref,
        "audit_ref": m91_decision.audit_ref,
        "replay_ref": m91_decision.replay_ref,
        "safe_session_summary": (
            "Define one low-risk tool autonomy session for human review without execution."
        ),
        "safe_tool_refs": ["tool:m92-low-risk-review-only"],
        "prior_milestone_refs": ["milestone:M69", "milestone:M90", "milestone:M91"],
        "m91_contract_decision": m91_decision,
        "low_risk_dry_run_record": dry_run_record,
    }
    data.update(overrides)
    return LowRiskToolAutonomySingleSessionRequest(**data)


def test_m92_low_risk_tool_autonomy_single_session_is_review_only() -> None:
    decision = build_low_risk_tool_autonomy_single_session_decision(_request())

    assert decision.status == LowRiskToolAutonomySingleSessionStatus.single_session_ready_for_review
    assert decision.review_only is True
    assert decision.low_risk_only is True
    assert decision.single_session_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.m91_contract_revalidated is True
    assert decision.low_risk_dry_run_revalidated is True
    assert decision.single_session_scope_defined is True
    assert decision.execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.autonomous_execution_authorized is False
    assert decision.session_start_authorized is False
    assert decision.background_worker_authorized is False
    assert decision.execution_performed is False
    assert decision.tool_execution_performed is False
    assert decision.session_start_performed is False
    assert decision.background_worker_started is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_tool_payload is False
    assert decision.receipt_plan.execution_performed is False
    assert decision.reason_codes == [
        "M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_REVIEW_ONLY",
        "M92_EXACT_M91_CONTRACT_BINDING_REQUIRED",
        "M92_EXACT_LOW_RISK_DRY_RUN_BINDING_REQUIRED",
        "M92_SINGLE_SESSION_ONLY",
        "M92_NO_REAL_TOOL_EXECUTION",
        "M93_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("autonomous_execution_requested", "AUTONOMOUS_EXECUTION_DENIED"),
        ("session_start_requested", "SESSION_START_DENIED"),
        ("additional_session_requested", "M92_ADDITIONAL_SESSION_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("multi_tool_requested", "M92_MULTI_TOOL_DENIED"),
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
        ("contains_raw_tool_payload", "M92_RAW_TOOL_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M92_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_secret", "SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED"),
    ],
)
def test_m92_denies_execution_authority_and_raw_fields(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_low_risk_tool_autonomy_single_session_request(_request(**{field: True}))


def test_m92_requires_exact_m91_and_low_risk_dry_run_bindings() -> None:
    for update, reason in [
        ({"m91_contract_decision_ref": "autonomous-tool-execution-contract-decision:other"}, "M92_M91_CONTRACT_BINDING_MISMATCH"),
        ({"low_risk_dry_run_record_ref": "low-risk-autonomous-dry-run-record:other"}, "M92_LOW_RISK_DRY_RUN_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M92_ACTOR_BINDING_MISMATCH"),
        ({"tool_intent_ref": "tool-intent:other"}, "M92_TOOL_INTENT_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m92"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_low_risk_tool_autonomy_single_session_decision(_request(**update))


def test_m92_revalidates_model_copy_mutated_bound_inputs() -> None:
    with pytest.raises(ValueError, match="TOOL_EXECUTION_DENIED"):
        build_low_risk_tool_autonomy_single_session_decision(
            _request(
                m91_contract_decision=_m91_decision().model_copy(
                    update={"tool_execution_authorized": True}
                )
            )
        )

    with pytest.raises(ValueError, match="TOOL_EXECUTION_DENIED"):
        build_low_risk_tool_autonomy_single_session_decision(
            _request(
                low_risk_dry_run_record=_m69_record().model_copy(
                    update={"tool_execution_enabled": True}
                )
            )
        )


def test_m92_revalidates_decision_and_receipt_flags() -> None:
    decision = build_low_risk_tool_autonomy_single_session_decision(_request())
    for update, reason in [
        ({"execution_authorized": True}, "EXECUTION_DENIED"),
        ({"tool_execution_authorized": True}, "TOOL_EXECUTION_DENIED"),
        ({"autonomous_execution_authorized": True}, "AUTONOMOUS_EXECUTION_DENIED"),
        ({"session_start_authorized": True}, "SESSION_START_DENIED"),
        ({"background_worker_started": True}, "BACKGROUND_WORKER_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_low_risk_tool_autonomy_single_session_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="M92_RAW_TOOL_PAYLOAD_DENIED"):
        validate_low_risk_tool_autonomy_single_session_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_tool_payload": True}
                    )
                }
            )
        )


def test_m92_policy_denies_execution_and_authority_flags() -> None:
    for field, reason in [
        ("low_risk_tool_autonomy_enabled", "M92_TOOL_AUTONOMY_ENABLEMENT_DENIED"),
        ("real_tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("session_start_enabled", "SESSION_START_DENIED"),
        ("additional_session_enabled", "M92_ADDITIONAL_SESSION_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_low_risk_tool_autonomy_single_session_policy(
                LowRiskToolAutonomySingleSessionPolicy(**{field: True})
            )
