#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md"
SCHEMA = ROOT / "docs/schemas/evidence_history_grammar.schema.json"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_ROUTE = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
ROUTE_STATUS_MANIFEST = ROOT / "docs/control_center/route_status_manifest.json"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"


GRAMMAR_KEYS = {
    "proposed",
    "approved",
    "happened",
    "changed",
    "undoable",
    "stale",
    "blocked",
}

REQUIRED_DOC_SNIPPETS = [
    "contract-ref:evidence-history-grammar:v1",
    "What was proposed?",
    "What was approved?",
    "What happened?",
    "What changed?",
    "What can be undone?",
    "What is stale?",
    "What remains blocked?",
    "Approval refs are identifiers only",
    "Rollback refs describe undo posture only and do not execute rollback",
    "safe refs and redacted summaries only",
    "public beta",
    "production authority",
]

REQUIRED_SOURCE_SNIPPETS = [
    "EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF",
    "EVIDENCE_HISTORY_GRAMMAR_KEYS",
    "EVIDENCE_HISTORY_GRAMMAR_REQUIRED_QUESTIONS",
    "EVIDENCE_HISTORY_SURFACE_BINDINGS",
    "history_answers",
    "approval_ref_authority",
    "rollback_execution_enabled",
    "memory_truth_authority",
    "context_injection_authorized",
    "raw_evidence_included",
]

