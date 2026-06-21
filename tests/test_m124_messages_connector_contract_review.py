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
        pytest.fail(f"M124 connectors package missing: {exc}")


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
    return connectors.build_contacts_connector_contract_refresh_record(
        source_record=connectors.build_calendar_connector_contract_refresh_record(
            source_record=connectors.build_email_connector_contract_refresh_record(
                source_record=_m120_source_record()
            )
        )
    )


def test_m124_messages_connector_refresh_is_contract_only_and_safe_ref_bound() -> None:
    connectors = _connectors()
    source_record = _source_record()
    record = connectors.build_messages_connector_contract_review_record(
        source_record=source_record
    )

    assert (
        record.status
        == connectors.MessagesConnectorContractReviewStatus.messages_connector_contract_review
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_contacts_connector_contract_refresh_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.messages_scope_bound is True
    assert record.messages_boundary_bound is True
    assert record.message_thread_boundary_bound is True
    assert record.consent_boundary_bound is True
    assert record.data_classification_bound is True
    assert record.retention_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_contacts_connector_contract_refresh_ref
        == source_record.contacts_connector_contract_refresh_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m123" in record.accepted_checkpoint_refs
    assert record.messages_scope_refs
    assert record.messages_boundary_refs
    assert record.message_thread_boundary_refs
    assert record.consent_boundary_refs
    assert record.data_classification_refs
    assert record.retention_boundary_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.messages_connector_runtime_enabled is False
    assert record.messages_account_auth_enabled is False
    assert record.messages_read_enabled is False
    assert record.messages_search_enabled is False
    assert record.messages_lookup_enabled is False
    assert record.messages_send_enabled is False
    assert record.message_thread_access_enabled is False
    assert record.messages_create_enabled is False
    assert record.messages_update_enabled is False
    assert record.messages_delete_enabled is False
    assert record.messages_export_enabled is False
    assert record.messages_bulk_export_enabled is False
    assert record.attachment_download_enabled is False
    assert record.raw_messages_content_enabled is False
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
        "M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW",
        "M124_CONTRACT_ONLY",
        "M124_REVIEW_ONLY",
        "M124_NO_MESSAGES_RUNTIME_ACCOUNT_AUTH_OR_SEND",
        "M125_REMAINS_FUTURE",
    ]


