from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.memory import (
    MemoryAuthority,
    MemoryReadRequest,
    MemoryRetrievalMode,
    MemoryRetrievalPolicy,
    MemoryScope,
    MemorySensitivity,
    MemoryStore,
    MemoryType,
    LegacyMemoryWriteRequest as MemoryWriteRequest,
)


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
        workspace_id="workspace_123",
        project_id="proj_123",
    )


def write(store, content, *, scope=MemoryScope.project, scope_id="proj_123", tags=None):
    return store.write_memory(
        MemoryWriteRequest(
            request_id=f"mwr_{len(store.list_memories())}",
            run_id="run_123",
            actor_context=actor(),
            memory_type=MemoryType.decision,
            scope=scope,
            scope_id=scope_id,
            project_id=scope_id,
            content=content,
            tags=tags or [],
            authority=MemoryAuthority.user_provided,
            sensitivity=MemorySensitivity.project_private,
            idempotency_key=f"idem_{len(store.list_memories())}",
            consent_ref="consent_123",
        )
    )


def test_keyword_retrieval_is_deterministic_and_scope_filtered():
    store = MemoryStore()
    write(store, "FastAPI is the API boundary for this project.", tags=["api"])
    write(store, "Memory uses source-linked recall below canonical files.", tags=["memory"])
    write(store, "Another workspace uses a different stack.", scope_id="other")

    decision = store.search(
        MemoryReadRequest(
            request_id="mrr_api",
            run_id="run_123",
            actor_context=actor(),
            query="api fastapi boundary",
            scope=MemoryScope.project,
            scope_id="proj_123",
            max_results=2,
            consent_ref="consent_123",
        )
    )

    assert decision.allowed is True
    assert [result.record_summary for result in decision.results] == [
        "FastAPI is the API boundary for this project."
    ]


def test_deleted_and_superseded_memories_are_filtered_by_default():
    store = MemoryStore()
    old = write(store, "Use the old project name.").memory_id
    new = write(store, "Use the current project name.").memory_id
    store.supersede_memory(old, store.get_memory(new), reason="name changed")
    store.delete_memory(new, deletion_ref="del_123", reason="user request")

    decision = store.search(
        MemoryReadRequest(
            request_id="mrr_name",
            run_id="run_123",
            actor_context=actor(),
            query="project name",
            scope=MemoryScope.project,
            scope_id="proj_123",
            consent_ref="consent_123",
        )
    )

    assert decision.results == []


def test_retrieval_policy_excludes_sensitive_without_consent_and_limits_results():
    store = MemoryStore()
    write(store, "Public memory about the roadmap.")
    write(store, "Sensitive memory about user private context.", scope=MemoryScope.user, scope_id="user_123")

    policy = MemoryRetrievalPolicy(
        retrieval_mode=MemoryRetrievalMode.keyword,
        max_results=1,
        include_sensitivity_levels=[MemorySensitivity.public, MemorySensitivity.project_private],
        embedding_model_ref="embed_contract_only",
        vector_index_ref="vector_contract_only",
    )
    decision = store.search(
        MemoryReadRequest(
            request_id="mrr_policy",
            run_id="run_123",
            actor_context=actor(),
            query="memory",
            scope=MemoryScope.project,
            scope_id="proj_123",
            max_results=10,
        ),
        policy=policy,
    )

    assert len(decision.results) == 1
    assert decision.results[0].record_summary == "Public memory about the roadmap."
    assert policy.embedding_model_ref == "embed_contract_only"
