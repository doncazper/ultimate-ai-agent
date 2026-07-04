from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.contracts import DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)


TURN_CONTRACT_ROUTER_CONTRACT_REF = "contract-ref:turn-contract-router:v1"
INVOCATION_POLICY_COMPILER_REF = "policy-ref:turn-contract-router:invocation-policy-compiler:v1"
TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    *DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    "blocked-authority:no-router-provider-selection",
    "blocked-authority:no-answer-context-injection",
    "blocked-authority:no-unapproved-execution",
    "blocked-authority:no-unscoped-side-effect",
)


class TurnContractKind(str, Enum):
    answer_directly = "answer_directly"
    base_answer = "base_answer"
    answer_with_reviewed_memory = "answer_with_reviewed_memory"
    draft_or_plan = "draft_or_plan"
    prepare_tool_or_action = "prepare_tool_or_action"
    approval_required = "approval_required"
    execute_approved_action = "execute_approved_action"
    ask_clarifying_question = "ask_clarifying_question"
    blocked_unsafe = "blocked_unsafe"


TURN_CONTRACT_ROUTER_REQUIRED_CONTRACT_KINDS = tuple(item.value for item in TurnContractKind)


class MemoryPolicy(str, Enum):
    none = "none"
    reviewed_relevant_only = "reviewed_relevant_only"
    scoped_to_approval = "scoped_to_approval"
    proposal_review_only = "proposal_review_only"


class ToolPolicy(str, Enum):
    none = "none"
    read_only_or_proposal_only = "read_only_or_proposal_only"
    envelope_only_no_execution = "envelope_only_no_execution"
    exact_approved_tool_only = "exact_approved_tool_only"


class ToolChoicePolicy(str, Enum):
    none = "none"
    auto_read_only = "auto_read_only"
    exact_approved = "exact_approved"


class StatePolicy(str, Enum):
    ephemeral_only = "ephemeral_only"
    draft_state_only = "draft_state_only"
    proposal_state_only = "proposal_state_only"
    action_envelope = "action_envelope"
    receipt_action_log = "receipt_action_log"


class ApprovalPolicy(str, Enum):
    not_required = "not_required"
    required_before_execution = "required_before_execution"
    already_approved_exact_scope = "already_approved_exact_scope"
    blocked = "blocked"


class PromptProfilePolicy(str, Enum):
    minimal_answer = "minimal_answer"
    base_answer = "base_answer"
    memory_answer = "memory_answer"
    draft_or_plan = "draft_or_plan"
    tool_or_action_prep = "tool_or_action_prep"
    approval_boundary = "approval_boundary"
    execution_exact_scope = "execution_exact_scope"
    clarify = "clarify"
    safe_refusal = "safe_refusal"


class OutputContract(str, Enum):
    plain_answer = "plain_answer"
    base_answer = "base_answer"
    memory_answer_with_refs = "memory_answer_with_refs"
    draft_or_plan = "draft_or_plan"
    action_or_tool_proposal = "action_or_tool_proposal"
    approval_envelope_required = "approval_envelope_required"
    execution_receipt_required = "execution_receipt_required"
    clarifying_question = "clarifying_question"
    safe_refusal = "safe_refusal"


class RiskFlag(str, Enum):
    low_risk = "low_risk"
    external_side_effect = "external_side_effect"
    credential_or_payment = "credential_or_payment"
    destructive = "destructive"
    privacy_boundary = "privacy_boundary"
    freshness_required = "freshness_required"
    memory_requested = "memory_requested"
    unsafe = "unsafe"


