from __future__ import annotations
from typing import Any

import hashlib
from dataclasses import dataclass

from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostGovernor
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelRouteCostMode,
    ModelRouteDecision,
    ModelRouteRequest,
    ModelRouteStatus,
    ModelRouter,
)
from ultimate_ai_agent.core.orchestration_efficiency.contracts import (
    CacheabilityPlan,
    FallbackPlan,
    OptimizationMetricSummary,
    OrchestrationEfficiencyPolicy,
    OrchestrationPreviewDecision,
    RouteScoreBreakdown,
    validate_cacheability_plan,
    validate_orchestration_efficiency_policy,
)
from ultimate_ai_agent.core.orchestration_efficiency.enums import OrchestrationPreviewStatus


@dataclass(frozen=True)
class _EligibleCandidate:
    profile: ModelCapabilityProfile
    decision: ModelRouteDecision
    runtime_seconds: float | None
    quality_score: float


class OrchestrationEfficiencyPlanner:
    def __init__(self, router: ModelRouter | None = None, cost_governor: CostGovernor | None = None) -> None:
        self.router = router or ModelRouter()
        self.cost_governor = cost_governor or self.router.cost_governor

    def preview(
        self,
        request: ModelRouteRequest,
        policy: OrchestrationEfficiencyPolicy,
        cacheability_plan: CacheabilityPlan | None = None,
    ) -> OrchestrationPreviewDecision:
        active_policy = validate_orchestration_efficiency_policy(policy)
        active_cache_plan = validate_cacheability_plan(
            cacheability_plan or self._default_cacheability_plan(request)
        )
        preflight_reasons = self._preflight_rejection_reasons(request, active_policy)
        if preflight_reasons:
            rejected_ids = sorted(profile.model_profile_id for profile in request.available_profiles)
            return self._failure_decision(
                request=request,
                policy=active_policy,
                cacheability_plan=active_cache_plan,
                rejected_profile_ids=rejected_ids,
                rejection_reason_codes=preflight_reasons,
                rejection_reasons=self._reason_counts(preflight_reasons),
                approval_required_count=1 if "CRITICAL_APPROVAL_REQUIRED" in preflight_reasons else 0,
                privacy_block_count=len(rejected_ids)
                if "CREDENTIAL_SECRET_NEVER_TO_MODEL" in preflight_reasons
                else 0,
                unknown_paid_cost_count=0,
            )

        eligible: list[_EligibleCandidate] = []
        rejected_profile_ids: list[str] = []
        rejection_reasons: dict[str, int] = {}
        rejection_reason_codes: list[str] = []
        approval_required_count = 0
        privacy_block_count = 0
        unknown_paid_cost_count = 0

        prepared = self.router._prepare_policy(request)
        routing_budgets = self._routing_budgets(request)
        for profile in sorted(request.available_profiles, key=lambda item: item.model_profile_id):
            decision, runtime_seconds = self._preview_profile(request, profile, prepared, routing_budgets)
            if decision.status != ModelRouteStatus.selected:
                rejected_profile_ids.append(profile.model_profile_id)
                reason_codes = self._translate_rejection_reasons(decision.reason_codes)
                rejection_reason_codes.extend(reason_codes)
                self._record_reasons(rejection_reasons, reason_codes)
                if decision.required_approval or decision.status == ModelRouteStatus.approval_required:
                    approval_required_count += 1
                if decision.status == ModelRouteStatus.privacy_blocked:
                    privacy_block_count += 1
                if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in reason_codes:
                    unknown_paid_cost_count += 1
                continue

            mode_reason = self._cost_mode_rejection_reason(profile, active_policy)
            quality_score = self._quality_score(profile, active_policy)
            if mode_reason or quality_score < active_policy.quality_floor:
                rejected_profile_ids.append(profile.model_profile_id)
                reason_codes = [
                    reason
                    for reason in [
                        mode_reason,
                        "QUALITY_THRESHOLD_NOT_MET" if quality_score < active_policy.quality_floor else None,
                    ]
                    if reason
                ]
                rejection_reason_codes.extend(reason_codes)
                self._record_reasons(rejection_reasons, reason_codes)
                continue

            eligible.append(
                _EligibleCandidate(
                    profile=profile,
                    decision=decision,
                    runtime_seconds=runtime_seconds,
                    quality_score=quality_score,
                )
            )

        score_breakdowns = self._score_candidates(request, active_policy, active_cache_plan, eligible)
        sorted_scores = sorted(score_breakdowns, key=lambda score: (score.total_score, score.model_profile_id))
        selected_score = sorted_scores[0] if sorted_scores else None
        selected_candidate = self._candidate_for_score(eligible, selected_score)

        if selected_candidate is None or selected_score is None:
            return self._failure_decision(
                request=request,
                policy=active_policy,
                cacheability_plan=active_cache_plan,
                rejected_profile_ids=sorted(set(rejected_profile_ids)),
                rejection_reason_codes=rejection_reason_codes or ["NO_MODEL_CANDIDATE"],
                rejection_reasons=rejection_reasons,
                approval_required_count=approval_required_count,
                privacy_block_count=privacy_block_count,
                unknown_paid_cost_count=unknown_paid_cost_count,
            )

        fallback_ids = [
            score.model_profile_id
            for score in sorted_scores
            if score.model_profile_id != selected_score.model_profile_id
        ]
        fallback_allowed = bool(active_policy.fallback_allowed or request.routing_policy.fallback_allowed)
        planned_fallback_ids = fallback_ids[: active_policy.max_fallback_candidates] if fallback_allowed else []
        fallback_plan = self._fallback_plan(
            request,
            primary_profile_id=selected_score.model_profile_id,
            fallback_profile_ids=planned_fallback_ids,
            fallback_allowed=fallback_allowed,
        )
        reason_codes = self._selected_reason_codes(active_policy, active_cache_plan, selected_score, fallback_plan)
        metric_summary = self._metric_summary(
            request=request,
            selected_candidate=selected_candidate,
            selected_score=selected_score,
            candidate_count=len(eligible),
            rejected_profile_ids=rejected_profile_ids,
            rejection_reasons=rejection_reasons,
            cacheability_plan=active_cache_plan,
            fallback_plan=fallback_plan,
            approval_required_count=approval_required_count,
            privacy_block_count=privacy_block_count,
            unknown_paid_cost_count=unknown_paid_cost_count,
            critical_verifier_planned_count=1 if active_policy.cost_mode == ModelRouteCostMode.critical else 0,
        )
        verifier_plan_ref = self._verifier_plan_ref(request, active_policy)
        return OrchestrationPreviewDecision(
            decision_id=self._decision_id(request, active_policy, selected_score.model_profile_id),
            request_id=request.request_id,
            run_id=request.run_id,
            policy_id=active_policy.policy_id,
            status=OrchestrationPreviewStatus.selected,
            cost_mode=active_policy.cost_mode,
            selected_profile_id=selected_candidate.profile.model_profile_id,
            selected_model_id=selected_candidate.profile.model_id,
            candidate_profile_ids=[candidate.profile.model_profile_id for candidate in eligible],
            rejected_profile_ids=sorted(set(rejected_profile_ids)),
            reason_codes=reason_codes,
            safe_message="Orchestration route preview selected by deterministic no-effect policy.",
            estimated_cost_usd=selected_candidate.decision.estimated_cost,
            estimated_latency_ms=selected_candidate.decision.estimated_latency_ms,
            estimated_runtime_seconds=selected_candidate.runtime_seconds,
            input_tokens=request.estimated_input_tokens,
            output_tokens=request.estimated_output_tokens,
            total_tokens=request.total_estimated_tokens,
            score_breakdowns=sorted_scores,
            selected_score=selected_score,
            cacheability_plan=active_cache_plan,
            fallback_plan=fallback_plan,
            metric_summary=metric_summary,
            required_approval=False,
            verification_required=active_policy.cost_mode == ModelRouteCostMode.critical,
            verifier_plan_ref=verifier_plan_ref,
            fallback_used=False,
            event_ref=request.event_ref,
            trace_id=active_policy.trace_id or request.event_ref,
            correlation_id=active_policy.correlation_id or request.run_id,
        )

    def _score_candidates(
        self,
        request: ModelRouteRequest,
        policy: OrchestrationEfficiencyPolicy,
        cacheability_plan: CacheabilityPlan,
        candidates: list[_EligibleCandidate],
    ) -> list[RouteScoreBreakdown]:
        if not candidates:
            return []
        cache_reuse_ratios = {
            candidate.profile.model_profile_id: self._cache_reuse_ratio(
                request,
                candidate.profile,
                cacheability_plan,
            )
            for candidate in candidates
        }
        adjusted_costs = {
            candidate.profile.model_profile_id: self._cache_adjusted_cost(
                candidate.decision.estimated_cost or 0.0,
                request,
                candidate.profile,
                cache_reuse_ratios[candidate.profile.model_profile_id],
            )
            for candidate in candidates
        }
        adjusted_latencies = {
            candidate.profile.model_profile_id: self._cache_adjusted_latency(
                candidate.decision.estimated_latency_ms or 0.0,
                cache_reuse_ratios[candidate.profile.model_profile_id],
            )
            for candidate in candidates
        }
        max_cost = max(adjusted_costs.values()) or 1.0
        max_latency = max(adjusted_latencies.values()) or 1.0
        weights = policy.weights
        scores: list[RouteScoreBreakdown] = []
        for candidate in candidates:
            cost = candidate.decision.estimated_cost or 0.0
            latency = candidate.decision.estimated_latency_ms or 0.0
            adjusted_cost = adjusted_costs[candidate.profile.model_profile_id]
            adjusted_latency = adjusted_latencies[candidate.profile.model_profile_id]
            cache_reuse_ratio = cache_reuse_ratios[candidate.profile.model_profile_id]
            context_limit = candidate.profile.max_context_tokens or max(request.total_estimated_tokens, 1)
            token_pressure = request.total_estimated_tokens / max(context_limit, 1)
            cache_miss_penalty = self._cache_miss_penalty(candidate.profile, cacheability_plan)
            inverse_quality = 1 - candidate.quality_score
            locality_penalty = 1.0 if candidate.profile.is_cloud else 0.0
            total_score = (
                weights.cost_weight * (adjusted_cost / max_cost)
                + weights.latency_weight * (adjusted_latency / max_latency)
                + weights.token_weight * token_pressure
                + weights.cache_weight * cache_miss_penalty
                + weights.quality_weight * inverse_quality
                + weights.locality_weight * locality_penalty
            )
            scores.append(
                RouteScoreBreakdown(
                    model_profile_id=candidate.profile.model_profile_id,
                    estimated_cost_usd=round(cost, 6),
                    estimated_latency_ms=round(latency, 3),
                    estimated_runtime_seconds=candidate.runtime_seconds,
                    cache_adjusted_estimated_cost_usd=round(adjusted_cost, 6),
                    cache_adjusted_latency_ms=round(adjusted_latency, 3),
                    cache_reuse_ratio=round(cache_reuse_ratio, 6),
                    total_tokens=request.total_estimated_tokens,
                    quality_score=candidate.quality_score,
                    normalized_estimated_cost=round(adjusted_cost / max_cost, 6),
                    normalized_latency=round(adjusted_latency / max_latency, 6),
                    normalized_token_pressure=round(token_pressure, 6),
                    cache_miss_penalty=cache_miss_penalty,
                    inverse_quality_score=round(inverse_quality, 6),
                    locality_penalty=locality_penalty,
                    total_score=round(total_score, 6),
                    reason_codes=self._score_reason_codes(policy, cacheability_plan, candidate.profile),
                )
            )
        return scores

    def _score_reason_codes(
        self,
        policy: OrchestrationEfficiencyPolicy,
        cacheability_plan: CacheabilityPlan,
        profile: ModelCapabilityProfile,
    ) -> list[str]:
        reasons = ["COST_WEIGHT_APPLIED", "LATENCY_WEIGHT_APPLIED", "QUALITY_THRESHOLD_MET"]
        if cacheability_plan.cache_eligible and self._cache_plan_applies(profile, cacheability_plan):
            reasons.append("CACHE_REUSE_PREFERRED")
        if policy.cost_mode == ModelRouteCostMode.local_private and not profile.is_cloud:
            reasons.append("LOCAL_PRIVATE_ROUTE_PREFERRED")
        return reasons

    def _preview_profile(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        prepared: Any,
        routing_budgets: list[CostBudget],
    ) -> tuple[ModelRouteDecision, float | None]:
        profile_reasons = self.router._profile_rejection_reasons(request, profile, prepared)
        if profile_reasons:
            approval_required = any(
                reason.startswith("APPROVAL_") or reason == "CLOUD_APPROVAL_REQUIRED"
                for reason in profile_reasons
            )
            return (
                self._profile_failure_decision(
                    request,
                    profile,
                    profile_reasons,
                    self.router._failure_status(profile_reasons, approval_required),
                    approval_required=approval_required,
                    prepared=prepared,
                ),
                None,
            )

        estimate = self.cost_governor.estimate_route_cost(request, profile)
        cost_decision = self.cost_governor.evaluate(estimate, routing_budgets)
        if cost_decision.status == BudgetStatus.approval_required:
            return (
                self._profile_failure_decision(
                    request,
                    profile,
                    cost_decision.reason_codes,
                    ModelRouteStatus.approval_required,
                    approval_required=True,
                    prepared=prepared,
                ),
                estimate.estimated_runtime_seconds,
            )
        if not cost_decision.allowed:
            return (
                self._profile_failure_decision(
                    request,
                    profile,
                    cost_decision.reason_codes,
                    ModelRouteStatus.budget_exceeded,
                    approval_required=False,
                    prepared=prepared,
                ),
                estimate.estimated_runtime_seconds,
            )

        warning_reason_codes = (
            cost_decision.reason_codes if cost_decision.status == BudgetStatus.warning else []
        )
        reason_codes = ["SELECTED_PROFILE", *warning_reason_codes]
        if profile.is_cloud and request.approval_ref and self.router.approval_authority is not None:
            reason_codes.append("APPROVAL_VALIDATED")
        return (
            ModelRouteDecision(
                request_id=request.request_id,
                run_id=request.run_id,
                status=ModelRouteStatus.selected,
                selected_profile_id=profile.model_profile_id,
                selected_model_id=profile.model_id,
                candidate_profile_ids=[profile.model_profile_id],
                rejected_profile_ids=[],
                reason_codes=reason_codes,
                safe_message="Model route selected by orchestration preview. No model execution was performed.",
                estimated_cost=estimate.estimated_cost_usd or 0.0,
                estimated_latency_ms=profile.time_to_first_token_ms or 0.0,
                cost_mode=str(request.routing_policy.cost_mode) if request.routing_policy.cost_mode else None,
                trace_id=request.event_ref,
                correlation_id=request.run_id,
                privacy_notes=self.router._privacy_notes(request, profile, prepared),
                required_approval=False,
                consent_refs=request.consent_refs,
                event_ref=request.event_ref,
            ),
            estimate.estimated_runtime_seconds,
        )

    def _profile_failure_decision(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        reason_codes: list[str],
        status: ModelRouteStatus,
        *,
        approval_required: bool,
        prepared: Any,
    ) -> ModelRouteDecision:
        return ModelRouteDecision(
            request_id=request.request_id,
            run_id=request.run_id,
            status=status,
            selected_profile_id=None,
            selected_model_id=None,
            candidate_profile_ids=[],
            rejected_profile_ids=[profile.model_profile_id],
            reason_codes=sorted(set(reason_codes)) or ["NO_MODEL_CANDIDATE"],
            safe_message="Model route rejected by orchestration preview. No model execution was performed.",
            cost_mode=str(request.routing_policy.cost_mode) if request.routing_policy.cost_mode else None,
            trace_id=request.event_ref,
            correlation_id=request.run_id,
            privacy_notes=self.router._privacy_notes(request, profile, prepared),
            required_approval=approval_required,
            consent_refs=request.consent_refs,
            event_ref=request.event_ref,
        )

    def _routing_budgets(self, request: ModelRouteRequest) -> list[CostBudget]:
        if request.routing_policy.max_estimated_cost_usd is None:
            return []
        return [
            CostBudget(
                budget_id=f"route_policy_{request.routing_policy.policy_id}",
                scope=BudgetScope.run,
                max_cost_usd=request.routing_policy.max_estimated_cost_usd,
                hard_limit=request.routing_policy.max_estimated_cost_hard_limit,
            )
        ]

    def _selected_reason_codes(
        self,
        policy: OrchestrationEfficiencyPolicy,
        cacheability_plan: CacheabilityPlan,
        selected_score: RouteScoreBreakdown,
        fallback_plan: FallbackPlan,
    ) -> list[str]:
        reasons = ["SELECTED_PROFILE", "CHEAPER_ROUTE_SELECTED", *selected_score.reason_codes]
        if (
            policy.cost_mode == ModelRouteCostMode.premium
            and selected_score.model_profile_id in policy.premium_profile_refs
        ):
            reasons.append("PREMIUM_ROUTE_JUSTIFIED")
        if policy.cost_mode == ModelRouteCostMode.critical:
            reasons.append("CRITICAL_VERIFIER_REQUIRED")
        if fallback_plan.fallback_profile_ids:
            reasons.append("FALLBACK_PLANNED")
        if cacheability_plan.invalidation_reason_codes:
            reasons.extend(cacheability_plan.invalidation_reason_codes)
        return sorted(set(reasons))

    def _failure_decision(
        self,
        *,
        request: ModelRouteRequest,
        policy: OrchestrationEfficiencyPolicy,
        cacheability_plan: CacheabilityPlan,
        rejected_profile_ids: list[str],
        rejection_reason_codes: list[str],
        rejection_reasons: dict[str, int],
        approval_required_count: int,
        privacy_block_count: int,
        unknown_paid_cost_count: int,
    ) -> OrchestrationPreviewDecision:
        status = self._failure_status(rejection_reason_codes)
        fallback_plan = self._fallback_plan(
            request,
            None,
            [],
            bool(policy.fallback_allowed or request.routing_policy.fallback_allowed),
        )
        metric_summary = OptimizationMetricSummary(
            candidate_count=0,
            rejected_count=len(set(rejected_profile_ids)),
            rejected_count_by_reason=dict(sorted(rejection_reasons.items())),
            input_tokens=request.estimated_input_tokens,
            output_tokens=request.estimated_output_tokens,
            total_tokens=request.total_estimated_tokens,
            available_history_tokens=self._available_history_tokens(request),
            cache_eligible_count=1 if cacheability_plan.cache_eligible else 0,
            cache_invalidation_reason_count=len(cacheability_plan.invalidation_reason_codes),
            budget_status=status.value,
            approval_required_count=approval_required_count,
            privacy_block_count=privacy_block_count,
            unknown_paid_cost_count=unknown_paid_cost_count,
            observability_estimated_bytes=self._estimate_observability_bytes(request),
        )
        return OrchestrationPreviewDecision(
            decision_id=self._decision_id(request, policy, "none"),
            request_id=request.request_id,
            run_id=request.run_id,
            policy_id=policy.policy_id,
            status=status,
            cost_mode=policy.cost_mode,
            selected_profile_id=None,
            selected_model_id=None,
            candidate_profile_ids=[],
            rejected_profile_ids=rejected_profile_ids,
            reason_codes=sorted(set(rejection_reason_codes)),
            safe_message="Orchestration route preview denied by deterministic no-effect policy.",
            input_tokens=request.estimated_input_tokens,
            output_tokens=request.estimated_output_tokens,
            total_tokens=request.total_estimated_tokens,
            cacheability_plan=cacheability_plan,
            fallback_plan=fallback_plan,
            metric_summary=metric_summary,
            required_approval=status == OrchestrationPreviewStatus.approval_required,
            verification_required=policy.cost_mode == ModelRouteCostMode.critical,
            verifier_plan_ref=self._verifier_plan_ref(request, policy),
            event_ref=request.event_ref,
            trace_id=policy.trace_id or request.event_ref,
            correlation_id=policy.correlation_id or request.run_id,
        )

    def _metric_summary(
        self,
        *,
        request: ModelRouteRequest,
        selected_candidate: _EligibleCandidate,
        selected_score: RouteScoreBreakdown,
        candidate_count: int,
        rejected_profile_ids: list[str],
        rejection_reasons: dict[str, int],
        cacheability_plan: CacheabilityPlan,
        fallback_plan: FallbackPlan,
        approval_required_count: int,
        privacy_block_count: int,
        unknown_paid_cost_count: int,
        critical_verifier_planned_count: int,
    ) -> OptimizationMetricSummary:
        return OptimizationMetricSummary(
            candidate_count=candidate_count,
            rejected_count=len(set(rejected_profile_ids)),
            rejected_count_by_reason=dict(sorted(rejection_reasons.items())),
            selected_profile_id=selected_score.model_profile_id,
            estimated_cost_usd=selected_candidate.decision.estimated_cost,
            estimated_latency_ms=selected_candidate.decision.estimated_latency_ms,
            estimated_runtime_seconds=selected_candidate.runtime_seconds,
            input_tokens=request.estimated_input_tokens,
            output_tokens=request.estimated_output_tokens,
            total_tokens=request.total_estimated_tokens,
            available_history_tokens=self._available_history_tokens(request),
            cache_eligible_count=1 if cacheability_plan.cache_eligible else 0,
            cache_invalidation_reason_count=len(cacheability_plan.invalidation_reason_codes),
            budget_status="selected",
            approval_required_count=approval_required_count,
            fallback_planned_count=len(fallback_plan.fallback_profile_ids),
            critical_verifier_planned_count=critical_verifier_planned_count,
            privacy_block_count=privacy_block_count,
            unknown_paid_cost_count=unknown_paid_cost_count,
            observability_estimated_bytes=self._estimate_observability_bytes(request),
        )

    def _fallback_plan(
        self,
        request: ModelRouteRequest,
        primary_profile_id: str | None,
        fallback_profile_ids: list[str],
        fallback_allowed: bool,
    ) -> FallbackPlan:
        suffix = primary_profile_id or "none"
        return FallbackPlan(
            plan_ref=f"fallback-plan:{request.request_id}:{suffix}",
            run_id=request.run_id,
            fallback_allowed=fallback_allowed,
            primary_profile_id=primary_profile_id,
            fallback_profile_ids=fallback_profile_ids,
            fallback_reason_codes=["FALLBACK_PLANNED"] if fallback_profile_ids else [],
            safe_summary="No-effect fallback plan over eligible model route previews.",
        )

    def _default_cacheability_plan(self, request: ModelRouteRequest) -> CacheabilityPlan:
        return CacheabilityPlan(
            plan_ref=f"cache-plan:{request.request_id}:undeclared",
            run_id=request.run_id,
            data_classification=str(request.data_classification.classification),
            consent_refs=list(request.consent_refs),
            approval_refs=[request.approval_ref] if request.approval_ref else [],
            cache_eligible=False,
            invalidation_reason_codes=["CACHE_PLAN_NOT_DECLARED"],
        )

    def _cache_plan_applies(self, profile: ModelCapabilityProfile, plan: CacheabilityPlan) -> bool:
        return plan.model_profile_id in {None, profile.model_profile_id}

    def _cache_miss_penalty(self, profile: ModelCapabilityProfile, plan: CacheabilityPlan) -> float:
        if (
            plan.cache_eligible
            and plan.predicted_cache_hit_tokens > 0
            and self._cache_plan_applies(profile, plan)
        ):
            return 0.0
        return 1.0

    def _cache_reuse_ratio(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        plan: CacheabilityPlan,
    ) -> float:
        if not plan.cache_eligible or not self._cache_plan_applies(profile, plan):
            return 0.0
        net_reuse_tokens = max(
            0,
            plan.predicted_cache_hit_tokens - plan.predicted_cache_write_tokens,
        )
        return min(1.0, net_reuse_tokens / max(request.total_estimated_tokens, 1))

    def _cache_adjusted_cost(
        self,
        raw_cost: float,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        cache_reuse_ratio: float,
    ) -> float:
        if cache_reuse_ratio <= 0 or profile.cost_per_1k_input_tokens is None:
            return raw_cost
        reusable_input_tokens = min(
            request.estimated_input_tokens,
            int(round(request.total_estimated_tokens * cache_reuse_ratio)),
        )
        input_discount = reusable_input_tokens / 1000 * profile.cost_per_1k_input_tokens
        return max(0.0, raw_cost - input_discount)

    def _cache_adjusted_latency(
        self,
        raw_latency_ms: float,
        cache_reuse_ratio: float,
    ) -> float:
        latency_discount = min(0.5, cache_reuse_ratio * 0.5)
        return raw_latency_ms * (1 - latency_discount)

    def _cost_mode_rejection_reason(
        self,
        profile: ModelCapabilityProfile,
        policy: OrchestrationEfficiencyPolicy,
    ) -> str | None:
        if (
            policy.cost_mode == ModelRouteCostMode.cheap
            and profile.model_profile_id in policy.premium_profile_refs
        ):
            return "PREMIUM_PROFILE_DISALLOWED_IN_CHEAP_MODE"
        if policy.cost_mode == ModelRouteCostMode.local_private and profile.is_cloud and not policy.allow_cloud_in_local_private:
            return "CLOUD_BLOCKED_BY_LOCAL_PRIVATE_MODE"
        return None

    def _critical_denial_reason(self, request: ModelRouteRequest, policy: OrchestrationEfficiencyPolicy) -> str | None:
        if policy.cost_mode != ModelRouteCostMode.critical:
            return None
        if policy.critical_requires_approval and not request.approval_ref:
            return "CRITICAL_APPROVAL_REQUIRED"
        if policy.critical_requires_verifier and not self._verifier_plan_ref(request, policy):
            return "CRITICAL_VERIFIER_REQUIRED"
        return None

    def _preflight_rejection_reasons(
        self,
        request: ModelRouteRequest,
        policy: OrchestrationEfficiencyPolicy,
    ) -> list[str]:
        classification = str(request.data_classification.classification)
        if classification == "credential_secret":
            return ["CREDENTIAL_SECRET_NEVER_TO_MODEL"]
        context_reason = self._context_budget_rejection_reason(request)
        if context_reason:
            return [context_reason]
        critical_denial = self._critical_denial_reason(request, policy)
        if critical_denial:
            return [critical_denial]
        if not request.available_profiles:
            return ["NO_MODEL_CANDIDATE"]
        return []

    def _context_budget_rejection_reason(self, request: ModelRouteRequest) -> str | None:
        if request.context_budget is None:
            return None
        available_history_tokens = request.context_budget.available_history_tokens
        if available_history_tokens <= 0 and request.estimated_input_tokens > 0:
            return "CONTEXT_BUDGET_EXHAUSTED"
        if request.estimated_input_tokens > available_history_tokens:
            return "CONTEXT_BUDGET_INSUFFICIENT"
        return None

    def _verifier_plan_ref(self, request: ModelRouteRequest, policy: OrchestrationEfficiencyPolicy) -> str | None:
        if policy.verifier_plan_ref:
            return policy.verifier_plan_ref
        if policy.cost_mode == ModelRouteCostMode.critical:
            return f"verifier-plan:{request.request_id}:critical"
        return None

    def _quality_score(self, profile: ModelCapabilityProfile, policy: OrchestrationEfficiencyPolicy) -> float:
        return policy.profile_quality_scores.get(profile.model_profile_id, policy.default_quality_score)

    def _candidate_for_score(
        self,
        candidates: list[_EligibleCandidate],
        score: RouteScoreBreakdown | None,
    ) -> _EligibleCandidate | None:
        if score is None:
            return None
        for candidate in candidates:
            if candidate.profile.model_profile_id == score.model_profile_id:
                return candidate
        return None

    def _translate_rejection_reasons(self, reasons: list[str]) -> list[str]:
        translated = []
        for reason in reasons:
            if reason == "UNKNOWN_PAID_COST_REQUIRES_APPROVAL":
                translated.append(reason)
            else:
                translated.append(reason)
        return translated

    def _failure_status(self, reasons: list[str]) -> OrchestrationPreviewStatus:
        if any(reason in {"CRITICAL_APPROVAL_REQUIRED", "CLOUD_APPROVAL_REQUIRED"} or reason.startswith("APPROVAL_") for reason in reasons):
            return OrchestrationPreviewStatus.approval_required
        if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in reasons:
            return OrchestrationPreviewStatus.approval_required
        if any("PRIVACY" in reason or reason.startswith("CLOUD_BLOCKED") or reason.startswith("CREDENTIAL_SECRET") for reason in reasons):
            return OrchestrationPreviewStatus.privacy_blocked
        if any(reason in {"CONTEXT_TOO_SMALL", "CONTEXT_BUDGET_EXHAUSTED", "CONTEXT_BUDGET_INSUFFICIENT", "TRIM_CONTEXT_REQUIRED"} for reason in reasons):
            return OrchestrationPreviewStatus.context_too_small
        if any("BUDGET" in reason for reason in reasons):
            return OrchestrationPreviewStatus.budget_exceeded
        if "CAPABILITY_MISSING" in reasons:
            return OrchestrationPreviewStatus.capability_missing
        if "NO_MODEL_CANDIDATE" in reasons:
            return OrchestrationPreviewStatus.no_candidate
        if reasons:
            return OrchestrationPreviewStatus.denied
        return OrchestrationPreviewStatus.no_candidate

    def _available_history_tokens(self, request: ModelRouteRequest) -> int | None:
        if request.context_budget is None:
            return None
        return request.context_budget.available_history_tokens

    def _estimate_observability_bytes(self, request: ModelRouteRequest) -> int:
        return 256 + len(request.available_profiles) * 96 + len(request.required_capabilities) * 32

    def _record_reasons(self, destination: dict[str, int], reasons: list[str]) -> None:
        for reason in reasons:
            destination[reason] = destination.get(reason, 0) + 1

    def _reason_counts(self, reasons: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        self._record_reasons(counts, reasons)
        return counts

    def _decision_id(self, request: ModelRouteRequest, policy: OrchestrationEfficiencyPolicy, selected_ref: str) -> str:
        source = f"{request.request_id}:{request.run_id}:{policy.policy_id}:{policy.cost_mode}:{selected_ref}"
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        return f"orch_{digest}"