FORBIDDEN_SERIALIZED_SNIPPETS = [
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _extract_evidence_history(today: dict) -> dict:
    return {
        "evidence_history_contract_ref": today["evidence_history_contract_ref"],
        "evidence_history_required_states": today["evidence_history_required_states"],
        "evidence_history_required_questions": today[
            "evidence_history_required_questions"
        ],
        "evidence_history_surface_bindings": today[
            "evidence_history_surface_bindings"
        ],
        "evidence_timeline": today["evidence_timeline"],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from ultimate_ai_agent.core.storage import (
        EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
        FounderLoopRepository,
    )

    with tempfile.TemporaryDirectory(prefix="uaa-p1-069-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    grammar = _extract_evidence_history(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(grammar), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live evidence history schema error: {error.message}")

    if grammar["evidence_history_contract_ref"] != EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF:
        failures.append("live evidence history contract ref drifted")
    if set(grammar["evidence_history_required_states"]) != GRAMMAR_KEYS:
        failures.append("live evidence history states drifted")
    if not grammar["evidence_timeline"]:
        failures.append("live evidence timeline is empty")

    serialized = json.dumps(grammar, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SERIALIZED_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live evidence history contains unsafe snippet: {forbidden}")

    for item in grammar["evidence_timeline"]:
        if set(item.get("history_answers", {})) != GRAMMAR_KEYS:
            failures.append(f"{item.get('timeline_item_ref')} missing grammar answers")
        for flag in [
            "approval_ref_authority",
            "rollback_execution_enabled",
            "memory_truth_authority",
            "context_injection_authorized",
            "raw_evidence_included",
        ]:
            if item.get(flag) is not False:
                failures.append(f"{item.get('timeline_item_ref')} has unsafe {flag}")
        approved = item["history_answers"]["approved"]["answer"].lower()
        undoable = item["history_answers"]["undoable"]["answer"].lower()
        if "authority" not in approved and "approved" in approved:
            failures.append(f"{item['timeline_item_ref']} approved answer is ambiguous")
        if "execute rollback" in undoable and "do not execute rollback" not in undoable:
            failures.append(f"{item['timeline_item_ref']} undo answer implies rollback")

    unsafe = dict(grammar)
    unsafe["evidence_timeline"] = [
        dict(grammar["evidence_timeline"][0], approval_ref_authority=True)
    ]
    if not list(validator.iter_errors(unsafe)):
        failures.append("schema accepted approval_ref_authority=true")

    unsafe = dict(grammar)
    unsafe["evidence_timeline"] = [
        dict(grammar["evidence_timeline"][0], raw_evidence_included=True)
    ]
    if not list(validator.iter_errors(unsafe)):
        failures.append("schema accepted raw_evidence_included=true")


def _validate_route_status_manifest(failures: list[str]) -> None:
    manifest = json.loads(_read(ROUTE_STATUS_MANIFEST))
    evidence_action = next(
        (
            action
            for action in manifest.get("visible_actions", [])
            if action.get("action_id") == "navigate-evidence"
        ),
        None,
    )
    if not evidence_action:
        failures.append("route status manifest missing navigate-evidence")
        return

    expected_route = {
        "method": "GET",
        "path": "/control-center/today/summary",
        "operation_id": "get_control_center_today_summary",
        "side_effect_class": "local_dev_workspace_only",
    }
    if expected_route not in evidence_action.get("backend_routes", []):
        failures.append("navigate-evidence missing Today summary backend route")


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT_DOC,
        SCHEMA,
        FOUNDER_LOOP,
        API_ROUTE,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        APP_TEST,
        ROUTE_STATUS_MANIFEST,
        STORAGE_TEST,
        API_TEST,
        ROUTE_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    _require(CONTRACT_DOC, REQUIRED_DOC_SNIPPETS, failures)
    _require(FOUNDER_LOOP, REQUIRED_SOURCE_SNIPPETS, failures)
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopEvidenceHistoryQuestion",
            "FounderLoopEvidenceHistoryAnswers",
            "evidence_history_contract_ref",
            "evidence_history_required_states",
            "evidence_history_required_questions",
            "evidence_history_surface_bindings",
            "approval_ref_authority",
            "rollback_execution_enabled",
            "memory_truth_authority",
            "context_injection_authorized",
            "raw_evidence_included",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Evidence history grammar",
            "History answers",
            "Approval ref authority",
            "Rollback execution",
            "Raw evidence included",
        ],
        failures,
    )
    _require(
        APP_TEST,
        [
            "Evidence history grammar",
            "What was proposed?",
            "contract-ref:evidence-history-grammar:v1",
            "Approval ref authority",
            "Rollback execution",
        ],
        failures,
    )
    _require(
        STORAGE_TEST,
        [
            "EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF",
            "approval_ref_authority",
            "rollback_execution_enabled",
            "raw_evidence_included",
            "rejects_authority_creep",
        ],
        failures,
    )
    _require(API_TEST, ["EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF"], failures)
    _require(ROUTE_TEST, ["/control-center/today/summary"], failures)

    route_file = _read(API_ROUTE)
    if '@router.get("/today/summary"' not in route_file:
        failures.append("Today summary route is missing")
    for unsafe_route in ['@router.post("/evidence', '@router.put("/evidence']:
        if unsafe_route in route_file:
            failures.append(f"evidence history must not add mutating route: {unsafe_route}")

    schema = json.loads(_read(SCHEMA))
    if schema.get("additionalProperties") is not False:
        failures.append("schema root must forbid additional properties")
    item_schema = schema["$defs"]["evidence_timeline_item"]
    if item_schema.get("additionalProperties") is not False:
        failures.append("timeline item schema must forbid additional properties")
    for flag in [
        "approval_ref_authority",
        "rollback_execution_enabled",
        "memory_truth_authority",
        "context_injection_authorized",
        "raw_evidence_included",
    ]:
        if item_schema["properties"][flag].get("const") is not False:
            failures.append(f"schema must require {flag}=false")

    _validate_live_contract(schema, failures)
    _validate_route_status_manifest(failures)

    lowered_doc = _read(CONTRACT_DOC).lower()
    unsafe_claims = [
        "production ready",
        "public beta ready",
        "public distribution ready",
        "evidence history complete product workflow",
        "model output is authority",
    ]
    for claim in unsafe_claims:
        if claim in lowered_doc:
            failures.append(f"contract doc contains unsafe claim: {claim}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("UAA-P1-069 Evidence history grammar verification PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
