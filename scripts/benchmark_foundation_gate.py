#!/usr/bin/env python3
"""Benchmark Foundation Gate and release-critical local latency paths."""
from __future__ import annotations


import argparse
import json
import math
import os
import statistics
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PERFORMANCE_REPORT_DIR = ROOT / "reports" / "performance"
PERFORMANCE_REPORT_JSON = PERFORMANCE_REPORT_DIR / "latest_release_latency_baseline.json"
PERFORMANCE_REPORT_MD = PERFORMANCE_REPORT_DIR / "latest_release_latency_baseline.md"
PERFORMANCE_REGRESSION_JSON = (
    PERFORMANCE_REPORT_DIR / "latest_performance_regression_report.json"
)
PERFORMANCE_REGRESSION_MD = PERFORMANCE_REPORT_DIR / "latest_performance_regression_report.md"
HOT_PATH_PROFILE_JSON = PERFORMANCE_REPORT_DIR / "latest_hot_path_profile.json"
HOT_PATH_PROFILE_MD = PERFORMANCE_REPORT_DIR / "latest_hot_path_profile.md"

RELEASE_LATENCY_BASELINE_TASK_REF = "UAA-P0-006"
RELEASE_LATENCY_GATE_TASK_REF = "UAA-P1-039"
PERFORMANCE_REGRESSION_TASK_REF = "UAA-P1-040"
HOT_PATH_PROFILE_TASK_REF = "UAA-P1-041"
RELEASE_LATENCY_REPORT_REF = "performance-report:p1-039:latest"
PERFORMANCE_REGRESSION_REPORT_REF = "performance-regression-report:p1-040:latest"
HOT_PATH_PROFILE_REPORT_REF = "hot-path-profile:p1-041:latest"
RELEASE_LATENCY_LOCAL_API_BEARER = "local-performance-api-bearer"
RELEASE_LATENCY_TASK_BEARER = "local-performance-bearer"
RELEASE_LATENCY_LOCAL_GATEWAY_KEY = "uaa-local-test"
RELEASE_LATENCY_CHAT_IDEMPOTENCY_KEY = "idempotency:release-latency:v1-chat"
RELEASE_LATENCY_BUDGETS_MS: dict[str, float] = {
    "health": 50.0,
    "api_manifest": 150.0,
    "model_route_preview": 150.0,
    "task_decomposition_classify": 100.0,
    "task_decomposition_decompose": 250.0,
    "file_read_preview_bounded_text": 150.0,
    "v1_models_local_gateway": 100.0,
    "v1_chat_completions_local_path": 250.0,
    "control_center_first_useful_local_render": 1500.0,
}
RELEASE_LATENCY_REQUIRED_PATH_IDS = frozenset(
    path_id
    for path_id in RELEASE_LATENCY_BUDGETS_MS
    if path_id != "control_center_first_useful_local_render"
)
RELEASE_LATENCY_OPTIONAL_PATH_IDS = frozenset(
    path_id
    for path_id in RELEASE_LATENCY_BUDGETS_MS
    if path_id not in RELEASE_LATENCY_REQUIRED_PATH_IDS
)


def _ensure_repo_on_path() -> None:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _status_value(status: Any) -> str:
    value = getattr(status, "value", status)
    return str(value)


def _evaluate_once() -> Any:
    _ensure_repo_on_path()
    from ultimate_ai_agent.core.gate import FoundationGateEvaluator

    return FoundationGateEvaluator(ROOT).evaluate()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark FoundationGateEvaluator.evaluate() and release latency paths.",
    )
    parser.add_argument(
        "--repeat",
        type=_positive_int,
        default=1,
        help="Number of timed Foundation Gate report evaluations. Default: 1.",
    )
    parser.add_argument(
        "--warmup",
        type=_non_negative_int,
        default=0,
        help="Number of untimed Foundation Gate warmup evaluations. Default: 0.",
    )
    parser.add_argument(
        "--path-repeat",
        type=_positive_int,
        default=5,
        help="Number of timed runs per release-critical local path. Default: 5.",
    )
    parser.add_argument(
        "--path-warmup",
        type=_non_negative_int,
        default=1,
        help="Number of untimed warmup runs per release-critical local path. Default: 1.",
    )
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="Do not write reports/performance output.",
    )
    parser.add_argument("--json", action="store_true", help="Print metrics as JSON.")
    return parser.parse_args(argv)


def _benchmark(
    *,
    repeat: int,
    warmup: int,
    path_repeat: int = 5,
    path_warmup: int = 1,
    write_report: bool = True,
) -> dict[str, object]:
    for _ in range(warmup):
        _evaluate_once()

    runs_ms: list[float] = []
    latest_report = None
    for _ in range(repeat):
        started = perf_counter()
        latest_report = _evaluate_once()
        runs_ms.append((perf_counter() - started) * 1000)

    best_ms = min(runs_ms)
    mean_ms = statistics.mean(runs_ms)
    report_status = _status_value(getattr(latest_report, "overall_status", "unknown"))
    results = getattr(latest_report, "results", ())
    result_count = len(results) if results is not None else 0

    release_latency = _benchmark_release_latency_paths(
        repeat=path_repeat,
        warmup=path_warmup,
        write_report=write_report,
    )
    return {
        "schema_version": "foundation_gate_benchmark.v2",
        "repeat": repeat,
        "warmup": warmup,
        "foundation_gate_runs_ms": [round(value, 2) for value in runs_ms],
        "foundation_gate_best_ms": round(best_ms, 2),
        "foundation_gate_mean_ms": round(mean_ms, 2),
        "foundation_gate_status": report_status,
        "foundation_gate_result_count": result_count,
        **release_latency,
    }


