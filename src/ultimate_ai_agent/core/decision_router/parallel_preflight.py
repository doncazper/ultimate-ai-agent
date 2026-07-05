from __future__ import annotations

import asyncio
import re
from enum import Enum
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.turn_classifier import classify_turn_contract
from ultimate_ai_agent.core.decision_router.turn_contracts import (
    InvocationPolicy,
    PromptProfilePolicy,
    RiskFlag,
    TurnContractKind,
    TurnDecision,
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    compile_invocation_policy,
)
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


TURN_PREFLIGHT_CONTRACT_REF = "contract-ref:turn-contract-router:parallel-preflight:v1"
TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    *TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    "blocked-authority:no-preflight-authority-grant",
    "blocked-authority:no-preflight-user-visible-draft",
    "blocked-authority:no-parallel-lane-execution",
)
TURN_PREFLIGHT_ENGINE_REF = "engine-ref:turn-contract-router:parallel-preflight:v1"


class TurnPreflightLaneKind(str, Enum):
    intent_lane = "intent_lane"
    risk_action_lane = "risk_action_lane"
    memory_trigger_lane = "memory_trigger_lane"
    memory_relevance_lane = "memory_relevance_lane"
    tool_manifest_lane = "tool_manifest_lane"
    answer_profile_lane = "answer_profile_lane"
    direct_answer_draft = "direct_answer_draft"


TURN_PREFLIGHT_REQUIRED_LANE_KINDS = tuple(item.value for item in TurnPreflightLaneKind)

_NO_EFFECT_FLAGS = (
    "no_runtime_model_call_performed",
    "no_provider_call_performed",
    "no_tool_execution_performed",
    "no_action_execution_performed",
    "no_workflow_execution_performed",
    "no_context_injection_performed",
    "no_memory_content_retrieved",
    "no_memory_write_performed",
    "no_durable_state_write_performed",
    "no_shell_subprocess_performed",
    "no_browser_network_performed",
    "no_connector_write_performed",
)
_RAW_TURN_TEXT_PATTERNS = (
    re.compile(r"\bhow do i build\b", re.IGNORECASE),
    re.compile(r"\bexplain how photosynthesis works\b", re.IGNORECASE),
    re.compile(r"\bwhat is a clean way to organize\b", re.IGNORECASE),
    re.compile(r"\bdesign one for my office\b", re.IGNORECASE),
    re.compile(r"\bmake me a shopping list\b", re.IGNORECASE),
    re.compile(r"\bfind current lumber prices\b", re.IGNORECASE),
    re.compile(r"\border the materials\b", re.IGNORECASE),
    re.compile(r"\buse my card\b", re.IGNORECASE),
    re.compile(r"\bremember that i prefer\b", re.IGNORECASE),
)


class TurnPreflightLaneResult(BaseModel):
    contract_ref: str = TURN_PREFLIGHT_CONTRACT_REF
    lane_result_ref: str = Field(..., min_length=1)
    lane_kind: TurnPreflightLaneKind
    candidate_turn_contract: TurnContractKind | None = None
    answer_profile_hint: PromptProfilePolicy | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    signal_refs: list[str] = Field(default_factory=list)
    memory_ref_candidates: list[str] = Field(default_factory=list)
    tool_category_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_content_included: bool = False
    authority_granted: bool = False
    execution_permitted: bool = False
    user_visible: bool = False
    direct_answer_draft_visible_to_user: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_lane_result(self) -> "TurnPreflightLaneResult":
        _validate_contract_ref(self.contract_ref)
        validate_task_ref(self.lane_result_ref, "lane_result_ref")
        _validate_safe_preflight_summary(self.safe_summary, "safe_summary")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.signal_refs, "signal_refs")
        _validate_ref_list(self.memory_ref_candidates, "memory_ref_candidates")
        _validate_ref_list(self.tool_category_refs, "tool_category_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn preflight lane")
        _validate_no_authority(self, "turn preflight lane")
        _validate_no_effect_flags(self, "turn preflight lane")
        if self.candidate_turn_contract == TurnContractKind.execute_approved_action.value:
            raise ValueError("parallel preflight lanes cannot select execute_approved_action")
        if self.lane_kind == TurnPreflightLaneKind.direct_answer_draft.value and self.user_visible:
            raise ValueError("direct_answer_draft lane result must not be user-visible")
        if (
            self.lane_kind == TurnPreflightLaneKind.direct_answer_draft.value
            and self.candidate_turn_contract
            not in {
                TurnContractKind.answer_directly.value,
                TurnContractKind.base_answer.value,
            }
        ):
            raise ValueError("direct_answer_draft lane can only draft direct/base answer candidates")
        if self.direct_answer_draft_visible_to_user:
            raise ValueError("direct_answer_draft cannot be visible before arbitration clears it")
        return self


