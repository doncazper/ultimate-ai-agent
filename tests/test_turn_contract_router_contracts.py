import pytest

from ultimate_ai_agent.core.decision_router import (
    ApprovedExecutionScope,
    ApprovalPolicy,
    InvocationPolicy,
    MemoryPolicy,
    OutputContract,
    PromptProfilePolicy,
    StatePolicy,
    ToolChoicePolicy,
    ToolPolicy,
    TurnContractKind,
    TurnDecision,
    compile_invocation_policy,
)


def _decision(turn_contract: TurnContractKind, decision_ref: str = "turn-decision:test") -> TurnDecision:
    return TurnDecision(
        decision_ref=decision_ref,
        turn_contract=turn_contract,
        confidence=0.9,
        safe_summary="Reviewed safe turn decision summary.",
        reason_refs=["reason-ref:turn-contract:test"],
        source_refs=["source:turn-contract:test"],
        evidence_refs=["evidence:turn-contract:test"],
    )


def _approved_scope() -> ApprovedExecutionScope:
    return ApprovedExecutionScope(
        scope_ref="approved-scope:turn-contract:test",
        approval_scope_ref="approval-scope:turn-contract:test",
        action_scope_ref="action-scope:turn-contract:test",
        tool_ref="tool-ref:turn-contract:test",
        arguments_ref="arguments-ref:turn-contract:test",
        merchant_ref="merchant-ref:turn-contract:test",
        recipient_ref="recipient-ref:turn-contract:test",
        account_ref="account-ref:turn-contract:test",
        cost_ref="cost-ref:turn-contract:test",
        credential_broker_ref="credential-broker-ref:turn-contract:test",
        risk_ref="risk-ref:turn-contract:test",
    )


def test_turn_contract_enum_values_match_phase_pack() -> None:
    assert {item.value for item in TurnContractKind} == {
        "answer_directly",
        "base_answer",
        "answer_with_reviewed_memory",
        "draft_or_plan",
        "prepare_tool_or_action",
        "approval_required",
        "execute_approved_action",
        "ask_clarifying_question",
        "blocked_unsafe",
    }


@pytest.mark.parametrize(
    ("turn_contract", "prompt_profile", "output_contract"),
    [
        (TurnContractKind.answer_directly, PromptProfilePolicy.minimal_answer.value, OutputContract.plain_answer.value),
        (TurnContractKind.base_answer, PromptProfilePolicy.base_answer.value, OutputContract.base_answer.value),
    ],
)
def test_direct_and_base_answer_compile_to_protected_policy(
    turn_contract: TurnContractKind,
    prompt_profile: str,
    output_contract: str,
) -> None:
    policy = compile_invocation_policy(_decision(turn_contract))

    assert policy.turn_contract == turn_contract.value
    assert policy.memory_scope == MemoryPolicy.none.value
    assert policy.tools == []
    assert policy.tool_choice == ToolChoicePolicy.none.value
    assert policy.planner is False
    assert policy.durable_state is False
    assert policy.approval_required is False
    assert policy.approval_policy == ApprovalPolicy.not_required.value
    assert policy.prompt_profile == prompt_profile
    assert policy.output_contract == output_contract
    assert policy.side_effects_allowed is False
    assert policy.memory_read_allowed is False
    assert policy.memory_write_allowed is False
    assert policy.tool_execution_allowed is False
    assert policy.action_execution_allowed is False
    assert policy.context_injection_allowed is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("memory_scope", MemoryPolicy.reviewed_relevant_only),
        ("tool_policy", ToolPolicy.read_only_or_proposal_only),
        ("tools", ["tool-category:read-only-or-proposal"]),
        ("tool_choice", ToolChoicePolicy.auto_read_only),
        ("planner", True),
        ("durable_state", True),
        ("approval_required", True),
        ("side_effects_allowed", True),
        ("memory_read_allowed", True),
        ("tool_execution_allowed", True),
    ],
)
def test_answer_preservation_policy_rejects_permission_expansion(field_name: str, value: object) -> None:
    kwargs = {
        "decision_ref": "turn-decision:direct",
        "turn_contract": TurnContractKind.answer_directly,
        field_name: value,
    }

    with pytest.raises(ValueError, match="answer preservation firewall denied expansion"):
        InvocationPolicy(**kwargs)


