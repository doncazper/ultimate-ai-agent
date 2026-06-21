#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md"
SCHEMA = ROOT / "docs/schemas/today_product_spine_contract.schema.json"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"


REQUIRED_DOC_SNIPPETS = [
    "Loop visibility is necessary but not sufficient for completion.",
    "standalone_complete_allowed: false",
    "does not add a new route",
    "raw prompts",
    "raw responses",
    "provider payloads",
    "public beta",
    "production authority",
]

REQUIRED_PAYLOAD_SNIPPETS = [
    "TODAY_PRODUCT_SPINE_CONTRACT_REF",
    "TODAY_PRODUCT_SPINE_REQUIRED_SIGNALS",
    "TODAY_PRODUCT_SPINE_MODULE_FEEDS",
    '"product_spine_contract_ref"',
    '"required_loop_surfaces"',
    '"required_today_signals"',
    '"module_feed_contract"',
    '"module_completion_contract"',
    '"plan_action_state"',
    '"stale_source_posture"',
    '"next_safe_actions"',
]

REQUIRED_TEST_SNIPPETS = [
    "TODAY_PRODUCT_SPINE_CONTRACT_REF",
    '"required_loop_surfaces"',
    '"required_today_signals"',
    '"module_feed_contract"',
    '"visibility_is_sufficient_for_completion"',
    '"standalone_module_complete_allowed"',
    '"execution_authorized"',
    '"connector_runtime_enabled"',
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def main() -> int:
    failures: list[str] = []

    for path in [
        CONTRACT_DOC,
        SCHEMA,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    _require(CONTRACT_DOC, REQUIRED_DOC_SNIPPETS, failures)
    _require(FOUNDER_LOOP, REQUIRED_PAYLOAD_SNIPPETS, failures)
    _require(
        FRONTEND_TYPES,
        [
            "product_spine_contract_ref",
            "required_loop_surfaces",
            "required_today_signals",
            "module_feed_contract",
            "module_completion_contract",
            "plan_action_state",
            "stale_source_posture",
            "next_safe_actions",
        ],
        failures,
    )
    _require(FRONTEND_PANEL, ["Product spine contract", "Module feed contract"], failures)
    _require(STORAGE_TEST, REQUIRED_TEST_SNIPPETS, failures)
    _require(API_TEST, REQUIRED_TEST_SNIPPETS, failures)
    _require(APP_TEST, ["Product spine contract", "Module feed contract"], failures)

    schema = json.loads(_read(SCHEMA))
    required = set(schema.get("required", []))
    expected_required = {
        "product_spine_contract_ref",
        "required_loop_surfaces",
        "required_today_signals",
        "module_feed_contract",
        "module_completion_contract",
        "plan_action_state",
        "stale_source_posture",
        "next_safe_actions",
    }
    missing_required = expected_required - required
    if missing_required:
        failures.append(f"schema missing required fields: {sorted(missing_required)}")

    completion = schema["properties"]["module_completion_contract"]["properties"]
    if completion["visibility_is_sufficient_for_completion"].get("const") is not False:
        failures.append("schema must require visibility_is_sufficient_for_completion false")
    if completion["standalone_module_complete_allowed"].get("const") is not False:
        failures.append("schema must require standalone_module_complete_allowed false")

    route_file = _read(ROOT / "src/ultimate_ai_agent/api/founder_loop.py")
    if '@router.get("/today/summary"' not in route_file:
        failures.append("existing Today summary route is missing")
    if 'router.post("/today' in route_file or 'router.put("/today' in route_file:
        failures.append("Today product spine must not add mutating Today routes")

    lowered_doc = _read(CONTRACT_DOC).lower()
    unsafe_claims = [
        "production ready",
        "public beta ready",
        "public distribution ready",
        "connector writes enabled",
        "model output is authority",
    ]
    for claim in unsafe_claims:
        if claim in lowered_doc:
            failures.append(f"contract doc contains unsafe claim: {claim}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("UAA-P1-068 Today product spine contract verification PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
