from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.model_router.decisions import ModelRouteDecision


FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF = (
    "contract-ref:fcc-fusion-routing-delegation:v1"
)
FCC_FUSION_ROUTING_READ_MODEL_SOURCE = (
    "python_core_fusion_routing_delegation_read_model"
)
FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:fusion-no-model-provider-call",
    "blocked-state:fusion-no-sidekick-execution",
    "blocked-state:fusion-no-action-execution",
    "blocked-state:fusion-no-tool-execution",
    "blocked-state:fusion-no-background-work",
    "blocked-state:fusion-no-shell-subprocess-execution",
    "blocked-state:fusion-no-browser-automation",
    "blocked-state:fusion-no-connector-write",
    "blocked-state:fusion-no-memory-write",
    "blocked-state:fusion-no-context-injection",
    "blocked-state:fusion-no-production-authority",
)
FCC_FUSION_ROUTING_SURFACES: tuple[str, ...] = (
    "Today",
    "Plans",
    "Actions",
    "Chat",
    "Evidence",
    "Code",
)

_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_.@-]+")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw context",
    "raw_context",
    "raw transcript",
    "raw_transcript",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "username",
    "host name",
    "hostname",
    "environment dump",
    "env dump",
    "credential",
    "secret",
    "bearer",
    "token",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/private/",
    "/tmp/",
    "/var/",
    "/etc/",
    "\\users\\",
    "\\appdata\\",
    ":\\",
)
_FORBIDDEN_PRODUCT_CLAIMS = (
    "sidekick execution implemented",
    "autonomous worker lane active",
    "model switching performed",
    "provider/model calls enabled",
    "provider model calls enabled",
    "action execution authorized by classification",
    "delegation proposal executed",
    "cache-aware runtime routing active",
    "production-ready routing",
    "public beta from this lane",
    "public release from this lane",
)


class WorkClassificationValue(str, Enum):
    judgment_required = "judgment_required"
    mechanical = "mechanical"
    validation = "validation"
    bookkeeping = "bookkeeping"
    ambiguous = "ambiguous"
    blocked = "blocked"


class ConfidencePosture(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"


class AmbiguityPosture(str, Enum):
    clear = "clear"
    some_ambiguity = "some_ambiguity"
    ambiguous = "ambiguous"
    blocked = "blocked"


class DelegationProposalState(str, Enum):
    proposed = "proposed"
    rejected = "rejected"
    deferred = "deferred"
    blocked = "blocked"
    future_only = "future_only"


class ProposedDelegateKind(str, Enum):
    none = "none"
    mechanical_worker = "mechanical_worker"
    validation_worker = "validation_worker"
    bookkeeping_worker = "bookkeeping_worker"


class RouteVisibilityStatus(str, Enum):
    selected = "selected"
    rejected = "rejected"
    blocked = "blocked"


class CacheReusePosture(str, Enum):
    none = "none"
    possible = "possible"
    expected = "expected"
    blocked = "blocked"


class RerouteReason(str, Enum):
    none = "none"
    privacy_blocked = "privacy_blocked"
    cost_blocked = "cost_blocked"
    context_too_small = "context_too_small"
    approval_required = "approval_required"
    unavailable_runtime = "unavailable_runtime"
    disabled_profile = "disabled_profile"
    validation_required = "validation_required"


class DogfoodOutcome(str, Enum):
    useful = "useful"
    not_useful = "not_useful"
    confusing = "confusing"
    wrong = "wrong"
    partially_useful = "partially_useful"
    blocked = "blocked"
    skipped = "skipped"
    needs_follow_up = "needs_follow_up"


class WorkClassification(BaseModel):
    schema_version: str = "fcc_fusion_work_classification.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    classification: WorkClassificationValue
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    confidence_posture: ConfidencePosture = ConfidencePosture.unknown
    ambiguity_posture: AmbiguityPosture = AmbiguityPosture.clear
    human_review_required: bool = True
    blocked_authority_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    reviewed_at_ref: str = "review-state:not-reviewed"
    expiry_posture_ref: str = "expiry-posture:review-before-use"
    review_aid_only: bool = True
    execution_authorized: bool = False
    action_execution_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_classification(self) -> "WorkClassification":
        _validate_safe_payload(self.model_dump(mode="json"), "work_classification")
        if self.classification in {
            WorkClassificationValue.judgment_required,
            WorkClassificationValue.ambiguous,
        }:
            if not self.human_review_required:
                raise ValueError("judgment or ambiguous work requires human review")
            if self.ambiguity_posture == AmbiguityPosture.clear:
                raise ValueError("judgment or ambiguous work must expose ambiguity posture")
        if self.classification == WorkClassificationValue.blocked:
            if not self.blocked_authority_refs:
                raise ValueError("blocked work requires blocked authority refs")
            if not self.human_review_required:
                raise ValueError("blocked work requires human review")
        if not self.review_aid_only:
            raise ValueError("classification must remain review aid only")
        if self.execution_authorized or self.action_execution_enabled:
            raise ValueError("classification cannot authorize execution")
        return self


class RouteDecisionVisibility(BaseModel):
    schema_version: str = "fcc_fusion_route_decision_visibility.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    status: RouteVisibilityStatus
    selected_profile_ref: str = "model-profile-ref:none-selected"
    rejected_profile_refs: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list, min_length=1)
    privacy_posture_ref: str = "privacy-posture:metadata-only"
    cost_posture_ref: str = "cost-posture:not-invoked"
    latency_posture_ref: str = "latency-posture:not-measured"
    context_posture_ref: str = "context-posture:not-expanded"
    approval_posture_ref: str = "approval-posture:not-authority"
    operator_summary: str = Field(..., min_length=1, max_length=500)
    no_execution_performed: bool = True
    model_invocation_performed: bool = False
    provider_call_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_visibility(self) -> "RouteDecisionVisibility":
        _validate_safe_payload(self.model_dump(mode="json"), "route_visibility")
        if not self.no_execution_performed:
            raise ValueError("route visibility must prove no execution")
        if self.model_invocation_performed or self.provider_call_performed:
            raise ValueError("route visibility cannot record provider/model calls")
        if self.status == RouteVisibilityStatus.selected and not self.selected_profile_ref:
            raise ValueError("selected route visibility requires selected profile ref")
        return self


