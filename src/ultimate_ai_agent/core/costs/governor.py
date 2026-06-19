import uuid
from typing import List

from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.decisions import CostDecision
from ultimate_ai_agent.core.costs.enums import BudgetStatus
from ultimate_ai_agent.core.costs.estimates import CostEstimate


class CostGovernor:
    def estimate_route_cost(self, route_request, profile) -> CostEstimate:
        input_tokens = route_request.estimated_input_tokens
        output_tokens = route_request.estimated_output_tokens
        input_rate = profile.cost_per_1k_input_tokens
        output_rate = profile.cost_per_1k_output_tokens
        unknown_cost = profile.is_cloud and (input_rate is None or output_rate is None)
        estimated_cost = None if unknown_cost else round(
            (input_tokens / 1000 * (input_rate or 0)) + (output_tokens / 1000 * (output_rate or 0)),
            6,
        )
        runtime_seconds = None
        if profile.estimated_tokens_per_second:
            runtime_seconds = round((input_tokens + output_tokens) / profile.estimated_tokens_per_second, 3)

        return CostEstimate(
            estimate_id=f"estimate_{uuid.uuid4().hex[:12]}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=estimated_cost,
            estimated_token_cost_usd=estimated_cost,
            estimated_runtime_seconds=runtime_seconds,
            estimated_observability_bytes=256,
            model_profile_id=profile.model_profile_id,
            provider_id=profile.provider_id,
            unknown_cost=unknown_cost,
        )

    def evaluate(self, estimate: CostEstimate, budgets: List[CostBudget]) -> CostDecision:
        if estimate.unknown_cost or estimate.estimated_cost_usd is None:
            return CostDecision(
                allowed=False,
                status=BudgetStatus.approval_required,
                estimate_id=estimate.estimate_id,
                reason_codes=["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"],
                safe_message="Cost estimate is unknown and requires approval before routing.",
                approval_required=True,
            )

        warnings: list[str] = []
        remaining_cost = None
        remaining_tokens = None
        for budget in budgets:
            denial = self._denial_reason(estimate, budget)
            if denial:
                if budget.hard_limit:
                    return CostDecision(
                        allowed=False,
                        status=BudgetStatus.denied,
                        budget_id=budget.budget_id,
                        estimate_id=estimate.estimate_id,
                        reason_codes=["HARD_BUDGET_EXCEEDED", denial],
                        safe_message="Budget check denied the route.",
                        remaining_cost_usd=remaining_cost,
                        remaining_tokens=remaining_tokens,
                    )
                warnings.extend(["SOFT_BUDGET_EXCEEDED", denial])
                continue
            warnings.extend(self._warning_reasons(estimate, budget))
            if budget.max_cost_usd is not None:
                remaining_cost = max(0.0, budget.max_cost_usd - estimate.estimated_cost_usd)
            if budget.max_total_tokens is not None:
                remaining_tokens = max(0, budget.max_total_tokens - estimate.total_tokens)

        if warnings:
            return CostDecision(
                allowed=True,
                status=BudgetStatus.warning,
                estimate_id=estimate.estimate_id,
                reason_codes=sorted(set(warnings)),
                safe_message="Budget check allowed with warning.",
                remaining_cost_usd=remaining_cost,
                remaining_tokens=remaining_tokens,
            )

        return CostDecision(
            allowed=True,
            status=BudgetStatus.allowed,
            estimate_id=estimate.estimate_id,
            reason_codes=["WITHIN_BUDGET"],
            safe_message="Budget check allowed.",
            remaining_cost_usd=remaining_cost,
            remaining_tokens=remaining_tokens,
        )

    def _denial_reason(self, estimate: CostEstimate, budget: CostBudget) -> str | None:
        checks = [
            (budget.max_cost_usd is not None and estimate.estimated_cost_usd is not None and estimate.estimated_cost_usd > budget.max_cost_usd, "COST_BUDGET_EXCEEDED"),
            (budget.max_input_tokens is not None and estimate.input_tokens > budget.max_input_tokens, "INPUT_TOKEN_BUDGET_EXCEEDED"),
            (budget.max_output_tokens is not None and estimate.output_tokens > budget.max_output_tokens, "OUTPUT_TOKEN_BUDGET_EXCEEDED"),
            (budget.max_total_tokens is not None and estimate.total_tokens > budget.max_total_tokens, "TOKEN_BUDGET_EXCEEDED"),
            (budget.max_runtime_seconds is not None and estimate.estimated_runtime_seconds is not None and estimate.estimated_runtime_seconds > budget.max_runtime_seconds, "RUNTIME_BUDGET_EXCEEDED"),
            (budget.max_local_memory_gb is not None and estimate.estimated_memory_gb is not None and estimate.estimated_memory_gb > budget.max_local_memory_gb, "MEMORY_BUDGET_EXCEEDED"),
            (budget.max_local_vram_gb is not None and estimate.estimated_vram_gb is not None and estimate.estimated_vram_gb > budget.max_local_vram_gb, "VRAM_BUDGET_EXCEEDED"),
        ]
        for failed, reason in checks:
            if failed:
                return reason
        return None

    def _warning_reasons(self, estimate: CostEstimate, budget: CostBudget) -> list[str]:
        reasons: list[str] = []
        threshold = budget.warning_threshold_percent / 100
        if budget.max_cost_usd is not None and estimate.estimated_cost_usd is not None:
            if estimate.estimated_cost_usd >= budget.max_cost_usd * threshold:
                reasons.append("COST_WARNING_THRESHOLD_REACHED")
        if budget.max_total_tokens is not None and estimate.total_tokens >= budget.max_total_tokens * threshold:
            reasons.append("TOKEN_WARNING_THRESHOLD_REACHED")
        return reasons
