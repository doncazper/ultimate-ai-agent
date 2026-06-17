#!/usr/bin/env python3
"""Fail when the typed Foundation Gate evaluator exceeds latency budgets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_BEST_MS = 20_000.0
DEFAULT_MAX_MEAN_MS = 25_000.0


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
        "--max-best-ms",
        type=_positive_float,
        default=_env_float_or_error(
            parser,
            "FOUNDATION_GATE_MAX_BEST_MS",
            DEFAULT_MAX_BEST_MS,
        ),
        help=(
            "Maximum allowed best Foundation Gate evaluation latency in ms. "
            "Default: 20000 or FOUNDATION_GATE_MAX_BEST_MS."
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _ensure_repo_on_path()
    from scripts.benchmark_foundation_gate import _benchmark

    metrics = _benchmark(repeat=args.repeat, warmup=args.warmup)
    best_ms = float(metrics["foundation_gate_best_ms"])
    mean_ms = float(metrics["foundation_gate_mean_ms"])
    status = str(metrics["foundation_gate_status"])
    failures = []
    if status != "passed":
        failures.append(f"Foundation Gate status is {status!r}, expected 'passed'")
    if best_ms > args.max_best_ms:
        failures.append(
            f"best {best_ms:.2f} ms exceeds budget {args.max_best_ms:.2f} ms"
        )
    if mean_ms > args.max_mean_ms:
        failures.append(
            f"mean {mean_ms:.2f} ms exceeds budget {args.max_mean_ms:.2f} ms"
        )

    payload = {
        **metrics,
        "max_best_ms": args.max_best_ms,
        "max_mean_ms": args.max_mean_ms,
        "passed": not failures,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent Foundation Gate latency check")
        print(f"Status: {status}")
        print(f"Best: {best_ms:.2f} ms/evaluation (budget {args.max_best_ms:.2f})")
        print(f"Mean: {mean_ms:.2f} ms/evaluation (budget {args.max_mean_ms:.2f})")
        if failures:
            print("FAILED")
            for failure in failures:
                print(f"- {failure}")
        else:
            print("PASSED")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
