#!/usr/bin/env python3
"""Benchmark the typed Foundation Gate evaluator without running commands."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


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
        description="Benchmark FoundationGateEvaluator.evaluate().",
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
    parser.add_argument("--json", action="store_true", help="Print metrics as JSON.")
    return parser.parse_args(argv)


def _benchmark(*, repeat: int, warmup: int) -> dict[str, object]:
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
    return {
        "schema_version": "foundation_gate_benchmark.v1",
        "repeat": repeat,
        "warmup": warmup,
        "foundation_gate_runs_ms": [round(value, 2) for value in runs_ms],
        "foundation_gate_best_ms": round(best_ms, 2),
        "foundation_gate_mean_ms": round(mean_ms, 2),
        "foundation_gate_status": report_status,
        "foundation_gate_result_count": result_count,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    metrics = _benchmark(repeat=args.repeat, warmup=args.warmup)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