class ApprovedExecutionScope(BaseModel):
    scope_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(..., min_length=1)
    action_scope_ref: str = Field(..., min_length=1)
    tool_ref: str = Field(..., min_length=1)
    arguments_ref: str = Field(..., min_length=1)
    merchant_ref: str = Field(..., min_length=1)
    recipient_ref: str = Field(..., min_length=1)
    account_ref: str = Field(..., min_length=1)
    cost_ref: str = Field(..., min_length=1)
    credential_broker_ref: str = Field(..., min_length=1)
    risk_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_scope(self) -> "ApprovedExecutionScope":
        for field_name in (
            "scope_ref",
            "approval_scope_ref",
            "action_scope_ref",
            "tool_ref",
            "arguments_ref",
            "merchant_ref",
            "recipient_ref",
            "account_ref",
            "cost_ref",
            "credential_broker_ref",
            "risk_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        return self


_ANSWER_PRESERVATION_CONTRACTS = {
    TurnContractKind.answer_directly.value,
    TurnContractKind.base_answer.value,
}
_EXECUTION_CONTRACT = TurnContractKind.execute_approved_action.value
_PROPOSAL_TOOL_REFS = ("tool-category:read-only-or-proposal",)
_ENVELOPE_TOOL_REFS = ("tool-category:approval-envelope-builder",)
_NO_EFFECT_FLAGS = (
    "no_runtime_model_call_performed",
    "no_provider_call_performed",
    "no_tool_execution_performed",
    "no_action_execution_performed",
    "no_memory_read_performed",
    "no_memory_write_performed",
    "no_durable_state_write_performed",
    "no_shell_subprocess_performed",
    "no_browser_network_performed",
    "no_connector_write_performed",
)


class TurnDecision(BaseModel):
    contract_ref: str = TURN_CONTRACT_ROUTER_CONTRACT_REF
    decision_ref: str = Field(..., min_length=1)
    turn_contract: TurnContractKind
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    approval_scope_ref: str | None = None
    action_scope_ref: str | None = None
    approved_tool_ref: str | None = None
    approved_arguments_ref: str | None = None
    approved_execution_scope: ApprovedExecutionScope | None = None
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_content_included: bool = False
    router_authority_granted: bool = False
    execution_performed: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_memory_read_performed: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_turn_decision(self) -> "TurnDecision":
        if self.contract_ref != TURN_CONTRACT_ROUTER_CONTRACT_REF:
            raise ValueError("unexpected turn contract router contract ref")
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.decision_ref, "decision_ref")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_optional_ref(self.approval_scope_ref, "approval_scope_ref")
        _validate_optional_ref(self.action_scope_ref, "action_scope_ref")
        _validate_optional_ref(self.approved_tool_ref, "approved_tool_ref")
        _validate_optional_ref(self.approved_arguments_ref, "approved_arguments_ref")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn decision")
        if not self.safe_refs_only:
            raise ValueError("turn decision must be safe-ref only")
        if self.raw_content_included:
            raise ValueError("turn decision must not include raw content")
        if self.router_authority_granted:
            raise ValueError("turn contract router must not grant authority")
        if self.execution_performed:
            raise ValueError("turn contract router must not perform execution")
        _validate_no_effect_flags(self, "turn decision")
        if self.turn_contract == _EXECUTION_CONTRACT:
            missing = [
                field_name
                for field_name in (
                    "approval_scope_ref",
                    "action_scope_ref",
                    "approved_tool_ref",
                    "approved_arguments_ref",
                    "approved_execution_scope",
                )
                if getattr(self, field_name) is None
            ]
            if missing:
                raise ValueError(f"execute_approved_action requires exact scope ref: {missing[0]}")
            _validate_turn_decision_matches_approved_scope(self)
        return self


