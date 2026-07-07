from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m89_emergency_stop_process_kill_safety import _request as _m89_request
from ultimate_ai_agent.core.sandbox import (
    ShellSubprocessHardeningFreezePolicy,
    ShellSubprocessHardeningFreezeRequest,
    ShellSubprocessHardeningFreezeStatus,
    build_emergency_stop_process_kill_safety,
    build_shell_subprocess_hardening_freeze,
    validate_shell_subprocess_hardening_freeze_decision,
    validate_shell_subprocess_hardening_freeze_policy,
    validate_shell_subprocess_hardening_freeze_request,
)


def _m89_decision() -> Any:
    return build_emergency_stop_process_kill_safety(_m89_request())


def _request(**overrides: Any) -> Any:
    m89_decision = overrides.pop("emergency_stop_process_kill_safety_decision", _m89_decision())
    data = {
        "request_ref": "shell-subprocess-hardening-freeze-request:m90",
        "hardening_freeze_ref": "shell-subprocess-hardening-freeze:m90",
        "emergency_stop_process_kill_safety_decision_ref": m89_decision.decision_ref,
        "mutating_command_proposal_decision_ref": m89_decision.mutating_command_proposal_decision_ref,
        "sandboxed_command_audit_replay_decision_ref": m89_decision.sandboxed_command_audit_replay_decision_ref,
        "shell_approval_gate_decision_ref": m89_decision.shell_approval_gate_decision_ref,
        "approval_bundle_ref": m89_decision.approval_bundle_ref,
        "approval_ref": m89_decision.approval_ref,
        "command_ref": m89_decision.command_ref,
        "sandbox_spec_ref": m89_decision.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.93.0",
        "actor_ref": m89_decision.actor_ref,
        "audit_ref": m89_decision.audit_ref,
        "replay_ref": m89_decision.replay_ref,
        "mutation_intent_ref": m89_decision.mutation_intent_ref,
        "mutation_scope_ref": m89_decision.mutation_scope_ref,
        "safe_target_process_ref": m89_decision.safe_target_process_ref,
        "safe_emergency_scope_ref": m89_decision.safe_emergency_scope_ref,
        "safe_freeze_summary": "Freeze shell, subprocess, process, and emergency boundaries as review-only metadata.",
        "safe_hardening_refs": ["hardening-ref:m90-shell-subprocess-freeze"],
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
            "milestone:M89",
        ],
        "emergency_stop_process_kill_safety_decision": m89_decision,
    }
    data.update(overrides)
    return ShellSubprocessHardeningFreezeRequest(**data)
