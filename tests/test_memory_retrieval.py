from typing import Any
import pytest
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.memory import store as memory_store_module
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


def actor() -> Any:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
        workspace_id="workspace_123",
        project_id="proj_123",
    )


def write(store: Any, content: str, *, scope: str = MemoryScope.project, scope_id: str = "proj_123", tags: Any | None = None) -> Any:
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
            summary=content,
            tags=tags or [],
            authority=MemoryAuthority.user_provided,
            sensitivity=MemorySensitivity.project_private,
            idempotency_key=f"idem_{len(store.list_memories())}",
            consent_ref="consent_123",
        )
    )


def test_keyword_retrieval_is_deterministic_and_scope_filtered() -> None:
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


def test_deleted_and_superseded_memories_are_filtered_by_default() -> None:
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


def test_retrieval_policy_excludes_sensitive_without_consent_and_limits_results() -> None:
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


def test_memory_search_never_returns_raw_content_without_summary() -> None:
    store = MemoryStore()
    store.write_memory(
        MemoryWriteRequest(
            request_id="mwr_raw",
            run_id="run_123",
            actor_context=actor(),
            memory_type=MemoryType.decision,
            scope=MemoryScope.project,
            scope_id="proj_123",
            project_id="proj_123",
            content="Raw retained private content should not be returned.",
            tags=["private"],
            authority=MemoryAuthority.user_provided,
            sensitivity=MemorySensitivity.project_private,
            idempotency_key="idem_raw",
            consent_ref="consent_123",
        )
    )

    decision = store.search(
        MemoryReadRequest(
            request_id="mrr_raw",
            run_id="run_123",
            actor_context=actor(),
            query="private",
            scope=MemoryScope.project,
            scope_id="proj_123",
            consent_ref="consent_123",
        )
    )

    serialized = str(decision.model_dump())
    assert "Raw retained private content" not in serialized
    assert decision.results[0].record_summary == "Redacted memory summary unavailable."
    assert "raw_memory_content_omitted" in decision.redactions_applied


def test_memory_search_scope_prefilter_skips_out_of_scope_scoring(monkeypatch: pytest.MonkeyPatch) -> None:
    store = MemoryStore()
    write(store, "Project-scoped memory about latency.", tags=["latency"])
    write(
        store,
        "User-scoped memory about latency.",
        scope=MemoryScope.user,
        scope_id="user_123",
        tags=["latency"],
    )
    scored_scopes = []
    original_score_memory = memory_store_module.score_memory

    def counting_score_memory(record: Any, query: str, tags: Any) -> Any:
        scored_scopes.append(record.scope)
        return original_score_memory(record, query, tags)

    monkeypatch.setattr(memory_store_module, "score_memory", counting_score_memory)

    decision = store.search(
        MemoryReadRequest(
            request_id="mrr_scope_prefilter",
            run_id="run_123",
            actor_context=actor(),
            query="latency",
            scope=MemoryScope.project,
            scope_id="proj_123",
            consent_ref="consent_123",
        )
    )

    assert decision.allowed is True
    assert scored_scopes == [MemoryScope.project]
