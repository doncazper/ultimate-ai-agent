from functools import lru_cache

import pytest

from tests.test_m129_connector_audit_revocation_hardening import _request as _m129_request


def _connectors():
    import ultimate_ai_agent.core.connectors as connectors

    return connectors


@lru_cache(maxsize=1)
def _source_report():
    connectors = _connectors()
    return connectors.build_connector_audit_revocation_hardening_report(
        _m129_request()
    )


def test_m130_connector_safety_freeze_is_freeze_only_and_non_authoritative():
    connectors = _connectors()
    source_report = _source_report()
    record = connectors.build_connector_safety_freeze_record(
        source_report=source_report
    )

    assert record.status == connectors.ConnectorSafetyFreezeStatus.frozen_for_review
    assert record.contract_only is True
    assert record.review_only is True
    assert record.freeze_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.exact_m129_hardening_bound is True
    assert record.connector_surface_frozen is True
    assert record.audit_replay_bound is True
    assert record.revocation_readiness_bound is True
    assert record.no_effect_receipt_required is True
    assert record.source_report_ref == source_report.report_ref
    assert record.source_hardening_ref == source_report.hardening_ref
    assert record.source_audit_ledger_entry_ref == (
        source_report.audit_ledger_entry.audit_ledger_entry_ref
    )
    assert record.source_revocation_record_ref == (
        source_report.revocation_record.revocation_record_ref
    )
    assert record.actor_ref == source_report.actor_ref
    assert record.user_ref == source_report.user_ref
    assert record.workspace_ref == source_report.workspace_ref
    assert record.accepted_checkpoint_refs == [
        "checkpoint:m121",
        "checkpoint:m122",
        "checkpoint:m123",
        "checkpoint:m124",
        "checkpoint:m125",
        "checkpoint:m126",
        "checkpoint:m127",
        "checkpoint:m128",
        "checkpoint:m129",
    ]
    assert record.live_connector_runtime_enabled is False
    assert record.live_connector_runtime_performed is False
    assert record.account_auth_enabled is False
    assert record.network_access_performed is False
    assert record.credential_handling_performed is False
    assert record.raw_connector_content_returned is False
    assert record.full_connector_content_returned is False
    assert record.connector_write_performed is False
    assert record.connector_send_performed is False
    assert record.connector_delete_performed is False
    assert record.connector_export_performed is False
    assert record.connector_bulk_export_performed is False
    assert record.attachment_download_performed is False
    assert record.audit_export_performed is False
    assert record.revocation_executed is False
    assert record.kill_switch_executed is False
    assert record.connector_approval_revoked is False
    assert record.connector_session_stopped is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M130_CONNECTOR_SAFETY_FREEZE",
        "M130_FREEZE_ONLY_CONNECTOR_BOUNDARY",
        "M130_EXACT_M129_HARDENING_REQUIRED",
        "M130_NO_CONNECTOR_RUNTIME_AUTHORITY",
        "M131_REMAINS_FUTURE",
    ]


