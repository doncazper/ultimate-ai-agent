#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.control_center.operational_status import (
    SETTINGS_KILL_SWITCH_CLARITY_CONTRACT_REF,
    ControlCenterSettingsAuthorityPosture,
    ControlCenterSettingsFeatureFlagPosture,
    ControlCenterSettingsKillSwitchPosture,
    ControlCenterSettingsStatus,
    build_control_center_settings_status,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KEYS = [
    "web",
    "providers",
    "connectors",
    "memory_context_use",
    "model_runtime",
    "local_model_lifecycle",
    "platform_capabilities",
]
DENIED_STATUS_FLAGS = [
    "callable_runtime_authority_enabled",
    "provider_configuration_enabled",
    "installer_behavior_enabled",
    "settings_toggle_grants_authority",
    "catalog_visibility_grants_authority",
    "production_authority_enabled",
]
DENIED_ROW_FLAGS = [
    "callable_runtime_authority",
    "setting_toggle_grants_authority",
    "provider_configuration_enabled",
    "connector_write_enabled",
    "context_injection_enabled",
    "model_call_enabled",
    "local_lifecycle_enabled",
    "installer_behavior_enabled",
    "production_authority_enabled",
    "authority_from_visibility",
]
DOC_PATHS = [
    ROOT / "docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md",
    ROOT / "docs/DOCUMENTATION_INDEX.md",
    ROOT / "docs/kanban/current_board.md",
    ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
    ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
]


def _fail(message: str) -> None:
    raise SystemExit(f"Product Loop 011 verifier failed: {message}")


