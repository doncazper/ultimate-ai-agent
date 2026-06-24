from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.memory import (
    CONTEXT_PACK_PROPOSAL_CONTRACT_REF,
    CONTEXT_PACK_PROPOSAL_ROUTE_REF,
    ContextPackProposal,
    ContextPackProposalIndex,
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MemoryReviewDecisionRequest,
    build_context_pack_proposal_index,
    build_l1_hot_memory_index,
    build_l2_factual_graph_temporal_index,
    build_l3_identity_session_preference_index,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:context-pack-reviewer",
        "source_refs": ["source-ref:manual-note:context-pack"],
        "evidence_refs": ["evidence-ref:context-pack"],
        "metadata_refs": ["metadata-ref:context-pack-preference-workspace"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _record_decision(
    repo: FounderLoopRepository,
    *,
    decision: str,
    metadata_ref: str = "metadata-ref:context-pack-preference-workspace",
) -> dict:
    request = _decision_request(
        metadata_refs=[metadata_ref],
        **(
            {
                "corrected_summary_ref": "safe-summary-ref:context-pack-correction",
                "corrected_safe_summary": "Corrected safe summary for context packs.",
            }
            if decision == "correct"
            else {}
        ),
    )
    return repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision=decision,  # type: ignore[arg-type]
        request=request,
        idempotency_key_ref=f"idempotency-ref:context-pack:{decision}:{metadata_ref}",
    )


def test_context_pack_proposal_accepts_safe_review_required_refs_only() -> None:
    proposal = ContextPackProposal(
        context_pack_ref="context-pack-ref:proposal:safe",
        proposal_ref="proposal-ref:context-pack:safe",
        purpose_ref="purpose-ref:founder-loop:review-safe-memory-context",
        source_memory_record_refs=["memory-record-ref:mem_contextsafe"],
        l1_preview_refs=["l1-preview-ref:contextsafe"],
        l2_projection_refs=[
            "fact-ref:context-pack:safe",
            "relation-ref:context-pack:safe",
            "temporal-ref:context-pack:safe",
        ],
        l3_representation_refs=["l3-item-ref:preference:contextsafe"],
        included_summary_refs=["safe-summary-ref:context-pack:safe"],
        inclusion_reason_refs=[
            "inclusion-reason-ref:context-pack-reviewed-l1-preview",
            "inclusion-reason-ref:context-pack-reviewed-l2-safe-projection",
            "inclusion-reason-ref:context-pack-reviewed-l3-representation-proposal",
            "inclusion-reason-ref:context-pack-source-evidence-receipt-linked",
            "inclusion-reason-ref:context-pack-review-required-not-injected",
        ],
        excluded_ref_reasons={
            "l3-item-ref:excluded": "excluded-reason-ref:context-pack-filtered-by-reviewed-memory-source-lanes"
        },
        source_refs=["source-ref:manual-note:context-pack"],
        evidence_refs=["evidence-ref:context-pack"],
        receipt_refs=["receipt:memory-review:accept:context-pack"],
        stale_state_refs=["stale-state-ref:none"],
        conflict_state_refs=["conflict-state-ref:none"],
    )

    assert proposal.contract_ref == CONTEXT_PACK_PROPOSAL_CONTRACT_REF
    assert proposal.proposal_only is True
    assert proposal.review_required is True
    assert proposal.context_injection_authorized is False
    assert proposal.hidden_prompt_context_authorized is False
    assert proposal.prompt_context_written is False
    assert proposal.model_provider_authority_allowed is False
    assert proposal.phase6_execution_hooks_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {"included_summary_refs": ["safe-summary-ref:raw-prompt"]},
        {"source_refs": ["source-ref:raw-private-content"]},
        {"context_injection_authorized": True},
        {"hidden_prompt_context_authorized": True},
        {"automatic_context_injection_authorized": True},
        {"prompt_context_written": True},
        {"truth_authority_enabled": True},
        {"approval_authority_granted": True},
        {"connector_write_authorized": True},
        {"external_crm_sync_authorized": True},
        {"account_sync_authorized": True},
        {"automatic_action_execution_authorized": True},
        {"model_provider_authority_allowed": True},
        {"embedding_index_enabled": True},
        {"vector_db_enabled": True},
        {"semantic_search_enabled": True},
        {"background_indexing_enabled": True},
        {"phase6_execution_hooks_enabled": True},
        {"raw_content_stored": True},
        {"proposal_only": False},
        {"review_required": False},
    ],
)
def test_context_pack_proposal_rejects_raw_private_or_authority_flags(
    override: dict[str, object],
) -> None:
    data: dict[str, object] = {
        "context_pack_ref": "context-pack-ref:proposal:safe",
        "proposal_ref": "proposal-ref:context-pack:safe",
        "purpose_ref": "purpose-ref:founder-loop:review-safe-memory-context",
        "source_memory_record_refs": ["memory-record-ref:mem_contextsafe"],
        "l1_preview_refs": ["l1-preview-ref:contextsafe"],
        "l2_projection_refs": ["fact-ref:context-pack:safe"],
        "l3_representation_refs": ["l3-item-ref:preference:contextsafe"],
        "included_summary_refs": ["safe-summary-ref:context-pack:safe"],
        "inclusion_reason_refs": [
            "inclusion-reason-ref:context-pack-reviewed-l3-representation-proposal"
        ],
        "source_refs": ["source-ref:manual-note:context-pack"],
        "evidence_refs": ["evidence-ref:context-pack"],
        "receipt_refs": ["receipt:memory-review:accept:context-pack"],
        "stale_state_refs": ["stale-state-ref:none"],
        "conflict_state_refs": ["conflict-state-ref:none"],
    }
    data.update(override)

    with pytest.raises(ValidationError):
        ContextPackProposal(**data)


