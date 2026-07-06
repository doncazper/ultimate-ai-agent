import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeToolRegistryAvailabilityReadModel,
    build_runtime_tool_registry_availability_read_model,
)


client = TestClient(app)


def test_runtime_tool_registry_is_read_only_availability() -> None:
    read_model = build_runtime_tool_registry_availability_read_model()

    assert read_model.schema_version == "runtime_tool_registry_availability.v1"
    assert read_model.status == "read_only_tool_registry_availability"
    assert read_model.route_ref == "GET /api/runtime/tool-registry"
    assert read_model.cli_ref == "uaa runtime inspect-tool-registry"
    assert read_model.tool_count == 12
    assert read_model.uaa_native_count == 4
    assert read_model.delegated_reference_count == 8
    assert read_model.preview_available_count == 4
    assert read_model.invocation_enabled_count == 0
    assert read_model.tool_invocation_enabled is False
    assert read_model.remote_discovery_enabled is False
    assert read_model.plugin_import_enabled is False
    assert read_model.connector_write_activation_enabled is False
    assert read_model.raw_tool_payload_persisted is False
    assert read_model.production_authority_enabled is False
    assert "proof-ref:hermes-runtime-adoption:phase-10:tool-registry" in (
        read_model.proof_refs
    )
    assert "blocked-authority:runtime-tool-registry-invocation" in (
        read_model.blocked_authority_refs
    )


def test_runtime_tool_registry_entries_have_availability_and_blockers() -> None:
    read_model = build_runtime_tool_registry_availability_read_model()

    availability_statuses = {entry.availability_status for entry in read_model.entries}
    assert availability_statuses == {
        "available_metadata_only",
        "configured_disabled",
        "approval_required_future_lane",
        "blocked",
        "unsupported",
    }
    high_authority_entries = [
        entry
        for entry in read_model.entries
        if entry.authority_class == "blocked_high_authority"
    ]
    assert high_authority_entries
    for entry in read_model.entries:
        assert entry.uaa_allows_invocation is False
        assert entry.execution_enabled is False
        assert entry.remote_discovery_performed is False
        assert entry.live_web_fetch_performed is False
        assert entry.provider_model_call_performed is False
        assert entry.plugin_import_enabled is False
        assert entry.connector_write_activation_enabled is False
        assert entry.raw_tool_payload_persisted is False
        assert entry.blocked_authority_refs
        assert entry.next_safe_action_refs
    for entry in high_authority_entries:
        assert "blocked-authority:runtime-tool-registry-high-authority" in (
            entry.blocked_authority_refs
        )


def test_runtime_tool_registry_rejects_invocation_claims() -> None:
    base = build_runtime_tool_registry_availability_read_model().model_dump()
    base["tool_invocation_enabled"] = True

    with pytest.raises(ValueError, match="AUTHORITY_DENIED"):
        RuntimeToolRegistryAvailabilityReadModel(**base)

    base = build_runtime_tool_registry_availability_read_model().model_dump()
    base["entries"][0]["uaa_allows_invocation"] = True
    base["invocation_enabled_count"] = 1

    with pytest.raises(ValueError, match="INVOCATION_DENIED"):
        RuntimeToolRegistryAvailabilityReadModel(**base)


def test_api_runtime_tool_registry_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/tool-registry")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_tool_registry_availability.v1"
    assert data["tool_count"] == 12
    assert data["invocation_enabled_count"] == 0
    assert data["tool_invocation_enabled"] is False
    assert data["remote_discovery_enabled"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-tool-registry:phase-10"
    )


def test_cli_runtime_tool_registry_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-tool-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_tool_registry"]
    assert payload["execution_performed"] is False
    assert payload["tool_invocation_performed"] is False
    assert payload["remote_discovery_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/tool-registry"
    assert read_model["cli_ref"] == "uaa runtime inspect-tool-registry"
    assert read_model["invocation_enabled_count"] == 0
