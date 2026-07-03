#!/usr/bin/env python3
from __future__ import annotations

import json

from ultimate_ai_agent.core.connectors import build_connector_draft_proposal_read_model


def main() -> int:
    read_model = build_connector_draft_proposal_read_model()
    payload = read_model.model_dump(mode="json")
    payload["real_connector_runtime_performed"] = False
    payload["connector_send_or_write_performed"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
