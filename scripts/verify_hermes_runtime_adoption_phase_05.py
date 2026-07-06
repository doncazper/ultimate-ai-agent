#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    build_runtime_streaming_progress_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_streaming_progress_payload(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_streaming_progress.v1":
        _fail("unexpected streaming progress schema")
    if payload.get("status") != "read_model_event_preview_only":
        _fail("streaming progress must stay read-model preview only")
    if payload.get("stream_state") != "stale_disconnected":
        _fail("streaming progress must be visibly stale/disconnected")
    if payload.get("stale_stream") is not True:
        _fail("stale stream label is required")
    if payload.get("uaa_controls_authority") is not True:
        _fail("UAA must remain the authority owner")
    if payload.get("control_center_talks_directly_to_runtime") is not False:
        _fail("Control Center must not talk directly to runtime")
    if payload.get("safe_refs_only") is not True:
        _fail("streaming progress must use safe refs only")
    if payload.get("bounded_retention_required") is not True:
        _fail("bounded retention must stay required")
    if payload.get("event_hashes_required") is not True:
        _fail("event hashes must stay required")
    for flag in [
        "live_subscription_enabled",
        "sse_transport_enabled",
        "websocket_transport_enabled",
        "reconnect_enabled",
        "event_ingest_enabled",
        "raw_runtime_payload_persisted",
        "raw_tool_payload_persisted",
        "raw_token_persisted",
        "raw_log_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
    ]:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    events = payload.get("event_previews")
    if not isinstance(events, list) or len(events) != 5:
        _fail("expected five ordered event previews")
    if payload.get("event_count") != len(events):
        _fail("event count drifted")
    sequences = [event.get("sequence") for event in events if isinstance(event, dict)]
    if sequences != list(range(len(events))):
        _fail("event previews are not ordered")
    event_kinds = {event.get("event_kind") for event in events if isinstance(event, dict)}
    for required_kind in [
        "token",
        "tool_started",
        "tool_completed",
        "approval_wait",
        "warning",
    ]:
        if required_kind not in event_kinds:
            _fail(f"missing event kind {required_kind}")
    proof_refs = payload.get("proof_refs")
    if not isinstance(proof_refs, list) or not proof_refs:
        _fail("missing proof refs")
    for event in events:
        if not isinstance(event, dict):
            _fail("event preview payload is invalid")
        if event.get("proof_ref") not in proof_refs:
            _fail("event proof ref is not bound to top-level proof refs")
        if not str(event.get("event_hash_ref", "")).startswith("event-hash-ref:"):
            _fail("event hash ref is missing")
        if int(event.get("preview_limit_bytes", 0)) > 2048:
            _fail("event preview limit is unbounded")
        for flag in [
            "runtime_payload_persisted",
            "raw_tool_payload_persisted",
            "raw_token_persisted",
            "raw_log_persisted",
            "raw_prompt_persisted",
            "raw_response_persisted",
        ]:
            if event.get(flag) is not False:
                _fail(f"event {flag} must remain false")
    blocked = payload.get("blocked_authority_refs")
    if not isinstance(blocked, list) or (
        "blocked-authority:runtime-streaming-progress-live-sse" not in blocked
    ):
        _fail("missing live streaming transport blocked ref")


def main() -> None:
    read_model = build_runtime_streaming_progress_read_model()
    _assert_streaming_progress_payload(read_model.model_dump(mode="json"))

    client = TestClient(app)
    response = client.get("/api/runtime/streaming-progress")
    if response.status_code != 200:
        _fail(f"streaming progress route returned {response.status_code}")
    body = response.json()
    _assert_streaming_progress_payload(body.get("data", {}))
    if body.get("redactions_applied") is None:
        _fail("streaming progress route must report redactions")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-streaming-progress",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    for field in [
        "execution_performed",
        "live_subscription_performed",
        "sse_subscription_performed",
        "websocket_subscription_performed",
        "raw_runtime_payload_persisted",
        "raw_tool_payload_persisted",
    ]:
        if cli_payload.get(field) is not False:
            _fail(f"CLI {field} must remain false")
    _assert_streaming_progress_payload(
        cli_payload.get("runtime_streaming_progress", {})
    )
    print(
        "Hermes Runtime Adoption Phase 05 streaming progress verification passed."
    )


if __name__ == "__main__":
    main()
