from typing import Any
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import scripts.run_foundation_gate as run_foundation_gate
from ultimate_ai_agent.core.gate.reports import FoundationGateResult, build_foundation_gate_report


class _FastFoundationGateEvaluator:
    def __init__(self, root: Any | None = None) -> None:
        self.root = root

    def evaluate(self) -> Any:
        return build_foundation_gate_report(
            version="test",
            results=[
                FoundationGateResult(
                    criterion_id="test_fast_gate_report",
                    status=run_foundation_gate.FoundationGateStatus.passed,
                    safe_message="Fast test report generated without repository scan.",
                )
            ],
        )


def _use_fast_gate_report(monkeypatch: pytest.MonkeyPatch) -> None:
    def fast_latency_summary(
        *,
        foundation_gate_report_json: Any,
        foundation_gate_report_md: Any,
        write_report: bool = True,
        precomputed_foundation_gate_ms: Any | None = None,
        precomputed_foundation_gate_status: Any | None = None,
        precomputed_foundation_gate_result_count: Any | None = None,
    ) -> Any:
        assert precomputed_foundation_gate_ms is not None
        assert precomputed_foundation_gate_status == "passed"
        assert precomputed_foundation_gate_result_count == 1
        return run_foundation_gate.FoundationGateLatencySummary(
            schema_version="uaa_foundation_gate_latency_summary.v1",
            task_ref="UAA-P1-043",
            status="passed",
            p50_p95_status="passed",
            foundation_gate_status="passed",
            foundation_gate_best_ms=1.0,
            foundation_gate_mean_ms=1.0,
            foundation_gate_best_budget_ms=20_000.0,
            foundation_gate_mean_budget_ms=25_000.0,
            release_latency_status="passed",
            hot_path_profile_status="passed",
            accepted_failures=[],
            failures=[],
            report_refs={}
            if not write_report
            else {
                "release_latency_report_json": (
                    "reports/performance/latest_release_latency_baseline.json"
                )
            },
            foundation_gate_report_json=foundation_gate_report_json,
            foundation_gate_report_md=foundation_gate_report_md,
            environment_safe_summary={
                "machine_identity_recorded": False,
                "environment_variables_recorded": False,
                "raw_paths_recorded": False,
            },
            authority_invariants={
                "authority_decisions_cached_for_speed": False,
                "foundation_gate_checks_preserved": True,
            },
            report_safety={
                "path_material_included": False,
                "credential_material_included": False,
            },
            path_results=[
                {
                    "path_id": "api_manifest",
                    "safe_label": "GET /api/manifest",
                    "required": True,
                    "status": "passed",
                    "samples": 1,
                    "p50_ms": 1.0,
                    "p95_ms": 1.0,
                    "budget_ms": 150.0,
                    "budget_status": "within_budget",
                    "reason_codes": [],
                    "authority_path_bypassed_for_speed": False,
                    "authority_decision_cached_for_speed": False,
                    "request_body_recorded": False,
                    "response_body_recorded": False,
                }
            ],
            optional_prerequisites=[],
        )

    monkeypatch.setattr(
        run_foundation_gate,
        "FoundationGateEvaluator",
        _FastFoundationGateEvaluator,
    )
    monkeypatch.setattr(
        run_foundation_gate,
        "exact_repository_revision",
        lambda _root: "git-sha:" + "a" * 40,
    )
    monkeypatch.setattr(
        run_foundation_gate,
        "build_latency_gate_summary",
        fast_latency_summary,
    )
    monkeypatch.setattr(
        run_foundation_gate,
        "build_release_lane_summary",
        lambda: run_foundation_gate.FoundationGateReleaseLaneSummary(
            schema_version="uaa_release_verification_lanes.v1",
            task_ref="UAA-P1-013",
            overall_status="definition_pass",
            definition_status="pass",
            command_execution_status="not_executed",
            lane_count=8,
            lane_ids=[
                "docs",
                "openapi",
                "api-safety",
                "security-redaction",
                "local-model-e2e",
                "durability",
                "frontend",
                "performance",
            ],
            status_semantics={
                "pass": "passed",
                "fail": "failed",
                "skipped": "skipped",
                "blocked": "blocked",
                "accepted_failure": "accepted failure",
            },
            accepted_failures=[],
            validation_failures=[],
            report_safety={"credential_material_included": False},
            safe_summary="Release lane definitions validated; commands not executed.",
        ),
    )


