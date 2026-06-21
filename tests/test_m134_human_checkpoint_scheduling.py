from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    M134_MAX_CHECKPOINT_WINDOW_SECONDS,
    M134_MAX_REVIEWER_REFS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    HumanCheckpointSchedulingPolicy,
    HumanCheckpointSchedulingRequest,
    HumanCheckpointSchedulingStatus,
    build_human_checkpoint_scheduling_decision,
    validate_human_checkpoint_scheduling_decision,
    validate_human_checkpoint_scheduling_policy,
    validate_human_checkpoint_scheduling_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "human-checkpoint-scheduling-request:m134:review",
        "checkpoint_schedule_ref": "human-checkpoint-scheduling:m134:review",
        "mode_ref": "autonomy-mode:m134:mode5",
        "actor_ref": "actor:m134:reviewer",
        "user_ref": "user:m134:owner",
        "workspace_ref": "workspace:m134:local",
        "scope_ref": "scope:m134:single-workspace",
        "resource_refs": ["resource:m134:checkpoint-summary"],
        "capability_refs": ["capability:m134:checkpoint-scheduling-review"],
        "allowlist_refs": ["allowlist:m134:safe-checkpoint-refs-only"],
        "m133_supervisor_decision_ref": (
            "long-running-task-supervisor-decision:m133:review"
        ),
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "checkpoint_plan_ref": "checkpoint-plan:m134:declared",
        "schedule_plan_ref": "schedule-plan:m134:review-only",
        "checkpoint_window_ref": "checkpoint-window:m134:bounded",
        "reviewer_refs": [
            "reviewer:m134:owner",
            "reviewer:m134:safety-reviewer",
        ],
        "consent_ref": "consent:m134:declared",
        "expiration_ref": "expiration:m134:window",
        "reminder_plan_ref": "reminder-plan:m134:no-runtime",
        "escalation_plan_ref": "escalation-plan:m134:no-runtime",
        "pause_condition_refs": ["pause-condition:m134:revoked"],
        "stop_condition_refs": ["stop-condition:m134:expired"],
        "policy_decision_ref": "policy-decision:m134:mode5-checkpoint",
        "risk_decision_ref": "risk-decision:m134:low-only",
        "audit_ref": "audit:m134:checkpoint-review",
        "replay_ref": "replay:m134:checkpoint-review",
        "revocation_ref": "revocation:m134:checkpoint-review",
        "kill_switch_ref": "kill-switch:m134:checkpoint-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m134:checkpoint:no-effect",
        "max_checkpoint_window_seconds": M134_MAX_CHECKPOINT_WINDOW_SECONDS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_checkpoint_summary": (
            "Review a human checkpoint scheduling contract without scheduling it."
        ),
    }
    data.update(overrides)
    return HumanCheckpointSchedulingRequest(**data)


