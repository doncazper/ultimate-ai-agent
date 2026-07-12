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
    L3_IDENTITY_SESSION_MODELING_CONTRACT_REF,
    L3_IDENTITY_SESSION_MODELING_ROUTE_REF,
    L3IdentitySessionPreferenceIndex,
    L3MemoryModelItem,
    MemoryReviewDecisionRequest,
    build_l1_hot_memory_index,
    build_l2_factual_graph_temporal_index,
    build_l3_identity_session_preference_index,
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
        "reviewer_ref": "actor-ref:l3-index-reviewer",
        "source_refs": ["source-ref:manual-note:l3-index"],
        "evidence_refs": ["evidence-ref:l3-index"],
        "metadata_refs": ["metadata-ref:l3-preference-workspace"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _record_decision(
    repo: FounderLoopRepository,
    *,
    decision: str,
    metadata_ref: str = "metadata-ref:l3-preference-workspace",
) -> dict:
    request = _decision_request(
        metadata_refs=[metadata_ref],
        **(
            {
                "corrected_summary_ref": "safe-summary-ref:l3-index-correction",
                "corrected_safe_summary": "Corrected safe summary for L3 index.",
            }
            if decision == "correct"
            else {}
        ),
    )
    return repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision=decision,  # type: ignore[arg-type]
        request=request,
        idempotency_key_ref=f"idempotency-ref:l3-index:{decision}:{metadata_ref}",
    )


def test_l3_memory_item_accepts_safe_representation_proposal_only() -> None:
    item = L3MemoryModelItem(
        l3_item_ref="l3-item-ref:preference:safe",
        l3_kind="preference",
        subject_ref="reviewed-recall-ref:l3-index:safe",
        workspace_ref="workspace-ref:local-founder-loop",
        session_ref="session-ref:l3-reviewed-recall:safe",
        safe_summary_ref="safe-summary-ref:l3-index:safe",
        supporting_memory_record_refs=["memory-record-ref:mem_l3safe"],
        supporting_l1_preview_refs=["l1-preview-ref:l3safe"],
        supporting_l2_item_refs=[
            "fact-ref:l3-index:safe",
            "relation-ref:l3-index:safe",
            "temporal-ref:l3-index:safe",
        ],
        source_refs=["source-ref:manual-note:l3-index"],
        evidence_refs=["evidence-ref:l3-index"],
        receipt_refs=["receipt:memory-review:accept:l3-index"],
        derivation_reason_refs=[
            "derivation-reason-ref:l3-derived-from-reviewed-l2-safe-ref-projection",
            "derivation-reason-ref:l3-source-evidence-receipt-refs-preserved",
            "derivation-reason-ref:l3-representation-proposal-only",
            "derivation-reason-ref:l3-no-truth-authority",
            "derivation-reason-ref:l3-no-hidden-context-injection",
        ],
    )

    assert item.contract_ref == L3_IDENTITY_SESSION_MODELING_CONTRACT_REF
    assert item.review_required is True
    assert item.truth_authority_enabled is False
    assert item.crm_truth_authority_enabled is False
    assert item.context_injection_authorized is False
    assert item.phase5_context_pack_proposals_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {"safe_summary_ref": "safe-summary-ref:raw-prompt"},
        {"source_refs": ["source-ref:raw-private-content"]},
        {"truth_authority_enabled": True},
        {"crm_truth_authority_enabled": True},
        {"context_injection_authorized": True},
        {"automatic_recall_authorized": True},
        {"automatic_memory_write_authorized": True},
        {"approval_authority_granted": True},
        {"connector_write_authorized": True},
        {"external_crm_sync_authorized": True},
        {"account_sync_authorized": True},
        {"automatic_action_execution_authorized": True},
        {"model_provider_authority_allowed": True},
        {"embedding_index_enabled": True},
        {"vector_db_enabled": True},
        {"semantic_search_enabled": True},
        {"llm_extraction_enabled": True},
        {"background_indexing_enabled": True},
        {"context_pack_injection_authorized": True},
        {"phase5_context_pack_proposals_enabled": True},
        {"phase6_execution_hooks_enabled": True},
        {"raw_content_stored": True},
        {"review_required": False},
    ],
)
def test_l3_memory_item_rejects_raw_private_or_authority_flags(
    override: dict[str, object],
) -> None:
    data: dict[str, object] = {
        "l3_item_ref": "l3-item-ref:preference:safe",
        "l3_kind": "preference",
        "subject_ref": "reviewed-recall-ref:l3-index:safe",
        "workspace_ref": "workspace-ref:local-founder-loop",
        "session_ref": "session-ref:l3-reviewed-recall:safe",
        "safe_summary_ref": "safe-summary-ref:l3-index:safe",
        "supporting_memory_record_refs": ["memory-record-ref:mem_l3safe"],
        "supporting_l1_preview_refs": ["l1-preview-ref:l3safe"],
        "supporting_l2_item_refs": [
            "fact-ref:l3-index:safe",
            "relation-ref:l3-index:safe",
            "temporal-ref:l3-index:safe",
        ],
        "source_refs": ["source-ref:manual-note:l3-index"],
        "evidence_refs": ["evidence-ref:l3-index"],
        "receipt_refs": ["receipt:memory-review:accept:l3-index"],
        "derivation_reason_refs": [
            "derivation-reason-ref:l3-derived-from-reviewed-l2-safe-ref-projection"
        ],
    }
    data.update(override)

    with pytest.raises(ValidationError):
        L3MemoryModelItem(**data)