def _benchmark_release_latency_paths(
    *,
    repeat: int,
    warmup: int,
    write_report: bool,
) -> dict[str, object]:
    _ensure_repo_on_path()
    with tempfile.TemporaryDirectory(prefix="uaa_perf_") as temp_dir:
        temp_root = Path(temp_dir)
        safe_root = temp_root / "workspace"
        safe_root.mkdir(parents=True, exist_ok=True)
        (safe_root / "preview.txt").write_text(
            "bounded local performance fixture",
            encoding="utf-8",
        )
        with _release_latency_environment(safe_root, temp_root):
            measurement_prerequisites = _prime_release_latency_prerequisites()
            results = _measure_release_paths(repeat=repeat, warmup=warmup)
            hot_path_profile_rows = _measure_hot_paths(repeat=repeat, warmup=warmup)

    required_failures = [
        result
        for result in results
        if result["required"] and result["status"] != "passed"
    ]
    prerequisite_failed = measurement_prerequisites["status"] != "passed"
    generated_at_utc = _utc_now_label()
    hot_path_profile = _build_hot_path_profile_report(
        rows=hot_path_profile_rows,
        generated_at_utc=generated_at_utc,
        repeat=repeat,
        warmup=warmup,
    )
    report = {
        "schema_version": "uaa_release_latency_baseline.v1",
        "task_ref": RELEASE_LATENCY_GATE_TASK_REF,
        "baseline_source_ref": RELEASE_LATENCY_BASELINE_TASK_REF,
        "report_ref": RELEASE_LATENCY_REPORT_REF,
        "generated_at_utc": generated_at_utc,
        "measurement_mode": "fastapi_testclient_local_dev",
        "path_repeat": repeat,
        "path_warmup": warmup,
        "overall_status": "failed"
        if required_failures or prerequisite_failed
        else "passed",
        "measurement_prerequisites": measurement_prerequisites,
        "budget_definitions_ms": {
            key: round(value, 2) for key, value in RELEASE_LATENCY_BUDGETS_MS.items()
        },
        "path_results": results,
        "budget_gate": {
            "task_ref": RELEASE_LATENCY_GATE_TASK_REF,
            "required_path_ids": sorted(RELEASE_LATENCY_REQUIRED_PATH_IDS),
            "optional_path_ids": sorted(RELEASE_LATENCY_OPTIONAL_PATH_IDS),
            "required_path_policy": "fail_when_missing_failed_or_over_budget",
            "optional_prerequisite_policy": "allow_passed_skipped_or_blocked_only",
            "dashboard_render_status": "skipped_until_frontend_timing_runner_scoped",
        },
        "authority_invariants": {
            "authority_decision_mode": "live_route_handlers_not_cached_skipped_or_bypassed",
            "policy_engine_bypassed_for_speed": False,
            "local_approval_authority_bypassed_for_speed": False,
            "authority_decisions_cached_for_speed": False,
            "route_side_effect_classification_preserved": True,
            "openapi_checks_preserved": True,
            "foundation_gate_checks_preserved": True,
        },
        "report_safety": {
            "prompt_content_included": False,
            "response_content_included": False,
            "provider_payload_content_included": False,
            "path_material_included": False,
            "log_material_included": False,
            "machine_identity_included": False,
            "environment_dump_included": False,
            "credential_material_included": False,
        },
        "report_write": {
            "idempotent_latest_files": True,
            "atomic_replace": True,
            "rollback": "delete reports/performance/latest_release_latency_baseline.json and .md",
        },
    }
    if write_report:
        _write_performance_reports(report, hot_path_profile)
    return {
        "release_latency_schema_version": report["schema_version"],
        "release_latency_report_json": _repo_relative(PERFORMANCE_REPORT_JSON),
        "release_latency_report_md": _repo_relative(PERFORMANCE_REPORT_MD),
        "performance_regression_report_json": _repo_relative(
            PERFORMANCE_REGRESSION_JSON
        ),
        "performance_regression_report_md": _repo_relative(PERFORMANCE_REGRESSION_MD),
        "hot_path_profile_report_json": _repo_relative(HOT_PATH_PROFILE_JSON),
        "hot_path_profile_report_md": _repo_relative(HOT_PATH_PROFILE_MD),
        "hot_path_profile_overall_status": hot_path_profile["overall_status"],
        "hot_path_profile_results": hot_path_profile_rows,
        "release_latency_overall_status": report["overall_status"],
        "release_latency_path_repeat": repeat,
        "release_latency_path_warmup": warmup,
        "release_latency_measurement_prerequisites": report[
            "measurement_prerequisites"
        ],
        "release_latency_budget_definitions_ms": report["budget_definitions_ms"],
        "release_latency_budget_passed": not required_failures,
        "release_latency_path_results": results,
    }


@contextmanager
def _release_latency_environment(safe_root: Path, temp_root: Path) -> Iterator[None]:
    updates = {
        "UAA_API_LOCAL_AUTH_ENABLED": "1",
        "UAA_API_LOCAL_BEARER": RELEASE_LATENCY_LOCAL_API_BEARER,
        "UAA_TASK_DECOMPOSITION_API_ENABLED": "1",
        "UAA_TASK_DECOMPOSITION_API_BEARER": RELEASE_LATENCY_TASK_BEARER,
        "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED": "1",
        "UAA_OPENWEBUI_TEST_GATEWAY_KEY": RELEASE_LATENCY_LOCAL_GATEWAY_KEY,
        "UAA_FILE_API_SAFE_ROOT": str(safe_root),
    }
    removals = [
        "UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY",
        "UAA_LLAMA_CPP_GATEWAY_ENABLED",
    ]
    previous = {key: os.environ.get(key) for key in [*updates, *removals]}
    try:
        for key in removals:
            os.environ.pop(key, None)
        os.environ.update(updates)
        _install_task_decomposition_test_service(temp_root)
        yield
    finally:
        _restore_task_decomposition_service()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