class TurnPreflightBundle(BaseModel):
    contract_ref: str = TURN_PREFLIGHT_CONTRACT_REF
    bundle_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    lane_results: list[TurnPreflightLaneResult] = Field(default_factory=list, min_length=1)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_content_included: bool = False
    authority_granted: bool = False
    execution_permitted: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_bundle(self) -> "TurnPreflightBundle":
        _validate_contract_ref(self.contract_ref)
        validate_task_ref(self.bundle_ref, "bundle_ref")
        _validate_safe_preflight_summary(self.safe_summary, "safe_summary")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn preflight bundle")
        _validate_no_authority(self, "turn preflight bundle")
        _validate_no_effect_flags(self, "turn preflight bundle")
        _validate_required_lane_kinds(self.lane_results)
        return self


class TurnPreflightArbitrationInput(BaseModel):
    contract_ref: str = TURN_PREFLIGHT_CONTRACT_REF
    arbitration_input_ref: str = Field(..., min_length=1)
    bundle: TurnPreflightBundle
    safe_summary: str = Field(..., min_length=1, max_length=500)
    candidate_decision_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_content_included: bool = False
    authority_granted: bool = False
    execution_permitted: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_arbitration_input(self) -> "TurnPreflightArbitrationInput":
        _validate_contract_ref(self.contract_ref)
        validate_task_ref(self.arbitration_input_ref, "arbitration_input_ref")
        _validate_safe_preflight_summary(self.safe_summary, "safe_summary")
        _validate_ref_list(self.candidate_decision_refs, "candidate_decision_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn preflight arbitration input")
        _validate_no_authority(self, "turn preflight arbitration input")
        _validate_no_effect_flags(self, "turn preflight arbitration input")
        return self


class TurnPreflightArbitrationResult(BaseModel):
    contract_ref: str = TURN_PREFLIGHT_CONTRACT_REF
    arbitration_result_ref: str = Field(..., min_length=1)
    arbitration_input_ref: str = Field(..., min_length=1)
    selected_turn_contract: TurnContractKind
    selected_decision_ref: str = Field(..., min_length=1)
    selected_policy_ref: str = Field(..., min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    lane_result_refs: list[str] = Field(default_factory=list, min_length=1)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    direct_answer_draft_cleared_for_display: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False
    authority_granted: bool = False
    execution_permitted: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_arbitration_result(self) -> "TurnPreflightArbitrationResult":
        _validate_contract_ref(self.contract_ref)
        validate_task_ref(self.arbitration_result_ref, "arbitration_result_ref")
        validate_task_ref(self.arbitration_input_ref, "arbitration_input_ref")
        validate_task_ref(self.selected_decision_ref, "selected_decision_ref")
        validate_task_ref(self.selected_policy_ref, "selected_policy_ref")
        _validate_safe_preflight_summary(self.safe_summary, "safe_summary")
        _validate_ref_list(self.lane_result_refs, "lane_result_refs")
        _validate_ref_list(self.reason_refs, "reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn preflight arbitration result")
        _validate_no_authority(self, "turn preflight arbitration result")
        _validate_no_effect_flags(self, "turn preflight arbitration result")
        if self.selected_turn_contract == TurnContractKind.execute_approved_action.value:
            raise ValueError("parallel preflight arbitration cannot select execute_approved_action")
        if self.direct_answer_draft_cleared_for_display and self.selected_turn_contract not in {
            TurnContractKind.answer_directly.value,
            TurnContractKind.base_answer.value,
        }:
            raise ValueError("direct_answer_draft can only be cleared for direct/base answer contracts")
        if self.direct_answer_draft_cleared_for_display and any(
            risk_flag != RiskFlag.low_risk.value for risk_flag in self.risk_flags
        ):
            raise ValueError("direct_answer_draft cannot be cleared with non-low-risk flags")
        return self


class TurnPreflightRunResult(BaseModel):
    contract_ref: str = TURN_PREFLIGHT_CONTRACT_REF
    engine_ref: str = TURN_PREFLIGHT_ENGINE_REF
    run_ref: str = Field(..., min_length=1)
    bundle: TurnPreflightBundle
    arbitration_input: TurnPreflightArbitrationInput
    arbitration_result: TurnPreflightArbitrationResult
    turn_decision: TurnDecision
    invocation_policy: InvocationPolicy
    latency_ms_bucket: str = "under_25_ms"
    safe_summary: str = Field(..., min_length=1, max_length=500)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_content_included: bool = False
    authority_granted: bool = False
    execution_permitted: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True
    invocation_policy_compiled_only: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_run_result(self) -> "TurnPreflightRunResult":
        _validate_contract_ref(self.contract_ref)
        validate_task_ref(self.engine_ref, "engine_ref")
        validate_task_ref(self.run_ref, "run_ref")
        _validate_safe_preflight_summary(self.safe_summary, "safe_summary")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "turn preflight run")
        _validate_no_authority(self, "turn preflight run")
        _validate_no_effect_flags(self, "turn preflight run")
        if self.turn_decision.turn_contract != self.arbitration_result.selected_turn_contract:
            raise ValueError("turn preflight run selected contract drift")
        if self.invocation_policy.turn_contract != self.turn_decision.turn_contract:
            raise ValueError("turn preflight run invocation policy drift")
        if self.arbitration_result.selected_decision_ref != self.turn_decision.decision_ref:
            raise ValueError("turn preflight run selected decision ref drift")
        if self.arbitration_result.selected_policy_ref != self.invocation_policy.policy_ref:
            raise ValueError("turn preflight run selected policy ref drift")
        if self.turn_decision.turn_contract == TurnContractKind.execute_approved_action.value:
            raise ValueError("turn preflight run cannot select execute_approved_action")
        if not self.invocation_policy_compiled_only:
            raise ValueError("turn preflight run invocation policy is advisory only")
        return self


