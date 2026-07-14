from ultimate_ai_agent.core.control_center import (
    ControlCenterCapabilityStatus,
    ControlCenterSurface,
    build_control_center_manifest,
)


def test_control_center_manifest_is_read_only_preview_only_and_deterministic() -> None:
    manifest = build_control_center_manifest(baseline_version="0.16.0")

    surfaces = [surface.surface for surface in manifest.surfaces]
    assert surfaces == sorted(surfaces)
    assert ControlCenterSurface.dashboard in surfaces
    assert ControlCenterSurface.approvals in surfaces
    assert ControlCenterSurface.runtime_readiness in surfaces
    assert ControlCenterSurface.foundation_gate in surfaces
    assert ControlCenterSurface.macos_setup_assistant in surfaces
    assert ControlCenterSurface.settings_status in surfaces
    assert ControlCenterSurface.local_models in surfaces
    assert ControlCenterSurface.plugin_governance in surfaces

    statuses = {surface.surface: surface.status for surface in manifest.surfaces}
    assert statuses[ControlCenterSurface.dashboard] == ControlCenterCapabilityStatus.available_read_only
    assert statuses[ControlCenterSurface.approvals] == ControlCenterCapabilityStatus.preview_only
    assert statuses[ControlCenterSurface.macos_setup_assistant] == ControlCenterCapabilityStatus.preview_only
    assert statuses[ControlCenterSurface.settings_status] == ControlCenterCapabilityStatus.available_read_only
    assert statuses[ControlCenterSurface.local_models] == ControlCenterCapabilityStatus.available_read_only
    assert statuses[ControlCenterSurface.remote_workers] == ControlCenterCapabilityStatus.validation_only
    assert statuses[ControlCenterSurface.private_mesh] == ControlCenterCapabilityStatus.planned_disabled
    assert statuses[ControlCenterSurface.mobile_planning] == ControlCenterCapabilityStatus.planned_disabled
    assert statuses[ControlCenterSurface.plugin_governance] == ControlCenterCapabilityStatus.planned_disabled


def test_control_center_manifest_blocks_execution_capabilities() -> None:
    manifest = build_control_center_manifest(baseline_version="0.16.0")
    dump = manifest.model_dump_json().lower()

    for forbidden in [
        "runtime_execution",
        "model_execution",
        "provider_invocation",
        "remote_dispatch",
        "mobile_sensor_access",
        "plugin_enablement",
        "frontend_build_tooling",
    ]:
        assert forbidden in manifest.blocked_capabilities
    assert "execute capability" not in manifest.allowed_capabilities
    assert "setup_assistant_summary" in manifest.allowed_capabilities
    assert "/control-center/setup-assistant/summary" in manifest.route_refs
    assert "settings_status_summary" in manifest.allowed_capabilities
    assert "local_models_status_summary" in manifest.allowed_capabilities
    assert "/control-center/settings/status" in manifest.route_refs
    assert "/control-center/local-models/status" in manifest.route_refs
    assert "api_key='abcdefghijklmnop'" not in dump
    assert manifest.metadata["frontend_implemented"] is False
    assert manifest.metadata["production_control_center"] is False
    assert str(manifest.metadata["build_id"]).startswith("build-ref:uaa:")
    assert str(manifest.metadata["commit_ref"]).startswith("commit-ref:git:")
    assert manifest.metadata["storage_schema_version"] == "founder_loop_storage.v1"
    assert manifest.metadata["capability_profile_version"]