def test_l3_index_derives_from_l2_reviewed_refs_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    accept_receipt = _record_decision(repo, decision="accept")
    correct_receipt = _record_decision(
        repo,
        decision="correct",
        metadata_ref="metadata-ref:l3-session-commitment",
    )

    l3_index = repo.memory_l3_identity_session_preference_index()

    assert l3_index["contract_ref"] == L3_IDENTITY_SESSION_MODELING_CONTRACT_REF
    assert l3_index["route_ref"] == L3_IDENTITY_SESSION_MODELING_ROUTE_REF
    assert l3_index["source_l2_fact_count"] == 1
    assert l3_index["source_l2_relation_count"] == 1
    assert l3_index["source_l2_temporal_count"] == 1
    assert l3_index["item_count"] == 1
    assert l3_index["safe_refs_only"] is True
    assert l3_index["representation_proposal_only"] is True
    assert l3_index["deterministic_projection_only"] is True
    assert l3_index["semantic_extraction_used"] is False
    assert l3_index["truth_authority_enabled"] is False
    assert l3_index["context_injection_authorized"] is False
    assert l3_index["external_crm_sync_authorized"] is False
    assert l3_index["account_sync_authorized"] is False
    receipt_refs = {accept_receipt["receipt_ref"], correct_receipt["receipt_ref"]}

    kinds = {item["l3_kind"] for item in l3_index["items"]}
    assert kinds == {"session"}
    for item in l3_index["items"]:
        assert item["supporting_memory_record_refs"]
        assert item["supporting_l1_preview_refs"]
        assert len(item["supporting_l2_item_refs"]) == 3
        assert item["source_refs"]
        assert item["evidence_refs"]
        assert set(item["receipt_refs"]) & receipt_refs
        assert item["review_required"] is True
        assert "derivation-reason-ref:l3-representation-proposal-only" in (
            item["derivation_reason_refs"]
        )
        assert item["truth_authority_enabled"] is False
        assert item["crm_truth_authority_enabled"] is False
        assert item["context_injection_authorized"] is False
        assert item["automatic_action_execution_authorized"] is False
        assert item["phase5_context_pack_proposals_enabled"] is False

    query_index = repo.memory_l3_identity_session_preference_index(
        query_ref=l3_index["items"][0]["supporting_memory_record_refs"][0],
    )
    assert query_index["item_count"] == 1


def test_l3_index_skips_unreviewed_rejected_raw_or_authority_records(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    _record_decision(repo, decision="accept")
    record = repo.list_memory_review_recall_records()[0]
    unreviewed = {**record, "memory_id": "mem_l3_unreviewed", "review_state": "pending"}
    raw = {**record, "memory_id": "mem_l3_raw", "safe_summary": "raw response body"}
    authority = {
        **record,
        "memory_id": "mem_l3_authority",
        "metadata": {
            **(record.get("metadata") or {}),
            "context_injection_authorized": True,
        },
    }
    l1_index = build_l1_hot_memory_index([record, unreviewed, raw, authority])
    l2_index = build_l2_factual_graph_temporal_index(l1_index)
    l3_index = build_l3_identity_session_preference_index(l2_index)

    assert isinstance(l3_index, L3IdentitySessionPreferenceIndex)
    assert l3_index.item_count == 1
    assert l3_index.skipped_l2_item_count >= 3

    rejected_repo = FounderLoopRepository(tmp_path / "rejected")
    _record_decision(rejected_repo, decision="reject")
    assert rejected_repo.memory_l3_identity_session_preference_index()["item_count"] == 0


def test_l3_index_api_route_is_backend_backed_and_read_only(
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
        "reviewer_ref": "actor-ref:l3-index-api-reviewer",
        "source_refs": ["source-ref:manual-note:l3-index-api"],
        "evidence_refs": ["evidence-ref:l3-index-api"],
        "metadata_refs": ["metadata-ref:l3-preference-workspace"],
    }

    decision = client.post(
        f"/control-center/memory/review/{candidate_ref}/accept",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:l3-index-api-accept"},
    )
    assert decision.status_code == 200
    receipt_ref = decision.json()["data"]["receipt_ref"]

    response = client.get("/control-center/memory/l3-index")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source_l2_fact_count"] == 1
    assert data["item_count"] == 1
    assert data["safe_refs_only"] is True
    assert data["representation_proposal_only"] is True
    assert data["semantic_extraction_used"] is False
    assert data["context_injection_authorized"] is False
    assert data["phase5_context_pack_proposals_enabled"] is False
    item = data["items"][0]
    assert receipt_ref in item["receipt_refs"]
    assert item["supporting_memory_record_refs"]
    assert item["supporting_l2_item_refs"]

    filtered = client.get(
        "/control-center/memory/l3-index",
        params={"query_ref": receipt_ref},
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["item_count"] == 1

    unsafe = client.get(
        "/control-center/memory/l3-index",
        params={"query_ref": "raw_prompt"},
    )
    assert unsafe.status_code == 400


def test_l3_index_route_manifest_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}
    route = routes["/control-center/memory/l3-index"]

    assert route.method == "GET"
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.idempotency_required is False
    assert route.rate_limit_group is None
    assert "control_center_memory_l3_identity_session_preference_modeling" in (
        manifest.capabilities_declared
    )
    assert "control_center_memory_l3_index_context_pack_injection" in (
        manifest.capabilities_blocked
    )
    assert "control_center_memory_l3_index_phase6_execution_hooks" in (
        manifest.capabilities_blocked
    )