class CacheContextEconomics(BaseModel):
    schema_version: str = "fcc_fusion_cache_context_economics.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    context_budget_ref: str = "context-budget-ref:not-expanded"
    compaction_boundary_ref: str = "compaction-boundary-ref:not-executed"
    cache_miss_expected: bool = False
    cache_reuse_posture: CacheReusePosture = CacheReusePosture.none
    reroute_reason: RerouteReason = RerouteReason.none
    estimated_context_cost_posture: str = "context-cost-posture:not-measured"
    cache_or_context_blocker_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explanatory_posture_only: bool = True
    measured_provider_event: bool = False
    runtime_model_switch_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_economics(self) -> "CacheContextEconomics":
        _validate_safe_payload(self.model_dump(mode="json"), "cache_context_economics")
        if not self.explanatory_posture_only:
            raise ValueError("cache/context economics must remain explanatory posture")
        if self.measured_provider_event and not self.evidence_refs:
            raise ValueError("measured cache/provider event requires evidence refs")
        if self.runtime_model_switch_performed:
            raise ValueError("runtime model switching is not scoped")
        return self


class DelegationProposalEnvelope(BaseModel):
    schema_version: str = "fcc_fusion_delegation_proposal.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    proposal_state: DelegationProposalState
    proposed_delegate_kind: ProposedDelegateKind = ProposedDelegateKind.none
    delegate_scope_ref: str = "delegate-scope-ref:none"
    main_owner_responsibility_refs: list[str] = Field(default_factory=list, min_length=1)
    delegated_work_refs: list[str] = Field(default_factory=list)
    review_required_posture_ref: str = "review-required:main-owner-final-review"
    blocked_execution_refs: list[str] = Field(default_factory=list, min_length=1)
    expected_receipt_refs: list[str] = Field(default_factory=list, min_length=1)
    rollback_safe_disable_posture_refs: list[str] = Field(default_factory=list, min_length=1)
    work_classification: WorkClassification
    future_only: bool = True
    creates_approval_ref: bool = False
    creates_execution_ref: bool = False
    worker_execution_enabled: bool = False
    background_dispatch_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_delegation(self) -> "DelegationProposalEnvelope":
        _validate_safe_payload(self.model_dump(mode="json"), "delegation_proposal")
        if not self.future_only:
            raise ValueError("delegation proposals must remain future-only")
        if (
            self.creates_approval_ref
            or self.creates_execution_ref
            or self.worker_execution_enabled
            or self.background_dispatch_enabled
        ):
            raise ValueError("delegation proposal cannot create authority or execute")
        if self.work_classification.classification in {
            WorkClassificationValue.judgment_required,
            WorkClassificationValue.ambiguous,
        }:
            if self.proposal_state == DelegationProposalState.proposed:
                raise ValueError("judgment or ambiguous work cannot be delegate-ready")
            if not self.work_classification.human_review_required:
                raise ValueError("judgment or ambiguous delegation requires review")
        if self.proposal_state == DelegationProposalState.proposed:
            if self.proposed_delegate_kind == ProposedDelegateKind.none:
                raise ValueError("proposed delegation requires delegate kind")
            if not self.delegated_work_refs:
                raise ValueError("proposed delegation requires delegated work refs")
        return self


