import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeRunEventsReadModel,
    RuntimeRunProposalReadModel,
    build_runtime_run_events_read_model,
)


client = TestClient(app)


def test_runtime_run_events_are_proposal_read_model_only() -> None:
    read_model = build_runtime_run_events_read_model()

    assert read_model.schema_version == "runtime_run_events.v1"
    assert read_model.status == "proposal_read_model_only"
    assert read_model.uaa_controls_authority is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.no_mutation_routes_registered is True
    assert read_model.create_run_route_enabled is False
    assert read_model.stop_run_route_enabled is False
    assert read_model.approval_resolution_route_enabled is False
    assert read_model.live_event_stream_enabled is False
    assert read_model.proposal_count == 1
    assert read_model.approval_wait_count == 1
    assert read_model.completed_run_count == 0
    assert read_model.safe_refs_only is True
    assert read_model.raw_runtime_payload_persisted is False
    assert "blocked-authority:runtime-run-create-route" in (
        read_model.blocked_authority_refs
    )
    assert "proof-ref:runtime-run-events:no-mutation-routes" in read_model.proof_refs


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
    assert all(
        proposal.uaa_durable_run_state != "completed"
        for proposal in read_model.run_proposals
    )
    assert all(
        proposal.create_run_enabled is False
        and proposal.stop_run_enabled is False
        and proposal.approval_resolution_enabled is False
        for proposal in read_model.run_proposals
    )


def test_runtime_run_events_rejects_mutation_and_completion_claims() -> None:
    base = build_runtime_run_events_read_model().model_dump()
    base["stop_run_route_enabled"] = True

    with pytest.raises(ValueError, match="UNSAFE_AUTHORITY_DENIED"):
        RuntimeRunEventsReadModel(**base)

    proposal = build_runtime_run_events_read_model().run_proposals[0].model_dump()
    proposal["uaa_durable_run_state"] = "completed"

    with pytest.raises(ValueError, match="FAKE_COMPLETION_DENIED"):
        RuntimeRunProposalReadModel(**proposal)


def test_api_runtime_run_events_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/run-events")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_run_events.v1"
    assert data["route_ref"] == "GET /api/runtime/run-events"
    assert data["create_run_route_enabled"] is False
    assert data["stop_run_route_enabled"] is False
    assert data["approval_resolution_route_enabled"] is False
    assert data["completed_run_count"] == 0
    assert data["raw_runtime_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-run-events:phase-03"
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
    assert read_model["route_ref"] == "GET /api/runtime/run-events"
    assert read_model["cli_ref"] == "uaa runtime inspect-run-events"
    assert read_model["completed_run_count"] == 0
