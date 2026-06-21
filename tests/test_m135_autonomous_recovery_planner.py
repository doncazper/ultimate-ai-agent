from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    M135_MAX_RECOVERY_STEP_REFS,
    M135_MAX_RECOVERY_WINDOW_SECONDS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    AutonomousRecoveryPlannerPolicy,
    AutonomousRecoveryPlannerRequest,
    AutonomousRecoveryPlannerStatus,
    build_autonomous_recovery_planner_decision,
    validate_autonomous_recovery_planner_decision,
    validate_autonomous_recovery_planner_policy,
    validate_autonomous_recovery_planner_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "autonomous-recovery-planner-request:m135:review",
        "recovery_plan_ref": "autonomous-recovery-plan:m135:review",
        "mode_ref": "autonomy-mode:m135:mode5",
        "actor_ref": "actor:m135:reviewer",
        "user_ref": "user:m135:owner",
        "workspace_ref": "workspace:m135:local",
        "scope_ref": "scope:m135:single-workspace",
        "resource_refs": ["resource:m135:recovery-summary"],
        "capability_refs": ["capability:m135:recovery-planning-review"],
        "allowlist_refs": ["allowlist:m135:safe-recovery-refs-only"],
        "m134_human_checkpoint_decision_ref": (
            "human-checkpoint-scheduling-decision:m134:review"
        ),
        "m133_supervisor_decision_ref": (
            "long-running-task-supervisor-decision:m133:review"
        ),
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "failure_signal_ref": "failure-signal:m135:declared",
        "recovery_trigger_ref": "recovery-trigger:m135:review-only",
        "recovery_strategy_ref": "recovery-strategy:m135:declared",
        "recovery_step_refs": [
            "recovery-step:m135:classify",
            "recovery-step:m135:checkpoint",
        ],
        "rollback_plan_ref": "rollback-plan:m135:no-execution",
        "resume_plan_ref": "resume-plan:m135:no-execution",
        "checkpoint_ref": "checkpoint:m135:human-review",
        "human_checkpoint_ref": "human-checkpoint:m135:owner-review",
        "policy_decision_ref": "policy-decision:m135:mode5-recovery",
        "risk_decision_ref": "risk-decision:m135:low-only",
        "audit_ref": "audit:m135:recovery-review",
        "replay_ref": "replay:m135:recovery-review",
        "revocation_ref": "revocation:m135:recovery-review",
        "kill_switch_ref": "kill-switch:m135:recovery-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m135:recovery:no-effect",
        "max_recovery_window_seconds": M135_MAX_RECOVERY_WINDOW_SECONDS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_recovery_summary": (
            "Review an autonomous recovery planner contract without executing it."
        ),
    }
    data.update(overrides)
    return AutonomousRecoveryPlannerRequest(**data)


