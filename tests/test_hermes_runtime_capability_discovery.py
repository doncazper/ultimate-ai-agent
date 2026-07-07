import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeCapabilityDiscoveryReadModel,
    RuntimeCapabilityGroupKind,
    RuntimeToolsetCapabilityPosture,
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
    assert read_model.toolset_posture.schema_version == (
        "runtime_toolset_capability_posture.v1"
    )
    assert read_model.toolset_posture.uaa_allowed_execution_count == 0
    assert read_model.toolset_posture.live_tool_invocation_enabled is False
    assert read_model.toolset_posture.toolset_config_mutation_enabled is False
    assert read_model.toolset_posture.hermes_toolset_enablement_enabled is False
    assert read_model.toolset_posture.raw_tool_payload_persisted is False
    assert "AuthorityLease domain/capability scope" in read_model.safe_summary
    assert "exact lanes graduate" not in read_model.safe_summary
    assert "proof-ref:hermes-runtime-adoption:phase-09:toolsets" in (
        read_model.toolset_posture.proof_refs
    )
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


def test_runtime_toolset_posture_maps_support_to_uaa_allowance() -> None:
    read_model = build_runtime_capability_discovery_read_model()
    posture = read_model.toolset_posture

    assert posture.toolset_count == 8
    assert posture.runtime_supported_count == 4
    assert posture.enabled_read_only_count == 1
    assert posture.configured_metadata_only_count == 1
    assert posture.approval_required_future_count == 2
    assert posture.blocked_count == 3
    assert posture.unsupported_count == 1
    assert posture.uaa_allowed_execution_count == 0
    assert "blocked-authority:runtime-toolset-invocation" in (
        posture.blocked_authority_refs
    )

    allowance_statuses = {record.uaa_allowance_status for record in posture.records}
    assert allowance_statuses == {
        "enabled_read_only",
        "configured_metadata_only",
        "approval_required_future_lane",
        "blocked",
        "unsupported",
    }
    high_authority_records = [
        record
        for record in posture.records
        if record.side_effect_class == "high_authority"
    ]
    assert high_authority_records
    for record in posture.records:
        assert record.uaa_allows_execution is False
        assert record.tool_invocation_enabled is False
        assert record.toolset_config_mutation_enabled is False
        assert record.hermes_toolset_enablement_enabled is False
        assert record.raw_tool_payload_persisted is False
        assert record.blocked_authority_refs
        assert record.next_safe_action_refs
    for record in high_authority_records:
        assert "blocked-authority:runtime-high-authority-toolset" in (
            record.blocked_authority_refs
        )


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


def test_runtime_toolset_posture_rejects_execution_claims() -> None:
    posture = build_runtime_capability_discovery_read_model().toolset_posture
    base = posture.model_dump()
    base["live_tool_invocation_enabled"] = True

    with pytest.raises(ValueError, match="AUTHORITY_DENIED"):
        RuntimeToolsetCapabilityPosture(**base)

    base = posture.model_dump()
    base["records"][0]["uaa_allows_execution"] = True
    base["uaa_allowed_execution_count"] = 1

    with pytest.raises(ValueError, match="EXECUTION_DENIED"):
        RuntimeToolsetCapabilityPosture(**base)


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
    assert data["toolset_posture"]["uaa_allowed_execution_count"] == 0
    assert data["toolset_posture"]["live_tool_invocation_enabled"] is False
    assert data["toolset_posture"]["toolset_config_mutation_enabled"] is False
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
    assert read_model["toolset_posture"]["toolset_count"] == 8
    assert read_model["toolset_posture"]["uaa_allowed_execution_count"] == 0
    assert read_model["toolset_posture"]["live_tool_invocation_enabled"] is False
