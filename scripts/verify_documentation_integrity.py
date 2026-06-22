#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification.documentation_integrity import legacy as _legacy  # noqa: E402

__all__ = [name for name in dir(_legacy) if not name.startswith("_")]
globals().update(
    {
        name: getattr(_legacy, name)
        for name in dir(_legacy)
        if not (name.startswith("__") and name.endswith("__"))
    }
)


if __name__ == "__main__":
    sys.exit(_legacy.main())
