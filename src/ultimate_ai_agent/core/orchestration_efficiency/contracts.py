from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.model_router import ModelRouteCostMode
from ultimate_ai_agent.core.orchestration_efficiency.enums import OrchestrationPreviewStatus


def _assert_secret_clean(value: Any, label: str) -> None:
    if scan_payload_for_secrets(value):
        raise ValueError(f"{label} contains secret-like content.")


class _EfficiencyModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class RouteOptimizationWeights(_EfficiencyModel):
    cost_weight: float = Field(default=1.0, ge=0)
    latency_weight: float = Field(default=1.0, ge=0)
    token_weight: float = Field(default=0.25, ge=0)
    cache_weight: float = Field(default=0.75, ge=0)
    quality_weight: float = Field(default=1.0, ge=0)
    locality_weight: float = Field(default=0.25, ge=0)

    @model_validator(mode="after")
    def at_least_one_weight(self):
        if not any(
            [
                self.cost_weight,
                self.latency_weight,
                self.token_weight,
                self.cache_weight,
                self.quality_weight,
                self.locality_weight,
            ]
        ):
            raise ValueError("At least one route optimization weight must be positive.")
        return self


class OrchestrationEfficiencyPolicy(_EfficiencyModel):
    policy_id: str = Field(..., min_length=1)
    cost_mode: ModelRouteCostMode = ModelRouteCostMode.balanced
    weights: RouteOptimizationWeights = Field(default_factory=RouteOptimizationWeights)
    quality_floor: float = Field(default=0.0, ge=0, le=1)
    default_quality_score: float = Field(default=0.75, ge=0, le=1)
    profile_quality_scores: dict[str, float] = Field(default_factory=dict)
    premium_profile_refs: list[str] = Field(default_factory=list)
    fallback_allowed: bool = False
    max_fallback_candidates: int = Field(default=2, ge=0, le=10)
    require_known_paid_cost: bool = True
    critical_requires_verifier: bool = True
    critical_requires_approval: bool = True
    allow_cloud_in_local_private: bool = False
    verifier_plan_ref: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self):
        _assert_secret_clean(self.metadata, "metadata")
        for ref in [*self.premium_profile_refs, *self.metadata_refs]:
            _assert_secret_clean(ref, "metadata_ref")
        for profile_id, score in self.profile_quality_scores.items():
            _assert_secret_clean(profile_id, "profile_quality_scores")
            if score < 0 or score > 1:
                raise ValueError("profile_quality_scores values must be between 0 and 1.")
        if self.verifier_plan_ref:
            _assert_secret_clean(self.verifier_plan_ref, "verifier_plan_ref")
        return self


class CacheabilityPlan(_EfficiencyModel):
    plan_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    model_profile_id: str | None = None
    runtime_optimization_profile_ref: str | None = None
    prompt_bundle_hash: str | None = None
    tool_schema_bundle_hash: str | None = None
    tool_order_hash: str | None = None
    context_pack_hash: str | None = None
    data_classification: str = Field(..., min_length=1)
    consent_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    cache_eligible: bool = False
    predicted_prefix_reuse_tokens: int = Field(default=0, ge=0)
    predicted_cache_write_tokens: int = Field(default=0, ge=0)
    predicted_cache_hit_tokens: int = Field(default=0, ge=0)
    invalidation_reason_codes: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cache_plan(self):
        _assert_secret_clean(self.model_dump(mode="json"), "cacheability_plan")
        if self.cache_eligible and not any(
            [
                self.prompt_bundle_hash,
                self.tool_schema_bundle_hash,
                self.tool_order_hash,
                self.context_pack_hash,
            ]
        ):
            raise ValueError("Cache-eligible plans must include at least one stable hash.")
        return self


class FallbackPlan(_EfficiencyModel):
    plan_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    fallback_allowed: bool = False
    primary_profile_id: str | None = None
    fallback_profile_ids: list[str] = Field(default_factory=list)
    fallback_reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_fallback_plan(self):
        _assert_secret_clean(self.model_dump(mode="json"), "fallback_plan")
        return self


class RouteScoreBreakdown(_EfficiencyModel):
    model_profile_id: str = Field(..., min_length=1)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    estimated_latency_ms: float = Field(default=0.0, ge=0)
    estimated_runtime_seconds: float | None = Field(None, ge=0)
    cache_adjusted_estimated_cost_usd: float = Field(default=0.0, ge=0)
    cache_adjusted_latency_ms: float = Field(default=0.0, ge=0)
    cache_reuse_ratio: float = Field(default=0.0, ge=0, le=1)
    total_tokens: int = Field(default=0, ge=0)
    quality_score: float = Field(default=0.0, ge=0, le=1)
    normalized_estimated_cost: float = Field(default=0.0, ge=0)
    normalized_latency: float = Field(default=0.0, ge=0)
    normalized_token_pressure: float = Field(default=0.0, ge=0)
    cache_miss_penalty: float = Field(default=0.0, ge=0)
    inverse_quality_score: float = Field(default=0.0, ge=0)
    locality_penalty: float = Field(default=0.0, ge=0)
    total_score: float = Field(default=0.0, ge=0)
    reason_codes: list[str] = Field(default_factory=list)


