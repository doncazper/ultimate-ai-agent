from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.chat import CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
from ultimate_ai_agent.core.code import GOVERNED_CODE_WORKBENCH_CONTRACT_REF
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.loop_binding import MEMORY_TO_LOOP_BINDING_CONTRACT_REF
from ultimate_ai_agent.core.planning.action_envelopes import (
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
)


USER_INTENT_UNDERSTANDING_CONTRACT_REF = (
    "contract-ref:user-intent-understanding:v1"
)

UserIntentSurface = Literal[
    "Today",
    "Memory Review",
    "Evidence Timeline",
    "Plans",
    "Actions",
    "Chat",
    "Governed Code",
]
UserIntentRoutingDecision = Literal["ask", "act", "defer"]
UserIntentConfidenceBand = Literal["high", "medium", "low", "conflicting"]
UserIntentAmbiguityPosture = Literal[
    "clear",
    "ambiguous_missing_scope",
    "ambiguous_conflicting_sources",
    "low_confidence",
    "stale_or_missing_evidence",
]

USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES: list[UserIntentSurface] = [
    "Today",
    "Memory Review",
    "Evidence Timeline",
    "Plans",
    "Actions",
    "Chat",
    "Governed Code",
]

USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS: list[UserIntentRoutingDecision] = [
    "ask",
    "act",
    "defer",
]

USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS = [
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    "contract-ref:evidence-history-grammar:v1",
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
]

USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "source_surface",
    "intent_label",
    "confidence_score",
    "confidence_band",
    "ambiguity_posture",
    "routing_decision",
    "source_refs",
    "evidence_refs",
    "dependency_refs",
    "required_contract_refs",
    "conflict_refs",
    "ask_user_question_ref",
    "next_safe_action",
]

USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-hidden-intent-authority",
    "blocked-state:low-confidence-must-ask-user",
    "blocked-state:conflicting-intent-must-ask-user",
    "blocked-state:no-action-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-tool-execution",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-code-apply-execution",
    "blocked-state:no-broad-autonomy",
    "blocked-state:no-public-beta",
    "blocked-state:no-production-authority",
]

_DENIED_FLAGS = [
    "hidden_authority_enabled",
    "acts_without_review",
    "action_execution_enabled",
    "approval_grant_capture_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "tool_execution_enabled",
    "provider_model_authority_allowed",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "code_apply_execution_enabled",
    "broad_autonomy_enabled",
    "public_beta_claim_enabled",
    "production_authority_enabled",
]


