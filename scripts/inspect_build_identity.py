#!/usr/bin/env python3
from __future__ import annotations

import json

from ultimate_ai_agent.core.build_identity import build_identity


def main() -> int:
    print(
        json.dumps(build_identity().model_dump(mode="json"), indent=2, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