_PREVIOUS_TASK_DECOMPOSITION_SERVICE: Any | None = None


def _install_task_decomposition_test_service(temp_root: Path) -> None:
    global _PREVIOUS_TASK_DECOMPOSITION_SERVICE
    from ultimate_ai_agent.api import app as api_app
    from ultimate_ai_agent.core.task_decomposition.runtime import (
        CapabilityRegistryStore,
        CapabilityRegistryStoreConfig,
        TaskDecompositionService,
    )

    _PREVIOUS_TASK_DECOMPOSITION_SERVICE = api_app._task_decomposition_service
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(
            registry_path=str(temp_root / "task-registry.json"),
            approval_state_path=str(temp_root / "task-approvals.json"),
            audit_path=str(temp_root / "task-audit.json"),
        )
    )
    api_app._task_decomposition_service = TaskDecompositionService(registry_store=store)


def _restore_task_decomposition_service() -> None:
    global _PREVIOUS_TASK_DECOMPOSITION_SERVICE
    if _PREVIOUS_TASK_DECOMPOSITION_SERVICE is None:
        return
    from ultimate_ai_agent.api import app as api_app

    api_app._task_decomposition_service = _PREVIOUS_TASK_DECOMPOSITION_SERVICE
    _PREVIOUS_TASK_DECOMPOSITION_SERVICE = None


def _measure_release_paths(*, repeat: int, warmup: int) -> list[dict[str, object]]:
    from fastapi.testclient import TestClient
    from ultimate_ai_agent.api import app as api_app

    client = TestClient(api_app.app)
    local_api_headers = {
        "Authorization": f"Bearer {RELEASE_LATENCY_LOCAL_API_BEARER}"
    }
    task_headers = {"Authorization": f"Bearer {RELEASE_LATENCY_TASK_BEARER}"}
    local_gateway_headers = {
        "Authorization": f"Bearer {RELEASE_LATENCY_LOCAL_GATEWAY_KEY}"
    }
    local_gateway_write_headers = {
        **local_gateway_headers,
        "X-UAA-Idempotency-Key": RELEASE_LATENCY_CHAT_IDEMPOTENCY_KEY,
    }
    return [
        _measure_path(
            "health",
            "GET /health",
            RELEASE_LATENCY_BUDGETS_MS["health"],
            repeat,
            warmup,
            lambda: _ok_status(client.get("/health")),
        ),
        _measure_path(
            "api_manifest",
            "GET /api/manifest",
            RELEASE_LATENCY_BUDGETS_MS["api_manifest"],
            repeat,
            warmup,
            lambda: _ok_status(client.get("/api/manifest")),
        ),
        _measure_path(
            "model_route_preview",
            "POST /models/route/preview",
            RELEASE_LATENCY_BUDGETS_MS["model_route_preview"],
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/models/route/preview",
                    headers=local_api_headers,
                    json=_model_route_payload(),
                )
            ),
        ),
        _measure_path(
            "task_decomposition_classify",
            "POST /task-decomposition/classify",
            RELEASE_LATENCY_BUDGETS_MS["task_decomposition_classify"],
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/task-decomposition/classify",
                    headers=task_headers,
                    json=_task_decomposition_payload(),
                )
            ),
        ),
        _measure_path(
            "task_decomposition_decompose",
            "POST /task-decomposition/decompose",
            RELEASE_LATENCY_BUDGETS_MS["task_decomposition_decompose"],
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/task-decomposition/decompose",
                    headers=task_headers,
                    json=_task_decomposition_payload(),
                )
            ),
        ),
        _measure_path(
            "file_read_preview_bounded_text",
            "POST /files/read/preview",
            RELEASE_LATENCY_BUDGETS_MS["file_read_preview_bounded_text"],
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/files/read/preview",
                    headers=local_api_headers,
                    json=_file_preview_payload(),
                )
            ),
        ),
        _measure_path(
            "v1_models_local_gateway",
            "GET /v1/models",
            RELEASE_LATENCY_BUDGETS_MS["v1_models_local_gateway"],
            repeat,
            warmup,
            lambda: _ok_status(client.get("/v1/models", headers=local_gateway_headers)),
        ),
        _measure_path(
            "v1_chat_completions_local_path",
            "POST /v1/chat/completions",
            RELEASE_LATENCY_BUDGETS_MS["v1_chat_completions_local_path"],
            repeat,
            warmup,
            lambda: _ok_status(
                client.post(
                    "/v1/chat/completions",
                    headers=local_gateway_write_headers,
                    json=_local_chat_payload(),
                )
            ),
        ),
        _control_center_render_measurement(),
    ]


def _prime_release_latency_prerequisites() -> dict[str, object]:
    from fastapi.testclient import TestClient
    from ultimate_ai_agent.api import app as api_app

    reason_codes: list[str] = []
    client = TestClient(api_app.app)
    try:
        response = client.get("/api/manifest")
        api_manifest_static_cache_primed = _ok_status(response)
    except Exception:
        api_manifest_static_cache_primed = False
    if not api_manifest_static_cache_primed:
        reason_codes.append("API_MANIFEST_STATIC_CACHE_PRIMER_FAILED")
    return {
        "status": "passed" if api_manifest_static_cache_primed else "failed",
        "api_manifest_static_cache_primed": api_manifest_static_cache_primed,
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
        "reason_codes": reason_codes,
    }


