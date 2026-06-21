from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    ABUSE_LOOP_DETECTION_DOCS,
    M139_MAX_SIGNAL_REFS,
    AbuseLoopDetectionDecision,
    AbuseLoopDetectionPolicy,
    AbuseLoopDetectionRequest,
    AbuseLoopDetectionStatus,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    build_abuse_loop_detection_decision,
    validate_abuse_loop_detection_decision,
    validate_abuse_loop_detection_policy,
    validate_abuse_loop_detection_request,
)


def _request(**updates: Any) -> AbuseLoopDetectionRequest:
    payload = {
        "request_ref": "abuse-loop-detection-request:test",
        "detection_plan_ref": "abuse-loop-detection-plan:test",
        "mode_ref": "autonomy-mode:trusted-recurring-automation",
        "actor_ref": "actor:test",
        "user_ref": "user:test",
        "workspace_ref": "workspace:test",
        "scope_ref": "scope:test",
        "resource_refs": ["resource:test"],
        "capability_refs": ["capability:abuse-loop-review"],
        "allowlist_refs": ["allowlist:test"],
        "m138_error_guardrail_decision_ref": "error-handling-guardrail-decision:test",
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
        "abuse_signal_refs": ["abuse-signal:prompt-loop-risk"],
        "loop_signal_refs": ["loop-signal:repeated-plan"],
        "pattern_policy_ref": "abuse-loop-pattern-policy:test",
        "threshold_policy_ref": "abuse-loop-threshold-policy:test",
        "intervention_plan_ref": "loop-intervention-plan:review-only",
        "escalation_plan_ref": "loop-escalation-plan:human-checkpoint",
        "human_checkpoint_ref": "human-checkpoint:test",
        "risk_decision_ref": "risk-decision:low",
        "audit_ref": "audit:abuse-loop",
        "replay_ref": "replay:abuse-loop",
        "revocation_ref": "revocation:abuse-loop",
        "kill_switch_ref": "kill-switch:abuse-loop",
        "no_effect_receipt_plan_ref": "receipt-plan:abuse-loop",
        "max_signal_refs": M139_MAX_SIGNAL_REFS,
        "max_pattern_refs": 8,
        "safe_detection_summary": (
            "Review-only abuse and loop detection refs for a scoped workflow."
        ),
    }
    payload.update(updates)
    return AbuseLoopDetectionRequest(**payload)


def test_m139_docs_are_registered() -> None:
    assert "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION.md" in (
        ABUSE_LOOP_DETECTION_DOCS
    )
    assert "docs/autonomy/M139_TO_M140_BOUNDARY.md" in ABUSE_LOOP_DETECTION_DOCS


