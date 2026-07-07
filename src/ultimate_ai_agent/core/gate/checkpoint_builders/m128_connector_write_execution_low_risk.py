from __future__ import annotations
from typing import Any
from functools import lru_cache
from ultimate_ai_agent.core.gate.checkpoint_builders.m127_connector_write_dry_run_planner import (
    _approval_decision,
    _request as _m127_request,
    _runtime_record,
)
from ultimate_ai_agent.core.time import utc_now


def _m127_decision() -> Any:
    connectors = _connectors()
    runtime_record = _runtime_record()
    approval_decision = _approval_decision(runtime_record)
    request = _m127_request(approval_decision)
    return connectors.plan_connector_write_dry_run(
        approval_decision, request, current_time=utc_now()
    )


def _connectors() -> Any:
    import ultimate_ai_agent.core.connectors as connectors

    return connectors


def _request(**overrides: Any) -> Any:
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


def _transport(_decision: Any) -> Any:
    connectors = _connectors()
    return connectors.ConnectorWriteExecutionTransportResponse(
        write_completed=True,
        safe_result_ref="connector-write-result-ref:m128:email-draft",
        safe_summary="Safe connector draft write completed.",
    )
