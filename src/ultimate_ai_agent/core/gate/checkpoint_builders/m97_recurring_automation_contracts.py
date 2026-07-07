from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.recurring_automation_contracts import (
    RecurringAutomationCadence,
    RecurringAutomationContractRequest,
    RecurringAutomationContractStatus,
    RecurringAutomationPolicy,
    build_recurring_automation_contract_decision,
    validate_recurring_automation_contract_decision,
    validate_recurring_automation_policy,
    validate_recurring_automation_request,
)


def _cadence(**overrides: Any) -> Any:
    data = {
        "cadence_ref": "recurring-cadence:m97-weekly-review",
        "cadence_label": "weekly-review",
        "minimum_interval_seconds": 604800,
        "max_occurrences": 4,
        "jitter_policy_ref": "jitter-policy:m97-none",
        "time_window_ref": "time-window:m97-business-hours",
    }
    data.update(overrides)
    return RecurringAutomationCadence(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "recurring-automation-request:m97-safe",
        "actor_ref": "actor:m97-reviewer",
        "scope_ref": "scope:m97-read-only-review",
        "resource_ref": "resource:m97-safe-summary",
        "action_ref": "action:m97-propose-recurring-review",
        "session_ref": "autonomy-session:m97-contract-only",
        "cadence": _cadence(),
        "approval_bundle_ref": "approval-bundle:m97-renewal-required",
        "renewal_policy_ref": "renewal-policy:m97-expiring-review",
        "expiration_ref": "expiration:m97-required",
        "stop_condition_refs": [
            "stop-condition:m97-user-revoked",
            "stop-condition:m97-expired",
        ],
        "audit_ref": "audit:m97-recurring-contract",
        "revocation_ref": "revocation:m97-recurring-contract",
        "safe_purpose": "Define a recurring automation contract only; do not run it.",
    }
    data.update(overrides)
    return RecurringAutomationContractRequest(**data)
