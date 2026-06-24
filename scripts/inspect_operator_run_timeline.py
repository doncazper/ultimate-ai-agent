#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


def load_operator_run_timeline(
    repository: FounderLoopRepository | None = None,
) -> dict[str, Any]:
    repo = repository or FounderLoopRepository.from_env()
    timeline = repo.evidence_timeline().get("operator_run_timeline")
    if not isinstance(timeline, dict):
        raise RuntimeError("operator run timeline is missing from evidence timeline")
    return timeline


def _bounded_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if value < 0:
        raise argparse.ArgumentTypeError("--limit-events must be non-negative")
    return min(value, 200)


def inspect_payload(
    *,
    repository: FounderLoopRepository | None = None,
    limit_events: int | None = None,
) -> dict[str, Any]:
    timeline = dict(load_operator_run_timeline(repository))
    if limit_events is not None:
        timeline["run_events"] = list(timeline.get("run_events", []))[
            : _bounded_limit(limit_events)
        ]
    return timeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the redacted Operator Run Timeline and frontier-AI cost posture "
            "from the Python core read model."
        )
    )
    parser.add_argument(
        "--limit-events",
        type=int,
        default=None,
        help="Limit rendered run events without changing the recorded event count.",
    )
    args = parser.parse_args(argv)
    payload = inspect_payload(limit_events=_bounded_limit(args.limit_events))
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
