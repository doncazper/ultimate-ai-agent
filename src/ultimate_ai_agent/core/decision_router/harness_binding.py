from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.turn_classifier import classify_turn_contract
from ultimate_ai_agent.core.decision_router.turn_contracts import (
    ApprovalPolicy,
    InvocationPolicy,
    MemoryPolicy,
    OutputContract,
    RiskFlag,
    ToolPolicy,
    TurnContractKind,
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    compile_invocation_policy,
)
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


TURN_HARNESS_BINDING_CONTRACT_REF = "contract-ref:turn-contract-router:harness-binding:v1"
TURN_HARNESS_BINDING_NO_EFFECT_SCOPE = "turn_harness_binding_compilation_only"
DEFAULT_CHAT_HARNESS_ROUTE_REF = "/v1/chat/completions"


class TurnHarnessBindingReadModel(BaseModel):
    contract_ref: str = TURN_HARNESS_BINDING_CONTRACT_REF
    binding_ref: str = Field(..., min_length=1)
    decision_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    turn_contract: TurnContractKind
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    memory_scope: MemoryPolicy
    memory_touched: bool = False
    reviewed_memory_refs_allowed: bool = False
    memory_content_retrieved: bool = False
    memory_write_allowed: bool = False
    memory_write_performed: bool = False
    tool_policy: ToolPolicy
    tools_exposed_count: int = Field(default=0, ge=0)
    tool_refs: list[str] = Field(default_factory=list)
    execution_tools_exposed_count: int = Field(default=0, ge=0)
    planner: bool = False
    durable_state: bool = False
    approval_policy: ApprovalPolicy
    approval_required: bool = False
    approval_envelope_required: bool = False
    side_effects_allowed: bool = False
    execution_ready: bool = False
    receipt_required: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_memory_body_persisted: bool = False
    raw_local_path_persisted: bool = False
    credential_persisted: bool = False
    safe_refs_only: bool = True
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    no_effect_scope: str = TURN_HARNESS_BINDING_NO_EFFECT_SCOPE
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "TurnHarnessBindingReadModel":
        if self.contract_ref != TURN_HARNESS_BINDING_CONTRACT_REF:
            raise ValueError("unexpected turn harness binding contract ref")
        if self.no_effect_scope != TURN_HARNESS_BINDING_NO_EFFECT_SCOPE:
            raise ValueError("turn harness binding no-effect scope must be compilation-only")
        for field_name in ("contract_ref", "binding_ref", "decision_ref", "policy_ref"):
            validate_task_ref(getattr(self, field_name), field_name)
        validate_safe_task_text(self.no_effect_scope, "no_effect_scope")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.tool_refs, "tool_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if not self.safe_refs_only:
            raise ValueError("turn harness binding must be safe-ref only")
        if any(
            (
                self.raw_prompt_persisted,
                self.raw_response_persisted,
                self.raw_memory_body_persisted,
                self.raw_local_path_persisted,
                self.credential_persisted,
            )
        ):
            raise ValueError("turn harness binding must not persist raw or credential content")
        if self.memory_content_retrieved:
            raise ValueError("turn harness binding must not retrieve memory content")
        if self.memory_write_performed:
            raise ValueError("turn harness binding must not perform memory writes")
        if not all(
            (
                self.no_runtime_model_call_performed,
                self.no_provider_call_performed,
                self.no_tool_execution_performed,
                self.no_action_execution_performed,
                self.no_shell_subprocess_performed,
                self.no_browser_network_performed,
                self.no_connector_write_performed,
            )
        ):
            raise ValueError("turn harness binding must remain no-effect")
        if self.turn_contract in {
            TurnContractKind.answer_directly.value,
            TurnContractKind.base_answer.value,
        }:
            _validate_answer_binding_is_empty(self)
        return self


def build_turn_harness_binding(
    request_text: str,
    *,
    binding_ref: str = "turn-harness-binding:deterministic",
    decision_ref: str = "turn-decision:harness-binding",
) -> TurnHarnessBindingReadModel:
    decision = classify_turn_contract(request_text, decision_ref=decision_ref)
    policy = compile_invocation_policy(decision)
    return binding_from_policy(
        policy,
        binding_ref=binding_ref,
        reason_refs=[*decision.reason_refs, "reason-ref:turn-harness-binding:compiled-policy"],
        evidence_refs=decision.evidence_refs,
    )


