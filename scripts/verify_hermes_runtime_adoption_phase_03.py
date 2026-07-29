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

    if read_model.status != "durable_local_replay":
        failures.append("runtime run events must expose durable local replay")
    if read_model.authority_state_route_ref != "GET /api/runtime/authority-state":
        failures.append("run events must expose AuthorityState route parity")
    if (
        read_model.authority_state_mapping_ref
        != "lane-ref:runtime-run-events-read-model"
    ):
        failures.append("run events must bind to the AuthorityState lane mapping")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("default read-only lease must allow run-event inspection")
    if "adapter-ref:runtime-run-create:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("run creation adapter must remain explicitly unsupported")
    if not read_model.uaa_controls_authority:
        failures.append("UAA must remain the authority owner")
    if not read_model.no_runtime_control_routes_registered:
        failures.append("delegated runtime control routes must remain unregistered")
    if any(
        (
            read_model.create_run_route_enabled,
            read_model.stop_run_route_enabled,
            read_model.approval_resolution_route_enabled,
            read_model.live_event_stream_enabled,
        )
    ):
        failures.append("run create/stop/approval/live stream flags must stay disabled")
    if read_model.proposal_count != len(read_model.run_proposals):
        failures.append("proposal count drifted from run proposals")
    expected_approval_wait_count = sum(
        event.event_kind == "approval_wait_entered"
        for event in read_model.event_previews
    )
    if read_model.approval_wait_count != expected_approval_wait_count:
        failures.append("approval-wait count drifted from durable events")
    expected_completed_run_count = sum(
        stream.successful_receipt_recorded
        or stream.terminal_event_kind == "completion_verified"
        for stream in read_model.stream_summaries
    )
    if read_model.completed_run_count != expected_completed_run_count:
        failures.append("completed-run count drifted from durable receipt truth")
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
        if (
            body.get("data", {}).get("authority_state_mapping_ref")
            != "lane-ref:runtime-run-events-read-model"
        ):
            failures.append("API route did not return AuthorityState mapping ref")

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
        if (
            payload.get("authority_state", {}).get("mapping_ref")
            != "lane-ref:runtime-run-events-read-model"
        ):
            failures.append("CLI payload must report AuthorityState mapping ref")

    if failures:
        print("Hermes runtime adoption Phase 03 verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Hermes runtime adoption Phase 03 verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
