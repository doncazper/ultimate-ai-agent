#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "packaging" / "local-runtime" / "packaging_proof_manifest.json"
PROOF_SCRIPT_PATH = ROOT / "scripts" / "run_local_runtime_packaging_proof.py"
REQUIRED_STEPS = {
    "compose-build",
    "api-health",
    "control-center-load",
    "route-manifest-check",
    "screenshot-capture",
    "clean-shutdown",
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
    failures.extend(_validate_proof_script())
    if manifest.get("schema_version") != "uaa-local-runtime-packaging-proof.v1":
        failures.append("packaging proof manifest schema version is not current")
    if "pending" in str(manifest.get("status", "")).lower():
        failures.append("packaging proof manifest status must not be pending")
    if manifest.get("distribution_claims_allowed") is not False:
        failures.append("packaging proof must deny distribution claims")
    if manifest.get("proof_script_ref") != "script:local-runtime-packaging-proof":
        failures.append("packaging proof manifest must reference the launch-smoke proof script")
    if manifest.get("summary_schema") != "uaa-local-runtime-packaging-proof-summary.v1":
        failures.append("packaging proof manifest must declare the safe summary schema")
    steps = manifest.get("required_steps", [])
    step_ids = {str(step.get("step_id")) for step in steps if isinstance(step, dict)}
    for step_id in sorted(REQUIRED_STEPS - step_ids):
        failures.append(f"packaging proof manifest missing step: {step_id}")
    safety = manifest.get("safety", {})
    for flag, value in safety.items():
        if value is not False:
            failures.append(f"packaging proof safety flag must be false: {flag}")
    serialized = " ".join(_string_values(manifest))
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment.lower() in serialized.lower():
            failures.append(f"packaging proof manifest contains forbidden fragment: {fragment}")
    for step in steps:
        if not isinstance(step, dict):
            failures.append("packaging proof step entry must be an object")
            continue
        if step.get("raw_log_included") is not False:
            failures.append(f"{step.get('step_id', 'unknown')} must not include raw logs")
        if "pending" in str(step.get("status", "")).lower():
            failures.append(f"{step.get('step_id', 'unknown')} status must not be pending")
        if not str(step.get("safe_evidence_ref", "")).startswith("packaging-proof:"):
            failures.append(f"{step.get('step_id', 'unknown')} evidence ref is not safe")
        if not str(step.get("command_ref", "")).startswith("command:packaging."):
            failures.append(f"{step.get('step_id', 'unknown')} command ref is not scoped")
    return failures


def validate_summary(summary: dict) -> list[str]:
    failures: list[str] = []
    if summary.get("schema_version") != "uaa-local-runtime-packaging-proof-summary.v1":
        failures.append("packaging proof summary schema version is not current")
    if summary.get("distribution_claims_allowed") is not False:
        failures.append("packaging proof summary must deny distribution claims")
    if not str(summary.get("proof_ref", "")).startswith("packaging-proof:"):
        failures.append("packaging proof summary ref is not safe")
    steps = summary.get("steps", [])
    step_ids = {str(step.get("step_id")) for step in steps if isinstance(step, dict)}
    for step_id in sorted(REQUIRED_STEPS - step_ids):
        failures.append(f"packaging proof summary missing step: {step_id}")
    for step in steps:
        if not isinstance(step, dict):
            failures.append("packaging proof summary step entry must be an object")
            continue
        if step.get("raw_log_included") is not False:
            failures.append(f"{step.get('step_id', 'unknown')} summary must not include raw logs")
        if not str(step.get("safe_evidence_ref", "")).startswith("packaging-proof:"):
            failures.append(f"{step.get('step_id', 'unknown')} summary evidence ref is not safe")
    screenshot = summary.get("screenshot_proof", {})
    if screenshot.get("raw_private_screenshot_included") is not False:
        failures.append("packaging screenshot proof must not include raw private screenshot")
    screenshot_hash = screenshot.get("sha256")
    if screenshot_hash is not None and (
        not isinstance(screenshot_hash, str)
        or not screenshot_hash.startswith("sha256:")
        or len(screenshot_hash) != 71
    ):
        failures.append("packaging screenshot proof hash is invalid")
    serialized = " ".join(_string_values(summary))
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment.lower() in serialized.lower():
            failures.append(f"packaging proof summary contains forbidden fragment: {fragment}")
    return failures


def _validate_proof_script() -> list[str]:
    failures: list[str] = []
    if not PROOF_SCRIPT_PATH.exists():
        return ["local runtime packaging proof script is missing"]
    script = PROOF_SCRIPT_PATH.read_text(encoding="utf-8")
    required_fragments = {
        "docker compose": ["\"docker\"", "\"compose\""],
        "compose up build": ["\"up\"", "\"--build\"", "\"--detach\""],
        "compose down": ["\"down\"", "\"--remove-orphans\""],
        "loopback port selection": ["_select_available_port", "DEFAULT_API_PORT", "DEFAULT_CONTROL_CENTER_PORT"],
        "api health": ["/health"],
        "api manifest": ["/api/manifest"],
        "control center load": ["/today"],
        "screenshot capture": ["\"npx\"", "\"playwright\"", "\"screenshot\""],
        "safe summary": ["raw_logs_omitted", "raw_paths_omitted", "safe_refs_only"],
    }
    for label, fragments in required_fragments.items():
        if not all(fragment in script for fragment in fragments):
            failures.append(f"packaging proof script missing {label} implementation")
    return failures


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
    print("OK: Local runtime packaging proof manifest is safe and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
