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
    RuntimeStreamingProgressReplayEvent,
    build_runtime_streaming_progress_replay_events,
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
    assert read_model.readonly_sse_replay_enabled is True
    assert (
        read_model.readonly_sse_replay_source_posture
        == "deterministic_redacted_preview"
    )
    assert read_model.readonly_sse_replay_durable_event_source is False
    assert read_model.readonly_sse_replay_requires_run_ref is True
    assert read_model.readonly_sse_replay_resume_supported is True
    assert read_model.readonly_sse_replay_control_messages_accepted is False
    assert read_model.readonly_sse_replay_mutation_enabled is False
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

    replay_payload = build_runtime_streaming_progress_replay_events(
        build_runtime_streaming_progress_read_model(),
        run_ref=build_runtime_streaming_progress_read_model().runtime_run_ref,
    )[0].model_dump()
    replay_payload["accepts_control_messages"] = True

    with pytest.raises(ValueError, match="REPLAY_CONTROL_DENIED"):
        RuntimeStreamingProgressReplayEvent(**replay_payload)


def test_runtime_streaming_progress_builds_readonly_sse_replay_events() -> None:
    read_model = build_runtime_streaming_progress_read_model()
    events = build_runtime_streaming_progress_replay_events(
        read_model,
        run_ref=read_model.runtime_run_ref,
        after_sequence=1,
    )

    assert [event.sequence for event in events] == [2, 3, 4]
    assert all(event.readonly_replay is True for event in events)
    assert all(
        event.source_posture == "deterministic_redacted_preview" for event in events
    )
    assert all(event.durable_event_source is False for event in events)
    assert all(event.accepts_control_messages is False for event in events)
    assert all(event.mutation_enabled is False for event in events)
    assert all(event.raw_payload_included is False for event in events)
    assert all(event.safe_summary for event in events)

    with pytest.raises(ValueError, match="RUN_REF_UNKNOWN"):
        build_runtime_streaming_progress_replay_events(
            read_model,
            run_ref="runtime-run-ref:unknown",
        )


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
    assert data["replay_route_ref"] == (
        "GET /api/runtime/streaming-progress?transport=sse"
    )
    assert data["readonly_sse_replay_enabled"] is True
    assert data["readonly_sse_replay_source_posture"] == (
        "deterministic_redacted_preview"
    )
    assert data["readonly_sse_replay_durable_event_source"] is False
    assert data["readonly_sse_replay_requires_run_ref"] is True
    assert data["readonly_sse_replay_control_messages_accepted"] is False
    assert data["readonly_sse_replay_mutation_enabled"] is False
    assert "adapter-ref:runtime-streaming-progress-live-sse:not-implemented" in (
        data["unsupported_adapter_refs"]
    )
    assert data["live_subscription_enabled"] is False
    assert data["sse_transport_enabled"] is False
    assert data["raw_tool_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-streaming-progress:phase-05"
    )


def test_api_runtime_streaming_progress_sse_replays_safe_ref_events() -> None:
    read_model = build_runtime_streaming_progress_read_model()

    with client.stream(
        "GET",
        "/api/runtime/streaming-progress",
        params={
            "transport": "sse",
            "run_ref": read_model.runtime_run_ref,
            "after_sequence": 2,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["x-uaa-authority"] == "read-only-sse-replay"
        assert response.headers["x-uaa-control-messages-accepted"] == "false"
        body = response.read().decode("utf-8")

    assert "event: approval_wait" in body
    assert "event: warning" in body
    assert "event: token" not in body
    assert "raw_payload_included" in body
    assert '"raw_payload_included":false' in body
    assert '"source_posture":"deterministic_redacted_preview"' in body
    assert '"durable_event_source":false' in body
    assert '"accepts_control_messages":false' in body
    assert '"mutation_enabled":false' in body
    assert "raw prompt" not in body.lower()
    assert "/" + "Users/" not in body


def test_api_runtime_streaming_progress_documents_sse_media_type() -> None:
    response_content = app.openapi()["paths"]["/api/runtime/streaming-progress"][
        "get"
    ]["responses"]["200"]["content"]

    assert "application/json" in response_content
    assert response_content["text/event-stream"]["schema"] == {"type": "string"}


def test_api_runtime_streaming_progress_sse_denies_unknown_run_ref() -> None:
    response = client.get(
        "/api/runtime/streaming-progress",
        params={"transport": "sse", "run_ref": "runtime-run-ref:unknown"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "RUNTIME_STREAMING_PROGRESS_REPLAY_DENIED"


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
    assert read_model["readonly_sse_replay_enabled"] is True


def test_cli_runtime_streaming_progress_replays_sse_lines() -> None:
    run_ref = build_runtime_streaming_progress_read_model().runtime_run_ref
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-streaming-progress",
            "--replay-sse",
            "--run-ref",
            run_ref,
            "--after-sequence",
            "3",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "event: warning" in result.stdout
    assert "event: approval_wait" not in result.stdout
    assert '"readonly_replay":true' in result.stdout
    assert '"accepts_control_messages":false' in result.stdout
    assert '"raw_payload_included":false' in result.stdout
    assert "/" + "Users/" not in result.stdout
