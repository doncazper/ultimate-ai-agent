import pytest

from ultimate_ai_agent.core.autonomy import (
    M137_MAX_BROWSER_PLAN_REFS,
    M137_MAX_WORKFLOW_STEP_REFS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    BrowserConnectorCombinedWorkflowPolicy,
    BrowserConnectorCombinedWorkflowRequest,
    BrowserConnectorCombinedWorkflowStatus,
    build_browser_connector_combined_workflow_decision,
    validate_browser_connector_combined_workflow_decision,
    validate_browser_connector_combined_workflow_policy,
    validate_browser_connector_combined_workflow_request,
)


def _request(**overrides):
    data = {
        "request_ref": "browser-connector-combined-workflow-request:m137:review",
        "combined_workflow_plan_ref": "combined-workflow-plan:m137:review",
        "mode_ref": "autonomy-mode:m137:mode5",
        "actor_ref": "actor:m137:reviewer",
        "user_ref": "user:m137:owner",
        "workspace_ref": "workspace:m137:local",
        "scope_ref": "scope:m137:single-workspace",
        "resource_refs": ["resource:m137:workflow-summary"],
        "capability_refs": ["capability:m137:combined-workflow-review"],
        "allowlist_refs": ["allowlist:m137:safe-browser-connector-refs-only"],
        "m136_dependency_execution_decision_ref": (
            "cross-tool-dependency-execution-decision:m136:review"
        ),
        "m135_recovery_planner_decision_ref": (
            "autonomous-recovery-planner-decision:m135:review"
        ),
        "m134_human_checkpoint_decision_ref": (
            "human-checkpoint-scheduling-decision:m134:review"
        ),
        "m133_supervisor_decision_ref": (
            "long-running-task-supervisor-decision:m133:review"
        ),
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "browser_workflow_ref": "browser-workflow:m137:observe-plan",
        "browser_observation_ref": "browser-observation:m137:safe-visible-text",
        "browser_action_plan_refs": [
            "browser-action-plan:m137:review-only-click",
            "browser-action-plan:m137:review-only-form",
        ],
        "connector_workflow_ref": "connector-workflow:m137:review-plan",
        "connector_account_scope_ref": "connector-account-scope:m137:safe-ref",
        "connector_action_plan_refs": [
            "connector-action-plan:m137:review-only-read",
            "connector-action-plan:m137:review-only-write",
        ],
        "workflow_step_refs": [
            "workflow-step:m137:observe",
            "workflow-step:m137:connector-review",
            "workflow-step:m137:human-checkpoint",
        ],
        "combined_dependency_graph_ref": "combined-dependency-graph:m137:declared",
        "dependency_order_ref": "dependency-order:m137:review-only",
        "safe_handoff_ref": "safe-handoff:m137:redacted-summary",
        "dry_run_plan_ref": "dry-run-plan:m137:no-execution",
        "approval_bundle_ref": "approval-bundle:m137:review-only",
        "checkpoint_ref": "checkpoint:m137:human-review",
        "human_checkpoint_ref": "human-checkpoint:m137:owner-review",
        "policy_decision_ref": "policy-decision:m137:mode5-combined-review",
        "risk_decision_ref": "risk-decision:m137:low-only",
        "audit_ref": "audit:m137:combined-review",
        "replay_ref": "replay:m137:combined-review",
        "revocation_ref": "revocation:m137:combined-review",
        "kill_switch_ref": "kill-switch:m137:combined-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m137:combined:no-effect",
        "max_workflow_steps": M137_MAX_WORKFLOW_STEP_REFS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_workflow_summary": (
            "Review browser and connector workflow refs without running actions."
        ),
    }
    data.update(overrides)
    return BrowserConnectorCombinedWorkflowRequest(**data)


