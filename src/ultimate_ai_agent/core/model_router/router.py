from dataclasses import dataclass
from typing import List

from ultimate_ai_agent.core.approvals import (
    ApprovalDecisionStatus,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    ApprovalValidationDecision,
    ApprovalValidationRequest,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.costs import (
    BudgetScope,
    BudgetStatus,
    CostBudget,
    CostGovernor,
)
from ultimate_ai_agent.core.model_router.decisions import (
    ModelRouteDecision,
    build_approval_validation_decision_ref,
)
from ultimate_ai_agent.core.model_router.enums import (
    ModelPrivacyClass,
    ModelRouteStatus,
)
from ultimate_ai_agent.core.model_router.profiles import ModelCapabilityProfile
from ultimate_ai_agent.core.model_router.requests import ModelRouteRequest


@dataclass(frozen=True)
class _Candidate:
    profile: ModelCapabilityProfile
    estimated_cost: float
    estimated_latency_ms: float
    warning_reason_codes: list[str]
    approval_validation_decision_ref: str | None = None


@dataclass(frozen=True)
class _PreparedRoutePolicy:
    classification: str
    required_capabilities: frozenset[str]
    allowed_provider_kinds: frozenset[str]
    forbidden_provider_kinds: frozenset[str]
    required_context_tokens: int
    context_budget_rejection_reason: str | None


class ModelRouter:
    def __init__(
        self,
        cost_governor: CostGovernor | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> None:
        self.cost_governor = cost_governor or CostGovernor()
        self.approval_authority = approval_authority

    def route(self, request: ModelRouteRequest) -> ModelRouteDecision:
        prepared = self._prepare_policy(request)
        if prepared.classification == "credential_secret":
            return self._decision(
                request,
                ModelRouteStatus.privacy_blocked,
                ["CREDENTIAL_SECRET_NEVER_TO_MODEL"],
                "Credential-secret data is never routed to a model.",
                prepared=prepared,
            )

        eligible: list[_Candidate] = []
        rejected: list[str] = []
        reasons: list[str] = []
        approval_required = False

        for profile in sorted(
            request.available_profiles, key=lambda item: item.model_profile_id
        ):
            profile_reasons = self._profile_rejection_reasons(
                request, profile, prepared
            )
            if profile_reasons:
                rejected.append(profile.model_profile_id)
                reasons.extend(profile_reasons)
                if any(
                    reason.startswith("APPROVAL_")
                    or reason == "CLOUD_APPROVAL_REQUIRED"
                    for reason in profile_reasons
                ):
                    approval_required = True
                continue

            approval_validation_decision_ref = None
            if self._approval_required_for_profile(request, profile, prepared):
                validation_request, decision = self._approval_validation(
                    request,
                    profile,
                )
                if not self._approval_decision_is_exact(decision, request):
                    rejected.append(profile.model_profile_id)
                    reasons.extend(
                        decision.reason_codes
                        if decision is not None
                        else ["APPROVAL_REF_UNVALIDATED"]
                    )
                    approval_required = True
                    continue
                approval_validation_decision_ref = (
                    build_approval_validation_decision_ref(
                        validation_request,
                        decision,
                    )
                )

            estimate = self.cost_governor.estimate_route_cost(request, profile)
            budgets = []
            if request.routing_policy.max_estimated_cost_usd is not None:
                budgets.append(
                    CostBudget(
                        budget_id=f"route_policy_{request.routing_policy.policy_id}",
                        scope=BudgetScope.run,
                        max_cost_usd=request.routing_policy.max_estimated_cost_usd,
                        hard_limit=request.routing_policy.max_estimated_cost_hard_limit,
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
                    warning_reason_codes=cost_decision.reason_codes
                    if cost_decision.status == BudgetStatus.warning
                    else [],
                    approval_validation_decision_ref=(approval_validation_decision_ref),
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
                prepared=prepared,
            )

        selected = min(
            eligible, key=lambda candidate: self._sort_key(request, candidate)
        )
        reason_codes = ["SELECTED_PROFILE", *selected.warning_reason_codes]
        if selected.approval_validation_decision_ref is not None:
            reason_codes.append("APPROVAL_VALIDATED")
        safe_message = (
            "Model route selected with policy warnings. No model execution was performed."
            if selected.warning_reason_codes
            else "Model route selected by deterministic policy. No model execution was performed."
        )
        return ModelRouteDecision(
            request_id=request.request_id,
            run_id=request.run_id,
            status=ModelRouteStatus.selected,
            selected_profile_id=selected.profile.model_profile_id,
            selected_model_id=selected.profile.model_id,
            candidate_profile_ids=[
                candidate.profile.model_profile_id for candidate in eligible
            ],
            rejected_profile_ids=sorted(set(rejected)),
            reason_codes=reason_codes,
            safe_message=safe_message,
            estimated_cost=selected.estimated_cost,
            estimated_latency_ms=selected.estimated_latency_ms,
            cost_mode=str(request.routing_policy.cost_mode)
            if request.routing_policy.cost_mode
            else None,
            trace_id=request.event_ref,
            correlation_id=request.run_id,
            privacy_notes=self._privacy_notes(request, selected.profile, prepared),
            required_approval=False,
            approval_validation_decision_ref=(
                selected.approval_validation_decision_ref
            ),
            consent_refs=request.consent_refs,
            event_ref=request.event_ref,
        )

    def _prepare_policy(self, request: ModelRouteRequest) -> _PreparedRoutePolicy:
        policy = request.routing_policy
        required = request.required_capabilities or policy.required_capabilities
        return _PreparedRoutePolicy(
            classification=self._classification(request),
            required_capabilities=frozenset(str(capability) for capability in required),
            allowed_provider_kinds=frozenset(
                str(kind) for kind in policy.allowed_provider_kinds
            ),
            forbidden_provider_kinds=frozenset(
                str(kind) for kind in policy.forbidden_provider_kinds
            ),
            required_context_tokens=self._required_context_tokens(request),
            context_budget_rejection_reason=self._context_budget_rejection_reason(
                request
            ),
        )

    def _profile_rejection_reasons(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        prepared: _PreparedRoutePolicy,
    ) -> List[str]:
        policy = request.routing_policy
        reasons: list[str] = []
        provider_kind = str(profile.provider_kind)
        capabilities = {str(capability) for capability in profile.capabilities}

        if not profile.enabled:
            reasons.append("PROFILE_DISABLED")
        if (
            prepared.allowed_provider_kinds
            and provider_kind not in prepared.allowed_provider_kinds
        ):
            reasons.append("PROVIDER_KIND_NOT_ALLOWED")
        if provider_kind in prepared.forbidden_provider_kinds:
            reasons.append("PROVIDER_KIND_FORBIDDEN")
        if not prepared.required_capabilities.issubset(capabilities):
            reasons.append("CAPABILITY_MISSING")
        if policy.require_structured_output and not profile.supports_structured_output:
            reasons.append("STRUCTURED_OUTPUT_REQUIRED")
        if policy.require_tool_support and not profile.supports_tools:
            reasons.append("TOOL_SUPPORT_REQUIRED")
        if profile.is_paid and not policy.allow_paid:
            reasons.append("PAID_MODEL_DISALLOWED")
        if profile.credential_ref and not request.credential_availability.get(
            profile.credential_ref, False
        ):
            reasons.append("CREDENTIAL_NOT_AVAILABLE")
        if prepared.context_budget_rejection_reason:
            reasons.append(prepared.context_budget_rejection_reason)
        if (
            profile.max_context_tokens is not None
            and profile.max_context_tokens < prepared.required_context_tokens
        ):
            reasons.append("CONTEXT_TOO_SMALL")
        if (
            policy.max_latency_ms is not None
            and profile.time_to_first_token_ms is not None
        ):
            if profile.time_to_first_token_ms > policy.max_latency_ms:
                reasons.append("LATENCY_TOO_HIGH")
        reasons.extend(self._privacy_rejections(request, profile, prepared))
        return reasons

    def _privacy_rejections(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        prepared: _PreparedRoutePolicy,
    ) -> list[str]:
        policy = request.routing_policy
        if not profile.is_cloud:
            return []
        if (
            policy.privacy_mode == ModelPrivacyClass.local_only
            or str(policy.privacy_mode) == "local_only"
        ):
            return ["CLOUD_BLOCKED_BY_PRIVACY_MODE"]
        if not policy.allow_cloud:
            return ["CLOUD_BLOCKED_BY_POLICY"]
        if prepared.classification in {
            "sensitive_personal",
            "regulated",
            "tcb_protected",
        }:
            if policy.require_human_approval_for_cloud:
                if not request.approval_ref:
                    return ["CLOUD_APPROVAL_REQUIRED"]
                approval_reasons = self._approval_rejection_reasons(request, profile)
                if approval_reasons:
                    return approval_reasons
        return []

    def _required_context_tokens(self, request: ModelRouteRequest) -> int:
        required = request.total_estimated_tokens
        if request.routing_policy.min_context_tokens:
            required = max(required, request.routing_policy.min_context_tokens)
        return required

    def _context_budget_rejection_reason(
        self, request: ModelRouteRequest
    ) -> str | None:
        if request.context_budget is None:
            return None
        available_history_tokens = request.context_budget.available_history_tokens
        if available_history_tokens <= 0 and request.estimated_input_tokens > 0:
            return "CONTEXT_BUDGET_EXHAUSTED"
        if request.estimated_input_tokens > available_history_tokens:
            return "CONTEXT_BUDGET_INSUFFICIENT"
        return None

    def _approval_rejection_reasons(
        self, request: ModelRouteRequest, profile: ModelCapabilityProfile
    ) -> list[str]:
        if not request.approval_ref:
            return ["CLOUD_APPROVAL_REQUIRED"]
        if request.approval_ref.startswith("approval_test_"):
            return ["APPROVAL_TEST_REF_DENIED"]
        if self.approval_authority is None:
            return ["APPROVAL_REF_UNVALIDATED"]
        _, decision = self._approval_validation(request, profile)
        if self._approval_decision_is_exact(decision, request):
            return []
        return (
            decision.reason_codes
            if decision is not None and decision.reason_codes
            else ["APPROVAL_REF_UNVALIDATED"]
        )

    def _approval_required_for_profile(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        prepared: _PreparedRoutePolicy,
    ) -> bool:
        return bool(
            profile.is_cloud
            and request.routing_policy.require_human_approval_for_cloud
            and prepared.classification
            in {"sensitive_personal", "regulated", "tcb_protected"}
        )

    def _approval_validation(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
    ) -> tuple[ApprovalValidationRequest | None, ApprovalValidationDecision | None]:
        if (
            not request.approval_ref
            or request.approval_ref.startswith("approval_test_")
            or self.approval_authority is None
        ):
            return None, None
        approval_request = LocalApprovalAuthority.request_for_model_route(
            request,
            subject_type=ApprovalSubjectType.model_route,
            subject_id=request.request_id,
            requested_action="route_cloud_model",
            resource_refs=[profile.model_profile_id],
            risk_level=ApprovalRiskLevel.high,
        )
        validation_request = approval_request.to_validation_request(
            request.approval_ref
        )
        return validation_request, self.approval_authority.validate(validation_request)

    @staticmethod
    def _approval_decision_is_exact(
        decision: ApprovalValidationDecision | None,
        request: ModelRouteRequest,
    ) -> bool:
        return bool(
            decision is not None
            and decision.allowed
            and decision.status == ApprovalDecisionStatus.approved.value
            and decision.approval_ref == request.approval_ref
            and decision.matched_grant_ref == request.approval_ref
            and "APPROVAL_VALIDATED" in decision.reason_codes
        )

    def _sort_key(
        self, request: ModelRouteRequest, candidate: _Candidate
    ) -> tuple[int, float, float, str]:
        local_rank = 0
        if request.routing_policy.prefer_local:
            local_rank = 0 if not candidate.profile.is_cloud else 1
        return (
            local_rank,
            candidate.estimated_cost,
            candidate.estimated_latency_ms,
            candidate.profile.model_profile_id,
        )

    def _failure_status(
        self, reasons: list[str], approval_required: bool
    ) -> ModelRouteStatus:
        if approval_required or any(
            reason.startswith("APPROVAL_") or reason == "CLOUD_APPROVAL_REQUIRED"
            for reason in reasons
        ):
            return ModelRouteStatus.approval_required
        if any(
            "PRIVACY" in reason
            or reason.startswith("CLOUD_BLOCKED")
            or reason.startswith("CREDENTIAL_SECRET")
            for reason in reasons
        ):
            return ModelRouteStatus.privacy_blocked
        if any(
            reason
            in {
                "CONTEXT_TOO_SMALL",
                "CONTEXT_BUDGET_EXHAUSTED",
                "CONTEXT_BUDGET_INSUFFICIENT",
            }
            for reason in reasons
        ):
            return ModelRouteStatus.context_too_small
        if any("BUDGET" in reason for reason in reasons):
            return ModelRouteStatus.budget_exceeded
        if any(reason == "CAPABILITY_MISSING" for reason in reasons):
            return ModelRouteStatus.capability_missing
        if reasons:
            return ModelRouteStatus.denied
        return ModelRouteStatus.no_candidate

    def _privacy_notes(
        self,
        request: ModelRouteRequest,
        profile: ModelCapabilityProfile,
        prepared: _PreparedRoutePolicy | None = None,
    ) -> list[str]:
        classification = (
            prepared.classification
            if prepared is not None
            else self._classification(request)
        )
        notes = [f"data_classification:{classification}"]
        notes.append(
            "cloud_metadata_only" if profile.is_cloud else "local_metadata_only"
        )
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
        prepared: _PreparedRoutePolicy | None = None,
    ) -> ModelRouteDecision:
        classification = (
            prepared.classification
            if prepared is not None
            else self._classification(request)
        )
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
            cost_mode=str(request.routing_policy.cost_mode)
            if request.routing_policy.cost_mode
            else None,
            trace_id=request.event_ref,
            correlation_id=request.run_id,
            privacy_notes=[f"data_classification:{classification}"],
            required_approval=required_approval,
            consent_refs=request.consent_refs,
            event_ref=request.event_ref,
        )
