#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ultimate_ai_agent.core.memory import run_governed_memory_retrieval_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic content-free governed memory benchmark."
    )
    parser.add_argument("--json", action="store_true", help="Emit redacted JSON.")
    args = parser.parse_args()
    result = run_governed_memory_retrieval_benchmark()
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
        return 0
    print("Governed memory retrieval benchmark")
    print(f"  Precision: {result.precision_at_limit:.2f}")
    print(f"  Recall: {result.recall_at_limit:.2f}")
    print(f"  Exclusion correctness: {result.exclusion_correctness:.2f}")
    print(f"  Selected refs: {len(result.selected_refs)}")
    print(f"  Excluded refs: {len(result.excluded_refs)}")
    print("  Raw content persisted: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
