import pytest

from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryRecord,
    MemoryScope,
    MemorySensitivity,
    MemoryType,
    validate_memory_record,
)


def test_credential_secret_memory_is_rejected():
    record = MemoryRecord(
        memory_id="mem_secret",
        memory_type=MemoryType.semantic,
        scope=MemoryScope.user,
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.credential_secret,
        content="Store an API key reference only.",
    )

    with pytest.raises(ValueError, match="credential_secret"):
        validate_memory_record(record)


def test_raw_secret_content_is_rejected():
    record = MemoryRecord(
        memory_id="mem_raw_secret",
        memory_type=MemoryType.semantic,
        scope=MemoryScope.user,
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.user_private,
        content="api_key='abcdefghijklmnop'",
    )

    with pytest.raises(ValueError, match="secret"):
        validate_memory_record(record)