def _measure_hot_paths(*, repeat: int, warmup: int) -> list[dict[str, object]]:
    from fastapi.testclient import TestClient
    from ultimate_ai_agent.api import app as api_app

    client = TestClient(api_app.app)
    task_headers = {"Authorization": f"Bearer {RELEASE_LATENCY_TASK_BEARER}"}
    return [
        _profile_hot_path(
            "task_decomposition_classify",
            "POST /task-decomposition/classify route handler",
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/task-decomposition/classify",
                    headers=task_headers,
                    json=_task_decomposition_payload(),
                )
            ),
            authority_boundary="task_decomposition_bearer_gate_and_route_handler",
        ),
        _profile_hot_path(
            "task_decomposition_decompose",
            "POST /task-decomposition/decompose route handler",
            repeat,
            warmup,
            lambda: _ok_result_envelope(
                client.post(
                    "/task-decomposition/decompose",
                    headers=task_headers,
                    json=_task_decomposition_payload(),
                )
            ),
            authority_boundary="task_decomposition_bearer_gate_and_route_handler",
        ),
        _profile_hot_path(
            "openapi_build",
            "OpenAPI schema build",
            repeat,
            warmup,
            lambda: _profile_openapi_build(api_app.app),
            authority_boundary="openapi_schema_generation_no_runtime_authority",
        ),
    ]