def run_parallel_turn_preflight(
    request_text: str,
    *,
    run_ref: str = "turn-preflight-run:deterministic",
    decision_ref: str = "turn-decision:parallel-preflight",
) -> TurnPreflightRunResult:
    return asyncio.run(
        run_parallel_turn_preflight_async(
            request_text,
            run_ref=run_ref,
            decision_ref=decision_ref,
        )
    )


async def run_parallel_turn_preflight_async(
    request_text: str,
    *,
    run_ref: str = "turn-preflight-run:deterministic",
    decision_ref: str = "turn-decision:parallel-preflight",
) -> TurnPreflightRunResult:
    start = perf_counter()
    seed_decision = classify_turn_contract(
        request_text,
        decision_ref=f"{decision_ref}:serial-seed",
        source_refs=["source:turn-preflight:serial-seed"],
        evidence_refs=["evidence:turn-preflight:serial-seed"],
    )
    lane_results = await asyncio.gather(
        *[
            _run_lane_safely(lane_kind, seed_decision)
            for lane_kind in TurnPreflightLaneKind
        ]
    )
    bundle = TurnPreflightBundle(
        bundle_ref=f"turn-preflight-bundle:{_safe_ref_suffix(run_ref)}",
        safe_summary="Parallel preflight completed no-effect sensing lanes with safe refs only.",
        lane_results=list(lane_results),
        reason_refs=["reason-ref:turn-preflight:bundle-built"],
        source_refs=["source:turn-preflight:engine"],
        evidence_refs=["evidence:turn-preflight:bundle"],
    )
    arbitration_input = TurnPreflightArbitrationInput(
        arbitration_input_ref=f"turn-preflight-arbitration-input:{_safe_ref_suffix(run_ref)}",
        bundle=bundle,
        safe_summary="Central arbitration input prepared lane refs for deterministic selection.",
        candidate_decision_refs=[seed_decision.decision_ref],
    )
    turn_decision = _arbitrate_turn_decision(
        seed_decision,
        list(lane_results),
        decision_ref=decision_ref,
    )
    invocation_policy = compile_invocation_policy(turn_decision)
    direct_draft_cleared = _direct_answer_draft_cleared_for_display(turn_decision, list(lane_results))
    arbitration_result = TurnPreflightArbitrationResult(
        arbitration_result_ref=f"turn-preflight-arbitration-result:{_safe_ref_suffix(run_ref)}",
        arbitration_input_ref=arbitration_input.arbitration_input_ref,
        selected_turn_contract=turn_decision.turn_contract,
        selected_decision_ref=turn_decision.decision_ref,
        selected_policy_ref=invocation_policy.policy_ref,
        confidence=turn_decision.confidence,
        safe_summary="Central arbitration selected one turn contract and compiled one invocation policy.",
        lane_result_refs=[result.lane_result_ref for result in lane_results],
        reason_refs=["reason-ref:turn-preflight:central-arbitration", *turn_decision.reason_refs],
        evidence_refs=turn_decision.evidence_refs,
        risk_flags=turn_decision.risk_flags,
        direct_answer_draft_cleared_for_display=direct_draft_cleared,
    )
    return TurnPreflightRunResult(
        run_ref=run_ref,
        bundle=bundle,
        arbitration_input=arbitration_input,
        arbitration_result=arbitration_result,
        turn_decision=turn_decision,
        invocation_policy=invocation_policy,
        latency_ms_bucket=_latency_bucket((perf_counter() - start) * 1000),
        safe_summary="Parallel preflight run produced no-effect routing truth for one turn.",
    )