class InvocationPolicy(BaseModel):
    policy_ref: str = INVOCATION_POLICY_COMPILER_REF
    decision_ref: str = Field(..., min_length=1)
    turn_contract: TurnContractKind
    memory_scope: MemoryPolicy = MemoryPolicy.none
    tool_policy: ToolPolicy = ToolPolicy.none
    tools: list[str] = Field(default_factory=list)
    tool_choice: ToolChoicePolicy = ToolChoicePolicy.none
    planner: bool = False
    durable_state: bool = False
    state_policy: StatePolicy = StatePolicy.ephemeral_only
    approval_policy: ApprovalPolicy = ApprovalPolicy.not_required
    approval_required: bool = False
    prompt_profile: PromptProfilePolicy = PromptProfilePolicy.minimal_answer
    output_contract: OutputContract = OutputContract.plain_answer
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    approval_scope_ref: str | None = None
    action_scope_ref: str | None = None
    allowed_tool_ref: str | None = None
    allowed_arguments_ref: str | None = None
    allowed_merchant_ref: str | None = None
    allowed_recipient_ref: str | None = None
    allowed_account_ref: str | None = None
    allowed_cost_ref: str | None = None
    allowed_credential_broker_ref: str | None = None
    allowed_risk_ref: str | None = None
    approved_execution_scope: ApprovedExecutionScope | None = None
    side_effects_allowed: bool = False
    receipt_required: bool = False
    execution_ready: bool = False
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    runtime_model_call_allowed: bool = False
    provider_call_allowed: bool = False
    memory_read_allowed: bool = False
    memory_write_allowed: bool = False
    tool_execution_allowed: bool = False
    action_execution_allowed: bool = False
    workflow_execution_allowed: bool = False
    context_injection_allowed: bool = False
    shell_subprocess_allowed: bool = False
    browser_network_allowed: bool = False
    connector_write_allowed: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_invocation_policy(self) -> "InvocationPolicy":
        validate_task_ref(self.policy_ref, "policy_ref")
        validate_task_ref(self.decision_ref, "decision_ref")
        _validate_ref_list(self.tools, "tools")
        _validate_optional_ref(self.approval_scope_ref, "approval_scope_ref")
        _validate_optional_ref(self.action_scope_ref, "action_scope_ref")
        _validate_optional_ref(self.allowed_tool_ref, "allowed_tool_ref")
        _validate_optional_ref(self.allowed_arguments_ref, "allowed_arguments_ref")
        _validate_optional_ref(self.allowed_merchant_ref, "allowed_merchant_ref")
        _validate_optional_ref(self.allowed_recipient_ref, "allowed_recipient_ref")
        _validate_optional_ref(self.allowed_account_ref, "allowed_account_ref")
        _validate_optional_ref(self.allowed_cost_ref, "allowed_cost_ref")
        _validate_optional_ref(self.allowed_credential_broker_ref, "allowed_credential_broker_ref")
        _validate_optional_ref(self.allowed_risk_ref, "allowed_risk_ref")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "invocation policy")
        if not self.safe_refs_only:
            raise ValueError("invocation policy must be safe-ref only")
        if self.raw_content_included:
            raise ValueError("invocation policy must not include raw content")
        if self.turn_contract in _ANSWER_PRESERVATION_CONTRACTS:
            _validate_answer_preservation_firewall(self)
        if self.turn_contract != _EXECUTION_CONTRACT and self.side_effects_allowed:
            raise ValueError("side effects are only allowed for exact approved execution")
        if self.turn_contract != _EXECUTION_CONTRACT and self.execution_ready:
            raise ValueError("execution readiness is only valid for exact approved execution")
        if self.turn_contract == _EXECUTION_CONTRACT:
            _validate_exact_execution_policy(self)
        else:
            _validate_runtime_denials(self, "non-execution invocation policy")
        return self


