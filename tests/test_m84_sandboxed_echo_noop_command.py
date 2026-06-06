import pytest

from ultimate_ai_agent.core.sandbox import (
    CommandProposalRequest,
    SandboxedEchoNoOpCommandDecision,
    SandboxedEchoNoOpCommandPolicy,
    SandboxedEchoNoOpCommandRequest,
    SandboxedEchoNoOpCommandStatus,
    ShellDryRunClass,
    ShellDryRunClassifierRequest,
    build_command_proposal,
    build_sandboxed_echo_noop_command,
    build_shell_dry_run_classification,
    validate_sandboxed_echo_noop_command_decision,
    validate_sandboxed_echo_noop_command_policy,
    validate_sandboxed_echo_noop_command_request,
)


def _command_proposal(command_ref: str = "command-ref:review-noop"):
    return build_command_proposal(
        CommandProposalRequest(
            request_ref="command-proposal-request:m84-base",
            proposal_ref="command-proposal:m84-base",
            sandbox_spec_ref="runtime-sandbox-spec:m81",
            baseline_ref="baseline:v0.87.0",
            actor_ref="actor:local-reviewer",
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
            ],
            command_ref=command_ref,
            safe_purpose="Describe a no-effect command proposal for sandboxed no-op review.",
            safe_command_label="review noop metadata",
            argv_preview=["review-noop", "--dry-summary"],
        )
    )


def _classification(command_ref: str = "command-ref:review-noop"):
    proposal = _command_proposal(command_ref=command_ref)
    return build_shell_dry_run_classification(
        ShellDryRunClassifierRequest(
            request_ref="shell-dry-run-classifier-request:m84-base",
            classifier_ref="shell-dry-run-classifier:m84-base",
            command_proposal_ref=proposal.proposal_ref,
            sandbox_spec_ref=proposal.sandbox_spec_ref,
            baseline_ref="baseline:v0.87.0",
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


def _request(**overrides):
    classification = overrides.pop("shell_dry_run_classification", _classification())
    data = {
        "request_ref": "sandboxed-echo-noop-command-request:m84",
        "sandboxed_command_ref": "sandboxed-echo-noop-command:m84",
        "shell_dry_run_classifier_ref": classification.classifier_ref,
        "shell_dry_run_decision_ref": classification.decision_ref,
        "command_proposal_ref": classification.command_proposal_ref,
        "sandbox_spec_ref": classification.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.87.0",
        "actor_ref": classification.actor_ref,
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
            "milestone:M83",
        ],
        "safe_echo_text": "M84 safe in-process echo/no-op review text.",
        "shell_dry_run_classification": classification,
    }
    data.update(overrides)
    return SandboxedEchoNoOpCommandRequest(**data)


def test_m84_sandboxed_echo_noop_is_in_process_and_non_executing() -> None:
    decision = build_sandboxed_echo_noop_command(_request())

    assert decision.status == SandboxedEchoNoOpCommandStatus.completed_for_review
    assert decision.classification == ShellDryRunClass.no_effect_review
    assert decision.sandboxed_echo_noop_allowed is True
    assert decision.in_process_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_echo_text == "M84 safe in-process echo/no-op review text."
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
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_shell_string is False
    assert decision.receipt_plan.store_raw_output is False
    assert decision.reason_codes == [
        "M84_SANDBOXED_ECHO_NOOP_COMMAND_ONLY",
        "M84_IN_PROCESS_ONLY",
        "M84_NO_SHELL_OR_SUBPROCESS_EXECUTION",
        "M85_REMAINS_FUTURE",
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
        ("contains_shell_string", "M84_SHELL_STRING_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("contains_secret", "SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED"),
    ],
)
def test_m84_sandboxed_echo_noop_denies_execution_and_authority_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_sandboxed_echo_noop_command_request(_request(**{field: True}))


def test_m84_sandboxed_echo_noop_requires_exact_m83_binding() -> None:
    with pytest.raises(ValueError, match="M84_SHELL_DRY_RUN_BINDING_MISMATCH"):
        validate_sandboxed_echo_noop_command_request(
            _request(shell_dry_run_decision_ref="shell-dry-run-classifier-decision:mismatch")
        )


def test_m84_sandboxed_echo_noop_requires_prior_m83() -> None:
    with pytest.raises(ValueError, match="M84_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_sandboxed_echo_noop_command_request(
            _request(
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                ]
            )
        )


def test_m84_sandboxed_echo_noop_rejects_non_no_effect_classification() -> None:
    with pytest.raises(ValueError, match="M84_NO_EFFECT_CLASSIFICATION_REQUIRED"):
        build_sandboxed_echo_noop_command(
            _request(shell_dry_run_classification=_classification(command_ref="command-ref:read-metadata"))
        )


def test_m84_sandboxed_echo_noop_denies_secret_like_echo_text() -> None:
    with pytest.raises(ValueError, match="SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED"):
        build_sandboxed_echo_noop_command(_request(safe_echo_text="api_key=sk_test_secret_value_12345"))


def test_m84_sandboxed_echo_noop_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "shell_execution_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_sandboxed_echo_noop_command(request)


def test_m84_sandboxed_echo_noop_revalidates_m83_decision() -> None:
    classification = _classification().model_copy(update={"shell_execution_performed": True})

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_sandboxed_echo_noop_command(_request(shell_dry_run_classification=classification))


def test_m84_sandboxed_echo_noop_policy_denies_execution_enablement() -> None:
    policy = SandboxedEchoNoOpCommandPolicy(
        command_execution_enabled=True,
        shell_execution_enabled=True,
        process_spawn_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_sandboxed_echo_noop_command_policy(policy)


def test_m84_sandboxed_echo_noop_decision_revalidation_denies_authority() -> None:
    decision = build_sandboxed_echo_noop_command(_request()).model_copy(
        update={
            "command_execution_performed": True,
            "shell_execution_performed": True,
        }
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_sandboxed_echo_noop_command_decision(decision)


def test_m84_sandboxed_echo_noop_receipt_stores_no_raw_command_or_output() -> None:
    decision = build_sandboxed_echo_noop_command(_request())
    unsafe = SandboxedEchoNoOpCommandDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "store_raw_command": True,
                "store_raw_output": True,
            },
        }
    )

    with pytest.raises(ValueError, match="M84_RECEIPT_RAW_COMMAND_DENIED"):
        validate_sandboxed_echo_noop_command_decision(unsafe)


def test_m84_sandboxed_echo_noop_receipt_revalidates_exact_bindings() -> None:
    decision = build_sandboxed_echo_noop_command(_request())
    unsafe = SandboxedEchoNoOpCommandDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "shell_dry_run_decision_ref": "shell-dry-run-classifier-decision:mismatch",
            },
        }
    )

    with pytest.raises(ValueError, match="M84_RECEIPT_BINDING_MISMATCH"):
        validate_sandboxed_echo_noop_command_decision(unsafe)
