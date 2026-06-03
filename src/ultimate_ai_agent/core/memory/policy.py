from ultimate_ai_agent.core.memory.provider import MemoryWriteRequest
from ultimate_ai_agent.core.memory.validation import validate_memory_write_request


def evaluate_memory_write_policy(request: MemoryWriteRequest):
    """Evaluate M24 reviewed-write policy without storing anything."""

    return validate_memory_write_request(request)
