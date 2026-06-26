#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.providers import build_provider_setup_guide_catalog  # noqa: E402


def main() -> int:
    catalog = build_provider_setup_guide_catalog()
    try:
        print(json.dumps(catalog.model_dump(mode="json"), indent=2, sort_keys=True))
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
