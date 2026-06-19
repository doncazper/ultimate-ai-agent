import json

import pytest

import scripts.benchmark_foundation_gate as benchmark_foundation_gate
import scripts.check_foundation_gate_latency as check_foundation_gate_latency


class _FakeReport:
    overall_status = "passed"
    results = ("criterion:one", "criterion:two")


def _release_latency_result(
    path_id: str,
    *,
    status: str = "passed",
    p95_ms: float | None = 1.0,
) -> dict[str, object]:
    required = path_id in benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS
    return {
        "path_id": path_id,
        "safe_label": path_id,
        "required": required,
        "status": status,
        "samples": 1 if p95_ms is not None else 0,
        "p50_ms": p95_ms,
        "p95_ms": p95_ms,
        "budget_ms": benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS[path_id],
        "budget_passed": None
        if p95_ms is None
        else p95_ms < benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS[path_id],
        "failed_call_count": 0 if status in {"passed", "skipped", "blocked"} else 1,
        "reason_codes": []
        if status == "passed"
        else ["FRONTEND_RENDER_TIMING_RUNNER_NOT_SCOPED"],
        "authority_path_bypassed_for_speed": False,
        "authority_decision_cached_for_speed": False,
        "response_body_recorded": False,
        "request_body_recorded": False,
    }


def _release_latency_success_payload(
    *,
    path_results: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if path_results is None:
        path_results = [
            _release_latency_result(path_id)
            for path_id in sorted(
                benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS
            )
        ]
        path_results.extend(
            _release_latency_result(path_id, status="skipped", p95_ms=None)
            for path_id in sorted(
                benchmark_foundation_gate.RELEASE_LATENCY_OPTIONAL_PATH_IDS
            )
        )
    return {
        "release_latency_overall_status": "passed",
        "release_latency_path_repeat": 1,
        "release_latency_path_warmup": 0,
        "release_latency_budget_definitions_ms": dict(
            benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
        ),
        "release_latency_path_results": path_results,
    }


def _release_latency_source_report() -> dict[str, object]:
    path_results = [
        _release_latency_result(path_id)
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS)
    ]
    path_results.extend(
        _release_latency_result(path_id, status="skipped", p95_ms=None)
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_OPTIONAL_PATH_IDS)
    )
    return {
        "schema_version": "uaa_release_latency_baseline.v1",
        "task_ref": "UAA-P1-039",
        "baseline_source_ref": "UAA-P0-006",
        "report_ref": "performance-report:p1-039:latest",
        "generated_at_utc": "2026-06-19T00:00:00Z",
        "measurement_mode": "fastapi_testclient_local_dev",
        "path_repeat": 1,
        "path_warmup": 0,
        "overall_status": "passed",
        "budget_definitions_ms": dict(
            benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
        ),
        "path_results": path_results,
    }


def _hot_path_rows() -> list[dict[str, object]]:
    return [
        {
            "profile_id": "task_decomposition_classify",
            "safe_label": "POST /task-decomposition/classify route handler",
            "status": "passed",
            "samples": 2,
            "warmup_samples": 1,
            "p50_ms": 1.0,
            "p95_ms": 1.5,
            "mean_ms": 1.25,
            "failed_call_count": 0,
            "warmup_failed_call_count": 0,
            "reason_codes": [],
            "authority_boundary": "task_decomposition_bearer_gate_and_route_handler",
            "authority_path_bypassed_for_speed": False,
            "authority_decision_cached_for_speed": False,
            "request_body_recorded": False,
            "response_body_recorded": False,
            "schema_body_recorded": False,
            "raw_path_recorded": False,
            "raw_log_recorded": False,
        },
        {
            "profile_id": "openapi_build",
            "safe_label": "OpenAPI schema build",
            "status": "passed",
            "samples": 2,
            "warmup_samples": 1,
            "p50_ms": 3.0,
            "p95_ms": 3.5,
            "mean_ms": 3.25,
            "failed_call_count": 0,
            "warmup_failed_call_count": 0,
            "reason_codes": [],
            "authority_boundary": "openapi_schema_generation_no_runtime_authority",
            "authority_path_bypassed_for_speed": False,
            "authority_decision_cached_for_speed": False,
            "request_body_recorded": False,
            "response_body_recorded": False,
            "schema_body_recorded": False,
            "raw_path_recorded": False,
            "raw_log_recorded": False,
        },
    ]