def test_m134_human_checkpoint_scheduling_is_review_only_and_route_free() -> None:
    decision = build_human_checkpoint_scheduling_decision(_request())

    assert decision.status == HumanCheckpointSchedulingStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.human_checkpoint_scheduling_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m133_supervisor_bound is True
    assert decision.m132_trusted_workflow_bound is True
    assert decision.checkpoint_plan_bound is True
    assert decision.schedule_plan_bound is True
    assert decision.checkpoint_window_bound is True
    assert decision.reviewer_bound is True
    assert decision.consent_bound is True
    assert decision.expiration_bound is True
    assert decision.reminder_plan_bound is True
    assert decision.escalation_plan_bound is True
    assert decision.pause_stop_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.max_checkpoint_window_seconds == M134_MAX_CHECKPOINT_WINDOW_SECONDS
    assert decision.max_risk_class == AutonomyRiskClass.low
    assert decision.mode5_runtime_authorized is False
    assert decision.human_checkpoint_scheduler_authorized is False
    assert decision.checkpoint_scheduled is False
    assert decision.human_checkpoint_prompt_sent is False
    assert decision.notification_delivered is False
    assert decision.reminder_runtime_started is False
    assert decision.calendar_written is False
    assert decision.approval_captured is False
    assert decision.escalation_runtime_started is False
    assert decision.supervisor_runtime_started is False
    assert decision.recovery_execution_performed is False
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
    assert decision.receipt_plan.checkpoint_scheduled is False
    assert decision.reason_codes == [
        "M134_HUMAN_CHECKPOINT_SCHEDULING_CONTRACT_ONLY",
        "M134_EXACT_CHECKPOINT_SCOPE_REQUIRED",
        "M134_HUMAN_REVIEWER_REFS_REQUIRED",
        "M134_NO_SCHEDULER_OR_PROMPT_RUNTIME",
        "M135_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M134_MODE5_RUNTIME_DENIED"),
        ("human_checkpoint_scheduler_enabled", "M134_CHECKPOINT_SCHEDULER_DENIED"),
        ("human_checkpoint_prompt_enabled", "M134_PROMPT_RUNTIME_DENIED"),
        ("notification_delivery_enabled", "M134_NOTIFICATION_DELIVERY_DENIED"),
        ("reminder_runtime_enabled", "M134_REMINDER_RUNTIME_DENIED"),
        ("calendar_write_enabled", "M134_CALENDAR_WRITE_DENIED"),
        ("approval_capture_enabled", "M134_APPROVAL_CAPTURE_DENIED"),
        ("escalation_runtime_enabled", "M134_ESCALATION_RUNTIME_DENIED"),
        ("supervisor_runtime_enabled", "M134_SUPERVISOR_RUNTIME_DENIED"),
        ("recovery_execution_enabled", "M135_RECOVERY_EXECUTION_DENIED"),
        ("scheduler_enabled", "M134_SCHEDULER_DENIED"),
        ("background_worker_enabled", "M134_BACKGROUND_WORKER_DENIED"),
        ("autonomous_actions_enabled", "M134_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M134_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M134_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M134_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M134_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M134_BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "M134_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M134_CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "M134_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M134_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M134_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M134_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M134_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M134_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M134_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M134_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m134_policy_denies_checkpoint_runtime_and_future_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_human_checkpoint_scheduling_policy(
            HumanCheckpointSchedulingPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M134_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M134_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M134_RESOURCE_REF_REQUIRED"),
        ({"resource_refs": ["resource:m134:a", "resource:m134:a"]}, "M134_REF_DUPLICATE"),
        ({"capability_refs": []}, "M134_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M134_ALLOWLIST_REF_REQUIRED"),
        ({"reviewer_refs": []}, "M134_REVIEWER_REF_REQUIRED"),
        (
            {
                "reviewer_refs": [
                    f"reviewer:m134:{index}"
                    for index in range(M134_MAX_REVIEWER_REFS + 1)
                ]
            },
            "M134_REF_LIST_TOO_LONG",
        ),
        ({"pause_condition_refs": []}, "M134_PAUSE_CONDITION_REF_REQUIRED"),
        ({"stop_condition_refs": []}, "M134_STOP_CONDITION_REF_REQUIRED"),
        (
            {"max_checkpoint_window_seconds": M134_MAX_CHECKPOINT_WINDOW_SECONDS + 1},
            "less than or equal",
        ),
        ({"mode5_runtime_requested": True}, "M134_MODE5_RUNTIME_DENIED"),
        (
            {"human_checkpoint_scheduler_requested": True},
            "M134_CHECKPOINT_SCHEDULER_DENIED",
        ),
        (
            {"human_checkpoint_prompt_requested": True},
            "M134_PROMPT_RUNTIME_DENIED",
        ),
        (
            {"notification_delivery_requested": True},
            "M134_NOTIFICATION_DELIVERY_DENIED",
        ),
        ({"reminder_runtime_requested": True}, "M134_REMINDER_RUNTIME_DENIED"),
        ({"calendar_write_requested": True}, "M134_CALENDAR_WRITE_DENIED"),
        ({"approval_capture_requested": True}, "M134_APPROVAL_CAPTURE_DENIED"),
        ({"escalation_runtime_requested": True}, "M134_ESCALATION_RUNTIME_DENIED"),
        ({"supervisor_runtime_requested": True}, "M134_SUPERVISOR_RUNTIME_DENIED"),
        ({"recovery_execution_requested": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        ({"scheduler_requested": True}, "M134_SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "M134_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_requested": True}, "M134_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M134_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M134_TOOL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "M134_BROWSER_AUTOMATION_DENIED"),
        ({"production_authority_requested": True}, "M134_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_prompt": True}, "M134_RAW_PROMPT_DENIED"),
        ({"contains_secret": True}, "M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED"),
    ],
)
def test_m134_request_denies_unsafe_or_unbounded_scope(override: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        build_human_checkpoint_scheduling_decision(_request(**override))


def test_m134_revalidates_model_copy_mutations_and_receipt_binding() -> None:
    decision = build_human_checkpoint_scheduling_decision(_request())

    for update, reason in [
        ({"contract_only": False}, "M134_CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M134_REVIEW_ONLY_REQUIRED"),
        ({"exact_scope_bound": False}, "M134_EXACT_SCOPE_REQUIRED"),
        ({"mode5_runtime_authorized": True}, "M134_MODE5_RUNTIME_DENIED"),
        (
            {"human_checkpoint_scheduler_authorized": True},
            "M134_CHECKPOINT_SCHEDULER_DENIED",
        ),
        ({"checkpoint_scheduled": True}, "M134_CHECKPOINT_SCHEDULER_DENIED"),
        ({"human_checkpoint_prompt_sent": True}, "M134_PROMPT_RUNTIME_DENIED"),
        ({"notification_delivered": True}, "M134_NOTIFICATION_DELIVERY_DENIED"),
        ({"reminder_runtime_started": True}, "M134_REMINDER_RUNTIME_DENIED"),
        ({"calendar_written": True}, "M134_CALENDAR_WRITE_DENIED"),
        ({"approval_captured": True}, "M134_APPROVAL_CAPTURE_DENIED"),
        ({"escalation_runtime_started": True}, "M134_ESCALATION_RUNTIME_DENIED"),
        ({"supervisor_runtime_started": True}, "M134_SUPERVISOR_RUNTIME_DENIED"),
        ({"recovery_execution_performed": True}, "M135_RECOVERY_EXECUTION_DENIED"),
        ({"scheduler_started": True}, "M134_SCHEDULER_DENIED"),
        ({"background_worker_started": True}, "M134_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_performed": True}, "M134_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_performed": True}, "M134_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M134_TOOL_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "M134_BACKEND_ROUTE_DENIED"),
        ({"production_authority_granted": True}, "M134_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["scheduled checkpoint"]}, "M134_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_human_checkpoint_scheduling_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="M134_RECEIPT_BINDING_MISMATCH"):
        validate_human_checkpoint_scheduling_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"scope_ref": "scope:m134:other"}
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="M134_RAW_PROMPT_DENIED"):
        validate_human_checkpoint_scheduling_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_prompt": True}
                    )
                }
            )
        )


def test_m134_denies_secret_like_metadata_on_request_policy_and_decision() -> None:
    with pytest.raises(ValueError, match="M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED"):
        validate_human_checkpoint_scheduling_request(
            _request(metadata={"connector_token": "abc123supersecret"})
        )

    with pytest.raises(ValueError, match="M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED"):
        validate_human_checkpoint_scheduling_policy(
            HumanCheckpointSchedulingPolicy(metadata={"api_key": "abc123supersecret"})
        )

    decision = build_human_checkpoint_scheduling_decision(_request())
    with pytest.raises(ValueError, match="M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED"):
        validate_human_checkpoint_scheduling_decision(
            decision.model_copy(update={"metadata": {"oauth_token": "abc123supersecret"}})
        )
