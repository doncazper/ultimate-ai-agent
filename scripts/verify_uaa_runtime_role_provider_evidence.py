#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/runtime/UAA_RUNTIME_ROLE_PROVIDER_EVIDENCE.md",
    "src/ultimate_ai_agent/core/providers/role_evidence.py",
    "src/ultimate_ai_agent/core/providers/control_plane.py",
    "scripts/dev/uaa_runtime.py",
    "tests/test_role_provider_evidence.py",
]

DOC_REQUIRED = [
    "UAA Runtime Role Provider Evidence",
    "does not copy external reference code",
    "advisory evidence only",
    "remote provider candidates remain blocked",
    "no provider SDK call",
    "no model invocation",
    "Control Center cannot mint authority",
    "inspect-role-provider-evidence",
]

CORE_REQUIRED = [
    "ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CONTRACT_REF",
    "RoleBasedModelProviderEvidenceReadModel",
    "RoleBasedProviderSelectionEvidence",
    "RoleProviderCandidateEvidence",
    "ModelProviderRole",
    "answerer",
    "planner",
    "reviewer",
    "synthesizer",
    "coder",
    "extractor",
    "safety_reviewer",
    "build_role_based_model_provider_evidence",
    "provider_sdk_call_enabled",
    "remote_model_call_enabled",
    "model_invocation_performed",
    "provider_payload_persisted",
]

CLI_REQUIRED = [
    "inspect-role-provider-evidence",
    "role_provider_evidence",
    "provider_model_call_performed",
]

TEST_REQUIRED = [
    "test_role_provider_evidence_covers_agent_roles_without_invocation",
    "test_role_provider_evidence_selects_local_advisory_and_blocks_remote",
    "test_role_provider_evidence_rejects_authority_drift",
    "test_role_provider_evidence_is_visible_in_control_center_api",
    "test_role_provider_evidence_cli_uses_same_safe_schema",
]

FORBIDDEN_OVERCLAIMS = [
    "provider/model call is enabled",
    "provider sdk call is enabled",
    "remote model calls are enabled",
    "model invocation is enabled",
    "provider output is authority",
    "production authority is enabled",
    "broad autonomy is enabled",
]

RAW_PATH_RE = re.compile(r"/Users/[^\s`)]+")


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

    doc = _read("docs/runtime/UAA_RUNTIME_ROLE_PROVIDER_EVIDENCE.md")
    core = _read("src/ultimate_ai_agent/core/providers/role_evidence.py")
    control_plane = _read("src/ultimate_ai_agent/core/providers/control_plane.py")
    cli = _read("scripts/dev/uaa_runtime.py")
    tests = _read("tests/test_role_provider_evidence.py")
    combined = "\n".join([doc, core, control_plane, cli, tests])

    failures.extend(_require_all(doc, DOC_REQUIRED, "doc evidence"))
    failures.extend(_require_all(core, CORE_REQUIRED, "core evidence"))
    failures.extend(_require_all(cli, CLI_REQUIRED, "CLI evidence"))
    failures.extend(_require_all(tests, TEST_REQUIRED, "test evidence"))

    lowered = combined.lower()
    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in lowered:
            failures.append(f"Forbidden overclaim present: {phrase}")
    if RAW_PATH_RE.search(combined):
        failures.append("Raw local path leaked in role-provider-evidence phase files")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("UAA runtime role provider evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