def build_chat_turn_harness_binding(
    messages: Iterable[Any],
    *,
    model_ref: str,
    route_ref: str = DEFAULT_CHAT_HARNESS_ROUTE_REF,
) -> TurnHarnessBindingReadModel:
    suffix = _safe_suffix(f"{route_ref}:{model_ref}")
    return build_turn_harness_binding(
        _last_user_message_text(messages),
        binding_ref=f"turn-harness-binding:v1-chat:{suffix}",
        decision_ref=f"turn-decision:v1-chat:{suffix}",
    )


def binding_from_policy(
    policy: InvocationPolicy,
    *,
    binding_ref: str,
    reason_refs: list[str],
    evidence_refs: list[str] | None = None,
) -> TurnHarnessBindingReadModel:
    execution_tools_exposed_count = 1 if policy.tool_execution_allowed else 0
    return TurnHarnessBindingReadModel(
        binding_ref=binding_ref,
        decision_ref=policy.decision_ref,
        policy_ref=policy.policy_ref,
        turn_contract=policy.turn_contract,
        safe_summary="Turn harness binding read model prepared safe capability refs without execution.",
        reason_refs=reason_refs,
        evidence_refs=evidence_refs or [],
        risk_flags=policy.risk_flags,
        memory_scope=policy.memory_scope,
        memory_touched=False,
        reviewed_memory_refs_allowed=policy.memory_scope
        in {
            MemoryPolicy.reviewed_relevant_only.value,
            MemoryPolicy.proposal_review_only.value,
            MemoryPolicy.scoped_to_approval.value,
        },
        memory_content_retrieved=False,
        memory_write_allowed=policy.memory_write_allowed,
        memory_write_performed=False,
        tool_policy=policy.tool_policy,
        tools_exposed_count=len(policy.tools),
        tool_refs=policy.tools,
        execution_tools_exposed_count=execution_tools_exposed_count,
        planner=policy.planner,
        durable_state=policy.durable_state,
        approval_policy=policy.approval_policy,
        approval_required=policy.approval_required,
        approval_envelope_required=policy.output_contract == OutputContract.approval_envelope_required.value,
        side_effects_allowed=policy.side_effects_allowed,
        execution_ready=policy.execution_ready,
        receipt_required=policy.receipt_required,
        blocked_authority_refs=policy.blocked_authority_refs,
    )


def _validate_answer_binding_is_empty(binding: TurnHarnessBindingReadModel) -> None:
    expected = {
        "memory_touched": False,
        "reviewed_memory_refs_allowed": False,
        "memory_content_retrieved": False,
        "memory_write_allowed": False,
        "memory_write_performed": False,
        "tools_exposed_count": 0,
        "execution_tools_exposed_count": 0,
        "planner": False,
        "durable_state": False,
        "approval_required": False,
        "side_effects_allowed": False,
        "execution_ready": False,
        "receipt_required": False,
    }
    for field_name, expected_value in expected.items():
        if getattr(binding, field_name) != expected_value:
            raise ValueError(f"answer harness binding denied capability expansion: {field_name}")
    if binding.tool_refs:
        raise ValueError("answer harness binding denied capability expansion: tool_refs")


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _last_user_message_text(messages: Iterable[Any]) -> str:
    last_user_text: str | None = None
    for message in messages:
        role, content = _message_role_and_content(message)
        if role == "user" and isinstance(content, str) and content.strip():
            last_user_text = content
    return last_user_text or "status"


def _message_role_and_content(message: Any) -> tuple[str | None, Any]:
    if isinstance(message, Mapping):
        role = message.get("role")
        content = message.get("content")
    else:
        role = getattr(message, "role", None)
        content = getattr(message, "content", None)
    normalized_role = role.strip().lower() if isinstance(role, str) else None
    return normalized_role, content


def _safe_suffix(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"safe-{digest}"
