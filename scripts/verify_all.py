#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification import run_all_legacy as _legacy  # noqa: E402

# Compatibility proof for text-based contract tests: scripts/verify_openapi_contract.py

if __name__ == "__main__":
    _legacy.main()
else:
    sys.modules[__name__] = _legacy
