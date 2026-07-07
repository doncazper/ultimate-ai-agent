from __future__ import annotations
from typing import Any
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
