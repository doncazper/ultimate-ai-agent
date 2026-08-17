import json
from pathlib import Path
from typing import Any

import pytest

import scripts.benchmark_foundation_gate as benchmark_foundation_gate
import scripts.check_foundation_gate_latency as check_foundation_gate_latency


class _FakeReport:
    overall_status = "passed"
    results = ("criterion:one", "criterion:two")


def test_health_release_path_uses_a_meaningful_p95_sample_floor() -> None:
    assert benchmark_foundation_gate.HEALTH_RELEASE_PATH_MIN_REPEAT == 20
    assert benchmark_foundation_gate._percentile_ms([1.0] * 19 + [85.0], 95) == 1.0
    assert benchmark_foundation_gate._percentile_ms([1.0] * 18 + [85.0] * 2, 95) == 85.0


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


def _release_latency_measurement_prerequisites() -> dict[str, object]:
    return {
        "status": "passed",
        "api_manifest_static_cache_primed": True,
        "primed_route_ref": "GET /api/manifest",
        "static_metadata_cache_only": True,
        "authority_decisions_cached_for_speed": False,
        "policy_decisions_cached_for_speed": False,
        "approval_decisions_cached_for_speed": False,
        "approval_state_cached_for_speed": False,
        "foundation_gate_status_cached_for_speed": False,
        "mutable_user_data_cached_for_speed": False,
        "secret_material_cached_for_speed": False,
        "request_body_recorded": False,
        "response_body_recorded": False,
        "raw_path_recorded": False,
        "raw_log_recorded": False,
        "reason_codes": [],
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
        "release_latency_measurement_prerequisites": (
            _release_latency_measurement_prerequisites()
        ),
        "release_latency_budget_definitions_ms": dict(
            benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
        ),
        "release_latency_path_results": path_results,
    }


def _performance_handoff_metrics(
    *,
    best_ms: float = 44_000.0,
    mean_ms: float = 44_000.0,
    path_results: list[dict[str, object]] | None = None,
    release_status: str = "passed",
) -> dict[str, object]:
    release_metrics = _release_latency_success_payload(path_results=path_results)
    return {
        "schema_version": "foundation_gate_benchmark.v2",
        "repeat": 1,
        "warmup": 1,
        "foundation_gate_warmup_statuses": ["passed"],
        "foundation_gate_warmup_result_counts": [2],
        "foundation_gate_runs_ms": [best_ms],
        "foundation_gate_best_ms": best_ms,
        "foundation_gate_mean_ms": mean_ms,
        "foundation_gate_status": "passed",
        "foundation_gate_result_count": 2,
        "release_latency_schema_version": "uaa_release_latency_baseline.v1",
        "hot_path_profile_overall_status": "passed",
        **release_metrics,
        "release_latency_overall_status": release_status,
        "release_latency_budget_passed": release_status == "passed",
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
        "measurement_prerequisites": _release_latency_measurement_prerequisites(),
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


def test_foundation_gate_benchmark_emits_parseable_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_foundation_gate, "_evaluate_once", lambda: _FakeReport())

    def deterministic_path_measurement(
        path_id: str,
        _label: str,
        _budget_ms: float,
        repeat: int,
        _warmup: int,
        _call: Any,
    ) -> dict[str, object]:
        result = _release_latency_result(path_id)
        result["samples"] = repeat
        return result

    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_prime_release_latency_prerequisites",
        _release_latency_measurement_prerequisites,
    )
    monkeypatch.setattr(
        benchmark_foundation_gate, "_measure_path", deterministic_path_measurement
    )
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_measure_hot_paths",
        lambda *, repeat, warmup: _hot_path_rows(),
    )

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
    prerequisites = metrics["release_latency_measurement_prerequisites"]
    assert prerequisites["status"] == "passed"
    assert prerequisites["api_manifest_static_cache_primed"] is True
    assert prerequisites["static_metadata_cache_only"] is True
    assert prerequisites["authority_decisions_cached_for_speed"] is False
    assert prerequisites["policy_decisions_cached_for_speed"] is False
    assert prerequisites["approval_decisions_cached_for_speed"] is False
    assert prerequisites["approval_state_cached_for_speed"] is False
    assert prerequisites["foundation_gate_status_cached_for_speed"] is False
    assert prerequisites["mutable_user_data_cached_for_speed"] is False
    assert prerequisites["secret_material_cached_for_speed"] is False
    assert metrics["release_latency_budget_definitions_ms"] == (
        benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
    )
    assert metrics["release_latency_overall_status"] == "passed"
    path_results = {
        result["path_id"]: result for result in metrics["release_latency_path_results"]
    }
    assert path_results["health"]["samples"] == 20
    assert path_results["api_manifest"]["samples"] == 1
    for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS):
        assert path_results[path_id]["status"] == "passed"
        assert path_results[path_id]["failed_call_count"] == 0
        assert path_results[path_id]["authority_path_bypassed_for_speed"] is False
    assert "release_latency_report_json" not in metrics
    assert "performance_regression_report_json" not in metrics
    assert "hot_path_profile_report_json" not in metrics
    assert metrics["hot_path_profile_overall_status"] == "passed"


