from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


PROVIDER_ROUTING_INTELLIGENCE_CONTRACT_REF = (
    "contract-ref:provider-routing-intelligence:v1"
)
PROVIDER_ROUTING_INTELLIGENCE_SOURCE_REF = (
    "source-ref:model-router:deterministic-routing-patterns:v0.8.9"
)
PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES = 4

_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:@-]{2,220}$")
_SAFE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,119}$")


class ProviderRoutingStrategy(str, Enum):
    best_value = "best_value"
    lowest_cost = "lowest_cost"
    lowest_latency = "lowest_latency"
    best_quality = "best_quality"
    local_first = "local_first"


class ProviderRoutingRuntimeClass(str, Enum):
    local = "local"
    hosted = "hosted"


class ProviderRoutingCompatibilityStatus(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    unknown = "unknown"


class ProviderRoutingConfigurationStatus(str, Enum):
    configured = "configured"
    not_configured = "not_configured"
    invalid = "invalid"
    unknown = "unknown"


class ProviderRoutingHealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    stale = "stale"
    unknown = "unknown"


class ProviderRoutingBudgetStatus(str, Enum):
    available = "available"
    constrained = "constrained"
    exhausted = "exhausted"
    unknown = "unknown"


class ProviderRoutingSafeDisableStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    unknown = "unknown"


class ProviderRoutingCandidateStatus(str, Enum):
    eligible_for_request_scoped_evaluation = "eligible_for_request_scoped_evaluation"
    degraded_requires_exact_policy = "degraded_requires_exact_policy"
    blocked = "blocked"


class _ProviderRoutingModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class ProviderRoutingNeed(_ProviderRoutingModel):
    request_ref: str = "provider-routing-request-ref:control-plane:default"
    task_ref: str = "task-ref:provider-routing:operator-inspection"
    strategy: ProviderRoutingStrategy = ProviderRoutingStrategy.best_value
    required_capability_refs: list[str] = Field(default_factory=list, max_length=12)
    minimum_context_tokens: int = Field(0, ge=0, le=2_000_000)
    allow_degraded: bool = False
    maximum_presented_candidates: int = Field(
        PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
        ge=1,
        le=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    )

    @model_validator(mode="after")
    def validate_need(self) -> "ProviderRoutingNeed":
        _validate_safe_refs(
            [self.request_ref, self.task_ref, *self.required_capability_refs],
            "PROVIDER_ROUTING_NEED_REF_INVALID",
        )
        _reject_unsafe(self.model_dump(mode="json"), "PROVIDER_ROUTING_NEED_UNSAFE")
        return self


class ProviderRoutingObservation(_ProviderRoutingModel):
    observation_ref: str
    provider_ref: str
    provider_label: str = Field(..., min_length=1, max_length=120)
    provider_manifest_ref: str
    model_ref: str
    adapter_ref: str
    runtime_class: ProviderRoutingRuntimeClass
    compatibility_status: ProviderRoutingCompatibilityStatus
    configuration_status: ProviderRoutingConfigurationStatus
    health_status: ProviderRoutingHealthStatus
    budget_status: ProviderRoutingBudgetStatus
    safe_disable_status: ProviderRoutingSafeDisableStatus
    metered: bool
    estimated_cost_usd: float | None = Field(None, ge=0, le=1_000_000)
    estimated_latency_ms: float | None = Field(None, ge=0, le=3_600_000)
    quality_score: float | None = Field(None, ge=0, le=100)
    context_tokens: int | None = Field(None, ge=1, le=2_000_000)
    capability_refs: list[str] = Field(default_factory=list, max_length=24)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1, max_length=24)
    source_ref: str

    @model_validator(mode="after")
    def validate_observation(self) -> "ProviderRoutingObservation":
        _validate_safe_refs(
            [
                self.observation_ref,
                self.provider_ref,
                self.provider_manifest_ref,
                self.model_ref,
                self.adapter_ref,
                *self.capability_refs,
                *self.evidence_refs,
                self.source_ref,
            ],
            "PROVIDER_ROUTING_OBSERVATION_REF_INVALID",
        )
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_OBSERVATION_UNSAFE",
        )
        return self


