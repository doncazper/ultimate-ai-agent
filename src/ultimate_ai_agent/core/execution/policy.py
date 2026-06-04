from ultimate_ai_agent.core.execution.enums import ExecutionStepMode
from ultimate_ai_agent.core.execution.validation import SAFE_STEP_MODES


def is_no_effect_step_mode(mode: ExecutionStepMode) -> bool:
    return mode in SAFE_STEP_MODES