def compile_invocation_policy(decision: TurnDecision) -> InvocationPolicy:
    parsed = decision if isinstance(decision, TurnDecision) else TurnDecision(**decision)
    common = {
        "decision_ref": parsed.decision_ref,
        "turn_contract": parsed.turn_contract,
        "risk_flags": parsed.risk_flags,
        "blocked_authority_refs": parsed.blocked_authority_refs,
    }
    if parsed.turn_contract == TurnContractKind.answer_directly.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.none,
            tool_policy=ToolPolicy.none,
            tools=[],
            tool_choice=ToolChoicePolicy.none,
            planner=False,
            durable_state=False,
            state_policy=StatePolicy.ephemeral_only,
            approval_policy=ApprovalPolicy.not_required,
            approval_required=False,
            prompt_profile=PromptProfilePolicy.minimal_answer,
            output_contract=OutputContract.plain_answer,
        )
    if parsed.turn_contract == TurnContractKind.base_answer.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.none,
            tool_policy=ToolPolicy.none,
            tools=[],
            tool_choice=ToolChoicePolicy.none,
            planner=False,
            durable_state=False,
            state_policy=StatePolicy.ephemeral_only,
            approval_policy=ApprovalPolicy.not_required,
            approval_required=False,
            prompt_profile=PromptProfilePolicy.base_answer,
            output_contract=OutputContract.base_answer,
        )
    if parsed.turn_contract == TurnContractKind.answer_with_reviewed_memory.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.reviewed_relevant_only,
            tool_policy=ToolPolicy.none,
            tools=[],
            tool_choice=ToolChoicePolicy.none,
            planner=False,
            durable_state=False,
            state_policy=StatePolicy.ephemeral_only,
            approval_policy=ApprovalPolicy.not_required,
            prompt_profile=PromptProfilePolicy.memory_answer,
            output_contract=OutputContract.memory_answer_with_refs,
            memory_read_allowed=True,
        )
    if parsed.turn_contract == TurnContractKind.draft_or_plan.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.none,
            tool_policy=ToolPolicy.none,
            tools=[],
            tool_choice=ToolChoicePolicy.none,
            planner=True,
            durable_state=False,
            state_policy=StatePolicy.draft_state_only,
            approval_policy=ApprovalPolicy.not_required,
            prompt_profile=PromptProfilePolicy.draft_or_plan,
            output_contract=OutputContract.draft_or_plan,
        )
    if parsed.turn_contract == TurnContractKind.prepare_tool_or_action.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.proposal_review_only,
            tool_policy=ToolPolicy.read_only_or_proposal_only,
            tools=list(_PROPOSAL_TOOL_REFS),
            tool_choice=ToolChoicePolicy.auto_read_only,
            planner=True,
            durable_state=False,
            state_policy=StatePolicy.proposal_state_only,
            approval_policy=ApprovalPolicy.not_required,
            prompt_profile=PromptProfilePolicy.tool_or_action_prep,
            output_contract=OutputContract.action_or_tool_proposal,
        )
    if parsed.turn_contract == TurnContractKind.approval_required.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.proposal_review_only,
            tool_policy=ToolPolicy.envelope_only_no_execution,
            tools=list(_ENVELOPE_TOOL_REFS),
            tool_choice=ToolChoicePolicy.auto_read_only,
            planner=True,
            durable_state=True,
            state_policy=StatePolicy.action_envelope,
            approval_policy=ApprovalPolicy.required_before_execution,
            approval_required=True,
            prompt_profile=PromptProfilePolicy.approval_boundary,
            output_contract=OutputContract.approval_envelope_required,
        )
    if parsed.turn_contract == TurnContractKind.execute_approved_action.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.scoped_to_approval,
            tool_policy=ToolPolicy.exact_approved_tool_only,
            tools=[parsed.approved_tool_ref],
            tool_choice=ToolChoicePolicy.exact_approved,
            planner=False,
            durable_state=True,
            state_policy=StatePolicy.receipt_action_log,
            approval_policy=ApprovalPolicy.already_approved_exact_scope,
            approval_required=False,
            prompt_profile=PromptProfilePolicy.execution_exact_scope,
            output_contract=OutputContract.execution_receipt_required,
            approval_scope_ref=parsed.approval_scope_ref,
            action_scope_ref=parsed.action_scope_ref,
            allowed_tool_ref=parsed.approved_tool_ref,
            allowed_arguments_ref=parsed.approved_arguments_ref,
            allowed_merchant_ref=parsed.approved_execution_scope.merchant_ref,
            allowed_recipient_ref=parsed.approved_execution_scope.recipient_ref,
            allowed_account_ref=parsed.approved_execution_scope.account_ref,
            allowed_cost_ref=parsed.approved_execution_scope.cost_ref,
            allowed_credential_broker_ref=parsed.approved_execution_scope.credential_broker_ref,
            allowed_risk_ref=parsed.approved_execution_scope.risk_ref,
            approved_execution_scope=parsed.approved_execution_scope,
            side_effects_allowed=True,
            receipt_required=True,
            execution_ready=True,
            tool_execution_allowed=True,
            action_execution_allowed=True,
        )
    if parsed.turn_contract == TurnContractKind.ask_clarifying_question.value:
        return InvocationPolicy(
            **common,
            memory_scope=MemoryPolicy.none,
            tool_policy=ToolPolicy.none,
            tools=[],
            tool_choice=ToolChoicePolicy.none,
            planner=False,
            durable_state=False,
            state_policy=StatePolicy.ephemeral_only,
            approval_policy=ApprovalPolicy.not_required,
            prompt_profile=PromptProfilePolicy.clarify,
            output_contract=OutputContract.clarifying_question,
        )
    return InvocationPolicy(
        **common,
        memory_scope=MemoryPolicy.none,
        tool_policy=ToolPolicy.none,
        tools=[],
        tool_choice=ToolChoicePolicy.none,
        planner=False,
        durable_state=False,
        state_policy=StatePolicy.ephemeral_only,
        approval_policy=ApprovalPolicy.blocked,
        prompt_profile=PromptProfilePolicy.safe_refusal,
        output_contract=OutputContract.safe_refusal,
    )


