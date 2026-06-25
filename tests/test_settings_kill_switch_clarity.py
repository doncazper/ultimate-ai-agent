from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.operational_status import (
    ControlCenterSettingsAuthorityPosture,
    ControlCenterSettingsFeatureFlagPosture,
    ControlCenterSettingsKillSwitchPosture,
    ControlCenterSettingsStatus,
    build_control_center_settings_status,
)


CANONICAL_KEYS = [
    "web",
    "providers",
    "connectors",
    "memory_context_use",
    "model_runtime",
    "local_model_lifecycle",
    "platform_capabilities",
]
SETTINGS_BLOCKED_AUTHORITIES = [
    "feature_flag_mutation",
    "kill_switch_mutation",
    "permission_mode_mutation",
    "model_identity_mutation",
    "runtime_lifecycle_mutation",
    "production_authority",
]
ROOT = Path(__file__).resolve().parents[1]


def test_settings_authority_posture_is_backend_owned_and_non_authorizing() -> None:
    status = build_control_center_settings_status()
    payload = status.model_dump(mode="json")

    assert payload["settings_authority_contract_ref"] == (
        "contract-ref:product-loop-011-settings-kill-switch-clarity:v1"
    )
    assert payload["settings_authority_verifier_ref"] == (
        "scripts/verify_product_loop_011_settings_kill_switch_clarity.py"
    )
    assert payload["runtime_capability_matrix_ref"] == "runtime_capability_matrix_m11"
    assert payload["platform_capability_snapshot_ref"] == (
        "platform-capability-snapshot:metadata-readiness"
    )
    assert [row["capability_key"] for row in payload["authority_postures"]] == (
        CANONICAL_KEYS
    )
    assert {"Blocked", "Degraded", "Partial", "Metadata only"} <= {
        row["state_label"] for row in payload["authority_postures"]
    }
    assert payload["callable_runtime_authority_enabled"] is False
    assert payload["provider_configuration_enabled"] is False
    assert payload["installer_behavior_enabled"] is False
    assert payload["settings_toggle_grants_authority"] is False
    assert payload["catalog_visibility_grants_authority"] is False
    assert payload["production_authority_enabled"] is False
    assert payload["blocked_authorities"] == SETTINGS_BLOCKED_AUTHORITIES

    for row in payload["authority_postures"]:
        assert row["callable_runtime_authority"] is False
        assert row["setting_toggle_grants_authority"] is False
        assert row["provider_configuration_enabled"] is False
        assert row["connector_write_enabled"] is False
        assert row["context_injection_enabled"] is False
        assert row["model_call_enabled"] is False
        assert row["local_lifecycle_enabled"] is False
        assert row["installer_behavior_enabled"] is False
        assert row["production_authority_enabled"] is False
        assert row["authority_from_visibility"] is False


def test_settings_kill_switch_and_feature_flags_remain_status_only() -> None:
    payload = build_control_center_settings_status().model_dump(mode="json")

    kill_switch = payload["kill_switch_postures"][0]
    assert kill_switch["state_label"] == "Not configured"
    assert kill_switch["execution_enabled"] is False
    assert kill_switch["revocation_execution_enabled"] is False
    assert kill_switch["approval_revocation_enabled"] is False
    assert kill_switch["authority_granted"] is False
    assert kill_switch["production_authority_enabled"] is False

    feature_flag = payload["feature_flag_postures"][0]
    assert feature_flag["state_label"] == "Metadata only"
    assert feature_flag["writable"] is False
    assert feature_flag["toggle_enabled"] is False
    assert feature_flag["runtime_activation_enabled"] is False
    assert feature_flag["authority_granted"] is False
    assert feature_flag["production_authority_enabled"] is False


