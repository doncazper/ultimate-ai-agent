from __future__ import annotations

import json
import sqlite3
import subprocess
import sys

from ultimate_ai_agent.core.news_signals import (
    NewsSignalArtifact,
    NewsSignalSource,
    NewsSignalsAdoptionStore,
)


def test_adoption_inspection_cli_is_content_safe(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = "source-ref:q34:private-cli-source"
    store.repository.upsert_source(
        NewsSignalSource(
            source_ref=source_ref,
            source_kind="official",
            safe_label="Private source label",
            state="ready",
            observed_at="2026-09-09T10:00:00Z",
            freshness_ttl_seconds=86_400,
            adapter_ref="connector-adapter-ref:q34:cli-test",
            provenance_ref="provenance-ref:q34:cli-test",
            retention_ref="retention-ref:q34:cli-test",
            reason_refs=("reason-ref:q34:cli-test",),
        )
    )
    for suffix, title, summary in (
        ("active", "Private active headline", "Private active summary"),
        ("archived", "Private archived headline", "Private archived summary"),
    ):
        store.repository.ingest_artifact(
            NewsSignalArtifact(
                artifact_ref=f"signal-ref:q34:cli-{suffix}",
                source_ref=source_ref,
                source_revision_ref=f"source-revision-ref:q34:cli-{suffix}",
                content_digest_ref=f"content-digest-ref:q34:cli-{suffix}",
                cluster_ref=f"cluster-ref:q34:cli-{suffix}",
                claim_ref=f"claim-ref:q34:cli-{suffix}",
                title=title,
                safe_summary=summary,
                source_label="Private source label",
                topic_ref=f"topic-ref:q34:cli-{suffix}",
                published_at="2026-09-09T11:00:00Z",
                observed_at="2026-09-09T12:00:00Z",
                confidence_percent=90,
                evidence_class="primary",
                claim_stance="supports",
                provenance_refs=(f"provenance-ref:q34:cli-{suffix}",),
            )
        )
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "INSERT INTO news_signal_archives(artifact_ref, archived) VALUES (?, 1)",
            ("signal-ref:q34:cli-archived",),
        )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_news_signals_adoption.py",
            "--state-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == (
        "uaa-news-signals-adoption-inspection.v1"
    )
    assert payload["workspace"]["revision"] == 0
    assert payload["workspace"]["status"] == "ready"
    assert payload["workspace"]["counts"] == {
        "active_signals": 1,
        "archived_signals": 1,
        "briefing_candidates": 0,
        "preferences": 0,
        "ranked_summary_items": 1,
        "returned_active_signal_refs": 1,
        "sources": 1,
        "today_items": 0,
    }
    assert payload["workspace"]["private_values_included"] is False
    assert payload["workspace"]["active_signal_refs"] == [
        "signal-ref:q34:cli-active"
    ]
    assert payload["external_network_read_performed"] is False
    assert payload["model_call_performed"] is False
    assert payload["raw_paths_included"] is False
    assert str(tmp_path) not in result.stdout
    for private_value in (
        "Private source label",
        "Private active headline",
        "Private active summary",
        "Private archived headline",
        "Private archived summary",
    ):
        assert private_value not in result.stdout
