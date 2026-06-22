#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md"
SCHEMA = ROOT / "docs/schemas/chat_local_operator_surface.schema.json"
CHAT_OPERATOR = ROOT / "src/ultimate_ai_agent/core/chat/operator_surface.py"
CHAT_INIT = ROOT / "src/ultimate_ai_agent/core/chat/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/OperatorFlowPanels.tsx"
FRONTEND_STATES = ROOT / "apps/control-center/src/components/OperatorSurfaceStates.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_074_chat_local_operator_surface.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_TRUTH_FIELDS = [
    "turn_ref",
    "route_ref",
    "model_ref",
    "runtime_truth",
    "auth_truth",
    "tool_denial_truth",
    "safe_evidence_refs",
    "plans_handoff_ref",
    "actions_handoff_ref",
    "blocked_state_refs",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-model-output-authority",
    "blocked-state:no-tool-execution",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-web-fetch",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-action-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-production-authority",
]
DENIED_POSTURE_FLAGS = [
    "response_visible",
    "prompt_body_visible",
    "completion_body_visible",
    "model_output_authority",
    "tool_execution_enabled",
    "memory_write_authorized",
    "context_injection_authorized",
    "provider_sdk_call_enabled",
    "web_fetch_enabled",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "action_execution_enabled",
    "approval_grant_capture_enabled",
    "production_authority_enabled",
]
FORBIDDEN_SNIPPETS = [
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
FORBIDDEN_PYTHON_RUNTIME_CALLS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "connector.write",
    "approval_authority.grant",
    "execute_action",
]
OLD_MISSING_MARKERS = [
    "contract-ref:chat-local-operator-surface-missing",
    "planned_blocked_until_uaa_p1_074",
    "chat-local-operator-surface-missing",
    "chat shell",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for snippet in snippets:
        if snippet.lower() in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {snippet!r}")


def _extract(today: dict) -> dict:
    return {
        "chat_local_operator_contract_ref": today[
            "chat_local_operator_contract_ref"
        ],
        "chat_local_operator_status": today["chat_local_operator_status"],
        "chat_local_operator_turn_ref": today["chat_local_operator_turn_ref"],
        "chat_local_operator_route_ref": today["chat_local_operator_route_ref"],
        "chat_local_operator_model_ref": today["chat_local_operator_model_ref"],
        "chat_local_operator_runtime_truth": today[
            "chat_local_operator_runtime_truth"
        ],
        "chat_local_operator_auth_truth": today["chat_local_operator_auth_truth"],
        "chat_local_operator_tool_denial_truth": today[
            "chat_local_operator_tool_denial_truth"
        ],
        "chat_local_operator_tool_denial_ref": today[
            "chat_local_operator_tool_denial_ref"
        ],
        "chat_local_operator_safe_evidence_refs": today[
            "chat_local_operator_safe_evidence_refs"
        ],
        "chat_local_operator_plans_handoff_ref": today[
            "chat_local_operator_plans_handoff_ref"
        ],
        "chat_local_operator_actions_handoff_ref": today[
            "chat_local_operator_actions_handoff_ref"
        ],
        "chat_local_operator_required_truth_fields": today[
            "chat_local_operator_required_truth_fields"
        ],
        "chat_local_operator_required_blocked_refs": today[
            "chat_local_operator_required_blocked_refs"
        ],
        "chat_local_operator_surface_bindings": today[
            "chat_local_operator_surface_bindings"
        ],
        "chat_local_operator_authority_posture": today[
            "chat_local_operator_authority_posture"
        ],
        "chat_local_operator_blocked_state_refs": today[
            "chat_local_operator_blocked_state_refs"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.chat import (
        CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS,
        CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS,
        CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
        ChatLocalOperatorTurnEnvelope,
        build_chat_local_operator_turn_envelope,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-074-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live Chat local operator schema error: {error.message}")

    if contract["chat_local_operator_contract_ref"] != (
        CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
    ):
        failures.append("live Chat local operator contract ref drifted")
    if contract["chat_local_operator_required_truth_fields"] != (
        CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS
    ):
        failures.append("live Chat local operator truth fields drifted")
    if contract["chat_local_operator_required_blocked_refs"] != (
        CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS
    ):
        failures.append("live Chat local operator blockers drifted")

    posture = contract["chat_local_operator_authority_posture"]
    if posture.get("safe_refs_only") is not True:
        failures.append("Chat local operator posture is not safe-ref-only")
    for flag in DENIED_POSTURE_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"Chat local operator posture has unsafe {flag}")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live Chat local operator contains {forbidden}")

    bindings = {
        binding["surface"]: binding
        for binding in contract["chat_local_operator_surface_bindings"]
    }
    if set(bindings) != {"Today", "Chat", "Plans", "Actions", "Evidence", "Memory"}:
        failures.append("Chat local operator surface bindings drifted")
    if bindings["Memory"]["feed_status"] != "blocked_until_cross_surface_memory_intake":
        failures.append("Chat local operator memory binding is not blocked")

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    chat_feed = module_feeds.get("Chat", {})
    if chat_feed.get("status") != "implemented_local_operator_surface_contract":
        failures.append("Today module feed does not mark Chat implemented")
    if CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF not in (
        chat_feed.get("current_feed_refs") or []
    ):
        failures.append("Today module feed missing Chat contract ref")

    timeline_kinds = {item["item_kind"] for item in today["evidence_timeline"]}
    if "chat_local_operator_turn_ref" not in timeline_kinds:
        failures.append("Evidence Timeline missing chat_local_operator_turn_ref")
    chat_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "chat_local_operator_turn_ref"
    )
    if chat_item["approval_ref_authority"] is not False:
        failures.append("Chat evidence item grants approval authority")
    if chat_item["rollback_execution_enabled"] is not False:
        failures.append("Chat evidence item enables rollback execution")
    if chat_item["memory_truth_authority"] is not False:
        failures.append("Chat evidence item treats memory/model output as truth")
    if set(REQUIRED_BLOCKED_REFS) - set(chat_item["blocked_states"]):
        failures.append("Chat evidence item missing blocked-state refs")

    envelope = build_chat_local_operator_turn_envelope(
        model_ref="model-ref:verifier",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
    )
    for flag in DENIED_POSTURE_FLAGS:
        if flag == "safe_refs_only":
            continue
        payload = envelope.model_dump(mode="json")
        if flag not in payload:
            continue
        payload[flag] = True
        try:
            ChatLocalOperatorTurnEnvelope(**payload)
        except ValidationError:
            continue
        failures.append(f"ChatLocalOperatorTurnEnvelope accepted unsafe {flag}=true")

    for unsafe_summary in [
        "raw prompt material",
        "raw response material",
        "provider payload material",
        "authorization material",
    ]:
        payload = envelope.model_dump(mode="json")
        payload["safe_summary"] = unsafe_summary
        try:
            ChatLocalOperatorTurnEnvelope(**payload)
        except ValidationError:
            continue
        failures.append(f"ChatLocalOperatorTurnEnvelope accepted {unsafe_summary}")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))

    required_snippets = [
        "contract-ref:chat-local-operator-surface:v1",
        "turn_ref",
        "runtime_truth",
        "auth_truth",
        "tool_denial_truth",
        "plans_handoff_ref",
        "actions_handoff_ref",
        "blocked-state:no-tool-execution",
        "blocked-state:no-memory-write",
        "blocked-state:no-action-execution",
        "model_output_authority",
        "tool_execution_enabled",
        "memory_write_authorized",
        "approval_grant_capture_enabled",
    ]
    _require(
        CHAT_OPERATOR,
        [
            "CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF",
            "ChatLocalOperatorTurnEnvelope",
            "build_chat_local_operator_turn_envelope",
            "UNSAFE_CHAT_OPERATOR_TEXT_FRAGMENTS",
        ],
        failures,
    )
    _require(
        FOUNDER_LOOP,
        ["CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF", "chat_local_operator_status"],
        failures,
    )
    _require(CHAT_INIT, ["ChatLocalOperatorTurnEnvelope"], failures)
    _require(FRONTEND_TYPES, ["chat_local_operator_contract_ref"], failures)
    _require(FRONTEND_CLIENT, ["CHAT_OPERATOR_CONTRACT_REF"], failures)
    _require(FRONTEND_PANEL, ["Chat Local Operator", "toolDenialTruth"], failures)
    _require(FRONTEND_STATES, ["Chat Local Operator"], failures)
    _require(FRONTEND_MOCK, required_snippets[:2], failures)
    _require(FOCUSED_TEST, ["CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF"], failures)
    _require(STORAGE_TEST, ["CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF"], failures)
    _require(API_TEST, ["CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF"], failures)
    _require(APP_TEST, ["Chat Local Operator"], failures)
    _require(SCHEMA, ["chat_local_operator_contract_ref"], failures)
    _require(CONTRACT_DOC, required_snippets, failures)

    for path in [
        CONTRACT_DOC,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_STATES,
        FRONTEND_MOCK,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
    ]:
        _require_absent(path, OLD_MISSING_MARKERS, failures)

    _require_absent(CHAT_OPERATOR, FORBIDDEN_PYTHON_RUNTIME_CALLS, failures)
    _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"[UAA-P1-074 verifier] {failure}")
        return 1

    print("[UAA-P1-074 verifier] Chat local operator checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