def test_m135_autonomous_recovery_planner_is_review_only_and_route_free() -> None:
    decision = build_autonomous_recovery_planner_decision(_request())

    assert decision.status == AutonomousRecoveryPlannerStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.autonomous_recovery_planner_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m134_human_checkpoint_bound is True
    assert decision.m133_supervisor_bound is True
    assert decision.m132_trusted_workflow_bound is True
    assert decision.recovery_plan_bound is True
    assert decision.failure_signal_bound is True
    assert decision.recovery_trigger_bound is True
    assert decision.recovery_strategy_bound is True
    assert decision.recovery_steps_bound is True
    assert decision.rollback_plan_bound is True
    assert decision.resume_plan_bound is True
    assert decision.checkpoint_bound is True
    assert decision.human_checkpoint_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.max_recovery_window_seconds == M135_MAX_RECOVERY_WINDOW_SECONDS
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.mode5_runtime_authorized is False
    assert decision.recovery_planner_runtime_authorized is False
    assert decision.recovery_execution_authorized is False
    assert decision.recovery_execution_performed is False
    assert decision.retry_execution_performed is False
    assert decision.resume_execution_performed is False
    assert decision.rollback_execution_performed is False
    assert decision.supervisor_runtime_started is False
    assert decision.checkpoint_scheduler_started is False
    assert decision.human_checkpoint_scheduler_started is False
    assert decision.human_checkpoint_prompt_sent is False
    assert decision.notification_delivered is False
    assert decision.scheduler_started is False
    assert decision.background_worker_started is False
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
    assert decision.receipt_plan.recovery_executed is False
    assert decision.receipt_plan.retry_executed is False
    assert decision.receipt_plan.resume_executed is False
    assert decision.receipt_plan.rollback_executed is False
    assert decision.reason_codes == [
        "M135_AUTONOMOUS_RECOVERY_PLANNER_CONTRACT_ONLY",
        "M135_EXACT_RECOVERY_SCOPE_REQUIRED",
        "M135_HUMAN_CHECKPOINT_BINDING_REQUIRED",
        "M135_NO_RECOVERY_EXECUTION",
        "M136_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M135_MODE5_RUNTIME_DENIED"),
        ("recovery_planner_runtime_enabled", "M135_RECOVERY_PLANNER_RUNTIME_DENIED"),
        ("recovery_execution_enabled", "M135_RECOVERY_EXECUTION_DENIED"),
        ("retry_execution_enabled", "M135_RETRY_EXECUTION_DENIED"),
        ("resume_execution_enabled", "M135_RESUME_EXECUTION_DENIED"),
        ("rollback_execution_enabled", "M135_ROLLBACK_EXECUTION_DENIED"),
        ("supervisor_runtime_enabled", "M135_SUPERVISOR_RUNTIME_DENIED"),
        ("checkpoint_scheduler_enabled", "M135_CHECKPOINT_SCHEDULER_DENIED"),
        (
            "human_checkpoint_scheduler_enabled",
            "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
        ),
        ("human_checkpoint_prompt_enabled", "M135_PROMPT_RUNTIME_DENIED"),
        ("notification_delivery_enabled", "M135_NOTIFICATION_DELIVERY_DENIED"),
        ("scheduler_enabled", "M135_SCHEDULER_DENIED"),
        ("background_worker_enabled", "M135_BACKGROUND_WORKER_DENIED"),
        ("autonomous_actions_enabled", "M135_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M135_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M135_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M135_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M135_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M135_BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "M135_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M135_CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "M135_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M135_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M135_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M135_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M135_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M135_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M135_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M135_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m135_policy_denies_recovery_runtime_and_future_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomous_recovery_planner_policy(
            AutonomousRecoveryPlannerPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M135_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M135_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M135_RESOURCE_REF_REQUIRED"),
        ({"resource_refs": ["resource:m135:a", "resource:m135:a"]}, "M135_REF_DUPLICATE"),
        ({"capability_refs": []}, "M135_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M135_ALLOWLIST_REF_REQUIRED"),
        ({"recovery_step_refs": []}, "M135_RECOVERY_STEP_REF_REQUIRED"),
        (
            {
                "recovery_step_refs": [
                    f"recovery-step:m135:{index}"
                    for index in range(M135_MAX_RECOVERY_STEP_REFS + 1)
                ]
            },
            "M135_REF_LIST_TOO_LONG",
        ),
        (
            {"max_recovery_window_seconds": M135_MAX_RECOVERY_WINDOW_SECONDS + 1},
            "less than or equal",
        ),
        ({"mode5_runtime_requested": True}, "M135_MODE5_RUNTIME_DENIED"),
        (
            {"recovery_planner_runtime_requested": True},
            "M135_RECOVERY_PLANNER_RUNTIME_DENIED",
        ),
        ({"recovery_execution_requested": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        ({"retry_execution_requested": True}, "M135_RETRY_EXECUTION_DENIED"),
        ({"resume_execution_requested": True}, "M135_RESUME_EXECUTION_DENIED"),
        ({"rollback_execution_requested": True}, "M135_ROLLBACK_EXECUTION_DENIED"),
        ({"supervisor_runtime_requested": True}, "M135_SUPERVISOR_RUNTIME_DENIED"),
        ({"checkpoint_scheduler_requested": True}, "M135_CHECKPOINT_SCHEDULER_DENIED"),
        (
            {"human_checkpoint_scheduler_requested": True},
            "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
        ),
        ({"human_checkpoint_prompt_requested": True}, "M135_PROMPT_RUNTIME_DENIED"),
        (
            {"notification_delivery_requested": True},
            "M135_NOTIFICATION_DELIVERY_DENIED",
        ),
        ({"scheduler_requested": True}, "M135_SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "M135_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_requested": True}, "M135_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M135_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M135_TOOL_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "M135_SHELL_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "M135_NETWORK_ACCESS_DENIED"),
        ({"browser_automation_requested": True}, "M135_BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_requested": True}, "M135_PLUGIN_EXECUTION_DENIED"),
        ({"connector_runtime_requested": True}, "M135_CONNECTOR_RUNTIME_DENIED"),
        ({"model_call_requested": True}, "M135_MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "M135_MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "M135_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_requested": True}, "M135_BACKEND_ROUTE_DENIED"),
        ({"dependency_requested": True}, "M135_DEPENDENCY_DENIED"),
        ({"beta_release_requested": True}, "M135_BETA_RELEASE_DENIED"),
        ({"production_authority_requested": True}, "M135_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_prompt": True}, "M135_RAW_PROMPT_DENIED"),
        (
            {"contains_raw_provider_payload": True},
            "M135_RAW_PROVIDER_PAYLOAD_DENIED",
        ),
        ({"contains_secret": True}, "M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED"),
        ({"side_effects_performed": ["retry"]}, "M135_SIDE_EFFECTS_DENIED"),
    ],
)
def test_m135_request_rejects_unbounded_or_executing_recovery(overrides: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomous_recovery_planner_request(_request(**overrides))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"selected_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M135_MODE5_REQUIRED"),
        ({"recovery_execution_authorized": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        ({"recovery_execution_performed": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        ({"retry_execution_performed": True}, "M135_RETRY_EXECUTION_DENIED"),
        ({"resume_execution_performed": True}, "M135_RESUME_EXECUTION_DENIED"),
        ({"rollback_execution_performed": True}, "M135_ROLLBACK_EXECUTION_DENIED"),
        ({"supervisor_runtime_started": True}, "M135_SUPERVISOR_RUNTIME_DENIED"),
        ({"checkpoint_scheduler_started": True}, "M135_CHECKPOINT_SCHEDULER_DENIED"),
        (
            {"human_checkpoint_scheduler_started": True},
            "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
        ),
        ({"human_checkpoint_prompt_sent": True}, "M135_PROMPT_RUNTIME_DENIED"),
        ({"notification_delivered": True}, "M135_NOTIFICATION_DELIVERY_DENIED"),
        ({"scheduler_started": True}, "M135_SCHEDULER_DENIED"),
        ({"background_worker_started": True}, "M135_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_authorized": True}, "M135_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_authorized": True}, "M135_EXECUTION_DENIED"),
        ({"tool_execution_authorized": True}, "M135_TOOL_EXECUTION_DENIED"),
        ({"shell_execution_performed": True}, "M135_SHELL_EXECUTION_DENIED"),
        ({"network_access_performed": True}, "M135_NETWORK_ACCESS_DENIED"),
        ({"browser_automation_performed": True}, "M135_BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_performed": True}, "M135_PLUGIN_EXECUTION_DENIED"),
        ({"connector_runtime_performed": True}, "M135_CONNECTOR_RUNTIME_DENIED"),
        ({"model_call_performed": True}, "M135_MODEL_CALL_DENIED"),
        ({"memory_write_performed": True}, "M135_MEMORY_WRITE_DENIED"),
        ({"context_injection_performed": True}, "M135_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_added": True}, "M135_BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "M135_CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "M135_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M135_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M135_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["resume"]}, "M135_SIDE_EFFECTS_DENIED"),
        ({"reason_codes": []}, "M135_REASON_CODE_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.high}, "M135_RISK_CEILING_DENIED"),
    ],
)
def test_m135_decision_rejects_runtime_or_unsafe_mutations(update: Any, reason: str) -> None:
    decision = build_autonomous_recovery_planner_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_autonomous_recovery_planner_decision(decision.model_copy(update=update))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("store_raw_prompt", "M135_RAW_PROMPT_DENIED"),
        ("store_raw_provider_payload", "M135_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("store_secret", "M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED"),
        ("recovery_executed", "M135_RECOVERY_EXECUTION_DENIED"),
        ("retry_executed", "M135_RETRY_EXECUTION_DENIED"),
        ("resume_executed", "M135_RESUME_EXECUTION_DENIED"),
        ("rollback_executed", "M135_ROLLBACK_EXECUTION_DENIED"),
        ("supervisor_started", "M135_SUPERVISOR_RUNTIME_DENIED"),
        ("checkpoint_scheduled", "M135_CHECKPOINT_SCHEDULER_DENIED"),
        ("prompt_sent", "M135_PROMPT_RUNTIME_DENIED"),
        ("notification_delivered", "M135_NOTIFICATION_DELIVERY_DENIED"),
        ("execution_performed", "M135_EXECUTION_DENIED"),
    ],
)
def test_m135_receipt_plan_rejects_raw_storage_and_effects(field: str, reason: str) -> None:
    decision = build_autonomous_recovery_planner_decision(_request())
    receipt = decision.receipt_plan.model_copy(update={field: True})

    with pytest.raises(ValueError, match=reason):
        validate_autonomous_recovery_planner_decision(
            decision.model_copy(update={"receipt_plan": receipt})
        )


def test_m135_receipt_plan_must_match_decision_scope() -> None:
    decision = build_autonomous_recovery_planner_decision(_request())

    with pytest.raises(ValueError, match="M135_RECEIPT_BINDING_MISMATCH"):
        validate_autonomous_recovery_planner_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"recovery_plan_ref": "autonomous-recovery-plan:m135:other"}
                    )
                }
            )
        )


def test_m135_rejects_secret_like_safe_summary_and_metadata() -> None:
    with pytest.raises(ValueError, match="M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED"):
        _request(safe_recovery_summary="api_key=secret")

    with pytest.raises(ValueError, match="M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED"):
        AutonomousRecoveryPlannerPolicy(metadata={"token": "secret"})
