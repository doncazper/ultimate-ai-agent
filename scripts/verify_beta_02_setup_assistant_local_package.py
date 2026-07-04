#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts import verify_local_macos_app_bundle_proof  # noqa: E402
from scripts.verify_local_runtime_packaging_proof import (  # noqa: E402
    load_manifest as load_runtime_packaging_manifest,
    validate_manifest as validate_runtime_packaging_manifest,
)
from ultimate_ai_agent.core.macos_setup_assistant import (  # noqa: E402
    build_default_macos_setup_assistant_plan,
)


SETUP_PANEL = ROOT / "apps" / "control-center" / "src" / "components" / "MacOSSetupAssistantPanel.tsx"
SETUP_TEST = ROOT / "apps" / "control-center" / "src" / "App.test.tsx"
RELEASE_SURFACE_MANIFEST = ROOT / "docs" / "control_center" / "release_surface_manifest.json"
SETUP_PLAN_DOC = ROOT / "docs" / "macos" / "UAA-setup-assistant-plan.md"
LOCAL_RUNTIME_DOC = ROOT / "docs" / "production" / "LOCAL_RUNTIME_PACKAGING.md"
LOCAL_RUNTIME_PROOF_SCRIPT = ROOT / "scripts" / "run_local_runtime_packaging_proof.py"

REQUIRED_FIRST_RUN_REFS = {
    "loop-ref:setup-to-daily-loop:v1",
    "contract-ref:start-here-local-loop:v1",
    "contract-ref:private-beta-readiness-gate:v1",
    "contract-ref:dogfood-live-loop:acceptance",
    "proof-ref:control-center-proof-index",
    "trust-ref:authority-map",
}
REQUIRED_PACKAGE_REFS = {
    "packaging-proof:local-runtime-loopback",
    "packaging-proof:local-macos-app-bundle",
    "packaging-proof-summary:local-macos-app-bundle",
    "script:verify-local-runtime-packaging-proof",
    "script:verify-local-macos-app-bundle-proof",
}
REQUIRED_PROMOTION_REFS = {
    "promotion-path-ref:setup:local-rehearsal-receipt",
    "promotion-path-ref:setup:operator-review-notes",
    "promotion-path-ref:setup:package-proof-hygiene",
    "promotion-path-ref:setup:exact-approved-mutation-pr",
}
REQUIRED_BLOCKED_CAPABILITIES = {
    "macos-setup-model-download",
    "macos-setup-launch-agent-change",
    "macos-setup-background-service-change",
    "macos-setup-bridge-enablement",
    "macos-setup-credential-storage",
    "macos-setup-rollback-execution",
    "macos-setup-signed-distribution",
    "macos-setup-production-authority",
}


def main() -> int:
    failures: list[str] = []
    failures.extend(_validate_plan())
    failures.extend(_validate_runtime_packaging())
    failures.extend(verify_local_macos_app_bundle_proof.verify())
    failures.extend(
        _require_fragments(
            SETUP_PANEL,
            [
                "First-run proof spine",
                "Local package proof",
                "Exact promotion path",
                "Provider setup is reference-only",
                "not needed for the local loop",
            ],
            "Control Center setup panel",
        )
    )
    failures.extend(
        _require_fragments(
            SETUP_TEST,
            [
                "First-run proof spine",
                "Local package proof",
                "Exact promotion path",
                "packaging-proof:local-macos-app-bundle",
                "loop-ref:setup-to-daily-loop:v1",
            ],
            "Control Center setup tests",
        )
    )
    failures.extend(
        _require_fragments(
            SETUP_PLAN_DOC,
            [
                "Beta 02 Setup Assistant And Local Package Hardening",
                "Full-strength version",
                "Repo-safe version",
                "Blocked / needs authority",
                "Exact promotion path",
                "Local package proof",
            ],
            "setup assistant plan doc",
        )
    )
    failures.extend(
        _require_fragments(
            LOCAL_RUNTIME_DOC,
            [
                "token_urlsafe",
                "chmod(0o600)",
                "local-only and unsigned",
                "without launching the app",
            ],
            "local runtime packaging doc",
        )
    )
    failures.extend(_validate_release_surface_manifest())
    failures.extend(_validate_secret_generation())
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: beta-02 setup assistant and local package lane is safe and current")
    return 0


