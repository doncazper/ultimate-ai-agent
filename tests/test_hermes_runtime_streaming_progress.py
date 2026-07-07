import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_STREAMING_PROGRESS_AUTHORITY_MAPPING_REF,
    RUNTIME_STREAMING_PROGRESS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_STREAMING_PROGRESS_AUTHORITY_STATE_ROUTE_REF,
    RuntimeStreamingProgressEventPreview,
    RuntimeStreamingProgressReadModel,
    build_runtime_streaming_progress_read_model,
)


client = TestClient(app)


def test_runtime_streaming_progress_is_read_model_only() -> None:
    read_model = build_runtime_streaming_progress_read_model()

    assert read_model.schema_version == "runtime_streaming_progress.v1"
    assert read_model.status == "read_model_event_preview_only"
    assert read_model.authority_state_route_ref == (
        RUNTIME_STREAMING_PROGRESS_AUTHORITY_STATE_ROUTE_REF
    )
    assert read_model.authority_state_cli_ref == (
        RUNTIME_STREAMING_PROGRESS_AUTHORITY_STATE_CLI_REF
    )
    assert read_model.authority_state_mapping_ref == (
        RUNTIME_STREAMING_PROGRESS_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert "adapter-ref:runtime-streaming-progress-live-sse:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.stream_state == "stale_disconnected"
    assert read_model.stale_stream is True
    assert read_model.live_subscription_enabled is False
    assert read_model.sse_transport_enabled is False
    assert read_model.websocket_transport_enabled is False
    assert read_model.reconnect_enabled is False
    assert read_model.event_ingest_enabled is False
    assert read_model.uaa_controls_authority is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.safe_refs_only is True
    assert read_model.raw_runtime_payload_persisted is False
    assert read_model.raw_tool_payload_persisted is False
    assert "blocked-authority:runtime-streaming-progress-live-sse" in (
        read_model.blocked_authority_refs
    )


def test_runtime_streaming_progress_orders_and_hashes_events() -> None:
    read_model = build_runtime_streaming_progress_read_model()

    assert read_model.event_count == len(read_model.event_previews)
    assert [event.sequence for event in read_model.event_previews] == list(
        range(read_model.event_count)
    )
    assert {event.event_kind for event in read_model.event_previews} >= {
        "token",
        "tool_started",
        "tool_completed",
        "warning",
        "approval_wait",
    }
    assert all(event.event_hash_ref.startswith("event-hash-ref:") for event in read_model.event_previews)
    assert all(event.proof_ref in read_model.proof_refs for event in read_model.event_previews)
    assert all(event.raw_tool_payload_persisted is False for event in read_model.event_previews)
    assert all(event.raw_token_persisted is False for event in read_model.event_previews)


def test_runtime_streaming_progress_rejects_live_or_raw_authority() -> None:
    payload = build_runtime_streaming_progress_read_model().model_dump()
    payload["live_subscription_enabled"] = True

    with pytest.raises(ValueError, match="LIVE_AUTHORITY_DENIED"):
        RuntimeStreamingProgressReadModel(**payload)

    payload = build_runtime_streaming_progress_read_model().model_dump()
    payload["stale_stream"] = False

    with pytest.raises(ValueError, match="STALE_LABEL_REQUIRED"):
        RuntimeStreamingProgressReadModel(**payload)

    payload = build_runtime_streaming_progress_read_model().model_dump()
    payload["authority_state_mapping_ref"] = (
        "lane-ref:wrong-runtime-streaming-progress"
    )

    with pytest.raises(ValueError, match="AUTHORITY_MAPPING_MISMATCH"):
        RuntimeStreamingProgressReadModel(**payload)

    event_payload = build_runtime_streaming_progress_read_model().event_previews[0].model_dump()
    event_payload["raw_token_persisted"] = True

    with pytest.raises(ValueError, match="RAW_PERSISTENCE_DENIED"):
        RuntimeStreamingProgressEventPreview(**event_payload)


def test_api_runtime_streaming_progress_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/streaming-progress")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_streaming_progress.v1"
    assert data["route_ref"] == "GET /api/runtime/streaming-progress"
    assert data["authority_state_route_ref"] == "GET /api/runtime/authority-state"
    assert data["authority_state_mapping_ref"] == (
        "lane-ref:runtime-streaming-progress-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert "adapter-ref:runtime-streaming-progress-live-sse:not-implemented" in (
        data["unsupported_adapter_refs"]
    )
    assert data["live_subscription_enabled"] is False
    assert data["sse_transport_enabled"] is False
    assert data["raw_tool_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-streaming-progress:phase-05"
    )


def test_cli_runtime_streaming_progress_uses_same_read_model() -> None:
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

    payload = json.loads(result.stdout)
    read_model = payload["runtime_streaming_progress"]
    assert payload["execution_performed"] is False
    assert payload["live_subscription_performed"] is False
    assert payload["sse_subscription_performed"] is False
    assert payload["websocket_subscription_performed"] is False
    assert payload["authority_state"]["mapping_ref"] == (
        "lane-ref:runtime-streaming-progress-read-model"
    )
    assert payload["authority_state"]["decision_outcome"] == "allow"
    assert read_model["route_ref"] == "GET /api/runtime/streaming-progress"
    assert read_model["cli_ref"] == "uaa runtime inspect-streaming-progress"
    assert read_model["authority_state_cli_ref"] == (
        "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model["stream_state"] == "stale_disconnected"
