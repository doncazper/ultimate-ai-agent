#!/usr/bin/env python3
"""Inspect the ECO-009 exact read-only connector posture and safe demo lane."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.connectors.read_only_platform import (  # noqa: E402
    CalendarMetadataSnapshotAdapter,
    CalendarMetadataSnapshotRow,
    ConnectorReadPlatform,
    ConnectorReadRequest,
    build_eco009_connector_read_platform_posture,
)


def _demo() -> tuple[ConnectorReadPlatform, ConnectorReadRequest]:
    observed_at = datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc)
    rows = tuple(
        CalendarMetadataSnapshotRow(
            event_ref=f"calendar-event-ref:eco-009-demo-{index}",
            starts_at=observed_at + timedelta(hours=index),
            ends_at=observed_at + timedelta(hours=index + 1),
            availability_ref="availability-ref:busy",
            provenance_ref="provenance-ref:eco-009:synthetic-demo",
            source_revision_ref="source-revision-ref:eco-009:synthetic-demo-v1",
        )
        for index in range(2)
    )
    platform = ConnectorReadPlatform()
    platform.register_calendar_snapshot(
        CalendarMetadataSnapshotAdapter(
            source_ref="connector-source-ref:eco-009:synthetic-demo",
            workspace_ref="workspace-ref:eco-009:synthetic-demo",
            rows=rows,
            provenance_ref="provenance-ref:eco-009:synthetic-demo",
        )
    )
    request = ConnectorReadRequest(
        request_ref="request-ref:eco-009:synthetic-demo",
        workspace_ref="workspace-ref:eco-009:synthetic-demo",
        source_ref="connector-source-ref:eco-009:synthetic-demo",
        field_refs=("event_ref", "starts_at", "ends_at", "availability_ref"),
        starts_at=observed_at,
        ends_at=observed_at + timedelta(days=1),
        limit=2,
    )
    return platform, request


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect ECO-009 without account, network, or write authority."
    )
    parser.add_argument(
        "--demo-safe-snapshot",
        action="store_true",
        help="Run a deterministic synthetic metadata-only snapshot read.",
    )
    args = parser.parse_args()

    platform: ConnectorReadPlatform | None = None
    outcome: dict[str, object] | None = None
    if args.demo_safe_snapshot:
        platform, request = _demo()
        outcome = platform.read(
            request,
            now=datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc),
        ).model_dump(mode="json")
    payload = {
        "schema_version": "uaa-eco-009-read-only-connector-inspection.v1",
        "command_ref": "repo-local-command:inspect-eco-009-read-only-connectors",
        "posture": build_eco009_connector_read_platform_posture(platform),
        "demo_outcome": outcome,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
