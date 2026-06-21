from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    M132_MAX_RECURRENCE_OCCURRENCES,
    M132_MIN_CADENCE_SECONDS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    TrustedRecurringWorkflowPolicy,
    TrustedRecurringWorkflowRequest,
    TrustedRecurringWorkflowStatus,
    build_trusted_recurring_workflow_decision,
    validate_trusted_recurring_workflow_decision,
    validate_trusted_recurring_workflow_policy,
    validate_trusted_recurring_workflow_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "trusted-recurring-workflow-request:m132:review",
        "trusted_workflow_ref": "trusted-recurring-workflow:m132:review",
        "mode_ref": "autonomy-mode:m132:mode5",
        "actor_ref": "actor:m132:reviewer",
        "user_ref": "user:m132:owner",
        "workspace_ref": "workspace:m132:local",
        "scope_ref": "scope:m132:single-workspace",
        "resource_refs": ["resource:m132:status-summary"],
        "capability_refs": ["capability:m132:trusted-recurring-review"],
        "allowlist_refs": ["allowlist:m132:safe-recurring-refs-only"],
        "m131_work_session_decision_ref": "mode4-scoped-work-session-decision:m131:review",
        "recurring_contract_ref": "recurring-automation-contract:m97:safe",
        "scoped_low_risk_recurring_ref": "scoped-recurring-low-risk:m98:safe",
        "cadence_ref": "cadence:m132:review-window",
        "approval_bundle_ref": "approval-bundle:m132:exact-scope",
        "approval_renewal_ref": "approval-renewal:m132:required",
        "expiration_ref": "expiration:m132:required",
        "stop_condition_refs": [
            "stop-condition:m132:user-revoked",
            "stop-condition:m132:renewal-expired",
        ],
        "policy_decision_ref": "policy-decision:m132:mode5",
        "risk_decision_ref": "risk-decision:m132:low-only",
        "audit_ref": "audit:m132:trusted-recurring",
        "replay_ref": "replay:m132:trusted-recurring",
        "revocation_ref": "revocation:m132:trusted-recurring",
        "kill_switch_ref": "kill-switch:m132:trusted-recurring",
        "no_effect_receipt_plan_ref": "receipt-plan:m132:trusted-recurring:no-effect",
        "minimum_interval_seconds": M132_MIN_CADENCE_SECONDS,
        "max_occurrences": M132_MAX_RECURRENCE_OCCURRENCES,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_goal_summary": "Review a Mode 5 trusted recurring workflow contract without starting it.",
    }
    data.update(overrides)
    return TrustedRecurringWorkflowRequest(**data)


