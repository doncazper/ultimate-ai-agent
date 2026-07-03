#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import stat
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = ROOT / ".uaa" / "local-runtime" / "macos-app-proof"
APP_NAME = "Ultimate AI Agent Local"
EXECUTABLE_NAME = "Ultimate AI Agent Local"
SUMMARY_SCHEMA = "uaa-local-macos-app-bundle-proof-summary.v1"
PROOF_REF = "packaging-proof:local-macos-app-bundle"
SUMMARY_REF = "packaging-proof-summary:local-macos-app-bundle"
BUNDLE_REF = "local-macos-app-bundle:ultimate-ai-agent-local"

FORBIDDEN_SUMMARY_FRAGMENTS = (
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
    "client_secret",
)

FORBIDDEN_LAUNCHER_FRAGMENTS = (
    "codesign",
    "notarytool",
    "launchctl",
    "launchagent",
    "0.0.0.0",
    "sudo ",
    "brew install",
)


def build_local_macos_app_bundle_proof(output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    """Create an ignored, unsigned local macOS app bundle proof."""
    bundle_root = output_root / f"{APP_NAME}.app"
    contents = bundle_root / "Contents"
    macos_dir = contents / "MacOS"
    resources_dir = contents / "Resources"
    executable = macos_dir / EXECUTABLE_NAME
    info_plist = contents / "Info.plist"
    readme = resources_dir / "README.txt"

    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    executable.write_text(_launcher_script(), encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    plist_data = _info_plist()
    with info_plist.open("wb") as handle:
        plistlib.dump(plist_data, handle, sort_keys=True)
    readme.write_text(_readme(), encoding="utf-8")

    summary = {
        "schema_version": SUMMARY_SCHEMA,
        "status": "passed",
        "proof_ref": PROOF_REF,
        "summary_ref": SUMMARY_REF,
        "bundle_ref": BUNDLE_REF,
        "artifact_root_ref": "ignored-state:uaa-local-runtime-macos-app-proof",
        "launcher_command_ref": "command:local-macos-app.trial-boot",
        "app_bundle_created": True,
        "info_plist_created": True,
        "launcher_entrypoint_created": True,
        "launch_executed": False,
        "distribution_claims_allowed": False,
        "signed": False,
        "notarized": False,
        "public_installer_created": False,
        "auto_update_enabled": False,
        "daemon_or_launchagent_created": False,
        "background_service_created": False,
        "provider_model_authority_added": False,
        "connector_write_authority_added": False,
        "browser_automation_added": False,
        "shell_subprocess_authority_added": False,
        "raw_path_included": False,
        "raw_log_included": False,
        "credential_material_included": False,
        "safe_disable_ref": "safe-disable:remove-local-macos-app-bundle",
        "rollback_ref": "rollback:delete-ignored-local-macos-app-bundle",
        "evidence_refs": [
            "packaging-proof:local-macos-app-info-plist",
            "packaging-proof:local-macos-app-launcher-entrypoint",
            "packaging-proof:local-macos-app-boundary-readme",
        ],
        "hash_refs": {
            "info_plist_sha256": _sha256_ref(info_plist),
            "launcher_entrypoint_sha256": _sha256_ref(executable),
            "boundary_readme_sha256": _sha256_ref(readme),
        },
        "redactions_applied": [
            "raw_paths_omitted",
            "raw_logs_omitted",
            "credentials_omitted",
            "safe_refs_only",
        ],
        "blocked_authority": [
            "signing",
            "notarization",
            "public_installer",
            "auto_update",
            "daemon_or_launchagent",
            "production_distribution",
            "provider_model_calls",
            "connector_writes",
            "browser_automation",
            "runtime_shell_authority",
        ],
    }
    failures = validate_summary(summary)
    if failures:
        raise RuntimeError("; ".join(failures))
    summary_path = output_root / "latest.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def validate_summary(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        failures.append("local macOS app proof summary schema drifted")
    if summary.get("status") != "passed":
        failures.append("local macOS app proof summary must be passed")
    if summary.get("proof_ref") != PROOF_REF:
        failures.append("local macOS app proof ref drifted")
    if summary.get("bundle_ref") != BUNDLE_REF:
        failures.append("local macOS app bundle ref drifted")
    for flag in [
        "launch_executed",
        "distribution_claims_allowed",
        "signed",
        "notarized",
        "public_installer_created",
        "auto_update_enabled",
        "daemon_or_launchagent_created",
        "background_service_created",
        "provider_model_authority_added",
        "connector_write_authority_added",
        "browser_automation_added",
        "shell_subprocess_authority_added",
        "raw_path_included",
        "raw_log_included",
        "credential_material_included",
    ]:
        if summary.get(flag) is not False:
            failures.append(f"local macOS app proof must keep {flag}=false")
    for flag in [
        "app_bundle_created",
        "info_plist_created",
        "launcher_entrypoint_created",
    ]:
        if summary.get(flag) is not True:
            failures.append(f"local macOS app proof must set {flag}=true")
    if not str(summary.get("artifact_root_ref", "")).startswith("ignored-state:"):
        failures.append("local macOS app proof must use an ignored-state artifact ref")
    for ref in summary.get("evidence_refs", []):
        if not str(ref).startswith("packaging-proof:local-macos-app-"):
            failures.append(f"unsafe local macOS app evidence ref: {ref}")
    serialized = " ".join(_string_values(summary))
    for fragment in FORBIDDEN_SUMMARY_FRAGMENTS:
        if fragment.lower() in serialized.lower():
            failures.append(f"local macOS app proof summary contains forbidden fragment: {fragment}")
    return failures


def _info_plist() -> dict[str, Any]:
    return {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": APP_NAME,
        "CFBundleExecutable": EXECUTABLE_NAME,
        "CFBundleIdentifier": "local.ultimate-ai-agent.control-center",
        "CFBundleName": APP_NAME,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.104.0-local",
        "CFBundleVersion": "0.104.0",
        "LSMinimumSystemVersion": "13.0",
        "UAAAuthorityBoundary": "local-only unsigned app bundle proof; not signed, not notarized, not public",
        "UAADistributionClaimsAllowed": False,
    }


def _launcher_script() -> str:
    return """#!/bin/sh
set -eu

APP_EXECUTABLE="$0"
SEARCH_DIR="$(CDPATH= cd -- "$(dirname -- "$APP_EXECUTABLE")" && pwd)"

while [ "$SEARCH_DIR" != "/" ]; do
  if [ -x "$SEARCH_DIR/scripts/dev/uaa" ]; then
    cd "$SEARCH_DIR"
    exec ./scripts/dev/uaa trial-boot
  fi
  SEARCH_DIR="$(dirname -- "$SEARCH_DIR")"
done

echo "Ultimate AI Agent repo root was not found for the local launcher." >&2
exit 1
"""


def _readme() -> str:
    return """Ultimate AI Agent Local.app

This app bundle is a local-only, unsigned operator launcher proof.

It is not signed, not notarized, not a public installer, not an auto-updater,
not a daemon, and not production distribution authority. Removing the generated
bundle disables this packaging lane artifact.
"""


def _sha256_ref(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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
    parser = argparse.ArgumentParser(description="Build the local unsigned macOS app bundle proof")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    summary = build_local_macos_app_bundle_proof(args.output_root)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