class UserIntentAuthorityPosture(BaseModel):
    review_required: bool = True
    safe_refs_only: bool = True
    evidence_required: bool = True
    low_confidence_asks_user: bool = True
    conflicting_intent_asks_user: bool = True
    hidden_authority_enabled: bool = False
    acts_without_review: bool = False
    action_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    tool_execution_enabled: bool = False
    provider_model_authority_allowed: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    broad_autonomy_enabled: bool = False
    public_beta_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_posture(self) -> "UserIntentAuthorityPosture":
        for field_name in (
            "review_required",
            "safe_refs_only",
            "evidence_required",
            "low_confidence_asks_user",
            "conflicting_intent_asks_user",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"authority posture must require {field_name}")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name) is not False:
                raise ValueError(f"authority posture must deny {field_name}")
        return self

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw source",
    "raw file",
    "raw_file",
    "raw log",
    "raw_log",
    "browser state",
    "shell history",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class ReviewableUserIntentProposal(BaseModel):
    contract_ref: str = USER_INTENT_UNDERSTANDING_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    source_surface: UserIntentSurface
    intent_label: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_band: UserIntentConfidenceBand
    ambiguity_posture: UserIntentAmbiguityPosture
    routing_decision: UserIntentRoutingDecision
    route_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    dependency_refs: list[str] = Field(default_factory=list, min_length=1)
    required_contract_refs: list[str] = Field(default_factory=list, min_length=1)
    conflict_refs: list[str] = Field(default_factory=list)
    ask_user_question_ref: str | None = None
    next_safe_action: str = Field(..., min_length=1, max_length=260)
    review_required: bool = True
    safe_refs_only: bool = True
    evidence_required: bool = True
    low_confidence_asks_user: bool = True
    conflicting_intent_asks_user: bool = True
    hidden_authority_enabled: bool = False
    acts_without_review: bool = False
    action_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    tool_execution_enabled: bool = False
    provider_model_authority_allowed: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    broad_autonomy_enabled: bool = False
    public_beta_claim_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "ReviewableUserIntentProposal":
        if self.contract_ref != USER_INTENT_UNDERSTANDING_CONTRACT_REF:
            raise ValueError("user intent understanding contract ref drifted")
        for field_name in ["contract_ref", "proposal_ref", "route_ref"]:
            _safe_ref(getattr(self, field_name), field_name)
        if self.ask_user_question_ref is not None:
            _safe_ref(self.ask_user_question_ref, "ask_user_question_ref")
        for field_name in [
            "source_refs",
            "evidence_refs",
            "dependency_refs",
            "required_contract_refs",
            "conflict_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "source_surface",
            "intent_label",
            "safe_summary",
            "confidence_band",
            "ambiguity_posture",
            "routing_decision",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        required_true = {
            "review_required": self.review_required,
            "safe_refs_only": self.safe_refs_only,
            "evidence_required": self.evidence_required,
            "low_confidence_asks_user": self.low_confidence_asks_user,
            "conflicting_intent_asks_user": self.conflicting_intent_asks_user,
        }
        disabled = [name for name, value in required_true.items() if not value]
        if disabled:
            raise ValueError(f"user intent proposal disabled {disabled[0]}")
        missing_dependencies = set(USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS) - set(
            self.dependency_refs
        )
        if missing_dependencies:
            raise ValueError("user intent proposal missing dependency refs")
        missing_blocked = set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("user intent proposal missing blocked refs")
        if self.confidence_band in {"low", "conflicting"} or self.confidence_score < 0.6:
            if self.routing_decision != "ask" or not self.ask_user_question_ref:
                raise ValueError("low or conflicting user intent must ask the user")
        expected_band: UserIntentConfidenceBand
        if self.ambiguity_posture == "ambiguous_conflicting_sources":
            expected_band = "conflicting"
        elif self.confidence_score >= 0.8:
            expected_band = "high"
        elif self.confidence_score >= 0.6:
            expected_band = "medium"
        else:
            expected_band = "low"
        if self.confidence_band != expected_band:
            raise ValueError("user intent confidence band does not match score or conflict")
        if self.ambiguity_posture == "ambiguous_conflicting_sources" and not self.conflict_refs:
            raise ValueError("conflicting user intent requires conflict refs")
        if self.ambiguity_posture == "ambiguous_conflicting_sources" and (
            self.routing_decision != "ask" or not self.ask_user_question_ref
        ):
            raise ValueError("conflicting user intent must ask the user")
        if self.routing_decision == "act" and self.confidence_score < 0.75:
            raise ValueError("act routing requires high confidence")
        if self.routing_decision == "act" and self.confidence_band != "high":
            raise ValueError("act routing requires the high confidence band")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by user intent understanding")
        return self


class UserIntentUnderstandingContract(BaseModel):
    contract_ref: str = USER_INTENT_UNDERSTANDING_CONTRACT_REF
    status: str = "implemented_reviewable_intent_proposals_authority_blocked"
    required_surfaces: list[UserIntentSurface] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES)
    )
    routing_decisions: list[UserIntentRoutingDecision] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS)
    )
    required_dependency_refs: list[str] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS)
    )
    required_ref_fields: list[str] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS)
    )
    proposals: list[ReviewableUserIntentProposal] = Field(
        default_factory=list, min_length=1
    )
    proposal_count: int
    surface_bindings: list[dict[str, str]]
    authority_posture: UserIntentAuthorityPosture
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS)
    )
    low_confidence_policy_ref: str = "policy-ref:user-intent:low-confidence-asks-user"
    conflict_policy_ref: str = "policy-ref:user-intent:conflict-asks-user"
    next_safe_action: str = (
        "Review intent proposals, ask the user when confidence is low or sources "
        "conflict, and route any action-shaped intent into reviewable envelopes only."
    )
    review_required: bool = True
    safe_refs_only: bool = True
    evidence_required: bool = True
    low_confidence_asks_user: bool = True
    conflicting_intent_asks_user: bool = True
    hidden_authority_enabled: bool = False
    acts_without_review: bool = False
    action_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    tool_execution_enabled: bool = False
    provider_model_authority_allowed: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    broad_autonomy_enabled: bool = False
    public_beta_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_contract(self) -> "UserIntentUnderstandingContract":
        if self.contract_ref != USER_INTENT_UNDERSTANDING_CONTRACT_REF:
            raise ValueError("user intent understanding contract ref drifted")
        _safe_ref(self.contract_ref, "contract_ref")
        _safe_refs(self.required_dependency_refs, "required_dependency_refs")
        _safe_refs(self.blocked_state_refs, "blocked_state_refs")
        _safe_ref(self.low_confidence_policy_ref, "low_confidence_policy_ref")
        _safe_ref(self.conflict_policy_ref, "conflict_policy_ref")
        _safe_text(self.status, "status")
        _safe_text(self.next_safe_action, "next_safe_action")
        if self.proposal_count != len(self.proposals):
            raise ValueError("user intent proposal count drifted")
        if set(self.required_surfaces) != set(USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES):
            raise ValueError("user intent required surfaces drifted")
        if set(self.routing_decisions) != set(USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS):
            raise ValueError("user intent routing decisions drifted")
        missing_blocked = set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("user intent contract missing blocked refs")
        required_true = {
            "review_required": self.review_required,
            "safe_refs_only": self.safe_refs_only,
            "evidence_required": self.evidence_required,
            "low_confidence_asks_user": self.low_confidence_asks_user,
            "conflicting_intent_asks_user": self.conflicting_intent_asks_user,
        }
        disabled = [name for name, value in required_true.items() if not value]
        if disabled:
            raise ValueError(f"user intent contract disabled {disabled[0]}")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by user intent understanding")
            if getattr(self.authority_posture, flag) is not False:
                raise ValueError(f"authority posture must deny {flag}")
        for field_name in required_true:
            if getattr(self.authority_posture, field_name) is not True:
                raise ValueError(f"authority posture must require {field_name}")
        return self


