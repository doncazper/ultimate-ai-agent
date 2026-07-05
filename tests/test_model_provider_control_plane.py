from __future__ import annotations

import json
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.providers.control_plane import (
    MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF,
    build_model_provider_control_plane_read_model,
)


LOCAL_TEST_BEARER = "model-provider-control-plane-local-bearer"


def test_model_provider_control_plane_unifies_governed_runtime_posture() -> None:
    read_model = build_model_provider_control_plane_read_model()
    payload = read_model.model_dump(mode="json")

    assert read_model.schema_version == "model_provider_control_plane.v1"
    assert read_model.route_ref == MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    assert read_model.backend_owned is True
    assert read_model.read_only is True
    assert read_model.safe_refs_only is True
    assert read_model.status == "governed_control_plane_wired"
    assert read_model.authority.exact_tiny_provider_lane_available is True
    assert read_model.authority.exact_credential_validation_lane_available is True
    assert read_model.authority.local_llama_cpp_gateway_available is True
    assert read_model.authority.provider_sdk_call_enabled is False
    assert read_model.authority.live_provider_network_call_enabled_by_default is False
    assert len(read_model.provider_adapters) >= 2
    assert all(adapter.receipt_store_required_before_network for adapter in read_model.provider_adapters)
    assert read_model.network_allowlists.default_network_denied is True
    assert read_model.network_allowlists.endpoint_refs
    assert read_model.model_metadata_discovery.provider_model_refs
    assert read_model.model_metadata_discovery.live_provider_model_discovery_enabled is False
    assert read_model.cost_hooks.unknown_paid_cost_blocks is True
    assert read_model.local_llama_cpp_lifecycle.process_start_performed_by_read_model is False
    assert read_model.local_llama_cpp_lifecycle.model_call_performed_by_read_model is False
    assert read_model.router_traces[0].status == "trace_only_no_execution"
    assert read_model.router_traces[0].model_execution_performed is False
    assert read_model.router_traces[0].provider_execution_performed is False
    assert read_model.router_traces[0].reason_codes
    assert "raw prompt" not in json.dumps(payload).lower()
    assert "raw response" not in json.dumps(payload).lower()
    assert "provider payload persisted" not in json.dumps(payload).lower()


def test_model_provider_control_plane_route_is_protected_read_only_and_safe(
    monkeypatch,
) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = TestClient(app)

    response = client.get(
        "/control-center/providers/runtime-control-plane",
        headers={"Authorization": f"Bearer {LOCAL_TEST_BEARER}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_providers_runtime_control_plane"
    assert "raw_credentials_omitted" in body["redactions_applied"]
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["authority"]["provider_sdk_call_enabled"] is False
    assert data["authority"]["live_provider_network_call_enabled_by_default"] is False
    assert data["secret_status"]["secret_material_visible"] is False
    assert data["network_allowlists"]["endpoint_refs"]
    assert data["local_llama_cpp_lifecycle"]["process_start_performed_by_read_model"] is False
    assert data["router_traces"][0]["model_execution_performed"] is False


def test_model_provider_control_plane_route_manifest_posture() -> None:
    manifest = build_api_manifest(app)
    route = next(
        route
        for route in manifest.routes
        if route.path == "/control-center/providers/runtime-control-plane"
        and route.method == "GET"
    )

    assert route.operation_id == "get_control_center_providers_runtime_control_plane"
    assert route.side_effect_class == "validation_only"
    assert route.route_classification == "local_readonly"
    assert route.approval_posture == "not_required_for_route_classification"
    assert "control_center_model_provider_control_plane_read_model" in (
        manifest.capabilities_declared
    )
    assert "control_center_model_provider_control_plane_as_runtime_authority" in (
        manifest.capabilities_blocked
    )


def test_model_provider_control_plane_cli_uses_same_safe_schema() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "model_provider_control_plane.v1"
    assert payload["backend_owned"] is True
    assert payload["read_only"] is True
    assert payload["authority"]["provider_sdk_call_enabled"] is False
    assert payload["authority"]["local_llama_cpp_lifecycle_contract_available"] is True
    assert len(payload["provider_adapters"]) >= 2
    assert payload["router_traces"][0]["status"] == "trace_only_no_execution"
