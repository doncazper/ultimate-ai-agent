#!/usr/bin/env python3
"""Run bounded liveness-only smoke checks against loopback adapter APIs."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def _run_liveness(package: Path, service: str, command: list[str]) -> bool:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(package / "compose.yaml"),
            "exec",
            "-T",
            service,
            *command,
        ],
        check=False,
        capture_output=True,
        timeout=15,
    )
    return result.returncode == 0


def main() -> int:
    package = Path(__file__).resolve().parents[1]
    try:
        searx_ok = _run_liveness(
            package,
            "searxng",
            ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"],
        )
        firecrawl_ok = _run_liveness(
            package,
            "firecrawl-api",
            [
                "node",
                "-e",
                "fetch('http://127.0.0.1:3002/v0/health/liveness')"
                ".then(r=>{if(!r.ok)process.exit(1)})"
                ".catch(()=>process.exit(1))",
            ],
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(
            "local web service smoke blocked: adapter_health_unavailable",
            file=sys.stderr,
        )
        return 1
    if not searx_ok or not firecrawl_ok:
        print(
            "local web service smoke blocked: liveness_check_failed",
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "schema_version": "uaa-local-web-services-smoke.v1",
                "checks": [
                    {
                        "evidence_ref": "local-web-service:searxng:liveness",
                        "status": "passed",
                    },
                    {
                        "evidence_ref": "local-web-service:firecrawl:liveness",
                        "status": "passed",
                    },
                ],
                "provider_payload_persisted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
