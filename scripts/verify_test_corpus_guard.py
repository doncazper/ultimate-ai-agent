#!/usr/bin/env python3
"""Run the deterministic test-corpus inventory and retirement guard."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verification.test_corpus_guard import (  # noqa: E402
    TestCorpusGuardError,
    verify_test_corpus_guard,
)


def main() -> int:
    try:
        result = verify_test_corpus_guard(ROOT)
    except TestCorpusGuardError as exc:
        print(f"test corpus guard failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
