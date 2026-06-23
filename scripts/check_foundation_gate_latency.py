#!/usr/bin/env python3
"""Fail when the typed Foundation Gate evaluator exceeds latency budgets."""
from __future__ import annotations


import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_BEST_MS = 30_000.0
DEFAULT_MAX_MEAN_MS = 25_000.0
FOUNDATION_GATE_LATENCY_SCHEMA_VERSION = "uaa_foundation_gate_latency_summary.v1"
FOUNDATION_GATE_LATENCY_TASK_REF = "UAA-P1-043"


def _ensure_repo_on_path() -> None:
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


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


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{name} must be a positive float, got {value!r}"
        ) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(
            f"{name} must be a positive float, got {value!r}"
        )
    return parsed


def _env_float_or_error(
    parser: argparse.ArgumentParser,
    name: str,
    default: float,
) -> float:
    try:
        return _env_float(name, default)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark the Foundation Gate report path and enforce latency budgets.",
    )
    parser.add_argument(
        "--repeat",
        type=_positive_int,
        default=1,
        help="Number of timed report evaluations. Default: 1.",
    )
    parser.add_argument(
        "--warmup",
        type=_non_negative_int,
        default=0,
        help="Number of untimed warmup evaluations. Default: 0.",
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
        "--max-best-ms",
        type=_positive_float,
        default=_env_float_or_error(
            parser,
            "FOUNDATION_GATE_MAX_BEST_MS",
            DEFAULT_MAX_BEST_MS,
        ),
        help=(
            "Maximum allowed best Foundation Gate evaluation latency in ms. "
            "Default: 30000 or FOUNDATION_GATE_MAX_BEST_MS."
        ),
    )
    parser.add_argument(
        "--max-mean-ms",
        type=_positive_float,
        default=_env_float_or_error(
            parser,
            "FOUNDATION_GATE_MAX_MEAN_MS",
            DEFAULT_MAX_MEAN_MS,
        ),
        help=(
            "Maximum allowed mean Foundation Gate evaluation latency in ms. "
            "Default: 25000 or FOUNDATION_GATE_MAX_MEAN_MS."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args(argv)


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: object) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return parsed if parsed >= 0 else 0


def _release_latency_gate_failures(metrics: dict[str, object]) -> list[str]:
    from scripts.benchmark_foundation_gate import (
        RELEASE_LATENCY_BUDGETS_MS,
        RELEASE_LATENCY_OPTIONAL_PATH_IDS,
        RELEASE_LATENCY_REQUIRED_PATH_IDS,
    )

    failures: list[str] = []
    path_results = metrics.get("release_latency_path_results", [])
    if not isinstance(path_results, list):
        return ["release latency path results are missing or malformed"]

    budget_definitions = metrics.get("release_latency_budget_definitions_ms", {})
    if isinstance(budget_definitions, dict):
        for path_id, expected_budget in RELEASE_LATENCY_BUDGETS_MS.items():
            actual_budget = _float_or_none(budget_definitions.get(path_id))
            if actual_budget != expected_budget:
                failures.append(
                    f"{path_id} budget definition is {actual_budget!r}, "
                    f"expected {expected_budget:.2f} ms"
                )
    else:
        failures.append("release latency budget definitions are missing or malformed")

    results_by_path: dict[str, dict[str, object]] = {}
    for result in path_results:
        if not isinstance(result, dict):
            failures.append("release latency path result is malformed")
            continue
        path_id = str(result.get("path_id", ""))
        if not path_id:
            failures.append("release latency path result is missing path_id")
            continue
        if path_id in results_by_path:
            failures.append(f"{path_id} release latency result is duplicated")
            continue
        results_by_path[path_id] = result

    missing_required = sorted(RELEASE_LATENCY_REQUIRED_PATH_IDS - results_by_path.keys())
    for path_id in missing_required:
        failures.append(f"{path_id} release latency result is missing")

    missing_optional = sorted(RELEASE_LATENCY_OPTIONAL_PATH_IDS - results_by_path.keys())
    for path_id in missing_optional:
        failures.append(f"{path_id} optional release latency status is missing")

    for path_id in sorted(RELEASE_LATENCY_REQUIRED_PATH_IDS):
        result = results_by_path.get(path_id)
        if result is None:
            continue
        safe_label = str(result.get("safe_label", path_id))
        result_status = str(result.get("status", "unknown"))
        p95_ms = _float_or_none(result.get("p95_ms"))
        budget_ms = _float_or_none(result.get("budget_ms"))
        expected_budget = RELEASE_LATENCY_BUDGETS_MS[path_id]
        if result_status != "passed":
            failures.append(
                f"{safe_label} release latency status is {result_status!r}, "
                "expected 'passed'"
            )
        if p95_ms is None:
            failures.append(f"{safe_label} release latency p95 is missing")
        elif p95_ms >= expected_budget:
            failures.append(
                f"{safe_label} p95 {p95_ms:.2f} ms exceeds budget {expected_budget:.2f} ms"
            )
        if budget_ms != expected_budget:
            failures.append(
                f"{safe_label} budget is {budget_ms!r}, expected {expected_budget:.2f} ms"
            )
        if result.get("authority_path_bypassed_for_speed") is True:
            failures.append(f"{safe_label} reports authority path bypassed for speed")
        if result.get("authority_decision_cached_for_speed") is True:
            failures.append(f"{safe_label} reports authority decision cached for speed")

    allowed_optional_statuses = {"passed", "skipped", "blocked"}
    for path_id in sorted(RELEASE_LATENCY_OPTIONAL_PATH_IDS):
        result = results_by_path.get(path_id)
        if result is None:
            continue
        safe_label = str(result.get("safe_label", path_id))
        result_status = str(result.get("status", "unknown"))
        expected_budget = RELEASE_LATENCY_BUDGETS_MS[path_id]
        if result_status not in allowed_optional_statuses:
            failures.append(
                f"{safe_label} optional release latency status is {result_status!r}, "
                "expected passed, skipped, or blocked"
            )
        if result_status == "passed":
            p95_ms = _float_or_none(result.get("p95_ms"))
            if p95_ms is None:
                failures.append(f"{safe_label} optional release latency p95 is missing")
            elif p95_ms >= expected_budget:
                failures.append(
                    f"{safe_label} optional p95 {p95_ms:.2f} ms exceeds budget {expected_budget:.2f} ms"
                )
        if result_status in {"skipped", "blocked"} and not result.get("reason_codes"):
            failures.append(
                f"{safe_label} optional {result_status} status lacks reason codes"
            )
        if result.get("authority_path_bypassed_for_speed") is True:
            failures.append(f"{safe_label} reports authority path bypassed for speed")
        if result.get("authority_decision_cached_for_speed") is True:
            failures.append(f"{safe_label} reports authority decision cached for speed")

    return failures


def _release_latency_measurement_prerequisite_failures(
    metrics: dict[str, object],
) -> list[str]:
    prerequisites = metrics.get("release_latency_measurement_prerequisites")
    if not isinstance(prerequisites, dict):
        return ["release latency measurement prerequisites are missing or malformed"]

    failures: list[str] = []
    if prerequisites.get("status") != "passed":
        failures.append("release latency measurement prerequisites did not pass")
    if prerequisites.get("api_manifest_static_cache_primed") is not True:
        failures.append("api manifest static metadata primer did not pass")
    if prerequisites.get("static_metadata_cache_only") is not True:
        failures.append("api manifest primer is not marked static-metadata only")
    false_required_flags = {
        "request_body_recorded": "request body recorded",
        "response_body_recorded": "response body recorded",
        "raw_path_recorded": "raw path recorded",
        "raw_log_recorded": "raw log recorded",
    }
    for flag, label in false_required_flags.items():
        value = prerequisites.get(flag)
        if value is True:
            failures.append(f"release latency primer reports {label}")
        elif value is not False:
            failures.append(
                f"release latency primer {label} flag is not explicitly false"
            )

    unsafe_cache_flags = {
        "authority_decisions_cached_for_speed": (
            "authority decisions cached for speed"
        ),
        "policy_decisions_cached_for_speed": "policy decisions cached for speed",
        "approval_decisions_cached_for_speed": (
            "approval decisions cached for speed"
        ),
        "approval_state_cached_for_speed": "approval state cached for speed",
        "foundation_gate_status_cached_for_speed": (
            "Foundation Gate status cached for speed"
        ),
        "mutable_user_data_cached_for_speed": (
            "mutable user data cached for speed"
        ),
        "secret_material_cached_for_speed": "secret material cached for speed",
    }
    for flag, label in unsafe_cache_flags.items():
        value = prerequisites.get(flag)
        if value is True:
            failures.append(f"release latency primer reports {label}")
        elif value is not False:
            failures.append(
                f"release latency primer {label} flag is not explicitly false"
            )
    return failures


def _foundation_gate_latency_failures(
    metrics: dict[str, object],
    *,
    max_best_ms: float,
    max_mean_ms: float,
) -> list[str]:
    failures: list[str] = []
    best_ms = _float_or_none(metrics.get("foundation_gate_best_ms"))
    mean_ms = _float_or_none(metrics.get("foundation_gate_mean_ms"))
    status = str(metrics.get("foundation_gate_status", "unknown"))
    if status != "passed":
        failures.append(f"Foundation Gate status is {status!r}, expected 'passed'")
    if best_ms is None:
        failures.append("Foundation Gate best latency is missing")
    elif best_ms > max_best_ms:
        failures.append(
            f"best {best_ms:.2f} ms exceeds budget {max_best_ms:.2f} ms"
        )
    if mean_ms is None:
        failures.append("Foundation Gate mean latency is missing")
    elif mean_ms > max_mean_ms:
        failures.append(
            f"mean {mean_ms:.2f} ms exceeds budget {max_mean_ms:.2f} ms"
        )
    release_latency_status = metrics.get("release_latency_overall_status")
    if release_latency_status not in {"passed", "failed"}:
        failures.append("release latency overall status is missing or malformed")
    elif release_latency_status != "passed":
        failures.append(
            f"release latency overall status is {release_latency_status!r}, "
            "expected 'passed'"
        )
    failures.extend(_release_latency_measurement_prerequisite_failures(metrics))
    failures.extend(_release_latency_gate_failures(metrics))
    return failures


def _safe_path_result(result: dict[str, object]) -> dict[str, object]:
    path_id = str(result.get("path_id") or "unknown_path")
    safe_label = str(result.get("safe_label") or path_id)
    status = str(result.get("status") or "unknown")
    p50_ms = _float_or_none(result.get("p50_ms"))
    p95_ms = _float_or_none(result.get("p95_ms"))
    budget_ms = _float_or_none(result.get("budget_ms"))
    if status in {"skipped", "blocked"}:
        budget_status = status
    elif p95_ms is None or budget_ms is None:
        budget_status = "not_measured"
    elif p95_ms < budget_ms:
        budget_status = "within_budget"
    else:
        budget_status = "over_budget"
    reason_codes = result.get("reason_codes", [])
    if not isinstance(reason_codes, list):
        reason_codes = ["MALFORMED_REASON_CODES"]
    return {
        "path_id": path_id,
        "safe_label": safe_label,
        "required": bool(result.get("required", False)),
        "status": status,
        "samples": _int_or_zero(result.get("samples")),
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "budget_ms": budget_ms,
        "budget_status": budget_status,
        "reason_codes": [str(code) for code in reason_codes],
        "authority_path_bypassed_for_speed": bool(
            result.get("authority_path_bypassed_for_speed", False)
        ),
        "authority_decision_cached_for_speed": bool(
            result.get("authority_decision_cached_for_speed", False)
        ),
        "request_body_recorded": bool(result.get("request_body_recorded", False)),
        "response_body_recorded": bool(result.get("response_body_recorded", False)),
    }


def build_foundation_gate_latency_summary(
    metrics: dict[str, object],
    *,
    max_best_ms: float = DEFAULT_MAX_BEST_MS,
    max_mean_ms: float = DEFAULT_MAX_MEAN_MS,
    foundation_gate_report_json: str | None = None,
    foundation_gate_report_md: str | None = None,
) -> dict[str, object]:
    from scripts.benchmark_foundation_gate import RELEASE_LATENCY_OPTIONAL_PATH_IDS

    failures = _foundation_gate_latency_failures(
        metrics,
        max_best_ms=max_best_ms,
        max_mean_ms=max_mean_ms,
    )
    raw_path_results = metrics.get("release_latency_path_results", [])
    safe_path_results = [
        _safe_path_result(result)
        for result in raw_path_results
        if isinstance(result, dict)
    ]
    optional_prerequisites = [
        result
        for result in safe_path_results
        if result["path_id"] in RELEASE_LATENCY_OPTIONAL_PATH_IDS
        and result["status"] in {"skipped", "blocked"}
    ]
    report_refs: dict[str, str] = {}
    for key in (
        "release_latency_report_json",
        "release_latency_report_md",
        "performance_regression_report_json",
        "performance_regression_report_md",
        "hot_path_profile_report_json",
        "hot_path_profile_report_md",
    ):
        value = metrics.get(key)
        if isinstance(value, str) and value:
            report_refs[key] = value

    return {
        "schema_version": FOUNDATION_GATE_LATENCY_SCHEMA_VERSION,
        "task_ref": FOUNDATION_GATE_LATENCY_TASK_REF,
        "status": "passed" if not failures else "failed",
        "p50_p95_status": str(metrics.get("release_latency_overall_status", "unknown")),
        "foundation_gate_status": str(metrics.get("foundation_gate_status", "unknown")),
        "foundation_gate_best_ms": _float_or_none(
            metrics.get("foundation_gate_best_ms")
        ),
        "foundation_gate_mean_ms": _float_or_none(
            metrics.get("foundation_gate_mean_ms")
        ),
        "foundation_gate_best_budget_ms": max_best_ms,
        "foundation_gate_mean_budget_ms": max_mean_ms,
        "release_latency_status": str(
            metrics.get("release_latency_overall_status", "unknown")
        ),
        "hot_path_profile_status": str(
            metrics.get("hot_path_profile_overall_status", "unknown")
        ),
        "accepted_failures": [],
        "failures": failures,
        "report_refs": report_refs,
        "foundation_gate_report_json": foundation_gate_report_json,
        "foundation_gate_report_md": foundation_gate_report_md,
        "environment_safe_summary": {
            "measurement_mode": "local_foundation_gate_latency_summary",
            "runner": "scripts.check_foundation_gate_latency",
            "optional_prerequisite_policy": "skipped_or_blocked_with_reason_codes",
            "machine_identity_recorded": False,
            "environment_variables_recorded": False,
            "raw_paths_recorded": False,
            "raw_logs_recorded": False,
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
        "path_results": safe_path_results,
        "optional_prerequisites": optional_prerequisites,
    }


def run_latency_gate_summary(
    *,
    repeat: int = 1,
    warmup: int = 0,
    path_repeat: int = 5,
    path_warmup: int = 1,
    max_best_ms: float = DEFAULT_MAX_BEST_MS,
    max_mean_ms: float = DEFAULT_MAX_MEAN_MS,
    foundation_gate_report_json: str | None = None,
    foundation_gate_report_md: str | None = None,
    precomputed_foundation_gate_ms: float | None = None,
    precomputed_foundation_gate_status: str | None = None,
    precomputed_foundation_gate_result_count: int | None = None,
) -> dict[str, object]:
    _ensure_repo_on_path()
    from scripts.benchmark_foundation_gate import _benchmark, _benchmark_release_latency_paths

    precomputed_values = (
        precomputed_foundation_gate_ms,
        precomputed_foundation_gate_status,
        precomputed_foundation_gate_result_count,
    )
    if any(value is not None for value in precomputed_values):
        if any(value is None for value in precomputed_values):
            raise ValueError(
                "precomputed Foundation Gate latency requires elapsed ms, status, "
                "and result count"
            )
        elapsed_ms = round(float(precomputed_foundation_gate_ms), 2)
        metrics = {
            "schema_version": "foundation_gate_benchmark.v2",
            "repeat": 1,
            "warmup": 0,
            "foundation_gate_runs_ms": [elapsed_ms],
            "foundation_gate_best_ms": elapsed_ms,
            "foundation_gate_mean_ms": elapsed_ms,
            "foundation_gate_status": str(precomputed_foundation_gate_status),
            "foundation_gate_result_count": int(
                precomputed_foundation_gate_result_count
            ),
            **_benchmark_release_latency_paths(
                repeat=path_repeat,
                warmup=path_warmup,
                write_report=True,
            ),
        }
    else:
        metrics = _benchmark(
            repeat=repeat,
            warmup=warmup,
            path_repeat=path_repeat,
            path_warmup=path_warmup,
        )
    return build_foundation_gate_latency_summary(
        metrics,
        max_best_ms=max_best_ms,
        max_mean_ms=max_mean_ms,
        foundation_gate_report_json=foundation_gate_report_json,
        foundation_gate_report_md=foundation_gate_report_md,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _ensure_repo_on_path()
    from scripts.benchmark_foundation_gate import _benchmark

    metrics = _benchmark(
        repeat=args.repeat,
        warmup=args.warmup,
        path_repeat=args.path_repeat,
        path_warmup=args.path_warmup,
    )
    best_ms = float(metrics["foundation_gate_best_ms"])
    mean_ms = float(metrics["foundation_gate_mean_ms"])
    status = str(metrics["foundation_gate_status"])
    failures = _foundation_gate_latency_failures(
        metrics,
        max_best_ms=args.max_best_ms,
        max_mean_ms=args.max_mean_ms,
    )

    payload = {
        **metrics,
        "max_best_ms": args.max_best_ms,
        "max_mean_ms": args.max_mean_ms,
        "passed": not failures,
        "failures": failures,
        "foundation_gate_latency_summary": build_foundation_gate_latency_summary(
            metrics,
            max_best_ms=args.max_best_ms,
            max_mean_ms=args.max_mean_ms,
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent Foundation Gate latency check")
        print(f"Status: {status}")
        print(f"Best: {best_ms:.2f} ms/evaluation (budget {args.max_best_ms:.2f})")
        print(f"Mean: {mean_ms:.2f} ms/evaluation (budget {args.max_mean_ms:.2f})")
        print(f"Release latency: {metrics['release_latency_overall_status']}")
        print(f"Report JSON: {metrics['release_latency_report_json']}")
        print(f"Report MD: {metrics['release_latency_report_md']}")
        print(f"Regression JSON: {metrics['performance_regression_report_json']}")
        print(f"Regression MD: {metrics['performance_regression_report_md']}")
        print(f"Hot profile JSON: {metrics['hot_path_profile_report_json']}")
        print(f"Hot profile MD: {metrics['hot_path_profile_report_md']}")
        for result in metrics.get("release_latency_path_results", []):
            if not isinstance(result, dict):
                continue
            p95 = result["p95_ms"] if result["p95_ms"] is not None else "skipped"
            print(
                f"- {result['safe_label']}: {result['status']} "
                f"(p95 {p95} ms, budget {result['budget_ms']} ms)"
            )
        if failures:
            print("FAILED")
            for failure in failures:
                print(f"- {failure}")
        else:
            print("PASSED")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
