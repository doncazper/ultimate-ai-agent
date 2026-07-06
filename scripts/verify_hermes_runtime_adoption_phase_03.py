#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import build_runtime_run_events_read_model


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_run_events_read_model()

    if read_model.status != "proposal_read_model_only":
        failures.append("runtime run events must remain proposal/read-model only")
    if not read_model.uaa_controls_authority:
        failures.append("UAA must remain the authority owner")
    if not read_model.no_mutation_routes_registered:
        failures.append("Phase 03 must not register mutation routes")
    if any(
        (
            read_model.create_run_route_enabled,
            read_model.stop_run_route_enabled,
            read_model.approval_resolution_route_enabled,
            read_model.live_event_stream_enabled,
        )
    ):
        failures.append("run create/stop/approval/live stream flags must stay disabled")
    if read_model.completed_run_count != 0:
        failures.append("Phase 03 must not claim completed delegated runs")
    if read_model.proposal_count != len(read_model.run_proposals):
        failures.append("proposal count drifted from run proposals")
    if read_model.approval_wait_count != 1:
        failures.append("expected one approval-wait proposal")
    if any(
        proposal.uaa_durable_run_state == "completed"
        for proposal in read_model.run_proposals
    ):
        failures.append("run proposal cannot claim completed durable state")
    if any(event.runtime_payload_persisted for event in read_model.event_previews):
        failures.append("runtime event previews cannot persist runtime payloads")

    client = TestClient(app)
    response = client.get("/api/runtime/run-events")
    if response.status_code != 200:
        failures.append(f"GET /api/runtime/run-events returned {response.status_code}")
    else:
        body = response.json()
        if body.get("data", {}).get("schema_version") != "runtime_run_events.v1":
            failures.append("API route did not return runtime_run_events.v1")

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-run-events",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    if cli.returncode != 0:
        failures.append("CLI inspect-run-events failed")
    else:
        payload = json.loads(cli.stdout)
        if payload.get("execution_performed") is not False:
            failures.append("CLI payload must report no execution")
        if payload.get("stop_performed") is not False:
            failures.append("CLI payload must report no stop")

    if failures:
        print("Hermes runtime adoption Phase 03 verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Hermes runtime adoption Phase 03 verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
