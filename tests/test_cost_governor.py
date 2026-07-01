from tests.m7_helpers import cloud_profile, local_profile, route_request
from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostGovernor, CostEstimate


def test_cost_governor_estimates_route_cost_from_profile_rates() -> None:
    estimate = CostGovernor().estimate_route_cost(
        route_request(profiles=[cloud_profile()]),
        cloud_profile(cost_per_1k_input_tokens=0.01, cost_per_1k_output_tokens=0.03),
    )

    assert estimate.input_tokens == 1000
    assert estimate.output_tokens == 500
    assert estimate.total_tokens == 1500
    assert estimate.estimated_cost_usd == 0.025


def test_over_hard_budget_is_denied() -> None:
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="estimate_over",
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            estimated_cost_usd=2.00,
        ),
        [CostBudget(budget_id="budget_run", scope=BudgetScope.run, max_cost_usd=1.00)],
    )

    assert decision.allowed is False
    assert decision.status == BudgetStatus.denied
    assert "COST_BUDGET_EXCEEDED" in decision.reason_codes


def test_warning_threshold_allows_with_warning_for_soft_limit() -> None:
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="estimate_warn",
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            estimated_cost_usd=0.90,
        ),
        [
            CostBudget(
                budget_id="budget_soft",
                scope=BudgetScope.run,
                max_cost_usd=1.00,
                warning_threshold_percent=80,
                hard_limit=False,
            )
        ],
    )

    assert decision.allowed is True
    assert decision.status == BudgetStatus.warning
    assert "COST_WARNING_THRESHOLD_REACHED" in decision.reason_codes


def test_soft_budget_overage_allows_with_warning() -> None:
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="estimate_soft_over",
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            estimated_cost_usd=2.00,
        ),
        [
            CostBudget(
                budget_id="budget_soft_over",
                scope=BudgetScope.run,
                max_cost_usd=1.00,
                hard_limit=False,
            )
        ],
    )

    assert decision.allowed is True
    assert decision.status == BudgetStatus.warning
    assert "SOFT_BUDGET_EXCEEDED" in decision.reason_codes
    assert "COST_BUDGET_EXCEEDED" in decision.reason_codes
    assert decision.safe_message == "Budget check allowed with warning."


def test_soft_budget_overage_does_not_bypass_later_hard_budget_denial() -> None:
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="estimate_soft_then_hard",
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            estimated_cost_usd=2.00,
        ),
        [
            CostBudget(
                budget_id="budget_soft_over",
                scope=BudgetScope.run,
                max_cost_usd=1.00,
                hard_limit=False,
            ),
            CostBudget(
                budget_id="budget_hard_over",
                scope=BudgetScope.run,
                max_cost_usd=1.50,
                hard_limit=True,
            ),
        ],
    )

    assert decision.allowed is False
    assert decision.status == BudgetStatus.denied
    assert "HARD_BUDGET_EXCEEDED" in decision.reason_codes


def test_unknown_paid_cost_requires_approval() -> None:
    estimate = CostGovernor().estimate_route_cost(
        route_request(profiles=[cloud_profile()]),
        cloud_profile(cost_per_1k_input_tokens=None, cost_per_1k_output_tokens=None),
    )
    decision = CostGovernor().evaluate(estimate, [])

    assert decision.allowed is False
    assert decision.status == BudgetStatus.approval_required
    assert decision.approval_required is True


def test_provider_invocation_unknown_paid_cost_blocks_before_budget_authority() -> None:
    decision = CostGovernor().evaluate(
        CostEstimate(
            estimate_id="cost-estimate-ref:provider-runtime:unknown",
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            estimated_cost_usd=None,
            model_profile_id="model-ref:provider-runtime:unknown-cost",
            provider_id="provider-ref:provider-runtime:unknown-cost",
            unknown_cost=True,
        ),
        [
            CostBudget(
                budget_id="budget-decision-ref:provider-runtime:tiny",
                scope=BudgetScope.provider,
                scope_id="provider-ref:provider-runtime:unknown-cost",
                max_cost_usd=1.00,
            )
        ],
    )

    assert decision.allowed is False
    assert decision.status == BudgetStatus.approval_required
    assert decision.reason_codes == ["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"]


def test_local_zero_cost_route_still_checks_token_budget() -> None:
    estimate = CostGovernor().estimate_route_cost(route_request(profiles=[local_profile()]), local_profile())
    decision = CostGovernor().evaluate(
        estimate,
        [CostBudget(budget_id="budget_tokens", scope=BudgetScope.run, max_total_tokens=1000)],
    )

    assert estimate.estimated_cost_usd == 0
    assert decision.allowed is False
    assert "TOKEN_BUDGET_EXCEEDED" in decision.reason_codes