def test_base_answer_decision_serializes_as_safe_contract_data() -> None:
    decision = _decision(TurnContractKind.base_answer, decision_ref="turn-decision:base-answer")
    payload = decision.model_dump(mode="json")

    assert payload["turn_contract"] == "base_answer"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_included"] is False
    assert payload["no_provider_call_performed"] is True
    assert payload["no_tool_execution_performed"] is True
    assert payload["no_memory_read_performed"] is True


def test_base_answer_policy_rejects_profile_drift() -> None:
    with pytest.raises(ValueError, match="profile drift"):
        InvocationPolicy(
            decision_ref="turn-decision:base-answer",
            turn_contract=TurnContractKind.base_answer,
            prompt_profile=PromptProfilePolicy.minimal_answer,
            output_contract=OutputContract.base_answer,
        )


def test_execute_approved_action_requires_exact_scope_refs() -> None:
    with pytest.raises(ValueError, match="approval_scope_ref"):
        _decision(TurnContractKind.execute_approved_action, decision_ref="turn-decision:execute-missing")

    with pytest.raises(ValueError, match="action_scope_ref"):
        TurnDecision(
            decision_ref="turn-decision:execute-missing-action",
            turn_contract=TurnContractKind.execute_approved_action,
            confidence=0.9,
            safe_summary="Reviewed exact execution posture.",
            reason_refs=["reason-ref:turn-contract:test"],
            source_refs=["source:turn-contract:test"],
            evidence_refs=["evidence:turn-contract:test"],
            approval_scope_ref="approval-scope:turn-contract:test",
        )


def test_execute_approved_action_compiles_only_exact_approved_policy() -> None:
    scope = _approved_scope()
    decision = TurnDecision(
        decision_ref="turn-decision:execute",
        turn_contract=TurnContractKind.execute_approved_action,
        confidence=0.9,
        safe_summary="Reviewed exact execution posture.",
        reason_refs=["reason-ref:turn-contract:test"],
        source_refs=["source:turn-contract:test"],
        evidence_refs=["evidence:turn-contract:test"],
        approval_scope_ref=scope.approval_scope_ref,
        action_scope_ref=scope.action_scope_ref,
        approved_tool_ref=scope.tool_ref,
        approved_arguments_ref=scope.arguments_ref,
        approved_execution_scope=scope,
    )

    policy = compile_invocation_policy(decision)

    assert policy.turn_contract == "execute_approved_action"
    assert policy.approval_policy == ApprovalPolicy.already_approved_exact_scope.value
    assert policy.approval_required is False
    assert policy.tools == ["tool-ref:turn-contract:test"]
    assert policy.tool_policy == ToolPolicy.exact_approved_tool_only.value
    assert policy.tool_choice == ToolChoicePolicy.exact_approved.value
    assert policy.allowed_tool_ref == "tool-ref:turn-contract:test"
    assert policy.allowed_arguments_ref == "arguments-ref:turn-contract:test"
    assert policy.allowed_merchant_ref == "merchant-ref:turn-contract:test"
    assert policy.allowed_recipient_ref == "recipient-ref:turn-contract:test"
    assert policy.allowed_account_ref == "account-ref:turn-contract:test"
    assert policy.allowed_cost_ref == "cost-ref:turn-contract:test"
    assert policy.allowed_credential_broker_ref == "credential-broker-ref:turn-contract:test"
    assert policy.allowed_risk_ref == "risk-ref:turn-contract:test"
    assert policy.side_effects_allowed is True
    assert policy.receipt_required is True
    assert policy.execution_ready is True
    assert policy.workflow_execution_allowed is False
    assert policy.provider_call_allowed is False
    assert policy.shell_subprocess_allowed is False
    assert policy.browser_network_allowed is False
    assert policy.connector_write_allowed is False