def _validate_answer_preservation_firewall(policy: InvocationPolicy) -> None:
    expected = {
        "memory_scope": MemoryPolicy.none.value,
        "tool_policy": ToolPolicy.none.value,
        "tools": [],
        "tool_choice": ToolChoicePolicy.none.value,
        "planner": False,
        "durable_state": False,
        "state_policy": StatePolicy.ephemeral_only.value,
        "approval_policy": ApprovalPolicy.not_required.value,
        "approval_required": False,
        "side_effects_allowed": False,
        "receipt_required": False,
        "execution_ready": False,
        "memory_read_allowed": False,
        "memory_write_allowed": False,
        "tool_execution_allowed": False,
        "action_execution_allowed": False,
        "workflow_execution_allowed": False,
        "context_injection_allowed": False,
        "shell_subprocess_allowed": False,
        "browser_network_allowed": False,
        "connector_write_allowed": False,
    }
    for field_name, expected_value in expected.items():
        if getattr(policy, field_name) != expected_value:
            raise ValueError(f"answer preservation firewall denied expansion: {field_name}")
    if policy.turn_contract == TurnContractKind.answer_directly.value:
        expected_prompt = PromptProfilePolicy.minimal_answer.value
        expected_output = OutputContract.plain_answer.value
    else:
        expected_prompt = PromptProfilePolicy.base_answer.value
        expected_output = OutputContract.base_answer.value
    if policy.prompt_profile != expected_prompt:
        raise ValueError("answer preservation firewall denied profile drift: prompt_profile")
    if policy.output_contract != expected_output:
        raise ValueError("answer preservation firewall denied profile drift: output_contract")
    _validate_runtime_denials(policy, "answer preservation policy")


