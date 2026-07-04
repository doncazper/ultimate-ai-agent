#!/usr/bin/env python3
"""Validate FCC-POLISH-001 Control Center polish baseline truth."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-POLISH-001"
DOC = ROOT / "docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md"
VISUAL_MANIFEST = ROOT / "docs/control_center/visual_regression_manifest.json"
VISUAL_SPEC = ROOT / "apps/control-center/tests/visual/control-center.visual.spec.ts"
PACKAGE_JSON = ROOT / "apps/control-center/package.json"
SETUP_PANEL = ROOT / "apps/control-center/src/components/MacOSSetupAssistantPanel.tsx"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
FOCUSED_TEST = ROOT / "tests/test_fcc_polish_001_native_apple_grade_ux_layer.py"

DOC_REF = "docs/control_center/FCC_POLISH_001_NATIVE_APPLE_GRADE_UX_LAYER.md"
VERIFIER_REF = "scripts/verify_fcc_polish_001_native_apple_grade_ux_layer.py"
TEST_REF = "tests/test_fcc_polish_001_native_apple_grade_ux_layer.py"
VISUAL_MANIFEST_REF = "docs/control_center/visual_regression_manifest.json"
VISUAL_SPEC_REF = "apps/control-center/tests/visual/control-center.visual.spec.ts"
REQUIRED_SURFACES = {
    "Overview",
    "Start Here",
    "Today",
    "Source Inbox",
    "Actions",
    "Plans",
    "Proof",
    "Trust",
    "Memory",
    "Evidence",
    "Settings",
    "Setup",
}
REQUIRED_STATE_SCENARIOS = {
    "state-loading",
    "state-empty",
    "state-error",
    "state-blocked",
    "state-partial",
    "state-success",
}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing FCC-POLISH-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented as a verified Control Center polish baseline",
            VISUAL_MANIFEST_REF,
            VISUAL_SPEC_REF,
            "Overview, Start Here, Today, Source Inbox, Actions, Plans, Proof, Trust, Memory, Evidence, Settings, and Setup",
            "route-state scenarios for loading, empty, error, blocked, partial, and success",
            "redacted test fixtures",
            "`/setup` remains a dry-run macOS-first setup preview",
            "no signed/public distribution",
            "no installer mutation",
            "no LaunchAgent install/load/start",
            "no notification delivery",
            "no native OS authority",
            "no production authority",
            VERIFIER_REF,
            TEST_REF,
        ],
        failures,
    )


def _validate_visual_baseline(root: Path, failures: list[str]) -> None:
    manifest_text = _read_text(root, VISUAL_MANIFEST, failures)
    if not manifest_text:
        return
    manifest = json.loads(manifest_text)
    if manifest.get("schema_version") != "uaa-control-center-visual-regression.v1":
        failures.append("visual regression manifest schema version drifted")
    policy = manifest.get("baseline_policy", {})
    for flag in [
        "raw_private_screenshots_allowed",
        "absolute_paths_allowed",
        "local_user_paths_allowed",
        "secret_material_allowed",
    ]:
        if policy.get(flag) is not False:
            failures.append(f"visual baseline policy must deny {flag}")
    if policy.get("checked_in_redacted_baselines_required") is not True:
        failures.append("visual baselines must require checked-in redacted baselines")
    surfaces = manifest.get("surfaces", [])
    surface_names = {str(surface.get("surface")) for surface in surfaces}
    if not REQUIRED_SURFACES.issubset(surface_names):
        failures.append("visual manifest missing required Founder Command Center surfaces")
    state_scenarios = manifest.get("state_scenarios", [])
    scenario_names = {
        str(scenario.get("scenario"))
        for scenario in state_scenarios
        if isinstance(scenario, dict)
    }
    if not REQUIRED_STATE_SCENARIOS.issubset(scenario_names):
        failures.append("visual manifest missing required route-state scenarios")
    for surface in surfaces:
        if surface.get("raw_private_screenshot_included") is not False:
            failures.append("visual baseline must not include raw private screenshots")
        hashes = surface.get("baseline_hashes", {})
        if not str(hashes.get("desktop", "")).startswith("sha256:"):
            failures.append(f"visual baseline desktop hash missing for {surface}")
        if not str(hashes.get("mobile", "")).startswith("sha256:"):
            failures.append(f"visual baseline mobile hash missing for {surface}")

    requirements = {
        VISUAL_SPEC: [
            "const surfaces =",
            "routeStateScenarios",
            "overview",
            "start",
            "today",
            "inbox",
            "actions",
            "plans",
            "proof",
            "trust",
            "memory",
            "evidence",
            "settings",
            "setup",
            "state-loading",
            "state-success",
            "Mock fallback active",
            "toHaveScreenshot",
        ],
        PACKAGE_JSON: [
            '"visual:check": "playwright test --config=playwright.visual.config.ts"',
            '"visual:capture": "playwright test --config=playwright.visual.config.ts --update-snapshots"',
        ],
        SETUP_PANEL: [
            "Visual setup preview",
            "installer actions",
            "Blocked setup authority",
            "Dry-run approval envelopes",
            "Receipts and rollback",
            "recommendation only",
        ],
        FOCUSED_TEST: [
            "test_polish_visual_manifest_covers_required_surfaces",
            "test_setup_assistant_copy_keeps_native_authority_blocked",
            "test_fcc_polish_001_verifier_passes_current_repo",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-POLISH-001 Native And Apple-Grade UX Layer",
            DOC_REF,
            "No signed distribution",
            "no production-readiness claim",
        ],
        FCC_BOARD: [
            "FCC-POLISH-001",
            "Native And Apple-grade UX Layer",
            DOC_REF,
            VISUAL_MANIFEST_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-POLISH-001",
            DOC_REF,
            VISUAL_MANIFEST_REF,
            "no installer mutation",
            "no native OS authority",
            "no production authority",
        ],
        DOCS_README: [DOC_REF, VISUAL_MANIFEST_REF],
        DOCS_INDEX: [DOC_REF, VISUAL_MANIFEST_REF],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_polish_001_native_apple_grade_ux_layer(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_visual_baseline(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-POLISH-001 polish and visual baseline truth."
    )
    parser.parse_args(argv)
    failures = validate_fcc_polish_001_native_apple_grade_ux_layer()
    if failures:
        print(f"{TASK_REF} verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"{TASK_REF} verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