class OptimizationMetricSummary(_EfficiencyModel):
    candidate_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    rejected_count_by_reason: dict[str, int] = Field(default_factory=dict)
    selected_profile_id: str | None = None
    estimated_cost_usd: float | None = Field(None, ge=0)
    estimated_latency_ms: float | None = Field(None, ge=0)
    estimated_runtime_seconds: float | None = Field(None, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    available_history_tokens: int | None = Field(None, ge=0)
    context_trimmed_tokens: int = Field(default=0, ge=0)
    cache_eligible_count: int = Field(default=0, ge=0)
    cache_invalidation_reason_count: int = Field(default=0, ge=0)
    budget_status: str | None = None
    approval_required_count: int = Field(default=0, ge=0)
    fallback_planned_count: int = Field(default=0, ge=0)
    critical_verifier_planned_count: int = Field(default=0, ge=0)
    privacy_block_count: int = Field(default=0, ge=0)
    unknown_paid_cost_count: int = Field(default=0, ge=0)
    observability_estimated_bytes: int = Field(default=0, ge=0)


class OrchestrationPreviewDecision(_EfficiencyModel):
    decision_id: str = Field(default_factory=lambda: f"orch_{uuid.uuid4().hex[:12]}")
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    policy_id: str = Field(..., min_length=1)
    status: OrchestrationPreviewStatus
    cost_mode: ModelRouteCostMode
    selected_profile_id: str | None = None
    selected_model_id: str | None = None
    candidate_profile_ids: list[str] = Field(default_factory=list)
    rejected_profile_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    estimated_cost_usd: float | None = Field(None, ge=0)
    estimated_latency_ms: float | None = Field(None, ge=0)
    estimated_runtime_seconds: float | None = Field(None, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    score_breakdowns: list[RouteScoreBreakdown] = Field(default_factory=list)
    selected_score: RouteScoreBreakdown | None = None
    cacheability_plan: CacheabilityPlan
    fallback_plan: FallbackPlan
    metric_summary: OptimizationMetricSummary
    required_approval: bool = False
    verification_required: bool = False
    verifier_plan_ref: str | None = None
    fallback_used: bool = False
    no_effect: bool = True
    event_ref: str | None = None
    eval_result_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None

    @model_validator(mode="after")
    def validate_preview_decision(self):
        _assert_secret_clean(self.model_dump(mode="json"), "orchestration_preview_decision")
        if not self.no_effect:
            raise ValueError("Orchestration preview decisions must remain no-effect.")
        if not self.reason_codes:
            raise ValueError("Orchestration preview decisions require reason codes.")
        return self

    def to_redacted_ledger_metadata(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "run_id": self.run_id,
            "policy_id": self.policy_id,
            "status": self.status,
            "cost_mode": self.cost_mode,
            "selected_profile_id": self.selected_profile_id,
            "candidate_count": self.metric_summary.candidate_count,
            "rejected_count": self.metric_summary.rejected_count,
            "reason_codes": list(self.reason_codes),
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_runtime_seconds": self.estimated_runtime_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cache_plan_ref": self.cacheability_plan.plan_ref,
            "cache_eligible": self.cacheability_plan.cache_eligible,
            "fallback_plan_ref": self.fallback_plan.plan_ref,
            "fallback_planned_count": self.metric_summary.fallback_planned_count,
            "verification_required": self.verification_required,
            "verifier_plan_ref": self.verifier_plan_ref,
            "required_approval": self.required_approval,
            "no_effect": self.no_effect,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
        }


def validate_orchestration_efficiency_policy(
    policy: OrchestrationEfficiencyPolicy,
) -> OrchestrationEfficiencyPolicy:
    return OrchestrationEfficiencyPolicy.model_validate(policy.model_dump())


def validate_cacheability_plan(plan: CacheabilityPlan) -> CacheabilityPlan:
    return CacheabilityPlan.model_validate(plan.model_dump())


def validate_orchestration_preview_decision(
    decision: OrchestrationPreviewDecision,
) -> OrchestrationPreviewDecision:
    return OrchestrationPreviewDecision.model_validate(decision.model_dump())
