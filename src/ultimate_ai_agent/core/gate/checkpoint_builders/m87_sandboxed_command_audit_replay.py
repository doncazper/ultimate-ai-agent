from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m86_shell_approval_gate import _request as _m86_request
from ultimate_ai_agent.core.sandbox import (
    SandboxedCommandAuditReplayRequest,
    SandboxedCommandAuditReplayStep,
    build_shell_approval_gate_decision,
)


def _m86_decision() -> Any:
    return build_shell_approval_gate_decision(_m86_request())


def _step(step_ref: str = "sandboxed-command-audit-replay-step:m87-gate") -> SandboxedCommandAuditReplayStep:
    gate = _m86_decision()
    return SandboxedCommandAuditReplayStep(
        step_ref=step_ref,
        event_ref="audit-event:m87-shell-gate-reviewed",
        source_decision_ref=gate.decision_ref,
        safe_summary="Replay view records the M86 shell approval gate review decision only.",
        reason_codes=["M87_REPLAY_VIEW_STEP_ONLY", "M87_NO_COMMAND_EXECUTION"],
    )


def _request(**overrides: Any) -> Any:
    gate = overrides.pop("shell_approval_gate_decision", _m86_decision())
    replay_steps = overrides.pop("replay_steps", [_step()])
    data = {
        "request_ref": "sandboxed-command-audit-replay-request:m87",
        "replay_view_ref": "sandboxed-command-audit-replay:m87",
        "shell_approval_gate_decision_ref": gate.decision_ref,
        "read_only_command_allowlist_decision_ref": gate.read_only_command_allowlist_decision_ref,
        "approval_bundle_ref": gate.approval_bundle_ref,
        "approval_ref": gate.approval_ref,
        "allowlist_ref": gate.allowlist_ref,
        "command_ref": gate.command_ref,
        "sandbox_spec_ref": gate.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.90.0",
        "actor_ref": gate.actor_ref,
        "audit_ref": "audit:m86-shell-gate",
        "replay_ref": "replay:m86-shell-gate",
        "replay_step_refs": [step.step_ref for step in replay_steps],
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
        ],
        "shell_approval_gate_decision": gate,
        "replay_steps": replay_steps,
        "safe_purpose": "Review a sandboxed command audit replay without running or retrying commands.",
    }
    data.update(overrides)
    return SandboxedCommandAuditReplayRequest(**data)