def test_m124_messages_connector_refresh_uses_safe_refs_only() -> None:
    connectors = _connectors()
    record = connectors.build_messages_connector_contract_review_record(
        source_record=_source_record()
    )

    assert record.messages_connector_contract_review_ref == (
        "messages-connector-contract-review:m124"
    )
    assert record.source_contacts_connector_contract_refresh_ref == (
        "contacts-connector-contract-refresh:m123"
    )
    assert record.messages_scope_refs == [
        "messages-scope-ref:m124:declared-messages-boundary",
        "messages-scope-ref:m124:metadata-preview-only",
        "messages-scope-ref:m124:no-account-action",
    ]
    assert record.messages_boundary_refs
    assert record.message_thread_boundary_refs
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
        "messages password",
        "send message",
        "message thread body",
        "bulk export",
        "read messages",
        "attachment download",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("messages_connector_runtime_enabled", "MESSAGES_CONNECTOR_RUNTIME_DENIED"),
        ("messages_account_auth_enabled", "MESSAGES_ACCOUNT_AUTH_DENIED"),
        ("messages_read_enabled", "MESSAGES_READ_DENIED"),
        ("messages_search_enabled", "MESSAGES_SEARCH_DENIED"),
        ("messages_lookup_enabled", "MESSAGES_LOOKUP_DENIED"),
        ("messages_send_enabled", "MESSAGES_SEND_DENIED"),
        ("message_thread_access_enabled", "MESSAGE_THREAD_ACCESS_DENIED"),
        ("messages_create_enabled", "MESSAGES_CREATE_DENIED"),
        ("messages_update_enabled", "MESSAGES_UPDATE_DENIED"),
        ("messages_delete_enabled", "MESSAGES_DELETE_DENIED"),
        ("messages_export_enabled", "MESSAGES_EXPORT_DENIED"),
        ("messages_bulk_export_enabled", "MESSAGES_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("raw_messages_content_enabled", "RAW_MESSAGES_CONTENT_DENIED"),
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
def test_m124_policy_denies_messages_runtime_and_account_authority(
    field: str, reason: str
) -> None:
    connectors = _connectors()
    with pytest.raises(ValueError, match=reason):
        connectors.validate_messages_connector_contract_review_policy(
            connectors.MessagesConnectorContractReviewPolicy(**{field: True})
        )


def test_m124_record_denies_model_copy_authority_flags() -> None:
    connectors = _connectors()
    record = connectors.build_messages_connector_contract_review_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M124_REVIEW_ONLY_REQUIRED"),
        ({"messages_scope_refs": []}, "M124_MESSAGES_SCOPE_REF_REQUIRED"),
        ({"messages_boundary_refs": []}, "M124_MESSAGES_BOUNDARY_REF_REQUIRED"),
        ({"message_thread_boundary_refs": []}, "M124_MESSAGE_THREAD_BOUNDARY_REF_REQUIRED"),
        ({"consent_boundary_refs": []}, "M124_CONSENT_BOUNDARY_REF_REQUIRED"),
        ({"messages_connector_runtime_enabled": True}, "MESSAGES_CONNECTOR_RUNTIME_DENIED"),
        ({"messages_account_auth_enabled": True}, "MESSAGES_ACCOUNT_AUTH_DENIED"),
        ({"messages_read_enabled": True}, "MESSAGES_READ_DENIED"),
        ({"messages_lookup_enabled": True}, "MESSAGES_LOOKUP_DENIED"),
        ({"messages_send_enabled": True}, "MESSAGES_SEND_DENIED"),
        ({"message_thread_access_enabled": True}, "MESSAGE_THREAD_ACCESS_DENIED"),
        ({"messages_create_enabled": True}, "MESSAGES_CREATE_DENIED"),
        ({"messages_update_enabled": True}, "MESSAGES_UPDATE_DENIED"),
        ({"messages_delete_enabled": True}, "MESSAGES_DELETE_DENIED"),
        ({"messages_export_enabled": True}, "MESSAGES_EXPORT_DENIED"),
        ({"messages_bulk_export_enabled": True}, "MESSAGES_BULK_EXPORT_DENIED"),
        ({"attachment_download_enabled": True}, "ATTACHMENT_DOWNLOAD_DENIED"),
        ({"raw_messages_content_enabled": True}, "RAW_MESSAGES_CONTENT_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"metadata": {"api_key": "sk-test"}}, "SECRET_LIKE_M124_MESSAGES_CONTENT_DENIED"),
        ({"side_effects_performed": ["messages-read"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_messages_connector_contract_review_record(
                record.model_copy(update=update)
            )


def test_m124_requires_exact_source_and_binding_refs() -> None:
    connectors = _connectors()
    record = connectors.build_messages_connector_contract_review_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_contacts_connector_contract_refresh_ref": "wrong-ref:m122"},
            "M124_SOURCE_CONTACTS_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline-ref:other"}, "M124_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor-ref:other"}, "M124_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M124_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M124_WORKSPACE_BINDING_MISMATCH"),
        (
            {"messages_connector_contract_review_ref": "messages-connector-contract-review:other"},
            "M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW_REF_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M124_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"accepted_checkpoint_refs": ["checkpoint:m120"]}, "M124_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_messages_connector_contract_review_record(
                record.model_copy(update=update)
            )


def test_m124_requires_safe_source_contacts_connector_refresh_record() -> None:
    connectors = _connectors()
    source_record = _source_record()
    unsafe_source = source_record.model_copy(update={"contacts_read_enabled": True})

    with pytest.raises(ValueError, match="CONTACTS_READ_DENIED"):
        connectors.build_messages_connector_contract_review_record(source_record=unsafe_source)
