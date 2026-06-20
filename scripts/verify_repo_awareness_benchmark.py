#!/usr/bin/env python3
"""Verify repo awareness benchmark schema, docs, and tracked snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmark_repo_awareness import validate_repo_awareness_benchmark  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the repo awareness benchmark ledger.")
    parser.parse_args(argv)
    failures = validate_repo_awareness_benchmark()
    if failures:
        print("FAIL: repo awareness benchmark verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: repo awareness benchmark ledger is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
