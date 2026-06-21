from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    ErrorHandlingGuardrailDecision,
    ErrorHandlingGuardrailPolicy,
    ErrorHandlingGuardrailRequest,
    ErrorHandlingGuardrailStatus,
    build_error_handling_guardrail_decision,
    validate_error_handling_guardrail_decision,
    validate_error_handling_guardrail_policy,
    validate_error_handling_guardrail_request,
)
from ultimate_ai_agent.core.autonomy.error_handling_guardrails import (
    ERROR_HANDLING_GUARDRAILS_DOCS,
    M138_MAX_ERROR_SIGNAL_REFS,
)


def _request(**updates: Any) -> ErrorHandlingGuardrailRequest:
    payload = {
        "request_ref": "error-handling-guardrail-request:test",
        "guardrail_plan_ref": "error-handling-guardrail-plan:test",
        "mode_ref": "autonomy-mode:trusted-recurring-automation",
        "actor_ref": "actor:test",
        "user_ref": "user:test",
        "workspace_ref": "workspace:test",
        "scope_ref": "scope:test",
        "resource_refs": ["resource:test"],
        "capability_refs": ["capability:error-guardrail-review"],
        "allowlist_refs": ["allowlist:test"],
        "m137_combined_workflow_decision_ref": (
            "browser-connector-combined-workflow-decision:test"
        ),
        "m136_dependency_execution_decision_ref": (
            "cross-tool-dependency-execution-decision:test"
        ),
        "m135_recovery_planner_decision_ref": "autonomous-recovery-decision:test",
        "m134_human_checkpoint_decision_ref": "human-checkpoint-decision:test",
        "m133_supervisor_decision_ref": "long-running-supervisor-decision:test",
        "m132_trusted_workflow_decision_ref": "trusted-workflow-decision:test",
        "error_signal_refs": ["error-signal:primary"],
        "guardrail_policy_ref": "error-guardrail-policy:test",
        "failure_mode_ref": "failure-mode:transient",
        "retry_policy_ref": "retry-policy:review-only",
        "fallback_policy_ref": "fallback-policy:review-only",
        "escalation_policy_ref": "escalation-policy:human-checkpoint",
        "recovery_plan_ref": "recovery-plan:review-only",
        "rollback_plan_ref": "rollback-plan:review-only",
        "resume_plan_ref": "resume-plan:review-only",
        "human_checkpoint_ref": "human-checkpoint:test",
        "risk_decision_ref": "risk-decision:low",
        "audit_ref": "audit:error-guardrail",
        "replay_ref": "replay:error-guardrail",
        "revocation_ref": "revocation:error-guardrail",
        "kill_switch_ref": "kill-switch:error-guardrail",
        "no_effect_receipt_plan_ref": "receipt-plan:error-guardrail",
        "max_error_signals": M138_MAX_ERROR_SIGNAL_REFS,
        "max_guardrail_refs": 8,
        "safe_guardrail_summary": (
            "Review-only error handling guardrails for a low-risk scoped workflow."
        ),
    }
    payload.update(updates)
    return ErrorHandlingGuardrailRequest(**payload)


def test_m138_docs_are_registered() -> None:
    assert "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS.md" in (
        ERROR_HANDLING_GUARDRAILS_DOCS
    )
    assert "docs/autonomy/M138_TO_M139_BOUNDARY.md" in ERROR_HANDLING_GUARDRAILS_DOCS