def test_m132_trusted_recurring_workflow_is_review_only_and_route_free() -> None:
    decision = build_trusted_recurring_workflow_decision(_request())

    assert decision.status == TrustedRecurringWorkflowStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.trusted_recurring_workflow_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m131_work_session_bound is True
    assert decision.recurring_contract_bound is True
    assert decision.scoped_low_risk_recurring_bound is True
    assert decision.cadence_bound is True
    assert decision.approval_bundle_bound is True
    assert decision.approval_renewal_bound is True
    assert decision.expiration_bound is True
    assert decision.stop_conditions_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.minimum_interval_seconds == M132_MIN_CADENCE_SECONDS
    assert decision.max_occurrences == M132_MAX_RECURRENCE_OCCURRENCES
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.mode5_runtime_authorized is False
    assert decision.trusted_recurring_workflow_start_authorized is False
    assert decision.workflow_started is False
    assert decision.recurrence_active is False
    assert decision.recurring_runtime_started is False
    assert decision.scheduler_started is False
    assert decision.background_worker_started is False
    assert decision.long_running_supervisor_started is False
    assert decision.autonomous_actions_authorized is False
    assert decision.execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.network_access_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.connector_runtime_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_prompt is False
    assert decision.reason_codes == [
        "M132_TRUSTED_RECURRING_WORKFLOW_CONTRACT_ONLY",
        "M132_EXACT_RECURRING_SCOPE_REQUIRED",
        "M132_APPROVAL_RENEWAL_REQUIRED",
        "M132_NO_SCHEDULER_OR_RUNTIME",
        "M133_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M132_MODE5_RUNTIME_DENIED"),
        ("trusted_recurring_workflow_start_enabled", "M132_WORKFLOW_START_DENIED"),
        ("recurring_runtime_enabled", "M132_RECURRING_RUNTIME_DENIED"),
        ("scheduler_enabled", "M132_SCHEDULER_DENIED"),
        ("background_worker_enabled", "M132_BACKGROUND_WORKER_DENIED"),
        ("long_running_supervisor_enabled", "M133_LONG_RUNNING_SUPERVISOR_DENIED"),
        ("autonomous_actions_enabled", "M132_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M132_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M132_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M132_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M132_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M132_BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "M132_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M132_CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "M132_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M132_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M132_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M132_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M132_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M132_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M132_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M132_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m132_policy_denies_runtime_scheduler_and_future_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_trusted_recurring_workflow_policy(
            TrustedRecurringWorkflowPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M132_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M132_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M132_RESOURCE_REF_REQUIRED"),
        (
            {"resource_refs": ["resource:m132:a", "resource:m132:a"]},
            "M132_REF_DUPLICATE",
        ),
        ({"capability_refs": []}, "M132_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M132_ALLOWLIST_REF_REQUIRED"),
        ({"stop_condition_refs": []}, "M132_STOP_CONDITION_REF_REQUIRED"),
        ({"minimum_interval_seconds": M132_MIN_CADENCE_SECONDS - 1}, "greater than or equal"),
        ({"max_occurrences": M132_MAX_RECURRENCE_OCCURRENCES + 1}, "less than or equal"),
        ({"mode5_runtime_requested": True}, "M132_MODE5_RUNTIME_DENIED"),
        (
            {"trusted_recurring_workflow_start_requested": True},
            "M132_WORKFLOW_START_DENIED",
        ),
        ({"recurring_runtime_requested": True}, "M132_RECURRING_RUNTIME_DENIED"),
        ({"recurrence_active": True}, "M132_RECURRENCE_ACTIVE_DENIED"),
        ({"scheduler_requested": True}, "M132_SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "M132_BACKGROUND_WORKER_DENIED"),
        ({"long_running_supervisor_requested": True}, "M133_LONG_RUNNING_SUPERVISOR_DENIED"),
        ({"autonomous_actions_requested": True}, "M132_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M132_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M132_TOOL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "M132_BROWSER_AUTOMATION_DENIED"),
        ({"production_authority_requested": True}, "M132_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_prompt": True}, "M132_RAW_PROMPT_DENIED"),
        ({"contains_secret": True}, "M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED"),
    ],
)
def test_m132_request_denies_unsafe_or_unbounded_scope(override: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        build_trusted_recurring_workflow_decision(_request(**override))


def test_m132_revalidates_model_copy_mutations_and_receipt_binding() -> None:
    decision = build_trusted_recurring_workflow_decision(_request())

    for update, reason in [
        ({"contract_only": False}, "M132_CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M132_REVIEW_ONLY_REQUIRED"),
        ({"exact_scope_bound": False}, "M132_EXACT_SCOPE_REQUIRED"),
        ({"mode5_runtime_authorized": True}, "M132_MODE5_RUNTIME_DENIED"),
        ({"workflow_started": True}, "M132_WORKFLOW_START_DENIED"),
        ({"recurrence_active": True}, "M132_RECURRENCE_ACTIVE_DENIED"),
        ({"recurring_runtime_started": True}, "M132_RECURRING_RUNTIME_DENIED"),
        ({"scheduler_started": True}, "M132_SCHEDULER_DENIED"),
        ({"background_worker_started": True}, "M132_BACKGROUND_WORKER_DENIED"),
        ({"long_running_supervisor_started": True}, "M133_LONG_RUNNING_SUPERVISOR_DENIED"),
        ({"autonomous_actions_performed": True}, "M132_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_performed": True}, "M132_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M132_TOOL_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "M132_BACKEND_ROUTE_DENIED"),
        ({"production_authority_granted": True}, "M132_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["started recurrence"]}, "M132_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_trusted_recurring_workflow_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="M132_RECEIPT_BINDING_MISMATCH"):
        validate_trusted_recurring_workflow_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"scope_ref": "scope:m132:other"}
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="M132_RAW_PROMPT_DENIED"):
        validate_trusted_recurring_workflow_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_prompt": True}
                    )
                }
            )
        )


def test_m132_denies_secret_like_metadata_on_request_policy_and_decision() -> None:
    with pytest.raises(ValueError, match="M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED"):
        validate_trusted_recurring_workflow_request(
            _request(metadata={"connector_token": "abc123supersecret"})
        )

    with pytest.raises(ValueError, match="M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED"):
        validate_trusted_recurring_workflow_policy(
            TrustedRecurringWorkflowPolicy(metadata={"api_key": "abc123supersecret"})
        )

    decision = build_trusted_recurring_workflow_decision(_request())
    with pytest.raises(ValueError, match="M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED"):
        validate_trusted_recurring_workflow_decision(
            decision.model_copy(update={"metadata": {"oauth_token": "abc123supersecret"}})
        )