async def _run_lane_safely(
    lane_kind: TurnPreflightLaneKind,
    seed_decision: TurnDecision,
) -> TurnPreflightLaneResult:
    try:
        return _default_lane_result(lane_kind, seed_decision)
    except Exception:
        return TurnPreflightLaneResult(
            lane_result_ref=f"turn-preflight-lane:{lane_kind.value}:failed-closed",
            lane_kind=lane_kind,
            candidate_turn_contract=TurnContractKind.approval_required,
            confidence=0.0,
            safe_summary="Parallel preflight lane failed closed without expanding authority.",
            reason_refs=["reason-ref:turn-preflight:lane-failed-closed"],
            source_refs=[f"source:turn-preflight:{lane_kind.value}"],
            evidence_refs=["evidence:turn-preflight:lane-failed-closed"],
            risk_flags=[RiskFlag.privacy_boundary],
        )


def _default_lane_result(lane_kind: TurnPreflightLaneKind, seed_decision: TurnDecision) -> TurnPreflightLaneResult:
    if lane_kind == TurnPreflightLaneKind.intent_lane:
        return _lane_result(
            lane_kind,
            seed_decision,
            reason_ref="reason-ref:turn-preflight:intent-candidate",
            signal_ref="signal-ref:turn-preflight:intent",
            safe_summary="Intent lane proposed a turn contract candidate without effects.",
        )
    if lane_kind == TurnPreflightLaneKind.risk_action_lane:
        risk_candidate = (
            TurnContractKind.approval_required
            if _has_risk(seed_decision, RiskFlag.external_side_effect, RiskFlag.credential_or_payment, RiskFlag.destructive)
            else seed_decision.turn_contract
        )
        return _lane_result(
            lane_kind,
            seed_decision,
            candidate_turn_contract=risk_candidate,
            reason_ref="reason-ref:turn-preflight:risk-action",
            signal_ref="signal-ref:turn-preflight:risk-action",
            safe_summary="Risk/action lane emitted veto or low-risk refs without execution.",
        )
    if lane_kind == TurnPreflightLaneKind.memory_trigger_lane:
        memory_candidate = (
            TurnContractKind.answer_with_reviewed_memory
            if RiskFlag.memory_requested.value in seed_decision.risk_flags
            else seed_decision.turn_contract
        )
        return _lane_result(
            lane_kind,
            seed_decision,
            candidate_turn_contract=memory_candidate,
            reason_ref="reason-ref:turn-preflight:memory-trigger",
            signal_ref="signal-ref:turn-preflight:memory-trigger",
            safe_summary="Memory trigger lane identified whether reviewed memory refs may be considered.",
        )
    if lane_kind == TurnPreflightLaneKind.memory_relevance_lane:
        memory_refs = (
            ["memory-ref:turn-preflight:reviewed-relevance-candidate"]
            if RiskFlag.memory_requested.value in seed_decision.risk_flags
            else []
        )
        return _lane_result(
            lane_kind,
            seed_decision,
            reason_ref="reason-ref:turn-preflight:memory-relevance",
            signal_ref="signal-ref:turn-preflight:memory-relevance",
            safe_summary="Memory relevance lane returned reviewed safe refs only when memory was triggered.",
            memory_ref_candidates=memory_refs,
        )
    if lane_kind == TurnPreflightLaneKind.tool_manifest_lane:
        tool_refs = _tool_category_refs_for_contract(str(seed_decision.turn_contract))
        return _lane_result(
            lane_kind,
            seed_decision,
            reason_ref="reason-ref:turn-preflight:tool-manifest",
            signal_ref="signal-ref:turn-preflight:tool-manifest",
            safe_summary="Tool manifest lane returned tool category refs without tool execution.",
            tool_category_refs=tool_refs,
        )
    if lane_kind == TurnPreflightLaneKind.answer_profile_lane:
        return _lane_result(
            lane_kind,
            seed_decision,
            answer_profile_hint=_answer_profile_for_contract(str(seed_decision.turn_contract)),
            reason_ref="reason-ref:turn-preflight:answer-profile",
            signal_ref="signal-ref:turn-preflight:answer-profile",
            safe_summary="Answer profile lane returned a prompt-profile hint without backend routing.",
        )
    direct_candidate = (
        seed_decision.turn_contract
        if seed_decision.turn_contract
        in {
            TurnContractKind.answer_directly.value,
            TurnContractKind.base_answer.value,
        }
        else TurnContractKind.answer_directly
    )
    return _lane_result(
        lane_kind,
        seed_decision,
        candidate_turn_contract=direct_candidate,
        reason_ref="reason-ref:turn-preflight:direct-answer-draft-held",
        signal_ref="signal-ref:turn-preflight:direct-answer-draft",
        safe_summary="Direct answer draft lane held a non-user-visible placeholder without model calls.",
    )


