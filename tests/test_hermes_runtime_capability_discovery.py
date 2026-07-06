import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeCapabilityDiscoveryReadModel,
    RuntimeCapabilityGroupKind,
    build_runtime_capability_discovery_read_model,
)


client = TestClient(app)


def test_runtime_capability_discovery_is_static_readiness_only() -> None:
    read_model = build_runtime_capability_discovery_read_model()

    assert read_model.schema_version == "runtime_capability_discovery.v1"
    assert read_model.status == "static_readiness_only"
    assert read_model.runtime_reachable is False
    assert read_model.live_discovery_performed is False
    assert read_model.stale is True
    assert read_model.stale_or_unreachable_degrades_to_blocked is True
    assert read_model.runtime_supported_cannot_grant_uaa_permission is True
    assert read_model.uaa_controls_authority is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.uaa_authorized_capability_count == 0
    assert read_model.runtime_supported_capability_count == 8
    assert read_model.safe_refs_only is True
    assert read_model.raw_provider_payload_persisted is False
    assert read_model.raw_runtime_payload_persisted is False
    assert "blocked-authority:runtime-capability-cannot-grant-permission" in (
        read_model.blocked_authority_refs
    )
    assert "proof-ref:runtime-capability-discovery:static-snapshot-hash" in (
        read_model.proof_refs
    )


def test_runtime_capability_discovery_includes_required_taxonomy() -> None:
    read_model = build_runtime_capability_discovery_read_model()

    assert {group.group_kind for group in read_model.capability_groups} == {
        kind.value for kind in RuntimeCapabilityGroupKind
    }
    for group in read_model.capability_groups:
        assert group.uaa_authorized_for_execution is False
        assert group.stale_or_unreachable_degrades_to_blocked is True
        assert group.capability_refs
        assert group.blocked_authority_refs
        assert group.next_safe_action_refs


def test_runtime_capability_discovery_rejects_permission_grant() -> None:
    base = build_runtime_capability_discovery_read_model().model_dump()
    base["runtime_supported_cannot_grant_uaa_permission"] = False

    with pytest.raises(ValueError, match="PERMISSION_GRANT_DENIED"):
        RuntimeCapabilityDiscoveryReadModel(**base)


def test_runtime_capability_discovery_rejects_live_discovery_claim() -> None:
    base = build_runtime_capability_discovery_read_model().model_dump()
    base["live_discovery_performed"] = True

    with pytest.raises(ValueError, match="LIVE_CALL_DENIED"):
        RuntimeCapabilityDiscoveryReadModel(**base)


def test_api_runtime_capability_discovery_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/capability-discovery")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_capability_discovery.v1"
    assert data["runtime_reachable"] is False
    assert data["live_discovery_performed"] is False
    assert data["uaa_authorized_capability_count"] == 0
    assert data["raw_runtime_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-capability-discovery:phase-02"
    )


def test_cli_runtime_capability_discovery_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-capability-discovery",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_capability_discovery"]
    assert payload["execution_performed"] is False
    assert payload["live_discovery_performed"] is False
    assert payload["runtime_permission_granted"] is False
    assert read_model["route_ref"] == "GET /api/runtime/capability-discovery"
    assert read_model["cli_ref"] == "uaa runtime inspect-capability-discovery"
    assert read_model["uaa_authorized_capability_count"] == 0
