#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


class MutationScoreError(RuntimeError):
    pass


def verify_mutation_score(
    stats_path: Path,
    *,
    minimum_score: float,
    minimum_total: int,
) -> float:
    payload = json.loads(stats_path.read_text(encoding="utf-8"))
    killed = int(payload.get("killed", 0))
    survived = int(payload.get("survived", 0))
    total = int(payload.get("total", 0))
    unresolved = sum(
        int(payload.get(field, 0))
        for field in (
            "no_tests",
            "suspicious",
            "timeout",
            "check_was_interrupted_by_user",
            "segfault",
        )
    )
    if total < minimum_total or killed + survived != total or unresolved:
        raise MutationScoreError("MUTATION_EVIDENCE_INCOMPLETE")
    score = killed * 100.0 / total
    if score < minimum_score:
        raise MutationScoreError("MUTATION_SCORE_BELOW_FLOOR")
    return score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stats_path", type=Path)
    parser.add_argument("--minimum-score", type=float, default=60.0)
    parser.add_argument("--minimum-total", type=int, default=200)
    args = parser.parse_args()
    try:
        score = verify_mutation_score(
            args.stats_path,
            minimum_score=args.minimum_score,
            minimum_total=args.minimum_total,
        )
    except (OSError, ValueError, json.JSONDecodeError, MutationScoreError) as exc:
        print(f"ERROR: mutation evidence failed closed ({exc})")
        return 1
    print(f"Mutation evidence passed: score={score:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
