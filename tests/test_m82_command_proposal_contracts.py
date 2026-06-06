import pytest

from ultimate_ai_agent.core.sandbox import (
    CommandProposalDecision,
    CommandProposalEffect,
    CommandProposalPolicy,
    CommandProposalRequest,
    CommandProposalStatus,
    build_command_proposal,
    validate_command_proposal_decision,
    validate_command_proposal_policy,
    validate_command_proposal_request,
)


def _request(**overrides):
    data = {
        "request_ref": "command-proposal-request:m82",
        "proposal_ref": "command-proposal:m82",
        "sandbox_spec_ref": "runtime-sandbox-spec:m81",
        "baseline_ref": "baseline:v0.85.0",
        "actor_ref": "actor:local-reviewer",
        "prior_milestone_refs": [
            "milestone:M57",
            "milestone:M58",
            "milestone:M80",
            "milestone:M81",
        ],
        "command_ref": "command-ref:review-noop",
        "safe_purpose": (
            "Describe a no-effect command proposal for human review without "
            "executing it or granting authority."
        ),
        "safe_command_label": "review noop metadata",
        "argv_preview": ["review-noop", "--dry-summary"],
    }
    data.update(overrides)
    return CommandProposalRequest(**data)


def test_m82_command_proposal_is_contract_only_and_non_authoritative() -> None:
    proposal = build_command_proposal(_request())

    assert proposal.status == CommandProposalStatus.proposed_for_review
    assert proposal.expected_effect == CommandProposalEffect.no_effect
    assert proposal.proposal_only is True
    assert proposal.review_only is True
    assert proposal.deterministic is True
    assert proposal.local_only is True
    assert proposal.structured_args_only is True
    assert proposal.execution_authorized is False
    assert proposal.command_execution_performed is False
    assert proposal.subprocess_execution_performed is False
    assert proposal.shell_execution_performed is False
    assert proposal.process_spawn_performed is False
    assert proposal.filesystem_mutation_performed is False
    assert proposal.network_access_performed is False
    assert proposal.tool_execution_performed is False
    assert proposal.browser_automation_performed is False
    assert proposal.plugin_execution_performed is False
    assert proposal.remote_execution_performed is False
    assert proposal.model_call_performed is False
    assert proposal.memory_write_performed is False
    assert proposal.context_injection_performed is False
    assert proposal.background_worker_started is False
    assert proposal.backend_route_added is False
    assert proposal.control_center_control_added is False
    assert proposal.dependency_added is False
    assert proposal.production_authority_granted is False
    assert proposal.side_effects_performed == []
    assert proposal.reason_codes == [
        "M82_COMMAND_PROPOSAL_CONTRACT_ONLY",
        "M82_NO_COMMAND_EXECUTION",
        "M83_REMAINS_FUTURE",
    ]
    assert proposal.receipt_plan.store_safe_summary_only is True
    assert proposal.receipt_plan.store_raw_command is False
    assert proposal.receipt_plan.store_shell_string is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_REQUEST_DENIED"),
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
        ("contains_shell_string", "M82_SHELL_STRING_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("contains_secret", "SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED"),
    ],
)
def test_m82_command_proposal_denies_runtime_authority_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_command_proposal_request(_request(**{field: True}))


@pytest.mark.parametrize(
    ("argv_preview", "reason"),
    [
        ([], "M82_ARGV_PREVIEW_REQUIRED"),
        (["review-noop && rm -rf tmp"], "M82_SHELL_STRING_DENIED"),
        (["review-noop", "/Users/local/private.txt"], "M82_RAW_OR_ABSOLUTE_PATH_DENIED"),
        (["review-noop", "token=abcde12345678901234"], "SECRET"),
    ],
)
def test_m82_command_proposal_rejects_shell_strings_paths_and_secrets(
    argv_preview: list[str], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_command_proposal_request(_request(argv_preview=argv_preview))


def test_m82_command_proposal_requires_prior_milestones() -> None:
    with pytest.raises(ValueError, match="M82_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_command_proposal_request(
            _request(prior_milestone_refs=["milestone:M57", "milestone:M58", "milestone:M80"])
        )

    with pytest.raises(ValueError, match="M82_PRIOR_MILESTONE_REF_DUPLICATE"):
        validate_command_proposal_request(
            _request(
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M81",
                ]
            )
        )


def test_m82_command_proposal_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "execution_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="EXECUTION_REQUEST_DENIED"):
        build_command_proposal(request)


def test_m82_command_proposal_policy_denies_execution_enablement() -> None:
    policy = CommandProposalPolicy(
        command_execution_enabled=True,
        shell_execution_enabled=True,
        network_access_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="COMMAND_EXECUTION_DENIED"):
        validate_command_proposal_policy(policy)


def test_m82_command_proposal_decision_revalidation_denies_authority() -> None:
    decision = build_command_proposal(_request()).model_copy(
        update={
            "execution_authorized": True,
            "command_execution_performed": True,
        }
    )

    with pytest.raises(ValueError, match="EXECUTION_AUTHORITY_DENIED"):
        validate_command_proposal_decision(decision)


def test_m82_command_proposal_receipt_stores_no_raw_command() -> None:
    decision = build_command_proposal(_request())
    unsafe = CommandProposalDecision.model_validate(
        {
            **decision.model_dump(),
            "receipt_plan": {
                **decision.receipt_plan.model_dump(),
                "store_raw_command": True,
            },
        }
    )

    with pytest.raises(ValueError, match="M82_RECEIPT_RAW_COMMAND_DENIED"):
        validate_command_proposal_decision(unsafe)