def _lane_result(
    lane_kind: TurnPreflightLaneKind,
    seed_decision: TurnDecision,
    *,
    candidate_turn_contract: TurnContractKind | str | None = None,
    answer_profile_hint: PromptProfilePolicy | None = None,
    reason_ref: str,
    signal_ref: str,
    safe_summary: str,
    memory_ref_candidates: list[str] | None = None,
    tool_category_refs: list[str] | None = None,
) -> TurnPreflightLaneResult:
    return TurnPreflightLaneResult(
        lane_result_ref=f"turn-preflight-lane:{lane_kind.value}",
        lane_kind=lane_kind,
        candidate_turn_contract=candidate_turn_contract or seed_decision.turn_contract,
        answer_profile_hint=answer_profile_hint,
        confidence=seed_decision.confidence,
        safe_summary=safe_summary,
        reason_refs=[reason_ref],
        source_refs=[f"source:turn-preflight:{lane_kind.value}"],
        evidence_refs=[f"evidence:turn-preflight:{lane_kind.value}"],
        signal_refs=[signal_ref],
        memory_ref_candidates=memory_ref_candidates or [],
        tool_category_refs=tool_category_refs or [],
        risk_flags=seed_decision.risk_flags,
    )


def _arbitrate_turn_decision(
    seed_decision: TurnDecision,
    lane_results: list[TurnPreflightLaneResult],
    *,
    decision_ref: str,
) -> TurnDecision:
    candidates = [
        result.candidate_turn_contract
        for result in lane_results
        if result.candidate_turn_contract is not None
    ]
    selected_contract = _highest_priority_contract([str(candidate) for candidate in candidates] or [seed_decision.turn_contract])
    risk_flags = _merge_risk_flags(seed_decision, lane_results)
    confidence = max([seed_decision.confidence, *[result.confidence for result in lane_results]], default=seed_decision.confidence)
    return TurnDecision(
        decision_ref=decision_ref,
        turn_contract=TurnContractKind(selected_contract),
        confidence=confidence,
        safe_summary="Parallel preflight arbitration selected a safe turn contract from lane refs.",
        reason_refs=[
            "reason-ref:turn-preflight:central-arbitration",
            *[ref for result in lane_results for ref in result.reason_refs],
        ],
        source_refs=["source:turn-preflight:central-arbitration"],
        evidence_refs=["evidence:turn-preflight:central-arbitration"],
        risk_flags=risk_flags,
    )


def _highest_priority_contract(candidates: list[str]) -> str:
    priority = (
        TurnContractKind.blocked_unsafe.value,
        TurnContractKind.approval_required.value,
        TurnContractKind.answer_with_reviewed_memory.value,
        TurnContractKind.prepare_tool_or_action.value,
        TurnContractKind.draft_or_plan.value,
        TurnContractKind.ask_clarifying_question.value,
        TurnContractKind.base_answer.value,
        TurnContractKind.answer_directly.value,
    )
    for contract in priority:
        if contract in candidates:
            return contract
    return TurnContractKind.answer_directly.value


def _merge_risk_flags(seed_decision: TurnDecision, lane_results: list[TurnPreflightLaneResult]) -> list[RiskFlag]:
    values: list[str] = []
    for value in [*seed_decision.risk_flags, *[flag for result in lane_results for flag in result.risk_flags]]:
        if value not in values:
            values.append(str(value))
    return [RiskFlag(value) for value in values if value in {flag.value for flag in RiskFlag}]