def _profile_hot_path(
    profile_id: str,
    label: str,
    repeat: int,
    warmup: int,
    call: Callable[[], bool],
    *,
    authority_boundary: str,
) -> dict[str, object]:
    warmup_failures = 0
    for _ in range(warmup):
        try:
            if not call():
                warmup_failures += 1
        except Exception:
            warmup_failures += 1

    runs_ms: list[float] = []
    failed_calls = 0
    for _ in range(repeat):
        started = perf_counter()
        try:
            ok = call()
        except Exception:
            ok = False
        elapsed_ms = (perf_counter() - started) * 1000
        runs_ms.append(elapsed_ms)
        if not ok:
            failed_calls += 1

    p50_ms = _percentile_ms(runs_ms, 50)
    p95_ms = _percentile_ms(runs_ms, 95)
    mean_ms = statistics.mean(runs_ms) if runs_ms else 0.0
    status = "passed" if failed_calls == 0 and warmup_failures == 0 else "failed"
    reason_codes = []
    if warmup_failures:
        reason_codes.append("PROFILE_WARMUP_EXPECTATION_FAILED")
    if failed_calls:
        reason_codes.append("PROFILE_EXPECTATION_FAILED")
    return {
        "profile_id": profile_id,
        "safe_label": label,
        "status": status,
        "samples": repeat,
        "warmup_samples": warmup,
        "p50_ms": round(p50_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "mean_ms": round(mean_ms, 2),
        "failed_call_count": failed_calls,
        "warmup_failed_call_count": warmup_failures,
        "reason_codes": reason_codes,
        "authority_boundary": authority_boundary,
        "authority_path_bypassed_for_speed": False,
        "authority_decision_cached_for_speed": False,
        "request_body_recorded": False,
        "response_body_recorded": False,
        "schema_body_recorded": False,
        "raw_path_recorded": False,
        "raw_log_recorded": False,
    }


def _profile_openapi_build(app_instance: Any) -> bool:
    previous_schema = getattr(app_instance, "openapi_schema", None)
    try:
        app_instance.openapi_schema = None
        schema = app_instance.openapi()
        return isinstance(schema, dict) and isinstance(schema.get("paths"), dict)
    finally:
        app_instance.openapi_schema = previous_schema


def _measure_path(
    path_id: str,
    label: str,
    budget_ms: float,
    repeat: int,
    warmup: int,
    call: Callable[[], bool],
) -> dict[str, object]:
    for _ in range(warmup):
        call()

    runs_ms: list[float] = []
    failed_calls = 0
    for _ in range(repeat):
        started = perf_counter()
        try:
            ok = call()
        except Exception:
            ok = False
        elapsed_ms = (perf_counter() - started) * 1000
        runs_ms.append(elapsed_ms)
        if not ok:
            failed_calls += 1

    p50_ms = _percentile_ms(runs_ms, 50)
    p95_ms = _percentile_ms(runs_ms, 95)
    budget_passed = p95_ms < budget_ms
    status = "passed" if failed_calls == 0 and budget_passed else "failed"
    reason_codes = []
    if failed_calls:
        reason_codes.append("HTTP_ROUTE_EXPECTATION_FAILED")
    if not budget_passed:
        reason_codes.append("P95_BUDGET_EXCEEDED")
    return {
        "path_id": path_id,
        "safe_label": label,
        "required": True,
        "status": status,
        "samples": repeat,
        "p50_ms": round(p50_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "budget_ms": round(budget_ms, 2),
        "budget_passed": budget_passed,
        "failed_call_count": failed_calls,
        "reason_codes": reason_codes,
        "authority_path_bypassed_for_speed": False,
        "authority_decision_cached_for_speed": False,
        "response_body_recorded": False,
        "request_body_recorded": False,
    }


def _control_center_render_measurement() -> dict[str, object]:
    return {
        "path_id": "control_center_first_useful_local_render",
        "safe_label": "Control Center first useful local render",
        "required": False,
        "status": "skipped",
        "samples": 0,
        "p50_ms": None,
        "p95_ms": None,
        "budget_ms": round(
            RELEASE_LATENCY_BUDGETS_MS["control_center_first_useful_local_render"],
            2,
        ),
        "budget_passed": None,
        "failed_call_count": 0,
        "reason_codes": ["FRONTEND_RENDER_TIMING_RUNNER_NOT_SCOPED"],
        "skipped_ref": "skipped-ref:p1-039:control-center-render-runner-not-scoped",
        "authority_path_bypassed_for_speed": False,
        "authority_decision_cached_for_speed": False,
        "response_body_recorded": False,
        "request_body_recorded": False,
    }


def _ok_status(response: Any, expected_status: int = 200) -> bool:
    return getattr(response, "status_code", None) == expected_status


def _ok_result_envelope(response: Any) -> bool:
    if getattr(response, "status_code", None) != 200:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return payload.get("success") is True


def _actor_payload() -> dict[str, str]:
    return {
        "actor_type": "human_user",
        "actor_id": "local_operator",
        "authority_source": "explicit_user_request",
    }


def _data_classification_payload() -> dict[str, str]:
    return {
        "classification": "project_private",
        "source": "performance_baseline",
    }


def _model_route_payload() -> dict[str, object]:
    return {
        "request_id": "model-route-request:p0-006",
        "run_id": "run:p0-006:model-route",
        "actor_context": _actor_payload(),
        "task_class": "chat",
        "prompt_summary": "Performance baseline summary only.",
        "data_classification": _data_classification_payload(),
        "required_capabilities": ["chat"],
        "estimated_input_tokens": 128,
        "estimated_output_tokens": 64,
        "routing_policy": {
            "policy_id": "policy:p0-006-local-route",
            "required_capabilities": ["chat"],
            "allowed_provider_kinds": ["local_runtime"],
            "privacy_mode": "local_only",
            "prefer_local": True,
            "allow_cloud": False,
            "allow_paid": False,
        },
        "available_profiles": [
            {
                "model_profile_id": "model-profile:p0-006-local",
                "provider_kind": "local_runtime",
                "model_id": "local-model:p0-006",
                "display_name": "Local baseline model",
                "capabilities": ["chat", "low_latency"],
                "privacy_class": "local_only",
                "max_context_tokens": 4096,
                "time_to_first_token_ms": 10,
                "enabled": True,
                "owner": "ultimate-ai-agent",
                "source": "performance-baseline",
                "version": "p0-006",
            }
        ],
    }


def _task_decomposition_payload() -> dict[str, object]:
    return {
        "raw_request": "Local planning baseline fixture.",
        "context": {"actor_id": "local_operator"},
    }


def _file_preview_payload() -> dict[str, object]:
    return {
        "safe_root_ref": "local_dev_workspace",
        "request": {
            "request_id": "file-read-request:p0-006",
            "run_id": "run:p0-006:file-preview",
            "actor_context": _actor_payload(),
            "path": "preview.txt",
            "purpose": "bounded preview baseline",
            "max_bytes": 128,
        }
    }


def _local_chat_payload() -> dict[str, object]:
    return {
        "model": "uaa-safe-local",
        "messages": [{"role": "user", "content": "Local chat baseline fixture."}],
    }


def _percentile_ms(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((percentile / 100) * len(ordered)) - 1)
    return ordered[min(index, len(ordered) - 1)]


def _write_performance_reports(
    report: dict[str, object],
    hot_path_profile: dict[str, object],
) -> None:
    PERFORMANCE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    regression_report = _performance_regression_report(report)
    _atomic_write_text(
        PERFORMANCE_REPORT_JSON,
        json.dumps(report, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(PERFORMANCE_REPORT_MD, _performance_markdown(report))
    _atomic_write_text(
        PERFORMANCE_REGRESSION_JSON,
        json.dumps(regression_report, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(
        PERFORMANCE_REGRESSION_MD,
        _performance_regression_markdown(regression_report),
    )
    _write_hot_path_profile_report(hot_path_profile)


def _write_hot_path_profile_report(report: dict[str, object]) -> None:
    PERFORMANCE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        HOT_PATH_PROFILE_JSON,
        json.dumps(report, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(HOT_PATH_PROFILE_MD, _hot_path_profile_markdown(report))


def run_hot_path_profile(
    *,
    repeat: int = 5,
    warmup: int = 1,
    write_report: bool = True,
) -> dict[str, object]:
    _ensure_repo_on_path()
    with tempfile.TemporaryDirectory(prefix="uaa_perf_") as temp_dir:
        temp_root = Path(temp_dir)
        safe_root = temp_root / "workspace"
        safe_root.mkdir(parents=True, exist_ok=True)
        with _release_latency_environment(safe_root, temp_root):
            rows = _measure_hot_paths(repeat=repeat, warmup=warmup)

    report = _build_hot_path_profile_report(
        rows=rows,
        generated_at_utc=_utc_now_label(),
        repeat=repeat,
        warmup=warmup,
    )
    if write_report:
        _write_hot_path_profile_report(report)
    return {
        "hot_path_profile_schema_version": report["schema_version"],
        "hot_path_profile_report_json": _repo_relative(HOT_PATH_PROFILE_JSON),
        "hot_path_profile_report_md": _repo_relative(HOT_PATH_PROFILE_MD),
        "hot_path_profile_overall_status": report["overall_status"],
        "hot_path_profile_results": rows,
    }


def _build_hot_path_profile_report(
    *,
    rows: list[dict[str, object]],
    generated_at_utc: str,
    repeat: int,
    warmup: int,
) -> dict[str, object]:
    failed_rows = [row for row in rows if row["status"] != "passed"]
    measurement_context = {"measurement_mode": "fastapi_testclient_local_dev"}
    return {
        "schema_version": "uaa_hot_path_profile.v1",
        "task_ref": HOT_PATH_PROFILE_TASK_REF,
        "source_task_refs": [
            RELEASE_LATENCY_GATE_TASK_REF,
            PERFORMANCE_REGRESSION_TASK_REF,
        ],
        "report_ref": HOT_PATH_PROFILE_REPORT_REF,
        "generated_at_utc": generated_at_utc,
        "measurement_mode": measurement_context["measurement_mode"],
        "profile_repeat": repeat,
        "profile_warmup": warmup,
        "overall_status": "failed" if failed_rows else "passed",
        "environment_safe_summary": _environment_safe_summary(measurement_context),
        "profile_scope": {
            "task_decomposition_profiled": True,
            "openapi_build_profiled": True,
            "timing_summary_only": True,
            "raw_request_response_schema_or_log_recorded": False,
        },
        "authority_invariants": {
            "policy_engine_bypassed_for_speed": False,
            "local_approval_authority_bypassed_for_speed": False,
            "authority_decisions_cached_for_speed": False,
            "authority_path_bypassed_for_speed": False,
            "openapi_checks_preserved": True,
            "route_side_effect_classification_preserved": True,
        },
        "summary": _hot_path_profile_summary(rows),
        "hot_paths": rows,
        "retention_guidance": {
            "latest_files_are_overwritten": True,
            "release_evidence_retention": (
                "retain JSON and Markdown summaries only after verification passes"
            ),
            "cleanup": (
                "delete reports/performance/latest_hot_path_profile.json and .md"
            ),
        },
        "report_safety": {
            "prompt_content_included": False,
            "response_content_included": False,
            "provider_payload_content_included": False,
            "path_material_included": False,
            "log_material_included": False,
            "machine_identity_included": False,
            "environment_dump_included": False,
            "credential_material_included": False,
            "openapi_schema_included": False,
        },
    }


def _hot_path_profile_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    statuses = [str(row["status"]) for row in rows]
    return {
        "total_rows": len(rows),
        "passed_rows": statuses.count("passed"),
        "failed_rows": statuses.count("failed"),
        "profiled_path_ids": [row["profile_id"] for row in rows],
    }


def _performance_regression_report(report: dict[str, object]) -> dict[str, object]:
    path_results = list(report["path_results"])  # type: ignore[index]
    regression_rows = [_performance_regression_row(result) for result in path_results]
    failed_rows = [
        row
        for row in regression_rows
        if row["required"] is True and row["regression_status"] != "passed"
    ]
    return {
        "schema_version": "uaa_performance_regression_report.v1",
        "task_ref": PERFORMANCE_REGRESSION_TASK_REF,
        "source_task_ref": report["task_ref"],
        "source_report_ref": report["report_ref"],
        "report_ref": PERFORMANCE_REGRESSION_REPORT_REF,
        "generated_at_utc": report["generated_at_utc"],
        "overall_status": "failed" if failed_rows else "passed",
        "environment_safe_summary": _environment_safe_summary(report),
        "regression_basis": {
            "comparison_mode": "current_measurement_against_release_budget",
            "historical_trend_storage": "not_retained_by_latest_report",
            "authority_decisions_cached_for_speed": False,
            "authority_path_bypassed_for_speed": False,
        },
        "summary": _performance_regression_summary(regression_rows),
        "path_regressions": regression_rows,
        "retention_guidance": {
            "latest_files_are_overwritten": True,
            "release_evidence_retention": (
                "retain JSON and Markdown reports as release evidence only after "
                "verification passes"
            ),
            "history_retention": (
                "retain safe report refs and summarized timing rows; do not retain "
                "raw local telemetry"
            ),
            "cleanup": (
                "delete reports/performance/latest_performance_regression_report.json "
                "and .md"
            ),
        },
        "report_safety": {
            "prompt_content_included": False,
            "response_content_included": False,
            "provider_payload_content_included": False,
            "path_material_included": False,
            "log_material_included": False,
            "machine_identity_included": False,
            "environment_dump_included": False,
            "credential_material_included": False,
        },
    }


def _performance_regression_row(result: dict[str, object]) -> dict[str, object]:
    p95_ms = result["p95_ms"]
    budget_ms = result["budget_ms"]
    if isinstance(p95_ms, (int, float)) and isinstance(budget_ms, (int, float)):
        budget_margin_ms = round(float(budget_ms) - float(p95_ms), 2)
        budget_ratio = round(float(p95_ms) / float(budget_ms), 4)
        budget_comparison = "under_budget" if budget_margin_ms > 0 else "over_budget"
    else:
        budget_margin_ms = None
        budget_ratio = None
        budget_comparison = "not_measured"

    regression_status = str(result["status"])
    return {
        "path_id": result["path_id"],
        "safe_label": result["safe_label"],
        "required": result["required"],
        "regression_status": regression_status,
        "samples": result["samples"],
        "p50_ms": result["p50_ms"],
        "p95_ms": p95_ms,
        "budget_ms": budget_ms,
        "budget_margin_ms": budget_margin_ms,
        "budget_ratio": budget_ratio,
        "budget_comparison": budget_comparison,
        "reason_codes": result["reason_codes"],
        "operator_action": _performance_operator_action(
            regression_status=regression_status,
            budget_comparison=budget_comparison,
            required=bool(result["required"]),
        ),
        "request_body_recorded": False,
        "response_body_recorded": False,
    }


def _performance_operator_action(
    *,
    regression_status: str,
    budget_comparison: str,
    required: bool,
) -> str:
    if regression_status == "passed" and budget_comparison == "under_budget":
        return "no_action_required"
    if regression_status in {"skipped", "blocked"} and not required:
        return "keep_visible_until_prerequisite_is_scoped"
    if budget_comparison == "over_budget":
        return "investigate_latency_regression_before_release"
    return "inspect_measurement_status_and_reason_codes"


def _performance_regression_summary(
    regression_rows: list[dict[str, object]],
) -> dict[str, object]:
    statuses = [str(row["regression_status"]) for row in regression_rows]
    over_budget = [
        row for row in regression_rows if row["budget_comparison"] == "over_budget"
    ]
    measured = [
        row
        for row in regression_rows
        if isinstance(row["p95_ms"], (int, float))
        and isinstance(row["budget_ms"], (int, float))
    ]
    return {
        "total_rows": len(regression_rows),
        "measured_rows": len(measured),
        "passed_rows": statuses.count("passed"),
        "failed_rows": statuses.count("failed"),
        "skipped_rows": statuses.count("skipped"),
        "blocked_rows": statuses.count("blocked"),
        "over_budget_rows": len(over_budget),
    }


def _environment_safe_summary(report: dict[str, object]) -> dict[str, object]:
    return {
        "measurement_mode": report["measurement_mode"],
        "runner": "fastapi_testclient_in_process",
        "network_scope": "local_in_process_no_external_network",
        "sample_policy": "per_path_sample_count_recorded_only",
        "machine_identity_recorded": False,
        "environment_variables_recorded": False,
        "raw_paths_recorded": False,
        "raw_logs_recorded": False,
        "raw_prompts_or_responses_recorded": False,
        "credential_material_recorded": False,
    }


def _hot_path_profile_markdown(report: dict[str, object]) -> str:
    rows = []
    for result in report["hot_paths"]:  # type: ignore[index]
        rows.append(
            "| {safe_label} | {status} | {samples} | {warmup} | {p50_ms} | {p95_ms} | {mean_ms} | {reason_codes} |".format(
                safe_label=result["safe_label"],
                status=result["status"],
                samples=result["samples"],
                warmup=result["warmup_samples"],
                p50_ms=result["p50_ms"],
                p95_ms=result["p95_ms"],
                mean_ms=result["mean_ms"],
                reason_codes=", ".join(result["reason_codes"])
                if result["reason_codes"]
                else "none",
            )
        )

    summary = report["summary"]  # type: ignore[index]
    environment = report["environment_safe_summary"]  # type: ignore[index]
    retention = report["retention_guidance"]  # type: ignore[index]
    return "\n".join(
        [
            "# Hot Path Profile",
            "",
            f"Task: `{report['task_ref']}`",
            f"Report ref: `{report['report_ref']}`",
            f"Generated: `{report['generated_at_utc']}`",
            f"Overall status: `{report['overall_status']}`",
            "",
            "## Scope",
            "",
            "Profiles task decomposition classify/decompose route handlers and OpenAPI schema build.",
            "Profiling output is timing-summary only. It does not record request bodies, response bodies, OpenAPI schema bodies, raw paths, logs, machine identity, environment dumps, prompts, provider payloads, or credential material.",
            "Task decomposition profiling uses the existing local bearer-gated route path; OpenAPI profiling restores the schema cache after each sample.",
            "",
            "## Environment-Safe Summary",
            "",
            f"- Measurement mode: `{environment['measurement_mode']}`",
            f"- Runner: `{environment['runner']}`",
            f"- Network scope: `{environment['network_scope']}`",
            "",
            "## Summary",
            "",
            f"- Total rows: `{summary['total_rows']}`",
            f"- Passed rows: `{summary['passed_rows']}`",
            f"- Failed rows: `{summary['failed_rows']}`",
            "",
            "## Timing Summary",
            "",
            "| Hot path | Status | Samples | Warmups | p50 ms | p95 ms | Mean ms | Reason codes |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
            *rows,
            "",
            "## Retention Guidance",
            "",
            f"- Latest files overwritten: `{retention['latest_files_are_overwritten']}`",
            f"- Release evidence retention: {retention['release_evidence_retention']}",
            f"- Cleanup: {retention['cleanup']}",
            "",
        ]
    )


def _performance_regression_markdown(report: dict[str, object]) -> str:
    rows = []
    for result in report["path_regressions"]:  # type: ignore[index]
        p50_ms = result["p50_ms"] if result["p50_ms"] is not None else "skipped"
        p95_ms = result["p95_ms"] if result["p95_ms"] is not None else "skipped"
        margin = (
            result["budget_margin_ms"]
            if result["budget_margin_ms"] is not None
            else "not measured"
        )
        rows.append(
            "| {safe_label} | {status} | {samples} | {p50_ms} | {p95_ms} | {budget_ms} | {comparison} | {margin} | {action} |".format(
                safe_label=result["safe_label"],
                status=result["regression_status"],
                samples=result["samples"],
                p50_ms=p50_ms,
                p95_ms=p95_ms,
                budget_ms=result["budget_ms"],
                comparison=result["budget_comparison"],
                margin=margin,
                action=result["operator_action"],
            )
        )

    summary = report["summary"]  # type: ignore[index]
    environment = report["environment_safe_summary"]  # type: ignore[index]
    retention = report["retention_guidance"]  # type: ignore[index]
    return "\n".join(
        [
            "# Performance Regression Report",
            "",
            f"Task: `{report['task_ref']}`",
            f"Source task: `{report['source_task_ref']}`",
            f"Source report: `{report['source_report_ref']}`",
            f"Report ref: `{report['report_ref']}`",
            f"Generated: `{report['generated_at_utc']}`",
            f"Overall status: `{report['overall_status']}`",
            "",
            "## Environment-Safe Summary",
            "",
            f"- Measurement mode: `{environment['measurement_mode']}`",
            f"- Runner: `{environment['runner']}`",
            f"- Network scope: `{environment['network_scope']}`",
            "- Machine identity, environment variables, raw paths, raw logs, prompts, responses, provider payloads, and credential material are not recorded.",
            "",
            "## Summary",
            "",
            f"- Total rows: `{summary['total_rows']}`",
            f"- Measured rows: `{summary['measured_rows']}`",
            f"- Passed rows: `{summary['passed_rows']}`",
            f"- Failed rows: `{summary['failed_rows']}`",
            f"- Skipped rows: `{summary['skipped_rows']}`",
            f"- Blocked rows: `{summary['blocked_rows']}`",
            f"- Over-budget rows: `{summary['over_budget_rows']}`",
            "",
            "## Budget Comparison",
            "",
            "| Path | Status | Samples | p50 ms | p95 ms | Budget ms | Comparison | Margin ms | Operator action |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
            *rows,
            "",
            "## Retention Guidance",
            "",
            f"- Latest files overwritten: `{retention['latest_files_are_overwritten']}`",
            f"- Release evidence retention: {retention['release_evidence_retention']}",
            f"- History retention: {retention['history_retention']}",
            f"- Cleanup: {retention['cleanup']}",
            "",
        ]
    )


def _performance_markdown(report: dict[str, object]) -> str:
    rows = []
    for result in report["path_results"]:  # type: ignore[index]
        p50_ms = result["p50_ms"] if result["p50_ms"] is not None else "skipped"
        p95_ms = result["p95_ms"] if result["p95_ms"] is not None else "skipped"
        rows.append(
            "| {safe_label} | {status} | {p50_ms} | {p95_ms} | {budget_ms} | {samples} |".format(
                safe_label=result["safe_label"],
                status=result["status"],
                p50_ms=p50_ms,
                p95_ms=p95_ms,
                budget_ms=result["budget_ms"],
                samples=result["samples"],
            )
        )
    return "\n".join(
        [
            "# Release Latency Baseline",
            "",
            f"Task: `{report['task_ref']}`",
            f"Baseline source: `{report['baseline_source_ref']}`",
            f"Report ref: `{report['report_ref']}`",
            f"Generated: `{report['generated_at_utc']}`",
            f"Overall status: `{report['overall_status']}`",
            "",
            "Gate policy: required paths fail when missing, failed, or over budget; optional prerequisites must report passed, skipped, or blocked.",
            "Authority decisions are measured on the route path and are not cached, skipped, or bypassed for speed.",
            "Measurement prerequisites prime only safe static manifest metadata before timed route samples; authority, policy, approval, mutable user data, and secret material are not cached for speed.",
            "Reports contain timing summaries and safe refs only; request and response bodies are not recorded.",
            "",
            "## Measurement Prerequisites",
            "",
            f"- Status: `{report['measurement_prerequisites']['status']}`",
            f"- Primed route ref: `{report['measurement_prerequisites']['primed_route_ref']}`",
            f"- Static metadata cache only: `{report['measurement_prerequisites']['static_metadata_cache_only']}`",
            f"- Authority decisions cached for speed: `{report['measurement_prerequisites']['authority_decisions_cached_for_speed']}`",
            f"- Foundation Gate status cached for speed: `{report['measurement_prerequisites']['foundation_gate_status_cached_for_speed']}`",
            f"- Secret material cached for speed: `{report['measurement_prerequisites']['secret_material_cached_for_speed']}`",
            "",
            "| Path | Status | p50 ms | p95 ms | Budget ms | Samples |",
            "|---|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "Rollback: delete `reports/performance/latest_release_latency_baseline.json` and `.md`.",
            "",
        ]
    )


def _atomic_write_text(path: Path, text: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(path)


def _repo_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _utc_now_label() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    metrics = _benchmark(
        repeat=args.repeat,
        warmup=args.warmup,
        path_repeat=args.path_repeat,
        path_warmup=args.path_warmup,
        write_report=not args.no_write_report,
    )
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent Foundation Gate benchmark")
        print(f"Repeats: {metrics['repeat']}")
        print(f"Warmups: {metrics['warmup']}")
        print(f"Status: {metrics['foundation_gate_status']}")
        print(f"Criteria: {metrics['foundation_gate_result_count']}")
        print(f"Mean: {metrics['foundation_gate_mean_ms']} ms/evaluation")
        print(f"Best: {metrics['foundation_gate_best_ms']} ms/evaluation")
        print("")
        print("Release latency baseline")
        print(f"Status: {metrics['release_latency_overall_status']}")
        print(f"Report JSON: {metrics['release_latency_report_json']}")
        print(f"Report MD: {metrics['release_latency_report_md']}")
        print(f"Regression JSON: {metrics['performance_regression_report_json']}")
        print(f"Regression MD: {metrics['performance_regression_report_md']}")
        print(f"Hot profile JSON: {metrics['hot_path_profile_report_json']}")
        print(f"Hot profile MD: {metrics['hot_path_profile_report_md']}")
        print(f"Hot profile status: {metrics['hot_path_profile_overall_status']}")
        for result in metrics["release_latency_path_results"]:  # type: ignore[index]
            p95 = result["p95_ms"] if result["p95_ms"] is not None else "skipped"
            print(
                f"- {result['safe_label']}: {result['status']} "
                f"(p95 {p95} ms, budget {result['budget_ms']} ms)"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
