import pytest

from ultimate_ai_agent.core.sandbox import (
    CommandProposalRequest,
    ShellDryRunClassificationStatus,
    ShellDryRunClass,
    ShellDryRunClassifierDecision,
    ShellDryRunClassifierPolicy,
    ShellDryRunClassifierRequest,
    build_command_proposal,
    build_shell_dry_run_classification,
    validate_shell_dry_run_classifier_decision,
    validate_shell_dry_run_classifier_policy,
    validate_shell_dry_run_classifier_request,
)


def _command_proposal(command_ref: str = "command-ref:review-noop"):
    return build_command_proposal(
        CommandProposalRequest(
            request_ref="command-proposal-request:m83-base",
            proposal_ref="command-proposal:m83-base",
            sandbox_spec_ref="runtime-sandbox-spec:m81",
            baseline_ref="baseline:v0.86.0",
            actor_ref="actor:local-reviewer",
            prior_milestone_refs=[
                "milestone:M57",
                "milestone:M58",
                "milestone:M80",
                "milestone:M81",
            ],
            command_ref=command_ref,
            safe_purpose="Describe a no-effect command proposal for dry-run classification review.",
            safe_command_label="review noop metadata",
            argv_preview=["review-noop", "--dry-summary"],
        )
    )


def _request(**overrides):
    proposal = overrides.pop("command_proposal", _command_proposal())
    data = {
        "request_ref": "shell-dry-run-classifier-request:m83",
        "classifier_ref": "shell-dry-run-classifier:m83",
        "command_proposal_ref": proposal.proposal_ref,
        "sandbox_spec_ref": proposal.sandbox_spec_ref,
        "baseline_ref": "baseline:v0.86.0",
        "actor_ref": proposal.actor_ref,
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
            "milestone:M82",
        ],
        "command_proposal": proposal,
    }
    data.update(overrides)
    return ShellDryRunClassifierRequest(**data)


def test_m83_shell_dry_run_classifier_is_review_only_and_non_executing() -> None:
    decision = build_shell_dry_run_classification(_request())

    assert decision.status == ShellDryRunClassificationStatus.classified_for_review
    assert decision.classification == ShellDryRunClass.no_effect_review
    assert decision.classifier_only is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.dry_run_classification_allowed is True
    assert decision.dry_run_execution_authorized is False
    assert decision.command_execution_authorized is False
    assert decision.shell_execution_authorized is False
    assert decision.subprocess_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.process_spawn_performed is False
    assert decision.command_execution_performed is False
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
    assert decision.reason_codes == [
        "M83_SHELL_DRY_RUN_CLASSIFIER_CONTRACT_ONLY",
        "M83_NO_SHELL_EXECUTION",
        "M84_REMAINS_FUTURE",
    ]
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_shell_string is False
    assert decision.receipt_plan.dry_run_execution_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("dry_run_execution_requested", "DRY_RUN_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
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
        ("contains_shell_string", "M83_SHELL_STRING_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("contains_secret", "SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED"),
    ],
)
def test_m83_shell_dry_run_classifier_denies_execution_and_authority_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_shell_dry_run_classifier_request(_request(**{field: True}))


def test_m83_shell_dry_run_classifier_requires_exact_command_proposal_binding() -> None:
    with pytest.raises(ValueError, match="M83_COMMAND_PROPOSAL_BINDING_MISMATCH"):
        validate_shell_dry_run_classifier_request(
            _request(command_proposal_ref="command-proposal:mismatch")
        )


def test_m83_shell_dry_run_classifier_requires_prior_m82() -> None:
    with pytest.raises(ValueError, match="M83_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_shell_dry_run_classifier_request(
            _request(prior_milestone_refs=["milestone:M57", "milestone:M58", "milestone:M80", "milestone:M81"])
        )


def test_m83_shell_dry_run_classifier_classifies_safe_refs_deterministically() -> None:
    read_decision = build_shell_dry_run_classification(
        _request(command_proposal=_command_proposal(command_ref="command-ref:read-metadata"))
    )
    mutate_decision = build_shell_dry_run_classification(
        _request(command_proposal=_command_proposal(command_ref="command-ref:write-file"))
    )

    assert read_decision.classification == ShellDryRunClass.read_only_candidate
    assert mutate_decision.classification == ShellDryRunClass.mutating_candidate_future
    assert "M84_REMAINS_FUTURE" in mutate_decision.reason_codes
    assert mutate_decision.command_execution_performed is False


def test_m83_shell_dry_run_classifier_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "dry_run_execution_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="DRY_RUN_EXECUTION_DENIED"):
        build_shell_dry_run_classification(request)


def test_m83_shell_dry_run_classifier_revalidates_m82_decision() -> None:
    proposal = _command_proposal().model_copy(update={"shell_execution_performed": True})

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_shell_dry_run_classification(_request(command_proposal=proposal))


def test_m83_shell_dry_run_classifier_policy_denies_execution_enablement() -> None:
    policy = ShellDryRunClassifierPolicy(
        dry_run_execution_enabled=True,
        shell_execution_enabled=True,
        process_spawn_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="DRY_RUN_EXECUTION_DENIED"):
        validate_shell_dry_run_classifier_policy(policy)


def test_m83_shell_dry_run_classifier_decision_revalidation_denies_authority() -> None:
    decision = build_shell_dry_run_classification(_request()).model_copy(
        update={
            "dry_run_execution_authorized": True,
            "shell_execution_performed": True,
        }
    )

    with pytest.raises(ValueError, match="DRY_RUN_EXECUTION_DENIED"):
        validate_shell_dry_run_classifier_decision(decision)


def test_m83_shell_dry_run_classifier_receipt_stores_no_raw_command() -> None:
    decision = build_shell_dry_run_classification(_request())
    unsafe = ShellDryRunClassifierDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "store_raw_command": True,
                "dry_run_execution_performed": True,
            },
        }
    )

    with pytest.raises(ValueError, match="M83_RECEIPT_RAW_COMMAND_DENIED"):
        validate_shell_dry_run_classifier_decision(unsafe)