class ProviderRoutingCandidate(_ProviderRoutingModel):
    candidate_ref: str
    rank: int | None = Field(None, ge=1, le=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES)
    provider_ref: str
    provider_label: str
    provider_manifest_ref: str
    model_ref: str
    adapter_ref: str
    status: ProviderRoutingCandidateStatus
    compatibility_status: ProviderRoutingCompatibilityStatus
    configuration_status: ProviderRoutingConfigurationStatus
    health_status: ProviderRoutingHealthStatus
    budget_status: ProviderRoutingBudgetStatus
    safe_disable_status: ProviderRoutingSafeDisableStatus
    estimated_cost_usd: float | None = None
    estimated_latency_ms: float | None = None
    quality_score: float | None = None
    reason_codes: list[str] = Field(default_factory=list, min_length=1)
    blocker_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    proposal_only: Literal[True] = True
    invocation_authorized: Literal[False] = False
    provider_call_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_candidate(self) -> "ProviderRoutingCandidate":
        _validate_safe_refs(
            [
                self.candidate_ref,
                self.provider_ref,
                self.provider_manifest_ref,
                self.model_ref,
                self.adapter_ref,
                *self.evidence_refs,
            ],
            "PROVIDER_ROUTING_CANDIDATE_REF_INVALID",
        )
        _validate_codes(self.reason_codes, "PROVIDER_ROUTING_REASON_CODE_INVALID")
        _validate_codes(self.blocker_codes, "PROVIDER_ROUTING_BLOCKER_CODE_INVALID")
        if self.status == ProviderRoutingCandidateStatus.blocked.value:
            if not self.blocker_codes or self.rank is not None:
                raise ValueError("PROVIDER_ROUTING_BLOCKED_CANDIDATE_INVALID")
        elif self.blocker_codes:
            raise ValueError("PROVIDER_ROUTING_ELIGIBLE_CANDIDATE_HAS_BLOCKERS")
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_CANDIDATE_UNSAFE",
        )
        return self


class ProviderRoutingProposal(_ProviderRoutingModel):
    schema_version: Literal["provider_routing_intelligence.v1"] = (
        "provider_routing_intelligence.v1"
    )
    contract_ref: str = PROVIDER_ROUTING_INTELLIGENCE_CONTRACT_REF
    proposal_ref: str
    request_ref: str
    request_fingerprint_ref: str
    strategy: ProviderRoutingStrategy
    status: Literal["proposal_only"] = "proposal_only"
    candidates: list[ProviderRoutingCandidate] = Field(default_factory=list)
    observed_candidate_count: int = Field(..., ge=0)
    presented_candidate_count: int = Field(..., ge=0)
    omitted_candidate_count: int = Field(..., ge=0)
    recommended_candidate_ref: str | None = None
    approval_queue_route_ref: str = "route-ref:control-center-approval-queue"
    run_detail_group_ref: str = "run-detail-group-ref:provider-routing-decision"
    bounded_fanout_presentation_ref: str = (
        "presentation-ref:provider-routing:bounded-candidates"
    )
    source_ref: str = PROVIDER_ROUTING_INTELLIGENCE_SOURCE_REF
    reason_codes: list[str] = Field(default_factory=list, min_length=1)
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    maximum_presented_candidates: int = PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES
    proposal_only: Literal[True] = True
    deterministic: Literal[True] = True
    safe_refs_only: Literal[True] = True
    approval_refs_are_identifiers_only: Literal[True] = True
    request_scoped_invocation_decision_required: Literal[True] = True
    invocation_authorized: Literal[False] = False
    provider_call_performed: Literal[False] = False
    fallback_execution_performed: Literal[False] = False
    background_fanout_performed: Literal[False] = False
    raw_prompt_persisted: Literal[False] = False
    raw_response_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_proposal(self) -> "ProviderRoutingProposal":
        refs = [
            self.contract_ref,
            self.proposal_ref,
            self.request_ref,
            self.request_fingerprint_ref,
            self.approval_queue_route_ref,
            self.run_detail_group_ref,
            self.bounded_fanout_presentation_ref,
            self.source_ref,
        ]
        if self.recommended_candidate_ref is not None:
            refs.append(self.recommended_candidate_ref)
        _validate_safe_refs(refs, "PROVIDER_ROUTING_PROPOSAL_REF_INVALID")
        _validate_codes(self.reason_codes, "PROVIDER_ROUTING_REASON_CODE_INVALID")
        _validate_codes(self.blocker_codes, "PROVIDER_ROUTING_BLOCKER_CODE_INVALID")
        if self.presented_candidate_count != len(self.candidates):
            raise ValueError("PROVIDER_ROUTING_PRESENTED_COUNT_DRIFT")
        if self.omitted_candidate_count != (
            self.observed_candidate_count - self.presented_candidate_count
        ):
            raise ValueError("PROVIDER_ROUTING_OMITTED_COUNT_DRIFT")
        if len(self.candidates) > self.maximum_presented_candidates:
            raise ValueError("PROVIDER_ROUTING_PRESENTATION_LIMIT_EXCEEDED")
        ranked = [
            candidate for candidate in self.candidates if candidate.rank is not None
        ]
        if [candidate.rank for candidate in ranked] != list(range(1, len(ranked) + 1)):
            raise ValueError("PROVIDER_ROUTING_RANK_ORDER_INVALID")
        if self.recommended_candidate_ref is not None:
            if not ranked or ranked[0].candidate_ref != self.recommended_candidate_ref:
                raise ValueError("PROVIDER_ROUTING_RECOMMENDATION_BINDING_INVALID")
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_PROPOSAL_UNSAFE",
        )
        return self


