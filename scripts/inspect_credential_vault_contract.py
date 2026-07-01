#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.secrets import build_provider_credential_vault_snapshot  # noqa: E402


def main() -> int:
    snapshot = build_provider_credential_vault_snapshot()
    try:
        print(json.dumps(snapshot.model_dump(mode="json"), indent=2, sort_keys=True))
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