def test_m130_connector_safety_freeze_uses_safe_refs_only():
    connectors = _connectors()
    record = connectors.build_connector_safety_freeze_record(
        source_report=_source_report()
    )

    assert record.freeze_ref == "connector-safety-freeze:m130"
    assert record.safety_checklist_ref.startswith(
        "connector-safety-freeze-checklist-ref:"
    )
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert record.revocation_ref.startswith("revocation-ref:")
    assert record.kill_switch_ref.startswith("kill-switch-ref:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_connector_runtime_enabled", "M130_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "M130_ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "M130_NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "M130_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "M130_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_enabled", "M130_FULL_CONTENT_READ_DENIED"),
        ("connector_write_enabled", "M130_CONNECTOR_WRITE_DENIED"),
        ("connector_send_enabled", "M130_CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "M130_CONNECTOR_DELETE_DENIED"),
        ("connector_export_enabled", "M130_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_enabled", "M130_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "M130_ATTACHMENT_DOWNLOAD_DENIED"),
        ("audit_export_enabled", "M130_AUDIT_EXPORT_DENIED"),
        ("revocation_execution_enabled", "M130_REVOCATION_EXECUTION_DENIED"),
        ("kill_switch_execution_enabled", "M130_KILL_SWITCH_EXECUTION_DENIED"),
        (
            "connector_approval_revocation_enabled",
            "M130_APPROVAL_REVOCATION_DENIED",
        ),
        ("connector_session_stop_enabled", "M130_CONNECTOR_SESSION_STOP_DENIED"),
        ("background_worker_enabled", "M130_BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "M130_SCHEDULER_DENIED"),
        ("external_service_enabled", "M130_EXTERNAL_SERVICE_DENIED"),
        ("model_call_enabled", "M130_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M130_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M130_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M130_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M130_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M130_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M130_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M130_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m130_policy_denies_connector_freeze_authority(field, reason):
    connectors = _connectors()

    with pytest.raises(ValueError, match=reason):
        connectors.validate_connector_safety_freeze_policy(
            connectors.ConnectorSafetyFreezePolicy(**{field: True})
        )


def test_m130_record_denies_model_copy_runtime_and_freeze_drift():
    connectors = _connectors()
    record = connectors.build_connector_safety_freeze_record(
        source_report=_source_report()
    )

    for update, reason in [
        ({"review_only": False}, "M130_REVIEW_ONLY_REQUIRED"),
        ({"freeze_only": False}, "M130_FREEZE_ONLY_REQUIRED"),
        ({"safe_refs_only": False}, "M130_SAFE_REFS_ONLY_REQUIRED"),
        (
            {"exact_m129_hardening_bound": False},
            "M130_EXACT_M129_HARDENING_REQUIRED",
        ),
        ({"connector_surface_frozen": False}, "M130_CONNECTOR_SURFACE_FREEZE_REQUIRED"),
        ({"accepted_checkpoint_refs": []}, "M130_ACCEPTED_CHECKPOINT_REFS_REQUIRED"),
        (
            {"accepted_checkpoint_refs": ["checkpoint:m121", "checkpoint:m121"]},
            "M130_ACCEPTED_CHECKPOINT_REF_DUPLICATE",
        ),
        ({"live_connector_runtime_performed": True}, "M130_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ({"network_access_performed": True}, "M130_NETWORK_ACCESS_DENIED"),
        ({"raw_connector_content_returned": True}, "M130_RAW_CONNECTOR_CONTENT_DENIED"),
        ({"connector_write_performed": True}, "M130_CONNECTOR_WRITE_DENIED"),
        ({"connector_export_performed": True}, "M130_CONNECTOR_EXPORT_DENIED"),
        ({"audit_export_performed": True}, "M130_AUDIT_EXPORT_DENIED"),
        ({"revocation_executed": True}, "M130_REVOCATION_EXECUTION_DENIED"),
        ({"kill_switch_executed": True}, "M130_KILL_SWITCH_EXECUTION_DENIED"),
        ({"connector_approval_revoked": True}, "M130_APPROVAL_REVOCATION_DENIED"),
        ({"connector_session_stopped": True}, "M130_CONNECTOR_SESSION_STOP_DENIED"),
        ({"backend_route_added": True}, "M130_BACKEND_ROUTE_DENIED"),
        ({"beta_release_enabled": True}, "M130_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M130_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["export audit data"]}, "M130_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_safety_freeze_record(
                record.model_copy(update=update)
            )


def test_m130_record_denies_source_binding_drift_and_secret_metadata():
    connectors = _connectors()
    record = connectors.build_connector_safety_freeze_record(
        source_report=_source_report()
    )

    for update, reason in [
        (
            {"source_report_ref": "connector-audit-revocation-hardening-report:m130:other"},
            "M130_SOURCE_REPORT_BINDING_MISMATCH",
        ),
        (
            {"source_hardening_ref": "connector-audit-revocation-hardening:m130:other"},
            "M130_SOURCE_HARDENING_BINDING_MISMATCH",
        ),
        ({"actor_ref": "actor-ref:m130:other"}, "M130_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:m130:other"}, "M130_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:m130:other"}, "M130_WORKSPACE_BINDING_MISMATCH"),
        ({"safety_checklist_ref": "checklist:m130"}, "M130_SAFETY_CHECKLIST_REF_REQUIRED"),
        ({"no_effect_receipt_plan_ref": "receipt:m130"}, "M130_NO_EFFECT_RECEIPT_PLAN_REQUIRED"),
        ({"metadata": {"connector_token": "abc123supersecret"}}, "M130_SECRET_LIKE_CONNECTOR_FREEZE_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_safety_freeze_record(
                record.model_copy(update=update)
            )


def test_m130_revalidates_mutated_m129_source_report():
    connectors = _connectors()
    source_report = _source_report().model_copy(update={"revocation_executed": True})

    with pytest.raises(ValueError, match="M129_REVOCATION_EXECUTION_DENIED"):
        connectors.build_connector_safety_freeze_record(source_report=source_report)