def build_provider_routing_proposal(
    need: ProviderRoutingNeed,
    observations: Iterable[ProviderRoutingObservation],
) -> ProviderRoutingProposal:
    rows = list(observations)
    provider_refs = [row.provider_ref for row in rows]
    if len(provider_refs) != len(set(provider_refs)):
        raise ValueError("PROVIDER_ROUTING_DUPLICATE_PROVIDER_REF")

    evaluated = [_evaluate_candidate(need, observation) for observation in rows]
    ranked = [candidate for candidate in evaluated if not candidate.blocker_codes]
    blocked = [candidate for candidate in evaluated if candidate.blocker_codes]
    ranked.sort(key=lambda candidate: _candidate_sort_key(need.strategy, candidate))
    blocked.sort(key=lambda candidate: candidate.provider_ref)

    ranked_for_presentation = ranked[: need.maximum_presented_candidates]
    ranked_with_positions = [
        candidate.model_copy(update={"rank": index})
        for index, candidate in enumerate(ranked_for_presentation, start=1)
    ]
    remaining_slots = need.maximum_presented_candidates - len(ranked_with_positions)
    presented = ranked_with_positions + blocked[:remaining_slots]
    recommended = (
        ranked_with_positions[0].candidate_ref if ranked_with_positions else None
    )
    fingerprint = _request_fingerprint(need)
    blocker_codes = sorted(
        {code for candidate in evaluated for code in candidate.blocker_codes}
    )
    reason_codes = ["PROVIDER_ROUTING_PROPOSAL_ONLY"]
    reason_codes.append(
        "PROVIDER_ROUTING_CANDIDATE_AVAILABLE"
        if recommended is not None
        else "PROVIDER_ROUTING_NO_ELIGIBLE_CANDIDATE"
    )
    return ProviderRoutingProposal(
        proposal_ref=f"provider-routing-proposal-ref:{fingerprint}:proposal-only",
        request_ref=need.request_ref,
        request_fingerprint_ref=f"request-fingerprint-ref:{fingerprint}",
        strategy=need.strategy,
        candidates=presented,
        observed_candidate_count=len(rows),
        presented_candidate_count=len(presented),
        omitted_candidate_count=len(rows) - len(presented),
        recommended_candidate_ref=recommended,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
        safe_summary=(
            "Provider routing proposal ranks bounded candidates using injected "
            "readiness, cost, latency, quality, and context observations. It does "
            "not authorize or perform provider invocation."
        ),
        maximum_presented_candidates=need.maximum_presented_candidates,
    )


def observations_from_provider_readiness(
    provider_readiness_items: Iterable[object],
) -> list[ProviderRoutingObservation]:
    return [_observation_from_readiness(item) for item in provider_readiness_items]


