from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m69_low_risk_autonomous_dry_run import _record as _m69_record
from ultimate_ai_agent.core.gate.checkpoint_builders.m91_autonomous_tool_execution_contract import _request as _m91_request
from ultimate_ai_agent.core.tools import build_autonomous_tool_execution_contract
from ultimate_ai_agent.core.autonomy import (
    LowRiskToolAutonomySingleSessionRequest,
)


def _m91_decision() -> Any:
    return build_autonomous_tool_execution_contract(_m91_request())


def _request(**overrides: Any) -> Any:
    m91_decision = overrides.pop("m91_contract_decision", _m91_decision())
    dry_run_record = overrides.pop("low_risk_dry_run_record", _m69_record())
    data = {
        "request_ref": "low-risk-tool-autonomy-single-session-request:m92",
        "single_session_ref": "autonomy-single-session:m92-review-only",
        "m91_contract_decision_ref": m91_decision.decision_ref,
        "low_risk_dry_run_record_ref": dry_run_record.record_ref,
        "actor_ref": m91_decision.actor_ref,
        "approval_ref": m91_decision.approval_ref,
        "tool_intent_ref": m91_decision.tool_intent_ref,
        "tool_runtime_ref": m91_decision.tool_runtime_ref,
        "capability_ref": m91_decision.capability_ref,
        "safe_tool_ref": m91_decision.safe_tool_ref,
        "safe_execution_scope_ref": m91_decision.safe_execution_scope_ref,
        "audit_ref": m91_decision.audit_ref,
        "replay_ref": m91_decision.replay_ref,
        "safe_session_summary": (
            "Define one low-risk tool autonomy session for human review without execution."
        ),
        "safe_tool_refs": ["tool:m92-low-risk-review-only"],
        "prior_milestone_refs": ["milestone:M69", "milestone:M90", "milestone:M91"],
        "m91_contract_decision": m91_decision,
        "low_risk_dry_run_record": dry_run_record,
    }
    data.update(overrides)
    return LowRiskToolAutonomySingleSessionRequest(**data)