def test_foundation_gate_benchmark_emits_parseable_metrics(monkeypatch):
    monkeypatch.setattr(benchmark_foundation_gate, "_evaluate_once", lambda: _FakeReport())

    metrics = benchmark_foundation_gate._benchmark(
        repeat=2,
        warmup=1,
        path_repeat=1,
        path_warmup=0,
        write_report=False,
    )

    assert metrics["schema_version"] == "foundation_gate_benchmark.v2"
    assert metrics["repeat"] == 2
    assert metrics["warmup"] == 1
    assert metrics["foundation_gate_status"] == "passed"
    assert metrics["foundation_gate_result_count"] == 2
    assert len(metrics["foundation_gate_runs_ms"]) == 2
    assert metrics["release_latency_schema_version"] == "uaa_release_latency_baseline.v1"
    assert metrics["release_latency_path_repeat"] == 1
    assert metrics["release_latency_path_warmup"] == 0
    assert metrics["release_latency_budget_definitions_ms"] == (
        benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
    )
    assert (
        metrics["performance_regression_report_json"]
        == "reports/performance/latest_performance_regression_report.json"
    )
    assert (
        metrics["performance_regression_report_md"]
        == "reports/performance/latest_performance_regression_report.md"
    )
    assert (
        metrics["hot_path_profile_report_json"]
        == "reports/performance/latest_hot_path_profile.json"
    )
    assert (
        metrics["hot_path_profile_report_md"]
        == "reports/performance/latest_hot_path_profile.md"
    )
    assert metrics["hot_path_profile_overall_status"] == "passed"


def test_performance_regression_report_is_release_evidence_ready():
    report = benchmark_foundation_gate._performance_regression_report(
        _release_latency_source_report()
    )

    assert report["schema_version"] == "uaa_performance_regression_report.v1"
    assert report["task_ref"] == "UAA-P1-040"
    assert report["overall_status"] == "passed"
    summary = report["summary"]
    environment = report["environment_safe_summary"]
    safety = report["report_safety"]
    path_regressions = report["path_regressions"]
    assert isinstance(summary, dict)
    assert isinstance(environment, dict)
    assert isinstance(safety, dict)
    assert isinstance(path_regressions, list)
    assert summary["measured_rows"] == len(
        benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS
    )
    assert environment["machine_identity_recorded"] is False
    assert environment["environment_variables_recorded"] is False
    assert environment["raw_paths_recorded"] is False
    assert safety["credential_material_included"] is False

    first_row = path_regressions[0]
    assert {
        "path_id",
        "safe_label",
        "regression_status",
        "samples",
        "p50_ms",
        "p95_ms",
        "budget_ms",
        "budget_margin_ms",
        "budget_comparison",
        "operator_action",
    }.issubset(first_row)


def test_performance_regression_markdown_includes_retention_guidance():
    report = benchmark_foundation_gate._performance_regression_report(
        _release_latency_source_report()
    )
    markdown = benchmark_foundation_gate._performance_regression_markdown(report)

    assert "# Performance Regression Report" in markdown
    assert "Environment-Safe Summary" in markdown
    assert "Budget Comparison" in markdown
    assert "Retention Guidance" in markdown
    assert "Machine identity, environment variables, raw paths" in markdown


def test_hot_path_profile_report_is_timing_summary_only():
    report = benchmark_foundation_gate._build_hot_path_profile_report(
        rows=_hot_path_rows(),
        generated_at_utc="2026-06-19T00:00:00Z",
        repeat=2,
        warmup=1,
    )

    assert report["schema_version"] == "uaa_hot_path_profile.v1"
    assert report["task_ref"] == "UAA-P1-041"
    assert report["overall_status"] == "passed"
    assert report["summary"]["profiled_path_ids"] == [  # type: ignore[index]
        "task_decomposition_classify",
        "openapi_build",
    ]
    assert report["report_safety"]["openapi_schema_included"] is False  # type: ignore[index]
    assert report["environment_safe_summary"]["raw_paths_recorded"] is False  # type: ignore[index]
    for row in report["hot_paths"]:  # type: ignore[index]
        assert row["request_body_recorded"] is False
        assert row["response_body_recorded"] is False
        assert row["schema_body_recorded"] is False
        assert row["raw_path_recorded"] is False
        assert row["raw_log_recorded"] is False


