from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.estimates import CostEstimate


def validate_cost_budget(budget: CostBudget) -> bool:
    if budget.expires_at and budget.expires_at <= budget.created_at:
        raise ValueError("CostBudget expires_at must be after created_at.")
    return True


def validate_cost_estimate(estimate: CostEstimate) -> bool:
    if estimate.total_tokens != estimate.input_tokens + estimate.output_tokens:
        raise ValueError("CostEstimate total_tokens must match input and output tokens.")
    return True
