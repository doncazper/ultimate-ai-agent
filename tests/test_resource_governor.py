from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostDecision, CostEstimate, CostGovernor


def test_resource_governor_blocks_local_memory_over_budget():
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="estimate_memory",
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
            estimated_cost_usd=0,
            estimated_memory_gb=32,
        ),
        [CostBudget(budget_id="budget_memory", scope=BudgetScope.run, max_local_memory_gb=16)],
    )

    assert decision.allowed is False
    assert decision.status == BudgetStatus.denied
    assert "MEMORY_BUDGET_EXCEEDED" in decision.reason_codes


def test_cost_decision_is_deterministic_contract():
    decision = CostDecision(
        decision_id="cost_decision_1",
        allowed=True,
        status=BudgetStatus.allowed,
        reason_codes=["WITHIN_BUDGET"],
        safe_message="Budget check allowed.",
    )

    assert decision.model_dump(mode="json")["status"] == "allowed"
