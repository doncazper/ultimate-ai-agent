from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.preview import (
    TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS,
    TurnRouterPreviewRequest,
    build_turn_router_preview,
)
from ultimate_ai_agent.core.decision_router.route_binding import (
    RouteDecisionBinding,
    build_route_decision_binding,
    safe_content_fingerprint_ref,
)
from ultimate_ai_agent.core.decision_router.turn_classifier import classify_turn_contract
from ultimate_ai_agent.core.decision_router.turn_contracts import (
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    TurnContractKind,
    compile_invocation_policy,
)
from ultimate_ai_agent.core.execution import (
    TurnRunApprovalChainReadModel,
    TurnRunApprovalState,
    TurnRunApprovalTransitionRequest,
    TurnRunApprovalTransitionStatus,
    apply_turn_run_approval_transition,
    build_empty_turn_run_approval_chain,
    build_sample_staged_orchestration_read_model,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)


PREPARED_TURN_SCHEMA_VERSION = "prepared_turn.v1"
PREPARED_TURN_CONTRACT_REF = "contract-ref:prepared-turn:v1"
PREPARED_TURN_CLI_REF = "repo-local-command:uaa-turn-router-prepare-turn"
PREPARED_TURN_API_REF = "GET /api/runtime/prepared-turn"
PREPARED_TURN_SOURCE_REF = "source-ref:prepared-turn:python-core"
PREPARED_TURN_REDACTIONS = (
    "redaction-ref:prepared-turn:raw-turn-text-omitted",
    "redaction-ref:prepared-turn:raw-model-output-omitted",
    "redaction-ref:prepared-turn:provider-payload-omitted",
)
PREPARED_TURN_BLOCKED_AUTHORITY_REFS = (
    *TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    "blocked-authority:prepared-turn-no-raw-prompt-persistence",
    "blocked-authority:prepared-turn-no-raw-model-output-persistence",
    "blocked-authority:prepared-turn-no-hidden-context-injection",
    "blocked-authority:prepared-turn-no-provider-model-call",
    "blocked-authority:prepared-turn-no-tool-execution",
    "blocked-authority:prepared-turn-no-action-execution",
    "blocked-authority:prepared-turn-no-browser-automation",
    "blocked-authority:prepared-turn-no-connector-write",
    "blocked-authority:prepared-turn-no-production-authority",
)


class PreparedTurnBranch(str, Enum):
    answer_directly = "answer_directly"
    base_answer = "base_answer"
    answer_with_reviewed_memory = "answer_with_reviewed_memory"
    draft_or_plan = "draft_or_plan"
    prepare_tool_or_action = "prepare_tool_or_action"
    approval_required = "approval_required"
    execute_approved_exact_action = "execute_approved_exact_action"
    blocked_unsafe = "blocked_unsafe"
    ask_clarifying_question = "ask_clarifying_question"


class PreparedTurnReadiness(BaseModel):
    readiness_ref: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    ready: bool = False
    review_required: bool = False
    blocked: bool = False
    refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_readiness(self) -> "PreparedTurnReadiness":
        validate_task_ref(self.readiness_ref, "readiness_ref")
        validate_safe_task_text(self.status, "readiness_status")
        validate_safe_task_text(self.safe_summary, "readiness_safe_summary")
        for ref in [*self.refs, *self.blocked_authority_refs]:
            validate_task_ref(ref, "prepared_turn_readiness_ref")
        if self.ready and self.blocked:
            raise ValueError("PREPARED_TURN_READINESS_READY_AND_BLOCKED")
        return self


class PreparedTurnNextAction(BaseModel):
    action_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    requires_approval: bool = False
    execution_permitted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_next_action(self) -> "PreparedTurnNextAction":
        validate_task_ref(self.action_ref, "next_action_ref")
        validate_safe_task_text(self.label, "next_action_label")
        validate_safe_task_text(self.safe_summary, "next_action_safe_summary")
        if self.execution_permitted:
            raise ValueError("PREPARED_TURN_NEXT_ACTION_EXECUTION_DENIED")
        return self


