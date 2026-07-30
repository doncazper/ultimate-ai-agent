import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    GOAL_RUNTIME_STATE_DIR_ENV,
    RUNTIME_RUN_EVENTS_AUTHORITY_MAPPING_REF,
    RUNTIME_RUN_EVENTS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_RUN_EVENTS_AUTHORITY_STATE_ROUTE_REF,
    RuntimeRunEventsReadModel,
    build_runtime_run_events_read_model,
)
from ultimate_ai_agent.core.runtime_gateway.storage import (
    RUNTIME_GATEWAY_STATE_DIR_ENV,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_goal_runtime_state(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        GOAL_RUNTIME_STATE_DIR_ENV,
        str(tmp_path / "goal-runtime"),
    )
    monkeypatch.setenv(
        RUNTIME_GATEWAY_STATE_DIR_ENV,
        str(tmp_path / "runtime-gateway"),
    )


def test_runtime_run_events_are_durable_local_replay_only() -> None:
    read_model = build_runtime_run_events_read_model()

    assert read_model.schema_version == "runtime_run_events.v1"
    assert read_model.status == "durable_local_replay"
    assert read_model.authority_state_route_ref == (
        RUNTIME_RUN_EVENTS_AUTHORITY_STATE_ROUTE_REF
    )
    assert read_model.authority_state_cli_ref == RUNTIME_RUN_EVENTS_AUTHORITY_STATE_CLI_REF
    assert read_model.authority_state_mapping_ref == (
        RUNTIME_RUN_EVENTS_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert "adapter-ref:runtime-run-create:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.uaa_controls_authority is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.no_runtime_control_routes_registered is True
    assert read_model.create_run_route_enabled is False
    assert read_model.stop_run_route_enabled is False
    assert read_model.approval_resolution_route_enabled is False
    assert read_model.live_event_stream_enabled is False
    assert read_model.proposal_count == 0
    assert read_model.approval_wait_count == 0
    assert read_model.completed_run_count == 0
    assert read_model.stream_count == 0
    assert read_model.retained_event_count == 0
    assert read_model.durable_event_source is True
    assert read_model.cursor_replay_supported is True
    assert read_model.bounded_retention_enabled is True
    assert read_model.goal_lifecycle.status == "durable_local_proof_backed"
    assert read_model.safe_refs_only is True
    assert read_model.raw_runtime_payload_persisted is False
    assert "blocked-authority:runtime-run-create-route" in (
        read_model.blocked_authority_refs
    )
    assert (
        "proof-ref:runtime-run-events:durable-hash-chain"
        in read_model.proof_refs
    )


def test_runtime_run_events_map_lifecycle_states_without_fake_completion() -> None:
    read_model = build_runtime_run_events_read_model()

    mapping_pairs = {
        (mapping.runtime_state, mapping.uaa_durable_run_state)
        for mapping in read_model.lifecycle_mappings
    }
    assert ("approval_wait", "approval_wait") in mapping_pairs
    assert ("completed", "completed") in mapping_pairs
    assert all(
        mapping.receipt_required_before_claim
        for mapping in read_model.lifecycle_mappings
    )
    assert read_model.run_proposals == []
    assert read_model.event_previews == []


def test_runtime_run_events_rejects_mutation_and_completion_claims() -> None:
    base = build_runtime_run_events_read_model().model_dump()
    base["stop_run_route_enabled"] = True

    with pytest.raises(ValueError, match="UNSAFE_AUTHORITY_DENIED"):
        RuntimeRunEventsReadModel(**base)

    fake_completion = build_runtime_run_events_read_model().model_dump()
    fake_completion["completed_run_count"] = 1
    with pytest.raises(ValueError, match="COMPLETION_COUNT_DRIFT"):
        RuntimeRunEventsReadModel(**fake_completion)

    authority_drift = build_runtime_run_events_read_model().model_dump()
    authority_drift["authority_state_mapping_ref"] = "lane-ref:wrong-runtime-run-events"

    with pytest.raises(ValueError, match="AUTHORITY_MAPPING_MISMATCH"):
        RuntimeRunEventsReadModel(**authority_drift)


def test_api_runtime_run_events_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/run-events")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_run_events.v1"
    assert data["route_ref"] == "GET /api/runtime/run-events"
    assert data["authority_state_route_ref"] == "GET /api/runtime/authority-state"
    assert data["authority_state_mapping_ref"] == (
        "lane-ref:runtime-run-events-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert "adapter-ref:runtime-run-live-event-stream:not-implemented" in (
        data["unsupported_adapter_refs"]
    )
    assert data["create_run_route_enabled"] is False
    assert data["stop_run_route_enabled"] is False
    assert data["approval_resolution_route_enabled"] is False
    assert data["completed_run_count"] == 0
    assert data["raw_runtime_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-run-events:phase-04"
    )


def test_cli_runtime_run_events_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-run-events",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_run_events"]
    assert payload["execution_performed"] is False
    assert payload["run_creation_performed"] is False
    assert payload["stop_performed"] is False
    assert payload["approval_resolution_performed"] is False
    assert payload["authority_state"]["mapping_ref"] == (
        "lane-ref:runtime-run-events-read-model"
    )
    assert payload["authority_state"]["decision_outcome"] == "allow"
    assert read_model["route_ref"] == "GET /api/runtime/run-events"
    assert read_model["cli_ref"] == "uaa runtime inspect-run-events"
    assert read_model["authority_state_cli_ref"] == (
        "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model["completed_run_count"] == 0
