from __future__ import annotations
from typing import Any
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