def _validate_exact_execution_policy(policy: InvocationPolicy) -> None:
    missing = [
        field_name
        for field_name in (
            "approval_scope_ref",
            "action_scope_ref",
            "allowed_tool_ref",
            "allowed_arguments_ref",
            "allowed_merchant_ref",
            "allowed_recipient_ref",
            "allowed_account_ref",
            "allowed_cost_ref",
            "allowed_credential_broker_ref",
            "allowed_risk_ref",
            "approved_execution_scope",
        )
        if getattr(policy, field_name) is None
    ]
    if missing:
        raise ValueError(f"execute_approved_action requires exact scope ref: {missing[0]}")
    _validate_policy_matches_approved_scope(policy)
    if policy.memory_scope != MemoryPolicy.scoped_to_approval.value:
        raise ValueError("execute_approved_action requires scoped approval memory policy")
    if policy.tool_policy != ToolPolicy.exact_approved_tool_only.value:
        raise ValueError("execute_approved_action requires exact approved tool policy")
    if policy.tool_choice != ToolChoicePolicy.exact_approved.value:
        raise ValueError("execute_approved_action requires exact approved tool choice")
    if policy.tools != [policy.allowed_tool_ref]:
        raise ValueError("execute_approved_action tools must match the exact approved tool ref")
    if policy.approval_policy != ApprovalPolicy.already_approved_exact_scope.value:
        raise ValueError("execute_approved_action requires already approved exact scope")
    if policy.approval_required:
        raise ValueError("execute_approved_action must not request fresh broad approval")
    if not all((policy.side_effects_allowed, policy.receipt_required, policy.execution_ready)):
        raise ValueError("execute_approved_action requires receipt-bound execution readiness")
    if not all((policy.tool_execution_allowed, policy.action_execution_allowed)):
        raise ValueError("execute_approved_action requires exact tool and action permission flags")
    blocked = [
        field_name
        for field_name in (
            "runtime_model_call_allowed",
            "provider_call_allowed",
            "memory_write_allowed",
            "workflow_execution_allowed",
            "context_injection_allowed",
            "shell_subprocess_allowed",
            "browser_network_allowed",
            "connector_write_allowed",
        )
        if getattr(policy, field_name)
    ]
    if blocked:
        raise ValueError(f"execute_approved_action enabled blocked authority: {blocked[0]}")


def _validate_turn_decision_matches_approved_scope(decision: TurnDecision) -> None:
    scope = decision.approved_execution_scope
    if scope is None:
        raise ValueError("execute_approved_action requires approved_execution_scope")
    expected = {
        "approval_scope_ref": scope.approval_scope_ref,
        "action_scope_ref": scope.action_scope_ref,
        "approved_tool_ref": scope.tool_ref,
        "approved_arguments_ref": scope.arguments_ref,
    }
    for field_name, expected_value in expected.items():
        if getattr(decision, field_name) != expected_value:
            raise ValueError(f"execute_approved_action scope mismatch: {field_name}")


def _validate_policy_matches_approved_scope(policy: InvocationPolicy) -> None:
    scope = policy.approved_execution_scope
    if scope is None:
        raise ValueError("execute_approved_action requires approved_execution_scope")
    expected = {
        "approval_scope_ref": scope.approval_scope_ref,
        "action_scope_ref": scope.action_scope_ref,
        "allowed_tool_ref": scope.tool_ref,
        "allowed_arguments_ref": scope.arguments_ref,
        "allowed_merchant_ref": scope.merchant_ref,
        "allowed_recipient_ref": scope.recipient_ref,
        "allowed_account_ref": scope.account_ref,
        "allowed_cost_ref": scope.cost_ref,
        "allowed_credential_broker_ref": scope.credential_broker_ref,
        "allowed_risk_ref": scope.risk_ref,
    }
    for field_name, expected_value in expected.items():
        if getattr(policy, field_name) != expected_value:
            raise ValueError(f"execute_approved_action scope mismatch: {field_name}")


def _validate_runtime_denials(policy: InvocationPolicy, owner: str) -> None:
    denied = [
        field_name
        for field_name in (
            "runtime_model_call_allowed",
            "provider_call_allowed",
            "memory_write_allowed",
            "tool_execution_allowed",
            "action_execution_allowed",
            "workflow_execution_allowed",
            "context_injection_allowed",
            "shell_subprocess_allowed",
            "browser_network_allowed",
            "connector_write_allowed",
        )
        if getattr(policy, field_name)
    ]
    if denied:
        raise ValueError(f"{owner} enabled denied runtime authority: {denied[0]}")


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        validate_task_ref(value, field_name)


def _validate_required_blocked_authorities(refs: list[str], owner: str) -> None:
    missing = set(TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS) - set(refs)
    if missing:
        raise ValueError(f"{owner} missing required blocked authority ref: {sorted(missing)[0]}")


def _validate_no_effect_flags(model: TurnDecision, owner: str) -> None:
    failed = [field_name for field_name in _NO_EFFECT_FLAGS if not getattr(model, field_name)]
    if failed:
        raise ValueError(f"{owner} failed no-effect proof flag: {failed[0]}")