def _observation_from_readiness(item: object) -> ProviderRoutingObservation:
    provider_ref = str(_safe_get(item, "provider_id", "provider-ref:unknown:missing"))
    slug = _safe_slug(provider_ref)
    binding = _safe_get(item, "cost_governor_binding", {})
    model_ref = str(_safe_get(binding, "model_ref", f"model-ref:{slug}:not-selected"))
    readiness_posture = str(_safe_get(item, "readiness_posture", "unknown"))
    configured = bool(_safe_get(item, "credential_configured", False))
    refs_bound = bool(_safe_get(item, "provider_model_refs_bound", False))
    return ProviderRoutingObservation(
        observation_ref=f"provider-routing-observation-ref:{slug}:credential-readiness",
        provider_ref=provider_ref,
        provider_label=str(_safe_get(item, "provider_label", "Provider")),
        provider_manifest_ref=str(
            _safe_get(
                item, "provider_manifest_ref", f"provider-manifest-ref:{slug}:missing"
            )
        ),
        model_ref=model_ref,
        adapter_ref=f"provider-adapter-ref:{slug}:not-scoped",
        runtime_class=ProviderRoutingRuntimeClass.hosted,
        compatibility_status=(
            ProviderRoutingCompatibilityStatus.supported
            if refs_bound
            else ProviderRoutingCompatibilityStatus.unknown
        ),
        configuration_status=(
            ProviderRoutingConfigurationStatus.configured
            if configured and readiness_posture == "configured"
            else ProviderRoutingConfigurationStatus.not_configured
        ),
        health_status=ProviderRoutingHealthStatus.unknown,
        budget_status=ProviderRoutingBudgetStatus.unknown,
        safe_disable_status=ProviderRoutingSafeDisableStatus.unknown,
        metered=True,
        evidence_refs=[
            str(
                _safe_get(
                    binding, "binding_ref", f"provider-cost-binding-ref:{slug}:missing"
                )
            ),
            str(_safe_get(item, "policy_ref", f"policy-ref:{slug}:missing")),
        ],
        source_ref="source-ref:python-core:provider-credential-readiness",
    )


def _evaluate_candidate(
    need: ProviderRoutingNeed,
    observation: ProviderRoutingObservation,
) -> ProviderRoutingCandidate:
    blockers: list[str] = []
    reasons = ["PROVIDER_OBSERVATION_EVALUATED"]
    if (
        observation.safe_disable_status
        != ProviderRoutingSafeDisableStatus.inactive.value
    ):
        blockers.append(
            "SAFE_DISABLE_ACTIVE"
            if observation.safe_disable_status
            == ProviderRoutingSafeDisableStatus.active.value
            else "SAFE_DISABLE_UNKNOWN"
        )
    if (
        observation.compatibility_status
        != ProviderRoutingCompatibilityStatus.supported.value
    ):
        blockers.append(
            "COMPATIBILITY_UNSUPPORTED"
            if observation.compatibility_status
            == ProviderRoutingCompatibilityStatus.unsupported.value
            else "COMPATIBILITY_UNKNOWN"
        )
    if (
        observation.configuration_status
        != ProviderRoutingConfigurationStatus.configured.value
    ):
        blockers.append(
            {
                ProviderRoutingConfigurationStatus.not_configured.value: "PROVIDER_NOT_CONFIGURED",
                ProviderRoutingConfigurationStatus.invalid.value: "PROVIDER_CONFIGURATION_INVALID",
            }.get(observation.configuration_status, "PROVIDER_CONFIGURATION_UNKNOWN")
        )
    if observation.health_status in {
        ProviderRoutingHealthStatus.unhealthy.value,
        ProviderRoutingHealthStatus.stale.value,
        ProviderRoutingHealthStatus.unknown.value,
    }:
        blockers.append(
            {
                ProviderRoutingHealthStatus.unhealthy.value: "PROVIDER_UNHEALTHY",
                ProviderRoutingHealthStatus.stale.value: "PROVIDER_HEALTH_STALE",
            }.get(observation.health_status, "PROVIDER_HEALTH_UNKNOWN")
        )
    if observation.health_status == ProviderRoutingHealthStatus.degraded.value:
        if need.allow_degraded:
            reasons.append("DEGRADED_USE_REQUIRES_EXACT_POLICY")
        else:
            blockers.append("DEGRADED_USE_NOT_PERMITTED")
    if observation.budget_status == ProviderRoutingBudgetStatus.exhausted.value:
        blockers.append("PROVIDER_BUDGET_EXHAUSTED")
    if (
        observation.metered
        and observation.budget_status == ProviderRoutingBudgetStatus.unknown.value
    ):
        blockers.append("METERED_PROVIDER_BUDGET_UNKNOWN")
    if observation.metered and observation.estimated_cost_usd is None:
        blockers.append("METERED_PROVIDER_COST_UNKNOWN")
    if observation.budget_status == ProviderRoutingBudgetStatus.constrained.value:
        reasons.append("PROVIDER_BUDGET_CONSTRAINED")
    missing_capabilities = set(need.required_capability_refs) - set(
        observation.capability_refs
    )
    if missing_capabilities:
        blockers.append("REQUIRED_CAPABILITY_MISSING")
    if need.minimum_context_tokens:
        if observation.context_tokens is None:
            blockers.append("CONTEXT_CAPACITY_UNKNOWN")
        elif observation.context_tokens < need.minimum_context_tokens:
            blockers.append("CONTEXT_CAPACITY_INSUFFICIENT")
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        status = ProviderRoutingCandidateStatus.blocked
        summary = "Provider candidate is blocked by fail-closed runtime evidence."
    elif observation.health_status == ProviderRoutingHealthStatus.degraded.value:
        status = ProviderRoutingCandidateStatus.degraded_requires_exact_policy
        summary = (
            "Provider candidate is degraded and requires an exact permitting policy."
        )
    else:
        status = ProviderRoutingCandidateStatus.eligible_for_request_scoped_evaluation
        reasons.append("ELIGIBLE_FOR_REQUEST_SCOPED_EVALUATION")
        summary = (
            "Provider candidate may proceed to exact request-scoped authority evaluation; "
            "this proposal grants no invocation authority."
        )
    return ProviderRoutingCandidate(
        candidate_ref=_candidate_ref(observation),
        provider_ref=observation.provider_ref,
        provider_label=observation.provider_label,
        provider_manifest_ref=observation.provider_manifest_ref,
        model_ref=observation.model_ref,
        adapter_ref=observation.adapter_ref,
        status=status,
        compatibility_status=observation.compatibility_status,
        configuration_status=observation.configuration_status,
        health_status=observation.health_status,
        budget_status=observation.budget_status,
        safe_disable_status=observation.safe_disable_status,
        estimated_cost_usd=observation.estimated_cost_usd,
        estimated_latency_ms=observation.estimated_latency_ms,
        quality_score=observation.quality_score,
        reason_codes=reasons,
        blocker_codes=blockers,
        evidence_refs=observation.evidence_refs,
        safe_summary=summary,
    )


