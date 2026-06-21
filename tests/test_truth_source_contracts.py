import pytest

from ultimate_ai_agent.core.truth import (
    TruthRouterManifest,
    TruthSourceKind,
    TruthSourcePriority,
    TruthSourceRef,
    TruthSourceStatus,
    build_truth_router_manifest,
)


def test_default_truth_router_manifest_disables_external_authority() -> None:
    manifest = build_truth_router_manifest("0.29.0")

    assert isinstance(manifest, TruthRouterManifest)
    assert manifest.truth_router_enabled is True
    assert manifest.external_verification_enabled is False
    assert manifest.web_search_enabled is False
    assert manifest.model_verification_enabled is False
    assert manifest.memory_as_authority_enabled is False
    assert manifest.automatic_claim_verification_enabled is False


def test_truth_source_ref_rejects_arbitrary_or_secret_refs() -> None:
    with pytest.raises(ValueError, match="structured source_ref"):
        TruthSourceRef(
            source_ref="not-structured",
            source_kind=TruthSourceKind.canonical_document,
            source_priority=TruthSourcePriority.canonical,
            source_status=TruthSourceStatus.active,
            safe_label="Canonical roadmap",
        )

    with pytest.raises(ValueError, match="secret-like"):
        TruthSourceRef(
            source_ref="canonical:roadmap",
            source_kind=TruthSourceKind.canonical_document,
            source_priority=TruthSourcePriority.canonical,
            source_status=TruthSourceStatus.active,
            safe_label="api_key=abc123",
        )


def test_truth_source_ref_blocks_memory_authority() -> None:
    with pytest.raises(ValueError, match="Memory cannot be authoritative"):
        TruthSourceRef(
            source_ref="memory:source-linked",
            source_kind=TruthSourceKind.source_linked_memory,
            source_priority=TruthSourcePriority.source_linked_memory,
            source_status=TruthSourceStatus.active,
            safe_label="Reviewed memory summary",
            authority_level="authoritative",
        )
