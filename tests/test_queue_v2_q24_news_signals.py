from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import route_side_effect_class
from ultimate_ai_agent.core.news_signals import (
    NewsSignalArtifact,
    NewsSignalPreference,
    NewsSignalSource,
    NewsSignalsRepository,
    build_news_signals_summary,
)


NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def _source(
    suffix: str = "official",
    *,
    kind: str = "official",
    state: str = "ready",
    ttl: int = 86_400,
) -> NewsSignalSource:
    return NewsSignalSource(
        source_ref=f"source-ref:q24:{suffix}",
        source_kind=kind,  # type: ignore[arg-type]
        safe_label=f"{suffix.title()} source",
        state=state,  # type: ignore[arg-type]
        observed_at="2026-08-22T11:30:00Z",
        freshness_ttl_seconds=ttl,
        reason_refs=("reason-ref:q24:local-artifact-ready",),
    )


def _artifact(
    suffix: str = "one",
    *,
    source_suffix: str = "official",
    published_at: str = "2026-08-22T10:00:00Z",
    confidence: int = 88,
    evidence_class: str = "primary",
    claim_stance: str = "supports",
    claim_suffix: str = "claim-one",
    cluster_suffix: str = "cluster-one",
) -> NewsSignalArtifact:
    return NewsSignalArtifact(
        artifact_ref=f"signal-ref:q24:{suffix}",
        source_ref=f"source-ref:q24:{source_suffix}",
        source_revision_ref=f"source-revision-ref:q24:{suffix}",
        content_digest_ref=f"content-digest-ref:q24:{suffix}",
        cluster_ref=f"cluster-ref:q24:{cluster_suffix}",
        claim_ref=f"claim-ref:q24:{claim_suffix}",
        title=f"Bounded signal {suffix}",
        safe_summary="A bounded redacted summary supplied by a local source lane.",
        source_label=f"{source_suffix.title()} source",
        topic_ref="topic-ref:q24:agent-governance",
        published_at=published_at,
        observed_at="2026-08-22T11:30:00Z",
        confidence_percent=confidence,
        evidence_class=evidence_class,  # type: ignore[arg-type]
        claim_stance=claim_stance,  # type: ignore[arg-type]
        interest_refs=("interest-ref:q24:agent-governance",),
        provenance_refs=(
            f"provenance-ref:q24:{suffix}",
            f"evidence-ref:q24:{suffix}",
        ),
    )


def test_empty_projection_is_truthfully_blocked_without_source() -> None:
    result = build_news_signals_summary(sources=(), artifacts=(), now=NOW)

    assert result["status"] == "blocked_no_graduated_source"
    assert result["items"] == []
    assert result["live_fetch_enabled"] is False
    assert result["authenticated_source_enabled"] is False
    assert result["model_summarization_enabled"] is False
    assert result["connector_write_enabled"] is False
    assert result["action_authority_granted"] is False
    assert result["blocked_state_refs"] == [
        "blocked-state-ref:q24:no-graduated-news-source"
    ]


def test_ranking_is_deterministic_and_explainable() -> None:
    official = _source()
    community = _source("community", kind="community")
    preferred = NewsSignalPreference(
        topic_ref="topic-ref:q24:agent-governance",
        weight=20,
        preference_ref="preference-ref:q24:agent-governance",
    )
    result = build_news_signals_summary(
        sources=(official, community),
        artifacts=(
            _artifact(
                "community",
                source_suffix="community",
                evidence_class="community",
                cluster_suffix="community",
            ),
            _artifact("official", cluster_suffix="official"),
        ),
        preferences=(preferred,),
        now=NOW,
    )

    items = result["items"]
    assert isinstance(items, list)
    assert [item["signal_ref"] for item in items] == [
        "signal-ref:q24:official",
        "signal-ref:q24:community",
    ]
    assert (
        "rank-reason-ref:q24:explicit-topic-preference" in items[0]["rank_reason_refs"]
    )
    assert items[0]["external_content_untrusted"] is True
    assert items[0]["briefing_candidate"] is True


def test_cluster_deduplication_preserves_coverage() -> None:
    result = build_news_signals_summary(
        sources=(_source(), _source("community", kind="community")),
        artifacts=(
            _artifact("primary"),
            _artifact(
                "corroborating",
                source_suffix="community",
                evidence_class="corroborating",
            ),
        ),
        now=NOW,
    )

    items = result["items"]
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]["coverage_count"] == 2
    assert items[0]["coverage_source_refs"] == [
        "source-ref:q24:community",
        "source-ref:q24:official",
    ]