def _validate_plan() -> list[str]:
    failures: list[str] = []
    plan = build_default_macos_setup_assistant_plan()
    if "daily loop" not in plan.full_strength_goal:
        failures.append("setup plan must preserve the full daily-loop goal")
    if "Read-only setup plan" not in plan.repo_safe_scope:
        failures.append("setup plan must declare repo-safe read-only scope")
    if "public distribution" not in plan.blocked_authority_summary:
        failures.append("setup plan must keep public distribution blocked")
    if not REQUIRED_FIRST_RUN_REFS.issubset(set(plan.first_run_loop_refs)):
        failures.append("setup plan missing first-run loop refs")
    if not REQUIRED_PACKAGE_REFS.issubset(set(plan.local_package_proof_refs)):
        failures.append("setup plan missing local package proof refs")
    if not REQUIRED_PROMOTION_REFS.issubset(set(plan.promotion_path_refs)):
        failures.append("setup plan missing exact promotion refs")
    if plan.local_package_proof_status != "local_unsigned_loopback_package_proof_available_runtime_launch_blocked":
        failures.append("setup plan package proof status must remain local unsigned and launch blocked")
    if not REQUIRED_BLOCKED_CAPABILITIES.issubset(set(plan.blocked_capabilities)):
        failures.append("setup plan missing blocked setup capabilities")
    denied_flags = {
        "native_macos_app_ready": plan.native_macos_app_ready,
        "installer_side_effects_enabled": plan.installer_side_effects_enabled,
        "setup_question_assistant_enabled": plan.setup_question_assistant_enabled,
        "model_output_authoritative": plan.model_output_authoritative,
    }
    for field_name, value in denied_flags.items():
        if value is not False:
            failures.append(f"setup plan must keep {field_name} false")
    if any(step.terminal_command_executed for step in plan.steps):
        failures.append("setup plan must not execute terminal commands")
    if any(step.state_change_performed for step in plan.steps):
        failures.append("setup plan must not perform state changes")
    if any(step.model_download_performed for step in plan.steps):
        failures.append("setup plan must not download models")
    return failures


def _validate_runtime_packaging() -> list[str]:
    failures = validate_runtime_packaging_manifest(load_runtime_packaging_manifest())
    if failures:
        return failures
    manifest = load_runtime_packaging_manifest()
    scope = str(manifest.get("packaging_scope", "")).lower()
    if "local loopback" not in scope:
        return ["runtime packaging manifest must remain local loopback scoped"]
    return []


def _validate_release_surface_manifest() -> list[str]:
    failures: list[str] = []
    manifest = json.loads(RELEASE_SURFACE_MANIFEST.read_text(encoding="utf-8"))
    setup = next(
        (
            surface
            for surface in manifest.get("routes", [])
            if isinstance(surface, dict) and surface.get("path") == "/setup"
        ),
        None,
    )
    if setup is None:
        return ["release surface manifest missing /setup surface"]
    if setup.get("status") != "partial" or setup.get("ui_status") != "dry-run":
        failures.append("/setup release surface must remain partial dry-run")
    blocked = set(str(item) for item in setup.get("blocked_capabilities", []))
    for capability in [
        "public_distribution_claim",
        "production_readiness_claim",
        "production_authority",
    ]:
        if capability not in blocked:
            failures.append(f"/setup release surface missing blocked capability: {capability}")
    evidence = " ".join(str(item) for item in setup.get("evidence_refs", []))
    for fragment in [
        "LOCAL_RUNTIME_PACKAGING.md",
        "packaging_distribution_local_macos_app_bundle_2026_07_03.md",
        "verify_local_macos_app_bundle_proof.py",
        "verify_beta_02_setup_assistant_local_package.py",
    ]:
        if fragment not in evidence:
            failures.append(f"/setup release surface missing evidence ref: {fragment}")
    proof_lanes = " ".join(str(item) for item in setup.get("proof_lanes", []))
    if "verify_beta_02_setup_assistant_local_package.py" not in proof_lanes:
        failures.append("/setup release surface missing beta-02 proof lane")
    caveats = " ".join(str(item) for item in setup.get("product_language_caveats", [])).lower()
    if "local package proof" not in caveats:
        failures.append("/setup release surface must caveat local package proof scope")
    return failures


def _validate_secret_generation() -> list[str]:
    script = LOCAL_RUNTIME_PROOF_SCRIPT.read_text(encoding="utf-8")
    failures: list[str] = []
    if "secrets.token_urlsafe(48)" not in script:
        failures.append("local runtime proof must generate high-entropy local secret material")
    if ".chmod(0o600)" not in script:
        failures.append("local runtime proof must chmod generated local secret material")
    if "local-runtime-proof-material" in script:
        failures.append("local runtime proof must not contain static local secret material")
    return failures


def _require_fragments(path: Path, fragments: list[str], label: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{label} missing fragment: {fragment}" for fragment in fragments if fragment not in text]


if __name__ == "__main__":
    raise SystemExit(main())
