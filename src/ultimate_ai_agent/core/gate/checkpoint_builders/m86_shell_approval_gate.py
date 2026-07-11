from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m66_scoped_approval_bundles import _bundle as _scoped_bundle
from ultimate_ai_agent.core.gate.checkpoint_builders.m66_scoped_approval_bundles import _scope as _approval_scope
from ultimate_ai_agent.core.autonomy import AutonomyRiskClass
from ultimate_ai_agent.core.sandbox import (
    CommandProposalRequest,
    ReadOnlyCommandAllowlistDecision,
    ReadOnlyCommandAllowlistEntry,
    ReadOnlyCommandAllowlistRequest,
    SandboxedEchoNoOpCommandRequest,
    ShellApprovalGateRequest,
    ShellDryRunClassifierRequest,
    build_command_proposal,
    build_read_only_command_allowlist_decision,
    build_sandboxed_echo_noop_command,
    build_shell_dry_run_classification,
)


def _allowlist_decision(command_ref: str = "command-ref:m86-safe-noop") -> ReadOnlyCommandAllowlistDecision:
    proposal = build_command_proposal(
        CommandProposalRequest(
            request_ref="command-proposal-request:m86-base",
            proposal_ref="command-proposal:m86-base",
            sandbox_spec_ref="runtime-sandbox-spec:m81",
            baseline_ref="baseline:v0.89.0",
            actor_ref="actor:local-reviewer",
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
            ],
            command_ref=command_ref,
            safe_purpose="Describe a no-effect command proposal for shell approval gate review.",
            safe_command_label="shell approval noop review",
            argv_preview=["safe-noop", "--dry-summary"],
        )
    )
    classification = build_shell_dry_run_classification(
        ShellDryRunClassifierRequest(
            request_ref="shell-dry-run-classifier-request:m86-base",
            classifier_ref="shell-dry-run-classifier:m86-base",
            command_proposal_ref=proposal.proposal_ref,
            sandbox_spec_ref=proposal.sandbox_spec_ref,
            baseline_ref="baseline:v0.89.0",
            actor_ref=proposal.actor_ref,
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
                "milestone:M82",
            ],
            command_proposal=proposal,
        )
    )
    sandboxed = build_sandboxed_echo_noop_command(
        SandboxedEchoNoOpCommandRequest(
            request_ref="sandboxed-echo-noop-command-request:m86-base",
            sandboxed_command_ref="sandboxed-echo-noop-command:m86-base",
            shell_dry_run_classifier_ref=classification.classifier_ref,
            shell_dry_run_decision_ref=classification.decision_ref,
            command_proposal_ref=classification.command_proposal_ref,
            sandbox_spec_ref=classification.sandbox_spec_ref,
            baseline_ref="baseline:v0.89.0",
            actor_ref=classification.actor_ref,
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
                "milestone:M82",
                "milestone:M83",
            ],
            safe_echo_text="M86 safe in-process echo/no-op upstream review text.",
            shell_dry_run_classification=classification,
        )
    )
    request = ReadOnlyCommandAllowlistRequest(
        request_ref="read-only-command-allowlist-request:m86-base",
        allowlist_ref="read-only-command-allowlist:m86",
        sandboxed_command_ref=sandboxed.sandboxed_command_ref,
        sandboxed_echo_noop_decision_ref=sandboxed.decision_ref,
        shell_dry_run_decision_ref=sandboxed.shell_dry_run_decision_ref,
        command_proposal_ref=sandboxed.command_proposal_ref,
        command_ref=command_ref,
        sandbox_spec_ref=sandboxed.sandbox_spec_ref,
        baseline_ref="baseline:v0.89.0",
        actor_ref=sandboxed.actor_ref,
        prior_milestone_refs=[
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
            "milestone:M84",
        ],
        sandboxed_echo_noop_decision=sandboxed,
        entries=[
            ReadOnlyCommandAllowlistEntry(
                entry_ref="read-only-command-allowlist-entry:m86-noop",
                command_ref=command_ref,
                safe_command_label="shell approval noop review",
                safe_argument_profile_ref="safe-argument-profile:m86-noop",
                reviewed_by_actor_ref=sandboxed.actor_ref,
            )
        ],
        requested_command_ref=command_ref,
        safe_purpose="Review a read-only command allowlist entry before shell approval gate evaluation.",
    )
    return build_read_only_command_allowlist_decision(request)


def _approval_bundle(allowlist_decision: ReadOnlyCommandAllowlistDecision | None = None, **overrides: Any) -> Any:
    decision = allowlist_decision or _allowlist_decision()
    scope = overrides.pop(
        "source_scope",
        _approval_scope(
            scope_ref="autonomy-session-scope:m86-shell-gate",
            resource_refs=[decision.command_ref, decision.sandbox_spec_ref],
            capability_refs=["capability:shell-approval-gate-review"],
            allowlist_refs=[decision.allowlist_ref],
            risk_class=AutonomyRiskClass.low,
            revocation_ref="revocation:m86-shell-gate",
            audit_ref="audit:m86-shell-gate",
            replay_ref="replay:m86-shell-gate",
        ),
    )
    data = {
        "bundle_ref": "scoped-approval-bundle:m86-shell-gate",
        "source_scope": scope,
        "approval_refs": ["approval:m86-shell-gate"],
        "actor_ref": decision.actor_ref,
        "resource_refs": [decision.command_ref, decision.sandbox_spec_ref],
        "capability_refs": ["capability:shell-approval-gate-review"],
        "allowlist_refs": [decision.allowlist_ref],
        "max_duration_seconds": scope.max_duration_seconds,
        "risk_class": scope.risk_class,
        "revocation_ref": scope.revocation_ref,
        "audit_ref": scope.audit_ref,
        "replay_ref": scope.replay_ref,
    }
    data.update(overrides)
    return _scoped_bundle(**data)


def _request(**overrides: Any) -> Any:
    allowlist_decision = overrides.pop("read_only_command_allowlist_decision", _allowlist_decision())
    approval_bundle = overrides.pop("approval_bundle", _approval_bundle(allowlist_decision))
    data = {
        "request_ref": "shell-approval-gate-request:m86",
        "gate_ref": "shell-approval-gate:m86",
        "read_only_command_allowlist_decision_ref": allowlist_decision.decision_ref,
        "allowlist_ref": allowlist_decision.allowlist_ref,
        "sandboxed_command_ref": allowlist_decision.sandboxed_command_ref,
        "sandboxed_echo_noop_decision_ref": allowlist_decision.sandboxed_echo_noop_decision_ref,
        "shell_dry_run_decision_ref": allowlist_decision.shell_dry_run_decision_ref,
        "command_proposal_ref": allowlist_decision.command_proposal_ref,
        "command_ref": allowlist_decision.command_ref,
        "sandbox_spec_ref": allowlist_decision.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.89.0",
        "actor_ref": allowlist_decision.actor_ref,
        "approval_bundle_ref": approval_bundle.bundle_ref,
        "approval_ref": "approval:m86-shell-gate",
        "revocation_ref": approval_bundle.revocation_ref,
        "audit_ref": approval_bundle.audit_ref,
        "replay_ref": approval_bundle.replay_ref,
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
            "milestone:M84",
            "milestone:M85",
        ],
        "read_only_command_allowlist_decision": allowlist_decision,
        "approval_bundle": approval_bundle,
        "safe_purpose": "Evaluate a shell approval gate decision for review without shell execution.",
    }
    data.update(overrides)
    return ShellApprovalGateRequest(**data)
