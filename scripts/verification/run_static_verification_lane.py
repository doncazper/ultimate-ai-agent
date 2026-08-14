#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification import run_all_legacy as legacy  # noqa: E402
from scripts.verification.static_scan_context import (  # noqa: E402
    resolve_repository_sha,
)
from scripts.verification.run_static_scan_shards import (  # noqa: E402
    execute_static_scans,
)


DEFAULT_STATIC_WORKERS = 4


def _parse_scheduler_args(
    argv: list[str] | None,
) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--static-workers", type=int, default=DEFAULT_STATIC_WORKERS)
    parser.add_argument("--cpu-budget")
    parser.add_argument("--static-scan-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--static-basetemp")
    parser.add_argument("--repository-sha")
    args, legacy_argv = parser.parse_known_args(argv)
    if (
        args.static_workers <= 0
        or not math.isfinite(args.static_scan_timeout_seconds)
        or args.static_scan_timeout_seconds <= 0
    ):
        parser.error("static worker settings must be greater than zero")
    return args, legacy_argv


def main(argv: list[str] | None = None) -> None:
    args, legacy_argv = _parse_scheduler_args(argv)
    original_run_static_scans = legacy.run_static_scans

    def run_static_scans(timings: Any | None = None) -> None:
        try:
            if args.static_workers == 1:
                actual_sha = resolve_repository_sha(legacy.ROOT)
                if (
                    args.repository_sha is not None
                    and args.repository_sha != actual_sha
                ):
                    raise ValueError("static scan repository identity mismatch")
                original_run_static_scans(timings)
                return
            report = execute_static_scans(
                legacy.SCAN_SEQUENCE,
                root=legacy.ROOT,
                max_workers=args.static_workers,
                cpu_budget=args.cpu_budget,
                basetemp=(Path(args.static_basetemp) if args.static_basetemp else None),
                scan_timeout_seconds=args.static_scan_timeout_seconds,
                repository_sha=args.repository_sha,
                safe_summary=True,
            )
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            print(
                "FAIL: static scheduler stopped safely "
                f"(failure-ref:{type(exc).__name__})",
                file=sys.stderr,
            )
            raise SystemExit(1) from None
        if timings is not None:
            timings.extend(report.timing_entries)
        if not report.passed:
            raise SystemExit(1)

    legacy.run_static_scans = run_static_scans
    try:
        legacy.main(legacy_argv)
    finally:
        legacy.run_static_scans = original_run_static_scans


if __name__ == "__main__":
    main()
