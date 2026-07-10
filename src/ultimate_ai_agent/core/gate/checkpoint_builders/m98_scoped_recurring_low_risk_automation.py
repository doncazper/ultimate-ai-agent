from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.scoped_recurring_low_risk_automation import (
    ScopedRecurringLowRiskAutomationCadence,
    ScopedRecurringLowRiskAutomationRequest,
)


def _cadence(**overrides: Any) -> Any:
    data = {
        "cadence_ref": "scoped-recurring-cadence:m98-daily-review",
        "cadence_label": "daily-review",
        "minimum_interval_seconds": 86400,
        "max_occurrences": 7,
        "time_window_ref": "time-window:m98-business-hours",
        "renewal_expiration_ref": "renewal-expiration:m98-required",
    }
    data.update(overrides)
    return ScopedRecurringLowRiskAutomationCadence(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "scoped-recurring-low-risk-request:m98-safe",
        "actor_ref": "actor:m98-reviewer",
        "scope_ref": "scope:m98-single-resource",
        "resource_ref": "resource:m98-redacted-status-summary",
        "workflow_ref": "workflow:m98-receipt-summary-refresh",
        "action_ref": "action:m98-read-only-refresh",
        "cadence": _cadence(),
        "approval_bundle_ref": "approval-bundle:m98-exact-scope",
        "renewal_ref": "renewal:m98-active",
        "expiration_ref": "expiration:m98-required",
        "stop_condition_refs": [
            "stop-condition:m98-user-revoked",
            "stop-condition:m98-renewal-expired",
        ],
        "audit_ref": "audit:m98-recurring-low-risk",
        "revocation_ref": "revocation:m98-recurring-low-risk",
        "kill_switch_ref": "kill-switch:m98-ready",
        "safe_purpose": "Allow only scoped low-risk read-only recurrence for review.",
    }
    data.update(overrides)
    return ScopedRecurringLowRiskAutomationRequest(**data)
