from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryRecord,
    MemoryScope,
    MemorySensitivity,
    MemoryStatus,
    MemoryStore,
    MemoryType,
)


def record(memory_id: str, content: str) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=MemoryType.decision,
        scope=MemoryScope.project,
        scope_id="proj_123",
        project_id="proj_123",
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.project_private,
        content=content,
    )


def test_correction_links_old_and_new_records():
    store = MemoryStore()
    store.add_memory(record("mem_old", "Old decision."))
    corrected = record("mem_new", "Corrected decision.")

    store.correct_memory("mem_old", corrected, reason="user correction")

    assert store.get_memory("mem_old").status == MemoryStatus.corrected
    assert store.get_memory("mem_old").superseded_by == "mem_new"
    assert store.get_memory("mem_new").correction_of == "mem_old"
    assert store.get_memory("mem_new").metadata["correction_reason"] == "user correction"
