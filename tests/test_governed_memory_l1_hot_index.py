from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    L1_HOT_MEMORY_INDEX_CONTRACT_REF,
    L1_HOT_MEMORY_INDEX_ROUTE_REF,
    L1HotMemoryPreview,
    MemoryReviewDecisionRequest,
    build_l1_hot_memory_index,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import (
    issue_memory_write_authority_lease,
    memory_write_authority_lease,
)


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:l1-index-reviewer",
        "source_refs": ["source-ref:manual-note:l1-index"],
        "evidence_refs": ["evidence-ref:l1-index"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _accepted_record(repo: FounderLoopRepository, *, decision: str = "accept") -> dict:
    candidate_ref = _first_candidate_ref(repo)
    request = _decision_request(
        **(
            {
                "corrected_summary_ref": "safe-summary-ref:l1-index-correction",
                "corrected_safe_summary": "Corrected safe summary for L1 index.",
            }
            if decision == "correct"
            else {}
        )
    )
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision=decision,  # type: ignore[arg-type]
        request=request,
        idempotency_key_ref=f"idempotency-ref:l1-index:{decision}",
    )
    return repo.list_memory_review_recall_records()[0]


def test_l1_hot_memory_preview_accepts_safe_reviewed_recall_only_record() -> None:
    preview = L1HotMemoryPreview(
        memory_record_ref="memory-record-ref:mem_l1safe",
        memory_id="mem_l1safe",
        reviewed_recall_ref="reviewed-recall-ref:l1-index:safe",
        safe_summary="Founder wants memory previews to explain source, evidence, and receipt refs.",
        preview_summary="Founder wants memory previews to explain source, evidence, and receipt refs.",
        memory_kind="structured_fact",
        source_refs=["source-ref:manual-note:l1-index"],
        evidence_refs=["evidence-ref:l1-index"],
        receipt_refs=["receipt:memory-review:accept:l1-index"],
        event_refs=["evidence-ref:l1-index"],
        metadata_refs=["reviewed-recall-ref:l1-index:safe"],
        tag_refs=["tag-ref:memory-review-decision"],
        match_reasons=["reviewed_recall_record"],
        supporting_ref_groups={
            "source_refs": ["source-ref:manual-note:l1-index"],
            "evidence_refs": ["evidence-ref:l1-index"],
            "receipt_refs": ["receipt:memory-review:accept:l1-index"],
        },
    )

    assert preview.contract_ref == L1_HOT_MEMORY_INDEX_CONTRACT_REF
    assert preview.context_injection_authorized is False
    assert preview.source_truth_authority is False
    assert preview.embedding_index_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {"safe_summary": "raw prompt text should never be indexed"},
        {"source_refs": ["source-ref:raw-private-content"]},
        {"context_injection_authorized": True},
        {"automatic_recall_authorized": True},
        {"embedding_index_enabled": True},
        {"vector_db_enabled": True},
        {"semantic_search_enabled": True},
    ],
)
def test_l1_hot_memory_preview_rejects_raw_private_or_authority_flags(
    override: dict[str, object],
) -> None:
    data: dict[str, object] = {
        "memory_record_ref": "memory-record-ref:mem_l1safe",
        "memory_id": "mem_l1safe",
        "reviewed_recall_ref": "reviewed-recall-ref:l1-index:safe",
        "safe_summary": "Founder wants safe memory preview refs.",
        "preview_summary": "Founder wants safe memory preview refs.",
        "memory_kind": "structured_fact",
        "source_refs": ["source-ref:manual-note:l1-index"],
        "evidence_refs": ["evidence-ref:l1-index"],
        "receipt_refs": ["receipt:memory-review:accept:l1-index"],
        "match_reasons": ["reviewed_recall_record"],
        "supporting_ref_groups": {
            "source_refs": ["source-ref:manual-note:l1-index"],
            "evidence_refs": ["evidence-ref:l1-index"],
            "receipt_refs": ["receipt:memory-review:accept:l1-index"],
        },
    }
    data.update(override)

    with pytest.raises(ValidationError):
        L1HotMemoryPreview(**data)