def _direct_answer_draft_cleared_for_display(
    decision: TurnDecision,
    lane_results: list[TurnPreflightLaneResult],
) -> bool:
    if decision.turn_contract not in {
        TurnContractKind.answer_directly.value,
        TurnContractKind.base_answer.value,
    }:
        return False
    if any(flag != RiskFlag.low_risk.value for flag in decision.risk_flags):
        return False
    return any(result.lane_kind == TurnPreflightLaneKind.direct_answer_draft.value for result in lane_results)


def _has_risk(seed_decision: TurnDecision, *risk_flags: RiskFlag) -> bool:
    return any(risk.value in seed_decision.risk_flags for risk in risk_flags)


def _tool_category_refs_for_contract(turn_contract: str) -> list[str]:
    if turn_contract == TurnContractKind.prepare_tool_or_action.value:
        return ["tool-category:turn-preflight:read-only-or-proposal"]
    if turn_contract == TurnContractKind.approval_required.value:
        return ["tool-category:turn-preflight:approval-envelope"]
    return []


def _answer_profile_for_contract(turn_contract: str) -> PromptProfilePolicy:
    mapping = {
        TurnContractKind.answer_directly.value: PromptProfilePolicy.minimal_answer,
        TurnContractKind.base_answer.value: PromptProfilePolicy.base_answer,
        TurnContractKind.answer_with_reviewed_memory.value: PromptProfilePolicy.memory_answer,
        TurnContractKind.draft_or_plan.value: PromptProfilePolicy.draft_or_plan,
        TurnContractKind.prepare_tool_or_action.value: PromptProfilePolicy.tool_or_action_prep,
        TurnContractKind.approval_required.value: PromptProfilePolicy.approval_boundary,
        TurnContractKind.ask_clarifying_question.value: PromptProfilePolicy.clarify,
        TurnContractKind.blocked_unsafe.value: PromptProfilePolicy.safe_refusal,
    }
    return mapping.get(turn_contract, PromptProfilePolicy.minimal_answer)


def _latency_bucket(duration_ms: float) -> str:
    if duration_ms < 25:
        return "under_25_ms"
    if duration_ms < 100:
        return "under_100_ms"
    return "over_100_ms"


def _safe_ref_suffix(value: str) -> str:
    return value.rsplit(":", 1)[-1]


def _validate_contract_ref(value: str) -> None:
    if value != TURN_PREFLIGHT_CONTRACT_REF:
        raise ValueError("unexpected turn preflight contract ref")
    validate_task_ref(value, "contract_ref")


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _validate_safe_preflight_summary(value: str, field_name: str) -> None:
    validate_safe_task_text(value, field_name)
    if any(pattern.search(value) for pattern in _RAW_TURN_TEXT_PATTERNS):
        raise ValueError(f"{field_name} must not include raw turn text")


def _validate_required_blocked_authorities(refs: list[str], owner: str) -> None:
    missing = set(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS) - set(refs)
    if missing:
        raise ValueError(f"{owner} missing required blocked authority ref: {sorted(missing)[0]}")


def _validate_no_authority(model: BaseModel, owner: str) -> None:
    if not getattr(model, "safe_refs_only"):
        raise ValueError(f"{owner} must be safe-ref only")
    if getattr(model, "raw_content_included"):
        raise ValueError(f"{owner} must not include raw content")
    if getattr(model, "authority_granted"):
        raise ValueError(f"{owner} must not grant authority")
    if getattr(model, "execution_permitted"):
        raise ValueError(f"{owner} must not permit execution")


def _validate_no_effect_flags(model: BaseModel, owner: str) -> None:
    failed = [field_name for field_name in _NO_EFFECT_FLAGS if not getattr(model, field_name)]
    if failed:
        raise ValueError(f"{owner} failed no-effect proof flag: {failed[0]}")


def _validate_required_lane_kinds(lane_results: list[TurnPreflightLaneResult]) -> None:
    seen: set[str] = set()
    for result in lane_results:
        lane_kind = str(result.lane_kind)
        if lane_kind in seen:
            raise ValueError(f"duplicate turn preflight lane kind: {lane_kind}")
        seen.add(lane_kind)
    missing = sorted(set(TURN_PREFLIGHT_REQUIRED_LANE_KINDS).difference(seen))
    if missing:
        raise ValueError(f"missing required turn preflight lane kind: {missing[0]}")
