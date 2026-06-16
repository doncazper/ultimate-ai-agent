import pytest

from ultimate_ai_agent.core.autonomy import (
    M131_MAX_WORK_SESSION_SECONDS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    Mode4ScopedWorkSessionPolicy,
    Mode4ScopedWorkSessionRequest,
    Mode4ScopedWorkSessionStatus,
    build_mode4_scoped_work_session_decision,
    validate_mode4_scoped_work_session_decision,
    validate_mode4_scoped_work_session_policy,
    validate_mode4_scoped_work_session_request,
)


def _request(**overrides):
    data = {
        "request_ref": "mode4-work-session-request:m131:review",
        "work_session_ref": "mode4-work-session:m131:review",
        "mode_ref": "autonomy-mode:m131:mode4",
        "actor_ref": "actor:m131:reviewer",
        "user_ref": "user:m131:owner",
        "workspace_ref": "workspace:m131:local",
        "scope_ref": "scope:m131:single-workspace",
        "resource_refs": ["resource:m131:status-summary"],
        "capability_refs": ["capability:m131:review-only-planning"],
        "allowlist_refs": ["allowlist:m131:safe-refs-only"],
        "policy_decision_ref": "policy-decision:m131:mode4",
        "approval_bundle_ref": "approval-bundle:m131:exact-scope",
        "risk_decision_ref": "risk-decision:m131:low-medium-ceiling",
        "audit_ref": "audit:m131:mode4",
        "replay_ref": "replay:m131:mode4",
        "revocation_ref": "revocation:m131:mode4",
        "kill_switch_ref": "kill-switch:m131:mode4",
        "no_effect_receipt_plan_ref": "receipt-plan:m131:mode4:no-effect",
        "max_duration_seconds": M131_MAX_WORK_SESSION_SECONDS,
        "max_risk_class": AutonomyRiskClass.medium,
        "safe_goal_summary": "Review a scoped Mode 4 work-session contract without starting it.",
    }
    data.update(overrides)
    return Mode4ScopedWorkSessionRequest(**data)


def test_m131_mode4_scoped_work_session_is_review_only_and_route_free():
    decision = build_mode4_scoped_work_session_decision(_request())

    assert decision.status == Mode4ScopedWorkSessionStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.scoped_autonomy_window
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.scoped_work_session_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.actor_bound is True
    assert decision.resource_bound is True
    assert decision.capability_bound is True
    assert decision.allowlist_bound is True
    assert decision.policy_decision_bound is True
    assert decision.approval_bundle_bound is True
    assert decision.risk_decision_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.max_duration_seconds == M131_MAX_WORK_SESSION_SECONDS
    assert decision.max_risk_class == AutonomyRiskClass.medium
    assert decision.mode4_runtime_authorized is False
    assert decision.scoped_work_session_start_authorized is False
    assert decision.session_started is False
    assert decision.session_active is False
    assert decision.autonomous_actions_authorized is False
    assert decision.execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.tool_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.network_access_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.background_worker_started is False
    assert decision.scheduler_started is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.production_authority_granted is False
    assert decision.trusted_recurring_workflow_enabled is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_prompt is False
    assert decision.reason_codes == [
        "M131_MODE4_SCOPED_WORK_SESSION_CONTRACT_ONLY",
        "M131_EXACT_SCOPE_REQUIRED",
        "M131_APPROVAL_BUNDLE_REQUIRED",
        "M131_NO_SESSION_START_OR_EXECUTION",
        "M132_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode4_runtime_enabled", "M131_MODE4_RUNTIME_DENIED"),
        ("scoped_work_session_start_enabled", "M131_SESSION_START_DENIED"),
        ("autonomous_actions_enabled", "M131_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M131_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M131_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M131_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M131_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M131_BROWSER_AUTOMATION_DENIED"),
        ("browser_form_enabled", "M131_BROWSER_FORM_DENIED"),
        ("authenticated_browser_enabled", "M131_AUTHENTICATED_BROWSER_DENIED"),
        ("download_enabled", "M131_DOWNLOAD_DENIED"),
        ("upload_enabled", "M131_UPLOAD_DENIED"),
        ("plugin_execution_enabled", "M131_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M131_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "M131_ACCOUNT_AUTH_DENIED"),
        ("background_worker_enabled", "M131_BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "M131_SCHEDULER_DENIED"),
        ("model_call_enabled", "M131_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M131_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M131_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M131_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M131_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M131_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M131_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M131_PRODUCTION_AUTHORITY_DENIED"),
        (
            "trusted_recurring_workflow_enabled",
            "M132_TRUSTED_RECURRING_WORKFLOW_DENIED",
        ),
    ],
)
def test_m131_policy_denies_runtime_and_future_authority(field, reason):
    with pytest.raises(ValueError, match=reason):
        validate_mode4_scoped_work_session_policy(
            Mode4ScopedWorkSessionPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.dry_run_plan}, "M131_MODE4_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.high}, "M131_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M131_RESOURCE_REF_REQUIRED"),
        (
            {"resource_refs": ["resource:m131:a", "resource:m131:a"]},
            "M131_REF_DUPLICATE",
        ),
        ({"capability_refs": []}, "M131_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M131_ALLOWLIST_REF_REQUIRED"),
        ({"mode4_runtime_requested": True}, "M131_MODE4_RUNTIME_DENIED"),
        ({"scoped_work_session_start_requested": True}, "M131_SESSION_START_DENIED"),
        ({"session_active": True}, "M131_SESSION_ACTIVE_DENIED"),
        ({"autonomous_actions_requested": True}, "M131_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M131_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M131_TOOL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "M131_BROWSER_AUTOMATION_DENIED"),
        ({"background_worker_requested": True}, "M131_BACKGROUND_WORKER_DENIED"),
        ({"production_authority_requested": True}, "M131_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_prompt": True}, "M131_RAW_PROMPT_DENIED"),
        ({"contains_secret": True}, "M131_SECRET_LIKE_MODE4_CONTENT_DENIED"),
    ],
)
def test_m131_request_denies_unsafe_or_unbounded_scope(override, reason):
    with pytest.raises(ValueError, match=reason):
        build_mode4_scoped_work_session_decision(_request(**override))


