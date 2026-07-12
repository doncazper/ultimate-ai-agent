#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/runtime/UAA_RUNTIME_ACTION_SIGNED_EVIDENCE.md",
    "src/ultimate_ai_agent/core/runtime_gateway/action_evidence.py",
    "src/ultimate_ai_agent/core/runtime_gateway/__init__.py",
    "src/ultimate_ai_agent/api/routes/runtime_pilot_service.py",
    "src/ultimate_ai_agent/core/control_center/runtime_action_bridge.py",
    "scripts/dev/uaa_runtime.py",
    "tests/test_runtime_action_signed_evidence.py",
]

DOC_REQUIRED = [
    "UAA Runtime Action Evidence",
    "does not copy external reference code",
    "Action Inbox approved workspace/execute utility command capabilities",
    "focused_pytest",
    "repo_verifier",
    "frontend_check",
    "repo_doctor",
    "legacy signed identifiers",
    "local SHA-256",
    "not cryptographic signatures",
    "Signing is blocked",
    "Control Center cannot mint authority",
    "broad runtime authority remains blocked",
    "no raw command output",
    "no unrestricted shell",
    "receipts evidence",
    "receipts verify-evidence",
]

CORE_REQUIRED = [
    "RUNTIME_ACTION_EVIDENCE_CONTRACT_REF",
    "RuntimeActionSignedEvidenceEnvelope",
    "RuntimeActionSignedEvidenceVerificationResult",
    "build_runtime_action_signed_evidence",
    "verify_runtime_action_signed_evidence",
    "route_decision_binding_ref",
    "envelope_hash_ref",
    "signed_envelope_ref",
    "integrity_scheme_ref",
    "sha256_hash_only_not_a_cryptographic_signature",
    "cryptographic_signature_present",
    "blocked_signing_lifecycle_not_implemented",
    "external_anchor_verified",
    "legacy_signed_envelope_ref_is_hash_only",
    "raw_command_output_persisted",
    "unrestricted_shell_execution_performed",
]

SURFACE_REQUIRED = [
    "signed_evidence_available",
    "signed_evidence_envelope",
    "signed_evidence_verification",
    "signed_evidence_refs",
    "signed_evidence_cli_ref",
    "signed_evidence_verifier_cli_ref",
    "governed-runtime-receipt-signed-evidence",
    "governed-runtime-receipt-verify-signed-evidence",
]

TEST_REQUIRED = [
    "test_runtime_action_signed_evidence_pass_path_is_verifiable",
    "repo_verifier",
    "frontend_check",
    "repo_doctor",
    "test_runtime_action_signed_evidence_requires_receipt_and_action_envelope",
    "test_runtime_action_signed_evidence_detects_scope_drift_and_tamper",
    "test_runtime_action_signed_evidence_idempotent_replay_is_stable",
    "test_runtime_action_signed_evidence_safe_disable_blocks_execution",
    "test_runtime_action_signed_evidence_cli_export_and_verify",
    "cryptographic_signature_verified",
]

FORBIDDEN_OVERCLAIMS = [
    "unrestricted shell is enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "plugin runtime import is enabled",
    "remote execution is enabled",
    "production authority is enabled",
    "public notarization is enabled",
]

RAW_PATH_RE = re.compile(r"/Users/[^\s`)]*")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require_all(text: str, needles: list[str], label: str) -> list[str]:
    return [f"Missing {label}: {needle}" for needle in needles if needle not in text]


def main() -> int:
    failures: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            failures.append(f"Missing required file: {rel}")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    doc = _read("docs/runtime/UAA_RUNTIME_ACTION_SIGNED_EVIDENCE.md")
    core = _read("src/ultimate_ai_agent/core/runtime_gateway/action_evidence.py")
    exports = _read("src/ultimate_ai_agent/core/runtime_gateway/__init__.py")
    api = _read("src/ultimate_ai_agent/api/routes/runtime_pilot_service.py")
    bridge = _read("src/ultimate_ai_agent/core/control_center/runtime_action_bridge.py")
    cli = _read("scripts/dev/uaa_runtime.py")
    tests = _read("tests/test_runtime_action_signed_evidence.py")
    combined = "\n".join([doc, core, exports, api, bridge, cli, tests])

    failures.extend(_require_all(doc, DOC_REQUIRED, "doc evidence"))
    failures.extend(_require_all(core + exports, CORE_REQUIRED, "core evidence"))
    failures.extend(_require_all(api + bridge + cli, SURFACE_REQUIRED, "surface evidence"))
    failures.extend(_require_all(tests, TEST_REQUIRED, "test evidence"))

    lowered = combined.lower()
    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in lowered:
            failures.append(f"Forbidden overclaim present: {phrase}")
    if RAW_PATH_RE.search(combined):
        failures.append("Raw local path leaked in runtime action evidence files")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("UAA runtime action evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
