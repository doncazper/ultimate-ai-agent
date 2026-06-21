from typing import Any
from importlib import import_module

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)
from ultimate_ai_agent.core.production_readiness import (
    build_account_connector_contract_review_record,
    build_production_threat_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _production_readiness() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.production_readiness")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M115 production_readiness package missing: {exc}")


def _source_record() -> Any:
    return build_account_connector_contract_review_record(
        source_record=build_secrets_boundary_record(
            source_record=build_user_workspace_identity_record(
                source_record=build_production_threat_model_record(
                    source_record=build_mobile_sensor_hardening_freeze_record(
                        source_record=build_mobile_sensor_audit_ledger_record(
                            source_record=build_mobile_kill_switch_revocation_record(
                                source_report=build_mobile_approval_renewal_ux_report()
                            )
                        )
                    )
                )
            )
        )
    )


def test_m115_audit_retention_policy_is_contract_only_and_non_authoritative() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()
    record = production_readiness.build_production_audit_retention_policy_record(
        source_record=source_record
    )

    assert (
        record.status
        == production_readiness.ProductionAuditRetentionPolicyStatus.retention_policy
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_account_connector_review_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.retention_schedule_bound is True
    assert record.redaction_boundary_bound is True
    assert record.deletion_window_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_account_connector_review_ref
        == source_record.account_connector_review_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
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
        "checkpoint:m111",
        "checkpoint:m112",
        "checkpoint:m113",
        "checkpoint:m114",
    ]
    assert record.retention_policy_refs
    assert record.retention_schedule_refs
    assert record.audit_data_class_refs
    assert record.redaction_policy_ref.startswith("redaction-policy-ref:")
    assert record.deletion_window_ref.startswith("deletion-window-ref:")
    assert record.legal_hold_boundary_ref.startswith("legal-hold-boundary-ref:")
    assert record.production_authority_enabled is False
    assert record.production_runtime_enabled is False
    assert record.audit_runtime_enabled is False
    assert record.audit_store_enabled is False
    assert record.audit_export_enabled is False
    assert record.raw_log_storage_enabled is False
    assert record.raw_prompt_storage_enabled is False
    assert record.raw_provider_payload_storage_enabled is False
    assert record.secret_storage_enabled is False
    assert record.external_saas_export_enabled is False
    assert record.network_delivery_enabled is False
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
        "M115_PRODUCTION_AUDIT_RETENTION_POLICY",
        "M115_CONTRACT_ONLY",
        "M115_REVIEW_ONLY",
        "M115_NO_AUDIT_RUNTIME_OR_EXPORT",
        "M116_REMAINS_FUTURE",
    ]


def test_m115_audit_retention_policy_uses_safe_refs_only() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_audit_retention_policy_record(
        source_record=_source_record()
    )

    assert record.audit_retention_policy_ref == "audit-retention-policy:m115"
    assert record.source_account_connector_review_ref == "account-connector-review:m114"
    assert record.retention_policy_refs == [
        "retention-policy-ref:m115:redacted-audit-minimum",
        "retention-policy-ref:m115:no-raw-log-retention",
        "retention-policy-ref:m115:no-external-delivery",
    ]
    assert record.retention_schedule_refs == [
        "retention-schedule-ref:m115:declared-safe-metadata-only",
        "retention-schedule-ref:m115:review-required-before-runtime",
    ]
    assert record.audit_data_class_refs == [
        "audit-data-class-ref:m115:safe-event-metadata",
        "audit-data-class-ref:m115:redacted-receipt-summary",
    ]
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "raw prompt",
        "raw provider payload",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
        ("audit_runtime_enabled", "AUDIT_RUNTIME_DENIED"),
        ("audit_store_enabled", "AUDIT_STORE_DENIED"),
        ("audit_export_enabled", "AUDIT_EXPORT_DENIED"),
        ("raw_log_storage_enabled", "RAW_LOG_STORAGE_DENIED"),
        ("raw_prompt_storage_enabled", "RAW_PROMPT_STORAGE_DENIED"),
        (
            "raw_provider_payload_storage_enabled",
            "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED",
        ),
        ("secret_storage_enabled", "SECRET_STORAGE_DENIED"),
        ("external_saas_export_enabled", "EXTERNAL_SAAS_EXPORT_DENIED"),
        ("network_delivery_enabled", "NETWORK_DELIVERY_DENIED"),
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
def test_m115_policy_denies_audit_runtime_and_export_authority(
    field: str, reason: str
) -> None:
    production_readiness = _production_readiness()
    with pytest.raises(ValueError, match=reason):
        production_readiness.validate_production_audit_retention_policy(
            production_readiness.ProductionAuditRetentionPolicy(**{field: True})
        )


