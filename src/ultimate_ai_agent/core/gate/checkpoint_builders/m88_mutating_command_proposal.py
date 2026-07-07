from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m87_sandboxed_command_audit_replay import _request as _m87_request
from ultimate_ai_agent.core.sandbox import (
    MutatingCommandProposalPolicy,
    MutatingCommandProposalRequest,
    MutatingCommandProposalStatus,
    build_mutating_command_proposal,
    build_sandboxed_command_audit_replay,
    validate_mutating_command_proposal_decision,
    validate_mutating_command_proposal_policy,
    validate_mutating_command_proposal_request,
)


def _m87_decision() -> Any:
    return build_sandboxed_command_audit_replay(_m87_request())


def _request(**overrides: Any) -> Any:
    replay = overrides.pop("sandboxed_command_audit_replay_decision", _m87_decision())
    data = {
        "request_ref": "mutating-command-proposal-request:m88",
        "mutating_proposal_ref": "mutating-command-proposal:m88",
        "sandboxed_command_audit_replay_decision_ref": replay.decision_ref,
        "shell_approval_gate_decision_ref": replay.shell_approval_gate_decision_ref,
        "approval_bundle_ref": replay.approval_bundle_ref,
        "approval_ref": replay.approval_ref,
        "command_ref": replay.command_ref,
        "sandbox_spec_ref": replay.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.91.0",
        "actor_ref": replay.actor_ref,
        "audit_ref": replay.audit_ref,
        "replay_ref": replay.replay_ref,
        "mutation_intent_ref": "mutation-intent:m88-review-only",
        "mutation_scope_ref": "mutation-scope:m88-safe-summary",
        "safe_mutation_summary": "Review a proposed mutating command as safe metadata only.",
        "safe_argument_refs": ["argument-ref:m88-review-only"],
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
        ],
        "sandboxed_command_audit_replay_decision": replay,
    }
    data.update(overrides)
    return MutatingCommandProposalRequest(**data)