def test_m131_revalidates_model_copy_mutations_and_receipt_binding():
    decision = build_mode4_scoped_work_session_decision(_request())

    for update, reason in [
        ({"contract_only": False}, "M131_CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M131_REVIEW_ONLY_REQUIRED"),
        ({"exact_scope_bound": False}, "M131_EXACT_SCOPE_REQUIRED"),
        ({"mode4_runtime_authorized": True}, "M131_MODE4_RUNTIME_DENIED"),
        ({"session_started": True}, "M131_SESSION_START_DENIED"),
        ({"session_active": True}, "M131_SESSION_ACTIVE_DENIED"),
        ({"autonomous_actions_performed": True}, "M131_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_performed": True}, "M131_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M131_TOOL_EXECUTION_DENIED"),
        ({"browser_form_performed": True}, "M131_BROWSER_FORM_DENIED"),
        ({"background_worker_started": True}, "M131_BACKGROUND_WORKER_DENIED"),
        ({"production_authority_granted": True}, "M131_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["started session"]}, "M131_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mode4_scoped_work_session_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="M131_RECEIPT_BINDING_MISMATCH"):
        validate_mode4_scoped_work_session_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"scope_ref": "scope:m131:other"}
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="M131_RAW_PROMPT_DENIED"):
        validate_mode4_scoped_work_session_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_prompt": True}
                    )
                }
            )
        )


def test_m131_denies_secret_like_metadata_on_request_policy_and_decision():
    with pytest.raises(ValueError, match="M131_SECRET_LIKE_MODE4_CONTENT_DENIED"):
        validate_mode4_scoped_work_session_request(
            _request(metadata={"connector_token": "abc123supersecret"})
        )

    with pytest.raises(ValueError, match="M131_SECRET_LIKE_MODE4_CONTENT_DENIED"):
        validate_mode4_scoped_work_session_policy(
            Mode4ScopedWorkSessionPolicy(metadata={"api_key": "abc123supersecret"})
        )

    decision = build_mode4_scoped_work_session_decision(_request())
    with pytest.raises(ValueError, match="M131_SECRET_LIKE_MODE4_CONTENT_DENIED"):
        validate_mode4_scoped_work_session_decision(
            decision.model_copy(update={"metadata": {"oauth_token": "abc123supersecret"}})
        )
