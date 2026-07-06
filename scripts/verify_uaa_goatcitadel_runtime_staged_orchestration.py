#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/runtime/UAA_GOATCITADEL_RUNTIME_STAGED_ORCHESTRATION_ENGINE.md",
    "src/ultimate_ai_agent/core/execution/staged_orchestration.py",
    "scripts/dev/uaa_runtime.py",
    "src/ultimate_ai_agent/api/routes/runtime_pilot_service.py",
    "tests/test_staged_orchestration_engine.py",
]

DOC_REQUIRED = [
    "UAA GoatCitadel Runtime Staged Orchestration Engine",
    "does not copy GoatCitadel code",
    "does not add runtime authority",
    "Control Center cannot mint authority",
    "GET /api/runtime/staged-orchestration",
    "inspect-staged-orchestration",
    "autonomous worker",
    "hidden model call",
    "unrestricted command execution",
    "browser automation",
    "connector write",
    "production authority",
    "raw payload persistence",
]

CORE_REQUIRED = [
    "STAGED_ORCHESTRATION_SCHEMA_VERSION",
    "StagedOrchestrationReadModel",
    "StagedOrchestrationPlan",
    "StagedOrchestrationStage",
    "StagedOrchestrationStep",
    "StagedOrchestrationCallbackRef",
    "StagedOrchestrationCheckpoint",
    "StagedOrchestrationDegradedHandoff",
    "StagedOrchestrationRuntimeCommandStepResult",
    "execute_approved_runtime_command_step",
    "approved_runtime_command_execution_enabled",
    "focused_pytest",
    "repo_verifier",
    "frontend_check",
    "repo_doctor",
    "validate_staged_orchestration_plan",
    "replay_staged_orchestration_checkpoint",
    "reason-ref:staged-orchestration:missing-dependency",
    "reason-ref:staged-orchestration:same-stage-dependency",
    "reason-ref:staged-orchestration:future-stage-dependency",
    "reason-ref:staged-orchestration:dependency-cycle",
    "reason-ref:staged-orchestration:degraded-handoff-missing",
    "reason-ref:staged-orchestration:downstream-not-skipped",
    "reason-ref:staged-orchestration:runtime-authority-not-promoted",
]

CLI_API_REQUIRED = [
    "inspect-staged-orchestration",
    "build_sample_staged_orchestration_read_model",
    "/staged-orchestration",
    "api_runtime_staged_orchestration",
]

TEST_REQUIRED = [
    "test_sample_staged_orchestration_read_model_is_safe_and_waiting",
    "test_dependency_validation_rejects_missing_same_stage_future_and_cycle",
    "test_degraded_step_requires_handoff",
    "test_downstream_of_failed_dependency_must_skip_block_or_degrade",
    "test_checkpoint_replay_is_idempotent_and_conflict_bound",
    "test_approved_runtime_command_step_executes_through_runtime_gateway",
    "expected_argv_suffix",
    "test_runtime_command_step_rejects_unpromoted_intent",
    "test_runtime_command_step_without_plan_enablement_is_rejected",
    "test_effectful_callback_and_raw_metadata_are_rejected",
    "test_runtime_cli_inspects_staged_orchestration_safe_json",
    "test_runtime_api_exposes_staged_orchestration_read_model",
]

FORBIDDEN_OVERCLAIMS = [
    "runtime authority is enabled",
    "autonomous workers are enabled",
    "hidden model calls are enabled",
    "unrestricted command execution is enabled",
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

    doc = _read("docs/runtime/UAA_GOATCITADEL_RUNTIME_STAGED_ORCHESTRATION_ENGINE.md")
    core = _read("src/ultimate_ai_agent/core/execution/staged_orchestration.py")
    cli = _read("scripts/dev/uaa_runtime.py")
    api = _read("src/ultimate_ai_agent/api/routes/runtime_pilot_service.py")
    tests = _read("tests/test_staged_orchestration_engine.py")

    failures.extend(_require_all(doc, DOC_REQUIRED, "doc evidence"))
    failures.extend(_require_all(core, CORE_REQUIRED, "core contract evidence"))
    failures.extend(_require_all(cli + api, CLI_API_REQUIRED, "CLI/API evidence"))
    failures.extend(_require_all(tests, TEST_REQUIRED, "test evidence"))

    combined = "\n".join([doc, core, cli, api, tests])
    lowered = combined.lower()
    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in lowered:
            failures.append(f"Forbidden overclaim present: {phrase}")
    if RAW_PATH_RE.search(combined):
        failures.append("Raw local path leaked in staged orchestration phase files")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("UAA GoatCitadel runtime staged orchestration engine verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
