import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import scripts.benchmark_repo_awareness as benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_repo_awareness_snapshot_scores_are_deterministic_and_safe() -> None:
    snapshot = benchmark.build_snapshot(
        root=ROOT,
        reason="manual_review",
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )

    assert snapshot["schema_version"] == "uaa_repo_awareness_benchmark.v1"
    assert snapshot["task_ref"] == "UAA-BENCH-001"
    assert snapshot["scan_mode"] == "whole_repo_deterministic"
    assert snapshot["reason"] == "manual-review"
    assert snapshot["weekly_review_model"]["mode"] == "reminder_plus_manual_command"
    assert snapshot["weekly_review_model"]["unattended_repo_writes"] is False
    assert snapshot["weekly_review_model"]["auto_commit"] is False
    assert {category["id"] for category in snapshot["categories"]} == set(benchmark.CATEGORY_WEIGHTS)
    assert snapshot["score_summary"]["overall_score"] == benchmark._overall_score(snapshot["categories"])
    assert all(value is False for value in snapshot["report_safety"].values())
    assert benchmark.validate_benchmark_snapshot(snapshot, root=ROOT) == []


def test_repo_awareness_snapshot_rejects_unknown_tier_and_score_mismatch() -> None:
    snapshot = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )
    broken = copy.deepcopy(snapshot)
    broken["categories"][0]["tier"] = "vibes"
    broken["score_summary"]["overall_score"] = 99

    failures = benchmark.validate_benchmark_snapshot(broken, root=ROOT)

    assert any("tier does not match score" in failure for failure in failures)
    assert any("does not match weighted category score" in failure for failure in failures)


def test_repo_awareness_snapshot_rejects_missing_evidence_path() -> None:
    snapshot = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )
    broken = copy.deepcopy(snapshot)
    broken["categories"][0]["evidence_refs"] = ["docs/not-real-benchmark-evidence.md"]

    failures = benchmark.validate_benchmark_snapshot(broken, root=ROOT)

    assert any("evidence ref is not a safe known ref" in failure for failure in failures)


def test_repo_awareness_snapshot_rejects_raw_private_fragments() -> None:
    snapshot = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )
    broken = copy.deepcopy(snapshot)
    broken["categories"][0]["safe_summary"] = "raw prompt: not allowed"

    failures = benchmark.validate_benchmark_snapshot(broken, root=ROOT)

    assert any("forbidden raw/private fragment" in failure for failure in failures)


def test_repo_awareness_compare_reports_deltas() -> None:
    older = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:1111111",
    )
    newer = copy.deepcopy(older)
    newer["benchmark_id"] = "repo-awareness-benchmark:20260620t120000z:manual-review"
    newer["generated_at_utc"] = "2026-06-20T12:00:00Z"
    newer["categories"][0]["score"] = min(100, newer["categories"][0]["score"] + 5)
    newer["categories"][0]["tier"] = benchmark.tier_for_score(newer["categories"][0]["score"])
    newer["score_summary"]["overall_score"] = benchmark._overall_score(newer["categories"])
    newer["score_summary"]["overall_tier"] = benchmark.tier_for_score(newer["score_summary"]["overall_score"])

    comparison = benchmark.compare_snapshots(older, newer, since="7d")

    assert comparison["schema_version"] == "uaa_repo_awareness_comparison.v1"
    assert comparison["status"] == "compared"
    assert comparison["overall_delta"] >= 0
    assert any(item["category_id"] == "module_maturity" for item in comparison["category_deltas"])


def test_repo_awareness_compare_reports_missing_prior_snapshot() -> None:
    latest = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )

    comparison = benchmark.compare_snapshots(None, latest, since="24h")

    assert comparison["status"] == "no_prior_snapshot"
    assert comparison["overall_delta"] is None
    assert comparison["safe_summary"] == "No prior benchmark snapshot exists for the requested comparison window."


def test_repo_awareness_write_snapshot_creates_latest_and_index(tmp_path: Path) -> None:
    source = ROOT / "docs"
    target_docs = tmp_path / "docs"
    target_benchmark = target_docs / "benchmarks" / "repo_awareness"
    target_benchmark.mkdir(parents=True)
    # The write path only needs the benchmark directory in this test.
    snapshot = benchmark.build_snapshot(
        root=ROOT,
        generated_at=datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc),
        commit_ref="commit:abcdef0",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)

    refs = benchmark.write_snapshot(snapshot, root=tmp_path)

    assert (tmp_path / refs["latest_json"]).exists()
    assert (tmp_path / refs["latest_md"]).exists()
    assert (tmp_path / refs["index_md"]).exists()
    assert json.loads((tmp_path / refs["latest_json"]).read_text(encoding="utf-8"))["benchmark_id"] == snapshot["benchmark_id"]
    assert source.exists()


def test_repo_awareness_verifier_passes_current_repo() -> None:
    assert benchmark.validate_repo_awareness_benchmark(root=ROOT) == []
