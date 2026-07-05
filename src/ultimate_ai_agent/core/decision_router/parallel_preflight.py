from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.turn_contracts import (
    PromptProfilePolicy,
    RiskFlag,
    TurnContractKind,
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


TURN_PREFLIGHT_CONTRACT_REF = "contract-ref:turn-contract-router:parallel-preflight:v1"
TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    *TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    "blocked-authority:no-preflight-authority-grant",
    "blocked-authority:no-preflight-user-visible-draft",
    "blocked-authority:no-parallel-lane-execution",
)


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
        _validate_unique_lane_kinds(self.lane_results)
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


def _validate_unique_lane_kinds(lane_results: list[TurnPreflightLaneResult]) -> None:
    seen: set[str] = set()
    for result in lane_results:
        lane_kind = str(result.lane_kind)
        if lane_kind in seen:
            raise ValueError(f"duplicate turn preflight lane kind: {lane_kind}")
        seen.add(lane_kind)
