import pytest
from ultimate_ai_agent.core.context_budget import (
    ContextBudget,
    validate_context_budget,
)

def test_context_budget_subtraction() -> None:
    budget = ContextBudget(
        model_context_limit=8000,
        system_prompt_tokens=1000,
        tool_schema_tokens=500,
        world_state_tokens=200,
        context_pack_tokens=300,
        completion_reserve_tokens=2000,
        safety_margin_tokens=1000
    )
    # Available should be: 8000 - (1000 + 500 + 200 + 300 + 2000 + 1000) = 8000 - 5000 = 3000
    assert budget.available_history_tokens == 3000
    assert validate_context_budget(budget) is True

def test_unknown_context_limit_fails_closed() -> None:
    budget = ContextBudget(
        model_context_limit=0,
        unknown_limit_fails_closed=True
    )
    with pytest.raises(ValueError, match="context limit is unknown and fail-closed is active"):
        validate_context_budget(budget)

    # Calling property should raise error
    with pytest.raises(ValueError, match="Context limit is unknown and fail-closed is active"):
        _ = budget.available_history_tokens

    # If fail closed is disabled, it should return a conservative default (less than or equal to default)
    budget.unknown_limit_fails_closed = False
    assert budget.available_history_tokens >= 0
