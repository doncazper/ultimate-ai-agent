#!/usr/bin/env python3
from __future__ import annotations

import json

from ultimate_ai_agent.core.control_center.operator_workspace_spine import (
    build_operator_workspace_spine_read_model,
)


def main() -> int:
    read_model = build_operator_workspace_spine_read_model()
    payload = read_model.model_dump(mode="json")
    payload.update(
        {
            "real_workspace_runtime_performed": False,
            "git_mutation_performed": False,
            "shell_subprocess_performed": False,
            "browser_automation_performed": False,
            "dev_server_started": False,
            "coworker_dispatch_performed": False,
            "provider_or_connector_runtime_performed": False,
        }
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
