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
        pytest.fail(f"M122 connectors package missing: {exc}")


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
    return connectors.build_email_connector_contract_refresh_record(
        source_record=_m120_source_record()
    )


def test_m122_calendar_connector_refresh_is_contract_only_and_safe_ref_bound() -> None:
    connectors = _connectors()
    source_record = _source_record()
    record = connectors.build_calendar_connector_contract_refresh_record(
        source_record=source_record
    )

    assert (
        record.status
        == connectors.CalendarConnectorContractRefreshStatus.calendar_connector_contract_refresh
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_email_connector_contract_refresh_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.calendar_scope_bound is True
    assert record.calendar_boundary_bound is True
    assert record.event_boundary_bound is True
    assert record.consent_boundary_bound is True
    assert record.data_classification_bound is True
    assert record.retention_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_email_connector_contract_refresh_ref
        == source_record.email_connector_contract_refresh_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m121" in record.accepted_checkpoint_refs
    assert record.calendar_scope_refs
    assert record.calendar_boundary_refs
    assert record.event_boundary_refs
    assert record.consent_boundary_refs
    assert record.data_classification_refs
    assert record.retention_boundary_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.calendar_connector_runtime_enabled is False
    assert record.calendar_account_auth_enabled is False
    assert record.calendar_read_enabled is False
    assert record.calendar_search_enabled is False
    assert record.calendar_event_create_enabled is False
    assert record.calendar_event_update_enabled is False
    assert record.calendar_event_delete_enabled is False
    assert record.calendar_invite_send_enabled is False
    assert record.calendar_attachment_download_enabled is False
    assert record.raw_calendar_content_enabled is False
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
        "M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH",
        "M122_CONTRACT_ONLY",
        "M122_REVIEW_ONLY",
        "M122_NO_CALENDAR_RUNTIME_OR_ACCOUNT_AUTH",
        "M123_REMAINS_FUTURE",
    ]


def test_m122_calendar_connector_refresh_uses_safe_refs_only() -> None:
    connectors = _connectors()
    record = connectors.build_calendar_connector_contract_refresh_record(
        source_record=_source_record()
    )

    assert record.calendar_connector_contract_refresh_ref == (
        "calendar-connector-contract-refresh:m122"
    )
    assert record.source_email_connector_contract_refresh_ref == (
        "email-connector-contract-refresh:m121"
    )
    assert record.calendar_scope_refs == [
        "calendar-scope-ref:m122:declared-calendar-boundary",
        "calendar-scope-ref:m122:metadata-preview-only",
        "calendar-scope-ref:m122:no-account-action",
    ]
    assert record.calendar_boundary_refs
    assert record.event_boundary_refs
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
        "calendar password",
        "create event",
        "delete event",
        "read calendar",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("calendar_connector_runtime_enabled", "CALENDAR_CONNECTOR_RUNTIME_DENIED"),
        ("calendar_account_auth_enabled", "CALENDAR_ACCOUNT_AUTH_DENIED"),
        ("calendar_read_enabled", "CALENDAR_READ_DENIED"),
        ("calendar_search_enabled", "CALENDAR_SEARCH_DENIED"),
        ("calendar_event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
        ("calendar_event_update_enabled", "CALENDAR_EVENT_UPDATE_DENIED"),
        ("calendar_event_delete_enabled", "CALENDAR_EVENT_DELETE_DENIED"),
        ("calendar_invite_send_enabled", "CALENDAR_INVITE_SEND_DENIED"),
        ("calendar_attachment_download_enabled", "CALENDAR_ATTACHMENT_DOWNLOAD_DENIED"),
        ("raw_calendar_content_enabled", "RAW_CALENDAR_CONTENT_DENIED"),
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
def test_m122_policy_denies_calendar_runtime_and_account_authority(
    field: str, reason: str
) -> None:
    connectors = _connectors()
    with pytest.raises(ValueError, match=reason):
        connectors.validate_calendar_connector_contract_refresh_policy(
            connectors.CalendarConnectorContractRefreshPolicy(**{field: True})
        )


def test_m122_record_denies_model_copy_authority_flags() -> None:
    connectors = _connectors()
    record = connectors.build_calendar_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M122_REVIEW_ONLY_REQUIRED"),
        ({"calendar_scope_refs": []}, "M122_CALENDAR_SCOPE_REF_REQUIRED"),
        ({"calendar_boundary_refs": []}, "M122_CALENDAR_BOUNDARY_REF_REQUIRED"),
        ({"event_boundary_refs": []}, "M122_EVENT_BOUNDARY_REF_REQUIRED"),
        ({"consent_boundary_refs": []}, "M122_CONSENT_BOUNDARY_REF_REQUIRED"),
        ({"calendar_connector_runtime_enabled": True}, "CALENDAR_CONNECTOR_RUNTIME_DENIED"),
        ({"calendar_account_auth_enabled": True}, "CALENDAR_ACCOUNT_AUTH_DENIED"),
        ({"calendar_read_enabled": True}, "CALENDAR_READ_DENIED"),
        ({"calendar_event_create_enabled": True}, "CALENDAR_EVENT_CREATE_DENIED"),
        ({"calendar_event_update_enabled": True}, "CALENDAR_EVENT_UPDATE_DENIED"),
        ({"calendar_event_delete_enabled": True}, "CALENDAR_EVENT_DELETE_DENIED"),
        ({"calendar_invite_send_enabled": True}, "CALENDAR_INVITE_SEND_DENIED"),
        ({"raw_calendar_content_enabled": True}, "RAW_CALENDAR_CONTENT_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"metadata": {"api_key": "sk-test"}}, "SECRET_LIKE_M122_CALENDAR_CONTENT_DENIED"),
        ({"side_effects_performed": ["calendar-read"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_calendar_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m122_requires_exact_source_and_binding_refs() -> None:
    connectors = _connectors()
    record = connectors.build_calendar_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_email_connector_contract_refresh_ref": "wrong-ref:m121"},
            "M122_SOURCE_EMAIL_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline-ref:other"}, "M122_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor-ref:other"}, "M122_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M122_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M122_WORKSPACE_BINDING_MISMATCH"),
        (
            {"calendar_connector_contract_refresh_ref": "calendar-connector-contract-refresh:other"},
            "M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M122_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"accepted_checkpoint_refs": ["checkpoint:m120"]}, "M122_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_calendar_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m122_requires_safe_source_email_connector_refresh_record() -> None:
    connectors = _connectors()
    source_record = _source_record()
    unsafe_source = source_record.model_copy(update={"email_read_enabled": True})

    with pytest.raises(ValueError, match="EMAIL_READ_DENIED"):
        connectors.build_calendar_connector_contract_refresh_record(source_record=unsafe_source)
