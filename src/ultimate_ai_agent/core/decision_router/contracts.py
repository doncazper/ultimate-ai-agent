from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


DECISION_ROUTER_CONTRACT_REF = "contract-ref:top-level-decision-router:v1"
DECISION_ROUTER_POLICY_REF = "policy-ref:top-level-decision-router:no-effect:v1"
DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:no-runtime-model-call",
    "blocked-authority:no-provider-call",
    "blocked-authority:no-tool-execution",
    "blocked-authority:no-action-execution",
    "blocked-authority:no-workflow-execution",
    "blocked-authority:no-memory-write",
    "blocked-authority:no-context-injection",
    "blocked-authority:no-shell-subprocess",
    "blocked-authority:no-browser-network",
    "blocked-authority:no-connector-write",
)


class DecisionRouterOutcomeKind(str, Enum):
    answer_directly = "answer_directly"
    use_reviewed_memory = "use_reviewed_memory"
    propose_action_inbox_item = "propose_action_inbox_item"
    ask_human = "ask_human"
    escalate_to_review = "escalate_to_review"
    defer = "defer"
    blocked_unsafe = "blocked_unsafe"
    insufficient_evidence = "insufficient_evidence"


DECISION_ROUTER_REQUIRED_OUTCOME_KINDS = tuple(item.value for item in DecisionRouterOutcomeKind)


class DecisionRouterAmbiguityPosture(str, Enum):
    clear = "clear"
    low_ambiguity = "low_ambiguity"
    ambiguous = "ambiguous"
    conflicting = "conflicting"
    insufficient_evidence = "insufficient_evidence"
    unsafe_blocked = "unsafe_blocked"


_OUTCOME_PRIORITY = {
    DecisionRouterOutcomeKind.answer_directly.value: 0,
    DecisionRouterOutcomeKind.use_reviewed_memory.value: 1,
    DecisionRouterOutcomeKind.propose_action_inbox_item.value: 2,
    DecisionRouterOutcomeKind.ask_human.value: 3,
    DecisionRouterOutcomeKind.escalate_to_review.value: 4,
    DecisionRouterOutcomeKind.defer.value: 5,
    DecisionRouterOutcomeKind.insufficient_evidence.value: 6,
    DecisionRouterOutcomeKind.blocked_unsafe.value: 7,
}
_DENIED_FLAG_FIELDS = (
    "runtime_model_call_allowed",
    "provider_call_allowed",
    "tool_execution_allowed",
    "action_execution_allowed",
    "workflow_execution_allowed",
    "memory_write_allowed",
    "context_injection_allowed",
    "shell_subprocess_allowed",
    "browser_network_allowed",
    "connector_write_allowed",
)
_BLOCKED_AUTHORITY_SOURCE_PREFIXES = (
    "model:",
    "runtime:",
    "openwebui:",
    "context-pack:",
)
_NO_EFFECT_FLAG_FIELDS = (
    "route_authority_granted",
    "execution_performed",
)
_REQUIRED_TRUE_NO_EFFECT_FIELDS = (
    "no_model_call_performed",
    "no_provider_call_performed",
    "no_tool_execution_performed",
    "no_action_execution_performed",
    "no_workflow_execution_performed",
    "no_memory_write_performed",
    "no_context_injection_performed",
    "no_shell_subprocess_performed",
    "no_browser_network_performed",
    "no_connector_write_performed",
)


class DecisionRouterBlockedState(BaseModel):
    blocked_state_ref: str = Field(..., min_length=1)
    reason_ref: str = Field(..., min_length=1)
    blocked_authority_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=400)
    evidence_refs: list[str] = Field(default_factory=list)
    next_safe_operator_action: str = Field(..., min_length=1, max_length=240)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_blocked_state(self) -> "DecisionRouterBlockedState":
        for field_name in ("blocked_state_ref", "reason_ref", "blocked_authority_ref"):
            validate_task_ref(getattr(self, field_name), field_name)
        for ref in self.evidence_refs:
            validate_task_ref(ref, "evidence_refs")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.next_safe_operator_action, "next_safe_operator_action")
        return self


