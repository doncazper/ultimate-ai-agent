from ultimate_ai_agent.core.context_budget import (
    ContextBudget,
    calibrate_tokens,
)

def test_token_calibration_increases() -> None:
    budget = ContextBudget(
        model_context_limit=8000,
        token_calibration_factor=1.0
    )
    # Underestimate: actual (200) > estimate (100)
    event = calibrate_tokens(
        budget=budget,
        run_id="run_cal",
        estimated_tokens=100,
        actual_tokens=200,
        calibration_event_id="cal_1"
    )
    assert event is not None
    assert budget.token_calibration_factor == 2.0
    assert event.new_calibration_factor == 2.0

def test_token_calibration_no_decrease() -> None:
    budget = ContextBudget(
        model_context_limit=8000,
        token_calibration_factor=1.5
    )
    # Overestimate: actual (50) < estimate (100) -> ratio = 0.5 < 1.5
    event = calibrate_tokens(
        budget=budget,
        run_id="run_cal",
        estimated_tokens=100,
        actual_tokens=50,
        calibration_event_id="cal_2"
    )
    assert event is None
    # Factor must stay at 1.5
    assert budget.token_calibration_factor == 1.5
