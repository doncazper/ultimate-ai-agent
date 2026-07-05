#!/usr/bin/env python3
from __future__ import annotations

import json

from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)


def main() -> int:
    read_model = build_model_provider_control_plane_read_model()
    print(json.dumps(read_model.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
