from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m88_mutating_command_proposal import _request as _m88_request
from ultimate_ai_agent.core.sandbox import (
    EmergencyStopProcessKillSafetyPolicy,
    EmergencyStopProcessKillSafetyRequest,
    EmergencyStopProcessKillSafetyStatus,
    build_emergency_stop_process_kill_safety,
    build_mutating_command_proposal,
    validate_emergency_stop_process_kill_safety_decision,
    validate_emergency_stop_process_kill_safety_policy,
    validate_emergency_stop_process_kill_safety_request,
)


def _m88_decision() -> Any:
    return build_mutating_command_proposal(_m88_request())


def _request(**overrides: Any) -> Any:
    proposal = overrides.pop("mutating_command_proposal_decision", _m88_decision())
    data = {
        "request_ref": "emergency-stop-process-kill-safety-request:m89",
        "emergency_stop_safety_ref": "emergency-stop-safety:m89",
        "process_kill_safety_ref": "process-kill-safety:m89",
        "mutating_command_proposal_decision_ref": proposal.decision_ref,
        "sandboxed_command_audit_replay_decision_ref": proposal.sandboxed_command_audit_replay_decision_ref,
        "shell_approval_gate_decision_ref": proposal.shell_approval_gate_decision_ref,
        "approval_bundle_ref": proposal.approval_bundle_ref,
        "approval_ref": proposal.approval_ref,
        "command_ref": proposal.command_ref,
        "sandbox_spec_ref": proposal.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.92.0",
        "actor_ref": proposal.actor_ref,
        "audit_ref": proposal.audit_ref,
        "replay_ref": proposal.replay_ref,
        "mutation_intent_ref": proposal.mutation_intent_ref,
        "mutation_scope_ref": proposal.mutation_scope_ref,
        "safe_target_process_ref": "process-target-ref:m89-safe-ref",
        "safe_emergency_scope_ref": "emergency-scope-ref:m89-safe-ref",
        "safe_stop_summary": "Review emergency stop and process kill safety as safe metadata only.",
        "safe_reason_refs": ["safety-reason-ref:m89-review-only"],
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
            "milestone:M84",
            "milestone:M85",
            "milestone:M86",
            "milestone:M87",
            "milestone:M88",
        ],
        "mutating_command_proposal_decision": proposal,
    }
    data.update(overrides)
    return EmergencyStopProcessKillSafetyRequest(**data)
