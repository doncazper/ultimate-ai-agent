from functools import lru_cache

import pytest

from tests.test_m128_connector_write_execution_low_risk import (
    _request as _m128_request,
    _transport as _m128_transport,
)


def _connectors():
    import ultimate_ai_agent.core.connectors as connectors

    return connectors


@lru_cache(maxsize=1)
def _m128_decision_and_result():
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_m128_request())
    result = connectors.perform_low_risk_connector_write(
        decision,
        transport=_m128_transport,
    )
    return decision, result


def _request(**overrides):
    connectors = _connectors()
    decision, result = overrides.pop("m128_pair") if "m128_pair" in overrides else _m128_decision_and_result()
    data = {
        "hardening_request_ref": "connector-audit-revocation-hardening-request:m129:email-draft",
        "hardening_ref": "connector-audit-revocation-hardening:m129:email-draft",
        "connector_write_execution_decision_ref": decision.decision_ref,
        "connector_write_execution_result_ref": result.result_ref,
        "execution_ref": decision.execution_ref,
        "connector_write_dry_run_plan_ref": decision.connector_write_dry_run_plan_ref,
        "connector_write_approval_ref": decision.connector_write_approval_ref,
        "safe_result_ref": result.safe_result_ref,
        "actor_ref": decision.actor_ref,
        "user_ref": decision.user_ref,
        "workspace_ref": decision.workspace_ref,
        "audit_ref": "audit-ref:m129:connector-write-email-draft",
        "replay_ref": "replay-ref:m129:connector-write-email-draft",
        "revocation_ref": "revocation-ref:m129:connector-write-email-draft",
        "kill_switch_ref": "kill-switch-ref:m129:connector-write-email-draft",
        "audit_ledger_entry_ref": "connector-audit-ledger-entry:m129:email-draft",
        "revocation_record_ref": "connector-revocation-hardening-record:m129:email-draft",
        "retention_policy_ref": "retention-policy-ref:m129:connector-audit",
        "redaction_ref": "redaction-ref:m129:connector-audit-safe-summary",
        "prior_milestone_refs": [
            "milestone:M125",
            "milestone:M126",
            "milestone:M127",
            "milestone:M128",
        ],
        "m128_decision": decision,
        "m128_result": result,
        "safe_audit_summary": "Safe audit entry for the low-risk connector write result.",
        "safe_revocation_summary": (
            "Revocation readiness recorded for governed review without execution."
        ),
        "metadata_refs": ["metadata-ref:m129:connector-audit"],
    }
    data.update(overrides)
    return connectors.ConnectorAuditRevocationHardeningRequest(**data)


def test_m129_connector_audit_revocation_report_is_exact_bound_and_safe():
    connectors = _connectors()
    report = connectors.build_connector_audit_revocation_hardening_report(_request())

    assert report.status == (
        connectors.ConnectorAuditRevocationHardeningStatus.hardened_for_governed_review
    )
    assert report.exact_m128_execution_bound is True
    assert report.audit_hardened is True
    assert report.revocation_hardened is True
    assert report.audit_bound is True
    assert report.replay_bound is True
    assert report.revocation_ready is True
    assert report.local_only is True
    assert report.safe_refs_only is True
    assert report.review_only is True
    assert report.live_connector_runtime_performed is False
    assert report.account_auth_performed is False
    assert report.network_access_performed is False
    assert report.credential_handling_performed is False
    assert report.raw_connector_content_returned is False
    assert report.full_connector_content_returned is False
    assert report.connector_write_performed is False
    assert report.connector_send_performed is False
    assert report.connector_delete_performed is False
    assert report.connector_export_performed is False
    assert report.connector_bulk_export_performed is False
    assert report.attachment_download_performed is False
    assert report.audit_export_performed is False
    assert report.revocation_executed is False
    assert report.kill_switch_executed is False
    assert report.model_call_performed is False
    assert report.memory_write_performed is False
    assert report.context_injection_performed is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.audit_ledger_entry.store_safe_refs_only is True
    assert report.audit_ledger_entry.store_safe_summary_only is True
    assert report.audit_ledger_entry.raw_audit_payload_stored is False
    assert report.audit_ledger_entry.audit_exported is False
    assert report.revocation_record.revocation_ready is True
    assert report.revocation_record.revocation_review_only is True
    assert report.revocation_record.revocation_executed is False
    assert report.revocation_record.kill_switch_executed is False
    assert report.revocation_record.connector_approval_revoked is False
    assert report.reason_codes == [
        "M129_CONNECTOR_AUDIT_REVOCATION_HARDENED",
        "M129_EXACT_M128_EXECUTION_REQUIRED",
        "M129_SAFE_AUDIT_ENTRY_REQUIRED",
        "M129_REVOCATION_READY_NO_EXECUTION",
        "M130_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_connector_runtime_requested", "M129_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_requested", "M129_ACCOUNT_AUTH_DENIED"),
        ("network_access_requested", "M129_NETWORK_ACCESS_DENIED"),
        ("credential_handling_requested", "M129_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_requested", "M129_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_requested", "M129_FULL_CONTENT_READ_DENIED"),
        ("connector_write_requested", "M129_CONNECTOR_WRITE_DENIED"),
        ("connector_send_requested", "M129_CONNECTOR_SEND_DENIED"),
        ("connector_delete_requested", "M129_CONNECTOR_DELETE_DENIED"),
        ("connector_export_requested", "M129_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_requested", "M129_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_requested", "M129_ATTACHMENT_DOWNLOAD_DENIED"),
        ("audit_export_requested", "M129_AUDIT_EXPORT_DENIED"),
        ("revocation_execution_requested", "M129_REVOCATION_EXECUTION_DENIED"),
        ("kill_switch_execution_requested", "M129_KILL_SWITCH_EXECUTION_DENIED"),
        ("model_call_requested", "M129_MODEL_CALL_DENIED"),
        ("memory_write_requested", "M129_MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "M129_CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "M129_BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "M129_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "M129_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M129_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m129_request_denies_unsafe_audit_revocation_authority(field, reason):
    connectors = _connectors()

    with pytest.raises(ValueError, match=reason):
        connectors.build_connector_audit_revocation_hardening_report(
            _request().model_copy(update={field: True})
        )


def test_m129_requires_exact_m128_decision_and_result_binding():
    connectors = _connectors()

    for update, reason in [
        (
            {"connector_write_execution_decision_ref": "connector-write-execution-decision:m129:other"},
            "M129_M128_DECISION_REF_MISMATCH",
        ),
        (
            {"connector_write_execution_result_ref": "connector-write-execution-result:m129:other"},
            "M129_M128_RESULT_REF_MISMATCH",
        ),
        ({"execution_ref": "connector-write-execution:m129:other"}, "M129_EXECUTION_REF_MISMATCH"),
        ({"safe_result_ref": "connector-write-result-ref:m129:other"}, "M129_SAFE_RESULT_REF_MISMATCH"),
        ({"actor_ref": "actor-ref:m129:other"}, "M129_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:m129:other"}, "M129_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:m129:other"}, "M129_WORKSPACE_BINDING_MISMATCH"),
        ({"revocation_ref": "revocation-ref:m128:old"}, "M129_EXACT_AUDIT_REVOCATION_REF_REQUIRED"),
        ({"kill_switch_ref": "kill-switch-ref:m128:old"}, "M129_EXACT_AUDIT_REVOCATION_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.build_connector_audit_revocation_hardening_report(
                _request(**update)
            )


