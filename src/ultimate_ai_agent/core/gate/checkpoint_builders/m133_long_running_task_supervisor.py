from __future__ import annotations
from typing import Any
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
