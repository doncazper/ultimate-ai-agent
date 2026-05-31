from typing import Optional
from ultimate_ai_agent.core.context_budget.models import ContextBudget, TokenCalibrationEvent

def calibrate_tokens(
    budget: ContextBudget,
    run_id: str,
    estimated_tokens: int,
    actual_tokens: int,
    calibration_event_id: str
) -> Optional[TokenCalibrationEvent]:
    """Calculate and apply token calibration factor updates.

    Rule:
    - Calibration factor can increase when actual tokens exceed estimate.
    - Calibration factor should not decrease automatically.
    """
    if estimated_tokens <= 0:
        return None
        
    ratio = actual_tokens / estimated_tokens
    if ratio > budget.token_calibration_factor:
        old_factor = budget.token_calibration_factor
        budget.token_calibration_factor = max(old_factor, ratio)
        return TokenCalibrationEvent(
            event_id=calibration_event_id,
            run_id=run_id,
            estimated_tokens=estimated_tokens,
            actual_tokens=actual_tokens,
            new_calibration_factor=budget.token_calibration_factor
        )
    return None
