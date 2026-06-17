from functools import lru_cache

import pytest

from tests.test_m127_connector_write_dry_run_planner import (
    _approval_decision,
    _request as _m127_request,
    _runtime_record,
)
from ultimate_ai_agent.core.time import utc_now


@lru_cache(maxsize=1)
def _m127_decision():
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _m127_request(approval_decision)
    return connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )


def _connectors():
    import ultimate_ai_agent.core.connectors as connectors

    return connectors


def _request(**overrides):
    connectors = _connectors()
    m127_decision = overrides.pop("m127_decision") if "m127_decision" in overrides else _m127_decision()
    assert m127_decision.plan is not None
    plan = m127_decision.plan
    data = {
        "request_ref": "connector-write-execution-request:m128:email-draft",
        "execution_ref": "connector-write-execution:m128:email-draft",
        "connector_write_dry_run_decision_ref": m127_decision.decision_ref,
        "connector_write_dry_run_plan_ref": plan.dry_run_plan_ref,
        "connector_write_approval_ref": "approval:connector-write:m128:email-draft",
        "connector_read_only_runtime_ref": plan.connector_read_only_runtime_ref,
        "source_messages_connector_contract_review_ref": (
            plan.source_messages_connector_contract_review_ref
        ),
        "source_baseline_ref": plan.source_baseline_ref,
        "actor_ref": plan.actor_ref,
        "user_ref": plan.user_ref,
        "workspace_ref": plan.workspace_ref,
        "connector_scope_refs": plan.connector_scope_refs,
        "connector_allowlist_refs": plan.connector_allowlist_refs,
        "dry_run_operation_refs": plan.dry_run_operation_refs,
        "write_target_refs": plan.write_target_refs,
        "safe_payload_summary_refs": plan.safe_payload_summary_refs,
        "safe_result_ref": "connector-write-result-ref:m128:email-draft",
        "safe_execution_scope_ref": "safe-execution-scope-ref:m128:email-draft",
        "low_risk_classification_ref": "risk-classification-ref:m128:low-risk-write",
        "audit_ref": plan.audit_ref,
        "replay_ref": plan.replay_ref,
        "revocation_ref": "revocation-ref:m128:email-draft",
        "kill_switch_ref": "kill-switch-ref:m128:email-draft",
        "idempotency_key": plan.idempotency_key,
        "prior_milestone_refs": ["milestone:M125", "milestone:M126", "milestone:M127"],
        "m127_decision": m127_decision,
        "safe_write_summary": "Write a safe connector draft from reviewed safe refs only.",
        "metadata_refs": ["metadata-ref:m128:email-draft"],
    }
    data.update(overrides)
    return connectors.ConnectorWriteExecutionLowRiskRequest(**data)


def _transport(_decision):
    connectors = _connectors()
    return connectors.ConnectorWriteExecutionTransportResponse(
        write_completed=True,
        safe_result_ref="connector-write-result-ref:m128:email-draft",
        safe_summary="Safe connector draft write completed.",
    )


def test_m128_low_risk_connector_write_decision_is_exact_bound_and_safe():
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_request())

    assert decision.status == (
        connectors.ConnectorWriteExecutionLowRiskStatus.write_allowed_for_low_risk_transport
    )
    assert decision.low_risk_write_allowed is True
    assert decision.exact_m127_dry_run_bound is True
    assert decision.exact_connector_write_approval_bound is True
    assert decision.transport_required is True
    assert decision.safe_refs_only is True
    assert decision.local_only is True
    assert decision.audit_bound is True
    assert decision.replay_bound is True
    assert decision.revocation_bound is True
    assert decision.write_performed is False
    assert decision.live_connector_runtime_performed is False
    assert decision.account_auth_performed is False
    assert decision.network_access_performed is False
    assert decision.credential_handling_performed is False
    assert decision.raw_connector_content_returned is False
    assert decision.full_connector_content_returned is False
    assert decision.connector_send_performed is False
    assert decision.connector_delete_performed is False
    assert decision.connector_export_performed is False
    assert decision.attachment_download_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.reason_codes == [
        "M128_LOW_RISK_CONNECTOR_WRITE_ALLOWED",
        "M128_EXACT_M127_DRY_RUN_REQUIRED",
        "M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED",
        "M128_SAFE_TRANSPORT_REQUIRED",
        "M129_REMAINS_FUTURE",
    ]


def test_m128_performs_low_risk_write_only_through_injected_safe_transport():
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_request())

    with pytest.raises(ValueError, match="M128_CONNECTOR_WRITE_TRANSPORT_REQUIRED"):
        connectors.perform_low_risk_connector_write(decision, transport=None)

    result = connectors.perform_low_risk_connector_write(decision, transport=_transport)

    assert result.status == connectors.ConnectorWriteExecutionLowRiskStatus.write_completed
    assert result.write_performed is True
    assert result.safe_result_ref == decision.safe_result_ref
    assert result.live_connector_runtime_performed is False
    assert result.account_auth_performed is False
    assert result.network_access_performed is False
    assert result.credential_handling_performed is False
    assert result.raw_connector_content_returned is False
    assert result.full_connector_content_returned is False
    assert result.connector_send_performed is False
    assert result.connector_delete_performed is False
    assert result.connector_export_performed is False
    assert result.attachment_download_performed is False
    assert result.model_call_performed is False
    assert result.memory_write_performed is False
    assert result.context_injection_performed is False
    assert result.backend_route_added is False
    assert result.control_center_control_added is False
    assert result.dependency_added is False
    assert result.production_authority_granted is False
    assert result.side_effects_performed == []
    assert result.reason_codes == [
        "M128_LOW_RISK_CONNECTOR_WRITE_COMPLETED",
        "M128_SAFE_RESULT_ONLY",
        "M128_AUDIT_AND_REVOCATION_REQUIRED",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("live_connector_runtime_requested", "M128_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_requested", "M128_ACCOUNT_AUTH_DENIED"),
        ("network_access_requested", "M128_NETWORK_ACCESS_DENIED"),
        ("credential_handling_requested", "M128_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_requested", "M128_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_requested", "M128_FULL_CONTENT_READ_DENIED"),
        ("connector_send_requested", "M128_CONNECTOR_SEND_DENIED"),
        ("connector_delete_requested", "M128_CONNECTOR_DELETE_DENIED"),
        ("connector_export_requested", "M128_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_requested", "M128_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_requested", "M128_ATTACHMENT_DOWNLOAD_DENIED"),
        ("model_call_requested", "M128_MODEL_CALL_DENIED"),
        ("memory_write_requested", "M128_MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "M128_CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "M128_BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "M128_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "M128_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M128_PRODUCTION_AUTHORITY_DENIED"),
        ("high_risk_write_requested", "M128_HIGH_RISK_CONNECTOR_WRITE_DENIED"),
    ],
)
def test_m128_request_denies_unsafe_connector_write_authority(field, reason):
    connectors = _connectors()

    with pytest.raises(ValueError, match=reason):
        connectors.build_connector_write_execution_decision(
            _request().model_copy(update={field: True})
        )


