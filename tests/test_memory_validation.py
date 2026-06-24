import pytest

from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryProvenance,
    MemoryRecord,
    MemoryScope,
    MemorySensitivity,
    MemorySourceRef,
    MemoryType,
    validate_memory_record,
)


def test_credential_secret_memory_is_rejected() -> None:
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


def test_raw_secret_content_is_rejected() -> None:
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


def test_memory_record_rejects_nested_unsafe_source_provenance() -> None:
    record = MemoryRecord(
        memory_id="mem_nested_path",
        memory_type=MemoryType.semantic,
        scope=MemoryScope.project,
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.project_private,
        content="Reviewed summary only.",
        source_refs=[
            MemorySourceRef(
                source_ref="source-ref:manual-note:nested-path",
                source_kind="manual_note",
                source_uri="/Users/example/private-note.md",
            )
        ],
    )

    with pytest.raises(ValueError, match="unsafe provenance"):
        validate_memory_record(record)


def test_memory_record_rejects_nested_unsafe_provenance_without_echoing_path() -> None:
    record = MemoryRecord(
        memory_id="mem_nested_provenance",
        memory_type=MemoryType.semantic,
        scope=MemoryScope.project,
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.project_private,
        content="Reviewed summary only.",
        provenance=MemoryProvenance(
            provenance_id="provenance-ref:manual-note:nested",
            source_refs=[
                MemorySourceRef(
                    source_ref="source-ref:manual-note:nested",
                    source_kind="manual_note",
                    locator="/home/example/private-note.md",
                )
            ],
        ),
    )

    with pytest.raises(ValueError) as exc_info:
        validate_memory_record(record)

    assert "unsafe provenance" in str(exc_info.value)
    assert "private-note" not in str(exc_info.value)
