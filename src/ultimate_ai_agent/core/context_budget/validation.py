from ultimate_ai_agent.core.context_budget.models import ContextBudget

def validate_context_budget(budget: ContextBudget) -> bool:
    """Validate that context budget parameters are consistent.

    Returns True if valid, raises ValueError if inconsistent or violates constraints.
    """
    if budget.model_context_limit <= 0 and budget.unknown_limit_fails_closed:
        raise ValueError("Cannot calculate budget: context limit is unknown and fail-closed is active.")
    
    if budget.token_calibration_factor < 1.0:
        raise ValueError("Token calibration factor must be >= 1.0.")
        
    return True
