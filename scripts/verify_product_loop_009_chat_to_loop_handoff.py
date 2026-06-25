#!/usr/bin/env python3
"""Verify Product Loop 009 Chat-to-loop handoff safety posture."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest  # noqa: E402
from ultimate_ai_agent.core.control_center.chat_to_loop_handoff import (  # noqa: E402
    CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
    CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS,
    CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE,
    CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS,
    ChatToLoopHandoffReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


CONTRACT = SRC / "ultimate_ai_agent/core/control_center/chat_to_loop_handoff.py"
STORAGE = SRC / "ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_chat_to_loop_handoff.py"
FOCUSED_TEST = ROOT / "tests/test_chat_to_loop_handoff_v1.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_OPERATOR = ROOT / "apps/control-center/src/components/OperatorFlowPanels.tsx"
FRONTEND_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_009_CHAT_TO_LOOP_HANDOFF.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"

DENIED_FLAGS = [
    "model_output_authority",
    "direct_memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "tool_execution_enabled",
    "connector_write_enabled",
    "action_execution_enabled",
    "plan_execution_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "live_web_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "production_authority_enabled",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, fragments: list[str], failures: list[str]) -> None:
    text = _read(path)
    for fragment in fragments:
        if fragment not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {fragment!r}")


def _require_absent(path: Path, fragments: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for fragment in fragments:
        if fragment.lower() in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {fragment!r}")


def _turn_request() -> ChatTurnReceiptRequest:
    return ChatTurnReceiptRequest(
        turn_ref="chat-turn:product-loop-009-verifier",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref="safe-summary-ref:chat-to-loop-verifier",
        evidence_refs=["evidence-ref:chat-to-loop:verifier"],
        metadata_refs=["metadata-ref:chat-to-loop:verifier"],
    )


def _assert_read_model(model: dict[str, Any], failures: list[str]) -> None:
    parsed = ChatToLoopHandoffReadModel(**model)
    if parsed.contract_ref != CHAT_TO_LOOP_HANDOFF_CONTRACT_REF:
        failures.append("Chat-to-loop contract ref drifted")
    if parsed.source != CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE:
        failures.append("Chat-to-loop source drifted")
    if tuple(parsed.outcome_kinds) != CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS:
        failures.append("Chat-to-loop outcome kinds drifted")
    if {outcome.outcome_kind for outcome in parsed.outcomes} != set(
        CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS
    ):
        failures.append("Chat-to-loop outcomes are missing a canonical kind")
    missing = set(CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS) - set(
        parsed.blocked_state_refs
    )
    if missing:
        failures.append("Chat-to-loop read model missing blocked refs")
    for flag in DENIED_FLAGS:
        if getattr(parsed, flag):
            failures.append(f"Chat-to-loop read model enables {flag}")


def _validate_live(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-009-live-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        turn_receipt = repo.record_chat_turn_receipt(
            request=_turn_request(),
            idempotency_key_ref="idempotency-ref:chat-to-loop-verifier-turn",
        )
        repo.record_chat_handoff(
            turn_ref=turn_receipt["turn_ref"],
            request=ChatHandoffRequest(
                handoff_target="actions",
                decision_reason_ref="decision-reason-ref:chat-to-loop-verifier-actions",
            ),
            idempotency_key_ref="idempotency-ref:chat-to-loop-verifier-actions",
        )
        repo.record_chat_handoff(
            turn_ref=turn_receipt["turn_ref"],
            request=ChatHandoffRequest(
                handoff_target="plans",
                decision_reason_ref="decision-reason-ref:chat-to-loop-verifier-plans",
            ),
            idempotency_key_ref="idempotency-ref:chat-to-loop-verifier-plans",
        )
        read_model = repo.chat_to_loop_handoff()["chat_to_loop_handoff_read_model"]
        _assert_read_model(read_model, failures)
        today = repo.today_summary()
        inbox = repo.actions_inbox()
        briefing = repo.morning_briefing()
        for surface_name, payload in {
            "Today": today,
            "Action Inbox": inbox,
            "Morning Briefing": briefing,
        }.items():
            if "chat_to_loop_handoff_read_model" not in payload:
                failures.append(f"{surface_name} missing Chat-to-loop read model")
        for flag in DENIED_FLAGS:
            payload = dict(read_model)
            payload[flag] = True
            try:
                ChatToLoopHandoffReadModel(**payload)
            except ValueError:
                continue
            failures.append(f"Chat-to-loop accepted unsafe flag {flag}")
        for unsafe_ref in (
            "evidence-ref:alice@example.com",
            "evidence-ref:workstation.local",
            "evidence-ref:relative/path/project",
            "evidence-ref:relative\\path\\project",
        ):
            payload = dict(read_model)
            payload["evidence_refs"] = [unsafe_ref]
            try:
                ChatToLoopHandoffReadModel(**payload)
            except ValueError:
                continue
            failures.append(f"Chat-to-loop accepted unsafe ref {unsafe_ref}")


def _validate_cli(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-009-cli-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        repo = FounderLoopRepository(state_dir)
        repo.record_chat_turn_receipt(
            request=_turn_request(),
            idempotency_key_ref="idempotency-ref:chat-to-loop-verifier-turn",
        )
        before_files = {
            path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in state_dir.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(state_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        after_files = {
            path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in state_dir.rglob("*")
            if path.is_file()
        }
        if after_files != before_files:
            failures.append("Chat-to-loop CLI modified existing state")
        payload = json.loads(result.stdout)
        if payload["storage_state"] != "existing_state_read_only":
            failures.append("Chat-to-loop CLI did not report read-only existing state")
        _assert_read_model(payload["chat_to_loop_handoff_read_model"], failures)
        missing_state = Path(temp_dir) / "missing_state"
        missing_result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(missing_state)],
            check=True,
            capture_output=True,
            text=True,
        )
        missing_payload = json.loads(missing_result.stdout)
        if missing_payload["storage_state"] != "state_not_found_no_write":
            failures.append("Chat-to-loop CLI missing state posture drifted")
        if missing_state.exists():
            failures.append("Chat-to-loop CLI created missing state directory")
        _assert_read_model(
            missing_payload["chat_to_loop_handoff_read_model"],
            failures,
        )


def _validate_static(failures: list[str]) -> None:
    _require(
        CONTRACT,
        [
            "CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS",
            "remember_this",
            "create_action",
            "add_to_plan",
            "defer",
            "ask_human",
            "blocked",
            "_SAFE_REF_RE",
            "_safe_handoffs_for_target",
            "blocked-state:chat-to-loop-no-plan-execution",
            "blocked-state:chat-to-loop-no-browser-execution",
            "direct_memory_write_authorized",
            "model_output_authority",
            "production_authority_enabled",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "build_chat_to_loop_handoff_read_model(",
            '"chat_to_loop_handoff_read_model"',
            "def chat_to_loop_handoff(",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "state_not_found_no_write",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "direct_memory_write_authorized",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_chat_to_loop_handoff_read_model_classifies_reviewable_outcomes",
            "test_chat_to_loop_handoff_rejects_authority_raw_content_and_unsafe_refs",
            "test_chat_to_loop_handoff_idempotency_replay_and_conflict",
            "test_chat_to_loop_handoff_keeps_created_refs_on_their_source_turn",
            "test_chat_to_loop_handoff_cli_is_read_only_and_redacted",
            "evidence-ref:alice@example.com",
            "evidence-ref:workstation.local",
            "evidence-ref:relative/path/project",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopChatToLoopHandoffReadModel",
            "FounderLoopChatToLoopHandoffOutcome",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeChatToLoopHandoffReadModel",
            "delete fallbackWithoutDigest.chat_to_loop_handoff_read_model",
            "hasMatchingChatToLoopHandoffCounts",
            "CHAT_TO_LOOP_UNSAFE_TEXT_FRAGMENTS",
            "hasExactStringList",
            "CHAT_TO_LOOP_HANDOFF_TARGET_SURFACES",
            "direct_memory_write_authorized",
        ],
        failures,
    )
    _require(
        FRONTEND_OPERATOR,
        [
            "ChatToLoopHandoffPanel",
            "chat_to_loop_handoff_read_model",
            "pending backend refresh",
        ],
        failures,
    )
    _require(
        FRONTEND_PANELS,
        [
            "ChatToLoopHandoffPanel",
            "chat_to_loop_handoff_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_MOCK,
        [
            "chatToLoopHandoffReadModel",
            "remember_this",
            "ask_human",
            "direct_memory_write_authorized: false",
        ],
        failures,
    )
    _require(
        APP_TEST,
        [
            "renders backend-owned Chat to Loop handoff outcomes",
            "fails closed for unsafe Chat to Loop handoff payloads",
            "fails closed for unsafe Chat to Loop handoff refs",
            "fails closed for unsafe Chat to Loop handoff rendered text",
            "fails closed for malformed Chat to Loop handoff outcomes",
            "does not backfill Chat to Loop handoff from mocks",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "Product Loop 009",
            "remember-this",
            "reviewed memory-intake proposal",
            "No model output authority",
            "No direct memory writes",
            "scripts/inspect_chat_to_loop_handoff.py",
        ],
        failures,
    )
    for doc in [BOARD, TRUTH_PACKET, INDEX]:
        _require(doc, ["Product Loop 009", "Chat to loop handoff"], failures)
    for path in [CONTRACT, STORAGE, CLI]:
        _require_absent(
            path,
            [
                "requests.",
                "httpx.",
                "urllib.request",
                "from openai",
                "import openai",
                "from anthropic",
                "import anthropic",
                "playwright",
                "selenium",
                "firecrawl",
                "browserbase",
                "execute_workflow(",
                "connector_write(",
            ],
            failures,
        )


def main() -> int:
    failures: list[str] = []
    _validate_live(failures)
    _validate_cli(failures)
    _validate_static(failures)
    if failures:
        print("Product Loop 009 Chat-to-loop handoff verifier failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Product Loop 009 Chat-to-loop handoff verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
