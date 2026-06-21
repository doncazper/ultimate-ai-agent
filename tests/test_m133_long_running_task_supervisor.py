from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    M133_MAX_CHECKPOINT_REFS,
    M133_MAX_SUPERVISOR_WINDOW_SECONDS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    LongRunningTaskSupervisorPolicy,
    LongRunningTaskSupervisorRequest,
    LongRunningTaskSupervisorStatus,
    build_long_running_task_supervisor_decision,
    validate_long_running_task_supervisor_decision,
    validate_long_running_task_supervisor_policy,
    validate_long_running_task_supervisor_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "long-running-task-supervisor-request:m133:review",
        "supervisor_ref": "long-running-task-supervisor:m133:review",
        "mode_ref": "autonomy-mode:m133:mode5",
        "actor_ref": "actor:m133:reviewer",
        "user_ref": "user:m133:owner",
        "workspace_ref": "workspace:m133:local",
        "scope_ref": "scope:m133:single-workspace",
        "resource_refs": ["resource:m133:task-state-summary"],
        "capability_refs": ["capability:m133:supervisor-review"],
        "allowlist_refs": ["allowlist:m133:safe-supervisor-refs-only"],
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "m131_work_session_decision_ref": "mode4-scoped-work-session-decision:m131:review",
        "supervisor_plan_ref": "supervisor-plan:m133:review-only",
        "task_ref": "task:m133:long-running-review",
        "run_state_ref": "run-state:m133:declared",
        "heartbeat_plan_ref": "heartbeat-plan:m133:no-runtime",
        "checkpoint_plan_ref": "checkpoint-plan:m133:no-scheduler",
        "checkpoint_refs": [
            "checkpoint:m133:declared-start",
            "checkpoint:m133:declared-review",
        ],
        "context_budget_ref": "context-budget:m133:bounded",
        "pause_condition_refs": ["pause-condition:m133:owner-requested"],
        "resume_condition_refs": ["resume-condition:m133:owner-reviewed"],
        "stop_condition_refs": [
            "stop-condition:m133:revoked",
            "stop-condition:m133:window-expired",
        ],
        "policy_decision_ref": "policy-decision:m133:mode5-supervisor",
        "risk_decision_ref": "risk-decision:m133:low-only",
        "audit_ref": "audit:m133:supervisor-review",
        "replay_ref": "replay:m133:supervisor-review",
        "revocation_ref": "revocation:m133:supervisor-review",
        "kill_switch_ref": "kill-switch:m133:supervisor-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m133:supervisor:no-effect",
        "max_supervisor_window_seconds": M133_MAX_SUPERVISOR_WINDOW_SECONDS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_task_summary": (
            "Review a long-running task supervisor contract without starting it."
        ),
    }
    data.update(overrides)
    return LongRunningTaskSupervisorRequest(**data)