def test_stale_and_conflicting_items_never_enter_briefing_projection() -> None:
    result = build_news_signals_summary(
        sources=(_source(), _source("community", kind="community")),
        artifacts=(
            _artifact(
                "stale",
                published_at="2026-08-18T10:00:00Z",
                cluster_suffix="stale",
                claim_suffix="stale",
            ),
            _artifact(
                "support",
                cluster_suffix="conflict-a",
                claim_suffix="conflict",
            ),
            _artifact(
                "dispute",
                source_suffix="community",
                evidence_class="community",
                claim_stance="disputes",
                cluster_suffix="conflict-b",
                claim_suffix="conflict",
            ),
        ),
        now=NOW,
    )

    assert result["conflicting_claim_refs"] == ["claim-ref:q24:conflict"]
    assert result["morning_briefing_projection"]["candidate_refs"] == []
    assert all(item["briefing_candidate"] is False for item in result["items"])


def test_unavailable_source_artifacts_are_withheld_from_visible_truth() -> None:
    result = build_news_signals_summary(
        sources=(_source(state="revoked"),),
        artifacts=(_artifact(),),
        now=NOW,
    )

    assert result["status"] == "blocked_source_unavailable"
    assert result["items"] == []
    assert result["today_projection"]["item_refs"] == []
    assert result["morning_briefing_projection"]["candidate_refs"] == []
    assert result["blocked_state_refs"] == ["blocked-state-ref:q24:source-unavailable"]


def test_briefing_candidates_are_selected_before_stream_truncation() -> None:
    result = build_news_signals_summary(
        sources=(_source(),),
        artifacts=(
            _artifact(
                "conflict-support",
                confidence=100,
                claim_suffix="conflict",
                cluster_suffix="conflict-support",
            ),
            _artifact(
                "conflict-dispute",
                confidence=100,
                claim_stance="disputes",
                claim_suffix="conflict",
                cluster_suffix="conflict-dispute",
            ),
            _artifact(
                "eligible",
                confidence=60,
                evidence_class="commentary",
                claim_suffix="eligible",
                cluster_suffix="eligible",
            ),
        ),
        now=NOW,
        limit=1,
    )

    assert result["items"][0]["conflict_state"] == "conflicting"
    assert result["morning_briefing_projection"]["candidate_refs"] == [
        "signal-ref:q24:eligible"
    ]


def test_repository_persists_idempotent_redacted_artifacts(tmp_path) -> None:
    repository = NewsSignalsRepository(tmp_path)
    source_receipt = repository.upsert_source(_source())
    artifact_receipt = repository.ingest_artifact(_artifact())
    replay_receipt = repository.ingest_artifact(_artifact())

    result = repository.summary(now=NOW)
    assert source_receipt.startswith("receipt-ref:q24:source:")
    assert artifact_receipt == replay_receipt
    assert len(result["items"]) == 1
    assert result["items"][0]["signal_ref"] == "signal-ref:q24:one"


def test_repository_rejects_same_revision_with_changed_payload(tmp_path) -> None:
    repository = NewsSignalsRepository(tmp_path)
    repository.upsert_source(_source())
    repository.ingest_artifact(_artifact())
    changed = _artifact().__dict__.copy()
    changed["safe_summary"] = "A different bounded summary with the same revision."

    with pytest.raises(ValueError, match="ARTIFACT_REVISION_CONFLICT"):
        repository.ingest_artifact(NewsSignalArtifact(**changed))


def test_repository_accepts_changed_payload_under_new_source_revision(tmp_path) -> None:
    repository = NewsSignalsRepository(tmp_path)
    repository.upsert_source(_source())
    first_receipt = repository.ingest_artifact(_artifact())
    changed = _artifact().__dict__.copy()
    changed["safe_summary"] = "A different bounded summary under a new revision."
    changed["source_revision_ref"] = "source-revision-ref:q24:one-v2"
    second_receipt = repository.ingest_artifact(
        NewsSignalArtifact(**changed),
        expected_current_source_revision_ref="source-revision-ref:q24:one",
    )

    assert first_receipt != second_receipt
    assert (
        repository.summary(now=NOW)["items"][0]["safe_summary"]
        == changed["safe_summary"]
    )


