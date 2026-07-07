import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS,
    RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF,
    RuntimePluginMetadataPostureReadModel,
    RuntimePluginMetadataSurface,
    build_runtime_plugin_metadata_posture_read_model,
)


client = TestClient(app)


def test_plugin_metadata_is_contract_only() -> None:
    read_model = build_runtime_plugin_metadata_posture_read_model()

    assert read_model.schema_version == "runtime_plugin_metadata_posture.v1"
    assert read_model.status == "metadata_contract_only"
    assert read_model.route_ref == RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF
    assert read_model.cli_ref == "uaa runtime inspect-plugin-metadata-posture"
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_route_ref == "GET /api/runtime/authority-state"
    assert (
        read_model.authority_state_cli_ref
        == "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_status == "implemented_authority_bound_read_model"
    assert "reason-ref:authority:active-lease-grants-domain-capability" in (
        read_model.authority_state_reason_refs
    )
    assert "adapter-ref:plugin-runtime-import:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.surface_count == 7
    assert read_model.blocked_surface_count == 7
    assert read_model.runtime_import_enabled is False
    assert read_model.hook_execution_enabled is False
    assert read_model.package_install_enabled is False
    assert read_model.marketplace_content_execution_enabled is False
    assert read_model.plugin_code_execution_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.raw_manifest_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_plugin_metadata_route_returns_authority_bound_read_model() -> None:
    response = client.get("/api/runtime/plugin-metadata-posture")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_plugin_metadata_posture"
    data = body["data"]
    assert data["schema_version"] == "runtime_plugin_metadata_posture.v1"
    assert data["route_ref"] == "GET /api/runtime/plugin-metadata-posture"
    assert (
        data["authority_state_mapping_ref"]
        == "lane-ref:runtime-plugin-metadata-posture-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["surface_count"] == 7
    assert data["blocked_surface_count"] == 7
    assert data["runtime_import_enabled"] is False
    assert data["hook_execution_enabled"] is False
    assert data["package_install_enabled"] is False
    assert data["plugin_code_execution_enabled"] is False


def test_plugin_metadata_surfaces_are_blocked() -> None:
    read_model = build_runtime_plugin_metadata_posture_read_model()
    surface_kinds = {surface.surface_kind for surface in read_model.surfaces}

    assert surface_kinds == {
        "adapter",
        "hook",
        "tool",
        "memory_provider",
        "context_engine",
        "ui_extension",
        "skill_bundle",
    }
    for surface in read_model.surfaces:
        assert surface.status == "blocked_until_grant"
        assert surface.surface_ref.startswith("plugin-surface-ref:")
        assert surface.reviewed_manifest_ref.startswith("reviewed-manifest-ref:")
        assert surface.static_scan_ref.startswith("static-scan-ref:")
        assert surface.sandbox_ref.startswith("sandbox-ref:")
        assert surface.activation_grant_ref.startswith("activation-grant-ref:")
        assert surface.rollback_ref.startswith("rollback-ref:")
        assert surface.safe_disable_ref.startswith("safe-disable-ref:")
        assert surface.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert surface.runtime_import_enabled is False
        assert surface.hook_execution_enabled is False
        assert surface.package_install_enabled is False
        assert surface.marketplace_content_execution_enabled is False
        assert surface.plugin_code_execution_enabled is False
        assert surface.connector_write_enabled is False
        assert surface.provider_call_enabled is False
        assert surface.shell_execution_enabled is False
        assert surface.raw_manifest_persisted is False
        assert surface.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "runtime_import_enabled",
        "hook_execution_enabled",
        "package_install_enabled",
        "marketplace_content_execution_enabled",
        "plugin_code_execution_enabled",
        "connector_write_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "raw_manifest_persisted",
        "control_center_mints_authority",
    ],
)
def test_plugin_metadata_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_plugin_metadata_posture_read_model().model_dump(
        mode="json"
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_PLUGIN_METADATA_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimePluginMetadataPostureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "runtime_import_enabled",
        "hook_execution_enabled",
        "package_install_enabled",
        "marketplace_content_execution_enabled",
        "plugin_code_execution_enabled",
        "connector_write_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "raw_manifest_persisted",
        "control_center_mints_authority",
    ],
)
def test_plugin_metadata_surface_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_plugin_metadata_posture_read_model()
        .surfaces[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_PLUGIN_METADATA_SURFACE_AUTHORITY_DENIED",
    ):
        RuntimePluginMetadataSurface(**payload)


def test_plugin_metadata_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-plugin-metadata-posture",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "raw_manifest_value" not in result.stdout
    assert "package_payload_value" not in result.stdout
    payload = json.loads(result.stdout)
    read_model = payload["runtime_plugin_metadata_posture"]
    assert payload["runtime_import_performed"] is False
    assert payload["hook_execution_performed"] is False
    assert payload["package_install_performed"] is False
    assert payload["plugin_code_execution_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/plugin-metadata-posture"
    assert (
        read_model["authority_state_mapping_ref"]
        == "lane-ref:runtime-plugin-metadata-posture-read-model"
    )
    assert read_model["authority_state_decision_outcome"] == "allow"
    assert read_model["surface_count"] == 7
    assert read_model["blocked_surface_count"] == 7