def test_m133_long_running_task_supervisor_is_review_only_and_route_free() -> None:
    decision = build_long_running_task_supervisor_decision(_request())

    assert decision.status == LongRunningTaskSupervisorStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.long_running_supervisor_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m132_trusted_workflow_bound is True
    assert decision.m131_work_session_bound is True
    assert decision.supervisor_plan_bound is True
    assert decision.task_state_bound is True
    assert decision.heartbeat_plan_bound is True
    assert decision.checkpoint_plan_bound is True
    assert decision.context_budget_bound is True
    assert decision.pause_resume_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.max_supervisor_window_seconds == M133_MAX_SUPERVISOR_WINDOW_SECONDS
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.mode5_runtime_authorized is False
    assert decision.supervisor_runtime_authorized is False
    assert decision.long_running_supervisor_start_authorized is False
    assert decision.supervisor_started is False
    assert decision.task_supervision_active is False
    assert decision.heartbeat_monitor_started is False
    assert decision.checkpoint_scheduler_started is False
    assert decision.resume_execution_performed is False
    assert decision.recovery_execution_performed is False
    assert decision.human_checkpoint_scheduling_performed is False
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
    assert decision.reason_codes == [
        "M133_LONG_RUNNING_TASK_SUPERVISOR_CONTRACT_ONLY",
        "M133_EXACT_SUPERVISOR_SCOPE_REQUIRED",
        "M133_HEARTBEAT_AND_CHECKPOINT_REFS_REQUIRED",
        "M133_NO_SUPERVISOR_RUNTIME",
        "M134_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M133_MODE5_RUNTIME_DENIED"),
        ("supervisor_runtime_enabled", "M133_SUPERVISOR_RUNTIME_DENIED"),
        ("long_running_supervisor_start_enabled", "M133_SUPERVISOR_START_DENIED"),
        ("task_supervision_enabled", "M133_TASK_SUPERVISION_DENIED"),
        ("heartbeat_monitor_enabled", "M133_HEARTBEAT_MONITOR_DENIED"),
        ("checkpoint_scheduler_enabled", "M133_CHECKPOINT_SCHEDULER_DENIED"),
        ("resume_execution_enabled", "M133_RESUME_EXECUTION_DENIED"),
        ("recovery_execution_enabled", "M135_RECOVERY_EXECUTION_DENIED"),
        (
            "human_checkpoint_scheduling_enabled",
            "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
        ),
        ("scheduler_enabled", "M133_SCHEDULER_DENIED"),
        ("background_worker_enabled", "M133_BACKGROUND_WORKER_DENIED"),
        ("autonomous_actions_enabled", "M133_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M133_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M133_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M133_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M133_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M133_BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "M133_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M133_CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "M133_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M133_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M133_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M133_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M133_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M133_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M133_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M133_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m133_policy_denies_supervisor_runtime_and_future_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_long_running_task_supervisor_policy(
            LongRunningTaskSupervisorPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M133_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M133_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M133_RESOURCE_REF_REQUIRED"),
        ({"resource_refs": ["resource:m133:a", "resource:m133:a"]}, "M133_REF_DUPLICATE"),
        ({"capability_refs": []}, "M133_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M133_ALLOWLIST_REF_REQUIRED"),
        ({"checkpoint_refs": []}, "M133_CHECKPOINT_REF_REQUIRED"),
        (
            {"checkpoint_refs": [f"checkpoint:m133:{index}" for index in range(M133_MAX_CHECKPOINT_REFS + 1)]},
            "M133_REF_LIST_TOO_LONG",
        ),
        ({"pause_condition_refs": []}, "M133_PAUSE_CONDITION_REF_REQUIRED"),
        ({"resume_condition_refs": []}, "M133_RESUME_CONDITION_REF_REQUIRED"),
        ({"stop_condition_refs": []}, "M133_STOP_CONDITION_REF_REQUIRED"),
        ({"max_supervisor_window_seconds": M133_MAX_SUPERVISOR_WINDOW_SECONDS + 1}, "less than or equal"),
        ({"mode5_runtime_requested": True}, "M133_MODE5_RUNTIME_DENIED"),
        ({"supervisor_runtime_requested": True}, "M133_SUPERVISOR_RUNTIME_DENIED"),
        (
            {"long_running_supervisor_start_requested": True},
            "M133_SUPERVISOR_START_DENIED",
        ),
        ({"task_supervision_requested": True}, "M133_TASK_SUPERVISION_DENIED"),
        ({"heartbeat_monitor_requested": True}, "M133_HEARTBEAT_MONITOR_DENIED"),
        (
            {"checkpoint_scheduler_requested": True},
            "M133_CHECKPOINT_SCHEDULER_DENIED",
        ),
        ({"resume_execution_requested": True}, "M133_RESUME_EXECUTION_DENIED"),
        ({"recovery_execution_requested": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        (
            {"human_checkpoint_scheduling_requested": True},
            "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
        ),
        ({"scheduler_requested": True}, "M133_SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "M133_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_requested": True}, "M133_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M133_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M133_TOOL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "M133_BROWSER_AUTOMATION_DENIED"),
        ({"production_authority_requested": True}, "M133_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_prompt": True}, "M133_RAW_PROMPT_DENIED"),
        ({"contains_secret": True}, "M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED"),
    ],
)
def test_m133_request_denies_unsafe_or_unbounded_scope(override: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        build_long_running_task_supervisor_decision(_request(**override))


def test_m133_revalidates_model_copy_mutations_and_receipt_binding() -> None:
    decision = build_long_running_task_supervisor_decision(_request())

    for update, reason in [
        ({"contract_only": False}, "M133_CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M133_REVIEW_ONLY_REQUIRED"),
        ({"exact_scope_bound": False}, "M133_EXACT_SCOPE_REQUIRED"),
        ({"mode5_runtime_authorized": True}, "M133_MODE5_RUNTIME_DENIED"),
        ({"supervisor_runtime_authorized": True}, "M133_SUPERVISOR_RUNTIME_DENIED"),
        ({"long_running_supervisor_start_authorized": True}, "M133_SUPERVISOR_START_DENIED"),
        ({"supervisor_started": True}, "M133_SUPERVISOR_START_DENIED"),
        ({"task_supervision_active": True}, "M133_TASK_SUPERVISION_DENIED"),
        ({"heartbeat_monitor_started": True}, "M133_HEARTBEAT_MONITOR_DENIED"),
        ({"checkpoint_scheduler_started": True}, "M133_CHECKPOINT_SCHEDULER_DENIED"),
        ({"resume_execution_performed": True}, "M133_RESUME_EXECUTION_DENIED"),
        ({"recovery_execution_performed": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        (
            {"human_checkpoint_scheduling_performed": True},
            "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
        ),
        ({"scheduler_started": True}, "M133_SCHEDULER_DENIED"),
        ({"background_worker_started": True}, "M133_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_performed": True}, "M133_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_performed": True}, "M133_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M133_TOOL_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "M133_BACKEND_ROUTE_DENIED"),
        ({"production_authority_granted": True}, "M133_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["started supervisor"]}, "M133_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_long_running_task_supervisor_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="M133_RECEIPT_BINDING_MISMATCH"):
        validate_long_running_task_supervisor_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"scope_ref": "scope:m133:other"}
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="M133_RAW_PROMPT_DENIED"):
        validate_long_running_task_supervisor_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_prompt": True}
                    )
                }
            )
        )


def test_m133_denies_secret_like_metadata_on_request_policy_and_decision() -> None:
    with pytest.raises(ValueError, match="M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED"):
        validate_long_running_task_supervisor_request(
            _request(metadata={"connector_token": "abc123supersecret"})
        )

    with pytest.raises(ValueError, match="M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED"):
        validate_long_running_task_supervisor_policy(
            LongRunningTaskSupervisorPolicy(metadata={"api_key": "abc123supersecret"})
        )

    decision = build_long_running_task_supervisor_decision(_request())
    with pytest.raises(ValueError, match="M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED"):
        validate_long_running_task_supervisor_decision(
            decision.model_copy(update={"metadata": {"oauth_token": "abc123supersecret"}})
        )