def test_hot_path_profile_markdown_documents_safe_usage():
    report = benchmark_foundation_gate._build_hot_path_profile_report(
        rows=_hot_path_rows(),
        generated_at_utc="2026-06-19T00:00:00Z",
        repeat=2,
        warmup=1,
    )
    markdown = benchmark_foundation_gate._hot_path_profile_markdown(report)

    assert "# Hot Path Profile" in markdown
    assert "OpenAPI schema build" in markdown
    assert "timing-summary only" in markdown
    assert "OpenAPI profiling restores the schema cache" in markdown


def test_foundation_gate_latency_guard_emits_parseable_metrics(monkeypatch, capsys):
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int):
        return {
            "schema_version": "foundation_gate_benchmark.v2",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_runs_ms": [10.0],
            "foundation_gate_best_ms": 10.0,
            "foundation_gate_mean_ms": 10.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
            **_release_latency_success_payload(),
            "release_latency_path_repeat": path_repeat,
            "release_latency_path_warmup": path_warmup,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fake_benchmark)

    exit_code = check_foundation_gate_latency.main(
        [
            "--repeat",
            "1",
            "--max-best-ms",
            "1000",
            "--max-mean-ms",
            "1000",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["failures"] == []
    assert payload["foundation_gate_mean_ms"] == 10.0
    summary = payload["foundation_gate_latency_summary"]
    assert summary["schema_version"] == "uaa_foundation_gate_latency_summary.v1"
    assert summary["task_ref"] == "UAA-P1-043"
    assert summary["status"] == "passed"
    assert summary["p50_p95_status"] == "passed"
    assert summary["accepted_failures"] == []
    assert summary["environment_safe_summary"]["raw_paths_recorded"] is False
    assert summary["report_safety"]["credential_material_included"] is False


def test_foundation_gate_latency_summary_reuses_precomputed_gate_timing(
    monkeypatch,
):
    def fail_benchmark(*args, **kwargs):
        pytest.fail("precomputed Foundation Gate timing must not rerun full benchmark")

    def fake_release_latency_paths(*, repeat: int, warmup: int, write_report: bool):
        assert repeat == 3
        assert warmup == 1
        assert write_report is True
        return {
            "release_latency_schema_version": "uaa_release_latency_baseline.v1",
            **_release_latency_success_payload(),
            "release_latency_path_repeat": repeat,
            "release_latency_path_warmup": warmup,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fail_benchmark)
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_benchmark_release_latency_paths",
        fake_release_latency_paths,
    )

    summary = check_foundation_gate_latency.run_latency_gate_summary(
        path_repeat=3,
        path_warmup=1,
        precomputed_foundation_gate_ms=12.34,
        precomputed_foundation_gate_status="passed",
        precomputed_foundation_gate_result_count=626,
    )

    assert summary["status"] == "passed"
    assert summary["foundation_gate_best_ms"] == 12.34
    assert summary["foundation_gate_mean_ms"] == 12.34
    assert summary["foundation_gate_status"] == "passed"
    assert summary["authority_invariants"]["foundation_gate_checks_preserved"] is True


def test_foundation_gate_latency_summary_rejects_partial_precomputed_timing():
    with pytest.raises(ValueError, match="requires elapsed ms, status, and result count"):
        check_foundation_gate_latency.run_latency_gate_summary(
            precomputed_foundation_gate_ms=12.34,
            precomputed_foundation_gate_status="passed",
        )


def test_foundation_gate_latency_guard_fails_when_budget_exceeded(monkeypatch, capsys):
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int):
        return {
            "schema_version": "foundation_gate_benchmark.v2",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_runs_ms": [1500.0],
            "foundation_gate_best_ms": 1500.0,
            "foundation_gate_mean_ms": 1500.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
            **_release_latency_success_payload(),
            "release_latency_path_repeat": path_repeat,
            "release_latency_path_warmup": path_warmup,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fake_benchmark)

    exit_code = check_foundation_gate_latency.main(
        [
            "--repeat",
            "1",
            "--max-best-ms",
            "1000",
            "--max-mean-ms",
            "1000",
            "--json",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert "best 1500.00 ms exceeds budget 1000.00 ms" in payload["failures"]
    assert "mean 1500.00 ms exceeds budget 1000.00 ms" in payload["failures"]
    assert payload["foundation_gate_latency_summary"]["status"] == "failed"


def test_release_latency_gate_fails_missing_required_path():
    path_results = [
        _release_latency_result(path_id)
        for path_id in sorted(
            benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS - {"api_manifest"}
        )
    ]
    path_results.extend(
        _release_latency_result(path_id, status="skipped", p95_ms=None)
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_OPTIONAL_PATH_IDS)
    )

    failures = check_foundation_gate_latency._release_latency_gate_failures(
        _release_latency_success_payload(path_results=path_results)
    )

    assert "api_manifest release latency result is missing" in failures


def test_release_latency_gate_fails_required_path_budget_regression():
    path_results = []
    for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS):
        if path_id == "api_manifest":
            path_results.append(
                _release_latency_result(path_id, status="failed", p95_ms=151.0)
            )
        else:
            path_results.append(_release_latency_result(path_id))
    path_results.extend(
        _release_latency_result(path_id, status="skipped", p95_ms=None)
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_OPTIONAL_PATH_IDS)
    )

    failures = check_foundation_gate_latency._release_latency_gate_failures(
        _release_latency_success_payload(path_results=path_results)
    )

    assert "api_manifest release latency status is 'failed', expected 'passed'" in failures
    assert "api_manifest p95 151.00 ms exceeds budget 150.00 ms" in failures