def test_m138_builds_review_only_guardrail_decision() -> None:
    decision = build_error_handling_guardrail_decision(_request())

    assert decision.status == ErrorHandlingGuardrailStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.autonomous_error_handling_guardrails_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m137_browser_connector_workflow_bound is True
    assert decision.m136_dependency_execution_bound is True
    assert decision.m135_recovery_planner_bound is True
    assert decision.error_signal_bound is True
    assert decision.guardrail_policy_bound is True
    assert decision.retry_policy_bound is True
    assert decision.fallback_policy_bound is True
    assert decision.escalation_policy_bound is True
    assert decision.recovery_plan_bound is True
    assert decision.rollback_plan_bound is True
    assert decision.resume_plan_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.error_handling_runtime_authorized is False
    assert decision.error_guardrail_runtime_started is False
    assert decision.autonomous_recovery_execution_authorized is False
    assert decision.retry_execution_authorized is False
    assert decision.retry_execution_performed is False
    assert decision.rollback_execution_performed is False
    assert decision.resume_execution_performed is False
    assert decision.dependency_execution_performed is False
    assert decision.browser_action_performed is False
    assert decision.connector_action_performed is False
    assert decision.tool_execution_performed is False
    assert decision.execution_performed is False
    assert decision.backend_route_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_raw_error_log is False
    assert decision.receipt_plan.store_raw_stack_trace is False
    assert decision.receipt_plan.retry_execution_performed is False
    assert "M138_AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_CONTRACT_ONLY" in (
        decision.reason_codes
    )
    assert "M139_REMAINS_FUTURE" in decision.reason_codes

    assert validate_error_handling_guardrail_decision(decision) == decision


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"mode5_runtime_enabled": True}, "M138_MODE5_RUNTIME_DENIED"),
        (
            {"error_handling_runtime_enabled": True},
            "M138_ERROR_HANDLING_RUNTIME_DENIED",
        ),
        (
            {"error_guardrail_runtime_enabled": True},
            "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
        ),
        (
            {"autonomous_recovery_execution_enabled": True},
            "M138_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_enabled": True}, "M138_RETRY_EXECUTION_DENIED"),
        ({"resume_execution_enabled": True}, "M138_RESUME_EXECUTION_DENIED"),
        ({"rollback_execution_enabled": True}, "M138_ROLLBACK_EXECUTION_DENIED"),
        ({"fallback_action_enabled": True}, "M138_FALLBACK_ACTION_DENIED"),
        ({"escalation_action_enabled": True}, "M138_ESCALATION_ACTION_DENIED"),
        ({"loop_recovery_enabled": True}, "M138_LOOP_RECOVERY_DENIED"),
        ({"dependency_execution_enabled": True}, "M138_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_enabled": True}, "M138_BROWSER_ACTION_DENIED"),
        ({"connector_action_enabled": True}, "M138_CONNECTOR_ACTION_DENIED"),
        ({"connector_write_enabled": True}, "M138_CONNECTOR_WRITE_DENIED"),
        ({"account_auth_enabled": True}, "M138_ACCOUNT_AUTH_DENIED"),
        ({"tool_execution_enabled": True}, "M138_TOOL_EXECUTION_DENIED"),
        ({"execution_enabled": True}, "M138_EXECUTION_DENIED"),
        ({"shell_execution_enabled": True}, "M138_SHELL_EXECUTION_DENIED"),
        ({"network_access_enabled": True}, "M138_NETWORK_ACCESS_DENIED"),
        ({"plugin_execution_enabled": True}, "M138_PLUGIN_EXECUTION_DENIED"),
        ({"model_call_enabled": True}, "M138_MODEL_CALL_DENIED"),
        ({"memory_write_enabled": True}, "M138_MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "M138_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_enabled": True}, "M138_BACKEND_ROUTE_DENIED"),
        (
            {"control_center_control_enabled": True},
            "M138_CONTROL_CENTER_CONTROL_DENIED",
        ),
        ({"dependency_added": True}, "M138_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M138_BETA_RELEASE_DENIED"),
        (
            {"production_authority_granted": True},
            "M138_PRODUCTION_AUTHORITY_DENIED",
        ),
    ],
)
def test_m138_policy_denies_runtime_authority(update: Any, reason: str) -> None:
    policy = ErrorHandlingGuardrailPolicy().model_copy(update=update)

    with pytest.raises(ValueError, match=reason):
        validate_error_handling_guardrail_policy(policy)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"error_handling_runtime_requested": True},
            "M138_ERROR_HANDLING_RUNTIME_DENIED",
        ),
        (
            {"error_guardrail_runtime_requested": True},
            "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
        ),
        (
            {"autonomous_recovery_execution_requested": True},
            "M138_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_requested": True}, "M138_RETRY_EXECUTION_DENIED"),
        ({"rollback_execution_requested": True}, "M138_ROLLBACK_EXECUTION_DENIED"),
        ({"dependency_execution_requested": True}, "M138_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_requested": True}, "M138_BROWSER_ACTION_DENIED"),
        ({"connector_action_requested": True}, "M138_CONNECTOR_ACTION_DENIED"),
        ({"tool_execution_requested": True}, "M138_TOOL_EXECUTION_DENIED"),
        ({"execution_requested": True}, "M138_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "M138_NETWORK_ACCESS_DENIED"),
        ({"backend_route_requested": True}, "M138_BACKEND_ROUTE_DENIED"),
        ({"dependency_requested": True}, "M138_DEPENDENCY_DENIED"),
        ({"production_authority_requested": True}, "M138_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_error_log": True}, "M138_RAW_ERROR_LOG_DENIED"),
        ({"contains_raw_stack_trace": True}, "M138_RAW_STACK_TRACE_DENIED"),
        ({"contains_raw_prompt": True}, "M138_RAW_PROMPT_DENIED"),
        (
            {"contains_raw_provider_payload": True},
            "M138_RAW_PROVIDER_PAYLOAD_DENIED",
        ),
        ({"contains_cookie_or_credential": True}, "M138_COOKIE_OR_CREDENTIAL_DENIED"),
        ({"contains_secret": True}, "M138_SECRET_DENIED"),
    ],
)
def test_m138_request_denies_unsafe_inputs(update: Any, reason: str) -> None:
    request = _request().model_copy(update=update)

    with pytest.raises(ValueError, match=reason):
        validate_error_handling_guardrail_request(request)


