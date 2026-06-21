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
        pytest.fail(f"M121 connectors package missing: {exc}")


def _source_record() -> Any:
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


def test_m121_email_connector_refresh_is_contract_only_and_safe_ref_bound() -> None:
    connectors = _connectors()
    source_record = _source_record()
    record = connectors.build_email_connector_contract_refresh_record(
        source_record=source_record
    )

    assert (
        record.status
        == connectors.EmailConnectorContractRefreshStatus.email_connector_contract_refresh
    )
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_production_authority_readiness_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.email_scope_bound is True
    assert record.mailbox_boundary_bound is True
    assert record.consent_boundary_bound is True
    assert record.data_classification_bound is True
    assert record.retention_boundary_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_production_authority_readiness_ref
        == source_record.production_authority_readiness_review_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m120" in record.accepted_checkpoint_refs
    assert record.email_scope_refs
    assert record.mailbox_boundary_refs
    assert record.consent_boundary_refs
    assert record.data_classification_refs
    assert record.retention_boundary_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.email_connector_runtime_enabled is False
    assert record.email_account_auth_enabled is False
    assert record.email_read_enabled is False
    assert record.email_search_enabled is False
    assert record.email_send_enabled is False
    assert record.email_write_enabled is False
    assert record.email_delete_enabled is False
    assert record.email_attachment_download_enabled is False
    assert record.raw_email_content_enabled is False
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
        "M121_EMAIL_CONNECTOR_CONTRACT_REFRESH",
        "M121_CONTRACT_ONLY",
        "M121_REVIEW_ONLY",
        "M121_NO_EMAIL_RUNTIME_OR_ACCOUNT_AUTH",
        "M122_REMAINS_FUTURE",
    ]


def test_m121_email_connector_refresh_uses_safe_refs_only() -> None:
    connectors = _connectors()
    record = connectors.build_email_connector_contract_refresh_record(
        source_record=_source_record()
    )

    assert record.email_connector_contract_refresh_ref == (
        "email-connector-contract-refresh:m121"
    )
    assert record.source_production_authority_readiness_ref == (
        "production-authority-readiness-review:m120"
    )
    assert record.email_scope_refs == [
        "email-scope-ref:m121:declared-mailbox-boundary",
        "email-scope-ref:m121:metadata-preview-only",
        "email-scope-ref:m121:no-account-action",
    ]
    assert record.mailbox_boundary_refs
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
        "imap password",
        "smtp password",
        "send email",
        "read inbox",
        "/users/",
    ]:
        assert forbidden not in summary


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("email_connector_runtime_enabled", "EMAIL_CONNECTOR_RUNTIME_DENIED"),
        ("email_account_auth_enabled", "EMAIL_ACCOUNT_AUTH_DENIED"),
        ("email_read_enabled", "EMAIL_READ_DENIED"),
        ("email_search_enabled", "EMAIL_SEARCH_DENIED"),
        ("email_send_enabled", "EMAIL_SEND_DENIED"),
        ("email_write_enabled", "EMAIL_WRITE_DENIED"),
        ("email_delete_enabled", "EMAIL_DELETE_DENIED"),
        ("email_attachment_download_enabled", "EMAIL_ATTACHMENT_DOWNLOAD_DENIED"),
        ("raw_email_content_enabled", "RAW_EMAIL_CONTENT_DENIED"),
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
def test_m121_policy_denies_email_runtime_and_account_authority(
    field: str, reason: str
) -> None:
    connectors = _connectors()
    with pytest.raises(ValueError, match=reason):
        connectors.validate_email_connector_contract_refresh_policy(
            connectors.EmailConnectorContractRefreshPolicy(**{field: True})
        )


def test_m121_record_denies_model_copy_authority_flags() -> None:
    connectors = _connectors()
    record = connectors.build_email_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "M121_REVIEW_ONLY_REQUIRED"),
        ({"email_scope_refs": []}, "M121_EMAIL_SCOPE_REF_REQUIRED"),
        ({"mailbox_boundary_refs": []}, "M121_MAILBOX_BOUNDARY_REF_REQUIRED"),
        ({"consent_boundary_refs": []}, "M121_CONSENT_BOUNDARY_REF_REQUIRED"),
        ({"email_connector_runtime_enabled": True}, "EMAIL_CONNECTOR_RUNTIME_DENIED"),
        ({"email_account_auth_enabled": True}, "EMAIL_ACCOUNT_AUTH_DENIED"),
        ({"email_read_enabled": True}, "EMAIL_READ_DENIED"),
        ({"email_send_enabled": True}, "EMAIL_SEND_DENIED"),
        ({"raw_email_content_enabled": True}, "RAW_EMAIL_CONTENT_DENIED"),
        ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
        ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "DEPENDENCY_DENIED"),
        ({"metadata": {"api_key": "sk-test"}}, "SECRET_LIKE_M121_EMAIL_CONTENT_DENIED"),
        ({"side_effects_performed": ["email-read"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_email_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m121_requires_exact_source_and_binding_refs() -> None:
    connectors = _connectors()
    record = connectors.build_email_connector_contract_refresh_record(
        source_record=_source_record()
    )

    for update, reason in [
        (
            {"source_production_authority_readiness_ref": "wrong-ref:m120"},
            "M121_SOURCE_PRODUCTION_AUTHORITY_READINESS_BINDING_MISMATCH",
        ),
        ({"source_baseline_ref": "baseline-ref:other"}, "M121_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor-ref:other"}, "M121_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:other"}, "M121_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:other"}, "M121_WORKSPACE_BINDING_MISMATCH"),
        (
            {"email_connector_contract_refresh_ref": "email-connector-contract-refresh:other"},
            "M121_EMAIL_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED",
        ),
        ({"accepted_checkpoint_refs": []}, "M121_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ({"accepted_checkpoint_refs": ["checkpoint:m119"]}, "M121_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_email_connector_contract_refresh_record(
                record.model_copy(update=update)
            )


def test_m121_requires_safe_source_production_authority_readiness_record() -> None:
    connectors = _connectors()
    source_record = _source_record()
    unsafe_source = source_record.model_copy(update={"production_authority_enabled": True})

    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        connectors.build_email_connector_contract_refresh_record(source_record=unsafe_source)