def test_l1_index_derives_from_reviewed_accept_and_correct_records_only(
    tmp_path: Path,
) -> None:
    accept_repo = FounderLoopRepository(
        tmp_path / "accept",
        active_authority_leases=[memory_write_authority_lease()],
    )
    accept_record = _accepted_record(accept_repo, decision="accept")
    accept_index = accept_repo.memory_l1_hot_index()

    assert accept_index["contract_ref"] == L1_HOT_MEMORY_INDEX_CONTRACT_REF
    assert accept_index["route_ref"] == L1_HOT_MEMORY_INDEX_ROUTE_REF
    assert accept_index["indexed_record_count"] == 1
    accept_preview = accept_index["previews"][0]
    assert accept_preview["memory_record_ref"] == f"memory-record-ref:{accept_record['memory_id']}"
    assert accept_preview["review_state"] == "user_reviewed"
    assert accept_preview["authority_level"] == "recall_only"
    assert accept_preview["source_refs"]
    assert accept_preview["evidence_refs"]
    assert accept_preview["receipt_refs"]
    assert "reviewed_recall_record" in accept_preview["match_reasons"]
    assert accept_preview["context_injection_authorized"] is False
    assert accept_preview["automatic_recall_authorized"] is False
    assert accept_index["embedding_index_enabled"] is False
    assert accept_index["vector_db_enabled"] is False

    query_index = accept_repo.memory_l1_hot_index(
        query_ref=accept_preview["receipt_refs"][0]
    )
    assert query_index["preview_count"] == 1

    correct_repo = FounderLoopRepository(
        tmp_path / "correct",
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accepted_record(correct_repo, decision="correct")
    correct_index = correct_repo.memory_l1_hot_index()
    assert correct_index["indexed_record_count"] == 1
    assert correct_index["previews"][0]["memory_kind"] == "correction"

    reject_repo = FounderLoopRepository(tmp_path / "reject")
    reject_repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(reject_repo),
        decision="reject",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:l1-index:reject",
    )
    reject_index = reject_repo.memory_l1_hot_index()
    assert reject_index["indexed_record_count"] == 0
    assert reject_repo.list_memory_review_recall_records() == []


def test_l1_index_skips_unreviewed_rejected_raw_or_private_records(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    record = _accepted_record(repo)
    unreviewed = {**record, "memory_id": "mem_unreviewed", "review_state": "user_review_required"}
    deleted = {**record, "memory_id": "mem_rejected", "retention_state": "deleted"}
    raw = {**record, "memory_id": "mem_raw", "safe_summary": "raw response body"}

    index = build_l1_hot_memory_index([record, unreviewed, deleted, raw])

    assert index.indexed_record_count == 1
    assert index.skipped_record_count == 3
    assert "memory-record-ref:mem_unreviewed" in index.skipped_record_refs
    assert "memory-record-ref:mem_rejected" in index.skipped_record_refs
    assert "memory-record-ref:mem_raw" in index.skipped_record_refs


def test_l1_index_api_route_is_backend_backed_and_preview_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    issue_memory_write_authority_lease(authority_state_dir)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    client = TestClient(app)
    candidate_ref = (
        "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )
    body = {
        "reviewer_ref": "actor-ref:l1-index-api-reviewer",
        "source_refs": ["source-ref:manual-note:l1-index-api"],
        "evidence_refs": ["evidence-ref:l1-index-api"],
    }

    decision = client.post(
        f"/control-center/memory/review/{candidate_ref}/accept",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:l1-index-api-accept"},
    )
    assert decision.status_code == 200
    receipt_ref = decision.json()["data"]["receipt_ref"]

    response = client.get("/control-center/memory/l1-index")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["indexed_record_count"] == 1
    assert data["context_injection_authorized"] is False
    assert data["automatic_recall_authorized"] is False
    assert data["automatic_memory_write_authorized"] is False
    assert data["semantic_search_enabled"] is False
    preview = data["previews"][0]
    assert receipt_ref in preview["receipt_refs"]
    assert preview["supporting_ref_groups"]["receipt_refs"]

    filtered = client.get(
        "/control-center/memory/l1-index",
        params={"query_ref": receipt_ref},
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["preview_count"] == 1

    unsafe = client.get(
        "/control-center/memory/l1-index",
        params={"query_ref": "raw_prompt"},
    )
    assert unsafe.status_code == 400


def test_l1_index_route_manifest_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}
    route = routes["/control-center/memory/l1-index"]

    assert route.method == "GET"
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.idempotency_required is False
    assert route.rate_limit_group is None
    assert "control_center_memory_l1_hot_local_index" in manifest.capabilities_declared
    assert "control_center_memory_l1_index_context_injection" in manifest.capabilities_blocked
