from __future__ import annotations

from typing import Any
from datetime import timedelta
from importlib import import_module
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


def _connectors() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        raise RuntimeError("M127 connectors package missing") from exc


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


def _runtime_record() -> Any:
    connectors = _connectors()
    return connectors.build_connector_read_only_runtime_record(
        source_record=_m124_source_record()
    )


def _approval_decision(runtime_record: Any, **overrides: Any) -> Any:
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


def _request(approval_decision: Any, **overrides: Any) -> Any:
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