def test_m137_browser_connector_combined_workflow_is_review_only_and_route_free():
    decision = build_browser_connector_combined_workflow_decision(_request())

    assert decision.status == BrowserConnectorCombinedWorkflowStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.browser_connector_combined_workflow_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m136_dependency_execution_bound is True
    assert decision.m135_recovery_planner_bound is True
    assert decision.m134_human_checkpoint_bound is True
    assert decision.m133_supervisor_bound is True
    assert decision.m132_trusted_workflow_bound is True
    assert decision.browser_plan_bound is True
    assert decision.connector_plan_bound is True
    assert decision.combined_dependency_graph_bound is True
    assert decision.dry_run_plan_bound is True
    assert decision.approval_bundle_bound is True
    assert decision.human_checkpoint_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.mode5_runtime_authorized is False
    assert decision.combined_workflow_runtime_authorized is False
    assert decision.browser_action_authorized is False
    assert decision.browser_action_performed is False
    assert decision.browser_click_performed is False
    assert decision.browser_form_performed is False
    assert decision.authenticated_browser_used is False
    assert decision.connector_runtime_authorized is False
    assert decision.connector_action_authorized is False
    assert decision.connector_write_performed is False
    assert decision.account_auth_performed is False
    assert decision.dependency_execution_authorized is False
    assert decision.dependency_execution_performed is False
    assert decision.tool_execution_authorized is False
    assert decision.tool_execution_performed is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.network_access_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_browser_plan_refs_only is True
    assert decision.receipt_plan.store_connector_plan_refs_only is True
    assert decision.receipt_plan.store_raw_browser_dom is False
    assert decision.receipt_plan.store_raw_connector_payload is False
    assert decision.receipt_plan.browser_action_performed is False
    assert decision.receipt_plan.connector_action_performed is False
    assert decision.reason_codes == [
        "M137_BROWSER_CONNECTOR_COMBINED_WORKFLOW_CONTRACT_ONLY",
        "M137_EXACT_BROWSER_CONNECTOR_SCOPE_REQUIRED",
        "M137_NO_BROWSER_OR_CONNECTOR_RUNTIME",
        "M137_NO_COMBINED_WORKFLOW_EXECUTION",
        "M138_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M137_MODE5_RUNTIME_DENIED"),
        ("combined_workflow_runtime_enabled", "M137_COMBINED_WORKFLOW_RUNTIME_DENIED"),
        ("browser_action_enabled", "M137_BROWSER_ACTION_DENIED"),
        ("browser_navigation_enabled", "M137_BROWSER_NAVIGATION_DENIED"),
        ("browser_click_enabled", "M137_BROWSER_CLICK_DENIED"),
        ("browser_form_enabled", "M137_BROWSER_FORM_DENIED"),
        ("browser_download_enabled", "M137_BROWSER_DOWNLOAD_DENIED"),
        ("browser_upload_enabled", "M137_BROWSER_UPLOAD_DENIED"),
        ("authenticated_browser_enabled", "M137_AUTHENTICATED_BROWSER_DENIED"),
        ("connector_runtime_enabled", "M137_CONNECTOR_RUNTIME_DENIED"),
        ("connector_read_runtime_enabled", "M137_CONNECTOR_RUNTIME_DENIED"),
        ("connector_write_enabled", "M137_CONNECTOR_WRITE_DENIED"),
        ("connector_send_enabled", "M137_CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "M137_CONNECTOR_DELETE_DENIED"),
        ("account_auth_enabled", "M137_ACCOUNT_AUTH_DENIED"),
        ("dependency_execution_enabled", "M137_DEPENDENCY_EXECUTION_DENIED"),
        ("dependency_resolver_runtime_enabled", "M137_DEPENDENCY_RESOLVER_DENIED"),
        ("cross_tool_runtime_enabled", "M137_CROSS_TOOL_RUNTIME_DENIED"),
        ("tool_execution_enabled", "M137_TOOL_EXECUTION_DENIED"),
        ("execution_enabled", "M137_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M137_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M137_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_enabled", "M137_PLUGIN_EXECUTION_DENIED"),
        ("model_call_enabled", "M137_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M137_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M137_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M137_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M137_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M137_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M137_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m137_policy_denies_browser_connector_runtime_and_future_authority(
    field, reason
):
    with pytest.raises(ValueError, match=reason):
        validate_browser_connector_combined_workflow_policy(
            BrowserConnectorCombinedWorkflowPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M137_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M137_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M137_RESOURCE_REF_REQUIRED"),
        ({"capability_refs": []}, "M137_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M137_ALLOWLIST_REF_REQUIRED"),
        ({"workflow_step_refs": []}, "M137_WORKFLOW_STEP_REF_REQUIRED"),
        (
            {
                "workflow_step_refs": [
                    f"workflow-step:m137:{index}"
                    for index in range(M137_MAX_WORKFLOW_STEP_REFS + 1)
                ]
            },
            "M137_REF_LIST_TOO_LONG",
        ),
        ({"browser_action_plan_refs": []}, "M137_BROWSER_PLAN_REF_REQUIRED"),
        (
            {
                "browser_action_plan_refs": [
                    f"browser-action-plan:m137:{index}"
                    for index in range(M137_MAX_BROWSER_PLAN_REFS + 1)
                ]
            },
            "M137_REF_LIST_TOO_LONG",
        ),
        ({"connector_action_plan_refs": []}, "M137_CONNECTOR_PLAN_REF_REQUIRED"),
        ({"mode5_runtime_requested": True}, "M137_MODE5_RUNTIME_DENIED"),
        (
            {"combined_workflow_runtime_requested": True},
            "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
        ),
        ({"browser_action_requested": True}, "M137_BROWSER_ACTION_DENIED"),
        ({"browser_click_requested": True}, "M137_BROWSER_CLICK_DENIED"),
        ({"browser_form_requested": True}, "M137_BROWSER_FORM_DENIED"),
        ({"authenticated_browser_requested": True}, "M137_AUTHENTICATED_BROWSER_DENIED"),
        ({"connector_runtime_requested": True}, "M137_CONNECTOR_RUNTIME_DENIED"),
        ({"connector_write_requested": True}, "M137_CONNECTOR_WRITE_DENIED"),
        ({"connector_send_requested": True}, "M137_CONNECTOR_SEND_DENIED"),
        ({"connector_delete_requested": True}, "M137_CONNECTOR_DELETE_DENIED"),
        ({"account_auth_requested": True}, "M137_ACCOUNT_AUTH_DENIED"),
        ({"dependency_execution_requested": True}, "M137_DEPENDENCY_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M137_TOOL_EXECUTION_DENIED"),
        ({"execution_requested": True}, "M137_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "M137_SHELL_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "M137_NETWORK_ACCESS_DENIED"),
        ({"plugin_execution_requested": True}, "M137_PLUGIN_EXECUTION_DENIED"),
        ({"model_call_requested": True}, "M137_MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "M137_MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "M137_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_requested": True}, "M137_BACKEND_ROUTE_DENIED"),
        ({"dependency_requested": True}, "M137_DEPENDENCY_DENIED"),
        ({"beta_release_requested": True}, "M137_BETA_RELEASE_DENIED"),
        ({"production_authority_requested": True}, "M137_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_browser_dom": True}, "M137_RAW_BROWSER_DOM_DENIED"),
        (
            {"contains_raw_connector_payload": True},
            "M137_RAW_CONNECTOR_PAYLOAD_DENIED",
        ),
        ({"contains_cookie_or_credential": True}, "M137_COOKIE_OR_CREDENTIAL_DENIED"),
        ({"contains_secret": True}, "M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED"),
        ({"side_effects_performed": ["browser-click"]}, "M137_SIDE_EFFECTS_DENIED"),
    ],
)
def test_m137_request_rejects_unbounded_or_executing_combined_workflows(
    overrides, reason
):
    with pytest.raises(ValueError, match=reason):
        validate_browser_connector_combined_workflow_request(_request(**overrides))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"selected_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M137_MODE5_REQUIRED"),
        ({"mode5_runtime_authorized": True}, "M137_MODE5_RUNTIME_DENIED"),
        (
            {"combined_workflow_runtime_authorized": True},
            "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
        ),
        ({"browser_action_authorized": True}, "M137_BROWSER_ACTION_DENIED"),
        ({"browser_action_performed": True}, "M137_BROWSER_ACTION_DENIED"),
        ({"browser_click_performed": True}, "M137_BROWSER_CLICK_DENIED"),
        ({"browser_form_performed": True}, "M137_BROWSER_FORM_DENIED"),
        ({"authenticated_browser_used": True}, "M137_AUTHENTICATED_BROWSER_DENIED"),
        ({"connector_runtime_authorized": True}, "M137_CONNECTOR_RUNTIME_DENIED"),
        ({"connector_action_authorized": True}, "M137_CONNECTOR_ACTION_DENIED"),
        ({"connector_write_performed": True}, "M137_CONNECTOR_WRITE_DENIED"),
        ({"account_auth_performed": True}, "M137_ACCOUNT_AUTH_DENIED"),
        ({"dependency_execution_authorized": True}, "M137_DEPENDENCY_EXECUTION_DENIED"),
        ({"dependency_execution_performed": True}, "M137_DEPENDENCY_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M137_TOOL_EXECUTION_DENIED"),
        ({"execution_performed": True}, "M137_EXECUTION_DENIED"),
        ({"shell_execution_performed": True}, "M137_SHELL_EXECUTION_DENIED"),
        ({"network_access_performed": True}, "M137_NETWORK_ACCESS_DENIED"),
        ({"plugin_execution_performed": True}, "M137_PLUGIN_EXECUTION_DENIED"),
        ({"model_call_performed": True}, "M137_MODEL_CALL_DENIED"),
        ({"memory_write_performed": True}, "M137_MEMORY_WRITE_DENIED"),
        ({"context_injection_performed": True}, "M137_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_added": True}, "M137_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M137_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M137_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M137_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m137_decision_rejects_runtime_or_authority_mutations(update, reason):
    decision = build_browser_connector_combined_workflow_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_browser_connector_combined_workflow_decision(
            decision.model_copy(update=update)
        )


def test_m137_receipt_plan_rejects_raw_browser_connector_payloads():
    decision = build_browser_connector_combined_workflow_decision(_request())

    with pytest.raises(ValueError, match="M137_RAW_BROWSER_DOM_DENIED"):
        validate_browser_connector_combined_workflow_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_browser_dom": True}
                    )
                }
            )
        )
    with pytest.raises(ValueError, match="M137_RAW_CONNECTOR_PAYLOAD_DENIED"):
        validate_browser_connector_combined_workflow_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_connector_payload": True}
                    )
                }
            )
        )
