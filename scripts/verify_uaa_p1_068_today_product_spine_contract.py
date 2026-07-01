#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md"
SCHEMA = ROOT / "docs/schemas/today_product_spine_contract.schema.json"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
TODAY_LOOP_CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/today_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
DOCUMENTATION_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
TODAY_LOOP_TEST = ROOT / "tests/test_today_loop_tightening.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
CLI_INSPECT = ROOT / "scripts/inspect_today_loop.py"


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
    "build_today_loop_read_model",
    '"today_loop_tightening_contract_ref"',
    '"today_loop_read_model"',
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

REQUIRED_TODAY_LOOP_TEST_SNIPPETS = [
    "TODAY_LOOP_TIGHTENING_CONTRACT_REF",
    '"today_loop_read_model"',
    "test_today_loop_storage_summary_returns_backend_owned_read_model",
    "test_today_loop_api_summary_returns_backend_owned_read_model",
    "test_today_loop_cli_inspection_is_read_only_and_redacted",
    "test_today_loop_read_model_redacts_dirty_memory_blocker_text",
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
        TODAY_LOOP_CONTRACT,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_CLIENT,
        DOCUMENTATION_INDEX,
        STORAGE_TEST,
        API_TEST,
        TODAY_LOOP_TEST,
        APP_TEST,
        CLI_INSPECT,
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
        TODAY_LOOP_CONTRACT,
        [
            "TODAY_LOOP_TIGHTENING_CONTRACT_REF",
            "TodayLoopReadModel",
            "build_today_loop_read_model",
            "action_execution_enabled: bool = False",
            "connector_runtime_enabled: bool = False",
            "runtime_model_calls_enabled: bool = False",
            "automatic_memory_write_authorized: bool = False",
            "context_injection_authorized: bool = False",
        ],
        failures,
    )
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
            "FounderLoopTodayLoopReadModel",
            "today_loop_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Product spine contract",
            "Module feed contract",
            "TodayLoopReadModelPanel",
            "Today decisions first",
            "backend digest missing",
            "Review and track",
        ],
        failures,
    )
    if "Execute and track" in _read(FRONTEND_PANEL):
        failures.append("Today command deck must not use broad 'Execute and track' wording")
    _require(
        FRONTEND_CLIENT,
        [
            "normalizeFounderToday",
            "fallbackWithoutDigest",
            "delete normalized.today_loop_read_model",
            "today_loop_tightening_contract_ref",
        ],
        failures,
    )
    if "143-route inventory fixture" in _read(DOCUMENTATION_INDEX):
        failures.append("docs/DOCUMENTATION_INDEX.md still references the stale 143-route inventory")
    _require(STORAGE_TEST, REQUIRED_TEST_SNIPPETS, failures)
    _require(API_TEST, REQUIRED_TEST_SNIPPETS, failures)
    _require(TODAY_LOOP_TEST, REQUIRED_TODAY_LOOP_TEST_SNIPPETS, failures)
    _require(
        APP_TEST,
        [
            "Product spine contract",
            "Module feed contract",
            "Today decisions first",
            "does not backfill the Today loop digest",
            "Execute and track",
        ],
        failures,
    )
    _require(
        CLI_INSPECT,
        [
            "repo-local-command:inspect-today-loop",
            "TODAY_LOOP_TIGHTENING_CONTRACT_REF",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "raw_paths_omitted",
        ],
        failures,
    )

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
    properties = schema.get("properties", {})
    if "today_loop_read_model" not in properties:
        failures.append("schema missing optional today_loop_read_model property")
    else:
        today_loop = properties["today_loop_read_model"]["properties"]
        for field_name in [
            "action_execution_enabled",
            "connector_runtime_enabled",
            "source_refresh_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            if today_loop[field_name].get("const") is not False:
                failures.append(f"schema must require {field_name} false")
        for field_name in [
            "local_read_model_only",
            "safe_refs_only",
            "backend_owned",
        ]:
            if today_loop[field_name].get("const") is not True:
                failures.append(f"schema must require {field_name} true")
        for field_name in [
            "follow_up_refs",
            "stale_or_deferred_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            if field_name not in today_loop:
                failures.append(f"schema today_loop_read_model missing {field_name}")
        lane_schema = today_loop["lanes"]["items"]
        digest_item_schema = today_loop["digest_items"]["items"]
        if lane_schema.get("additionalProperties") is not False:
            failures.append("schema today_loop_read_model.lanes items must forbid extras")
        if digest_item_schema.get("additionalProperties") is not False:
            failures.append("schema today_loop_read_model.digest_items must forbid extras")
        for field_name in [
            "lane_id",
            "label",
            "status",
            "count",
            "item_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
            "next_safe_action",
            "review_only",
        ]:
            if field_name not in set(lane_schema.get("required", [])):
                failures.append(f"schema lane items missing required {field_name}")
        for field_name in [
            "item_ref",
            "lane_id",
            "surface",
            "title",
            "state_label",
            "status",
            "priority",
            "safe_summary",
            "reason",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
            "stale_state",
            "review_required",
            "next_safe_action",
            "authority_boundary",
            "safe_refs_only",
            "content_untrusted",
            "action_execution_enabled",
            "connector_runtime_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            if field_name not in set(digest_item_schema.get("required", [])):
                failures.append(f"schema digest items missing required {field_name}")
        for field_name in [
            "action_execution_enabled",
            "connector_runtime_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            if digest_item_schema["properties"][field_name].get("const") is not False:
                failures.append(f"schema digest items must require {field_name} false")

    completion = schema["properties"]["module_completion_contract"]["properties"]
    if completion["visibility_is_sufficient_for_completion"].get("const") is not False:
        failures.append("schema must require visibility_is_sufficient_for_completion false")
    if completion["standalone_module_complete_allowed"].get("const") is not False:
        failures.append("schema must require standalone_module_complete_allowed false")

    route_file = _read(ROOT / "src/ultimate_ai_agent/api/founder_loop.py")
    if '@router.get("/today/summary"' not in route_file:
        failures.append("existing Today summary route is missing")
    allowed_today_mutation = '@router.post("/today/action-envelope", response_model=ResultEnvelope)'
    today_mutation_lines = [
        line.strip()
        for line in route_file.splitlines()
        if (
            'router.post("/today' in line
            or 'router.put("/today' in line
            or 'router.patch("/today' in line
            or 'router.delete("/today' in line
        )
    ]
    unexpected_today_mutations = [
        line for line in today_mutation_lines if line != allowed_today_mutation
    ]
    if route_file.count(allowed_today_mutation) != 1:
        failures.append("Today action-envelope route must remain exactly one scoped mutating route")
    if unexpected_today_mutations:
        failures.append(
            "Today product spine must not add mutating Today routes beyond "
            "the scoped action-envelope contract"
        )

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