def test_settings_posture_models_reject_authority_flags() -> None:
    with pytest.raises(ValidationError, match="CONTROL_CENTER_SETTINGS_AUTHORITY_ROW_DENIED"):
        ControlCenterSettingsAuthorityPosture(
            capability_key="web",
            label="Web",
            state_label="Blocked",
            posture_ref="settings-authority:web",
            source_refs=["GET /api/manifest"],
            safe_summary="Unsafe row.",
            blocked_authority_refs=["blocked-state:test"],
            next_safe_action="Review only.",
            callable_runtime_authority=True,
        )

    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_KILL_SWITCH_EXECUTION_DENIED",
    ):
        ControlCenterSettingsKillSwitchPosture(
            posture_ref="settings-kill-switch:test",
            label="Test",
            state_label="Blocked",
            safe_summary="Unsafe kill switch.",
            revocation_ref="revocation-ref:test",
            safe_disable_ref="safe-disable-ref:test",
            evidence_refs=["evidence-ref:test"],
            next_safe_action="Review only.",
            execution_enabled=True,
        )

    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_FEATURE_FLAG_WRITE_DENIED",
    ):
        ControlCenterSettingsFeatureFlagPosture(
            posture_ref="settings-feature-flag:test",
            label="Test",
            state_label="Metadata only",
            safe_summary="Unsafe feature flag.",
            owner_ref="owner-ref:test",
            evidence_refs=["evidence-ref:test"],
            next_safe_action="Review only.",
            toggle_enabled=True,
        )


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    [
        ("safe_summary", "raw prompt material"),
        ("safe_summary", "raw_response material"),
        ("safe_summary", "raw_provider_payload material"),
        ("safe_summary", "username: private actor"),
        ("safe_summary", "hostname: workstation"),
        ("source_refs", ["/Users/example/private"]),
    ],
)
def test_settings_authority_rows_reject_private_or_raw_text(
    field_name: str,
    unsafe_value: str | list[str],
) -> None:
    row = {
        "capability_key": "web",
        "label": "Web",
        "state_label": "Blocked",
        "posture_ref": "settings-authority:web",
        "source_refs": ["GET /api/manifest"],
        "safe_summary": "Safe refs only.",
        "blocked_authority_refs": ["blocked-state:test"],
        "next_safe_action": "Review only.",
    }
    row[field_name] = unsafe_value

    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_AUTHORITY_ROW_PRIVATE_OR_RAW_VALUE_REJECTED",
    ):
        ControlCenterSettingsAuthorityPosture(**row)


def test_settings_related_postures_reject_private_or_raw_text() -> None:
    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_KILL_SWITCH_PRIVATE_OR_RAW_VALUE_REJECTED",
    ):
        ControlCenterSettingsKillSwitchPosture(
            posture_ref="settings-kill-switch:test",
            label="Test",
            state_label="Blocked",
            safe_summary="raw log material",
            revocation_ref="revocation-ref:test",
            safe_disable_ref="safe-disable-ref:test",
            evidence_refs=["evidence-ref:test"],
            next_safe_action="Review only.",
        )

    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_FEATURE_FLAG_PRIVATE_OR_RAW_VALUE_REJECTED",
    ):
        ControlCenterSettingsFeatureFlagPosture(
            posture_ref="settings-feature-flag:test",
            label="Test",
            state_label="Metadata only",
            safe_summary="Safe refs only.",
            owner_ref="owner-ref:test",
            evidence_refs=["C:\\Users\\example\\private"],
            next_safe_action="Review only.",
        )


def test_settings_status_rejects_private_or_raw_text() -> None:
    payload = build_control_center_settings_status().model_dump(mode="json")
    payload["review_proposals"] = ["hostname: workstation"]

    with pytest.raises(
        ValidationError,
        match="CONTROL_CENTER_SETTINGS_STATUS_PRIVATE_OR_RAW_VALUE_REJECTED",
    ):
        ControlCenterSettingsStatus(**payload)


def test_settings_authority_cli_inspection_matches_backend_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/inspect_settings_authority_posture.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["ok"] is True
    assert payload["contract_ref"] == (
        "contract-ref:product-loop-011-settings-kill-switch-clarity:v1"
    )
    assert [row["capability_key"] for row in payload["authority_postures"]] == (
        CANONICAL_KEYS
    )
    assert all(value is False for value in payload["authority_denied"].values())


def test_settings_manifest_currentness_refs_are_aligned() -> None:
    operational = json.loads(
        (ROOT / "docs/control_center/operational_maturity_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    settings_entry = next(
        entry for entry in operational["modules"] if entry["module_id"] == "settings"
    )
    assert settings_entry["blocked_authorities"] == SETTINGS_BLOCKED_AUTHORITIES
    assert "scripts/inspect_settings_authority_posture.py" in settings_entry[
        "cli_or_script_refs"
    ]
    assert "scripts/verify_product_loop_011_settings_kill_switch_clarity.py" in (
        settings_entry["verifier_refs"]
    )
    assert "tests/test_settings_kill_switch_clarity.py" in settings_entry["test_refs"]

    route_status_text = (
        ROOT / "docs/control_center/route_status_manifest.json"
    ).read_text(encoding="utf-8")
    assert "provider-configuration" in route_status_text
    assert "kill-switch-execution" in route_status_text
    assert "revocation-execution" in route_status_text

    release_surface_text = (
        ROOT / "docs/control_center/release_surface_manifest.json"
    ).read_text(encoding="utf-8")
    assert "docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md" in (
        release_surface_text
    )
    assert "connector_runtime" in release_surface_text
    assert "public_beta_claim" in release_surface_text
    assert "model_calls" in release_surface_text
    assert "live_web" in release_surface_text
