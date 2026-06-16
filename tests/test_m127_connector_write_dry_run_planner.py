from datetime import timedelta
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
        pytest.fail(f"M127 connectors package missing: {exc}")


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


def _runtime_record():
    connectors = _connectors()
    return connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )


def _approval_decision(runtime_record, **overrides):
    connectors = _connectors()
    data = {
        "approval_ref": "connector-approval-capture:m126:m127-source",
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
        "audit_ref": "audit-ref:m126:m127-source",
        "replay_ref": "replay-ref:m126:m127-source",
        "no_effect_receipt_plan_ref": (
            "receipt-plan-ref:m126:m127-source:no-effect"
        ),
        "decision": connectors.ConnectorApprovalDecisionKind.approve_review_only,
        "idempotency_key": "idempotency-ref:m126:m127-source",
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
        "safe_reason": "User reviewed safe connector metadata refs only.",
        "metadata_refs": ["metadata-ref:m126:m127-source"],
    }
    data.update(overrides)
    request = connectors.ConnectorApprovalCaptureRequest(**data)
    return connectors.capture_connector_approval(
        runtime_record, request, current_time=utc_now()
    )


def _request(approval_decision, **overrides):
    connectors = _connectors()
    assert approval_decision.record is not None
    record = approval_decision.record
    data = {
        "dry_run_request_ref": "connector-write-dry-run-request:m127:email-draft",
        "approval_ref": record.approval_ref,
        "connector_read_only_runtime_ref": record.connector_read_only_runtime_ref,
        "source_messages_connector_contract_review_ref": (
            record.source_messages_connector_contract_review_ref
        ),
        "source_baseline_ref": record.source_baseline_ref,
        "actor_ref": record.actor_ref,
        "user_ref": record.user_ref,
        "workspace_ref": record.workspace_ref,
        "connector_scope_refs": record.connector_scope_refs,
        "connector_allowlist_refs": record.connector_allowlist_refs,
        "source_operation_allowlist_refs": record.operation_allowlist_refs,
        "redacted_metadata_preview_refs": record.redacted_metadata_preview_refs,
        "dry_run_operation_refs": [
            "connector-write-dry-run-operation-ref:m127:plan-email-draft"
        ],
        "write_target_refs": ["connector-write-target-ref:m127:email-draft-safe-ref"],
        "safe_payload_summary_refs": [
            "safe-payload-summary-ref:m127:email-draft-summary"
        ],
        "data_minimization_refs": [
            "data-minimization-ref:m127:headers-and-safe-summary-only"
        ],
        "redaction_refs": ["redaction-ref:m127:no-recipient-body-or-secret"],
        "audit_ref": "audit-ref:m127:connector-write-dry-run",
        "replay_ref": "replay-ref:m127:connector-write-dry-run",
        "idempotency_key": "idempotency-ref:m127:connector-write-dry-run",
        "dry_run_receipt_plan_ref": (
            "receipt-plan-ref:m127:connector-write-dry-run:no-effect"
        ),
        "action_kind": connectors.ConnectorWriteDryRunActionKind.plan_email_draft,
        "requested_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
        "safe_reason": "Plan an email draft from safe refs only.",
        "metadata_refs": ["metadata-ref:m127:connector-write-dry-run"],
    }
    data.update(overrides)
    return connectors.ConnectorWriteDryRunRequest(**data)


def test_m127_connector_write_dry_run_plans_safe_refs_without_authority():
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _request(approval_decision)

    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorWriteDryRunStatus.planned_for_review
    assert decision.planned is True
    assert decision.persisted is True
    assert decision.dry_run_only is True
    assert decision.plan is not None
    assert decision.receipt_plan is not None
    assert decision.plan.approval_ref == approval_decision.approval_ref
    assert decision.plan.connector_read_only_runtime_ref == (
        runtime_record.connector_read_only_runtime_ref
    )
    assert decision.plan.actor_ref == runtime_record.actor_ref
    assert decision.plan.user_ref == runtime_record.user_ref
    assert decision.plan.workspace_ref == runtime_record.workspace_ref
    assert decision.plan.dry_run_operation_refs == [
        "connector-write-dry-run-operation-ref:m127:plan-email-draft"
    ]
    assert decision.plan.write_target_refs == [
        "connector-write-target-ref:m127:email-draft-safe-ref"
    ]
    assert decision.receipt_plan.connector_write_performed is False
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
    assert "api_key" not in dumped


