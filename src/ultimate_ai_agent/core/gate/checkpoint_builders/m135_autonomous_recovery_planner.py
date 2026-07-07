from __future__ import annotations
from typing import Any
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
