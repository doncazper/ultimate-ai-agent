from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m90_shell_subprocess_hardening_freeze import _request as _m90_request
from ultimate_ai_agent.core.sandbox import build_shell_subprocess_hardening_freeze
from ultimate_ai_agent.core.tools import (
    AutonomousToolExecutionContractPolicy,
    AutonomousToolExecutionContractRequest,
    AutonomousToolExecutionContractStatus,
    build_autonomous_tool_execution_contract,
    validate_autonomous_tool_execution_contract_decision,
    validate_autonomous_tool_execution_contract_policy,
    validate_autonomous_tool_execution_contract_request,
)


def _m90_decision() -> Any:
    return build_shell_subprocess_hardening_freeze(_m90_request())


def _request(**overrides: Any) -> Any:
    m90_decision = overrides.pop("shell_subprocess_hardening_freeze_decision", _m90_decision())
    data = {
        "request_ref": "autonomous-tool-execution-contract-request:m91",
        "contract_ref": "autonomous-tool-execution-contract:m91",
        "shell_subprocess_hardening_freeze_decision_ref": m90_decision.decision_ref,
        "emergency_stop_process_kill_safety_decision_ref": (
            m90_decision.emergency_stop_process_kill_safety_decision_ref
        ),
        "command_ref": m90_decision.command_ref,
        "sandbox_spec_ref": m90_decision.sandbox_spec_ref,
        "approval_bundle_ref": m90_decision.approval_bundle_ref,
        "approval_ref": m90_decision.approval_ref,
        "actor_ref": m90_decision.actor_ref,
        "audit_ref": m90_decision.audit_ref,
        "replay_ref": m90_decision.replay_ref,
        "tool_intent_ref": "tool-intent:m91-review-only",
        "tool_runtime_ref": "tool-runtime:m91-contract-only",
        "capability_ref": "capability:m91-autonomous-tool-contract",
        "autonomy_session_ref": "autonomy-session:m91-not-started",
        "safe_execution_scope_ref": "execution-scope:m91-safe-review-only",
        "safe_tool_ref": "tool:m91-review-only-contract",
        "safe_contract_summary": (
            "Define autonomous tool execution contract requirements without enabling execution."
        ),
        "safe_contract_refs": ["contract-ref:m91-no-real-tool-execution"],
        "prior_milestone_refs": [
            "milestone:M53",
            "milestone:M61",
            "milestone:M62",
            "milestone:M63",
            "milestone:M66",
            "milestone:M67",
            "milestone:M68",
            "milestone:M70",
            "milestone:M80",
            "milestone:M90",
        ],
        "shell_subprocess_hardening_freeze_decision": m90_decision,
    }
    data.update(overrides)
    return AutonomousToolExecutionContractRequest(**data)
