from pydantic import ValidationError

from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryRecord,
    MemoryScope,
    MemorySensitivity,
    MemorySourceRef,
    MemoryStatus,
    MemoryType,
)


def test_user_provided_memory_can_be_source_free() -> None:
    record = MemoryRecord(
        memory_id="mem_user_pref",
        memory_type=MemoryType.preference,
        scope=MemoryScope.user,
        user_id="user_123",
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.user_private,
        content="User prefers concise release summaries.",
    )

    assert record.source_refs == []
    assert record.status == MemoryStatus.active


def test_non_user_memory_requires_source_ref() -> None:
    try:
        MemoryRecord(
            memory_id="mem_project_decision",
            memory_type=MemoryType.decision,
            scope=MemoryScope.project,
            project_id="proj_123",
            authority=MemoryAuthority.canonical_file_derived,
            sensitivity=MemorySensitivity.project_private,
            content="Project uses FastAPI for the API boundary.",
        )
    except ValidationError as exc:
        assert "source_refs" in str(exc)
    else:
        raise AssertionError("Expected source_refs validation failure")


def test_memory_record_can_reference_file_source() -> None:
    record = MemoryRecord(
        memory_id="mem_file_source",
        memory_type=MemoryType.artifact_summary,
        scope=MemoryScope.project,
        project_id="proj_123",
        authority=MemoryAuthority.canonical_file_derived,
        sensitivity=MemorySensitivity.project_private,
        content="The roadmap says M4 implements Memory Service and File Manager.",
        source_refs=[
            MemorySourceRef(
                source_id="docs/canonical/09_roadmap.md",
                source_type="file",
                file_ref="file_roadmap",
                locator="line:148",
                trust_level="canonical",
            )
        ],
    )

    assert record.source_refs[0].file_ref == "file_roadmap"
