#!/usr/bin/env python3
from __future__ import annotations

import json

from ultimate_ai_agent.core.platform_capabilities import build_platform_capability_snapshot


def build_cli_payload() -> dict[str, object]:
    return build_platform_capability_snapshot().model_dump(mode="json")


def main() -> int:
    print(json.dumps(build_cli_payload(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