def test_m139_builds_review_only_abuse_loop_decision() -> None:
    decision = build_abuse_loop_detection_decision(_request())

    assert decision.status == AbuseLoopDetectionStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.autonomy_abuse_loop_detection_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m138_error_guardrail_bound is True
    assert decision.m137_browser_connector_workflow_bound is True
    assert decision.m136_dependency_execution_bound is True
    assert decision.m135_recovery_planner_bound is True
    assert decision.abuse_signal_bound is True
    assert decision.loop_signal_bound is True
    assert decision.pattern_policy_bound is True
    assert decision.threshold_policy_bound is True
    assert decision.intervention_plan_bound is True
    assert decision.escalation_plan_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.abuse_detection_runtime_authorized is False
    assert decision.loop_detection_runtime_authorized is False
    assert decision.loop_monitor_started is False
    assert decision.detector_runtime_started is False
    assert decision.loop_intervention_performed is False
    assert decision.autonomous_recovery_execution_authorized is False
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
    assert decision.receipt_plan.store_raw_abuse_log is False
    assert decision.receipt_plan.store_raw_loop_trace is False
    assert decision.receipt_plan.detector_runtime_started is False
    assert "M139_AUTONOMY_ABUSE_LOOP_DETECTION_CONTRACT_ONLY" in (
        decision.reason_codes
    )
    assert "M140_REMAINS_FUTURE" in decision.reason_codes

    assert validate_abuse_loop_detection_decision(decision) == decision


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"abuse_detection_runtime_enabled": True},
            "M139_ABUSE_DETECTION_RUNTIME_DENIED",
        ),
        (
            {"loop_detection_runtime_enabled": True},
            "M139_LOOP_DETECTION_RUNTIME_DENIED",
        ),
        ({"loop_monitor_enabled": True}, "M139_LOOP_MONITOR_DENIED"),
        ({"detector_runtime_enabled": True}, "M139_DETECTOR_RUNTIME_DENIED"),
        ({"loop_intervention_enabled": True}, "M139_LOOP_INTERVENTION_DENIED"),
        (
            {"autonomous_recovery_execution_enabled": True},
            "M139_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_enabled": True}, "M139_RETRY_EXECUTION_DENIED"),
        ({"rollback_execution_enabled": True}, "M139_ROLLBACK_EXECUTION_DENIED"),
        ({"dependency_execution_enabled": True}, "M139_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_enabled": True}, "M139_BROWSER_ACTION_DENIED"),
        ({"connector_action_enabled": True}, "M139_CONNECTOR_ACTION_DENIED"),
        ({"tool_execution_enabled": True}, "M139_TOOL_EXECUTION_DENIED"),
        ({"execution_enabled": True}, "M139_EXECUTION_DENIED"),
        ({"shell_execution_enabled": True}, "M139_SHELL_EXECUTION_DENIED"),
        ({"network_access_enabled": True}, "M139_NETWORK_ACCESS_DENIED"),
        ({"plugin_execution_enabled": True}, "M139_PLUGIN_EXECUTION_DENIED"),
        ({"model_call_enabled": True}, "M139_MODEL_CALL_DENIED"),
        ({"memory_write_enabled": True}, "M139_MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "M139_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_enabled": True}, "M139_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M139_DEPENDENCY_DENIED"),
        (
            {"production_authority_granted": True},
            "M139_PRODUCTION_AUTHORITY_DENIED",
        ),
    ],
)
def test_m139_policy_denies_runtime_authority(update: Any, reason: str) -> None:
    policy = AbuseLoopDetectionPolicy().model_copy(update=update)

    with pytest.raises(ValueError, match=reason):
        validate_abuse_loop_detection_policy(policy)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"abuse_detection_runtime_requested": True},
            "M139_ABUSE_DETECTION_RUNTIME_DENIED",
        ),
        (
            {"loop_detection_runtime_requested": True},
            "M139_LOOP_DETECTION_RUNTIME_DENIED",
        ),
        ({"loop_monitor_requested": True}, "M139_LOOP_MONITOR_DENIED"),
        ({"loop_intervention_requested": True}, "M139_LOOP_INTERVENTION_DENIED"),
        (
            {"autonomous_recovery_execution_requested": True},
            "M139_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_requested": True}, "M139_RETRY_EXECUTION_DENIED"),
        ({"dependency_execution_requested": True}, "M139_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_requested": True}, "M139_BROWSER_ACTION_DENIED"),
        ({"connector_action_requested": True}, "M139_CONNECTOR_ACTION_DENIED"),
        ({"tool_execution_requested": True}, "M139_TOOL_EXECUTION_DENIED"),
        ({"execution_requested": True}, "M139_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "M139_NETWORK_ACCESS_DENIED"),
        ({"backend_route_requested": True}, "M139_BACKEND_ROUTE_DENIED"),
        ({"production_authority_requested": True}, "M139_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_abuse_log": True}, "M139_RAW_ABUSE_LOG_DENIED"),
        ({"contains_raw_loop_trace": True}, "M139_RAW_LOOP_TRACE_DENIED"),
        ({"contains_raw_prompt": True}, "M139_RAW_PROMPT_DENIED"),
        (
            {"contains_raw_provider_payload": True},
            "M139_RAW_PROVIDER_PAYLOAD_DENIED",
        ),
        ({"contains_cookie_or_credential": True}, "M139_COOKIE_OR_CREDENTIAL_DENIED"),
        ({"contains_secret": True}, "M139_SECRET_DENIED"),
    ],
)
def test_m139_request_denies_unsafe_inputs(update: Any, reason: str) -> None:
    request = _request().model_copy(update=update)

    with pytest.raises(ValueError, match=reason):
        validate_abuse_loop_detection_request(request)