def test_m129_revalidates_mutated_m128_result_and_report_outputs():
    connectors = _connectors()
    decision, result = _m128_decision_and_result()
    mutated_result = result.model_copy(update={"network_access_performed": True})

    with pytest.raises(ValueError, match="M128_NETWORK_ACCESS_DENIED"):
        connectors.build_connector_audit_revocation_hardening_report(
            _request(m128_pair=(decision, mutated_result))
        )

    report = connectors.build_connector_audit_revocation_hardening_report(_request())
    with pytest.raises(ValueError, match="M129_REVOCATION_EXECUTION_DENIED"):
        connectors.validate_connector_audit_revocation_hardening_report(
            report.model_copy(update={"revocation_executed": True})
        )
    with pytest.raises(ValueError, match="M129_KILL_SWITCH_EXECUTION_DENIED"):
        connectors.validate_connector_audit_revocation_hardening_report(
            report.model_copy(update={"kill_switch_executed": True})
        )


def test_m129_ledger_and_revocation_records_deny_raw_or_executed_mutations():
    connectors = _connectors()
    report = connectors.build_connector_audit_revocation_hardening_report(_request())

    with pytest.raises(ValueError, match="M129_RAW_AUDIT_PAYLOAD_DENIED"):
        connectors.validate_connector_audit_ledger_entry(
            report.audit_ledger_entry.model_copy(
                update={"raw_audit_payload_stored": True}
            )
        )
    with pytest.raises(ValueError, match="M129_AUDIT_EXPORT_DENIED"):
        connectors.validate_connector_audit_ledger_entry(
            report.audit_ledger_entry.model_copy(update={"audit_exported": True})
        )
    with pytest.raises(ValueError, match="M129_APPROVAL_REVOCATION_EXECUTION_DENIED"):
        connectors.validate_connector_revocation_hardening_record(
            report.revocation_record.model_copy(
                update={"connector_approval_revoked": True}
            )
        )
    with pytest.raises(ValueError, match="M129_CONNECTOR_SESSION_STOP_DENIED"):
        connectors.validate_connector_revocation_hardening_record(
            report.revocation_record.model_copy(
                update={"connector_session_stopped": True}
            )
        )


def test_m129_policy_denies_runtime_and_revocation_execution_enablement():
    connectors = _connectors()

    for update, reason in [
        ({"live_connector_runtime_enabled": True}, "M129_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ({"network_access_enabled": True}, "M129_NETWORK_ACCESS_DENIED"),
        ({"audit_export_enabled": True}, "M129_AUDIT_EXPORT_DENIED"),
        ({"revocation_execution_enabled": True}, "M129_REVOCATION_EXECUTION_DENIED"),
        ({"kill_switch_execution_enabled": True}, "M129_KILL_SWITCH_EXECUTION_DENIED"),
        ({"production_authority_granted": True}, "M129_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.build_connector_audit_revocation_hardening_report(
                _request(),
                policy=connectors.ConnectorAuditRevocationHardeningPolicy(
                    **update
                ),
            )
