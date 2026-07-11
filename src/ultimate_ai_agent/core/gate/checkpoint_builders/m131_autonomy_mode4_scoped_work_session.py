from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    M131_MAX_WORK_SESSION_SECONDS,
    AutonomyRiskClass,
    Mode4ScopedWorkSessionRequest,
)


def _request(**overrides: Any) -> Any:
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