def test_m127_denies_denied_m126_approval_decision():
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(
        runtime_record,
        decision=connectors.ConnectorApprovalDecisionKind.deny_review_only,
    )
    request = _request(approval_decision)

    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorWriteDryRunStatus.rejected
    assert "M127_SOURCE_APPROVAL_NOT_APPROVED" in decision.reason_codes
    assert decision.planned is False
    assert decision.persisted is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        (
            {"approval_ref": "connector-approval-capture:m126:other"},
            "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_REF_MISMATCH",
        ),
        ({"actor_ref": "actor-ref:m127:other"}, "M127_CONNECTOR_WRITE_DRY_RUN_ACTOR_MISMATCH"),
        ({"user_ref": "user-ref:m127:other"}, "M127_CONNECTOR_WRITE_DRY_RUN_USER_MISMATCH"),
        (
            {"workspace_ref": "workspace-ref:m127:other"},
            "M127_CONNECTOR_WRITE_DRY_RUN_WORKSPACE_MISMATCH",
        ),
        (
            {"connector_read_only_runtime_ref": "connector-read-only-runtime:other"},
            "M127_CONNECTOR_WRITE_DRY_RUN_RUNTIME_REF_MISMATCH",
        ),
        (
            {
                "source_operation_allowlist_refs": [
                    "connector-operation-ref:m125:other"
                ]
            },
            "M127_CONNECTOR_WRITE_DRY_RUN_SOURCE_OPERATION_REF_MISMATCH",
        ),
        (
            {"approval_ref": "approval_test_m127"},
            "M127_CONNECTOR_WRITE_DRY_RUN_TEST_APPROVAL_DENIED",
        ),
        (
            {"expires_at": utc_now() - timedelta(minutes=1)},
            "M127_CONNECTOR_WRITE_DRY_RUN_EXPIRED",
        ),
        ({"revoked_at": utc_now()}, "M127_CONNECTOR_WRITE_DRY_RUN_REVOKED"),
        (
            {
                "replay_nonce": "replay-ref:m127:nonce",
                "used_replay_nonces": ["replay-ref:m127:nonce"],
            },
            "M127_CONNECTOR_WRITE_DRY_RUN_REPLAY_DETECTED",
        ),
        (
            {"dry_run_operation_refs": ["connector-write-dry-run-operation-ref:m127:unknown"]},
            "M127_CONNECTOR_WRITE_DRY_RUN_ACTION_OPERATION_REQUIRED",
        ),
    ],
)
def test_m127_denies_binding_lifecycle_and_allowlist_failures(override, reason):
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _request(approval_decision).model_copy(update=override)

    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorWriteDryRunStatus.rejected
    assert reason in decision.reason_codes
    assert decision.planned is False
    assert decision.persisted is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("live_connector_runtime_enabled", "M127_LIVE_CONNECTOR_RUNTIME_DENIED"),
        ("account_auth_enabled", "M127_ACCOUNT_AUTH_DENIED"),
        ("network_access_enabled", "M127_NETWORK_ACCESS_DENIED"),
        ("credential_handling_enabled", "M127_CREDENTIAL_HANDLING_DENIED"),
        ("raw_connector_content_enabled", "M127_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_content_read_enabled", "M127_FULL_CONTENT_READ_DENIED"),
        ("connector_write_enabled", "M127_CONNECTOR_WRITE_EXECUTION_DENIED"),
        ("connector_send_enabled", "M127_CONNECTOR_SEND_DENIED"),
        ("connector_delete_enabled", "M127_CONNECTOR_DELETE_DENIED"),
        ("connector_export_enabled", "M127_CONNECTOR_EXPORT_DENIED"),
        ("connector_bulk_export_enabled", "M127_CONNECTOR_BULK_EXPORT_DENIED"),
        ("attachment_download_enabled", "M127_ATTACHMENT_DOWNLOAD_DENIED"),
        ("model_call_enabled", "M127_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M127_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M127_CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "M127_EXECUTION_DENIED"),
        ("backend_route_added", "M127_BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "M127_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M127_DEPENDENCY_DENIED"),
    ],
)
def test_m127_model_copy_mutated_request_flags_are_revalidated(flag, reason):
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _request(approval_decision).model_copy(update={flag: True})

    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorWriteDryRunStatus.rejected
    assert reason in decision.reason_codes
    assert decision.planned is False
    assert decision.persisted is False
    assert decision.execution_performed is False


def test_m127_secret_metadata_is_denied_without_echoing_secret():
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _request(approval_decision).model_copy(
        update={"metadata": {"api_key": "connector-secret-abc123"}}
    )

    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.status == connectors.ConnectorWriteDryRunStatus.rejected
    assert "M127_CONNECTOR_WRITE_DRY_RUN_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "connector-secret-abc123" not in decision.safe_message
    assert "connector-secret-abc123" not in str(decision.model_dump(mode="json"))


def test_m127_plan_validation_denies_raw_fields_and_effects():
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _request(approval_decision)
    decision = connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )

    assert decision.plan is not None
    for field, reason in [
        ("raw_connector_content", "M127_RAW_CONNECTOR_CONTENT_DENIED"),
        ("full_connector_content", "M127_FULL_CONTENT_READ_DENIED"),
        ("side_effects_performed", "M127_CONNECTOR_WRITE_DRY_RUN_SIDE_EFFECTS_DENIED"),
        ("connector_write_enabled", "M127_CONNECTOR_WRITE_EXECUTION_DENIED"),
        ("execution_enabled", "M127_EXECUTION_DENIED"),
    ]:
        value = ["write executed"] if field == "side_effects_performed" else True
        with pytest.raises(ValueError, match=reason):
            connectors.validate_connector_write_dry_run_plan(
                decision.plan.model_copy(update={field: value})
            )
