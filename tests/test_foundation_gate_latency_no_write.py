from typing import Any

import pytest

import scripts.benchmark_foundation_gate as benchmark_foundation_gate
import scripts.check_foundation_gate_latency as check_foundation_gate_latency


def _path_result(path_id: str) -> dict[str, object]:
    return {
        "path_id": path_id,
        "safe_label": path_id,
        "required": True,
        "status": "passed",
        "samples": 1,
        "p50_ms": 1.0,
        "p95_ms": 1.0,
        "budget_ms": benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS[path_id],
        "reason_codes": [],
        "authority_path_bypassed_for_speed": False,
        "authority_decision_cached_for_speed": False,
        "request_body_recorded": False,
        "response_body_recorded": False,
    }


def _success_payload() -> dict[str, object]:
    path_results = [
        _path_result(path_id)
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_REQUIRED_PATH_IDS)
    ]
    path_results.extend(
        {
            "path_id": path_id,
            "safe_label": path_id,
            "required": False,
            "status": "skipped",
            "samples": 0,
            "p50_ms": None,
            "p95_ms": None,
            "budget_ms": benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS[path_id],
            "reason_codes": ["FRONTEND_RENDER_TIMING_RUNNER_NOT_SCOPED"],
            "authority_path_bypassed_for_speed": False,
            "authority_decision_cached_for_speed": False,
            "request_body_recorded": False,
            "response_body_recorded": False,
        }
        for path_id in sorted(benchmark_foundation_gate.RELEASE_LATENCY_OPTIONAL_PATH_IDS)
    )
    return {
        "release_latency_schema_version": "uaa_release_latency_baseline.v1",
        "hot_path_profile_overall_status": "passed",
        "release_latency_overall_status": "passed",
        "release_latency_path_repeat": 3,
        "release_latency_path_warmup": 1,
        "release_latency_measurement_prerequisites": {
            "status": "passed",
            "api_manifest_static_cache_primed": True,
            "static_metadata_cache_only": True,
            "request_body_recorded": False,
            "response_body_recorded": False,
            "raw_path_recorded": False,
            "raw_log_recorded": False,
            "authority_decisions_cached_for_speed": False,
            "policy_decisions_cached_for_speed": False,
            "approval_decisions_cached_for_speed": False,
            "approval_state_cached_for_speed": False,
            "foundation_gate_status_cached_for_speed": False,
            "mutable_user_data_cached_for_speed": False,
            "secret_material_cached_for_speed": False,
        },
        "release_latency_budget_definitions_ms": dict(
            benchmark_foundation_gate.RELEASE_LATENCY_BUDGETS_MS
        ),
        "release_latency_path_results": path_results,
    }


def test_latency_summary_no_write_omits_latest_report_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_report_values: list[bool] = []

    def fail_benchmark(*args: Any, **kwargs: Any) -> None:
        pytest.fail("precomputed Foundation Gate timing must not rerun full benchmark")

    def fake_release_latency_paths(
        *,
        repeat: int,
        warmup: int,
        write_report: bool,
    ) -> dict[str, object]:
        write_report_values.append(write_report)
        return {
            **_success_payload(),
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
        write_report=False,
        precomputed_foundation_gate_ms=12.34,
        precomputed_foundation_gate_status="passed",
        precomputed_foundation_gate_result_count=626,
    )

    assert write_report_values == [False]
    assert summary["status"] == "passed"
    assert summary["report_refs"] == {}
