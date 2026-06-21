from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyRiskClass,
    LowRiskAutonomousDryRunRequest,
    LowRiskAutonomousDryRunStep,
    build_low_risk_autonomous_dry_run_record,
    validate_low_risk_autonomous_dry_run_record,
)

from tests.test_m68_autonomy_risk_classifier import _decision as _risk_decision
from tests.test_m68_autonomy_risk_classifier import _request as _risk_request


def _step(**overrides: Any) -> Any:
    data = {
        "step_ref": "low-risk-dry-run-step:m69-inspect-redacted-review",
        "intent_ref": "intent:inspect-redacted-review-packet",
        "capability_ref": "capability:observe-only-review",
        "resource_ref": "resource:local-prototype",
        "risk_class": AutonomyRiskClass.low,
        "dry_run_outcome_ref": "dry-run-outcome:m69-review-only",
    }
    data.update(overrides)
    return LowRiskAutonomousDryRunStep(**data)


def _request(**overrides: Any) -> Any:
    risk_decision = overrides.pop("risk_decision", _risk_decision())
    data = {
        "dry_run_request_ref": "low-risk-autonomous-dry-run-request:m69-local-review",
        "risk_decision": risk_decision,
        "risk_decision_ref": risk_decision.decision_ref,
        "actor_ref": risk_decision.actor_ref,
        "resource_refs": list(risk_decision.resource_refs),
        "capability_refs": list(risk_decision.capability_refs),
        "allowlist_refs": list(risk_decision.allowlist_refs),
        "bundle_ref": risk_decision.bundle_ref,
        "revocation_record_ref": risk_decision.revocation_record_ref,
        "source_scope_ref": risk_decision.source_scope_ref,
        "audit_ref": risk_decision.audit_ref,
        "replay_ref": risk_decision.replay_ref,
        "steps": [_step()],
    }
    data.update(overrides)
    return LowRiskAutonomousDryRunRequest(**data)


def _record(**overrides: Any) -> Any:
    request = overrides.pop("dry_run_request", _request())
    record = build_low_risk_autonomous_dry_run_record(request)
    if overrides:
        return record.model_copy(update=overrides)
    return record


def test_low_risk_autonomous_dry_run_is_review_only_and_non_authoritative() -> None:
    record = _record()

    assert record.dry_run_valid_for_review is True
    assert record.review_only is True
    assert record.dry_run_only is True
    assert record.low_risk_only is True
    assert record.deterministic is True
    assert record.derived_risk_class == AutonomyRiskClass.low
    assert record.authority_granted is False
    assert record.policy_activation_requested is False
    assert record.session_start_requested is False
    assert record.autonomous_actions_enabled is False
    assert record.background_worker_enabled is False
    assert record.execution_requested is False
    assert record.execution_performed is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M69_LOW_RISK_AUTONOMOUS_DRY_RUN_REVIEW_ONLY",
        "M69_LOW_RISK_ONLY",
        "M69_DRY_RUN_NO_AUTHORITY",
    ]


@pytest.mark.parametrize(
    "risk_class",
    [AutonomyRiskClass.medium, AutonomyRiskClass.high, AutonomyRiskClass.critical],
)
def test_low_risk_autonomous_dry_run_denies_non_low_risk_decisions(
    risk_class: AutonomyRiskClass,
) -> None:
    decision = _risk_decision(
        classification_request=_risk_request(
            declared_risk_class=risk_class,
        )
    )

    with pytest.raises(ValueError, match="LOW_RISK_DRY_RUN_RISK_CEILING_DENIED"):
        build_low_risk_autonomous_dry_run_record(_request(risk_decision=decision))


def test_low_risk_autonomous_dry_run_denies_step_risk_above_low() -> None:
    with pytest.raises(ValueError, match="LOW_RISK_DRY_RUN_STEP_RISK_DENIED"):
        build_low_risk_autonomous_dry_run_record(
            _request(steps=[_step(risk_class=AutonomyRiskClass.medium)])
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority_granted", "LOW_RISK_DRY_RUN_AUTHORITY_DENIED"),
        ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
        ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("execution_performed", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_low_risk_autonomous_dry_run_denies_authority_and_execution_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_low_risk_autonomous_dry_run_record(_record(**{field: True}))


def test_low_risk_autonomous_dry_run_denies_binding_drift_test_refs_and_secret_metadata() -> None:
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m69"}, "APPROVAL_TEST_REF_DENIED"),
        ({"risk_decision_ref": "autonomy-risk-classification-decision:other"}, "LOW_RISK_DRY_RUN_RISK_DECISION_BINDING_MISMATCH_DENIED"),
        ({"actor_ref": "actor:other-reviewer"}, "LOW_RISK_DRY_RUN_ACTOR_BINDING_MISMATCH_DENIED"),
        ({"resource_refs": ["resource:other"]}, "LOW_RISK_DRY_RUN_RESOURCE_BINDING_MISMATCH_DENIED"),
        ({"capability_refs": ["capability:other"]}, "LOW_RISK_DRY_RUN_CAPABILITY_BINDING_MISMATCH_DENIED"),
        ({"allowlist_refs": ["allowlist:other"]}, "LOW_RISK_DRY_RUN_ALLOWLIST_BINDING_MISMATCH_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_low_risk_autonomous_dry_run_record(_record().model_copy(update=update))


def test_low_risk_autonomous_dry_run_revalidates_model_copy_mutated_risk_decision() -> None:
    higher_risk_decision = _risk_decision().model_copy(
        update={"derived_risk_class": AutonomyRiskClass.medium}
    )

    with pytest.raises(ValueError, match="AUTONOMY_RISK_CLASSIFICATION_DRIFT_DENIED"):
        build_low_risk_autonomous_dry_run_record(_request(risk_decision=higher_risk_decision))


def test_low_risk_autonomous_dry_run_denies_side_effects_and_step_authority() -> None:
    with pytest.raises(ValueError, match="AUTONOMY_SIDE_EFFECTS_DENIED"):
        validate_low_risk_autonomous_dry_run_record(
            _record(side_effects_performed=["dry-run:persisted"])
        )

    with pytest.raises(ValueError, match="LOW_RISK_DRY_RUN_STEP_AUTHORITY_DENIED"):
        build_low_risk_autonomous_dry_run_record(_request(steps=[_step(authority_granted=True)]))
