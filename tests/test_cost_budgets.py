from pydantic import ValidationError

from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate, ResourceKind


def test_cost_budget_contract_tracks_money_tokens_and_resources() -> None:
    budget = CostBudget(
        budget_id="budget_run",
        scope=BudgetScope.run,
        max_cost_usd=1.50,
        max_input_tokens=10_000,
        max_output_tokens=5_000,
        max_total_tokens=12_000,
        max_runtime_seconds=30,
        max_local_memory_gb=16,
        max_local_vram_gb=8,
    )

    assert budget.scope == BudgetScope.run
    assert budget.warning_threshold_percent == 80
    assert ResourceKind.tokens.value == "tokens"


def test_cost_estimate_total_tokens_is_validated() -> None:
    estimate = CostEstimate(
        estimate_id="estimate_1",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.01,
    )

    assert estimate.total_tokens == 150


def test_cost_budget_rejects_unknown_fields() -> None:
    payload = {"budget_id": "budget_extra", "scope": BudgetScope.run, "unexpected": True}

    try:
        CostBudget(**payload)
    except ValidationError as exc:
        assert "extra" in str(exc).lower()
    else:
        raise AssertionError("CostBudget accepted an unknown field")
