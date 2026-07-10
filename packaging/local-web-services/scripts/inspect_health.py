#!/usr/bin/env python3
"""Print a bounded safe health summary for the local provider stack."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


EXPECTED_SERVICES = (
    "firecrawl-api",
    "firecrawl-playwright",
    "firecrawl-postgres",
    "firecrawl-rabbitmq",
    "firecrawl-redis",
    "searxng",
    "searxng-valkey",
)


def main() -> int:
    package = Path(__file__).resolve().parents[1]
    command = [
        "docker",
        "compose",
        "-f",
        str(package / "compose.yaml"),
        "ps",
        "--format",
        "json",
    ]
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=30
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("local web service health blocked: compose_unavailable", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print("local web service health blocked: compose_failed", file=sys.stderr)
        return 1
    try:
        raw = result.stdout.strip()
        if not raw:
            rows = []
        elif raw.startswith("["):
            rows = json.loads(raw)
        else:
            rows = [json.loads(line) for line in raw.splitlines()]
    except json.JSONDecodeError:
        print(
            "local web service health blocked: invalid_compose_summary", file=sys.stderr
        )
        return 1
    by_service = {row.get("Service"): row for row in rows if isinstance(row, dict)}
    safe = []
    healthy = True
    for service in EXPECTED_SERVICES:
        row = by_service.get(service, {})
        state = str(row.get("State", "missing")).lower()
        health = str(row.get("Health", "unknown")).lower() or "unknown"
        healthy = healthy and state == "running" and health == "healthy"
        safe.append(
            {
                "service_ref": f"local-web-service:{service}",
                "state": state,
                "health": health,
            }
        )
    print(
        json.dumps(
            {"schema_version": "uaa-local-web-services-health.v1", "services": safe},
            sort_keys=True,
        )
    )
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
