from typing import Any
from functools import lru_cache
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
        pytest.fail(f"M125 connectors package missing: {exc}")


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
def _m124_source_record() -> Any:
    connectors = _connectors()
    return connectors.build_messages_connector_contract_review_record(
        source_record=connectors.build_contacts_connector_contract_refresh_record(
            source_record=connectors.build_calendar_connector_contract_refresh_record(
                source_record=connectors.build_email_connector_contract_refresh_record(
                    source_record=_m120_source_record()
                )
            )
        )
    )


def test_m125_connector_runtime_is_read_only_safe_ref_bound() -> None:
    connectors = _connectors()
    source_record = _m124_source_record()
    record = connectors.build_connector_read_only_runtime_record(
        source_record=source_record
    )

    assert (
        record.status
        == connectors.ConnectorReadOnlyRuntimeStatus.connector_read_only_runtime_reviewed
    )
    assert record.read_only_runtime is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.baseline_bound is True
    assert record.source_messages_connector_contract_review_bound is True
    assert record.user_bound is True
    assert record.workspace_bound is True
    assert record.connector_scope_bound is True
    assert record.connector_allowlist_bound is True
    assert record.operation_allowlist_bound is True
    assert record.data_minimization_bound is True
    assert record.redaction_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert (
        record.source_messages_connector_contract_review_ref
        == source_record.messages_connector_contract_review_ref
    )
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.user_ref == source_record.user_ref
    assert record.workspace_ref == source_record.workspace_ref
    assert "checkpoint:m124" in record.accepted_checkpoint_refs
    assert record.connector_scope_refs
    assert record.connector_allowlist_refs == [
        "connector-allowlist-ref:m125:email-metadata-only",
        "connector-allowlist-ref:m125:calendar-metadata-only",
        "connector-allowlist-ref:m125:contacts-metadata-only",
        "connector-allowlist-ref:m125:messages-metadata-only",
    ]
    assert record.operation_allowlist_refs == [
        "connector-operation-ref:m125:list-safe-metadata",
        "connector-operation-ref:m125:get-safe-summary-by-ref",
    ]
    assert record.redacted_metadata_preview_refs
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert record.live_connector_runtime_enabled is False
    assert record.account_auth_enabled is False
    assert record.network_access_enabled is False
    assert record.credential_handling_enabled is False
    assert record.raw_connector_content_enabled is False
    assert record.full_content_read_enabled is False
    assert record.connector_write_enabled is False
    assert record.connector_send_enabled is False
    assert record.connector_delete_enabled is False
    assert record.connector_export_enabled is False
    assert record.connector_bulk_export_enabled is False
    assert record.attachment_download_enabled is False
    assert record.model_call_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M125_CONNECTOR_READ_ONLY_RUNTIME",
        "M125_SAFE_METADATA_ONLY",
        "M125_NO_AUTH_NETWORK_RAW_CONTENT_OR_WRITES",
        "M126_REMAINS_FUTURE",
    ]


def test_m125_connector_runtime_uses_safe_summaries_only() -> None:
    connectors = _connectors()
    record = connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )

    assert record.connector_read_only_runtime_ref == (
        "connector-read-only-runtime:m125"
    )
    assert record.source_messages_connector_contract_review_ref == (
        "messages-connector-contract-review:m124"
    )
    summary = record.safe_summary.lower()
    for forbidden in [
        "api_key",
        "password",
        "bearer",
        "authorization",
        "cookie",
        "oauth token",
        "raw email body",
        "raw calendar body",
        "raw contact",
        "raw message",
        "send message",
        "download attachment",
        "bulk export",
        "/users/",
    ]:
        assert forbidden not in summary
    for preview_ref in record.redacted_metadata_preview_refs:
        assert "metadata-preview-ref:m125:" in preview_ref


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_connector_runtime_enabled", "LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_enabled", "FULL_CONTENT_READ_DENIED"),
        ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
        ("connector_send_enabled", "CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "CONNECTOR_DELETE_DENIED"),
        ("connector_export_enabled", "CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_enabled", "CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("backend_route_added", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ],
)
def test_m125_record_model_copy_denies_authority_flags(field: str, reason: str) -> None:
    connectors = _connectors()
    record = connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )

    with pytest.raises(ValueError, match=reason):
        connectors.validate_connector_read_only_runtime_record(
            record.model_copy(update={field: True})
        )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("read_only_runtime", False, "M125_READ_ONLY_RUNTIME_REQUIRED"),
        ("connector_scope_refs", [], "M125_CONNECTOR_SCOPE_REF_REQUIRED"),
        ("connector_allowlist_refs", [], "M125_CONNECTOR_ALLOWLIST_REF_REQUIRED"),
        ("operation_allowlist_refs", [], "M125_OPERATION_ALLOWLIST_REF_REQUIRED"),
        ("data_minimization_refs", [], "M125_DATA_MINIMIZATION_REF_REQUIRED"),
        ("redaction_refs", [], "M125_REDACTION_REF_REQUIRED"),
        (
            "source_messages_connector_contract_review_ref",
            "messages-connector-contract-review:mismatched",
            "M125_SOURCE_MESSAGES_CONNECTOR_CONTRACT_REVIEW_REF_MISMATCH",
        ),
        ("safe_summary", "raw message body: hello", "SAFE_PAYLOAD_UNSAFE"),
        ("side_effects_performed", ["read live account"], "SIDE_EFFECTS_DENIED"),
    ],
)
def test_m125_record_requires_exact_bindings_and_safe_refs(
    field: str, value: object, reason: str
) -> None:
    connectors = _connectors()
    record = connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )

    with pytest.raises(ValueError, match=reason):
        connectors.validate_connector_read_only_runtime_record(
            record.model_copy(update={field: value})
        )


def test_m125_policy_denies_unsafe_connector_runtime_modes() -> None:
    connectors = _connectors()

    for field, reason in [
        ("live_connector_runtime_enabled", "LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "RAW_CONNECTOR_CONTENT_DENIED"),
        ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_read_only_runtime_policy(
                connectors.ConnectorReadOnlyRuntimePolicy().model_copy(
                    update={field: True}
                )
            )


def test_m125_revalidates_source_m124_record() -> None:
    connectors = _connectors()
    source_record = _m124_source_record().model_copy(
        update={"messages_send_enabled": True}
    )

    with pytest.raises(ValueError, match="MESSAGES_SEND_DENIED"):
        connectors.build_connector_read_only_runtime_record(source_record=source_record)
