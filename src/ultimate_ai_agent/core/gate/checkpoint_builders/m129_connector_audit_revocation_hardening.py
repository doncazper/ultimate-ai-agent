from __future__ import annotations
from typing import Any
from functools import lru_cache
from ultimate_ai_agent.core.gate.checkpoint_builders.m128_connector_write_execution_low_risk import (
    _request as _m128_request,
    _transport as _m128_transport,
)


def _connectors() -> Any:
    import ultimate_ai_agent.core.connectors as connectors

    return connectors


def _m128_decision_and_result() -> tuple[Any, ...]:
    connectors = _connectors()
    decision = connectors.build_connector_write_execution_decision(_m128_request())
    result = connectors.perform_low_risk_connector_write(
        decision,
        transport=_m128_transport,
    )
    return decision, result


def _request(**overrides: Any) -> Any:
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