@pytest.mark.parametrize(
    ("field_name", "broadened_ref"),
    [
        ("allowed_tool_ref", "tool-ref:turn-contract:other"),
        ("allowed_arguments_ref", "arguments-ref:turn-contract:other"),
        ("allowed_merchant_ref", "merchant-ref:turn-contract:other"),
        ("allowed_recipient_ref", "recipient-ref:turn-contract:other"),
        ("allowed_account_ref", "account-ref:turn-contract:other"),
        ("allowed_cost_ref", "cost-ref:turn-contract:other"),
        ("allowed_credential_broker_ref", "credential-broker-ref:turn-contract:other"),
    ],
)
def test_execute_approved_action_policy_rejects_exact_scope_broadening(
    field_name: str,
    broadened_ref: str,
) -> None:
    scope = _approved_scope()
    decision = TurnDecision(
        decision_ref="turn-decision:execute-scope",
        turn_contract=TurnContractKind.execute_approved_action,
        confidence=0.9,
        safe_summary="Reviewed exact execution posture.",
        reason_refs=["reason-ref:turn-contract:test"],
        source_refs=["source:turn-contract:test"],
        evidence_refs=["evidence:turn-contract:test"],
        approval_scope_ref=scope.approval_scope_ref,
        action_scope_ref=scope.action_scope_ref,
        approved_tool_ref=scope.tool_ref,
        approved_arguments_ref=scope.arguments_ref,
        approved_execution_scope=scope,
    )
    payload = compile_invocation_policy(decision).model_dump(mode="json")
    payload[field_name] = broadened_ref

    with pytest.raises(ValueError, match=field_name):
        InvocationPolicy(**payload)


def test_execute_approved_action_policy_rejects_memory_write_authority() -> None:
    scope = _approved_scope()
    decision = TurnDecision(
        decision_ref="turn-decision:execute-memory-write",
        turn_contract=TurnContractKind.execute_approved_action,
        confidence=0.9,
        safe_summary="Reviewed exact execution posture.",
        reason_refs=["reason-ref:turn-contract:test"],
        source_refs=["source:turn-contract:test"],
        evidence_refs=["evidence:turn-contract:test"],
        approval_scope_ref=scope.approval_scope_ref,
        action_scope_ref=scope.action_scope_ref,
        approved_tool_ref=scope.tool_ref,
        approved_arguments_ref=scope.arguments_ref,
        approved_execution_scope=scope,
    )
    payload = compile_invocation_policy(decision).model_dump(mode="json")
    payload["memory_write_allowed"] = True

    with pytest.raises(ValueError, match="memory_write_allowed"):
        InvocationPolicy(**payload)


def test_approval_required_policy_exposes_only_envelope_posture() -> None:
    policy = compile_invocation_policy(_decision(TurnContractKind.approval_required))

    assert policy.tool_policy == ToolPolicy.envelope_only_no_execution.value
    assert policy.tools == ["tool-category:approval-envelope-builder"]
    assert policy.approval_required is True
    assert policy.side_effects_allowed is False
    assert policy.execution_ready is False
    assert policy.tool_execution_allowed is False
    assert policy.action_execution_allowed is False
    assert policy.receipt_required is False


def test_non_execution_contracts_reject_side_effects_allowed() -> None:
    with pytest.raises(ValueError, match="side effects are only allowed"):
        InvocationPolicy(
            decision_ref="turn-decision:approval",
            turn_contract=TurnContractKind.approval_required,
            memory_scope=MemoryPolicy.proposal_review_only,
            tool_policy=ToolPolicy.envelope_only_no_execution,
            tools=["tool-category:approval-envelope-builder"],
            tool_choice=ToolChoicePolicy.auto_read_only,
            planner=True,
            durable_state=True,
            state_policy=StatePolicy.action_envelope,
            approval_policy=ApprovalPolicy.required_before_execution,
            approval_required=True,
            prompt_profile=PromptProfilePolicy.approval_boundary,
            output_contract=OutputContract.approval_envelope_required,
            side_effects_allowed=True,
        )


def test_prepare_tool_policy_is_proposal_only_and_not_execution() -> None:
    policy = compile_invocation_policy(_decision(TurnContractKind.prepare_tool_or_action))

    assert policy.tool_policy == ToolPolicy.read_only_or_proposal_only.value
    assert policy.tools == ["tool-category:read-only-or-proposal"]
    assert policy.tool_execution_allowed is False
    assert policy.action_execution_allowed is False
    assert policy.execution_ready is False
