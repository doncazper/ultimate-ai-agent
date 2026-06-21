from typing import Any
import pytest

from ultimate_ai_agent.core.scoped_recurring_low_risk_automation import (
    ScopedRecurringLowRiskAutomationCadence,
    ScopedRecurringLowRiskAutomationPolicy,
    ScopedRecurringLowRiskAutomationRequest,
    ScopedRecurringLowRiskAutomationStatus,
    build_scoped_recurring_low_risk_automation_decision,
    validate_scoped_recurring_low_risk_automation_decision,
    validate_scoped_recurring_low_risk_automation_policy,
    validate_scoped_recurring_low_risk_automation_request,
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


def test_scoped_recurring_low_risk_automation_builds_review_ready_decision() -> None:
    decision = build_scoped_recurring_low_risk_automation_decision(_request())

    assert decision.status == ScopedRecurringLowRiskAutomationStatus.scoped_low_risk_ready_for_review
    assert decision.low_risk_only is True
    assert decision.read_only_only is True
    assert decision.strict_cadence_required is True
    assert decision.renewal_required is True
    assert decision.renewal_not_expired is True
    assert decision.stop_conditions_required is True
    assert decision.audit_required is True
    assert decision.revocation_required is True
    assert decision.kill_switch_required is True
    assert decision.kill_switch_available is True
    assert decision.no_secret_access is True
    assert decision.runtime_started is False
    assert decision.scheduler_enabled is False
    assert decision.background_worker_enabled is False
    assert decision.recurring_execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_payload is False
    assert decision.receipt_plan.secret_access_performed is False
    assert decision.reason_codes == [
        "M98_SCOPED_RECURRING_LOW_RISK_READY_FOR_REVIEW",
        "LOW_RISK_READ_ONLY_ONLY",
        "STRICT_CADENCE_REQUIRED",
        "RENEWAL_ACTIVE",
        "STOP_CONDITIONS_REQUIRED",
        "KILL_SWITCH_READY",
        "AUDIT_TRAIL_REQUIRED",
        "NO_RUNTIME_SCHEDULER_OR_WORKER",
        "M99_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"approval_ref": "approval:m98-alone"}, "APPROVAL_REF_NOT_RECURRING_AUTONOMY_AUTHORITY"),
        ({"approval_test_ref": "approval_test_m98"}, "APPROVAL_TEST_REF_DENIED"),
        ({"authority_refs": ["approval:m98"]}, "AUTHORITY_REF_NOT_RECURRING_AUTONOMY_AUTHORITY"),
        ({"stop_condition_refs": []}, "STOP_CONDITION_REQUIRED"),
        ({"kill_switch_ref": ""}, "SAFE_REF_REQUIRED"),
        ({"renewal_expired": True}, "RENEWAL_EXPIRED_DENIED"),
        ({"revoked": True}, "REVOCATION_DENIED"),
        ({"kill_switch_available": False}, "KILL_SWITCH_REQUIRED"),
        ({"mutating_task_requested": True}, "MUTATING_TASK_DENIED"),
        ({"credential_access_requested": True}, "SECRET_ACCESS_DENIED"),
        ({"account_action_requested": True}, "ACCOUNT_ACTION_DENIED"),
        ({"shell_write_requested": True}, "SHELL_WRITE_DENIED"),
        ({"network_write_requested": True}, "NETWORK_WRITE_DENIED"),
        ({"browser_write_requested": True}, "BROWSER_WRITE_DENIED"),
        ({"silent_background_collection_requested": True}, "BACKGROUND_COLLECTION_DENIED"),
        ({"scheduler_requested": True}, "SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_scoped_recurring_low_risk_automation_denies_unsafe_requests(
    override: dict[str, object], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_scoped_recurring_low_risk_automation_decision(_request(**override))


def test_scoped_recurring_low_risk_automation_requires_strict_cadence() -> None:
    for cadence_update, reason in [
        ({"minimum_interval_seconds": 0}, "CADENCE_INTERVAL_TOO_SHORT"),
        ({"minimum_interval_seconds": 299}, "CADENCE_INTERVAL_TOO_SHORT"),
        ({"max_occurrences": 0}, "MAX_OCCURRENCES_REQUIRED"),
        ({"max_occurrences": 32}, "MAX_OCCURRENCES_TOO_HIGH"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_scoped_recurring_low_risk_automation_decision(
                _request(cadence=_cadence(**cadence_update))
            )


def test_scoped_recurring_low_risk_automation_policy_rejects_runtime_authority() -> None:
    for update, reason in [
        ({"low_risk_only": False}, "LOW_RISK_ONLY_REQUIRED"),
        ({"read_only_only": False}, "READ_ONLY_ONLY_REQUIRED"),
        ({"strict_cadence_required": False}, "STRICT_CADENCE_REQUIRED"),
        ({"renewal_required": False}, "RENEWAL_REQUIRED"),
        ({"kill_switch_required": False}, "KILL_SWITCH_REQUIRED"),
        ({"scheduler_allowed": True}, "SCHEDULER_DENIED"),
        ({"background_worker_allowed": True}, "BACKGROUND_WORKER_DENIED"),
        ({"mutating_tasks_allowed": True}, "MUTATING_TASK_DENIED"),
        ({"secret_access_allowed": True}, "SECRET_ACCESS_DENIED"),
        ({"production_authority_allowed": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_recurring_low_risk_automation_policy(
                ScopedRecurringLowRiskAutomationPolicy(**update)
            )


def test_scoped_recurring_low_risk_automation_revalidates_model_copy_mutations() -> None:
    request = _request()

    for update, reason in [
        ({"approval_test_ref": "approval_test_m98"}, "APPROVAL_TEST_REF_DENIED"),
        ({"renewal_expired": True}, "RENEWAL_EXPIRED_DENIED"),
        ({"kill_switch_available": False}, "KILL_SWITCH_REQUIRED"),
        ({"credential_access_requested": True}, "SECRET_ACCESS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_recurring_low_risk_automation_request(request.model_copy(update=update))

    decision = build_scoped_recurring_low_risk_automation_decision(request)
    for update, reason in [
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"secret_access_performed": True}, "SECRET_ACCESS_DENIED"),
        ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_recurring_low_risk_automation_decision(
                decision.model_copy(update=update)
            )

    with pytest.raises(ValueError, match="RAW_PAYLOAD_DENIED"):
        validate_scoped_recurring_low_risk_automation_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_payload": True}
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="RECEIPT_PLAN_BINDING_MISMATCH"):
        validate_scoped_recurring_low_risk_automation_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"resource_ref": "resource:m98-different"}
                    )
                }
            )
        )
