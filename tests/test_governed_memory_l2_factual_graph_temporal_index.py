from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF,
    L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF,
    L2FactualGraphTemporalIndex,
    L2MemoryFactItem,
    MemoryReviewDecisionRequest,
    build_l1_hot_memory_index,
    build_l2_factual_graph_temporal_index,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:l2-index-reviewer",
        "source_refs": ["source-ref:manual-note:l2-index"],
        "evidence_refs": ["evidence-ref:l2-index"],
        "metadata_refs": ["metadata-ref:l2-index"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _record_decision(
    repo: FounderLoopRepository,
    *,
    decision: str,
) -> dict:
    request = _decision_request(
        **(
            {"corrected_summary_ref": "safe-summary-ref:l2-index-correction"}
            if decision == "correct"
            else {}
        )
    )
    return repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision=decision,  # type: ignore[arg-type]
        request=request,
        idempotency_key_ref=f"idempotency-ref:l2-index:{decision}",
    )


def test_l2_fact_item_accepts_safe_ref_projection_only() -> None:
    fact = L2MemoryFactItem(
        fact_ref="fact-ref:l2-reviewed-recall:safe",
        memory_record_ref="memory-record-ref:mem_l2safe",
        reviewed_recall_ref="reviewed-recall-ref:l2-index:safe",
        safe_summary="Founder wants factual graph temporal recall previews with receipts.",
        fact_subject_ref="reviewed-recall-ref:l2-index:safe",
        fact_value_ref="safe-summary-ref:l2-reviewed-recall:safe",
        source_refs=["source-ref:manual-note:l2-index"],
        evidence_refs=["evidence-ref:l2-index"],
        receipt_refs=["receipt:memory-review:accept:l2-index"],
        event_refs=["evidence-ref:l2-index"],
        metadata_refs=["metadata-ref:l2-index"],
        tag_refs=["tag-ref:memory-review-decision"],
        derivation_reasons=[
            "derived_from_l1_reviewed_recall_preview",
            "safe_summary_bounded_preview_only",
            "source_evidence_receipt_refs_preserved",
            "deterministic_ref_projection_not_semantic_extraction",
        ],
        supporting_refs=[
            "memory-record-ref:mem_l2safe",
            "reviewed-recall-ref:l2-index:safe",
            "source-ref:manual-note:l2-index",
            "evidence-ref:l2-index",
            "receipt:memory-review:accept:l2-index",
        ],
    )

    assert fact.contract_ref == L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    assert fact.truth_authority_enabled is False
    assert fact.context_injection_authorized is False
    assert fact.semantic_search_enabled is False
    assert fact.llm_entity_extraction_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {"safe_summary": "raw prompt text must not become L2 memory"},
        {"source_refs": ["source-ref:raw-private-content"]},
        {"truth_authority_enabled": True},
        {"context_injection_authorized": True},
        {"automatic_recall_authorized": True},
        {"embedding_index_enabled": True},
        {"vector_db_enabled": True},
        {"semantic_search_enabled": True},
        {"llm_entity_extraction_enabled": True},
        {"context_pack_injection_authorized": True},
    ],
)
def test_l2_fact_item_rejects_raw_private_or_authority_flags(
    override: dict[str, object],
) -> None:
    data: dict[str, object] = {
        "fact_ref": "fact-ref:l2-reviewed-recall:safe",
        "memory_record_ref": "memory-record-ref:mem_l2safe",
        "reviewed_recall_ref": "reviewed-recall-ref:l2-index:safe",
        "safe_summary": "Founder wants safe L2 memory previews.",
        "fact_subject_ref": "reviewed-recall-ref:l2-index:safe",
        "fact_value_ref": "safe-summary-ref:l2-reviewed-recall:safe",
        "source_refs": ["source-ref:manual-note:l2-index"],
        "evidence_refs": ["evidence-ref:l2-index"],
        "receipt_refs": ["receipt:memory-review:accept:l2-index"],
        "derivation_reasons": ["derived_from_l1_reviewed_recall_preview"],
        "supporting_refs": [
            "memory-record-ref:mem_l2safe",
            "source-ref:manual-note:l2-index",
            "evidence-ref:l2-index",
            "receipt:memory-review:accept:l2-index",
        ],
    }
    data.update(override)

    with pytest.raises(ValidationError):
        L2MemoryFactItem(**data)


