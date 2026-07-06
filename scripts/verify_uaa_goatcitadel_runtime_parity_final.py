#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/runtime/UAA_GOATCITADEL_RUNTIME_PARITY_FINAL_HARDENING.md",
    "docs/runtime/UAA_GOATCITADEL_RUNTIME_PARITY_SCORECARD.md",
    "src/ultimate_ai_agent/core/control_center/runtime_parity_loop.py",
    "src/ultimate_ai_agent/core/control_center/runtime_action_bridge.py",
    "src/ultimate_ai_agent/api/routes/runtime_pilot_service.py",
    "scripts/dev/uaa_runtime.py",
    "tests/test_runtime_parity_loop_read_model.py",
]

DOC_REQUIRED = [
    "UAA GoatCitadel Runtime Parity Final Hardening",
    "GET /api/runtime/parity-loop",
    "inspect-parity-loop",
    "Control Center cannot mint",
    "Still blocked",
    "runtime model calls",
    "provider SDK calls",
    "browser automation",
    "connector writes",
    "unrestricted shell",
    "production authority",
]

CORE_REQUIRED = [
    "RuntimeParityLoopReadModel",
    "build_runtime_parity_loop_read_model",
    "RUNTIME_PARITY_LOOP_CONTRACT_REF",
    "runtime-loop-stage-ref:prepared-turn",
    "runtime-loop-stage-ref:signed-evidence",
    "execution_performed_by_read_model",
    "control_center_mints_authority",
    "broad_runtime_authority_enabled",
    "raw_prompt_persisted",
]

SURFACE_REQUIRED = [
    "@router.get(\"/parity-loop\"",
    "api_runtime_parity_loop",
    "inspect-parity-loop",
    "runtime_parity_loop_api_ref",
    "runtime_parity_loop_cli_ref",
    "runtime_parity_loop_stage_refs",
    "GET /api/runtime/parity-loop",
]

TEST_REQUIRED = [
    "test_runtime_parity_loop_read_model_is_backend_owned_and_safe_ref_only",
    "test_runtime_parity_loop_links_receipt_and_signed_evidence",
    "test_runtime_parity_loop_api_and_cli_are_safe_ref_inspection",
    "test_runtime_action_bridge_projects_runtime_parity_loop_refs",
]

FORBIDDEN = [
    "broad runtime authority is enabled",
    "provider sdk calls are enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "unrestricted shell is enabled",
    "production authority is enabled",
]

RAW_PATH_RE = re.compile(r"/Users/[^\s`)]*")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _missing(text: str, needles: list[str], label: str) -> list[str]:
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

    doc = _read("docs/runtime/UAA_GOATCITADEL_RUNTIME_PARITY_FINAL_HARDENING.md")
    scorecard = _read("docs/runtime/UAA_GOATCITADEL_RUNTIME_PARITY_SCORECARD.md")
    core = _read("src/ultimate_ai_agent/core/control_center/runtime_parity_loop.py")
    bridge = _read("src/ultimate_ai_agent/core/control_center/runtime_action_bridge.py")
    api = _read("src/ultimate_ai_agent/api/routes/runtime_pilot_service.py")
    cli = _read("scripts/dev/uaa_runtime.py")
    tests = _read("tests/test_runtime_parity_loop_read_model.py")
    combined = "\n".join([doc, scorecard, core, bridge, api, cli, tests])

    failures.extend(_missing(doc + scorecard, DOC_REQUIRED, "doc evidence"))
    failures.extend(_missing(core, CORE_REQUIRED, "core evidence"))
    failures.extend(_missing(api + cli + bridge, SURFACE_REQUIRED, "surface evidence"))
    failures.extend(_missing(tests, TEST_REQUIRED, "test evidence"))

    lowered = combined.lower()
    for phrase in FORBIDDEN:
        if phrase in lowered:
            failures.append(f"Forbidden overclaim present: {phrase}")
    if RAW_PATH_RE.search(combined):
        failures.append("Raw local path leaked in runtime parity final files")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("UAA GoatCitadel runtime parity final hardening verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
