import pytest

from ultimate_ai_agent.core.recall import (
    RecallCandidate,
    RecallSourceKind,
    RecallSelection,
)


def test_recall_selection_rejects_secret_like_metadata_refs():
    with pytest.raises(ValueError, match="secret"):
        RecallSelection(
            candidate_ref="recall:candidate:secret-ref",
            source_ref="canonical:m26",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="Safe summary.",
            priority_rank=0,
            token_estimate=4,
            metadata_refs=["api_key:super-secret-value"],
        )


def test_context_pack_build_request_rejects_raw_content_in_decision():
    with pytest.raises(ValueError, match="raw"):
        RecallSelection(
            candidate_ref="recall:candidate:raw",
            source_ref="canonical:m26",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="Safe summary.",
            priority_rank=0,
            token_estimate=4,
            metadata={"raw_prompt": "not allowed"},
        )


def test_recall_candidate_rejects_private_local_path_metadata():
    with pytest.raises(ValueError, match="private"):
        RecallCandidate(
            candidate_ref="recall:candidate:path",
            source_ref="canonical:m26",
            source_kind=RecallSourceKind.canonical_document,
            safe_summary="Safe summary.",
            metadata={"path": "/Users/example/private.txt"},
        )