def test_m138_request_denies_wrong_mode_and_risk() -> None:
    with pytest.raises(ValueError, match="M138_MODE5_REQUIRED"):
        validate_error_handling_guardrail_request(
            _request().model_copy(
                update={
                    "requested_mode": AutonomyAuthorityMode.ask_before_every_action
                }
            )
        )

    with pytest.raises(ValueError, match="M138_RISK_CEILING_DENIED"):
        validate_error_handling_guardrail_request(
            _request().model_copy(update={"max_risk_class": AutonomyRiskClass.medium})
        )


def test_m138_request_denies_error_signal_overflow() -> None:
    request = _request().model_copy(
        update={
            "error_signal_refs": [
                f"error-signal:{index}"
                for index in range(M138_MAX_ERROR_SIGNAL_REFS + 1)
            ]
        }
    )

    with pytest.raises(ValueError, match="M138_ERROR_SIGNAL_REF_REQUIRED"):
        validate_error_handling_guardrail_request(request)


def test_m138_request_denies_side_effects_and_secret_like_content() -> None:
    with pytest.raises(ValueError, match="M138_SIDE_EFFECTS_DENIED"):
        validate_error_handling_guardrail_request(
            _request().model_copy(update={"side_effects_performed": ["retry-executed"]})
        )

    with pytest.raises(ValueError, match="M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED"):
        validate_error_handling_guardrail_request(
            _request().model_copy(update={"metadata": {"api_key": "secret-value"}})
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"error_handling_runtime_authorized": True},
            "M138_ERROR_HANDLING_RUNTIME_DENIED",
        ),
        (
            {"error_guardrail_runtime_started": True},
            "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
        ),
        (
            {"autonomous_recovery_execution_authorized": True},
            "M138_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_authorized": True}, "M138_RETRY_EXECUTION_DENIED"),
        ({"retry_execution_performed": True}, "M138_RETRY_EXECUTION_DENIED"),
        ({"rollback_execution_performed": True}, "M138_ROLLBACK_EXECUTION_DENIED"),
        ({"resume_execution_performed": True}, "M138_RESUME_EXECUTION_DENIED"),
        ({"fallback_action_performed": True}, "M138_FALLBACK_ACTION_DENIED"),
        ({"escalation_action_performed": True}, "M138_ESCALATION_ACTION_DENIED"),
        ({"dependency_execution_performed": True}, "M138_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_performed": True}, "M138_BROWSER_ACTION_DENIED"),
        ({"connector_action_performed": True}, "M138_CONNECTOR_ACTION_DENIED"),
        ({"connector_write_performed": True}, "M138_CONNECTOR_WRITE_DENIED"),
        ({"tool_execution_performed": True}, "M138_TOOL_EXECUTION_DENIED"),
        ({"execution_performed": True}, "M138_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "M138_BACKEND_ROUTE_DENIED"),
        (
            {"production_authority_granted": True},
            "M138_PRODUCTION_AUTHORITY_DENIED",
        ),
    ],
)
def test_m138_decision_denies_unsafe_mutations(update: Any, reason: str) -> None:
    decision = build_error_handling_guardrail_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_error_handling_guardrail_decision(decision.model_copy(update=update))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"store_raw_error_log": True}, "M138_RAW_ERROR_LOG_DENIED"),
        ({"store_raw_stack_trace": True}, "M138_RAW_STACK_TRACE_DENIED"),
        ({"store_raw_prompt": True}, "M138_RAW_PROMPT_DENIED"),
        ({"store_raw_provider_payload": True}, "M138_RAW_PROVIDER_PAYLOAD_DENIED"),
        ({"store_cookie_or_credential": True}, "M138_COOKIE_OR_CREDENTIAL_DENIED"),
        ({"store_secret": True}, "M138_SECRET_DENIED"),
        ({"retry_execution_performed": True}, "M138_RETRY_EXECUTION_DENIED"),
        ({"rollback_execution_performed": True}, "M138_ROLLBACK_EXECUTION_DENIED"),
        ({"recovery_execution_performed": True}, "M138_RECOVERY_EXECUTION_DENIED"),
        (
            {"error_handling_runtime_started": True},
            "M138_ERROR_HANDLING_RUNTIME_DENIED",
        ),
    ],
)
def test_m138_receipt_plan_denies_raw_and_runtime_mutations(update: Any, reason: str) -> None:
    decision = build_error_handling_guardrail_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_error_handling_guardrail_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(update=update)
                }
            )
        )


def test_m138_decision_requires_contract_reason_code() -> None:
    decision = build_error_handling_guardrail_decision(_request())

    with pytest.raises(ValueError, match="M138_REASON_CODE_REQUIRED"):
        validate_error_handling_guardrail_decision(
            ErrorHandlingGuardrailDecision.model_validate(
                decision.model_dump() | {"reason_codes": ["M139_REMAINS_FUTURE"]}
            )
        )
