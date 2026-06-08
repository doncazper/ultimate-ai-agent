from importlib import import_module

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)


def _production_readiness():
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M111 production_readiness package missing: {exc}")


def _source_record():
    return build_mobile_sensor_hardening_freeze_record(
        source_record=build_mobile_sensor_audit_ledger_record(
            source_record=build_mobile_kill_switch_revocation_record(
                source_report=build_mobile_approval_renewal_ux_report()
            )
        )
    )


def test_m111_production_threat_model_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_production_threat_model_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.ProductionThreatModelStatus.threat_model_contract
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_freeze_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_freeze_ref == source_record.freeze_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.accepted_checkpoint_refs == [
        "checkpoint:m101",
        "checkpoint:m102",
        "checkpoint:m103",
        "checkpoint:m104",
        "checkpoint:m105",
        "checkpoint:m106",
        "checkpoint:m107",
        "checkpoint:m108",
        "checkpoint:m109",
        "checkpoint:m110",
    ]
    assert record.threat_surface_refs
    assert record.mitigation_plan_refs
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.external_distribution_enabled is False
    assert record.deployment_enabled is False
    assert record.credential_handling_enabled is False
    assert record.network_access_enabled is False
    assert record.model_call_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.tool_execution_enabled is False
    assert record.shell_execution_enabled is False
    assert record.browser_automation_enabled is False
    assert record.plugin_execution_enabled is False
    assert record.mobile_sensor_enabled is False
    assert record.background_worker_enabled is False
    assert record.remote_execution_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M111_PRODUCTION_THREAT_MODEL",
        "M111_CONTRACT_ONLY",
        "M111_REVIEW_ONLY",
        "M111_NO_PRODUCTION_AUTHORITY",
        "M112_REMAINS_FUTURE",
    ]


def test_m111_production_threat_model_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_threat_model_record(
        source_record=_source_record()
    )

    assert record.threat_model_ref == "production-threat-model:m111"
    assert record.source_freeze_ref.startswith("mobile-sensor-hardening-freeze:")
    assert record.source_baseline_ref.startswith("baseline:")
    assert record.threat_surface_refs == [
        "threat-surface-ref:m111:production-runtime",
        "threat-surface-ref:m111:credential-boundary",
        "threat-surface-ref:m111:deployment-boundary",
    ]
    assert record.mitigation_plan_refs == [
        "mitigation-plan-ref:m111:no-production-authority",
        "mitigation-plan-ref:m111:no-credential-handling",
        "mitigation-plan-ref:m111:no-deployment-runtime",
    ]
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "credential value" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
        ("deployment_enabled", "DEPLOYMENT_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m111_policy_denies_production_authority(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_production_threat_model_policy(
            production_readiness.ProductionThreatModelPolicy(**{field: True})
        )


def test_m111_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_threat_model_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M111_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M111_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M111_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M111_BASELINE_BINDING_REQUIRED"),
        ({"source_freeze_bound": False}, "M111_SOURCE_FREEZE_BINDING_REQUIRED"),
        ({"accepted_checkpoint_refs": []}, "M111_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"threat_surface_refs": []}, "M111_THREAT_SURFACE_REF_REQUIRED"),
        ({"mitigation_plan_refs": []}, "M111_MITIGATION_PLAN_REF_REQUIRED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"external_distribution_enabled": True}, "EXTERNAL_DISTRIBUTION_DENIED"),
        ({"deployment_enabled": True}, "DEPLOYMENT_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"model_call_enabled": True}, "MODEL_CALL_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
        ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_enabled": True}, "PLUGIN_EXECUTION_DENIED"),
        ({"mobile_sensor_enabled": True}, "MOBILE_SENSOR_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"side_effects_performed": ["deploy to production"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_threat_model_record(
                record.model_copy(update=update)
            )


def test_m111_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_threat_model_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_freeze_ref": "mobile-sensor-hardening-freeze:other"},
            "M111_SOURCE_FREEZE_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M111_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M111_ACTOR_BINDING_MISMATCH"),
        ({"threat_model_ref": "threat-model:m111"}, "M111_THREAT_MODEL_REF_REQUIRED"),
        (
            {"threat_surface_refs": ["threat-surface:m111"]},
            "M111_THREAT_SURFACE_REF_REQUIRED",
        ),
        (
            {"mitigation_plan_refs": ["mitigation:m111"]},
            "M111_MITIGATION_PLAN_REF_REQUIRED",
        ),
        (
            {"no_effect_receipt_plan_ref": "receipt:m111"},
            "M111_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED",
        ),
        (
            {"metadata": {"production_token": "abc123supersecret"}},
            "SECRET_LIKE_M111_PRODUCTION_THREAT_MODEL_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_threat_model_record(
                record.model_copy(update=update)
            )


def test_m111_requires_safe_source_freeze_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record().model_copy(
        update={"production_authority_enabled": True}
    )

    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        production_readiness.build_production_threat_model_record(
            source_record=source_record
        )