def _read(path: Path) -> str:
    if not path.exists():
        _fail(f"missing required file {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _normalized_text(path: Path) -> str:
    return " ".join(_read(path).split())


def _assert_backend_contract() -> dict[str, Any]:
    status = build_control_center_settings_status()
    payload = status.model_dump(mode="json")
    if payload["settings_authority_contract_ref"] != SETTINGS_KILL_SWITCH_CLARITY_CONTRACT_REF:
        _fail("settings authority contract ref drifted")
    keys = [row["capability_key"] for row in payload["authority_postures"]]
    if keys != CANONICAL_KEYS:
        _fail(f"canonical Settings authority keys drifted: {keys}")
    labels = {row["state_label"] for row in payload["authority_postures"]}
    if not {"Blocked", "Degraded", "Partial", "Metadata only"}.issubset(labels):
        _fail("Settings posture labels must include blocked/degraded/partial/metadata-only")
    for flag in DENIED_STATUS_FLAGS:
        if payload[flag] is not False:
            _fail(f"settings status flag must remain false: {flag}")
    for row in payload["authority_postures"]:
        for flag in DENIED_ROW_FLAGS:
            if row[flag] is not False:
                _fail(f"settings authority row flag must remain false: {flag}")
    kill_switch = payload["kill_switch_postures"][0]
    for flag in [
        "execution_enabled",
        "revocation_execution_enabled",
        "approval_revocation_enabled",
        "authority_granted",
        "production_authority_enabled",
    ]:
        if kill_switch[flag] is not False:
            _fail(f"kill-switch posture flag must remain false: {flag}")
    feature_flag = payload["feature_flag_postures"][0]
    for flag in [
        "writable",
        "toggle_enabled",
        "runtime_activation_enabled",
        "authority_granted",
        "production_authority_enabled",
    ]:
        if feature_flag[flag] is not False:
            _fail(f"feature-flag posture flag must remain false: {flag}")
    _assert_model_rejects_authority()
    return payload


def _assert_model_rejects_authority() -> None:
    try:
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
    except ValueError:
        pass
    else:
        _fail("authority posture accepted callable runtime authority")

    try:
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
    except ValueError:
        pass
    else:
        _fail("kill-switch posture accepted execution authority")

    try:
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
    except ValueError:
        pass
    else:
        _fail("feature-flag posture accepted toggle authority")

    _assert_model_rejects_private_or_raw_content()


def _assert_model_rejects_private_or_raw_content() -> None:
    authority_row = {
        "capability_key": "web",
        "label": "Web",
        "state_label": "Blocked",
        "posture_ref": "settings-authority:web",
        "source_refs": ["GET /api/manifest"],
        "safe_summary": "Safe refs only.",
        "blocked_authority_refs": ["blocked-state:test"],
        "next_safe_action": "Review only.",
    }
    unsafe_authority_values = [
        ("safe_summary", "raw prompt material"),
        ("safe_summary", "raw_response material"),
        ("safe_summary", "raw_provider_payload material"),
        ("safe_summary", "username: private actor"),
        ("safe_summary", "hostname: workstation"),
        ("source_refs", ["/Users/example/private"]),
    ]
    for field_name, unsafe_value in unsafe_authority_values:
        row = dict(authority_row)
        row[field_name] = unsafe_value
        try:
            ControlCenterSettingsAuthorityPosture(**row)
        except ValueError:
            pass
        else:
            _fail(f"authority posture accepted unsafe Settings value: {unsafe_value}")

    try:
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
    except ValueError:
        pass
    else:
        _fail("kill-switch posture accepted raw log material")

    try:
        ControlCenterSettingsFeatureFlagPosture(
            posture_ref="settings-feature-flag:test",
            label="Test",
            state_label="Metadata only",
            safe_summary="Safe refs only.",
            owner_ref="owner-ref:test",
            evidence_refs=["C:\\Users\\example\\private"],
            next_safe_action="Review only.",
        )
    except ValueError:
        pass
    else:
        _fail("feature-flag posture accepted a raw path")

    payload = build_control_center_settings_status().model_dump(mode="json")
    payload["review_proposals"] = ["hostname: workstation"]
    try:
        ControlCenterSettingsStatus(**payload)
    except ValueError:
        pass
    else:
        _fail("settings status accepted hostname material")


def _assert_cli_contract(expected: dict[str, Any]) -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/inspect_settings_authority_posture.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    payload = json.loads(completed.stdout)
    if payload["contract_ref"] != expected["settings_authority_contract_ref"]:
        _fail("CLI contract ref does not match backend settings status")
    if [row["capability_key"] for row in payload["authority_postures"]] != CANONICAL_KEYS:
        _fail("CLI authority posture keys drifted")
    if any(payload["authority_denied"].values()):
        _fail("CLI reported an enabled denied authority flag")


def _assert_static_ui() -> None:
    component = _read(ROOT / "apps/control-center/src/components/OperatorFlowPanels.tsx")
    tests = _read(ROOT / "apps/control-center/src/App.test.tsx")
    required_component_snippets = [
        "Settings authority posture labels",
        "Settings kill-switch and feature-flag posture",
        "settingsStatusRecord.authority_postures",
        "settingsStatusRecord.kill_switch_postures",
        "settingsStatusRecord.feature_flag_postures",
        "Settings authority posture unavailable",
    ]
    for snippet in required_component_snippets:
        if snippet not in component:
            _fail(f"Settings UI missing snippet: {snippet}")
    required_test_snippets = [
        "Web",
        "Providers",
        "Connectors",
        "Memory context use",
        "Model runtime",
        "Local model lifecycle",
        "Platform capabilities",
        "Degraded",
        "Partial",
        "Metadata only",
        "configure provider",
        "inject context",
    ]
    for snippet in required_test_snippets:
        if snippet not in tests:
            _fail(f"Settings UI tests missing snippet: {snippet}")


def _assert_manifests() -> None:
    operational = _read(ROOT / "docs/control_center/operational_maturity_manifest.json")
    route_status = _read(ROOT / "docs/control_center/route_status_manifest.json")
    release_surface = _read(ROOT / "docs/control_center/release_surface_manifest.json")
    operational_required = [
        "scripts/inspect_settings_authority_posture.py",
        "scripts/verify_product_loop_011_settings_kill_switch_clarity.py",
        "tests/test_settings_kill_switch_clarity.py",
        "runtime_lifecycle_mutation",
    ]
    for snippet in operational_required:
        if snippet not in operational:
            _fail(f"operational maturity manifest missing snippet: {snippet}")
    route_required = [
        "blocked/degraded/partial authority posture labels",
        "provider-configuration",
        "kill-switch-execution",
        "revocation-execution",
        "runtime-lifecycle-mutation",
    ]
    for snippet in route_required:
        if snippet not in route_status:
            _fail(f"route status manifest missing snippet: {snippet}")
    release_required = [
        "docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md",
        "scripts/inspect_settings_authority_posture.py",
        "feature_flag_writes",
        "provider_configuration",
        "installer_behavior",
        "runtime_activation",
        "connector_runtime",
        "public_beta_claim",
        "model_calls",
        "provider_sdk_calls",
        "live_web",
        "shell_browser_execution",
    ]
    for snippet in release_required:
        if snippet not in release_surface:
            _fail(f"release surface manifest missing snippet: {snippet}")


def _assert_docs() -> None:
    common_phrases = [
        "Product Loop 011",
        "Settings and kill-switch clarity",
        "blocked/degraded/partial",
        "no toggles that grant authority",
        "no provider configuration",
        "no installer behavior",
        "no runtime activation",
        "no feature-flag writes",
        "no kill-switch execution",
        "no revocation execution",
        "no connector runtime",
        "no connector writes",
        "no model calls",
        "no provider SDK calls",
        "no live web",
        "no shell/browser execution",
        "no public beta",
        "no production readiness",
        "no production authority",
    ]
    for path in DOC_PATHS:
        text = _normalized_text(path)
        for phrase in common_phrases:
            if phrase not in text:
                _fail(f"{path.relative_to(ROOT)} missing phrase: {phrase}")
    cli_phrase = "scripts/inspect_settings_authority_posture.py"
    for path in [
        ROOT / "docs/control_center/PRODUCT_LOOP_011_SETTINGS_KILL_SWITCH_CLARITY.md",
        ROOT / "docs/kanban/current_board.md",
        ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        ROOT / "docs/DOCUMENTATION_INDEX.md",
    ]:
        if cli_phrase not in _normalized_text(path):
            _fail(f"{path.relative_to(ROOT)} missing phrase: {cli_phrase}")


def main() -> int:
    payload = _assert_backend_contract()
    _assert_cli_contract(payload)
    _assert_static_ui()
    _assert_manifests()
    _assert_docs()
    print("Product Loop 011 Settings kill-switch clarity verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