class PreparedTurn(BaseModel):
    schema_version: str = PREPARED_TURN_SCHEMA_VERSION
    contract_ref: str = PREPARED_TURN_CONTRACT_REF
    source_ref: str = PREPARED_TURN_SOURCE_REF
    prepared_turn_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    operator_ref: str = Field(..., min_length=1)
    task_ref: str = Field(..., min_length=1)
    latest_user_turn_ref: str = Field(..., min_length=1)
    turn_contract_decision_ref: str = Field(..., min_length=1)
    selected_turn_contract: str = Field(..., min_length=1)
    branch: PreparedTurnBranch
    route_decision_binding: RouteDecisionBinding
    memory_readiness: PreparedTurnReadiness
    context_readiness: PreparedTurnReadiness
    tool_action_readiness: PreparedTurnReadiness
    orchestration_readiness: PreparedTurnReadiness
    durable_run_ref: str | None = None
    turn_run_approval_chain: TurnRunApprovalChainReadModel | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    next_actions: list[PreparedTurnNextAction] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(PREPARED_TURN_BLOCKED_AUTHORITY_REFS)
    )
    redactions_applied: list[str] = Field(default_factory=lambda: list(PREPARED_TURN_REDACTIONS))
    safe_summary: str = Field(..., min_length=1)
    raw_prompt_persisted: bool = False
    raw_model_output_persisted: bool = False
    provider_payload_persisted: bool = False
    context_injection_performed: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    action_execution_performed: bool = False
    execution_performed: bool = False
    backend_owned: bool = True
    control_center_can_mint_authority: bool = False
    cli_ref: str = PREPARED_TURN_CLI_REF
    api_ref: str = PREPARED_TURN_API_REF

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_prepared_turn(self) -> "PreparedTurn":
        for field_name in (
            "contract_ref",
            "source_ref",
            "prepared_turn_ref",
            "session_ref",
            "operator_ref",
            "task_ref",
            "latest_user_turn_ref",
            "turn_contract_decision_ref",
            "cli_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        validate_safe_task_text(self.api_ref, "api_ref")
        validate_safe_task_text(self.selected_turn_contract, "selected_turn_contract")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        if self.durable_run_ref:
            validate_task_ref(self.durable_run_ref, "durable_run_ref")
        for ref in [
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.redactions_applied,
        ]:
            validate_task_ref(ref, "prepared_turn_ref_list")
        denied_flags = (
            self.raw_prompt_persisted,
            self.raw_model_output_persisted,
            self.provider_payload_persisted,
            self.context_injection_performed,
            self.model_call_performed,
            self.tool_execution_performed,
            self.action_execution_performed,
            self.execution_performed,
            not self.backend_owned,
            self.control_center_can_mint_authority,
        )
        if any(denied_flags):
            raise ValueError("PREPARED_TURN_AUTHORITY_OR_RAW_PERSISTENCE_DENIED")
        return self


def prepare_turn(
    *,
    text: str | None = None,
    sample_id: str | None = None,
    session_ref: str = "session-ref:prepared-turn:local",
    operator_ref: str = "operator-ref:prepared-turn:local",
    task_ref: str = "task-ref:prepared-turn:local",
) -> PreparedTurn:
    if bool(text) == bool(sample_id):
        raise ValueError("provide exactly one of text or sample_id")
    request = TurnRouterPreviewRequest(sample_id=sample_id, text=text)
    preview = build_turn_router_preview(request)
    turn_text = (
        TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS[sample_id]
        if sample_id is not None
        else text or ""
    )
    decision = classify_turn_contract(turn_text)
    policy = compile_invocation_policy(decision)
    suffix = sample_id or "ephemeral"
    latest_turn_ref = f"turn-ref:prepared-turn:{suffix}"
    content_fingerprint_ref = safe_content_fingerprint_ref(
        turn_text,
        namespace="prepared-turn-content",
    )
    route_binding = build_route_decision_binding(
        policy,
        actor_ref=operator_ref,
        session_ref=session_ref,
        turn_ref=latest_turn_ref,
        route_ref=PREPARED_TURN_API_REF,
        side_effect_class="local_dev_workspace_only",
        idempotency_key=f"idempotency-ref:prepared-turn:{suffix}",
        content_fingerprint_ref=content_fingerprint_ref,
        context_fingerprint_ref=_context_fingerprint_ref(policy.turn_contract),
        approval_ref=_approval_ref(policy.turn_contract),
        approval_scope_ref=policy.approval_scope_ref,
        resource_refs=[task_ref],
    )
    branch = _branch_for_contract(policy.turn_contract)
    chain = _prepared_turn_approval_chain(
        suffix=suffix,
        latest_turn_ref=latest_turn_ref,
        task_ref=task_ref,
        route_binding=route_binding,
        approval_ref=_approval_ref(policy.turn_contract),
    )
    return PreparedTurn(
        prepared_turn_ref=f"prepared-turn-ref:{suffix}",
        session_ref=session_ref,
        operator_ref=operator_ref,
        task_ref=task_ref,
        latest_user_turn_ref=latest_turn_ref,
        turn_contract_decision_ref=decision.decision_ref,
        selected_turn_contract=policy.turn_contract,
        branch=branch,
        route_decision_binding=route_binding,
        memory_readiness=_memory_readiness(policy.turn_contract),
        context_readiness=_context_readiness(policy.turn_contract),
        tool_action_readiness=_tool_action_readiness(policy.turn_contract),
        orchestration_readiness=_orchestration_readiness(policy.turn_contract),
        durable_run_ref=chain.linkage.durable_run_ref.ref,
        turn_run_approval_chain=chain,
        evidence_refs=[
            *preview.evidence_refs,
            "evidence-ref:prepared-turn:route-binding",
            "evidence-ref:prepared-turn:orchestration",
        ],
        next_actions=_next_actions(policy.turn_contract),
        safe_summary=_safe_summary(policy.turn_contract),
    )


def _prepared_turn_approval_chain(
    *,
    suffix: str,
    latest_turn_ref: str,
    task_ref: str,
    route_binding: RouteDecisionBinding,
    approval_ref: str | None,
) -> TurnRunApprovalChainReadModel:
    durable_run_ref = f"durable-run-ref:prepared-turn:{suffix}"
    chain = build_empty_turn_run_approval_chain(
        chain_ref=f"turn-run-chain:prepared-turn:{suffix}",
        turn_ref=latest_turn_ref,
        durable_run_ref=durable_run_ref,
        operator_task_ref=task_ref,
        approval_ref=approval_ref,
        route_decision_binding_ref=route_binding.binding_ref,
    )
    target_states = [TurnRunApprovalState.routed]
    if str(route_binding.turn_contract) in {
        TurnContractKind.draft_or_plan.value,
        TurnContractKind.prepare_tool_or_action.value,
        TurnContractKind.approval_required.value,
        TurnContractKind.execute_approved_action.value,
    }:
        target_states.append(TurnRunApprovalState.planning)
    if approval_ref:
        target_states.append(TurnRunApprovalState.waiting_for_approval)
    for state in target_states:
        request = TurnRunApprovalTransitionRequest(
            transition_ref=f"turn-run-transition:prepared-turn:{suffix}:{state.value}",
            from_state=chain.current_state,
            to_state=state,
            actor_ref=route_binding.actor_ref,
            idempotency_key=f"idempotency-ref:prepared-turn:{suffix}:{state.value}",
            checkpoint_ref=f"checkpoint-ref:prepared-turn:{suffix}:{state.value}",
            receipt_ref=f"receipt-ref:prepared-turn:{suffix}:{state.value}",
            replay_ref=f"replay-ref:prepared-turn:{suffix}:{state.value}",
            approval_ref=approval_ref
            if state == TurnRunApprovalState.waiting_for_approval
            else None,
            approval_scope_run_ref=durable_run_ref
            if state == TurnRunApprovalState.waiting_for_approval
            else None,
            approval_scope_turn_ref=latest_turn_ref
            if state == TurnRunApprovalState.waiting_for_approval
            else None,
            route_decision_binding_ref=route_binding.binding_ref,
            evidence_refs=[f"evidence-ref:prepared-turn-chain:{state.value}"],
            reason_refs=[f"reason-ref:prepared-turn-chain:{state.value}"],
            safe_summary="Prepared turn recorded state-only durable run posture.",
        )
        chain, decision = apply_turn_run_approval_transition(chain, request)
        if decision.status != TurnRunApprovalTransitionStatus.accepted.value:
            raise ValueError("prepared turn approval chain transition failed")
    return chain


def build_sample_prepared_turns() -> list[PreparedTurn]:
    return [
        prepare_turn(sample_id="diy-desk"),
        prepare_turn(sample_id="office-memory"),
        prepare_turn(sample_id="current-lumber-prices"),
        prepare_turn(sample_id="order-materials"),
        prepare_turn(sample_id="base-answer-bypass"),
    ]


def _branch_for_contract(turn_contract: str) -> PreparedTurnBranch:
    if turn_contract == TurnContractKind.execute_approved_action.value:
        return PreparedTurnBranch.execute_approved_exact_action
    return PreparedTurnBranch(turn_contract)


def _context_fingerprint_ref(turn_contract: str) -> str | None:
    if turn_contract in {
        TurnContractKind.answer_with_reviewed_memory.value,
        TurnContractKind.draft_or_plan.value,
        TurnContractKind.prepare_tool_or_action.value,
        TurnContractKind.approval_required.value,
        TurnContractKind.execute_approved_action.value,
    }:
        return f"context-fingerprint-ref:prepared-turn:{turn_contract}"
    return None


def _approval_ref(turn_contract: str) -> str | None:
    if turn_contract in {
        TurnContractKind.approval_required.value,
        TurnContractKind.execute_approved_action.value,
    }:
        return f"approval-ref:prepared-turn:{turn_contract}"
    return None


def _memory_readiness(turn_contract: str) -> PreparedTurnReadiness:
    if turn_contract == TurnContractKind.answer_with_reviewed_memory.value:
        return PreparedTurnReadiness(
            readiness_ref="readiness-ref:prepared-turn:memory-reviewed",
            status="reviewed_memory_refs_ready",
            safe_summary="Reviewed memory refs may support the answer without raw memory bodies.",
            ready=True,
            review_required=True,
            refs=["memory-ref:prepared-turn:reviewed-context"],
        )
    return PreparedTurnReadiness(
        readiness_ref="readiness-ref:prepared-turn:memory-not-used",
        status="memory_not_used",
        safe_summary="This branch does not retrieve or inject memory.",
    )


def _context_readiness(turn_contract: str) -> PreparedTurnReadiness:
    if turn_contract in {
        TurnContractKind.answer_with_reviewed_memory.value,
        TurnContractKind.draft_or_plan.value,
        TurnContractKind.prepare_tool_or_action.value,
        TurnContractKind.approval_required.value,
    }:
        return PreparedTurnReadiness(
            readiness_ref=f"readiness-ref:prepared-turn:context:{turn_contract}",
            status="context_refs_ready",
            safe_summary="Context readiness uses safe refs only and performs no injection.",
            ready=True,
            refs=[f"context-pack-ref:prepared-turn:{turn_contract}"],
        )
    return PreparedTurnReadiness(
        readiness_ref="readiness-ref:prepared-turn:context-not-used",
        status="context_not_used",
        safe_summary="No context pack is needed for this branch.",
    )


def _tool_action_readiness(turn_contract: str) -> PreparedTurnReadiness:
    if turn_contract == TurnContractKind.prepare_tool_or_action.value:
        return PreparedTurnReadiness(
            readiness_ref="readiness-ref:prepared-turn:tool-action-proposal",
            status="proposal_only",
            safe_summary="Tool/action readiness is proposal-only; execution stays blocked.",
            ready=True,
            review_required=True,
            refs=["tool-intent-ref:prepared-turn:read-only-research"],
            blocked_authority_refs=["blocked-authority:prepared-turn-no-tool-execution"],
        )
    if turn_contract == TurnContractKind.approval_required.value:
        return PreparedTurnReadiness(
            readiness_ref="readiness-ref:prepared-turn:approval-envelope",
            status="approval_required",
            safe_summary="Action envelope posture is ready for exact operator approval.",
            ready=True,
            review_required=True,
            refs=["action-envelope-ref:prepared-turn:approval-required"],
            blocked_authority_refs=["blocked-authority:prepared-turn-no-action-execution"],
        )
    if turn_contract == TurnContractKind.blocked_unsafe.value:
        return PreparedTurnReadiness(
            readiness_ref="readiness-ref:prepared-turn:blocked-unsafe",
            status="blocked",
            safe_summary="Unsafe or unsupported work is blocked before tool/action prep.",
            blocked=True,
            blocked_authority_refs=["blocked-authority:prepared-turn-blocked-unsafe"],
        )
    return PreparedTurnReadiness(
        readiness_ref="readiness-ref:prepared-turn:tool-action-not-used",
        status="tool_action_not_used",
        safe_summary="No tool or action readiness is needed for this branch.",
    )


def _orchestration_readiness(turn_contract: str) -> PreparedTurnReadiness:
    read_model = build_sample_staged_orchestration_read_model()
    if turn_contract in {
        TurnContractKind.draft_or_plan.value,
        TurnContractKind.prepare_tool_or_action.value,
        TurnContractKind.approval_required.value,
    }:
        return PreparedTurnReadiness(
            readiness_ref="readiness-ref:prepared-turn:staged-orchestration",
            status="eligible_no_effect",
            safe_summary="Staged orchestration is inspectable as no-effect plan posture.",
            ready=True,
            refs=[read_model.plan.plan_ref],
        )
    return PreparedTurnReadiness(
        readiness_ref="readiness-ref:prepared-turn:orchestration-not-needed",
        status="orchestration_not_needed",
        safe_summary="No staged orchestration is needed for this branch.",
    )


def _next_actions(turn_contract: str) -> list[PreparedTurnNextAction]:
    if turn_contract in {
        TurnContractKind.answer_directly.value,
        TurnContractKind.base_answer.value,
    }:
        return [
            PreparedTurnNextAction(
                action_ref="next-action-ref:prepared-turn:answer",
                label="answer",
                safe_summary="Return a direct answer without memory, tools, or durable mutation.",
            )
        ]
    if turn_contract == TurnContractKind.answer_with_reviewed_memory.value:
        return [
            PreparedTurnNextAction(
                action_ref="next-action-ref:prepared-turn:answer-with-memory-refs",
                label="answer_with_reviewed_memory_refs",
                safe_summary="Answer using reviewed memory refs only.",
            )
        ]
    if turn_contract == TurnContractKind.approval_required.value:
        return [
            PreparedTurnNextAction(
                action_ref="next-action-ref:prepared-turn:request-approval",
                label="request_exact_approval",
                safe_summary="Ask the operator to approve the exact action envelope.",
                requires_approval=True,
            )
        ]
    if turn_contract == TurnContractKind.blocked_unsafe.value:
        return [
            PreparedTurnNextAction(
                action_ref="next-action-ref:prepared-turn:block",
                label="explain_blocked_state",
                safe_summary="Explain the blocked state and offer a safe alternative.",
            )
        ]
    if turn_contract == TurnContractKind.ask_clarifying_question.value:
        return [
            PreparedTurnNextAction(
                action_ref="next-action-ref:prepared-turn:clarify",
                label="ask_clarifying_question",
                safe_summary="Ask a clarifying question before choosing a branch.",
            )
        ]
    return [
        PreparedTurnNextAction(
            action_ref="next-action-ref:prepared-turn:plan-or-propose",
            label="draft_or_propose",
            safe_summary="Draft a plan or proposal without executing tools/actions.",
        )
    ]


def _safe_summary(turn_contract: str) -> str:
    summaries: dict[str, str] = {
        TurnContractKind.answer_directly.value: "Prepared turn can answer directly.",
        TurnContractKind.base_answer.value: "Prepared turn uses the base_answer branch.",
        TurnContractKind.answer_with_reviewed_memory.value: (
            "Prepared turn can answer with reviewed memory refs."
        ),
        TurnContractKind.draft_or_plan.value: "Prepared turn can draft or plan.",
        TurnContractKind.prepare_tool_or_action.value: (
            "Prepared turn can prepare a tool/action proposal without execution."
        ),
        TurnContractKind.approval_required.value: (
            "Prepared turn requires exact operator approval before execution."
        ),
        TurnContractKind.execute_approved_action.value: (
            "Prepared turn can only execute an already approved exact action in a future lane."
        ),
        TurnContractKind.ask_clarifying_question.value: (
            "Prepared turn should ask a clarifying question."
        ),
        TurnContractKind.blocked_unsafe.value: "Prepared turn is blocked as unsafe.",
    }
    return summaries.get(turn_contract, "Prepared turn branch is inspectable.")