def test_m139_request_denies_wrong_mode_risk_and_signal_overflow() -> None:
    with pytest.raises(ValueError, match="M139_MODE5_REQUIRED"):
        validate_abuse_loop_detection_request(
            _request().model_copy(
                update={
                    "requested_mode": AutonomyAuthorityMode.ask_before_every_action
                }
            )
        )

    with pytest.raises(ValueError, match="M139_RISK_CEILING_DENIED"):
        validate_abuse_loop_detection_request(
            _request().model_copy(update={"max_risk_class": AutonomyRiskClass.medium})
        )

    with pytest.raises(ValueError, match="M139_SIGNAL_LIMIT_DENIED"):
        validate_abuse_loop_detection_request(
            _request().model_copy(
                update={
                    "abuse_signal_refs": ["abuse-signal:a", "abuse-signal:b"],
                    "loop_signal_refs": ["loop-signal:a"],
                    "max_signal_refs": 2,
                }
            )
        )


def test_m139_request_denies_side_effects_and_secret_like_content() -> None:
    with pytest.raises(ValueError, match="M139_SIDE_EFFECTS_DENIED"):
        validate_abuse_loop_detection_request(
            _request().model_copy(update={"side_effects_performed": ["monitor-started"]})
        )

    with pytest.raises(ValueError, match="M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED"):
        validate_abuse_loop_detection_request(
            _request().model_copy(update={"metadata": {"api_key": "secret-value"}})
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"abuse_detection_runtime_authorized": True},
            "M139_ABUSE_DETECTION_RUNTIME_DENIED",
        ),
        (
            {"loop_detection_runtime_authorized": True},
            "M139_LOOP_DETECTION_RUNTIME_DENIED",
        ),
        ({"loop_monitor_started": True}, "M139_LOOP_MONITOR_DENIED"),
        ({"detector_runtime_started": True}, "M139_DETECTOR_RUNTIME_DENIED"),
        ({"loop_intervention_performed": True}, "M139_LOOP_INTERVENTION_DENIED"),
        (
            {"autonomous_recovery_execution_authorized": True},
            "M139_RECOVERY_EXECUTION_DENIED",
        ),
        ({"retry_execution_performed": True}, "M139_RETRY_EXECUTION_DENIED"),
        ({"rollback_execution_performed": True}, "M139_ROLLBACK_EXECUTION_DENIED"),
        ({"resume_execution_performed": True}, "M139_RESUME_EXECUTION_DENIED"),
        ({"dependency_execution_performed": True}, "M139_DEPENDENCY_EXECUTION_DENIED"),
        ({"browser_action_performed": True}, "M139_BROWSER_ACTION_DENIED"),
        ({"connector_action_performed": True}, "M139_CONNECTOR_ACTION_DENIED"),
        ({"tool_execution_performed": True}, "M139_TOOL_EXECUTION_DENIED"),
        ({"execution_performed": True}, "M139_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "M139_BACKEND_ROUTE_DENIED"),
        (
            {"production_authority_granted": True},
            "M139_PRODUCTION_AUTHORITY_DENIED",
        ),
    ],
)
def test_m139_decision_denies_unsafe_mutations(update: Any, reason: str) -> None:
    decision = build_abuse_loop_detection_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_abuse_loop_detection_decision(decision.model_copy(update=update))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"store_raw_abuse_log": True}, "M139_RAW_ABUSE_LOG_DENIED"),
        ({"store_raw_loop_trace": True}, "M139_RAW_LOOP_TRACE_DENIED"),
        ({"store_raw_prompt": True}, "M139_RAW_PROMPT_DENIED"),
        ({"store_raw_provider_payload": True}, "M139_RAW_PROVIDER_PAYLOAD_DENIED"),
        ({"store_cookie_or_credential": True}, "M139_COOKIE_OR_CREDENTIAL_DENIED"),
        ({"store_secret": True}, "M139_SECRET_DENIED"),
        ({"detector_runtime_started": True}, "M139_DETECTOR_RUNTIME_DENIED"),
        ({"loop_intervention_performed": True}, "M139_LOOP_INTERVENTION_DENIED"),
        ({"recovery_execution_performed": True}, "M139_RECOVERY_EXECUTION_DENIED"),
    ],
)
def test_m139_receipt_plan_denies_raw_and_runtime_mutations(update: Any, reason: str) -> None:
    decision = build_abuse_loop_detection_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_abuse_loop_detection_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(update=update)
                }
            )
        )


def test_m139_decision_requires_contract_reason_code() -> None:
    decision = build_abuse_loop_detection_decision(_request())

    with pytest.raises(ValueError, match="M139_REASON_CODE_REQUIRED"):
        validate_abuse_loop_detection_decision(
            AbuseLoopDetectionDecision.model_validate(
                decision.model_dump() | {"reason_codes": ["M140_REMAINS_FUTURE"]}
            )
        )