class FusionDogfoodEvidenceRecord(BaseModel):
    schema_version: str = "fcc_fusion_dogfood_evidence.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    review_record_ref: str = Field(..., min_length=1)
    outcome: DogfoodOutcome
    friction_delta_ref: str = "dogfood-delta-ref:not-measured"
    review_time_delta_ref: str = "dogfood-delta-ref:not-measured"
    cost_confusion_delta_ref: str = "dogfood-delta-ref:not-measured"
    routing_cost_delta_ref: str = "dogfood-delta-ref:not-measured"
    ambiguity_delta_ref: str = "dogfood-delta-ref:not-measured"
    interruption_delta_ref: str = "dogfood-delta-ref:not-measured"
    redacted_summary_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    local_private_only: bool = True
    external_analytics_enabled: bool = False
    live_learning_claimed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "FusionDogfoodEvidenceRecord":
        _validate_safe_payload(self.model_dump(mode="json"), "fusion_dogfood_record")
        if not self.local_private_only:
            raise ValueError("dogfood evidence must stay local/private")
        if self.external_analytics_enabled or self.live_learning_claimed:
            raise ValueError("dogfood evidence cannot enable analytics or learning claims")
        return self


class FusionRoutingDelegationReadModel(BaseModel):
    schema_version: str = "fcc_fusion_routing_delegation.v1"
    contract_ref: str = FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    source: str = FCC_FUSION_ROUTING_READ_MODEL_SOURCE
    status: str = "implemented_backend_owned_readability_metadata_no_execution"
    backend_owned: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    surfaces: list[str] = Field(default_factory=lambda: list(FCC_FUSION_ROUTING_SURFACES))
    work_classifications: list[WorkClassification] = Field(default_factory=list, min_length=1)
    route_decisions: list[RouteDecisionVisibility] = Field(default_factory=list, min_length=1)
    delegation_proposals: list[DelegationProposalEnvelope] = Field(default_factory=list, min_length=1)
    cache_context_economics: list[CacheContextEconomics] = Field(default_factory=list, min_length=1)
    dogfood_records: list[FusionDogfoodEvidenceRecord] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=lambda: list(FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS))
    next_safe_action: str = (
        "Use classification, route, delegation, and context/cost fields as review aids only."
    )
    authority_boundary: str = (
        "Fusion routing and delegation metadata improves review readability; it does not "
        "authorize sidekick execution, action execution, provider/model calls, memory writes, "
        "context injection, browser/shell work, connector writes, background dispatch, or "
        "production authority."
    )
    action_execution_enabled: bool = False
    sidekick_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    connector_write_enabled: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    background_dispatch_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "FusionRoutingDelegationReadModel":
        _validate_safe_payload(self.model_dump(mode="json"), "fusion_read_model")
        if self.source != FCC_FUSION_ROUTING_READ_MODEL_SOURCE:
            raise ValueError("unexpected fusion read-model source")
        if not self.backend_owned or not self.safe_refs_only or self.raw_content_included:
            raise ValueError("fusion read model must stay backend-owned safe refs only")
        missing = set(FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing:
            raise ValueError("fusion read model missing blocked refs")
        denied = [
            "action_execution_enabled",
            "sidekick_execution_enabled",
            "provider_model_call_enabled",
            "shell_subprocess_execution_enabled",
            "browser_execution_enabled",
            "connector_write_enabled",
            "memory_write_authorized",
            "context_injection_authorized",
            "background_dispatch_enabled",
            "production_authority_enabled",
        ]
        for field_name in denied:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        return self


def build_work_classification(
    classification: WorkClassificationValue | str,
    *,
    suffix_ref: str,
    source_ref: str,
    evidence_ref: str,
    reason_ref: str | None = None,
    blocked_authority_refs: list[str] | None = None,
    confidence_posture: ConfidencePosture = ConfidencePosture.medium,
    ambiguity_posture: AmbiguityPosture | None = None,
) -> WorkClassification:
    value = WorkClassificationValue(classification)
    suffix = _safe_suffix(suffix_ref)
    blocked_refs = list(blocked_authority_refs or [])
    if value == WorkClassificationValue.blocked and not blocked_refs:
        blocked_refs = ["blocked-state:fusion-classification-missing-authority"]
    if ambiguity_posture is None:
        ambiguity_posture = (
            AmbiguityPosture.ambiguous
            if value in {
                WorkClassificationValue.judgment_required,
                WorkClassificationValue.ambiguous,
            }
            else AmbiguityPosture.blocked
            if value == WorkClassificationValue.blocked
            else AmbiguityPosture.clear
        )
    return WorkClassification(
        classification=value,
        reason_refs=[reason_ref or f"classification-reason-ref:fusion:{suffix}"],
        confidence_posture=confidence_posture,
        ambiguity_posture=ambiguity_posture,
        human_review_required=value
        in {
            WorkClassificationValue.judgment_required,
            WorkClassificationValue.ambiguous,
            WorkClassificationValue.blocked,
        },
        blocked_authority_refs=blocked_refs,
        source_refs=[source_ref],
        evidence_refs=[evidence_ref],
        reviewed_at_ref="review-state:not-reviewed",
        expiry_posture_ref=f"expiry-posture:fusion:{suffix}:review-before-use",
    )


def build_route_visibility_from_decision(
    decision: ModelRouteDecision,
) -> RouteDecisionVisibility:
    rejected = [f"model-profile-ref:{_safe_suffix(ref)}" for ref in decision.rejected_profile_ids]
    selected = (
        f"model-profile-ref:{_safe_suffix(decision.selected_profile_id)}"
        if decision.selected_profile_id
        else "model-profile-ref:none-selected"
    )
    status = (
        RouteVisibilityStatus.selected
        if str(decision.status) == "selected"
        else RouteVisibilityStatus.blocked
        if str(decision.status)
        in {
            "approval_required",
            "budget_exceeded",
            "privacy_blocked",
            "context_too_small",
        }
        else RouteVisibilityStatus.rejected
    )
    reason_codes = decision.reason_codes or ["NO_ROUTE_REASON_RECORDED"]
    return RouteDecisionVisibility(
        status=status,
        selected_profile_ref=selected,
        rejected_profile_refs=rejected,
        reason_codes=reason_codes,
        privacy_posture_ref=_route_privacy_posture(decision.reason_codes),
        cost_posture_ref=_route_cost_posture(decision.reason_codes),
        latency_posture_ref="latency-posture:estimated-only",
        context_posture_ref=_route_context_posture(decision.reason_codes, str(decision.status)),
        approval_posture_ref=(
            "approval-posture:required"
            if decision.required_approval or "CLOUD_APPROVAL_REQUIRED" in reason_codes
            else "approval-posture:not-required-for-preview"
        ),
        operator_summary=(
            f"Route preview status {decision.status}; no model execution was performed."
        ),
    )


def build_delegation_proposal(
    *,
    work_classification: WorkClassification,
    suffix_ref: str,
) -> DelegationProposalEnvelope:
    suffix = _safe_suffix(suffix_ref)
    if work_classification.classification == WorkClassificationValue.mechanical:
        state = DelegationProposalState.proposed
        delegate = ProposedDelegateKind.mechanical_worker
        delegated_refs = [f"delegated-work-ref:fusion:{suffix}"]
    elif work_classification.classification == WorkClassificationValue.validation:
        state = DelegationProposalState.proposed
        delegate = ProposedDelegateKind.validation_worker
        delegated_refs = [f"delegated-work-ref:fusion:{suffix}"]
    elif work_classification.classification == WorkClassificationValue.bookkeeping:
        state = DelegationProposalState.proposed
        delegate = ProposedDelegateKind.bookkeeping_worker
        delegated_refs = [f"delegated-work-ref:fusion:{suffix}"]
    elif work_classification.classification == WorkClassificationValue.blocked:
        state = DelegationProposalState.blocked
        delegate = ProposedDelegateKind.none
        delegated_refs = []
    else:
        state = DelegationProposalState.deferred
        delegate = ProposedDelegateKind.none
        delegated_refs = []

    return DelegationProposalEnvelope(
        proposal_state=state,
        proposed_delegate_kind=delegate,
        delegate_scope_ref=f"delegate-scope-ref:fusion:{suffix}",
        main_owner_responsibility_refs=[
            f"main-owner-responsibility-ref:fusion:{suffix}:plan",
            f"main-owner-responsibility-ref:fusion:{suffix}:final-review",
        ],
        delegated_work_refs=delegated_refs,
        blocked_execution_refs=[
            "blocked-state:fusion-sidekick-worker-execution-not-scoped",
            "blocked-state:fusion-background-dispatch-not-scoped",
        ],
        expected_receipt_refs=[f"receipt-plan:fusion-delegation:{suffix}"],
        rollback_safe_disable_posture_refs=[
            f"rollback-posture-ref:fusion-delegation:{suffix}",
            f"safe-disable-posture-ref:fusion-delegation:{suffix}",
        ],
        work_classification=work_classification,
    )


def build_cache_context_economics(
    *,
    suffix_ref: str,
    reroute_reason: RerouteReason = RerouteReason.none,
    cache_miss_expected: bool = False,
    blocker_refs: list[str] | None = None,
) -> CacheContextEconomics:
    suffix = _safe_suffix(suffix_ref)
    return CacheContextEconomics(
        context_budget_ref=f"context-budget-ref:fusion:{suffix}",
        compaction_boundary_ref=f"compaction-boundary-ref:fusion:{suffix}:not-executed",
        cache_miss_expected=cache_miss_expected,
        cache_reuse_posture=(
            CacheReusePosture.blocked if blocker_refs else CacheReusePosture.possible
        ),
        reroute_reason=reroute_reason,
        estimated_context_cost_posture="context-cost-posture:estimated-metadata-only",
        cache_or_context_blocker_refs=blocker_refs or [],
        evidence_refs=[f"evidence-ref:fusion-cache-context:{suffix}"],
    )


def build_dogfood_record(
    *,
    suffix_ref: str,
    outcome: DogfoodOutcome = DogfoodOutcome.needs_follow_up,
) -> FusionDogfoodEvidenceRecord:
    suffix = _safe_suffix(suffix_ref)
    return FusionDogfoodEvidenceRecord(
        review_record_ref=f"dogfood-review-ref:fusion:{suffix}",
        outcome=outcome,
        friction_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:operator-friction",
        review_time_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:review-time",
        cost_confusion_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:cost-confusion",
        routing_cost_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:routing-cost",
        ambiguity_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:ambiguity",
        interruption_delta_ref=f"dogfood-delta-ref:fusion:{suffix}:interruptions",
        redacted_summary_ref=f"redacted-summary-ref:fusion-dogfood:{suffix}",
        evidence_refs=[f"evidence-ref:fusion-dogfood:{suffix}"],
    )


def build_fusion_routing_delegation_read_model() -> FusionRoutingDelegationReadModel:
    mechanical = build_work_classification(
        WorkClassificationValue.mechanical,
        suffix_ref="action-inbox-review",
        source_ref="source-ref:fusion:action-inbox",
        evidence_ref="evidence-ref:fusion:action-inbox",
        reason_ref="classification-reason-ref:fusion:mechanical-review",
    )
    judgment = build_work_classification(
        WorkClassificationValue.judgment_required,
        suffix_ref="plan-review",
        source_ref="source-ref:fusion:plans",
        evidence_ref="evidence-ref:fusion:plans",
        reason_ref="classification-reason-ref:fusion:operator-judgment",
        confidence_posture=ConfidencePosture.medium,
    )
    blocked = build_work_classification(
        WorkClassificationValue.blocked,
        suffix_ref="provider-route",
        source_ref="source-ref:fusion:model-router",
        evidence_ref="evidence-ref:fusion:model-router",
        reason_ref="classification-reason-ref:fusion:provider-authority-blocked",
        blocked_authority_refs=[
            "blocked-state:fusion-no-model-provider-call",
            "blocked-state:fusion-exact-provider-authority-missing",
        ],
        confidence_posture=ConfidencePosture.high,
    )
    route_decisions = [
        RouteDecisionVisibility(
            status=RouteVisibilityStatus.selected,
            selected_profile_ref="model-profile-ref:local-preview",
            rejected_profile_refs=[],
            reason_codes=["SELECTED_PROFILE"],
            privacy_posture_ref="privacy-posture:local-metadata-only",
            cost_posture_ref="cost-posture:no-paid-provider-call",
            latency_posture_ref="latency-posture:estimated-only",
            context_posture_ref="context-posture:within-preview-budget",
            approval_posture_ref="approval-posture:not-required-for-preview",
            operator_summary=(
                "Local preview route is selected for metadata visibility only; no model execution was performed."
            ),
        ),
        RouteDecisionVisibility(
            status=RouteVisibilityStatus.blocked,
            selected_profile_ref="model-profile-ref:none-selected",
            rejected_profile_refs=["model-profile-ref:cloud-paid"],
            reason_codes=["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"],
            privacy_posture_ref="privacy-posture:cloud-review-required",
            cost_posture_ref="cost-posture:unknown-paid-cost-blocked",
            latency_posture_ref="latency-posture:not-measured",
            context_posture_ref="context-posture:not-expanded",
            approval_posture_ref="approval-posture:required",
            operator_summary=(
                "Paid cloud route is blocked until exact approval and CostGovernor posture are reviewed."
            ),
        ),
    ]
    return FusionRoutingDelegationReadModel(
        work_classifications=[mechanical, judgment, blocked],
        route_decisions=route_decisions,
        delegation_proposals=[
            build_delegation_proposal(
                work_classification=mechanical,
                suffix_ref="action-inbox-review",
            ),
            build_delegation_proposal(
                work_classification=judgment,
                suffix_ref="plan-review",
            ),
            build_delegation_proposal(
                work_classification=blocked,
                suffix_ref="provider-route",
            ),
        ],
        cache_context_economics=[
            build_cache_context_economics(suffix_ref="action-inbox-review"),
            build_cache_context_economics(
                suffix_ref="provider-route",
                reroute_reason=RerouteReason.cost_blocked,
                blocker_refs=["blocked-state:fusion-unknown-paid-cost"],
            ),
        ],
        dogfood_records=[
            build_dogfood_record(
                suffix_ref="routing-delegation-readability",
                outcome=DogfoodOutcome.needs_follow_up,
            )
        ],
    )


def fusion_routing_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": "implemented_backend_owned_readability_metadata",
            "feed_ref": FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
            "authority_boundary": "Classification, routing, delegation, and context/cost fields are review aids only.",
        }
        for surface in FCC_FUSION_ROUTING_SURFACES
    ]