def test_m115_record_denies_model_copy_authority_flags() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_audit_retention_policy_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M115_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M115_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M115_ACTOR_BINDING_REQUIRED"),
        ({"baseline_bound": False}, "M115_BASELINE_BINDING_REQUIRED"),
        (
            {"source_account_connector_review_bound": False},
            "M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_BINDING_REQUIRED",
        ),
        ({"user_bound": False}, "M115_USER_BINDING_REQUIRED"),
        ({"workspace_bound": False}, "M115_WORKSPACE_BINDING_REQUIRED"),
        (
            {"retention_schedule_bound": False},
            "M115_RETENTION_SCHEDULE_BINDING_REQUIRED",
        ),
        (
            {"redaction_boundary_bound": False},
            "M115_REDACTION_BOUNDARY_BINDING_REQUIRED",
        ),
        (
            {"deletion_window_bound": False},
            "M115_DELETION_WINDOW_BINDING_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M115_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"retention_policy_refs": []}, "M115_RETENTION_POLICY_REF_REQUIRED"),
        ({"retention_schedule_refs": []}, "M115_RETENTION_SCHEDULE_REF_REQUIRED"),
        ({"audit_data_class_refs": []}, "M115_AUDIT_DATA_CLASS_REF_REQUIRED"),
        ({"redaction_policy_ref": ""}, "M115_REDACTION_POLICY_REF_REQUIRED"),
        ({"deletion_window_ref": ""}, "M115_DELETION_WINDOW_REF_REQUIRED"),
        (
            {"legal_hold_boundary_ref": ""},
            "M115_LEGAL_HOLD_BOUNDARY_REF_REQUIRED",
        ),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
        ({"audit_runtime_enabled": True}, "AUDIT_RUNTIME_DENIED"),
        ({"audit_store_enabled": True}, "AUDIT_STORE_DENIED"),
        ({"audit_export_enabled": True}, "AUDIT_EXPORT_DENIED"),
        ({"raw_log_storage_enabled": True}, "RAW_LOG_STORAGE_DENIED"),
        ({"raw_prompt_storage_enabled": True}, "RAW_PROMPT_STORAGE_DENIED"),
        (
            {"raw_provider_payload_storage_enabled": True},
            "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED",
        ),
        ({"secret_storage_enabled": True}, "SECRET_STORAGE_DENIED"),
        ({"external_saas_export_enabled": True}, "EXTERNAL_SAAS_EXPORT_DENIED"),
        ({"network_delivery_enabled": True}, "NETWORK_DELIVERY_DENIED"),
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
        ({"side_effects_performed": ["export audit logs"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_audit_retention_policy_record(
                record.model_copy(update=update)
            )


def test_m115_record_denies_binding_drift_and_secret_metadata() -> None:
    production_readiness = _production_readiness()
    record = production_readiness.build_production_audit_retention_policy_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_account_connector_review_ref": "account-connector-review:other"},
            "M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline:other"}, "M115_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M115_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M115_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M115_WORKSPACE_BINDING_MISMATCH"),
        (
            {"audit_retention_policy_ref": "audit-retention-policy:other"},
            "M115_AUDIT_RETENTION_POLICY_REF_REQUIRED",
        ),
        (
            {"retention_policy_refs": ["retention-policy:m115"]},
            "M115_RETENTION_POLICY_REF_REQUIRED",
        ),
        (
            {"retention_schedule_refs": ["retention-schedule:m115"]},
            "M115_RETENTION_SCHEDULE_REF_REQUIRED",
        ),
        (
            {"audit_data_class_refs": ["audit-data-class:m115"]},
            "M115_AUDIT_DATA_CLASS_REF_REQUIRED",
        ),
        (
            {"redaction_policy_ref": "redaction-policy:m115"},
            "M115_REDACTION_POLICY_REF_REQUIRED",
        ),
        (
            {"deletion_window_ref": "deletion-window:m115"},
            "M115_DELETION_WINDOW_REF_REQUIRED",
        ),
        (
            {"legal_hold_boundary_ref": "legal-hold-boundary:m115"},
            "M115_LEGAL_HOLD_BOUNDARY_REF_REQUIRED",
        ),
        (
            {"no_effect_receipt_plan_ref": "receipt:m115"},
            "M115_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED",
        ),
        (
            {"metadata": {"authorization": "Bearer abc123supersecret"}},
            "SECRET_LIKE_M115_AUDIT_RETENTION_CONTENT_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            production_readiness.validate_production_audit_retention_policy_record(
                record.model_copy(update=update)
            )


def test_m115_requires_safe_source_account_connector_record() -> None:
    production_readiness = _production_readiness()
    source_record = _source_record()

    with pytest.raises(ValueError, match="ACCOUNT_ACTION_DENIED"):
        production_readiness.build_production_audit_retention_policy_record(
            source_record=source_record.model_copy(
                update={"account_action_enabled": True}
            )
        )
