from __future__ import annotations

import json
import sqlite3
import subprocess
import sys

import pytest

from ultimate_ai_agent.core.news_signals import (
    NewsSignalArtifact,
    NewsSignalSource,
    NewsSignalsAdoptionStore,
    NewsSignalsRepository,
)


def _seed_adopted_schema(state_dir):
    """Explicit synthetic fixture setup, not an implicit inspection side effect."""
    NewsSignalsRepository(state_dir)
    store = NewsSignalsAdoptionStore(state_dir)
    with sqlite3.connect(store.db_path) as conn:
        store._ensure_adoption_schema(conn)
    return store


@pytest.mark.parametrize("q24_only", [False, True])
def test_inspection_cli_does_not_initialize_news(tmp_path, q24_only):
    state_dir = tmp_path / "news"
    database = state_dir / "news_signals.sqlite3"
    if q24_only:
        import gc

        NewsSignalsRepository(state_dir)
        gc.collect()
    before = database.read_bytes() if database.exists() else None
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_news_signals_adoption.py",
            "--state-dir",
            str(state_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout)["workspace"]["storage_status"] == (
        "q24_only" if q24_only else "missing"
    )
    assert (database.read_bytes() if database.exists() else None) == before
    if not q24_only:
        assert not state_dir.exists()


def test_adoption_inspection_cli_is_content_safe(tmp_path) -> None:
    store = _seed_adopted_schema(tmp_path)
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

    assert payload["schema_version"] == ("uaa-news-signals-adoption-inspection.v1")
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
    assert payload["workspace"]["active_signal_refs"] == ["signal-ref:q34:cli-active"]
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


@pytest.mark.parametrize("failure", ("database", "undo", "state-file"))
def test_adoption_inspection_cli_failures_are_content_safe(tmp_path, failure) -> None:
    state_dir = tmp_path / "private-inspection-state"
    if failure == "state-file":
        state_dir.write_text("private invalid state", encoding="utf-8")
    elif failure == "database":
        state_dir.mkdir()
        (state_dir / "news_signals.sqlite3").write_bytes(b"private truncated database")
    else:
        store = _seed_adopted_schema(state_dir)
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                "INSERT INTO news_signals_adoption_undo(singleton, snapshot_json) "
                "VALUES (1, ?)",
                ("private invalid undo",),
            )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_news_signals_adoption.py",
            "--state-dir",
            str(state_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["error"]["code"] == "NEWS_SIGNALS_ADOPTION_INSPECTION_BLOCKED"
    assert payload["workspace"] is None
    assert payload["raw_paths_included"] is False
    assert payload["raw_source_content_included"] is False
    assert payload["external_network_read_performed"] is False
    assert payload["model_call_performed"] is False
    assert str(tmp_path) not in result.stdout
    assert "Traceback" not in result.stdout
    assert "private invalid" not in result.stdout
    assert "private truncated" not in result.stdout


@pytest.mark.parametrize("option", ("--limit", "--unknown-option"))
def test_adoption_inspection_cli_argument_errors_do_not_echo_input(option) -> None:
    private_value = "private-input-marker"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_news_signals_adoption.py",
            option,
            private_value,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["error"]["code"] == "NEWS_SIGNALS_ADOPTION_INSPECTION_BLOCKED"
    assert private_value not in result.stdout
