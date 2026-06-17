from datetime import timedelta
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
from ultimate_ai_agent.core.time import utc_now


def _connectors():
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M126 connectors package missing: {exc}")


@lru_cache(maxsize=1)
def _m120_source_record():
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
def _m124_source_record():
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


@lru_cache(maxsize=1)
def _runtime_record():
    connectors = _connectors()
    return connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )


def _request(runtime_record, **overrides):
    connectors = _connectors()
    data = {
        "approval_ref": "connector-approval-capture:m126:approval",
        "actor_ref": runtime_record.actor_ref,
        "user_ref": runtime_record.user_ref,
        "workspace_ref": runtime_record.workspace_ref,
        "connector_read_only_runtime_ref": (
            runtime_record.connector_read_only_runtime_ref
        ),
        "source_messages_connector_contract_review_ref": (
            runtime_record.source_messages_connector_contract_review_ref
        ),
        "source_baseline_ref": runtime_record.source_baseline_ref,
        "connector_scope_refs": runtime_record.connector_scope_refs,
        "connector_allowlist_refs": runtime_record.connector_allowlist_refs,
        "operation_allowlist_refs": runtime_record.operation_allowlist_refs,
        "redacted_metadata_preview_refs": (
            runtime_record.redacted_metadata_preview_refs
        ),
        "audit_ref": "audit-ref:m126:connector-approval-capture",
        "replay_ref": "replay-ref:m126:connector-approval-capture",
        "no_effect_receipt_plan_ref": (
            "receipt-plan-ref:m126:connector-approval-capture:no-effect"
        ),
        "decision": connectors.ConnectorApprovalDecisionKind.approve_review_only,
        "idempotency_key": "idempotency-ref:m126:connector-approval-capture",
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
        "safe_reason": "User reviewed safe connector metadata refs only.",
        "metadata_refs": ["metadata-ref:m126:connector-approval-capture"],
    }
    data.update(overrides)
    return connectors.ConnectorApprovalCaptureRequest(**data)


def test_m126_connector_approval_capture_persists_safe_record_without_authority():
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(runtime_record)

    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert (
        decision.status
        == connectors.ConnectorApprovalCaptureDecisionStatus.approved_for_review_only
    )
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.review_only is True
    assert decision.record is not None
    assert (
        decision.record.connector_read_only_runtime_ref
        == runtime_record.connector_read_only_runtime_ref
    )
    assert decision.record.actor_ref == runtime_record.actor_ref
    assert decision.record.user_ref == runtime_record.user_ref
    assert decision.record.workspace_ref == runtime_record.workspace_ref
    assert decision.record.connector_allowlist_refs == runtime_record.connector_allowlist_refs
    assert decision.record.redacted_metadata_preview_refs == (
        runtime_record.redacted_metadata_preview_refs
    )
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.raw_connector_content_stored is False
    assert decision.receipt_plan.full_content_stored is False
    assert decision.live_connector_runtime_authorized is False
    assert decision.account_auth_authorized is False
    assert decision.network_access_authorized is False
    assert decision.credential_handling_authorized is False
    assert decision.raw_connector_content_authorized is False
    assert decision.full_content_read_authorized is False
    assert decision.connector_write_authorized is False
    assert decision.connector_send_authorized is False
    assert decision.connector_delete_authorized is False
    assert decision.connector_export_authorized is False
    assert decision.attachment_download_authorized is False
    assert decision.model_call_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    dumped = decision.model_dump(mode="json")
    assert "raw_connector_content" not in dumped
    assert "full_connector_content" not in dumped
    assert "account_secret" not in dumped