def build_user_intent_understanding_contract() -> UserIntentUnderstandingContract:
    proposals = [
        _proposal(
            proposal_ref="intent-proposal:today-founder-follow-up-priority",
            source_surface="Today",
            intent_label="prioritize_founder_follow_up",
            safe_summary=(
                "Today suggests a founder follow-up should be reviewed against "
                "memory commitments and evidence blockers."
            ),
            confidence_score=0.72,
            confidence_band="medium",
            ambiguity_posture="stale_or_missing_evidence",
            routing_decision="defer",
            route_ref="intent-route:defer-until-evidence-reviewed",
            source_refs=[
                "today-ref:founder-loop-summary",
                "follow-up-ref:actions:founder-action-memory-review-flow",
            ],
            evidence_refs=[
                "evidence-ref:founder-loop:today-summary",
                "evidence-ref:memory-to-loop-binding:review",
            ],
            conflict_refs=[],
            ask_user_question_ref=None,
            next_safe_action=(
                "Defer action until memory and evidence refs are reviewed in Today."
            ),
        ),
        _proposal(
            proposal_ref="intent-proposal:chat-handoff-needs-plan-scope",
            source_surface="Chat",
            intent_label="clarify_chat_to_plan_handoff",
            safe_summary=(
                "Chat handoff indicates a possible plan, but the exact scope is "
                "missing and should be clarified before any Action envelope."
            ),
            confidence_score=0.48,
            confidence_band="low",
            ambiguity_posture="ambiguous_missing_scope",
            routing_decision="ask",
            route_ref="intent-route:ask-user-clarifying-question",
            source_refs=[
                "chat-turn:local-operator:redacted-founder-loop",
                "handoff-ref:chat-to-plans:local-operator",
            ],
            evidence_refs=[
                "evidence-ref:chat-local-operator:route-runtime-auth-tool-denial",
                "evidence-ref:chat-local-operator:handoff",
            ],
            conflict_refs=[],
            ask_user_question_ref="question-ref:intent:chat-plan-scope",
            next_safe_action=(
                "Ask the user to confirm the intended plan scope before routing."
            ),
        ),
        _proposal(
            proposal_ref="intent-proposal:review-setup-hardening-envelope",
            source_surface="Actions",
            intent_label="review_existing_action_envelope",
            safe_summary=(
                "Action Inbox evidence supports reviewing an existing setup "
                "hardening envelope without granting execution."
            ),
            confidence_score=0.86,
            confidence_band="high",
            ambiguity_posture="clear",
            routing_decision="act",
            route_ref="intent-route:act-reviewable-envelope-only",
            source_refs=[
                "action-envelope:plans:founder-action-setup-assistant-hardening",
                "approval-envelope:founder-loop:setup-assistant-hardening",
            ],
            evidence_refs=[
                "evidence-ref:founder-loop:action-inbox",
                "receipt-plan:founder-loop:setup-assistant-hardening",
            ],
            conflict_refs=[],
            ask_user_question_ref=None,
            next_safe_action=(
                "Route to reviewable Action envelope metadata only; keep execution blocked."
            ),
        ),
        _proposal(
            proposal_ref="intent-proposal:crm-follow-up-conflict",
            source_surface="Memory Review",
            intent_label="resolve_conflicting_crm_follow_up",
            safe_summary=(
                "Memory review and CRM-lite follow-up refs disagree about the "
                "next relationship action, so the user must choose the intent."
            ),
            confidence_score=0.39,
            confidence_band="conflicting",
            ambiguity_posture="ambiguous_conflicting_sources",
            routing_decision="ask",
            route_ref="intent-route:ask-user-conflict-resolution",
            source_refs=[
                "memory-review:founder-loop-preferences",
                "crm-lite-ref:follow-up-candidate",
            ],
            evidence_refs=[
                "evidence-ref:memory-review:founder-loop-preferences",
                "evidence-ref:business-memory-quality:conflict-check",
            ],
            conflict_refs=[
                "conflict-ref:intent:crm-follow-up-next-action",
                "quality-ref:conflicting",
            ],
            ask_user_question_ref="question-ref:intent:crm-follow-up-conflict",
            next_safe_action=(
                "Ask the user to resolve the follow-up intent before creating any action."
            ),
        ),
    ]
    return UserIntentUnderstandingContract(
        proposals=proposals,
        proposal_count=len(proposals),
        surface_bindings=user_intent_understanding_surface_bindings(),
        authority_posture=user_intent_understanding_authority_posture(),
    )


