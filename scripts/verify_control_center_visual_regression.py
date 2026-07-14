#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "docs" / "control_center" / "visual_regression_manifest.json"
CONTROL_CENTER_ROOT = ROOT / "apps" / "control-center"
PACKAGE_JSON_PATH = CONTROL_CENTER_ROOT / "package.json"
PLAYWRIGHT_CONFIG_PATH = CONTROL_CENTER_ROOT / "playwright.visual.config.ts"
VISUAL_SPEC_PATH = (
    CONTROL_CENTER_ROOT / "tests" / "visual" / "control-center.visual.spec.ts"
)
SNAPSHOT_ROOT = CONTROL_CENTER_ROOT / "tests" / "visual" / "__snapshots__"
REQUIRED_SURFACES = {
    "Overview",
    "Start Here",
    "Today",
    "Actions",
    "Source Inbox",
    "Plans",
    "Proof",
    "Trust",
    "Memory",
    "Evidence",
    "Settings",
    "Setup",
    "Studio Skill Workbench",
    "Messenger Desktop Fixture",
}
REQUIRED_VIEWPORTS = {"desktop", "mobile"}
STUDIO_DESKTOP_VARIANTS = {
    "wide": {
        "viewport_ref": "viewport:desktop-wide-1586x992",
        "width": 1586,
        "height": 992,
        "file_id": "studio-skills-wide",
    },
    "compact": {
        "viewport_ref": "viewport:desktop-compact-1280x800",
        "width": 1280,
        "height": 800,
        "file_id": "studio-skills-compact",
    },
}
MESSENGER_SURFACE_IDS = (
    "founder",
    "personal",
    "dm",
    "group",
    "threads",
    "search",
    "room-info",
    "invite",
    "room-settings",
    "sessions",
    "intelligence",
    "recovery",
    "dark",
    "calling",
    "setup",
)
MESSENGER_DESKTOP_VIEWPORTS = {
    "wide": {
        "viewport_ref": "viewport:desktop-wide-1440x900",
        "width": 1440,
        "height": 900,
    },
    "compact": {
        "viewport_ref": "viewport:desktop-compact-1180x800",
        "width": 1180,
        "height": 800,
    },
}
MESSENGER_DESKTOP_VARIANTS = {
    f"{surface_id}-{viewport}": {
        "surface_id": surface_id,
        "viewport_ref": details["viewport_ref"],
        "width": details["width"],
        "height": details["height"],
        "file_id": f"messenger-{surface_id}-{viewport}",
    }
    for viewport, details in MESSENGER_DESKTOP_VIEWPORTS.items()
    for surface_id in MESSENGER_SURFACE_IDS
}
REQUIRED_STATE_SCENARIOS = {
    "state-loading",
    "state-empty",
    "state-error",
    "state-blocked",
    "state-partial",
    "state-success",
}
EXPECTED_PLATFORM_POSTURE = {
    "macos": {
        "status": "implemented",
        "render_ref": "visual-baselines:control-center:macos-canonical",
        "compatibility_claimed": True,
    },
    "linux": {
        "status": "render_placeholder",
        "render_ref": "visual-placeholder:control-center:linux",
        "compatibility_claimed": False,
        "activation_posture": "deferred_until_backend_production_ready",
        "port_source": "then-current-macos-canonical",
    },
    "windows": {
        "status": "render_placeholder",
        "render_ref": "visual-placeholder:control-center:windows",
        "compatibility_claimed": False,
        "activation_posture": "deferred_until_backend_production_ready",
        "port_source": "then-current-macos-canonical",
    },
}
FORBIDDEN_FRAGMENTS = (
    "/Users/",
    "\\Users\\",
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
)


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict) -> list[str]:
    failures: list[str] = []
    failures.extend(_validate_tooling())
    if manifest.get("schema_version") != "uaa-control-center-visual-regression.v1":
        failures.append("visual regression manifest schema version is not current")
    if manifest.get("status") != "active checked-in macOS visual baseline":
        failures.append(
            "visual regression manifest status must identify the active macOS baseline"
        )
    if manifest.get("playwright_dependency_status") != "control-center devDependency":
        failures.append(
            "visual regression manifest must record Playwright as a Control Center devDependency"
        )
    policy = manifest.get("baseline_policy", {})
    if policy.get("checked_in_redacted_baselines_required") is not True:
        failures.append("visual baselines must require checked-in redacted baselines")
    if policy.get("canonical_platform") != "macos":
        failures.append("visual baselines must declare macOS as the canonical platform")
    if policy.get("non_macos_baselines_allowed") is not False:
        failures.append("visual baselines must keep non-macOS baselines disabled")
    for flag in [
        "raw_private_screenshots_allowed",
        "absolute_paths_allowed",
        "local_user_paths_allowed",
        "secret_material_allowed",
    ]:
        if policy.get(flag) is not False:
            failures.append(f"visual baseline policy must deny {flag}")
    if manifest.get("platform_posture") != EXPECTED_PLATFORM_POSTURE:
        failures.append(
            "visual platform posture must implement macOS and keep Linux/Windows as deferred render placeholders"
        )
    surfaces = manifest.get("surfaces", [])
    surface_names = {
        str(surface.get("surface")) for surface in surfaces if isinstance(surface, dict)
    }
    for surface in sorted(REQUIRED_SURFACES - surface_names):
        failures.append(f"visual regression manifest missing surface: {surface}")
    serialized = " ".join(_string_values(manifest))
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment.lower() in serialized.lower():
            failures.append(
                f"visual regression manifest contains forbidden fragment: {fragment}"
            )
    for surface in surfaces:
        if not isinstance(surface, dict):
            failures.append("visual regression surface entry must be an object")
            continue
        surface_name = str(surface.get("surface", "unknown"))
        if surface.get("raw_private_screenshot_included") is not False:
            failures.append(f"{surface_name} must not include raw private screenshot")
        route = str(surface.get("route", ""))
        if not route.startswith("/"):
            failures.append(f"{surface_name} route must be repo-local path")
        baseline_ref = str(surface.get("baseline_ref", ""))
        if not baseline_ref.startswith("visual-baseline:control-center:"):
            failures.append(f"{surface_name} baseline ref is not safe")
        if surface.get("baseline_status") != "checked-in redacted PNG baseline":
            failures.append(f"{surface_name} baseline status must be checked-in")
        failures.extend(_validate_baselines(surface))
    state_scenarios = manifest.get("state_scenarios", [])
    if not isinstance(state_scenarios, list):
        failures.append("visual regression manifest state_scenarios must be a list")
        state_scenarios = []
    scenario_names = {
        str(scenario.get("scenario"))
        for scenario in state_scenarios
        if isinstance(scenario, dict)
    }
    for scenario in sorted(REQUIRED_STATE_SCENARIOS - scenario_names):
        failures.append(
            f"visual regression manifest missing state scenario: {scenario}"
        )
    for scenario in state_scenarios:
        if not isinstance(scenario, dict):
            failures.append("visual regression state scenario entry must be an object")
            continue
        scenario_name = str(scenario.get("scenario", "unknown"))
        if scenario_name not in REQUIRED_STATE_SCENARIOS:
            failures.append(
                f"visual regression manifest has unknown state scenario: {scenario_name}"
            )
        if scenario.get("raw_private_screenshot_included") is not False:
            failures.append(f"{scenario_name} must not include raw private screenshot")
        if scenario.get("baseline_status") != "checked-in redacted PNG baseline":
            failures.append(f"{scenario_name} baseline status must be checked-in")
        failures.extend(_validate_baselines(scenario))
    return failures