def test_repository_rejects_delayed_stale_revision_replay(tmp_path) -> None:
    repository = NewsSignalsRepository(tmp_path)
    repository.upsert_source(_source())
    revision_one = _artifact()
    repository.ingest_artifact(revision_one)
    revision_two_values = revision_one.__dict__.copy()
    revision_two_values["source_revision_ref"] = "source-revision-ref:q24:one-v2"
    revision_two_values["safe_summary"] = "A bounded second revision summary."
    repository.ingest_artifact(
        NewsSignalArtifact(**revision_two_values),
        expected_current_source_revision_ref=revision_one.source_revision_ref,
    )

    with pytest.raises(ValueError, match="ARTIFACT_STALE_REVISION_REPLAY"):
        repository.ingest_artifact(
            revision_one,
            expected_current_source_revision_ref=revision_one.source_revision_ref,
        )

    assert repository.summary(now=NOW)["items"][0]["source_revision_ref"] == (
        "source-revision-ref:q24:one-v2"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "https://unsafe.example/article"),
        ("safe_summary", "contact operator@example.test"),
        ("source_label", "/Users/example/private"),
        ("title", "Update from localhost is unavailable"),
        ("safe_summary", "Observed service address [2001:db8::1]"),
    ],
)
def test_artifact_rejects_raw_locator_or_identity_content(
    field: str, value: str
) -> None:
    values = _artifact().__dict__.copy()
    values[field] = value
    with pytest.raises(ValueError, match="REDACTION_REQUIRED"):
        NewsSignalArtifact(**values)


def test_artifact_requires_registered_source(tmp_path) -> None:
    repository = NewsSignalsRepository(tmp_path)
    with pytest.raises(ValueError, match="ARTIFACT_SOURCE_NOT_REGISTERED"):
        repository.ingest_artifact(_artifact())


def test_source_readiness_is_bounded_in_memory_and_storage(tmp_path) -> None:
    sources = tuple(_source(f"source-{index}") for index in range(25))
    with pytest.raises(ValueError, match="SOURCE_READINESS_LIMIT_EXCEEDED"):
        build_news_signals_summary(sources=sources, artifacts=(), now=NOW)

    repository = NewsSignalsRepository(tmp_path)
    for source in sources[:24]:
        repository.upsert_source(source)
    with pytest.raises(ValueError, match="SOURCE_READINESS_LIMIT_EXCEEDED"):
        repository.upsert_source(sources[24])
    assert len(repository.summary(now=NOW)["source_readiness"]) == 24


def test_repository_reads_sources_and_artifacts_from_one_snapshot(
    monkeypatch, tmp_path
) -> None:
    repository = NewsSignalsRepository(tmp_path)
    repository.upsert_source(_source())
    repository.ingest_artifact(_artifact())
    statements: list[str] = []

    def tracked_connect() -> sqlite3.Connection:
        conn = sqlite3.connect(repository.db_path)
        conn.row_factory = sqlite3.Row
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(repository, "_connect", tracked_connect)
    repository.summary(now=NOW)

    begin_index = statements.index("BEGIN")
    source_select_index = next(
        index
        for index, statement in enumerate(statements)
        if "FROM news_signal_sources" in statement
    )
    artifact_select_index = next(
        index
        for index, statement in enumerate(statements)
        if "FROM news_signal_artifacts" in statement
    )
    assert begin_index < source_select_index < artifact_select_index


def test_news_signals_route_declares_local_storage_side_effect() -> None:
    assert (
        route_side_effect_class("/control-center/news-signals/summary").value
        == "local_dev_workspace_only"
    )


def test_api_returns_backend_owned_empty_truth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "state"))
    response = TestClient(app).get("/control-center/news-signals/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["backend_owned"] is True
    assert payload["data"]["status"] == "blocked_no_graduated_source"
    assert payload["data"]["items"] == []
    assert "raw_source_content_omitted" in payload["redactions_applied"]


def test_api_and_founder_loop_projections_share_backend_truth(
    monkeypatch, tmp_path
) -> None:
    state_dir = tmp_path / "state"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    repository = NewsSignalsRepository(state_dir)
    repository.upsert_source(_source())
    repository.ingest_artifact(_artifact())
    client = TestClient(app)

    news = client.get("/control-center/news-signals/summary").json()["data"]
    today = client.get("/control-center/today/summary").json()["data"]
    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]

    assert today["news_signals_projection"] == news["today_projection"]
    assert briefing["news_signals_projection"] == news["morning_briefing_projection"]
