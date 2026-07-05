#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/runtime/UAA_GOATCITADEL_RUNTIME_PREPARED_TURN_LOOP.md",
    "src/ultimate_ai_agent/core/decision_router/prepared_turn.py",
    "scripts/dev/uaa_turn_router.py",
    "src/ultimate_ai_agent/api/routes/runtime_pilot_service.py",
    "tests/test_prepared_turn.py",
]

DOC_REQUIRED = [
    "UAA GoatCitadel Runtime Prepared Turn Loop",
    "does not copy GoatCitadel code",
    "does not add runtime authority",
    "Prepared turns never persist raw prompt text",
    "Control Center cannot mint authority",
    "Route decisions are not approval",
    "GET /api/runtime/prepared-turn",
    "prepare-turn",
]

CORE_REQUIRED = [
    "PREPARED_TURN_SCHEMA_VERSION",
    "PreparedTurn",
    "PreparedTurnBranch",
    "PreparedTurnReadiness",
    "PreparedTurnNextAction",
    "prepare_turn",
    "build_sample_prepared_turns",
    "base_answer",
    "answer_with_reviewed_memory",
    "prepare_tool_or_action",
    "approval_required",
    "blocked_unsafe",
    "ask_clarifying_question",
    "raw_prompt_persisted",
    "raw_model_output_persisted",
    "context_injection_performed",
    "model_call_performed",
    "tool_execution_performed",
    "action_execution_performed",
]

CLI_API_REQUIRED = [
    "prepare-turn",
    "/prepared-turn",
    "api_runtime_prepared_turn",
]

TEST_REQUIRED = [
    "test_prepared_turn_direct_answer_has_no_memory_tools_or_execution",
    "test_prepared_turn_memory_readiness_uses_reviewed_refs_only",
    "test_prepared_turn_tool_action_readiness_is_proposal_only",
    "test_prepared_turn_approval_required_has_exact_envelope_posture",
    "test_prepared_turn_blocks_base_answer_bypass_for_payment_action",
    "test_prepared_turn_rejects_raw_persistence_or_execution_flags",
    "test_turn_router_cli_prepares_turn_without_raw_prompt",
    "test_runtime_api_exposes_prepared_turn_read_model",
]

FORBIDDEN_OVERCLAIMS = [
    "runtime authority is enabled",
    "provider/model call is enabled",
    "tool execution is enabled",
    "action execution is enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "production authority is enabled",
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

    doc = _read("docs/runtime/UAA_GOATCITADEL_RUNTIME_PREPARED_TURN_LOOP.md")
    core = _read("src/ultimate_ai_agent/core/decision_router/prepared_turn.py")
    cli = _read("scripts/dev/uaa_turn_router.py")
    api = _read("src/ultimate_ai_agent/api/routes/runtime_pilot_service.py")
    tests = _read("tests/test_prepared_turn.py")
    combined = "\n".join([doc, core, cli, api, tests])

    failures.extend(_require_all(doc, DOC_REQUIRED, "doc evidence"))
    failures.extend(_require_all(core, CORE_REQUIRED, "core evidence"))
    failures.extend(_require_all(cli + api, CLI_API_REQUIRED, "CLI/API evidence"))
    failures.extend(_require_all(tests, TEST_REQUIRED, "test evidence"))

    lowered = combined.lower()
    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in lowered:
            failures.append(f"Forbidden overclaim present: {phrase}")
    if RAW_PATH_RE.search(combined):
        failures.append("Raw local path leaked in prepared-turn phase files")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("UAA GoatCitadel runtime prepared turn loop verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
