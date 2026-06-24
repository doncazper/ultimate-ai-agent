from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.memory import (
    MEMORY_RANKING_BLOCKED_STATE_REFS,
    MEMORY_RANKING_COMPONENT_BOUNDS,
    MEMORY_RANKING_CONTRACT_REF,
    ManualMemoryCandidateRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _storage_counts(repo: FounderLoopRepository) -> dict[str, int]:
    counts = dict(repo.storage_status()["counts"])
    counts["memory_review_recall_records"] = len(
        repo.list_memory_review_recall_records()
    )
    return counts


def _record_manual_candidate(repo: FounderLoopRepository, slug: str) -> None:
    repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"{slug} review candidate",
            safe_summary=f"{slug} safe summary for review only.",
            source_refs=[f"source-ref:manual-note:{slug}"],
            provenance_refs=[f"provenance-ref:manual-note:{slug}"],
            missing_evidence_refs=[f"missing-evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:manual-memory-{slug}",
    )


def test_ranked_recall_read_model_is_deterministic_and_read_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    before_counts = _storage_counts(repo)
    first = repo.memory_workbench(limit=20)
    second = repo.memory_workbench(limit=20)

    assert _stable_json(first["ranking"]) == _stable_json(second["ranking"])
    assert _storage_counts(repo) == before_counts

    ranking = first["ranking"]
    assert ranking["schema_version"] == "fcc_mem_022_ranked_retrieval_recall_tuning.v1"
    assert ranking["contract_ref"] == MEMORY_RANKING_CONTRACT_REF
    assert ranking["candidate_count"] == len(first["items"])
    assert ranking["ranked_candidate_refs"] == [
        item["memory_ref"] for item in first["items"]
    ]
    assert not set(ranking["included_ranked_refs"]).intersection(
        {entry["memory_ref"] for entry in ranking["excluded_refs"]}
    )
    assert ranking["score_component_bounds"] == MEMORY_RANKING_COMPONENT_BOUNDS
    assert ranking["safe_refs_only"] is True
    assert ranking["lexical_tag_ref_only"] is True
    assert ranking["embedding_search_enabled"] is False
    assert ranking["vector_db_enabled"] is False
    assert ranking["semantic_provider_enabled"] is False
    assert ranking["context_injection_authorized"] is False
    assert ranking["memory_write_performed"] is False
    assert ranking["auto_maintenance_performed"] is False
    assert ranking["action_execution_authorized"] is False
    assert ranking["production_authority_enabled"] is False
    for blocked_ref in MEMORY_RANKING_BLOCKED_STATE_REFS:
        assert blocked_ref in ranking["blocked_authority_refs"]

    for item in first["items"]:
        components = item["rank_components"]
        assert set(components) == set(MEMORY_RANKING_COMPONENT_BOUNDS)
        for component, score in components.items():
            assert isinstance(score, int)
            assert 0 <= score <= MEMORY_RANKING_COMPONENT_BOUNDS[component]
        assert item["rank_score"] == min(
            sum(components.values()),
            sum(MEMORY_RANKING_COMPONENT_BOUNDS.values()),
        )
        assert item["included_reason_refs"]
        assert item["why_ranked_refs"]
        if item["excluded_reason_refs"]:
            assert (
                "rank-include-ref:visible-but-recall-use-blocked"
                in item["included_reason_refs"]
            )
        assert item["cache_key"].startswith("cache-key:fcc-mem-022-ranking-item:")
        assert isinstance(item["token_estimate"], int)
        assert item["token_estimate"] > 0
        assert item["ranking_blocked_authority_refs"] == MEMORY_RANKING_BLOCKED_STATE_REFS


def test_query_ref_improves_matching_candidate_without_mutating_memory(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    _record_manual_candidate(repo, "ranked-alpha")
    _record_manual_candidate(repo, "ranked-beta")

    before_counts = _storage_counts(repo)
    workbench = repo.memory_workbench(
        query_ref="source-ref:manual-note:ranked-alpha",
        limit=20,
    )
    after_workbench_counts = _storage_counts(repo)
    search = repo.memory_search(
        query_ref="source-ref:manual-note:ranked-alpha",
        limit=20,
    )

    assert after_workbench_counts == before_counts
    assert _storage_counts(repo) == before_counts

    items_by_title = {item["title"]: item for item in workbench["items"]}
    alpha = items_by_title["ranked-alpha review candidate"]
    beta = items_by_title["ranked-beta review candidate"]
    assert (
        alpha["rank_components"]["lexical_safe_summary_title_match"]
        > beta["rank_components"]["lexical_safe_summary_title_match"]
    )
    assert alpha["rank_score"] > beta["rank_score"]
    assert "rank-include-ref:lexical-safe-summary-title-match" in alpha[
        "included_reason_refs"
    ]
    assert "rank-exclusion-ref:evidence-missing" in alpha["excluded_reason_refs"]
    assert alpha["missing_evidence_pressure"] == 1

    assert search["count"] == 1
    assert search["items"][0]["title"] == "ranked-alpha review candidate"
    assert search["ranking"]["query_ref"] == "source-ref:manual-note:ranked-alpha"
    assert search["ranking"]["status"] == (
        "implemented_filtered_ranked_read_model_safe_refs_only"
    )
    assert search["ranking"]["excluded_refs"][0]["reason_refs"]


def test_ranked_recall_payload_has_no_hidden_context_or_provider_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    serialized = json.dumps(repo.memory_workbench(), sort_keys=True).lower()

    for forbidden in [
        "embedding_search_enabled\": true",
        "vector_db_enabled\": true",
        "semantic_provider_enabled\": true",
        "context_injection_authorized\": true",
        "memory_write_performed\": true",
        "auto_maintenance_performed\": true",
        "action_execution_authorized\": true",
        "production_authority_enabled\": true",
        "raw_prompt",
        "raw_response",
        "provider_payload",
    ]:
        assert forbidden not in serialized
