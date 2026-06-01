from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryScope,
    MemorySensitivity,
    MemorySourceRef,
    MemoryStore,
    MemoryType,
    MemoryWriteDisposition,
    MemoryWriteRequest,
)


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
        workspace_id="workspace_123",
        project_id="proj_123",
    )


def test_write_memory_requires_consent_for_sensitive_data():
    store = MemoryStore()
    request = MemoryWriteRequest(
        request_id="mwr_sensitive",
        run_id="run_123",
        actor_context=actor(),
        memory_type=MemoryType.semantic,
        scope=MemoryScope.user,
        user_id="user_123",
        content="User disclosed a sensitive personal preference.",
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.sensitive_personal,
        idempotency_key="idem_sensitive",
    )

    decision = store.write_memory(request)

    assert decision.allowed is False
    assert decision.disposition == MemoryWriteDisposition.reject
    assert "CONSENT_REQUIRED" in decision.reason_codes


def test_write_memory_is_idempotent_for_same_key():
    store = MemoryStore()
    request = MemoryWriteRequest(
        request_id="mwr_pref",
        run_id="run_123",
        actor_context=actor(),
        memory_type=MemoryType.preference,
        scope=MemoryScope.user,
        user_id="user_123",
        content="User prefers short final answers.",
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.user_private,
        idempotency_key="idem_pref",
        consent_ref="consent_123",
    )

    first = store.write_memory(request)
    second = store.write_memory(request)

    assert first.allowed is True
    assert second.allowed is True
    assert first.memory_id == second.memory_id
    assert len(store.list_memories(scope=MemoryScope.user)) == 1


def test_non_user_write_requires_source_ref():
    store = MemoryStore()
    request = MemoryWriteRequest(
        request_id="mwr_source",
        run_id="run_123",
        actor_context=actor(),
        memory_type=MemoryType.decision,
        scope=MemoryScope.project,
        project_id="proj_123",
        content="The project uses source-linked memory.",
        authority=MemoryAuthority.canonical_file_derived,
        sensitivity=MemorySensitivity.project_private,
        idempotency_key="idem_source",
    )

    decision = store.write_memory(request)

    assert decision.allowed is False
    assert "SOURCE_REF_REQUIRED" in decision.reason_codes


def test_active_memory_can_be_written_with_source_ref():
    store = MemoryStore()
    request = MemoryWriteRequest(
        request_id="mwr_project",
        run_id="run_123",
        actor_context=actor(),
        memory_type=MemoryType.decision,
        scope=MemoryScope.project,
        project_id="proj_123",
        content="M4 memory must be source linked.",
        source_refs=[MemorySourceRef(source_id="event_123", source_type="event", event_ref="event_123")],
        authority=MemoryAuthority.event_ledger_derived,
        sensitivity=MemorySensitivity.project_private,
        idempotency_key="idem_project",
    )

    decision = store.write_memory(request)

    assert decision.allowed is True
    assert store.get_memory(decision.memory_id).content == "M4 memory must be source linked."
