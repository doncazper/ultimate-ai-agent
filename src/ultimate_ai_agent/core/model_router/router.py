from dataclasses import dataclass
from typing import List

from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostGovernor
from ultimate_ai_agent.core.model_router.decisions import ModelRouteDecision
from ultimate_ai_agent.core.model_router.enums import ModelPrivacyClass, ModelRouteStatus
from ultimate_ai_agent.core.model_router.profiles import ModelCapabilityProfile
from ultimate_ai_agent.core.model_router.requests import ModelRouteRequest


@dataclass(frozen=True)
class _Candidate:
    profile: ModelCapabilityProfile
    estimated_cost: float
    estimated_latency_ms: float


class ModelRouter:
    def __init__(self, cost_governor: CostGovernor | None = None):
        self.cost_governor = cost_governor or CostGovernor()

    def route(self, request: ModelRouteRequest) -> ModelRouteDecision:
        if self._classification(request) == "credential_secret":
            return self._decision(
                request,
                ModelRouteStatus.privacy_blocked,
                ["CREDENTIAL_SECRET_NEVER_TO_MODEL"],
                "Credential-secret data is never routed to a model.",
            )

        eligible: list[_Candidate] = []
        rejected: list[str] = []
        reasons: list[str] = []
        approval_required = False

        for profile in sorted(request.available_profiles, key=lambda item: item.model_profile_id):
            profile_reasons = self._profile_rejection_reasons(request, profile)
            if profile_reasons:
                rejected.append(profile.model_profile_id)
                reasons.extend(profile_reasons)
                if "CLOUD_APPROVAL_REQUIRED" in profile_reasons:
                    approval_required = True
                continue

            estimate = self.cost_governor.estimate_route_cost(request, profile)
            budgets = []
            if request.routing_policy.max_estimated_cost_usd is not None:
                budgets.append(
                    CostBudget(
                        budget_id=f"route_policy_{request.routing_policy.policy_id}",
                        scope=BudgetScope.run,
                        max_cost_usd=request.routing_policy.max_estimated_cost_usd,
                    )
                )
            cost_decision = self.cost_governor.evaluate(estimate, budgets)
            if cost_decision.status == BudgetStatus.approval_required:
                rejected.append(profile.model_profile_id)
                reasons.extend(cost_decision.reason_codes)
                approval_required = True
                continue
            if not cost_decision.allowed:
                rejected.append(profile.model_profile_id)
                reasons.extend(cost_decision.reason_codes)
                continue

            eligible.append(
                _Candidate(
                    profile=profile,
                    estimated_cost=estimate.estimated_cost_usd or 0.0,
                    estimated_latency_ms=profile.time_to_first_token_ms or 0.0,
                )
            )

        if not eligible:
            return self._decision(
                request,
                self._failure_status(reasons, approval_required),
                sorted(set(reasons)) or ["NO_MODEL_CANDIDATE"],
                "No model profile matched the routing policy.",
                rejected_profile_ids=sorted(set(rejected)),
                required_approval=approval_required,
            )

        selected = sorted(eligible, key=lambda candidate: self._sort_key(request, candidate))[0]
        return ModelRouteDecision(
            request_id=request.request_id,
            run_id=request.run_id,
            status=ModelRouteStatus.selected,
            selected_profile_id=selected.profile.model_profile_id,
            selected_model_id=selected.profile.model_id,
            candidate_profile_ids=[candidate.profile.model_profile_id for candidate in eligible],
            rejected_profile_ids=sorted(set(rejected)),
            reason_codes=["SELECTED_PROFILE"],
            safe_message="Model route selected by deterministic policy. No model execution was performed.",
            estimated_cost=selected.estimated_cost,
            estimated_latency_ms=selected.estimated_latency_ms,
            privacy_notes=self._privacy_notes(request, selected.profile),
            required_approval=False,
            consent_refs=request.consent_refs,
            event_ref=request.event_ref,
        )

    def _profile_rejection_reasons(self, request: ModelRouteRequest, profile: ModelCapabilityProfile) -> List[str]:
        policy = request.routing_policy
        reasons: list[str] = []
        provider_kind = str(profile.provider_kind)
        required = set(request.required_capabilities or policy.required_capabilities)
        capabilities = {str(capability) for capability in profile.capabilities}

        if not profile.enabled:
            reasons.append("PROFILE_DISABLED")
        if policy.allowed_provider_kinds and provider_kind not in {str(kind) for kind in policy.allowed_provider_kinds}:
            reasons.append("PROVIDER_KIND_NOT_ALLOWED")
        if provider_kind in {str(kind) for kind in policy.forbidden_provider_kinds}:
            reasons.append("PROVIDER_KIND_FORBIDDEN")
        if not {str(capability) for capability in required}.issubset(capabilities):
            reasons.append("CAPABILITY_MISSING")
        if policy.require_structured_output and not profile.supports_structured_output:
            reasons.append("STRUCTURED_OUTPUT_REQUIRED")
        if policy.require_tool_support and not profile.supports_tools:
            reasons.append("TOOL_SUPPORT_REQUIRED")
        if profile.is_paid and not policy.allow_paid:
            reasons.append("PAID_MODEL_DISALLOWED")
        if profile.credential_ref and not request.credential_availability.get(profile.credential_ref, False):
            reasons.append("CREDENTIAL_NOT_AVAILABLE")
        if profile.max_context_tokens is not None and profile.max_context_tokens < self._required_context_tokens(request):
            reasons.append("CONTEXT_TOO_SMALL")
        if policy.max_latency_ms is not None and profile.time_to_first_token_ms is not None:
            if profile.time_to_first_token_ms > policy.max_latency_ms:
                reasons.append("LATENCY_TOO_HIGH")
        reasons.extend(self._privacy_rejections(request, profile))
        return reasons

    def _privacy_rejections(self, request: ModelRouteRequest, profile: ModelCapabilityProfile) -> list[str]:
        policy = request.routing_policy
        classification = self._classification(request)
        if not profile.is_cloud:
            return []
        if policy.privacy_mode == ModelPrivacyClass.local_only or str(policy.privacy_mode) == "local_only":
            return ["CLOUD_BLOCKED_BY_PRIVACY_MODE"]
        if not policy.allow_cloud:
            return ["CLOUD_BLOCKED_BY_POLICY"]
        if classification in {"sensitive_personal", "regulated", "tcb_protected"}:
            if policy.require_human_approval_for_cloud and not request.approval_ref:
                return ["CLOUD_APPROVAL_REQUIRED"]
        return []

    def _required_context_tokens(self, request: ModelRouteRequest) -> int:
        required = request.total_estimated_tokens
        if request.routing_policy.min_context_tokens:
            required = max(required, request.routing_policy.min_context_tokens)
        if request.context_budget is not None:
            required = max(required, request.context_budget.model_context_limit)
        return required

    def _sort_key(self, request: ModelRouteRequest, candidate: _Candidate) -> tuple[int, float, float, str]:
        local_rank = 0
        if request.routing_policy.prefer_local:
            local_rank = 0 if not candidate.profile.is_cloud else 1
        return (
            local_rank,
            candidate.estimated_cost,
            candidate.estimated_latency_ms,
            candidate.profile.model_profile_id,
        )

    def _failure_status(self, reasons: list[str], approval_required: bool) -> ModelRouteStatus:
        if approval_required:
            return ModelRouteStatus.approval_required
        if any("PRIVACY" in reason or reason.startswith("CLOUD_BLOCKED") or reason.startswith("CREDENTIAL_SECRET") for reason in reasons):
            return ModelRouteStatus.privacy_blocked
        if any(reason == "CONTEXT_TOO_SMALL" for reason in reasons):
            return ModelRouteStatus.context_too_small
        if any("BUDGET" in reason for reason in reasons):
            return ModelRouteStatus.budget_exceeded
        if any(reason == "CAPABILITY_MISSING" for reason in reasons):
            return ModelRouteStatus.capability_missing
        if reasons:
            return ModelRouteStatus.denied
        return ModelRouteStatus.no_candidate

    def _privacy_notes(self, request: ModelRouteRequest, profile: ModelCapabilityProfile) -> list[str]:
        notes = [f"data_classification:{self._classification(request)}"]
        notes.append("cloud_metadata_only" if profile.is_cloud else "local_metadata_only")
        return notes

    def _classification(self, request: ModelRouteRequest) -> str:
        return str(request.data_classification.classification)

    def _decision(
        self,
        request: ModelRouteRequest,
        status: ModelRouteStatus,
        reason_codes: list[str],
        safe_message: str,
        rejected_profile_ids: list[str] | None = None,
        required_approval: bool = False,
    ) -> ModelRouteDecision:
        return ModelRouteDecision(
            request_id=request.request_id,
            run_id=request.run_id,
            status=status,
            selected_profile_id=None,
            selected_model_id=None,
            candidate_profile_ids=[],
            rejected_profile_ids=rejected_profile_ids or [],
            reason_codes=reason_codes,
            safe_message=safe_message,
            privacy_notes=[f"data_classification:{self._classification(request)}"],
            required_approval=required_approval,
            consent_refs=request.consent_refs,
            event_ref=request.event_ref,
        )