def test_m128_requires_exact_m127_binding_and_write_approval():
    connectors = _connectors()

    for update, reason in [
        (
            {"connector_write_dry_run_decision_ref": "connector-write-dry-run-decision:other"},
            "M128_M127_DRY_RUN_DECISION_REF_MISMATCH",
        ),
        (
            {"connector_write_dry_run_plan_ref": "connector-write-dry-run-plan:other"},
            "M128_M127_DRY_RUN_PLAN_REF_MISMATCH",
        ),
        ({"actor_ref": "actor-ref:m128:other"}, "M128_ACTOR_BINDING_MISMATCH"),
        ({"user_ref": "user-ref:m128:other"}, "M128_USER_BINDING_MISMATCH"),
        ({"workspace_ref": "workspace-ref:m128:other"}, "M128_WORKSPACE_BINDING_MISMATCH"),
        (
            {"connector_write_approval_ref": "approval-test-ref:m128"},
            "M128_CONNECTOR_WRITE_APPROVAL_TEST_REF_DENIED",
        ),
        (
            {"connector_write_approval_ref": "approval:connector-write:m128:wildcard"},
            "M128_WILDCARD_CONNECTOR_WRITE_APPROVAL_DENIED",
        ),
        (
            {"connector_write_approval_ref": "approval:scope-only"},
            "M128_EXACT_CONNECTOR_WRITE_APPROVAL_REQUIRED",
        ),
        (
            {"low_risk_classification_ref": "risk-classification-ref:m128:critical"},
            "M128_LOW_RISK_CLASSIFICATION_REQUIRED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.build_connector_write_execution_decision(_request(**update))


def test_m128_revalidates_model_copy_mutated_m127_decision_and_outputs():
    connectors = _connectors()
    m127_decision = _m127_decision().model_copy(update={"connector_write_authorized": True})
    with pytest.raises(ValueError, match="M128_M127_DRY_RUN_AUTHORITY_MISMATCH"):
        connectors.build_connector_write_execution_decision(
            _request().model_copy(update={"m127_decision": m127_decision})
        )

    decision = connectors.build_connector_write_execution_decision(_request())
    with pytest.raises(ValueError, match="M128_WRITE_NOT_ALLOWED_IN_DECISION"):
        connectors.validate_connector_write_execution_decision(
            decision.model_copy(update={"write_performed": True})
        )

    result = connectors.perform_low_risk_connector_write(decision, transport=_transport)
    with pytest.raises(ValueError, match="M128_NETWORK_ACCESS_DENIED"):
        connectors.validate_connector_write_execution_result(
            result.model_copy(update={"network_access_performed": True})
        )


def test_m128_transport_denies_hidden_unsafe_side_effects():
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_request())

    def unsafe_transport(_decision):
        return connectors.ConnectorWriteExecutionTransportResponse(
            write_completed=True,
            safe_result_ref=decision.safe_result_ref,
            safe_summary="Unsafe connector write response.",
            network_access_performed=True,
        )

    with pytest.raises(ValueError, match="M128_NETWORK_ACCESS_DENIED"):
        connectors.perform_low_risk_connector_write(decision, transport=unsafe_transport)


def test_m128_transport_result_ref_must_match_decision():
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_request())

    def mismatched_transport(_decision):
        return connectors.ConnectorWriteExecutionTransportResponse(
            write_completed=True,
            safe_result_ref="connector-write-result-ref:m128:other",
            safe_summary="Safe connector draft write completed.",
        )

    with pytest.raises(ValueError, match="M128_SAFE_RESULT_REF_MISMATCH"):
        connectors.perform_low_risk_connector_write(decision, transport=mismatched_transport)


def test_m128_policy_denies_unsafe_enablement_flags():
    connectors = _connectors()

    for field, reason in [
        ("live_connector_runtime_enabled", "M128_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "M128_ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "M128_NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "M128_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "M128_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_enabled", "M128_FULL_CONTENT_READ_DENIED"),
        ("connector_send_enabled", "M128_CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "M128_CONNECTOR_DELETE_DENIED"),
        ("connector_export_enabled", "M128_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_enabled", "M128_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "M128_ATTACHMENT_DOWNLOAD_DENIED"),
        ("model_call_enabled", "M128_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M128_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M128_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M128_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M128_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M128_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M128_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_write_execution_policy(
                connectors.ConnectorWriteExecutionLowRiskPolicy(**{field: True})
            )