def user_intent_understanding_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": f"user_intent_{_slug(surface)}_review_only",
            "feed_ref": f"user-intent-surface:{_slug(surface)}",
            "authority_boundary": (
                "Intent proposals are review-only safe refs; ask/act/defer "
                "routing does not grant execution, approval, memory, or tool authority."
            ),
        }
        for surface in USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES
    ]


def user_intent_understanding_authority_posture() -> dict[str, bool]:
    posture = {
        "review_required": True,
        "safe_refs_only": True,
        "evidence_required": True,
        "low_confidence_asks_user": True,
        "conflicting_intent_asks_user": True,
    }
    posture.update({flag: False for flag in _DENIED_FLAGS})
    return UserIntentAuthorityPosture(**posture).model_dump(mode="json")


def _proposal(
    *,
    proposal_ref: str,
    source_surface: UserIntentSurface,
    intent_label: str,
    safe_summary: str,
    confidence_score: float,
    confidence_band: UserIntentConfidenceBand,
    ambiguity_posture: UserIntentAmbiguityPosture,
    routing_decision: UserIntentRoutingDecision,
    route_ref: str,
    source_refs: list[str],
    evidence_refs: list[str],
    conflict_refs: list[str],
    ask_user_question_ref: str | None,
    next_safe_action: str,
) -> ReviewableUserIntentProposal:
    return ReviewableUserIntentProposal(
        proposal_ref=proposal_ref,
        source_surface=source_surface,
        intent_label=intent_label,
        safe_summary=safe_summary,
        confidence_score=confidence_score,
        confidence_band=confidence_band,
        ambiguity_posture=ambiguity_posture,
        routing_decision=routing_decision,
        route_ref=route_ref,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        dependency_refs=list(USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS),
        required_contract_refs=list(USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS),
        conflict_refs=conflict_refs,
        ask_user_question_ref=ask_user_question_ref,
        next_safe_action=next_safe_action,
    )


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _safe_text(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe content")


def _slug(value: str) -> str:
    return value.lower().replace("/", "-").replace(" ", "-")
