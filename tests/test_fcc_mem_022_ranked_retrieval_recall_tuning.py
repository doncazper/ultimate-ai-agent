from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.memory import (
    MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    MEMORY_HRR_REQUIRED_MILESTONE_REF,
    MEMORY_RANKING_BLOCKED_STATE_REFS,
    MEMORY_RANKING_COMPONENT_BOUNDS,
    MEMORY_RANKING_CONTRACT_REF,
    ManualMemoryCandidateRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


client = TestClient(app)


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


def _record_accepted_candidate(repo: FounderLoopRepository, slug: str) -> dict[str, Any]:
    candidate = repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"{slug} reviewed preference",
            safe_summary=f"{slug} reviewed safe preference summary.",
            source_refs=[f"source-ref:manual-note:{slug}"],
            provenance_refs=[f"provenance-ref:manual-note:{slug}"],
            evidence_refs=[f"evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:manual-memory-reviewed-{slug}",
    )
    return repo.record_memory_review_decision(
        candidate_ref=str(candidate["candidate_ref"]),
        decision="accept",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:local-operator",
            source_refs=[f"source-ref:manual-note:{slug}"],
            evidence_refs=[f"evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:memory-accept-{slug}",
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


def test_safe_query_is_hashed_and_propagates_through_memory_indexes(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    decision = _record_accepted_candidate(repo, "safe-query-alpha")

    workbench = repo.memory_workbench(safe_query="safe query alpha", limit=20)
    serialized = json.dumps(workbench, sort_keys=True)

    assert workbench["query_mode"] == "safe_query"
    assert workbench["safe_query_ref"].startswith("safe-query-ref:fcc-mem-022:")
    assert "safe query alpha" not in serialized.lower()
    assert workbench["search_index_status"]["safe_summary_refs_only"] is True
    assert workbench["search_index_status"]["raw_content_indexed"] is False
    assert workbench["hrr_readiness"]["hrr_enabled"] is False
    assert workbench["hrr_readiness"]["algebraic_retrieval_enabled"] is False
    assert (
        workbench["hrr_readiness"]["required_milestone_ref"]
        == MEMORY_HRR_REQUIRED_MILESTONE_REF
    )

    for route_model in [
        repo.memory_l1_hot_index(safe_query="safe query alpha", limit=20),
        repo.memory_l2_factual_graph_temporal_index(
            safe_query="safe query alpha",
            limit=20,
        ),
        repo.memory_l3_identity_session_preference_index(
            safe_query="safe query alpha",
            limit=20,
        ),
        repo.memory_context_pack_proposals(safe_query="safe query alpha", limit=20),
    ]:
        assert route_model["query_mode"] == "safe_query"
        assert route_model["safe_query_ref"] == workbench["safe_query_ref"]
        assert route_model["search_index_status"]["raw_content_indexed"] is False
        assert route_model["hrr_readiness"]["hrr_enabled"] is False
        assert route_model["retrieval_strategy_refs"]

    l1 = repo.memory_l1_hot_index(safe_query="safe query alpha", limit=20)
    preview = next(
        item
        for item in l1["previews"]
        if item["memory_record_ref"] == decision["reviewed_recall_record_ref"]
    )
    assert preview["epistemic_role"] == "observation"
    assert preview["score_components"]["query_match"] > 0
    assert preview["score"] > 0

    l3 = repo.memory_l3_identity_session_preference_index(
        safe_query="safe query alpha",
        limit=20,
    )
    l3_item = l3["items"][0]
    assert l3_item["observer_ref"] == "peer-ref:local-operator"
    assert l3_item["observed_ref"].startswith("source-ref:manual-note:")
    assert l3_item["peer_card_ref"].startswith("peer-card-ref:local-operator:")
    assert l3_item["representation_scope_ref"].startswith(
        "representation-scope-ref:l3:"
    )

    try:
        repo.memory_workbench(
            query_ref="source-ref:manual-note:safe-query-alpha",
            safe_query="safe query alpha",
        )
    except ValueError as exc:
        assert "mutually exclusive" in str(exc)
    else:
        raise AssertionError("query_ref plus safe_query must be rejected")


def test_feedback_receipts_tune_trust_and_power_inspection_models(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    decision = _record_accepted_candidate(repo, "feedback-alpha")
    memory_record_ref = decision["reviewed_recall_record_ref"]

    receipt = repo.record_memory_feedback(
        request=MemoryFeedbackRequest(
            memory_record_ref=memory_record_ref,
            feedback_kind="conflict",
            reviewer_ref="actor-ref:local-operator",
            source_refs=["source-ref:memory-feedback:feedback-alpha"],
            evidence_refs=["evidence-ref:memory-feedback:feedback-alpha"],
            blocked_state_refs=MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
        ),
        idempotency_key_ref="idempotency-ref:memory-feedback-alpha",
    )

    assert receipt["receipt_ref"].startswith("receipt:memory-feedback:")
    assert receipt["memory_record_ref"] == memory_record_ref
    assert receipt["trust_delta"] == 0.0
    assert receipt["conflict_state_after"] == "possible_conflict"
    assert receipt["memory_delete_performed"] is False
    assert receipt["memory_export_performed"] is False
    assert receipt["context_injection_authorized"] is False
    assert receipt["connector_write_authorized"] is False

    replayed = repo.record_memory_feedback(
        request=MemoryFeedbackRequest(
            memory_record_ref=memory_record_ref,
            feedback_kind="conflict",
            reviewer_ref="actor-ref:local-operator",
            source_refs=["source-ref:memory-feedback:feedback-alpha"],
            evidence_refs=["evidence-ref:memory-feedback:feedback-alpha"],
            blocked_state_refs=MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
        ),
        idempotency_key_ref="idempotency-ref:memory-feedback-alpha",
    )
    assert replayed["receipt_ref"] == receipt["receipt_ref"]
    assert replayed["replayed"] is True

    observations = repo.memory_observation_candidates(safe_query="feedback alpha")
    assert observations["candidate_count"] >= 1
    observation = observations["candidates"][0]
    assert observation["proof_count"] >= 1
    assert memory_record_ref in observation["supporting_memory_record_refs"]
    assert observation["safe_summary"].startswith("Observation candidate for")
    assert observation["hrr_enabled"] is False

    probe = repo.memory_probe(entity_ref=memory_record_ref)
    assert memory_record_ref in probe["reviewed_recall_refs"]
    assert receipt["receipt_ref"] in probe["feedback_receipt_refs"]
    assert probe["counts"]["feedback"] == 1
    assert probe["hrr_readiness"]["algebraic_retrieval_enabled"] is False

    contradictions = repo.memory_contradictions()
    assert contradictions["preview_count"] >= 1
    assert any(
        preview["memory_ref"] == memory_record_ref
        for preview in contradictions["previews"]
    )
    assert contradictions["hrr_readiness"]["hrr_enabled"] is False


def test_memory_feature_mine_api_routes_are_hash_only_and_authority_blocked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    repo = FounderLoopRepository.from_env()
    decision = _record_accepted_candidate(repo, "api-alpha")
    memory_record_ref = decision["reviewed_recall_record_ref"]

    unsafe_combo = client.get(
        "/control-center/memory/workbench",
        params={
            "query_ref": "source-ref:manual-note:api-alpha",
            "safe_query": "api alpha",
        },
    )
    assert unsafe_combo.status_code == 400

    workbench = client.get(
        "/control-center/memory/workbench",
        params={"safe_query": "api alpha"},
    )
    assert workbench.status_code == 200
    workbench_data = workbench.json()["data"]
    assert workbench_data["query_mode"] == "safe_query"
    assert workbench_data["safe_query_ref"].startswith("safe-query-ref:fcc-mem-022:")
    assert "api alpha" not in workbench.text.lower()

    feedback = client.post(
        "/control-center/memory/feedback",
        headers={"x-uaa-idempotency-ref": "idempotency-ref:api-feedback-alpha"},
        json={
            "memory_record_ref": memory_record_ref,
            "feedback_kind": "stale",
            "reviewer_ref": "actor-ref:local-operator",
            "source_refs": ["source-ref:memory-feedback:api-alpha"],
            "evidence_refs": ["evidence-ref:memory-feedback:api-alpha"],
            "blocked_state_refs": MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
        },
    )
    assert feedback.status_code == 200
    feedback_data = feedback.json()["data"]
    assert feedback_data["memory_record_ref"] == memory_record_ref
    assert feedback_data["memory_delete_performed"] is False
    assert feedback_data["context_injection_authorized"] is False

    for path, key in [
        ("/control-center/memory/observation-candidates", "candidate_count"),
        (f"/control-center/memory/probe?entity_ref={memory_record_ref}", "counts"),
        ("/control-center/memory/contradictions", "preview_count"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()["data"]
        assert key in payload
        assert payload["hrr_readiness"]["hrr_enabled"] is False


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