def test_performance_regression_report_is_release_evidence_ready() -> None:
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


def test_performance_regression_markdown_includes_retention_guidance() -> None:
    report = benchmark_foundation_gate._performance_regression_report(
        _release_latency_source_report()
    )
    markdown = benchmark_foundation_gate._performance_regression_markdown(report)

    assert "# Performance Regression Report" in markdown
    assert "Environment-Safe Summary" in markdown
    assert "Budget Comparison" in markdown
    assert "Retention Guidance" in markdown
    assert "Machine identity, environment variables, raw paths" in markdown


def test_release_latency_markdown_includes_measurement_prerequisites() -> None:
    markdown = benchmark_foundation_gate._performance_markdown(
        _release_latency_source_report()
    )

    assert "Measurement Prerequisites" in markdown
    assert "Static metadata cache only: `True`" in markdown
    assert "Authority decisions cached for speed: `False`" in markdown
    assert "Secret material cached for speed: `False`" in markdown


def test_release_latency_report_fails_failed_measurement_prerequisite(monkeypatch: pytest.MonkeyPatch) -> None:
    failed_prerequisites = _release_latency_measurement_prerequisites()
    failed_prerequisites["status"] = "failed"
    failed_prerequisites["api_manifest_static_cache_primed"] = False
    failed_prerequisites["reason_codes"] = ["API_MANIFEST_STATIC_CACHE_PRIMER_FAILED"]

    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_prime_release_latency_prerequisites",
        lambda: failed_prerequisites,
    )
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_measure_release_paths",
        lambda *, repeat, warmup: [
            _release_latency_result(path_id)
            for path_id in sorted(
                benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS
            )
        ],
    )
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_measure_hot_paths",
        lambda *, repeat, warmup: _hot_path_rows(),
    )

    metrics = benchmark_foundation_gate._benchmark_release_latency_paths(
        repeat=1,
        warmup=0,
        write_report=False,
    )

    assert metrics["release_latency_overall_status"] == "failed"
    assert metrics["release_latency_measurement_prerequisites"] == failed_prerequisites


def test_hot_path_profile_report_is_timing_summary_only() -> None:
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


def test_hot_path_profile_markdown_documents_safe_usage() -> None:
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


def test_foundation_gate_latency_guard_emits_parseable_metrics(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int) -> dict[str, Any]:
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_benchmark(*args: Any, **kwargs: Any) -> None:
        pytest.fail("precomputed Foundation Gate timing must not rerun full benchmark")

    def fake_release_latency_paths(*, repeat: int, warmup: int, write_report: bool) -> dict[str, Any]:
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


def test_foundation_gate_latency_summary_rejects_partial_precomputed_timing() -> None:
    with pytest.raises(ValueError, match="requires elapsed ms, status, and result count"):
        check_foundation_gate_latency.run_latency_gate_summary(
            precomputed_foundation_gate_ms=12.34,
            precomputed_foundation_gate_status="passed",
        )


