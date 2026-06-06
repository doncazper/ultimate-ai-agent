import pytest

from tests.test_m66_scoped_approval_bundles import _bundle as _scoped_bundle
from tests.test_m66_scoped_approval_bundles import _scope as _approval_scope
from ultimate_ai_agent.core.autonomy import AutonomyRiskClass
from ultimate_ai_agent.core.sandbox import (
    CommandProposalRequest,
    ReadOnlyCommandAllowlistDecision,
    ReadOnlyCommandAllowlistEntry,
    ReadOnlyCommandAllowlistRequest,
    SandboxedEchoNoOpCommandRequest,
    ShellApprovalGatePolicy,
    ShellApprovalGateRequest,
    ShellApprovalGateStatus,
    ShellDryRunClassifierRequest,
    build_command_proposal,
    build_read_only_command_allowlist_decision,
    build_sandboxed_echo_noop_command,
    build_shell_approval_gate_decision,
    build_shell_dry_run_classification,
    validate_shell_approval_gate_decision,
    validate_shell_approval_gate_policy,
    validate_shell_approval_gate_request,
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


def _approval_bundle(allowlist_decision: ReadOnlyCommandAllowlistDecision | None = None, **overrides):
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


def _request(**overrides):
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


def test_m86_shell_approval_gate_is_review_only_and_non_executing() -> None:
    decision = build_shell_approval_gate_decision(_request())

    assert decision.status == ShellApprovalGateStatus.approved_for_review
    assert decision.approval_valid_for_review is True
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.read_only_only is True
    assert decision.approval_ref_is_identifier_only is True
    assert decision.approval_bound_to_allowlist is True
    assert decision.approval_bound_to_command is True
    assert decision.approval_bound_to_actor is True
    assert decision.approval_bound_to_sandbox is True
    assert decision.command_execution_authorized is False
    assert decision.shell_execution_authorized is False
    assert decision.subprocess_execution_authorized is False
    assert decision.process_spawn_authorized is False
    assert decision.command_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.subprocess_execution_performed is False
    assert decision.process_spawn_performed is False
    assert decision.filesystem_mutation_performed is False
    assert decision.network_access_performed is False
    assert decision.tool_execution_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.remote_execution_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.background_worker_started is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_shell_string is False
    assert decision.receipt_plan.store_raw_output is False
    assert decision.reason_codes == [
        "M86_SHELL_APPROVAL_GATE_REVIEW_ONLY",
        "M86_EXACT_M85_ALLOWLIST_BINDING_REQUIRED",
        "M86_APPROVAL_BUNDLE_EXACT_SCOPE_REQUIRED",
        "M86_NO_SHELL_EXECUTION",
        "M87_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_shell_string", "M86_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M86_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M86_RAW_OUTPUT_DENIED"),
        ("contains_secret", "SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED"),
    ],
)
def test_m86_shell_approval_gate_denies_execution_and_raw_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_shell_approval_gate_request(_request(**{field: True}))


def test_m86_shell_approval_gate_requires_m85_prior_ref() -> None:
    with pytest.raises(ValueError, match="M86_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_shell_approval_gate_request(
            _request(
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                    "milestone:M84",
                ]
            )
        )


def test_m86_shell_approval_gate_revalidates_model_copy_mutated_allowlist_decision() -> None:
    allowlist_decision = _allowlist_decision()
    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        build_shell_approval_gate_decision(
            _request(
                read_only_command_allowlist_decision=allowlist_decision.model_copy(
                    update={"command_execution_authorized": True}
                )
            )
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"approval_ref": "approval:m86-other"}, "M86_APPROVAL_REF_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m86"}, "APPROVAL_TEST_REF_DENIED"),
        ({"approval_bundle_ref": "scoped-approval-bundle:other"}, "M86_APPROVAL_BUNDLE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other-reviewer"}, "M86_ACTOR_BINDING_MISMATCH"),
        ({"command_ref": "command-ref:other"}, "M86_COMMAND_BINDING_MISMATCH"),
        ({"allowlist_ref": "read-only-command-allowlist:other"}, "M86_ALLOWLIST_BINDING_MISMATCH"),
        ({"sandbox_spec_ref": "runtime-sandbox-spec:other"}, "M86_SANDBOX_SPEC_BINDING_MISMATCH"),
    ],
)
def test_m86_shell_approval_gate_requires_exact_binding(update: dict[str, str], reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        build_shell_approval_gate_decision(_request(**update))


@pytest.mark.parametrize(
    ("approval_bundle_update", "reason"),
    [
        ({"approval_refs": ["approval:m86-other"]}, "M86_APPROVAL_REF_BINDING_MISMATCH"),
        ({"approval_refs": ["approval_test_:m86"]}, "APPROVAL_TEST_REF_DENIED"),
        ({"revoked": True}, "APPROVAL_BUNDLE_REVOKED_DENIED"),
        ({"expired": True}, "APPROVAL_BUNDLE_EXPIRED_DENIED"),
        ({"replay_used": True}, "APPROVAL_BUNDLE_REPLAY_DENIED"),
        ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ],
)
def test_m86_shell_approval_gate_revalidates_approval_bundle(
    approval_bundle_update: dict[str, object], reason: str
) -> None:
    allowlist_decision = _allowlist_decision()
    with pytest.raises(ValueError, match=reason):
        build_shell_approval_gate_decision(
            _request(
                read_only_command_allowlist_decision=allowlist_decision,
                approval_bundle=_approval_bundle(allowlist_decision).model_copy(
                    update=approval_bundle_update
                ),
            )
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
        ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m86_shell_approval_gate_policy_denies_authority_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_shell_approval_gate_policy(ShellApprovalGatePolicy(**{field: True}))


def test_m86_shell_approval_gate_revalidates_receipt_and_decision_flags() -> None:
    decision = build_shell_approval_gate_decision(_request())
    for update, reason in [
        ({"shell_execution_authorized": True}, "SHELL_EXECUTION_DENIED"),
        ({"shell_execution_performed": True}, "SHELL_EXECUTION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_shell_approval_gate_decision(decision.model_copy(update=update))

    for update, reason in [
        ({"store_raw_command": True}, "M86_RAW_COMMAND_DENIED"),
        ({"store_shell_string": True}, "M86_SHELL_STRING_DENIED"),
        ({"store_raw_output": True}, "M86_RAW_OUTPUT_DENIED"),
        ({"shell_execution_performed": True}, "SHELL_EXECUTION_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_shell_approval_gate_decision(
                decision.model_copy(update={"receipt_plan": decision.receipt_plan.model_copy(update=update)})
            )
