#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/unified_work_thread.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
DEV_CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/FCC_THREAD_001_UNIFIED_WORK_THREAD.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
README = ROOT / "docs/README.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
FOCUSED_TEST = ROOT / "tests/test_fcc_thread_001_unified_work_thread.py"


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
            failures.append(
                f"{path.relative_to(ROOT)} contains forbidden snippet {snippet!r}"
            )


def _validate_live_read_model(failures: list[str]) -> None:
    from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
    from ultimate_ai_agent.core.control_center.action_decisions import (
        FounderLoopActionDecisionRequest,
    )
    from ultimate_ai_agent.core.control_center.unified_work_thread import (
        UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS,
        UNIFIED_WORK_THREAD_STEP_ORDER,
        UnifiedWorkThreadReadModel,
    )
    from ultimate_ai_agent.core.memory import (
        FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
        MemoryReviewDecisionRequest,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="fcc-thread-001-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        repo = FounderLoopRepository(state_dir)
        turn_receipt = repo.record_chat_turn_receipt(
            request=ChatTurnReceiptRequest(
                turn_ref="chat-turn:fcc-thread-001-verifier",
                route_ref="/v1/chat/completions",
                model_ref="model-ref:local-chat-gateway",
                runtime_truth="runtime-readiness-gated",
                auth_truth="local-bearer-required",
                tool_denial_truth="tools-functions-streaming-denied",
                safe_summary_ref="safe-summary-ref:fcc-thread-001-verifier",
                evidence_refs=["evidence-ref:fcc-thread-001-verifier:chat"],
                metadata_refs=["metadata-ref:fcc-thread-001-verifier:chat"],
            ),
            idempotency_key_ref="idempotency-ref:fcc-thread-001-verifier-chat",
        )
        handoff_receipt = repo.record_chat_handoff(
            turn_ref=turn_receipt["turn_ref"],
            request=ChatHandoffRequest(
                handoff_target="actions",
                decision_reason_ref="decision-reason-ref:fcc-thread-001-verifier-action",
                metadata_refs=["metadata-ref:fcc-thread-001-verifier-action"],
            ),
            idempotency_key_ref="idempotency-ref:fcc-thread-001-verifier-action",
        )
        action_receipt = repo.record_action_decision(
            action_id="setup-assistant-hardening",
            decision="defer",
            request=FounderLoopActionDecisionRequest(
                expected_revision_ref=next(
                    str(item["action_revision_ref"])
                    for item in repo.list_action_inbox(limit=200)
                    if item["item_ref"]
                    == "founder-action:setup-assistant-hardening"
                ),
                decision_reason_ref="decision-reason-ref:fcc-thread-001-verifier-defer"
            ),
            idempotency_key_ref="idempotency-ref:fcc-thread-001-verifier-defer",
        )
        candidate_ref = str(
            repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
        )
        memory_receipt = repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="defer",
            request=MemoryReviewDecisionRequest(
                reviewer_ref="actor-ref:fcc-thread-001-verifier",
                source_refs=["source-ref:fcc-thread-001-verifier-memory"],
                evidence_refs=["evidence-ref:fcc-thread-001-verifier-memory"],
                blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
            ),
            idempotency_key_ref="idempotency-ref:fcc-thread-001-verifier-memory",
        )
        today = repo.today_summary()
        result = subprocess.run(
            [
                sys.executable,
                str(DEV_CLI),
                "--state-dir",
                str(state_dir),
                "inspect-work-thread",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    read_model = today.get("unified_work_thread_read_model")
    if not isinstance(read_model, dict):
        failures.append("today_summary() missing Unified Work Thread read model")
        return
    try:
        parsed = UnifiedWorkThreadReadModel(**read_model)
    except Exception as exc:
        failures.append(f"Unified Work Thread read model failed validation: {exc}")
        return
    if parsed.step_order != list(UNIFIED_WORK_THREAD_STEP_ORDER):
        failures.append("Unified Work Thread step order drifted")
    if set(UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS) - set(
        parsed.blocked_authority_refs
    ):
        failures.append("Unified Work Thread missing blocked refs")
    if turn_receipt["receipt_ref"] not in parsed.chat_turn_receipt_refs:
        failures.append("Chat turn receipt missing from Unified Work Thread")
    if handoff_receipt["receipt_ref"] not in parsed.chat_handoff_receipt_refs:
        failures.append("Chat handoff receipt missing from Unified Work Thread")
    if action_receipt["receipt_ref"] not in parsed.action_decision_receipt_refs:
        failures.append("Action decision receipt missing from Unified Work Thread")
    if memory_receipt["receipt_ref"] not in parsed.memory_review_receipt_refs:
        failures.append("Memory review receipt missing from Unified Work Thread")
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "a2a_runtime_dispatch_enabled",
        "mcp_runtime_dispatch_enabled",
        "browser_execution_enabled",
        "live_web_enabled",
        "connector_read_enabled",
        "connector_write_enabled",
        "email_calendar_send_enabled",
        "crm_write_enabled",
        "account_sync_enabled",
        "shell_subprocess_execution_enabled",
        "background_autonomy_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "action_execution_enabled",
        "public_beta_claim_enabled",
        "public_release_claim_enabled",
        "production_authority_enabled",
    ]:
        if getattr(parsed, flag):
            failures.append(f"Unified Work Thread enables {flag}")

    if result.returncode != 0:
        failures.append("inspect-work-thread CLI failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        failures.append("inspect-work-thread CLI emitted invalid JSON")
        return
    if payload.get("command_ref") != "repo-local-command:founder-loop-inspect-work-thread":
        failures.append("inspect-work-thread CLI command ref drifted")
    if payload.get("raw_content_omitted") is not True:
        failures.append("inspect-work-thread CLI missing raw-content omission flag")
    if payload.get("raw_paths_omitted") is not True:
        failures.append("inspect-work-thread CLI missing raw-path omission flag")
    if "fcc-thread-001-" in result.stdout and "/founder_loop" in result.stdout:
        failures.append("inspect-work-thread CLI leaked temp state path")


def verify() -> list[str]:
    failures: list[str] = []
    for path in [
        CONTRACT,
        STORAGE,
        DEV_CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        DOC,
        INDEX,
        README,
        BOARD,
        TRUTH_PACKET,
        FOCUSED_TEST,
    ]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    _require(
        CONTRACT,
        [
            "UNIFIED_WORK_THREAD_CONTRACT_REF",
            "UnifiedWorkThreadReadModel",
            "build_unified_work_thread_read_model",
            "UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "unified_work_thread_read_model",
            "unified_work_thread_contract_ref",
            "build_unified_work_thread_read_model",
        ],
        failures,
    )
    _require(
        DEV_CLI,
        [
            "inspect-work-thread",
            "repo-local-command:founder-loop-inspect-work-thread",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "state_not_found_no_write",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeUnifiedWorkThreadReadModel",
            "UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS",
            "unified_work_thread_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "UnifiedWorkThreadPanel",
            "Unified Work Thread",
            "Backend-owned read model",
            "No provider/model calls",
            "No production authority",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "renders backend-owned Unified Work Thread from backend data",
            "fails closed for unsafe Unified Work Thread authority flags",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "FCC-THREAD-001 Unified Work Thread Read Model",
            "No runtime dispatch or execution",
            "inspect-work-thread",
            "No provider/model calls",
        ],
        failures,
    )
    _require(
        INDEX,
        [
            "FCC-THREAD-001 Unified Work Thread Read Model",
            "scripts/verify_fcc_thread_001_unified_work_thread.py",
        ],
        failures,
    )
    _require(
        README,
        [
            "unified_work_thread_read_model",
            "FCC-THREAD-001 Unified Work Thread",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "FCC-THREAD-001 Unified Work Thread Read Model",
            "unified_work_thread_read_model",
            "No-authority phrases: no runtime dispatch or execution",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "FCC-THREAD-001 Unified Work Thread Read Model",
            "unified_work_thread_read_model",
            "no provider/model calls",
        ],
        failures,
    )
    for path in [CONTRACT, DOC, FRONTEND_PANEL, FOCUSED_TEST]:
        _require_absent(
            path,
            [
                "production ready",
                "public beta is enabled",
                "provider calls enabled",
                "connector writes enabled",
            ],
            failures,
        )
    _validate_live_read_model(failures)
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("FCC-THREAD-001 Unified Work Thread verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