class DecisionRouterCandidate(BaseModel):
    candidate_ref: str = Field(..., min_length=1)
    outcome_kind: DecisionRouterOutcomeKind
    safe_summary: str = Field(..., min_length=1, max_length=500)
    safe_reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    ambiguity_posture: DecisionRouterAmbiguityPosture = DecisionRouterAmbiguityPosture.clear
    next_safe_operator_action: str = Field(..., min_length=1, max_length=240)
    downstream_proposal_refs: list[str] = Field(default_factory=list)
    module_refs: list[str] = Field(default_factory=list)
    operator_surface_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    route_authority_granted: bool = False
    execution_performed: bool = False
    no_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_context_injection_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_candidate(self) -> "DecisionRouterCandidate":
        validate_task_ref(self.candidate_ref, "candidate_ref")
        _validate_ref_list(self.safe_reason_refs, "safe_reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.downstream_proposal_refs, "downstream_proposal_refs")
        _validate_ref_list(self.module_refs, "module_refs")
        _validate_ref_list(self.operator_surface_refs, "operator_surface_refs")
        _validate_ref_list(self.metadata_refs, "metadata_refs")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.next_safe_operator_action, "next_safe_operator_action")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "candidate")
        _validate_source_refs_are_not_authority(self.source_refs, "candidate.source_refs")
        _validate_no_effect_flags(self, "candidate")
        if self.outcome_kind == DecisionRouterOutcomeKind.propose_action_inbox_item.value and not self.downstream_proposal_refs:
            raise ValueError("propose_action_inbox_item candidates must include downstream_proposal_refs")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class DecisionRouterTrace(BaseModel):
    trace_ref: str = Field(..., min_length=1)
    router_input_ref: str = Field(..., min_length=1)
    candidate_refs: list[str] = Field(default_factory=list)
    selected_candidate_ref: str | None = None
    excluded_candidate_refs: list[str] = Field(default_factory=list)
    safe_reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    deterministic_policy_ref: str = DECISION_ROUTER_POLICY_REF
    no_effect: bool = True
    no_runtime_model_call: bool = True
    no_tool_execution: bool = True
    no_memory_write: bool = True
    no_context_injection: bool = True
    no_action_execution: bool = True
    no_workflow_execution: bool = True
    route_authority_granted: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_trace(self) -> "DecisionRouterTrace":
        validate_task_ref(self.trace_ref, "trace_ref")
        validate_task_ref(self.router_input_ref, "router_input_ref")
        if self.selected_candidate_ref is not None:
            validate_task_ref(self.selected_candidate_ref, "selected_candidate_ref")
        _validate_ref_list(self.candidate_refs, "candidate_refs")
        _validate_ref_list(self.excluded_candidate_refs, "excluded_candidate_refs")
        _validate_ref_list(self.safe_reason_refs, "safe_reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        validate_task_ref(self.deterministic_policy_ref, "deterministic_policy_ref")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "trace")
        if not all(
            (
                self.no_effect,
                self.no_runtime_model_call,
                self.no_tool_execution,
                self.no_memory_write,
                self.no_context_injection,
                self.no_action_execution,
                self.no_workflow_execution,
            )
        ):
            raise ValueError("decision router trace must remain no-effect")
        _validate_no_effect_flags(self, "trace")
        return self


class DecisionRouterInput(BaseModel):
    contract_ref: str = DECISION_ROUTER_CONTRACT_REF
    router_input_ref: str = Field(..., min_length=1)
    safe_request_summary: str = Field(..., min_length=1, max_length=500)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    memory_read_model_refs: list[str] = Field(default_factory=list)
    plan_refs: list[str] = Field(default_factory=list)
    action_inbox_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    tool_decision_refs: list[str] = Field(default_factory=list)
    human_review_refs: list[str] = Field(default_factory=list)
    evidence_timeline_refs: list[str] = Field(default_factory=list)
    candidates: list[DecisionRouterCandidate] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    runtime_model_call_allowed: bool = False
    provider_call_allowed: bool = False
    tool_execution_allowed: bool = False
    action_execution_allowed: bool = False
    workflow_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    shell_subprocess_allowed: bool = False
    browser_network_allowed: bool = False
    connector_write_allowed: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_input(self) -> "DecisionRouterInput":
        if self.contract_ref != DECISION_ROUTER_CONTRACT_REF:
            raise ValueError("unexpected decision router contract ref")
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.router_input_ref, "router_input_ref")
        validate_safe_task_text(self.safe_request_summary, "safe_request_summary")
        for field_name in (
            "source_refs",
            "evidence_refs",
            "memory_read_model_refs",
            "plan_refs",
            "action_inbox_refs",
            "approval_refs",
            "tool_decision_refs",
            "human_review_refs",
            "evidence_timeline_refs",
            "blocked_authority_refs",
            "metadata_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_required_blocked_authorities(self.blocked_authority_refs, "input")
        _validate_source_refs_are_not_authority(self.source_refs, "input.source_refs")
        _validate_denied_flags(self, "input")
        if not self.safe_refs_only:
            raise ValueError("decision router input must be safe-ref only")
        if self.raw_content_included:
            raise ValueError("decision router input must not include raw content")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class DecisionRouterOutcome(BaseModel):
    contract_ref: str = DECISION_ROUTER_CONTRACT_REF
    outcome_ref: str = Field(..., min_length=1)
    router_input_ref: str = Field(..., min_length=1)
    outcome_kind: DecisionRouterOutcomeKind
    selected_candidate_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=500)
    safe_reason_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    ambiguity_posture: DecisionRouterAmbiguityPosture = DecisionRouterAmbiguityPosture.clear
    next_safe_operator_action: str = Field(..., min_length=1, max_length=240)
    downstream_proposal_refs: list[str] = Field(default_factory=list)
    blocked_states: list[DecisionRouterBlockedState] = Field(default_factory=list)
    trace: DecisionRouterTrace
    runtime_model_call_allowed: bool = False
    provider_call_allowed: bool = False
    tool_execution_allowed: bool = False
    action_execution_allowed: bool = False
    workflow_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    shell_subprocess_allowed: bool = False
    browser_network_allowed: bool = False
    connector_write_allowed: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False
    route_authority_granted: bool = False
    execution_performed: bool = False
    no_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_context_injection_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_outcome(self) -> "DecisionRouterOutcome":
        if self.contract_ref != DECISION_ROUTER_CONTRACT_REF:
            raise ValueError("unexpected decision router contract ref")
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.outcome_ref, "outcome_ref")
        validate_task_ref(self.router_input_ref, "router_input_ref")
        if self.selected_candidate_ref is not None:
            validate_task_ref(self.selected_candidate_ref, "selected_candidate_ref")
        _validate_ref_list(self.safe_reason_refs, "safe_reason_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.downstream_proposal_refs, "downstream_proposal_refs")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.next_safe_operator_action, "next_safe_operator_action")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "outcome")
        _validate_source_refs_are_not_authority(self.source_refs, "outcome.source_refs")
        _validate_denied_flags(self, "outcome")
        _validate_no_effect_flags(self, "outcome")
        if not self.safe_refs_only:
            raise ValueError("decision router outcome must be safe-ref only")
        if self.raw_content_included:
            raise ValueError("decision router outcome must not include raw content")
        if self.outcome_kind == DecisionRouterOutcomeKind.propose_action_inbox_item.value and not self.downstream_proposal_refs:
            raise ValueError("propose_action_inbox_item outcomes must include downstream_proposal_refs")
        if self.outcome_kind in {
            DecisionRouterOutcomeKind.blocked_unsafe.value,
            DecisionRouterOutcomeKind.insufficient_evidence.value,
        } and not self.blocked_states:
            raise ValueError("blocked or insufficient-evidence outcomes must include blocked_states")
        return self


def route_decision(router_input: DecisionRouterInput) -> DecisionRouterOutcome:
    parsed = router_input if isinstance(router_input, DecisionRouterInput) else DecisionRouterInput(**router_input)
    if not parsed.candidates:
        return _insufficient_evidence_outcome(parsed)
    selected = _select_candidate(parsed.candidates)
    excluded = [candidate.candidate_ref for candidate in parsed.candidates if candidate.candidate_ref != selected.candidate_ref]
    blocked_states = _blocked_states_for_candidate(selected)
    trace = DecisionRouterTrace(
        trace_ref=f"decision-router-trace:{_safe_suffix(parsed.router_input_ref)}",
        router_input_ref=parsed.router_input_ref,
        candidate_refs=[candidate.candidate_ref for candidate in parsed.candidates],
        selected_candidate_ref=selected.candidate_ref,
        excluded_candidate_refs=excluded,
        safe_reason_refs=selected.safe_reason_refs,
        evidence_refs=_dedupe([*parsed.evidence_refs, *selected.evidence_refs]),
        source_refs=_dedupe([*parsed.source_refs, *selected.source_refs]),
        blocked_authority_refs=_dedupe([*parsed.blocked_authority_refs, *selected.blocked_authority_refs]),
    )
    return DecisionRouterOutcome(
        outcome_ref=f"decision-router-outcome:{_safe_suffix(selected.candidate_ref)}",
        router_input_ref=parsed.router_input_ref,
        outcome_kind=selected.outcome_kind,
        selected_candidate_ref=selected.candidate_ref,
        safe_summary=selected.safe_summary,
        safe_reason_refs=selected.safe_reason_refs,
        evidence_refs=trace.evidence_refs,
        source_refs=trace.source_refs,
        blocked_authority_refs=trace.blocked_authority_refs,
        confidence=selected.confidence,
        ambiguity_posture=selected.ambiguity_posture,
        next_safe_operator_action=selected.next_safe_operator_action,
        downstream_proposal_refs=selected.downstream_proposal_refs,
        blocked_states=blocked_states,
        trace=trace,
    )


def _select_candidate(candidates: list[DecisionRouterCandidate]) -> DecisionRouterCandidate:
    blocked = [
        candidate
        for candidate in candidates
        if candidate.outcome_kind == DecisionRouterOutcomeKind.blocked_unsafe.value
    ]
    if blocked:
        return sorted(blocked, key=lambda item: (-item.confidence, item.candidate_ref))[0]
    return sorted(candidates, key=lambda item: (-item.confidence, _OUTCOME_PRIORITY[str(item.outcome_kind)], item.candidate_ref))[0]


def _insufficient_evidence_outcome(router_input: DecisionRouterInput) -> DecisionRouterOutcome:
    blocked_state = DecisionRouterBlockedState(
        blocked_state_ref=f"blocked-state:decision-router:{_safe_suffix(router_input.router_input_ref)}:insufficient-evidence",
        reason_ref="reason-ref:decision-router:insufficient-evidence",
        blocked_authority_ref="blocked-authority:no-insufficient-evidence-routing",
        safe_summary="No eligible decision candidates were available from bounded safe refs.",
        evidence_refs=router_input.evidence_refs,
        next_safe_operator_action="Provide reviewed source, evidence, memory, plan, approval, or action proposal refs.",
    )
    trace = DecisionRouterTrace(
        trace_ref=f"decision-router-trace:{_safe_suffix(router_input.router_input_ref)}",
        router_input_ref=router_input.router_input_ref,
        candidate_refs=[],
        selected_candidate_ref=None,
        excluded_candidate_refs=[],
        safe_reason_refs=["reason-ref:decision-router:insufficient-evidence"],
        evidence_refs=router_input.evidence_refs,
        source_refs=router_input.source_refs,
        blocked_authority_refs=router_input.blocked_authority_refs,
    )
    return DecisionRouterOutcome(
        outcome_ref=f"decision-router-outcome:{_safe_suffix(router_input.router_input_ref)}:insufficient-evidence",
        router_input_ref=router_input.router_input_ref,
        outcome_kind=DecisionRouterOutcomeKind.insufficient_evidence,
        safe_summary="Decision router could not select a path from the provided safe refs.",
        safe_reason_refs=["reason-ref:decision-router:insufficient-evidence"],
        evidence_refs=router_input.evidence_refs,
        source_refs=router_input.source_refs,
        blocked_authority_refs=router_input.blocked_authority_refs,
        confidence=0.0,
        ambiguity_posture=DecisionRouterAmbiguityPosture.insufficient_evidence,
        next_safe_operator_action="Add reviewed evidence or ask a human to clarify the requested path.",
        blocked_states=[blocked_state],
        trace=trace,
    )


def _blocked_states_for_candidate(candidate: DecisionRouterCandidate) -> list[DecisionRouterBlockedState]:
    if candidate.outcome_kind == DecisionRouterOutcomeKind.blocked_unsafe.value:
        return [
            DecisionRouterBlockedState(
                blocked_state_ref=f"blocked-state:decision-router:{_safe_suffix(candidate.candidate_ref)}:unsafe",
                reason_ref=candidate.safe_reason_refs[0],
                blocked_authority_ref="blocked-authority:no-unsafe-routing",
                safe_summary="The selected decision candidate is blocked as unsafe.",
                evidence_refs=candidate.evidence_refs,
                next_safe_operator_action=candidate.next_safe_operator_action,
            )
        ]
    if candidate.outcome_kind == DecisionRouterOutcomeKind.insufficient_evidence.value:
        return [
            DecisionRouterBlockedState(
                blocked_state_ref=f"blocked-state:decision-router:{_safe_suffix(candidate.candidate_ref)}:insufficient-evidence",
                reason_ref=candidate.safe_reason_refs[0],
                blocked_authority_ref="blocked-authority:no-insufficient-evidence-routing",
                safe_summary="The selected decision candidate needs more reviewed evidence.",
                evidence_refs=candidate.evidence_refs,
                next_safe_operator_action=candidate.next_safe_operator_action,
            )
        ]
    return []


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _validate_required_blocked_authorities(refs: list[str], owner: str) -> None:
    missing = set(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS) - set(refs)
    if missing:
        raise ValueError(f"{owner} missing required blocked authority ref: {sorted(missing)[0]}")


def _validate_denied_flags(model: Any, owner: str) -> None:
    enabled = [field_name for field_name in _DENIED_FLAG_FIELDS if getattr(model, field_name)]
    if enabled:
        raise ValueError(f"{owner} enabled denied authority: {enabled[0]}")


def _validate_no_effect_flags(model: Any, owner: str) -> None:
    false_required = [field_name for field_name in _NO_EFFECT_FLAG_FIELDS if getattr(model, field_name)]
    if false_required:
        raise ValueError(f"{owner} granted denied route authority: {false_required[0]}")
    true_required = [field_name for field_name in _REQUIRED_TRUE_NO_EFFECT_FIELDS if not getattr(model, field_name, True)]
    if true_required:
        raise ValueError(f"{owner} failed no-effect proof flag: {true_required[0]}")


def _validate_source_refs_are_not_authority(refs: list[str], field_name: str) -> None:
    blocked = [
        ref
        for ref in refs
        if ref.lower().startswith(_BLOCKED_AUTHORITY_SOURCE_PREFIXES)
    ]
    if blocked:
        raise ValueError(f"{field_name} contains non-authoritative source ref: {blocked[0]}")


def _safe_suffix(value: str) -> str:
    return value.split(":", 1)[-1].replace("/", "-").replace(":", "-")


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
