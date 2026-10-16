#!/usr/bin/env python3
"""Inspect two frozen collection contexts without granting corpus acceptance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verification.isolated_collection_observation import (  # noqa: E402
    ObservationError,
    observe_pair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--test", action="append", required=True)
    parser.add_argument("--model-module", action="append", required=True)
    arguments = parser.parse_args()
    try:
        result = observe_pair(
            arguments.baseline,
            arguments.candidate,
            tests=tuple(arguments.test),
            model_modules=tuple(arguments.model_module),
        )
    except ObservationError as exc:
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "reason": str(exc),
                    "acceptance_authority": False,
                }
            )
        )
        return 2
    except (OSError, ValueError):
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "reason": "input_unavailable",
                    "acceptance_authority": False,
                }
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "observed_equal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
