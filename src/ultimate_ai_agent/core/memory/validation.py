from ultimate_ai_agent.core.memory.enums import MemorySensitivity
from ultimate_ai_agent.core.memory.records import MemoryRecord
from ultimate_ai_agent.core.memory.redaction import memory_contains_secret


def validate_memory_record(record: MemoryRecord) -> bool:
    if record.sensitivity == MemorySensitivity.credential_secret:
        raise ValueError("credential_secret memories are rejected by default.")
    if memory_contains_secret(record.model_dump()):
        raise ValueError("Memory record contains secret-like content.")
    return True