def test_context_pack_proposals_derive_from_reviewed_l1_l2_l3_layers(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    accept_receipt = _record_decision(repo, decision="accept")
    correct_receipt = _record_decision(
        repo,
        decision="correct",
        metadata_ref="metadata-ref:context-pack-session-commitment",
    )

    context_packs = repo.memory_context_pack_proposals()

    assert context_packs["contract_ref"] == CONTEXT_PACK_PROPOSAL_CONTRACT_REF
    assert context_packs["route_ref"] == CONTEXT_PACK_PROPOSAL_ROUTE_REF
    assert context_packs["source_l1_preview_count"] == 2
    assert context_packs["source_l2_projection_count"] == 6
    assert context_packs["source_l3_representation_count"] == 2
    assert context_packs["context_pack_count"] == 2
    assert context_packs["safe_refs_only"] is True
    assert context_packs["proposal_only"] is True
    assert context_packs["derived_from_reviewed_memory_only"] is True
    assert context_packs["context_injection_performed"] is False
    assert context_packs["provider_model_call_performed"] is False
    receipt_refs = {accept_receipt["receipt_ref"], correct_receipt["receipt_ref"]}

    for proposal in context_packs["proposals"]:
        assert proposal["source_memory_record_refs"]
        assert proposal["l1_preview_refs"]
        assert proposal["l2_projection_refs"]
        assert proposal["l3_representation_refs"]
        assert proposal["included_summary_refs"]
        assert proposal["source_refs"]
        assert proposal["evidence_refs"]
        assert set(proposal["receipt_refs"]) & receipt_refs
        assert proposal["inclusion_reason_refs"]
        assert "inclusion-reason-ref:context-pack-review-required-not-injected" in (
            proposal["inclusion_reason_refs"]
        )
        assert proposal["evidence_answer_refs"]
        assert proposal["proposal_only"] is True
        assert proposal["review_required"] is True
        assert proposal["context_injection_authorized"] is False
        assert proposal["hidden_prompt_context_authorized"] is False
        assert proposal["automatic_action_execution_authorized"] is False
        assert proposal["model_provider_authority_allowed"] is False
        assert proposal["production_authority_enabled"] is False

    filtered = repo.memory_context_pack_proposals(
        query_ref=context_packs["proposals"][0]["source_memory_record_refs"][0],
    )
    assert filtered["context_pack_count"] == 1


def test_context_pack_proposals_skip_unreviewed_rejected_raw_or_authority_records(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    _record_decision(repo, decision="accept")
    record = repo.list_memory_review_recall_records()[0]
    unreviewed = {
        **record,
        "memory_id": "mem_context_pack_unreviewed",
        "review_state": "pending",
    }
    raw = {
        **record,
        "memory_id": "mem_context_pack_raw",
        "safe_summary": "raw response body",
    }
    authority = {
        **record,
        "memory_id": "mem_context_pack_authority",
        "metadata": {
            **(record.get("metadata") or {}),
            "context_injection_authorized": True,
        },
    }
    l1_index = build_l1_hot_memory_index([record, unreviewed, raw, authority])
    l2_index = build_l2_factual_graph_temporal_index(l1_index)
    l3_index = build_l3_identity_session_preference_index(l2_index)
    context_packs = build_context_pack_proposal_index(l1_index, l2_index, l3_index)

    assert isinstance(context_packs, ContextPackProposalIndex)
    assert context_packs.context_pack_count == 1
    assert context_packs.skipped_ref_reasons

    rejected_repo = FounderLoopRepository(tmp_path / "rejected")
    _record_decision(rejected_repo, decision="reject")
    assert rejected_repo.memory_context_pack_proposals()["context_pack_count"] == 0


def test_context_pack_api_route_is_backend_backed_and_read_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)
    candidate_ref = (
        "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )
    body = {
        "reviewer_ref": "actor-ref:context-pack-api-reviewer",
        "source_refs": ["source-ref:manual-note:context-pack-api"],
        "evidence_refs": ["evidence-ref:context-pack-api"],
        "metadata_refs": ["metadata-ref:context-pack-preference-workspace"],
    }

    decision = client.post(
        f"/control-center/memory/review/{candidate_ref}/accept",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:context-pack-api-accept"},
    )
    assert decision.status_code == 200
    receipt_ref = decision.json()["data"]["receipt_ref"]

    response = client.get("/control-center/memory/context-packs")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source_l1_preview_count"] == 1
    assert data["source_l2_projection_count"] == 3
    assert data["source_l3_representation_count"] == 1
    assert data["context_pack_count"] == 1
    assert data["proposal_only"] is True
    assert data["context_injection_authorized"] is False
    assert data["context_injection_performed"] is False
    assert data["provider_model_call_performed"] is False
    proposal = data["proposals"][0]
    assert receipt_ref in proposal["receipt_refs"]
    assert proposal["l3_representation_refs"]
    assert proposal["included_summary_refs"]

    filtered = client.get(
        "/control-center/memory/context-packs",
        params={"query_ref": receipt_ref},
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["context_pack_count"] == 1

    unsafe = client.get(
        "/control-center/memory/context-packs",
        params={"query_ref": "raw_prompt"},
    )
    assert unsafe.status_code == 400


def test_context_pack_route_manifest_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}
    route = routes["/control-center/memory/context-packs"]

    assert route.method == "GET"
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.idempotency_required is False
    assert route.rate_limit_group is None
    assert "control_center_memory_context_pack_proposals" in (
        manifest.capabilities_declared
    )
    for blocked in [
        "control_center_memory_context_pack_hidden_injection",
        "control_center_memory_context_pack_prompt_stuffing",
        "control_center_memory_context_pack_provider_model_calls",
        "control_center_memory_context_pack_phase6_execution_hooks",
    ]:
        assert blocked in manifest.capabilities_blocked
