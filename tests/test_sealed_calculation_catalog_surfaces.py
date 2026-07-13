from __future__ import annotations

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import (
    build_authority_lane_catalog_read_model,
    build_authority_state_read_model,
)


client = TestClient(app)


def test_manifest_declares_exact_arithmetic_and_keeps_broad_lanes_blocked() -> None:
    response = client.get("/api/manifest")
    assert response.status_code == 200
    manifest = response.json()

    for capability in (
        "sealed_deterministic_calculation_exact_mission_lane",
        "sealed_calculation_no_per_invocation_approval_after_exact_lease",
        "sealed_calculation_atomic_start_content_free_receipts",
    ):
        assert capability in manifest["capabilities_declared"]
    for capability in (
        "sealed_calculation_without_exact_mission_lease",
        "sealed_calculation_without_pinned_attested_backend",
        "sealed_calculation_general_python_or_codeact_execution",
        "sealed_calculation_shell_execution",
        "sealed_calculation_network_or_host_filesystem_access",
        "sealed_calculation_environment_credentials_or_package_access",
        "sealed_calculation_control_center_execution",
    ):
        assert capability in manifest["capabilities_blocked"]


def test_authority_catalogs_bind_exact_arithmetic_without_global_authority() -> None:
    authority_state = build_authority_state_read_model()
    mapping = next(
        item
        for item in authority_state.capability_mappings
        if item.lane_ref == "lane-ref:sealed-arithmetic-exact-lease"
    )
    assert mapping.domain == "workspace"
    assert mapping.capability == "execute"
    assert mapping.required_mode == "delegated_mission_autonomous_window"
    assert mapping.status == "implemented_exact_mission_lease_required"
    assert not mapping.unsupported_adapter_refs

    catalog = build_authority_lane_catalog_read_model().model_dump(mode="json")
    lane = next(
        item
        for item in catalog["entries"]
        if item["lane_id"] == "calculation.sealed_arithmetic"
    )
    assert lane["status"] == "implemented"
    assert lane["authority_domain"] == "workspace"
    assert lane["authority_capability"] == "execute"
    assert lane["required_mode"] == "delegated_mission_autonomous_window"
    assert lane["side_effect_class"] == "sandboxed_compute_read_only"
    assert lane["allowed_inputs_schema"]["network"] is False
    assert lane["allowed_inputs_schema"]["host_mounts"] is False
    assert "shell execution" in lane["denied_capabilities"]
    assert lane["idempotency_required"] is True
    assert lane["receipt_kind"] == "sealed_calculation_content_free_execution_receipt"