def _candidate_sort_key(
    strategy: ProviderRoutingStrategy | str,
    candidate: ProviderRoutingCandidate,
) -> tuple[float, float, float, str]:
    cost = (
        candidate.estimated_cost_usd
        if candidate.estimated_cost_usd is not None
        else float("inf")
    )
    latency = (
        candidate.estimated_latency_ms
        if candidate.estimated_latency_ms is not None
        else float("inf")
    )
    quality = candidate.quality_score if candidate.quality_score is not None else 0.0
    if strategy == ProviderRoutingStrategy.lowest_cost.value:
        return (cost, latency, -quality, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.lowest_latency.value:
        return (latency, cost, -quality, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.best_quality.value:
        return (-quality, cost, latency, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.local_first.value:
        local_rank = 0 if ":local" in candidate.adapter_ref else 1
        return (float(local_rank), cost, latency, candidate.provider_ref)
    value = quality / (1.0 + cost)
    return (-value, latency, cost, candidate.provider_ref)


def _candidate_ref(observation: ProviderRoutingObservation) -> str:
    digest = hashlib.sha256(
        f"{observation.provider_ref}|{observation.model_ref}|{observation.adapter_ref}".encode()
    ).hexdigest()[:16]
    return f"provider-routing-candidate-ref:{digest}"


def _request_fingerprint(need: ProviderRoutingNeed) -> str:
    payload = json.dumps(
        need.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _validate_safe_refs(values: Iterable[str], error_code: str) -> None:
    if any(_SAFE_REF_RE.fullmatch(value) is None for value in values):
        raise ValueError(error_code)


def _validate_codes(values: Iterable[str], error_code: str) -> None:
    if any(_SAFE_CODE_RE.fullmatch(value) is None for value in values):
        raise ValueError(error_code)
    if len(list(values)) != len(set(values)):
        raise ValueError(f"{error_code}_DUPLICATE")


def _reject_unsafe(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


def _safe_get(value: object, field_name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _safe_slug(value: str) -> str:
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", value.lower()) if token]
    return "-".join(tokens[:4]) or "provider"
