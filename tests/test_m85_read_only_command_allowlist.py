import pytest

from ultimate_ai_agent.core.sandbox import (
    CommandProposalRequest,
    ReadOnlyCommandAllowlistDecision,
    ReadOnlyCommandAllowlistEntry,
    ReadOnlyCommandAllowlistPolicy,
    ReadOnlyCommandAllowlistStatus,
    SandboxedEchoNoOpCommandRequest,
    ShellDryRunClassifierRequest,
    build_command_proposal,
    build_read_only_command_allowlist_decision,
    build_sandboxed_echo_noop_command,
    build_shell_dry_run_classification,
    validate_read_only_command_allowlist_decision,
    validate_read_only_command_allowlist_entry,
    validate_read_only_command_allowlist_policy,
    validate_read_only_command_allowlist_request,
)
from ultimate_ai_agent.core.sandbox.read_only_command_allowlist import (
    ReadOnlyCommandAllowlistRequest,
)


def _sandboxed_echo_decision(command_ref: str = "command-ref:safe-noop"):
    proposal = build_command_proposal(
        CommandProposalRequest(
            request_ref="command-proposal-request:m85-base",
            proposal_ref="command-proposal:m85-base",
            sandbox_spec_ref="runtime-sandbox-spec:m81",
            baseline_ref="baseline:v0.88.0",
            actor_ref="actor:local-reviewer",
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
            ],
            command_ref=command_ref,
            safe_purpose="Describe a no-effect command proposal for allowlist review.",
            safe_command_label="allowlisted noop review",
            argv_preview=["safe-noop", "--dry-summary"],
        )
    )
    classification = build_shell_dry_run_classification(
        ShellDryRunClassifierRequest(
            request_ref="shell-dry-run-classifier-request:m85-base",
            classifier_ref="shell-dry-run-classifier:m85-base",
            command_proposal_ref=proposal.proposal_ref,
            sandbox_spec_ref=proposal.sandbox_spec_ref,
            baseline_ref="baseline:v0.88.0",
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
    return build_sandboxed_echo_noop_command(
        SandboxedEchoNoOpCommandRequest(
            request_ref="sandboxed-echo-noop-command-request:m85-base",
            sandboxed_command_ref="sandboxed-echo-noop-command:m85-base",
            shell_dry_run_classifier_ref=classification.classifier_ref,
            shell_dry_run_decision_ref=classification.decision_ref,
            command_proposal_ref=classification.command_proposal_ref,
            sandbox_spec_ref=classification.sandbox_spec_ref,
            baseline_ref="baseline:v0.88.0",
            actor_ref=classification.actor_ref,
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
                "milestone:M82",
                "milestone:M83",
            ],
            safe_echo_text="M85 safe in-process echo/no-op upstream review text.",
            shell_dry_run_classification=classification,
        )
    )


def _entry(command_ref: str = "command-ref:safe-noop"):
    return ReadOnlyCommandAllowlistEntry(
        entry_ref="read-only-command-allowlist-entry:m85-noop",
        command_ref=command_ref,
        safe_command_label="allowlisted noop review",
        safe_argument_profile_ref="safe-argument-profile:m85-noop",
        reviewed_by_actor_ref="actor:local-reviewer",
    )


def _request(**overrides):
    upstream = overrides.pop("sandboxed_echo_noop_decision", _sandboxed_echo_decision())
    command_ref = overrides.pop("requested_command_ref", "command-ref:safe-noop")
    data = {
        "request_ref": "read-only-command-allowlist-request:m85",
        "allowlist_ref": "read-only-command-allowlist:m85",
        "sandboxed_command_ref": upstream.sandboxed_command_ref,
        "sandboxed_echo_noop_decision_ref": upstream.decision_ref,
        "shell_dry_run_decision_ref": upstream.shell_dry_run_decision_ref,
        "command_proposal_ref": upstream.command_proposal_ref,
        "command_ref": command_ref,
        "sandbox_spec_ref": upstream.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.88.0",
        "actor_ref": upstream.actor_ref,
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
            "milestone:M84",
        ],
        "sandboxed_echo_noop_decision": upstream,
        "entries": [_entry(command_ref)],
        "requested_command_ref": command_ref,
        "safe_purpose": "Review whether a no-effect command ref is on the read-only allowlist.",
    }
    data.update(overrides)
    return ReadOnlyCommandAllowlistRequest(**data)


