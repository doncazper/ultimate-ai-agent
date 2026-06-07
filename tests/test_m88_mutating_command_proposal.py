import pytest

from tests.test_m87_sandboxed_command_audit_replay import _request as _m87_request
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


def _m87_decision():
    return build_sandboxed_command_audit_replay(_m87_request())


def _request(**overrides):
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


def test_m88_mutating_command_proposal_is_review_only() -> None:
    decision = build_mutating_command_proposal(_request())

    assert decision.status == MutatingCommandProposalStatus.proposed_for_review
    assert decision.contract_only is True
    assert decision.proposal_only is True
    assert decision.review_only is True
    assert decision.mutating_command_review_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.audit_replay_decision_revalidated is True
    assert decision.mutation_scope_bound is True
    assert decision.command_execution_authorized is False
    assert decision.command_execution_performed is False
    assert decision.shell_execution_authorized is False
    assert decision.shell_execution_performed is False
    assert decision.subprocess_execution_authorized is False
    assert decision.subprocess_execution_performed is False
    assert decision.process_spawn_authorized is False
    assert decision.process_spawn_performed is False
    assert decision.filesystem_mutation_authorized is False
    assert decision.filesystem_mutation_performed is False
    assert decision.network_access_performed is False
    assert decision.tool_execution_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.remote_execution_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_mutation_scope_ref_only is True
    assert decision.receipt_plan.store_raw_command is False
    assert decision.receipt_plan.store_raw_output is False
    assert decision.reason_codes == [
        "M88_MUTATING_COMMAND_PROPOSAL_REVIEW_ONLY",
        "M88_EXACT_M87_AUDIT_REPLAY_BINDING_REQUIRED",
        "M88_SAFE_MUTATION_SCOPE_REQUIRED",
        "M88_NO_COMMAND_EXECUTION",
        "M89_REMAINS_FUTURE",
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
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_shell_string", "M88_SHELL_STRING_DENIED"),
        ("contains_raw_command", "M88_RAW_COMMAND_DENIED"),
        ("contains_raw_output", "M88_RAW_OUTPUT_DENIED"),
        ("contains_secret", "SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED"),
    ],
)
def test_m88_mutating_command_proposal_denies_execution_mutation_and_raw_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mutating_command_proposal_request(_request(**{field: True}))


def test_m88_requires_exact_m87_audit_replay_binding() -> None:
    for update, reason in [
        (
            {"sandboxed_command_audit_replay_decision_ref": "sandboxed-command-audit-replay-decision:other"},
            "M88_M87_AUDIT_REPLAY_BINDING_MISMATCH",
        ),
        ({"command_ref": "command-ref:other"}, "M88_COMMAND_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M88_ACTOR_BINDING_MISMATCH"),
        ({"sandbox_spec_ref": "runtime-sandbox-spec:other"}, "M88_SANDBOX_SPEC_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m88"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_mutating_command_proposal(_request(**update))


def test_m88_requires_safe_mutation_scope_and_argument_refs() -> None:
    for update, reason in [
        ({"mutation_intent_ref": "mutation-intent:other"}, "M88_MUTATION_SCOPE_BINDING_MISMATCH"),
        ({"mutation_scope_ref": "mutation-scope:other"}, "M88_MUTATION_SCOPE_BINDING_MISMATCH"),
        ({"safe_argument_refs": []}, "M88_SAFE_ARGUMENT_REFS_REQUIRED"),
        ({"safe_argument_refs": ["argument-ref:m88-review-only", "argument-ref:m88-review-only"]}, "M88_SAFE_ARGUMENT_REF_DUPLICATE"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_mutating_command_proposal(_request(**update))


def test_m88_revalidates_model_copy_mutated_m87_replay_decision() -> None:
    replay = _m87_decision()
    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_mutating_command_proposal(
            _request(
                sandboxed_command_audit_replay_decision=replay.model_copy(
                    update={"shell_execution_authorized": True}
                )
            )
        )


def test_m88_revalidates_decision_and_receipt_flags() -> None:
    decision = build_mutating_command_proposal(_request())
    for update, reason in [
        ({"command_execution_authorized": True}, "COMMAND_EXECUTION_DENIED"),
        ({"filesystem_mutation_authorized": True}, "FILESYSTEM_MUTATION_DENIED"),
        ({"filesystem_mutation_performed": True}, "FILESYSTEM_MUTATION_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mutating_command_proposal_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="M88_RAW_COMMAND_DENIED"):
        validate_mutating_command_proposal_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_command": True}
                    )
                }
            )
        )


def test_m88_policy_denies_execution_mutation_and_authority_flags() -> None:
    for field, reason in [
        ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mutating_command_proposal_policy(
                MutatingCommandProposalPolicy(**{field: True})
            )
