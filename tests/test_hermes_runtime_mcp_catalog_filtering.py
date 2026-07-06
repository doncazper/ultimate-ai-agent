import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS,
    RUNTIME_MCP_CATALOG_FILTERING_CONTRACT_REF,
    RuntimeMcpCatalogFilteringReadModel,
    RuntimeMcpServerCatalogEntry,
    RuntimeMcpToolSlice,
    build_runtime_mcp_catalog_filtering_read_model,
)


client = TestClient(app)


def test_mcp_catalog_filtering_is_metadata_only_posture() -> None:
    read_model = build_runtime_mcp_catalog_filtering_read_model()

    assert read_model.schema_version == "runtime_mcp_catalog_filtering.v1"
    assert read_model.contract_ref == RUNTIME_MCP_CATALOG_FILTERING_CONTRACT_REF
    assert read_model.status == "metadata_catalog_filtering_posture"
    assert read_model.route_ref == "GET /api/runtime/mcp-catalog-filtering"
    assert read_model.cli_ref == "uaa runtime inspect-mcp-catalog-filtering"
    assert read_model.server_count == 3
    assert read_model.reviewed_metadata_count == 1
    assert read_model.review_required_count == 1
    assert read_model.activation_blocked_count == 1
    assert read_model.tool_slice_count == 6
    assert read_model.metadata_visible_tool_count == 1
    assert read_model.filtered_blocked_tool_count == 4
    assert read_model.grant_required_tool_count == 1
    assert read_model.metadata_catalog_visible is True
    assert read_model.tool_filter_contracts_visible is True
    assert read_model.blocked_activation_states_visible is True
    assert read_model.install_enabled is False
    assert read_model.subprocess_runtime_enabled is False
    assert read_model.oauth_login_enabled is False
    assert read_model.tool_invocation_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.raw_manifest_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_mcp_catalog_filtering_servers_and_tool_slices_deny_runtime_authority() -> None:
    read_model = build_runtime_mcp_catalog_filtering_read_model()
    states_by_server = {server.display_label: server.catalog_state for server in read_model.servers}

    assert states_by_server == {
        "Filesystem metadata server": "reviewed_metadata",
        "Browser research server": "activation_blocked",
        "CRM draft server": "review_required",
    }
    for server in read_model.servers:
        assert server.tool_count == len(server.tool_slices)
        assert server.install_enabled is False
        assert server.subprocess_runtime_enabled is False
        assert server.oauth_login_enabled is False
        assert server.tool_invocation_enabled is False
        assert server.connector_write_enabled is False
        assert server.raw_manifest_persisted is False
        assert set(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS).issubset(
            set(server.blocked_authority_refs)
        )
        for tool in server.tool_slices:
            assert tool.metadata_visible is True
            assert tool.invocation_enabled is False
            assert tool.connector_write_enabled is False
            assert tool.raw_schema_persisted is False
            assert tool.runtime_dispatch_enabled is False
            assert set(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS).issubset(
                set(tool.blocked_authority_refs)
            )


@pytest.mark.parametrize(
    "field",
    [
        "install_enabled",
        "subprocess_runtime_enabled",
        "oauth_login_enabled",
        "tool_invocation_enabled",
        "connector_write_enabled",
        "raw_manifest_persisted",
        "control_center_mints_authority",
    ],
)
def test_mcp_catalog_filtering_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_mcp_catalog_filtering_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MCP_CATALOG_AUTHORITY_DENIED"):
        RuntimeMcpCatalogFilteringReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "install_enabled",
        "subprocess_runtime_enabled",
        "oauth_login_enabled",
        "tool_invocation_enabled",
        "connector_write_enabled",
        "raw_manifest_persisted",
    ],
)
def test_mcp_catalog_filtering_server_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_mcp_catalog_filtering_read_model()
        .servers[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MCP_SERVER_AUTHORITY_DENIED"):
        RuntimeMcpServerCatalogEntry(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "invocation_enabled",
        "connector_write_enabled",
        "raw_schema_persisted",
        "runtime_dispatch_enabled",
    ],
)
def test_mcp_catalog_filtering_tool_slice_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_mcp_catalog_filtering_read_model()
        .servers[0]
        .tool_slices[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MCP_TOOL_AUTHORITY_DENIED"):
        RuntimeMcpToolSlice(**payload)


def test_mcp_catalog_filtering_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/mcp-catalog-filtering")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_mcp_catalog_filtering"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/mcp-catalog-filtering"
    assert data["server_count"] == 3
    assert data["tool_slice_count"] == 6
    assert data["install_enabled"] is False
    assert data["subprocess_runtime_enabled"] is False
    assert data["oauth_login_enabled"] is False
    assert data["tool_invocation_enabled"] is False
    assert data["connector_write_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_value" not in serialized
    assert "provider_payload_value" not in serialized
    assert "raw_manifest_payload" not in serialized


def test_mcp_catalog_filtering_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-mcp-catalog-filtering",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_mcp_catalog_filtering"]
    assert payload["safe_refs_only"] is True
    assert payload["metadata_only"] is True
    assert payload["install_performed"] is False
    assert payload["subprocess_runtime_performed"] is False
    assert payload["oauth_login_performed"] is False
    assert payload["tool_invocation_performed"] is False
    assert payload["connector_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/mcp-catalog-filtering"
    assert read_model["cli_ref"] == "uaa runtime inspect-mcp-catalog-filtering"
    assert read_model["server_count"] == 3
    assert read_model["tool_slice_count"] == 6