def fusion_routing_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "backend_owned": True,
        "review_aid_only": True,
        "classification_authorizes_execution": False,
        "delegation_executes": False,
        "sidekick_execution_enabled": False,
        "action_execution_enabled": False,
        "provider_model_call_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_execution_enabled": False,
        "connector_write_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "background_dispatch_enabled": False,
        "production_authority_enabled": False,
    }


def forbidden_fusion_claims(text: str) -> list[str]:
    lowered = " ".join(text.lower().split())
    return [claim for claim in _FORBIDDEN_PRODUCT_CLAIMS if claim in lowered]


def _route_privacy_posture(reason_codes: list[str]) -> str:
    if any("PRIVACY" in reason or reason.startswith("CLOUD_BLOCKED") for reason in reason_codes):
        return "privacy-posture:blocked"
    return "privacy-posture:metadata-only"


def _route_cost_posture(reason_codes: list[str]) -> str:
    if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in reason_codes:
        return "cost-posture:unknown-paid-cost-blocked"
    if any("BUDGET" in reason for reason in reason_codes):
        return "cost-posture:budget-blocked"
    return "cost-posture:preview-only"


def _route_context_posture(reason_codes: list[str], status: str) -> str:
    if any("CONTEXT" in reason for reason in reason_codes) or status == "context_too_small":
        return "context-posture:blocked"
    return "context-posture:preview-only"


def _safe_suffix(value: str | None) -> str:
    suffix = _SAFE_SUFFIX_RE.sub("-", str(value or "").lower()).strip("-")
    return suffix or "missing"


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            validate_safe_execution_text(value, field_name)
            if _looks_like_ref(value):
                validate_execution_ref(value, field_name)
            lowered = value.lower()
            if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{field_name} contains unsafe content")
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_execution_text(str(key), field_name)
            _validate_safe_payload(item, field_name)


def _looks_like_ref(value: str) -> bool:
    return ":" in value and " " not in value and "\n" not in value