def test_m85_read_only_command_allowlist_is_review_only_and_non_executing() -> None:
    decision = build_read_only_command_allowlist_decision(_request())

    assert decision.status == ReadOnlyCommandAllowlistStatus.allowlisted_for_review
    assert decision.allowlist_match_found is True
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.read_only_only is True
    assert decision.command_execution_authorized is False
    assert decision.shell_execution_authorized is False
    assert decision.subprocess_execution_authorized is False
    assert decision.process_spawn_authorized is False
    assert decision.command_execution_performed is False
    assert decision.subprocess_execution_performed is False
    assert decision.shell_execution_performed is False
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
    assert decision.receipt_plan.store_allowlist_refs_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_shell_string is False
    assert decision.receipt_plan.store_raw_output is False
    assert decision.reason_codes == [
        "M85_READ_ONLY_COMMAND_ALLOWLIST_CONTRACT_ONLY",
        "M85_EXACT_M84_BINDING_REQUIRED",
        "M85_NO_COMMAND_EXECUTION",
        "M86_REMAINS_FUTURE",
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
        ("contains_shell_string", "M85_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M85_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M85_RAW_OUTPUT_DENIED"),
        ("contains_secret", "SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED"),
    ],
)
def test_m85_read_only_command_allowlist_denies_execution_and_raw_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_read_only_command_allowlist_request(_request(**{field: True}))


def test_m85_read_only_command_allowlist_requires_m84_prior_ref() -> None:
    with pytest.raises(ValueError, match="M85_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_read_only_command_allowlist_request(
            _request(
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                ]
            )
        )


def test_m85_read_only_command_allowlist_requires_exact_m84_binding() -> None:
    with pytest.raises(ValueError, match="M85_M84_BINDING_MISMATCH"):
        validate_read_only_command_allowlist_request(
            _request(sandboxed_echo_noop_decision_ref="sandboxed-echo-noop-command-decision:mismatch")
        )


def test_m85_read_only_command_allowlist_requires_matching_entry() -> None:
    with pytest.raises(ValueError, match="M85_ALLOWLIST_ENTRY_NOT_FOUND"):
        validate_read_only_command_allowlist_request(
            _request(
                requested_command_ref="command-ref:not-allowlisted",
                command_ref="command-ref:not-allowlisted",
                entries=[_entry("command-ref:safe-noop")],
            )
        )


def test_m85_read_only_command_allowlist_rejects_duplicate_command_entries() -> None:
    with pytest.raises(ValueError, match="M85_ALLOWLIST_COMMAND_DUPLICATE"):
        validate_read_only_command_allowlist_request(
            _request(
                entries=[
                    _entry("command-ref:safe-noop"),
                    _entry("command-ref:safe-noop").model_copy(
                        update={"entry_ref": "read-only-command-allowlist-entry:m85-noop-2"}
                    ),
                ]
            )
        )


def test_m85_read_only_command_allowlist_entry_denies_authority() -> None:
    unsafe = _entry().model_copy(
        update={
            "command_execution_authorized": True,
            "production_authority_authorized": True,
        }
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_read_only_command_allowlist_entry(unsafe)


def test_m85_read_only_command_allowlist_policy_denies_execution_enablement() -> None:
    policy = ReadOnlyCommandAllowlistPolicy(
        command_execution_enabled=True,
        shell_execution_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_read_only_command_allowlist_policy(policy)


def test_m85_read_only_command_allowlist_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "shell_execution_requested": True,
            "contains_raw_command": True,
        }
    )

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_read_only_command_allowlist_decision(request)


def test_m85_read_only_command_allowlist_revalidates_mutated_m84_decision() -> None:
    upstream = _sandboxed_echo_decision().model_copy(update={"shell_execution_performed": True})

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_read_only_command_allowlist_decision(
            _request(sandboxed_echo_noop_decision=upstream)
        )


def test_m85_read_only_command_allowlist_decision_revalidation_denies_authority() -> None:
    decision = build_read_only_command_allowlist_decision(_request()).model_copy(
        update={
            "command_execution_authorized": True,
            "command_execution_performed": True,
        }
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_read_only_command_allowlist_decision(decision)


def test_m85_read_only_command_allowlist_receipt_stores_no_raw_command_or_output() -> None:
    decision = build_read_only_command_allowlist_decision(_request())
    unsafe = ReadOnlyCommandAllowlistDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "store_raw_command": True,
                "store_raw_output": True,
            },
        }
    )

    with pytest.raises(ValueError, match="M85_RECEIPT_RAW_COMMAND_DENIED"):
        validate_read_only_command_allowlist_decision(unsafe)


def test_m85_read_only_command_allowlist_receipt_revalidates_exact_bindings() -> None:
    decision = build_read_only_command_allowlist_decision(_request())
    unsafe = ReadOnlyCommandAllowlistDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "sandboxed_echo_noop_decision_ref": "sandboxed-echo-noop-command-decision:mismatch",
            },
        }
    )

    with pytest.raises(ValueError, match="M85_RECEIPT_BINDING_MISMATCH"):
        validate_read_only_command_allowlist_decision(unsafe)