def test_latency_gate_reuses_exact_warmed_benchmark_measurement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handoff_path = tmp_path / benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_NAME
    monkeypatch.setenv(
        benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_ENV,
        str(handoff_path),
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.VERIFICATION_REPOSITORY_SHA_ENV,
        "a" * 40,
    )
    benchmark_foundation_gate._write_performance_metrics_handoff(
        _performance_handoff_metrics()
    )
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_benchmark",
        lambda **_kwargs: pytest.fail(
            "latency gate must not take a second contention-sensitive sample"
        ),
    )

    exit_code = check_foundation_gate_latency.main(
        ["--max-best-ms", "45000", "--max-mean-ms", "45000", "--json"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["passed"] is True
    assert not handoff_path.exists()


def test_performance_handoff_rejects_missing_parent_with_bounded_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff_path = (
        tmp_path
        / "missing"
        / benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_NAME
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_ENV,
        str(handoff_path),
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.VERIFICATION_REPOSITORY_SHA_ENV,
        "a" * 40,
    )

    with pytest.raises(RuntimeError, match="handoff parent is unsafe"):
        benchmark_foundation_gate._write_performance_metrics_handoff(
            _performance_handoff_metrics()
        )


def test_failed_latency_gate_writes_bounded_content_free_route_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handoff_path = tmp_path / benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_NAME
    receipt_path = (
        tmp_path
        / check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_NAME
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_ENV,
        str(handoff_path),
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.VERIFICATION_REPOSITORY_SHA_ENV,
        "a" * 40,
    )
    monkeypatch.setenv(
        check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_ENV,
        str(receipt_path),
    )
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
    failing = next(
        result for result in path_results if result["path_id"] == "api_manifest"
    )
    failing.update(
        {
            "status": "failed",
            "p50_ms": 200.0,
            "p95_ms": 200.0,
            "budget_passed": False,
            "failed_call_count": 0,
            "reason_codes": ["P95_BUDGET_EXCEEDED"],
        }
    )
    benchmark_foundation_gate._write_performance_metrics_handoff(
        _performance_handoff_metrics(
            path_results=path_results,
            release_status="failed",
        )
    )

    exit_code = check_foundation_gate_latency.main(
        ["--max-best-ms", "45000", "--max-mean-ms", "45000", "--json"]
    )

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["passed"] is False
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["failure_refs"] == [
        "failure-ref:performance-latency:release-latency:status-not-passed",
        "failure-ref:performance-latency:route:api_manifest:p95:"
        "budget-150ms:observed-gte-1.25x-lt-1.5x",
        "failure-ref:performance-latency:route:api_manifest:status-not-passed",
    ]
    serialized = json.dumps(receipt, sort_keys=True)
    assert "200.0" not in serialized
    assert str(tmp_path) not in serialized
    assert receipt["redaction_status"] == (
        "content_free_refs_and_duration_buckets_only"
    )
    assert not handoff_path.exists()


def test_latency_gate_rejects_malformed_handoff_with_safe_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handoff_path = tmp_path / benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_NAME
    receipt_path = (
        tmp_path
        / check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_NAME
    )
    handoff_path.write_text("{}", encoding="utf-8")
    handoff_path.chmod(0o600)
    monkeypatch.setenv(
        check_foundation_gate_latency.PERFORMANCE_METRICS_HANDOFF_ENV,
        str(handoff_path),
    )
    monkeypatch.setenv(
        check_foundation_gate_latency.VERIFICATION_REPOSITORY_SHA_ENV,
        "a" * 40,
    )
    monkeypatch.setenv(
        check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_ENV,
        str(receipt_path),
    )

    assert check_foundation_gate_latency.main(["--json"]) == 1

    assert json.loads(capsys.readouterr().out)["safe_failure_refs"] == [
        "failure-ref:performance-latency:measurement-handoff:invalid"
    ]
    assert json.loads(receipt_path.read_text(encoding="utf-8"))[
        "failure_refs"
    ] == ["failure-ref:performance-latency:measurement-handoff:invalid"]


@pytest.mark.parametrize(
    "mutations",
    (
        {"schema_version": "foundation_gate_benchmark.v1"},
        {"release_latency_schema_version": "uaa_release_latency_baseline.v0"},
        {
            "foundation_gate_best_ms": 1.0,
            "foundation_gate_mean_ms": 1.0,
        },
    ),
)
def test_latency_gate_rejects_inconsistent_typed_handoff_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mutations: dict[str, object],
) -> None:
    handoff_path = tmp_path / benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_NAME
    receipt_path = (
        tmp_path
        / check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_NAME
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.PERFORMANCE_METRICS_HANDOFF_ENV,
        str(handoff_path),
    )
    monkeypatch.setenv(
        benchmark_foundation_gate.VERIFICATION_REPOSITORY_SHA_ENV,
        "a" * 40,
    )
    monkeypatch.setenv(
        check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_ENV,
        str(receipt_path),
    )
    benchmark_foundation_gate._write_performance_metrics_handoff(
        _performance_handoff_metrics(best_ms=60_000.0, mean_ms=60_000.0)
    )
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    payload["metrics"].update(mutations)
    payload["measurement_digest"] = benchmark_foundation_gate.hashlib.sha256(
        benchmark_foundation_gate._canonical_json_bytes(payload["metrics"])
    ).hexdigest()
    handoff_path.write_bytes(
        benchmark_foundation_gate._canonical_json_bytes(payload)
    )
    handoff_path.chmod(0o600)

    assert check_foundation_gate_latency.main(
        ["--max-best-ms", "45000", "--max-mean-ms", "45000", "--json"]
    ) == 1

    assert json.loads(capsys.readouterr().out)["safe_failure_refs"] == [
        "failure-ref:performance-latency:measurement-handoff:invalid"
    ]
    assert json.loads(receipt_path.read_text(encoding="utf-8"))[
        "failure_refs"
    ] == ["failure-ref:performance-latency:measurement-handoff:invalid"]


def test_safe_failure_refs_are_capped_without_raw_measurements() -> None:
    metrics = _performance_handoff_metrics(
        best_ms=100_000.0,
        mean_ms=100_000.0,
        path_results=[
            {
                **_release_latency_result(path_id, status="failed"),
                "p95_ms": 100_000.0,
                "budget_passed": False,
                "failed_call_count": 1,
                "authority_path_bypassed_for_speed": True,
                "authority_decision_cached_for_speed": True,
            }
            for path_id in sorted(
                benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
            )
        ],
        release_status="failed",
    )
    failures = check_foundation_gate_latency._foundation_gate_latency_failures(
        metrics,
        max_best_ms=45_000,
        max_mean_ms=45_000,
    )

    refs = check_foundation_gate_latency._safe_failure_refs(
        metrics,
        max_best_ms=45_000,
        max_mean_ms=45_000,
        failures=failures,
    )

    assert len(refs) == check_foundation_gate_latency.MAX_PERFORMANCE_SAFE_FAILURE_REFS
    assert "failure-ref:performance-latency:evidence:ref-cap-exceeded" in refs
    assert refs == tuple(sorted(refs))
    assert "100000" not in json.dumps(refs)


def test_integer_budget_refs_are_python_310_compatible() -> None:
    assert check_foundation_gate_latency._budget_ref(45_000) == "45000ms"
    assert check_foundation_gate_latency._budget_ref(45_000.5) == "45000.5ms"


def test_safe_failure_refs_force_failed_payload_and_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _performance_handoff_metrics()
    receipt_path = (
        tmp_path
        / check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_NAME
    )
    safe_ref = "failure-ref:performance-latency:validation:failed"
    monkeypatch.setattr(
        benchmark_foundation_gate,
        "_benchmark",
        lambda **_kwargs: metrics,
    )
    monkeypatch.setattr(
        check_foundation_gate_latency,
        "_safe_failure_refs",
        lambda *_args, **_kwargs: (safe_ref,),
    )
    monkeypatch.setenv(
        check_foundation_gate_latency.PERFORMANCE_SAFE_FAILURE_RECEIPT_ENV,
        str(receipt_path),
    )

    assert check_foundation_gate_latency.main(
        ["--max-best-ms", "45000", "--max-mean-ms", "45000", "--json"]
    ) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert payload["safe_failure_refs"] == [safe_ref]
    assert payload["failures"] == [
        "safe performance failure evidence is present"
    ]
    assert payload["foundation_gate_latency_summary"]["status"] == "failed"
    assert payload["foundation_gate_latency_summary"]["failures"] == [
        "safe performance failure evidence is present"
    ]
    assert json.loads(receipt_path.read_text(encoding="utf-8"))[
        "failure_refs"
    ] == [safe_ref]


def test_foundation_gate_latency_guard_fails_when_budget_exceeded(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int) -> dict[str, Any]:
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


def test_release_latency_gate_fails_missing_required_path() -> None:
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


def test_release_latency_gate_fails_required_path_budget_regression() -> None:
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


def test_release_latency_gate_allows_optional_skipped_prerequisite() -> None:
    failures = check_foundation_gate_latency._release_latency_gate_failures(
        _release_latency_success_payload()
    )

    assert failures == []


def test_release_latency_gate_requires_measurement_prerequisites() -> None:
    payload = _release_latency_success_payload()
    payload.pop("release_latency_measurement_prerequisites")

    failures = (
        check_foundation_gate_latency._release_latency_measurement_prerequisite_failures(
            payload
        )
    )

    assert failures == [
        "release latency measurement prerequisites are missing or malformed"
    ]


def test_release_latency_gate_rejects_unsafe_primer_caching() -> None:
    payload = _release_latency_success_payload()
    prerequisites = dict(payload["release_latency_measurement_prerequisites"])
    prerequisites["authority_decisions_cached_for_speed"] = True
    prerequisites["mutable_user_data_cached_for_speed"] = True
    payload["release_latency_measurement_prerequisites"] = prerequisites

    failures = (
        check_foundation_gate_latency._release_latency_measurement_prerequisite_failures(
            payload
        )
    )

    assert (
        "release latency primer reports authority decisions cached for speed"
        in failures
    )
    assert (
        "release latency primer reports mutable user data cached for speed"
        in failures
    )


def test_release_latency_gate_rejects_missing_explicit_false_primer_flag() -> None:
    payload = _release_latency_success_payload()
    prerequisites = dict(payload["release_latency_measurement_prerequisites"])
    prerequisites.pop("secret_material_cached_for_speed")
    payload["release_latency_measurement_prerequisites"] = prerequisites

    failures = (
        check_foundation_gate_latency._release_latency_measurement_prerequisite_failures(
            payload
        )
    )

    assert (
        "release latency primer secret material cached for speed flag is not explicitly false"
        in failures
    )


def test_foundation_gate_latency_summary_keeps_optional_skips_visible() -> None:
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
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_benchmark(*, repeat: int, warmup: int, path_repeat: int, path_warmup: int) -> dict[str, Any]:
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


def test_foundation_gate_latency_guard_fails_failed_untimed_warmup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_benchmark(
        *,
        repeat: int,
        warmup: int,
        path_repeat: int,
        path_warmup: int,
    ) -> dict[str, Any]:
        return {
            "schema_version": "foundation_gate_benchmark.v2",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_warmup_statuses": ["failed"],
            "foundation_gate_warmup_result_counts": [2],
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
            "--warmup",
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
        "Foundation Gate warmup 1 status is 'failed', expected 'passed'"
        in payload["failures"]
    )


def test_foundation_gate_latency_guard_accepts_valid_untimed_warmup() -> None:
    metrics = {
        "warmup": 1,
        "foundation_gate_warmup_statuses": ["passed"],
        "foundation_gate_warmup_result_counts": [2],
        "foundation_gate_best_ms": 10.0,
        "foundation_gate_mean_ms": 10.0,
        "foundation_gate_status": "passed",
        "foundation_gate_result_count": 2,
        **_release_latency_success_payload(),
    }

    assert (
        check_foundation_gate_latency._foundation_gate_latency_failures(
            metrics,
            max_best_ms=1_000,
            max_mean_ms=1_000,
        )
        == []
    )


@pytest.mark.parametrize(
    ("change", "expected_failure"),
    (
        (
            {"foundation_gate_warmup_statuses": []},
            "Foundation Gate warmup statuses are missing or malformed",
        ),
        (
            {"foundation_gate_warmup_statuses": None},
            "Foundation Gate warmup statuses are missing or malformed",
        ),
        (
            {"foundation_gate_warmup_result_counts": []},
            "Foundation Gate warmup result counts are missing or malformed",
        ),
        (
            {"foundation_gate_warmup_result_counts": [0]},
            "Foundation Gate warmup result counts are missing or malformed",
        ),
        (
            {"foundation_gate_warmup_result_counts": [True]},
            "Foundation Gate warmup result counts are missing or malformed",
        ),
    ),
)
def test_foundation_gate_latency_guard_rejects_malformed_untimed_warmup(
    change: dict[str, object],
    expected_failure: str,
) -> None:
    metrics = {
        "warmup": 1,
        "foundation_gate_warmup_statuses": ["passed"],
        "foundation_gate_warmup_result_counts": [2],
        "foundation_gate_best_ms": 10.0,
        "foundation_gate_mean_ms": 10.0,
        "foundation_gate_status": "passed",
        "foundation_gate_result_count": 2,
        **_release_latency_success_payload(),
        **change,
    }

    failures = check_foundation_gate_latency._foundation_gate_latency_failures(
        metrics,
        max_best_ms=1_000,
        max_mean_ms=1_000,
    )

    assert expected_failure in failures


def test_foundation_gate_latency_guard_rejects_invalid_env_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDATION_GATE_MAX_MEAN_MS", "not-a-number")

    with pytest.raises(SystemExit) as exc:
        check_foundation_gate_latency.main(["--json"])

    assert exc.value.code == 2
