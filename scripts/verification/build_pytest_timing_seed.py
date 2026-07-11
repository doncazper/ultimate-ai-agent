#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification.run_pytest_shards import (  # noqa: E402
    TIMING_SCHEMA_VERSION,
    discover_test_files,
    parse_pytest_durations,
)


ALLOWED_SOURCE_STATUSES = ("green", "completed_with_failures")


def build_seed(log_dir: Path, *, source_run_status: str) -> dict[str, object]:
    logs = sorted(log_dir.glob("pytest-shard-*.log"))
    if not logs:
        raise ValueError("PYTEST_TIMING_SEED_LOGS_REQUIRED")
    files = set(discover_test_files(ROOT))
    timings: dict[str, float] = {}
    for log_path in logs:
        parsed = parse_pytest_durations(
            log_path.read_text(encoding="utf-8", errors="replace"),
            files,
        )
        for file_path, seconds in parsed.items():
            timings[file_path] = timings.get(file_path, 0.0) + seconds
    if not timings:
        raise ValueError("PYTEST_TIMING_SEED_DURATIONS_REQUIRED")
    return {
        "schema_version": TIMING_SCHEMA_VERSION,
        "advisory_only": True,
        "verification_evidence": False,
        "declared_source_run_status": source_run_status,
        "source_run_status_attestation": "operator_supplied_advisory",
        "timed_file_count": len(timings),
        "timings": [
            {
                "path": file_path,
                "seconds": round(max(seconds, 0.001), 6),
                "source": "historical-pytest-duration-summary",
            }
            for file_path, seconds in sorted(timings.items())
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a safe repo-relative advisory pytest timing seed from shard logs."
        )
    )
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--source-run-status",
        choices=ALLOWED_SOURCE_STATUSES,
        required=True,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_seed(
        Path(args.log_dir),
        source_run_status=args.source_run_status,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(
        "Pytest timing seed written: "
        f"files={payload['timed_file_count']} advisory_only=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