def test_run_foundation_gate_writes_requested_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fast_gate_report(monkeypatch)
    monkeypatch.setattr(run_foundation_gate, "ROOT", tmp_path)
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(["--skip-commands", "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "passed"
    assert payload["command_mode"] == "report-only"
    assert payload["command_receipts"][0]["status"] == "report_only"
    assert (
        "No external verifier commands were run"
        in payload["command_receipts"][0]["safe_summary"]
    )
    assert "local read/probe code" in payload["command_receipts"][0]["safe_summary"]
    assert payload["latency_gate"]["schema_version"] == "uaa_foundation_gate_latency_summary.v1"
    assert payload["latency_gate"]["status"] == "passed"
    assert payload["latency_gate"]["foundation_gate_report_json"] == (
        "reports/foundation_gate/latest_foundation_gate_report.json"
    )
    assert payload["release_verification_lanes"]["schema_version"] == (
        "uaa_release_verification_lanes.v1"
    )
    assert payload["release_verification_lanes"]["definition_status"] == "pass"
    assert payload["release_verification_lanes"]["command_execution_status"] == "not_executed"
    assert payload["release_verification_lanes"]["lane_count"] == 8
    expected_count = len(payload["results"])
    assert payload["summary"] == f"{expected_count} passed, 0 failed, 0 warnings, 0 blocked."


def test_run_foundation_gate_ci_mode_records_external_verify_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fast_gate_report(monkeypatch)
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(
        ["--command-mode", "ci-after-verify-all", "--no-write-latest", "--output", str(output_path)]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["command_mode"] == "ci-after-verify-all"
    assert payload["command_receipts"][0]["command_ref"] == "command:scripts.verify_all"
    assert payload["command_receipts"][0]["status"] == "satisfied_external"
    assert payload["command_receipts"][0]["satisfied_by"] == "ci-master-verification"
    assert payload["latency_gate"]["foundation_gate_report_json"] is None
    assert payload["latency_gate"]["report_refs"] == {}


def test_run_foundation_gate_parallel_ci_mode_records_external_verify_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_fast_gate_report(monkeypatch)
    output_path = tmp_path / "gate_report.json"
    prerequisite_path = tmp_path / "prerequisite.json"
    prerequisite_ref = "foundation-prerequisite:" + "b" * 64
    observed: dict[str, object] = {}

    def fake_load(
        path: Path,
        repo: Path,
        sha: str,
        base_sha: str,
    ) -> SimpleNamespace:
        observed.update(
            path=path,
            repo=repo,
            sha=sha,
            base_sha=base_sha,
        )
        return SimpleNamespace(content_ref=prerequisite_ref)

    monkeypatch.setattr(
        run_foundation_gate,
        "load_foundation_prerequisite_manifest",
        fake_load,
    )

    exit_code = run_foundation_gate.main(
        [
            "--command-mode",
            "ci-parallel",
            "--ci-prerequisite-manifest",
            str(prerequisite_path),
            "--ci-prerequisite-sha",
            "a" * 40,
            "--ci-prerequisite-base-sha",
            "c" * 40,
            "--no-write-latest",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["command_mode"] == "ci-parallel"
    assert payload["command_receipts"][0]["command_ref"] == "command:ci.parallel_verification"
    assert payload["command_receipts"][0]["status"] == "satisfied_by_exact_receipts"
    assert payload["command_receipts"][0]["satisfied_by"] == prerequisite_ref
    assert observed["base_sha"] == "c" * 40
    assert "exact-SHA, exact-plan" in payload["command_receipts"][0]["safe_summary"]
    assert payload["latency_gate"]["foundation_gate_report_json"] is None
    assert payload["latency_gate"]["report_refs"] == {}


def test_parallel_ci_mode_rejects_missing_exact_receipt_evidence() -> None:
    with pytest.raises(SystemExit) as error:
        run_foundation_gate.main(["--command-mode", "ci-parallel", "--no-write-latest"])

    assert error.value.code == 2


def test_atomic_report_write_leaves_latest_json_valid_after_repeated_writes(tmp_path: Path) -> None:
    report_path = tmp_path / "latest_foundation_gate_report.json"
    payloads = [
        {"report_id": "gate_report_1", "overall_status": "passed", "summary": "first"},
        {"report_id": "gate_report_2", "overall_status": "passed", "summary": "second"},
        {"report_id": "gate_report_3", "overall_status": "passed", "summary": "third"},
    ]

    for payload in payloads:
        run_foundation_gate.write_json_atomic(report_path, json.dumps(payload, indent=2))
        latest = json.loads(report_path.read_text(encoding="utf-8"))
        assert latest["overall_status"] == "passed"

    latest = json.loads(report_path.read_text(encoding="utf-8"))
    assert latest["report_id"] == "gate_report_3"
    assert report_path.stat().st_size > 0


def test_atomic_report_write_keeps_latest_json_parseable_under_concurrent_writes(tmp_path: Path) -> None:
    report_path = tmp_path / "latest_foundation_gate_report.json"

    def write_report(index: int) -> None:
        payload = {
            "report_id": f"gate_report_{index}",
            "overall_status": "passed",
            "summary": f"{index} passed, 0 failed, 0 warnings, 0 blocked.",
        }
        run_foundation_gate.write_json_atomic(report_path, json.dumps(payload, indent=2))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write_report, range(16)))

    latest = json.loads(report_path.read_text(encoding="utf-8"))
    assert latest["overall_status"] == "passed"
    assert latest["report_id"].startswith("gate_report_")
    assert report_path.stat().st_size > 0
    assert not list(tmp_path.glob(".latest_foundation_gate_report.json.*.tmp"))


def test_write_json_atomic_rejects_empty_payload_with_clear_error(tmp_path: Path) -> None:
    report_path = tmp_path / "latest_foundation_gate_report.json"

    # An empty/whitespace payload must raise the explicit "must not be empty"
    # error rather than an opaque JSONDecodeError, and must not create a file.
    with pytest.raises(ValueError, match="must not be empty"):
        run_foundation_gate.write_json_atomic(report_path, "   ")

    assert not report_path.exists()