def test_l2_index_derives_fact_graph_and_time_from_l1_previews_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    accept_receipt = _record_decision(repo, decision="accept")
    correct_receipt = _record_decision(repo, decision="correct")
    l2_index = repo.memory_l2_factual_graph_temporal_index()

    assert l2_index["contract_ref"] == L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    assert l2_index["route_ref"] == L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF
    assert l2_index["source_l1_preview_count"] == 2
    assert l2_index["fact_count"] == 2
    assert l2_index["relation_count"] == 2
    assert l2_index["temporal_count"] == 2
    assert l2_index["truth_authority_enabled"] is False
    assert l2_index["context_injection_authorized"] is False
    assert l2_index["automatic_recall_authorized"] is False
    assert l2_index["embedding_index_enabled"] is False
    assert l2_index["vector_db_enabled"] is False
    assert l2_index["semantic_search_enabled"] is False
    assert l2_index["llm_entity_extraction_enabled"] is False
    receipt_refs = {accept_receipt["receipt_ref"], correct_receipt["receipt_ref"]}

    for collection_name in ["facts", "graph_relations", "temporal_items"]:
        for item in l2_index[collection_name]:
            assert item["memory_record_ref"].startswith("memory-record-ref:")
            assert item["source_refs"]
            assert item["evidence_refs"]
            assert item["receipt_refs"]
            assert set(item["receipt_refs"]) & receipt_refs
            assert item["supporting_refs"]
            assert "derived_from_l1_reviewed_recall_preview" in item["derivation_reasons"]
            assert "deterministic_ref_projection_not_semantic_extraction" in item["derivation_reasons"]
            assert item["truth_authority_enabled"] is False
            assert item["context_injection_authorized"] is False
            assert item["automatic_action_execution_authorized"] is False

    query_index = repo.memory_l2_factual_graph_temporal_index(
        query_ref=l2_index["facts"][0]["memory_record_ref"],
    )
    assert query_index["fact_count"] == 1
    assert query_index["graph_relations"][0]["memory_record_ref"] == (
        l2_index["facts"][0]["memory_record_ref"]
    )


def test_l2_index_skips_rejected_unreviewed_raw_or_authority_records(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    _record_decision(repo, decision="accept")
    record = repo.list_memory_review_recall_records()[0]
    unreviewed = {**record, "memory_id": "mem_l2_unreviewed", "review_state": "pending"}
    raw = {**record, "memory_id": "mem_l2_raw", "safe_summary": "raw response body"}
    authority = {
        **record,
        "memory_id": "mem_l2_authority",
        "metadata": {
            **(record.get("metadata") or {}),
            "context_injection_authorized": True,
        },
    }
    rejected_repo = FounderLoopRepository(tmp_path / "rejected")
    _record_decision(rejected_repo, decision="reject")

    l1_index = build_l1_hot_memory_index([record, unreviewed, raw, authority])
    l2_index = build_l2_factual_graph_temporal_index(l1_index)

    assert l2_index.fact_count == 1
    assert l2_index.relation_count == 1
    assert l2_index.temporal_count == 1
    assert l2_index.skipped_l1_preview_count >= 3
    assert rejected_repo.memory_l2_factual_graph_temporal_index()["fact_count"] == 0


def test_l2_index_api_route_is_backend_backed_and_read_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)
    candidate_ref = (
        "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )
    body = {
        "reviewer_ref": "actor-ref:l2-index-api-reviewer",
        "source_refs": ["source-ref:manual-note:l2-index-api"],
        "evidence_refs": ["evidence-ref:l2-index-api"],
    }

    decision = client.post(
        f"/control-center/memory/review/{candidate_ref}/accept",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:l2-index-api-accept"},
    )
    assert decision.status_code == 200
    receipt_ref = decision.json()["data"]["receipt_ref"]

    response = client.get("/control-center/memory/l2-index")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source_l1_preview_count"] == 1
    assert data["fact_count"] == 1
    assert data["relation_count"] == 1
    assert data["temporal_count"] == 1
    assert data["context_injection_authorized"] is False
    assert data["automatic_recall_authorized"] is False
    assert data["semantic_extraction_used"] is False
    assert data["semantic_search_enabled"] is False
    assert receipt_ref in data["facts"][0]["receipt_refs"]

    filtered = client.get(
        "/control-center/memory/l2-index",
        params={"query_ref": receipt_ref},
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["fact_count"] == 1

    unsafe = client.get(
        "/control-center/memory/l2-index",
        params={"query_ref": "raw_prompt"},
    )
    assert unsafe.status_code == 400


def test_l2_index_route_manifest_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}
    route = routes["/control-center/memory/l2-index"]

    assert route.method == "GET"
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.idempotency_required is False
    assert route.rate_limit_group is None
    assert "control_center_memory_l2_factual_graph_temporal_index" in (
        manifest.capabilities_declared
    )
    assert "control_center_memory_l2_index_context_injection" in (
        manifest.capabilities_blocked
    )
    assert "control_center_memory_l2_index_semantic_search" in (
        manifest.capabilities_blocked
    )