def test_m126_connector_approval_denial_persists_safe_denial_record():
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(
        runtime_record,
        decision=connectors.ConnectorApprovalDecisionKind.deny_review_only,
    )

    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert (
        decision.status
        == connectors.ConnectorApprovalCaptureDecisionStatus.denied_for_review
    )
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.record is not None
    assert (
        decision.record.decision
        == connectors.ConnectorApprovalDecisionKind.deny_review_only
    )
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"actor_ref": "actor-ref:m126:other"}, "M126_CONNECTOR_APPROVAL_ACTOR_MISMATCH"),
        ({"user_ref": "user-ref:m126:other"}, "M126_CONNECTOR_APPROVAL_USER_MISMATCH"),
        ({"workspace_ref": "workspace-ref:m126:other"}, "M126_CONNECTOR_APPROVAL_WORKSPACE_MISMATCH"),
        (
            {"connector_read_only_runtime_ref": "connector-read-only-runtime:other"},
            "M126_CONNECTOR_APPROVAL_RUNTIME_REF_MISMATCH",
        ),
        (
            {
                "source_messages_connector_contract_review_ref": (
                    "messages-connector-contract-review:other"
                )
            },
            "M126_CONNECTOR_APPROVAL_SOURCE_REVIEW_REF_MISMATCH",
        ),
        (
            {"connector_allowlist_refs": ["connector-allowlist-ref:m126:other"]},
            "M126_CONNECTOR_APPROVAL_ALLOWLIST_REF_MISMATCH",
        ),
        (
            {"redacted_metadata_preview_refs": ["metadata-preview-ref:m126:other"]},
            "M126_CONNECTOR_APPROVAL_METADATA_PREVIEW_REF_MISMATCH",
        ),
        (
            {"approval_ref": "approval_test_m126"},
            "M126_CONNECTOR_APPROVAL_TEST_REF_DENIED",
        ),
        (
            {"expires_at": utc_now() - timedelta(minutes=1)},
            "M126_CONNECTOR_APPROVAL_EXPIRED",
        ),
        ({"revoked_at": utc_now()}, "M126_CONNECTOR_APPROVAL_REVOKED"),
        (
            {
                "replay_nonce": "replay-ref:m126:nonce",
                "used_replay_nonces": ["replay-ref:m126:nonce"],
            },
            "M126_CONNECTOR_APPROVAL_REPLAY_DETECTED",
        ),
    ],
)
def test_m126_capture_denies_binding_authority_and_lifecycle_failures(
    override, reason
):
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(runtime_record).model_copy(update=override)

    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.captured is False
    assert decision.persisted is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("live_connector_runtime_enabled", "M126_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "M126_ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "M126_NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "M126_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "M126_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_enabled", "M126_FULL_CONTENT_READ_DENIED"),
        ("connector_write_enabled", "M126_CONNECTOR_WRITE_DENIED"),
        ("connector_send_enabled", "M126_CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "M126_CONNECTOR_DELETE_DENIED"),
        ("connector_export_enabled", "M126_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_enabled", "M126_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "M126_ATTACHMENT_DOWNLOAD_DENIED"),
        ("model_call_enabled", "M126_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M126_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M126_CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "M126_EXECUTION_DENIED"),
        ("backend_route_added", "M126_BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "M126_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M126_DEPENDENCY_DENIED"),
    ],
)
def test_m126_model_copy_mutated_capture_request_flags_are_revalidated(
    flag, reason
):
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(runtime_record).model_copy(update={flag: True})

    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.captured is False
    assert decision.persisted is False
    assert decision.execution_performed is False


def test_m126_model_copy_mutated_secret_metadata_is_denied_without_echoing_secret():
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(runtime_record).model_copy(
        update={"metadata": {"api_key": "connector-secret-abc123"}}
    )

    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorApprovalCaptureDecisionStatus.rejected
    assert "M126_CONNECTOR_APPROVAL_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "connector-secret-abc123" not in decision.safe_message
    assert "connector-secret-abc123" not in str(decision.model_dump(mode="json"))


def test_m126_record_validation_denies_model_copy_authority_and_raw_fields():
    connectors = _connectors()
    runtime_record = _runtime_record()
    request = _request(runtime_record)
    decision = connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )

    assert decision.record is not None
    for field, reason in [
        ("raw_connector_content", "M126_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_connector_content", "M126_FULL_CONTENT_READ_DENIED"),
        ("connector_export_enabled", "M126_CONNECTOR_EXPORT_DENIED"),
        ("execution_enabled", "M126_EXECUTION_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_approval_capture_record(
                decision.record.model_copy(update={field: True})
            )