def _validate_tooling() -> list[str]:
    failures: list[str] = []
    package = json.loads(PACKAGE_JSON_PATH.read_text(encoding="utf-8"))
    scripts = package.get("scripts", {})
    dev_deps = package.get("devDependencies", {})
    if "@playwright/test" not in dev_deps:
        failures.append(
            "Control Center package must include @playwright/test as a devDependency"
        )
    if scripts.get("visual:check") != (
        "playwright test --config=playwright.visual.config.ts --project=desktop"
    ):
        failures.append(
            "Control Center package must define the macOS-first desktop visual check"
        )
    if scripts.get("visual:capture") != (
        "playwright test --config=playwright.visual.config.ts "
        "--project=desktop --update-snapshots"
    ):
        failures.append(
            "Control Center package must define the macOS-first desktop visual capture"
        )
    if not PLAYWRIGHT_CONFIG_PATH.exists():
        failures.append("Playwright visual config is missing")
    if not VISUAL_SPEC_PATH.exists():
        failures.append("Playwright visual spec is missing")
    return failures


def _validate_baselines(surface: dict) -> list[str]:
    if surface.get("surface") == "Studio Skill Workbench":
        return _validate_studio_desktop_baselines(surface)
    if surface.get("surface") == "Messenger Desktop Fixture":
        return _validate_messenger_desktop_baselines(surface)
    failures: list[str] = []
    surface_name = str(surface.get("surface") or surface.get("scenario") or "")
    surface_id = _surface_id(surface)
    file_refs = surface.get("baseline_file_refs", {})
    hashes = surface.get("baseline_hashes", {})
    if set(file_refs) != REQUIRED_VIEWPORTS:
        failures.append(
            f"{surface_name} must list desktop and mobile baseline file refs"
        )
    if set(hashes) != REQUIRED_VIEWPORTS:
        failures.append(f"{surface_name} must list desktop and mobile baseline hashes")
    for viewport in sorted(REQUIRED_VIEWPORTS):
        expected_ref = f"visual-baseline-file:{viewport}:{surface_id}"
        if file_refs.get(viewport) != expected_ref:
            failures.append(f"{surface_name} {viewport} baseline file ref is not safe")
        expected_hash = str(hashes.get(viewport, ""))
        if not expected_hash.startswith("sha256:") or len(expected_hash) != 71:
            failures.append(f"{surface_name} {viewport} baseline hash is invalid")
            continue
        baseline_path = SNAPSHOT_ROOT / viewport / f"{surface_id}.png"
        if not baseline_path.exists():
            failures.append(f"{surface_name} {viewport} baseline PNG is missing")
            continue
        actual_hash = "sha256:" + hashlib.sha256(baseline_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            failures.append(
                f"{surface_name} {viewport} baseline hash does not match checked-in PNG"
            )
    return failures


def _validate_studio_desktop_baselines(surface: dict) -> list[str]:
    failures: list[str] = []
    variants = surface.get("desktop_variants", {})
    if set(variants) != set(STUDIO_DESKTOP_VARIANTS):
        failures.append(
            "Studio Skill Workbench must list wide and compact desktop variants"
        )
        return failures
    if "mobile" in variants or "mobile" in surface.get("baseline_file_refs", {}):
        failures.append("Studio Skill Workbench must not claim a mobile baseline")
    for name, expected in STUDIO_DESKTOP_VARIANTS.items():
        variant = variants.get(name, {})
        file_id = expected["file_id"]
        expected_ref = f"visual-baseline-file:desktop:{file_id}"
        if variant.get("viewport_ref") != expected["viewport_ref"]:
            failures.append(f"Studio Skill Workbench {name} viewport ref drifted")
        if variant.get("width") != expected["width"]:
            failures.append(f"Studio Skill Workbench {name} width drifted")
        if variant.get("height") != expected["height"]:
            failures.append(f"Studio Skill Workbench {name} height drifted")
        if variant.get("baseline_file_ref") != expected_ref:
            failures.append(f"Studio Skill Workbench {name} file ref is not safe")
        expected_hash = str(variant.get("baseline_hash", ""))
        if not expected_hash.startswith("sha256:") or len(expected_hash) != 71:
            failures.append(f"Studio Skill Workbench {name} hash is invalid")
            continue
        baseline_path = SNAPSHOT_ROOT / "desktop" / f"{file_id}.png"
        if not baseline_path.exists():
            failures.append(f"Studio Skill Workbench {name} baseline PNG is missing")
            continue
        encoded = baseline_path.read_bytes()
        if len(encoded) < 24 or encoded[:8] != b"\x89PNG\r\n\x1a\n":
            failures.append(f"Studio Skill Workbench {name} baseline is not PNG")
            continue
        width, height = struct.unpack(">II", encoded[16:24])
        if (width, height) != (expected["width"], expected["height"]):
            failures.append(f"Studio Skill Workbench {name} PNG dimensions drifted")
        actual_hash = "sha256:" + hashlib.sha256(encoded).hexdigest()
        if actual_hash != expected_hash:
            failures.append(
                f"Studio Skill Workbench {name} baseline hash does not match checked-in PNG"
            )
    return failures


def _validate_messenger_desktop_baselines(surface: dict) -> list[str]:
    failures: list[str] = []
    variants = surface.get("desktop_variants", {})
    if set(variants) != set(MESSENGER_DESKTOP_VARIANTS):
        failures.append(
            "Messenger Desktop Fixture must list all 15 surfaces at wide and compact desktop widths"
        )
        return failures
    if "mobile" in variants or "mobile" in surface.get("baseline_file_refs", {}):
        failures.append("Messenger Desktop Fixture must not claim a mobile baseline")
    for name, expected in MESSENGER_DESKTOP_VARIANTS.items():
        variant = variants.get(name, {})
        file_id = expected["file_id"]
        expected_ref = f"visual-baseline-file:desktop:{file_id}"
        for field in ("surface_id", "viewport_ref", "width", "height"):
            if variant.get(field) != expected[field]:
                failures.append(f"Messenger Desktop Fixture {name} {field} drifted")
        if variant.get("baseline_file_ref") != expected_ref:
            failures.append(f"Messenger Desktop Fixture {name} file ref is not safe")
        expected_hash = str(variant.get("baseline_hash", ""))
        if not expected_hash.startswith("sha256:") or len(expected_hash) != 71:
            failures.append(f"Messenger Desktop Fixture {name} hash is invalid")
            continue
        baseline_path = SNAPSHOT_ROOT / "desktop" / f"{file_id}.png"
        if not baseline_path.exists():
            failures.append(f"Messenger Desktop Fixture {name} baseline PNG is missing")
            continue
        encoded = baseline_path.read_bytes()
        if len(encoded) < 24 or encoded[:8] != b"\x89PNG\r\n\x1a\n":
            failures.append(f"Messenger Desktop Fixture {name} baseline is not PNG")
            continue
        width, height = struct.unpack(">II", encoded[16:24])
        if (width, height) != (expected["width"], expected["height"]):
            failures.append(f"Messenger Desktop Fixture {name} PNG dimensions drifted")
        actual_hash = "sha256:" + hashlib.sha256(encoded).hexdigest()
        if actual_hash != expected_hash:
            failures.append(
                f"Messenger Desktop Fixture {name} baseline hash does not match checked-in PNG"
            )
    return failures


def _surface_id(surface: dict) -> str:
    baseline_ref = str(surface.get("baseline_ref", ""))
    if baseline_ref.startswith("visual-baseline:control-center:"):
        return baseline_ref.rsplit(":", 1)[-1]
    return str(surface.get("surface", "")).lower().replace(" ", "-")


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_string_values(item))
        return values
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    return []


def main() -> int:
    failures = validate_manifest(load_manifest())
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: Control Center visual regression manifest is safe and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
