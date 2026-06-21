from typing import Any
from ultimate_ai_agent.core.truth import (
    SourceConflictSeverity,
    TruthAuthorityLevel,
    TruthSourceManifest,
    TruthSourceType,
    resolve_source_conflict,
)


def source(source_id: str, source_type: Any, authority: Any, **metadata: Any) -> Any:
    return TruthSourceManifest(
        source_id=source_id,
        source_type=source_type,
        authority_level=authority,
        display_name=source_id,
        owner="tests",
        allowed_scopes=["project"],
        allowed_purposes=["answer"],
        data_classification="project_private",
        metadata=metadata,
    )


def test_canonical_beats_memory_conflict() -> None:
    report = resolve_source_conflict(
        claim_id="claim_project",
        sources=[
            source("src_memory", TruthSourceType.memory, TruthAuthorityLevel.medium),
            source("src_canonical", TruthSourceType.canonical_file, TruthAuthorityLevel.authoritative),
        ],
        description="Memory conflicts with canonical file.",
    )

    assert report.preferred_source_id == "src_canonical"
    assert "CANONICAL_OVERRIDES_MEMORY" in report.reason_codes


def test_api_database_beats_document_for_hard_live_fact() -> None:
    report = resolve_source_conflict(
        claim_id="claim_metric",
        sources=[
            source("src_doc", TruthSourceType.approved_document, TruthAuthorityLevel.high),
            source("src_api", TruthSourceType.api, TruthAuthorityLevel.authoritative),
        ],
        description="Document conflicts with API.",
        hard_live_fact=True,
    )

    assert report.preferred_source_id == "src_api"
    assert "STRUCTURED_SOURCE_OVERRIDES_DOCUMENT" in report.reason_codes


def test_stale_provider_result_does_not_automatically_beat_current_canonical() -> None:
    report = resolve_source_conflict(
        claim_id="claim_stale",
        sources=[
            source("src_provider", TruthSourceType.provider_result, TruthAuthorityLevel.authoritative, freshness_status="stale"),
            source("src_canonical", TruthSourceType.canonical_file, TruthAuthorityLevel.high, freshness_status="current"),
        ],
        description="Stale provider conflicts with canonical.",
        hard_live_fact=True,
    )

    assert report.preferred_source_id is None
    assert report.requires_human_review is True


def test_unresolved_conflict_requires_human_review() -> None:
    report = resolve_source_conflict(
        claim_id="claim_unresolved",
        sources=[
            source("src_a", TruthSourceType.approved_document, TruthAuthorityLevel.medium),
            source("src_b", TruthSourceType.external_source, TruthAuthorityLevel.medium),
        ],
        description="No deterministic policy applies.",
    )

    assert report.severity == SourceConflictSeverity.medium
    assert report.requires_human_review is True
