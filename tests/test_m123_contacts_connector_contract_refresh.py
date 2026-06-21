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
    build_deployment_mode_matrix_record,
    build_production_audit_retention_policy_record,
    build_production_authority_readiness_review_record,
    build_production_red_team_harness_record,
    build_production_threat_model_record,
    build_remote_agent_coordination_contract_record,
    build_role_based_authority_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _connectors() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M123 connectors package missing: {exc}")


def _m120_source_record() -> Any:
    return build_production_authority_readiness_review_record(
        source_record=build_production_red_team_harness_record(
            source_record=build_deployment_mode_matrix_record(
                source_record=build_remote_agent_coordination_contract_record(
                    source_record=build_role_based_authority_model_record(
                        source_record=build_production_audit_retention_policy_record(
                            source_record=build_account_connector_contract_review_record(
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
                        )
                    )
                )
            )
        )
    )


def _source_record() -> Any:
    connectors = _connectors()
    return connectors.build_calendar_connector_contract_refresh_record(
        source_record=connectors.build_email_connector_contract_refresh_record(
            source_record=_m120_source_record()
        )
    )


def test_m123_contacts_connector_refresh_is_contract_only_and_safe_ref_bound() -> None:
    connectors = _connectors()
    source_record = _source_record()
    record = connectors.build_contacts_connector_contract_refresh_record(
        source_record=source_record
    )

    assert (
        record.status
        == connectors.ContactsConnectorContractRefreshStatus.contacts_connector_contract_refresh
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_calendar_connector_contract_refresh_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.contacts_scope_bound is True
    assert record.contacts_boundary_bound is True
    assert record.contact_boundary_bound is True
    assert record.consent_boundary_bound is True
    assert record.data_classification_bound is True
    assert record.retention_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_calendar_connector_contract_refresh_ref
        == source_record.calendar_connector_contract_refresh_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m122" in record.accepted_checkpoint_refs
    assert record.contacts_scope_refs
    assert record.contacts_boundary_refs
    assert record.contact_boundary_refs
    assert record.consent_boundary_refs
    assert record.data_classification_refs
    assert record.retention_boundary_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.contacts_connector_runtime_enabled is False
    assert record.contacts_account_auth_enabled is False
    assert record.contacts_read_enabled is False
    assert record.contacts_search_enabled is False
    assert record.contacts_lookup_enabled is False
    assert record.contacts_create_enabled is False
    assert record.contacts_update_enabled is False
    assert record.contacts_delete_enabled is False
    assert record.contacts_export_enabled is False
    assert record.contacts_bulk_export_enabled is False
    assert record.raw_contacts_content_enabled is False
    assert record.credential_handling_enabled is False
    assert record.network_access_enabled is False
    assert record.account_action_enabled is False
    assert record.model_call_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH",
        "M123_CONTRACT_ONLY",
        "M123_REVIEW_ONLY",
        "M123_NO_CONTACTS_RUNTIME_OR_ACCOUNT_AUTH",
        "M124_REMAINS_FUTURE",
    ]


def test_m123_contacts_connector_refresh_uses_safe_refs_only() -> None:
    connectors = _connectors()
    record = connectors.build_contacts_connector_contract_refresh_record(
        source_record=_source_record()
    )

    assert record.contacts_connector_contract_refresh_ref == (
        "contacts-connector-contract-refresh:m123"
    )
    assert record.source_calendar_connector_contract_refresh_ref == (
        "calendar-connector-contract-refresh:m122"
    )
    assert record.contacts_scope_refs == [
        "contacts-scope-ref:m123:declared-contacts-boundary",
        "contacts-scope-ref:m123:metadata-preview-only",
        "contacts-scope-ref:m123:no-account-action",
    ]
    assert record.contacts_boundary_refs
    assert record.contact_boundary_refs
    assert record.consent_boundary_refs
    assert record.data_classification_refs
    assert record.retention_boundary_refs
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "oauth token",
        "contacts password",
        "create contact",
        "delete contact",
        "bulk export",
        "read contacts",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("contacts_connector_runtime_enabled", "CONTACTS_CONNECTOR_RUNTIME_DENIED"),
        ("contacts_account_auth_enabled", "CONTACTS_ACCOUNT_AUTH_DENIED"),
        ("contacts_read_enabled", "CONTACTS_READ_DENIED"),
        ("contacts_search_enabled", "CONTACTS_SEARCH_DENIED"),
        ("contacts_lookup_enabled", "CONTACTS_LOOKUP_DENIED"),
        ("contacts_create_enabled", "CONTACTS_CREATE_DENIED"),
        ("contacts_update_enabled", "CONTACTS_UPDATE_DENIED"),
        ("contacts_delete_enabled", "CONTACTS_DELETE_DENIED"),
        ("contacts_export_enabled", "CONTACTS_EXPORT_DENIED"),
        ("contacts_bulk_export_enabled", "CONTACTS_BULK_EXPORT_DENIED"),
        ("raw_contacts_content_enabled", "RAW_CONTACTS_CONTENT_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m123_policy_denies_contacts_runtime_and_account_authority(
    field: str, reason: str
) -> None:
    connectors = _connectors()
    with pytest.raises(ValueError, match=reason):
        connectors.validate_contacts_connector_contract_refresh_policy(
            connectors.ContactsConnectorContractRefreshPolicy(**{field: True})
        )


def test_m123_record_denies_model_copy_authority_flags() -> None:
    connectors = _connectors()
    record = connectors.build_contacts_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M123_REVIEW_ONLY_REQUIRED"),
        ({"contacts_scope_refs": []}, "M123_CONTACTS_SCOPE_REF_REQUIRED"),
        ({"contacts_boundary_refs": []}, "M123_CONTACTS_BOUNDARY_REF_REQUIRED"),
        ({"contact_boundary_refs": []}, "M123_CONTACT_BOUNDARY_REF_REQUIRED"),
        ({"consent_boundary_refs": []}, "M123_CONSENT_BOUNDARY_REF_REQUIRED"),
        ({"contacts_connector_runtime_enabled": True}, "CONTACTS_CONNECTOR_RUNTIME_DENIED"),
        ({"contacts_account_auth_enabled": True}, "CONTACTS_ACCOUNT_AUTH_DENIED"),
        ({"contacts_read_enabled": True}, "CONTACTS_READ_DENIED"),
        ({"contacts_lookup_enabled": True}, "CONTACTS_LOOKUP_DENIED"),
        ({"contacts_create_enabled": True}, "CONTACTS_CREATE_DENIED"),
        ({"contacts_update_enabled": True}, "CONTACTS_UPDATE_DENIED"),
        ({"contacts_delete_enabled": True}, "CONTACTS_DELETE_DENIED"),
        ({"contacts_export_enabled": True}, "CONTACTS_EXPORT_DENIED"),
        ({"contacts_bulk_export_enabled": True}, "CONTACTS_BULK_EXPORT_DENIED"),
        ({"raw_contacts_content_enabled": True}, "RAW_CONTACTS_CONTENT_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"metadata": {"api_key": "sk-test"}}, "SECRET_LIKE_M123_CONTACTS_CONTENT_DENIED"),
        ({"side_effects_performed": ["contacts-read"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_contacts_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m123_requires_exact_source_and_binding_refs() -> None:
    connectors = _connectors()
    record = connectors.build_contacts_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_calendar_connector_contract_refresh_ref": "wrong-ref:m122"},
            "M123_SOURCE_CALENDAR_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline-ref:other"}, "M123_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor-ref:other"}, "M123_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M123_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M123_WORKSPACE_BINDING_MISMATCH"),
        (
            {"contacts_connector_contract_refresh_ref": "contacts-connector-contract-refresh:other"},
            "M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M123_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"accepted_checkpoint_refs": ["checkpoint:m120"]}, "M123_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_contacts_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m123_requires_safe_source_calendar_connector_refresh_record() -> None:
    connectors = _connectors()
    source_record = _source_record()
    unsafe_source = source_record.model_copy(update={"calendar_read_enabled": True})

    with pytest.raises(ValueError, match="CALENDAR_READ_DENIED"):
        connectors.build_contacts_connector_contract_refresh_record(source_record=unsafe_source)
