#!/usr/bin/env python3
"""Profile release-critical hot paths with timing-summary-only output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmark_foundation_gate import (  # noqa: E402
    run_hot_path_profile,
)


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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile task decomposition and OpenAPI hot paths safely.",
    )
    parser.add_argument(
        "--repeat",
        type=_positive_int,
        default=5,
        help="Number of timed samples per hot path. Default: 5.",
    )
    parser.add_argument(
        "--warmup",
        type=_non_negative_int,
        default=1,
        help="Number of untimed warmup samples per hot path. Default: 1.",
    )
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="Do not write reports/performance output.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    metrics = run_hot_path_profile(
        repeat=args.repeat,
        warmup=args.warmup,
        write_report=not args.no_write_report,
    )
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent hot path profile")
        print(f"Status: {metrics['hot_path_profile_overall_status']}")
        print(f"Report JSON: {metrics['hot_path_profile_report_json']}")
        print(f"Report MD: {metrics['hot_path_profile_report_md']}")
        for result in metrics["hot_path_profile_results"]:  # type: ignore[index]
            print(
                f"- {result['safe_label']}: {result['status']} "
                f"(p95 {result['p95_ms']} ms, samples {result['samples']})"
            )
    return 0 if metrics["hot_path_profile_overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
