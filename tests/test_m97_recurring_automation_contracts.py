from typing import Any
import pytest

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


def test_recurring_automation_contract_builds_disabled_contract_only_decision() -> None:
    decision = build_recurring_automation_contract_decision(_request())

    assert decision.status == RecurringAutomationContractStatus.contract_ready_disabled
    assert decision.capability_exists is True
    assert decision.disabled_by_default is True
    assert decision.contract_only is True
    assert decision.approval_renewal_required is True
    assert decision.expiration_required is True
    assert decision.stop_conditions_required is True
    assert decision.audit_required is True
    assert decision.revocation_required is True
    assert decision.recurrence_runtime_enabled is False
    assert decision.background_worker_enabled is False
    assert decision.cron_daemon_enabled is False
    assert decision.scheduler_enabled is False
    assert decision.side_effects_allowed is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_payload is False
    assert decision.receipt_plan.recurrence_runtime_started is False
    assert decision.receipt_plan.background_worker_started is False
    assert decision.reason_codes == [
        "M97_RECURRING_AUTOMATION_CONTRACT_READY_DISABLED",
        "CONTRACT_ONLY",
        "APPROVAL_RENEWAL_REQUIRED",
        "EXPIRATION_REQUIRED",
        "STOP_CONDITIONS_REQUIRED",
        "NO_RECURRENCE_RUNTIME",
        "NO_BACKGROUND_EXECUTION",
        "M98_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"approval_ref": "approval:m97-alone"}, "APPROVAL_REF_NOT_RECURRING_AUTOMATION_AUTHORITY"),
        ({"approval_test_ref": "approval_test_m97"}, "APPROVAL_TEST_REF_DENIED"),
        ({"authority_refs": ["approval:m97"]}, "AUTHORITY_REF_NOT_RECURRING_AUTOMATION_AUTHORITY"),
        ({"stop_condition_refs": []}, "STOP_CONDITION_REQUIRED"),
        ({"recurrence_runtime_requested": True}, "RECURRENCE_RUNTIME_DENIED"),
        ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
        ({"cron_daemon_requested": True}, "CRON_DAEMON_DENIED"),
        ({"scheduler_requested": True}, "SCHEDULER_DENIED"),
        ({"side_effect_requested": True}, "SIDE_EFFECTS_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_recurring_automation_contract_denies_authority_and_runtime_requests(
    override: dict[str, object], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_recurring_automation_contract_decision(_request(**override))


def test_recurring_automation_contract_requires_safe_cadence_bounds() -> None:
    for cadence_update, reason in [
        ({"minimum_interval_seconds": 0}, "CADENCE_INTERVAL_TOO_SHORT"),
        ({"minimum_interval_seconds": 30}, "CADENCE_INTERVAL_TOO_SHORT"),
        ({"max_occurrences": 0}, "MAX_OCCURRENCES_REQUIRED"),
        ({"max_occurrences": 101}, "MAX_OCCURRENCES_TOO_HIGH"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_recurring_automation_contract_decision(
                _request(cadence=_cadence(**cadence_update))
            )


def test_recurring_automation_policy_rejects_runtime_enablement() -> None:
    for update, reason in [
        ({"disabled_by_default": False}, "DISABLED_BY_DEFAULT_REQUIRED"),
        ({"approval_renewal_required": False}, "APPROVAL_RENEWAL_REQUIRED"),
        ({"expiration_required": False}, "EXPIRATION_REQUIRED"),
        ({"stop_conditions_required": False}, "STOP_CONDITIONS_REQUIRED"),
        ({"recurrence_runtime_allowed": True}, "RECURRENCE_RUNTIME_DENIED"),
        ({"background_worker_allowed": True}, "BACKGROUND_WORKER_DENIED"),
        ({"cron_daemon_allowed": True}, "CRON_DAEMON_DENIED"),
        ({"scheduler_allowed": True}, "SCHEDULER_DENIED"),
        ({"production_authority_allowed": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_recurring_automation_policy(RecurringAutomationPolicy(**update))


def test_recurring_automation_contract_revalidates_model_copy_mutations() -> None:
    request = _request()

    for update, reason in [
        ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
        ({"approval_test_ref": "approval_test_m97"}, "APPROVAL_TEST_REF_DENIED"),
        ({"stop_condition_refs": []}, "STOP_CONDITION_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_recurring_automation_request(request.model_copy(update=update))

    decision = build_recurring_automation_contract_decision(request)
    for update, reason in [
        ({"recurrence_runtime_enabled": True}, "RECURRENCE_RUNTIME_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_recurring_automation_contract_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="BACKGROUND_WORKER_DENIED"):
        validate_recurring_automation_contract_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"background_worker_started": True}
                    )
                }
            )
        )