def test_release_latency_gate_allows_optional_skipped_prerequisite():
    failures = check_foundation_gate_latency._release_latency_gate_failures(
        _release_latency_success_payload()
    )

    assert failures == []


def test_foundation_gate_latency_summary_keeps_optional_skips_visible():
    summary = check_foundation_gate_latency.build_foundation_gate_latency_summary(
        {
            "schema_version": "foundation_gate_benchmark.v2",
            "foundation_gate_runs_ms": [10.0],
            "foundation_gate_best_ms": 10.0,
            "foundation_gate_mean_ms": 10.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
            "release_latency_report_json": (
                "reports/performance/latest_release_latency_baseline.json"
            ),
            "release_latency_report_md": (
                "reports/performance/latest_release_latency_baseline.md"
            ),
            "performance_regression_report_json": (
                "reports/performance/latest_performance_regression_report.json"
            ),
            "performance_regression_report_md": (
                "reports/performance/latest_performance_regression_report.md"
            ),
            "hot_path_profile_report_json": (
                "reports/performance/latest_hot_path_profile.json"
            ),
            "hot_path_profile_report_md": (
                "reports/performance/latest_hot_path_profile.md"
            ),
            "hot_path_profile_overall_status": "passed",
            **_release_latency_success_payload(),
        },
        foundation_gate_report_json=(
            "reports/foundation_gate/latest_foundation_gate_report.json"
        ),
        foundation_gate_report_md=(
            "reports/foundation_gate/latest_foundation_gate_report.md"
        ),
    )

    assert summary["status"] == "passed"
    assert summary["foundation_gate_report_json"] == (
        "reports/foundation_gate/latest_foundation_gate_report.json"
    )
    assert summary["report_refs"]["release_latency_report_json"] == (
        "reports/performance/latest_release_latency_baseline.json"
    )
    assert summary["optional_prerequisites"]
    assert summary["optional_prerequisites"][0]["status"] == "skipped"
    assert summary["optional_prerequisites"][0]["reason_codes"] == [
        "FRONTEND_RENDER_TIMING_RUNNER_NOT_SCOPED"
    ]
    assert summary["authority_invariants"]["foundation_gate_checks_preserved"] is True
    assert summary["report_safety"]["path_material_included"] is False


def test_foundation_gate_latency_guard_fails_failed_release_overall(
    monkeypatch,
    capsys,
):
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int):
        return {
            "schema_version": "foundation_gate_benchmark.v2",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_runs_ms": [10.0],
            "foundation_gate_best_ms": 10.0,
            "foundation_gate_mean_ms": 10.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
            **_release_latency_success_payload(),
            "release_latency_overall_status": "failed",
            "release_latency_path_repeat": path_repeat,
            "release_latency_path_warmup": path_warmup,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fake_benchmark)

    exit_code = check_foundation_gate_latency.main(
        [
            "--repeat",
            "1",
            "--max-best-ms",
            "1000",
            "--max-mean-ms",
            "1000",
            "--json",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert (
        "release latency overall status is 'failed', expected 'passed'"
        in payload["failures"]
    )


def test_foundation_gate_latency_guard_rejects_invalid_env_budget(monkeypatch):
    monkeypatch.setenv("FOUNDATION_GATE_MAX_MEAN_MS", "not-a-number")

    with pytest.raises(SystemExit) as exc:
        check_foundation_gate_latency.main(["--json"])

    assert exc.value.code == 2
