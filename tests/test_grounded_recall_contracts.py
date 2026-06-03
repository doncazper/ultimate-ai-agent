import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.recall import (
    GroundedRecallManifest,
    GroundedRecallRequest,
    RecallCandidate,
    RecallCandidateStatus,
    RecallSourceKind,
)


def test_grounded_recall_models_are_contract_only_and_forbid_extra_fields():
    candidate = RecallCandidate(
        candidate_ref="recall:candidate:canonical",
        source_ref="canonical:m26",
        source_kind=RecallSourceKind.canonical_document,
        safe_summary="Canonical roadmap summary for M26.",
        evidence_refs=["evidence:m26"],
        token_estimate=12,
    )
    request = GroundedRecallRequest(
        request_id="recall:req:001",
        query_summary="Need safe M26 roadmap context.",
        candidates=[candidate],
        max_candidates=3,
        max_context_tokens=120,
    )

    assert request.candidates[0].source_kind == RecallSourceKind.canonical_document
    assert request.enable_vector_search is False
    assert request.enable_embeddings is False
    assert request.enable_external_retrieval is False
    assert request.context_injection_enabled is False

    with pytest.raises(ValidationError):
        RecallCandidate(
            candidate_ref="recall:candidate:extra",
            source_ref="canonical:extra",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="Safe summary.",
            raw_content="not allowed",
        )


def test_grounded_recall_manifest_defaults_disable_runtime_behaviors():
    manifest = GroundedRecallManifest(baseline_version="0.30.0")

    assert manifest.recall_router_enabled is True
    assert manifest.context_pack_builder_enabled is True
    assert manifest.context_injection_enabled is False
    assert manifest.vector_search_enabled is False
    assert manifest.embeddings_enabled is False
    assert manifest.semantic_search_enabled is False
    assert manifest.rag_ingestion_enabled is False
    assert manifest.external_retrieval_enabled is False
    assert manifest.source_crawling_enabled is False
    assert manifest.automatic_memory_write_enabled is False
    assert manifest.backend_routes_added is False


def test_grounded_recall_request_rejects_unsafe_runtime_flags():
    candidate = RecallCandidate(
        candidate_ref="recall:candidate:flag",
        source_ref="canonical:m26",
        source_kind=RecallSourceKind.canonical_document,
        safe_summary="Canonical summary.",
    )

    for field in [
        "allow_model_output",
        "allow_runtime_output",
        "allow_openwebui_output",
        "allow_raw_content",
        "enable_vector_search",
        "enable_embeddings",
        "enable_external_retrieval",
        "enable_source_crawling",
        "automatic_memory_write",
        "context_injection_enabled",
    ]:
        with pytest.raises(ValueError, match=field):
            GroundedRecallRequest(
                request_id=f"recall:req:{field}",
                query_summary="Need safe recall context.",
                candidates=[candidate],
                **{field: True},
            )


def test_grounded_recall_candidate_rejects_raw_or_secret_like_summary():
    with pytest.raises(ValueError, match="raw"):
        RecallCandidate(
            candidate_ref="recall:candidate:raw",
            source_ref="canonical:m26",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="raw prompt transcript should not appear",
        )

    with pytest.raises(ValueError, match="secret"):
        RecallCandidate(
            candidate_ref="recall:candidate:secret",
            source_ref="canonical:m26",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="api_key=sk-test-secret-value",
        )


def test_grounded_recall_status_enum_blocks_revoked_and_deleted_sources():
    assert RecallCandidateStatus.revoked.value == "revoked"
    assert RecallCandidateStatus.deleted.value == "deleted"
    assert RecallCandidateStatus.superseded.value == "superseded"
