#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/follow_up_tracker.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_follow_up_tracker.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_004_FOLLOW_UP_TRACKER.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
TEST = ROOT / "tests/test_follow_up_tracker.py"


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
        CONTRACT,
        STORAGE,
        CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        DOC,
        BOARD,
        TRUTH_PACKET,
        TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    _require(
        CONTRACT,
        [
            "FOLLOW_UP_TRACKER_CONTRACT_REF",
            "FollowUpTrackerItem",
            "FollowUpTrackerReadModel",
            "build_follow_up_tracker_read_model",
            "relationship_follow_up",
            "pending_reply",
            "automatic_task_creation_enabled: bool = False",
            "message_send_enabled: bool = False",
            "runtime_model_calls_enabled: bool = False",
            "hidden_memory_write_authorized: bool = False",
            "blocked-state:follow-up-tracker-no-context-injection",
            "blocked-state:follow-up-tracker-no-production-authority",
            "raw_content_included: bool = False",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            '"follow_up_tracker_contract_ref"',
            '"follow_up_tracker"',
            "build_follow_up_tracker_read_model(",
            "actions_inbox",
            "morning_briefing",
            "today_summary",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:inspect-follow-up-tracker",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "raw_paths_omitted",
            '"message_send_enabled": False',
            '"action_execution_enabled": False',
            '"hidden_memory_write_authorized": False',
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopFollowUpTrackerItem",
            "FounderLoopFollowUpTrackerReadModel",
            "follow_up_tracker_contract_ref?: string",
            "follow_up_tracker?: FounderLoopFollowUpTrackerReadModel",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "stripFollowUpTrackerIfMissing",
            "delete fallbackWithoutDigest.follow_up_tracker",
            "delete normalized.follow_up_tracker",
            "follow_up_tracker_contract_ref",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "FollowUpTrackerPanel",
            "backend tracker missing",
            "No reminders, messages, source fetches",
            "context injection",
            "production authority",
            "Reminder scheduler",
            "Message send",
            "Connector reads",
            "Connector writes",
            "Email/calendar fetch",
            "Task creation",
            "Action execution",
            "Runtime model calls",
            "Hidden memory write",
            "Context injection",
            "Production authority",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "backend tracker missing",
            "contract-ref:product-loop-004-follow-up-tracker:v1",
            "python_core_follow_up_tracker_read_model",
            "follow_up_tracker).toBeUndefined",
            "Reminder scheduler",
            "Production authority",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "contract-ref:product-loop-004-follow-up-tracker:v1",
            "scripts/inspect_follow_up_tracker.py",
            "review-only",
            "not a reminder engine",
            "action-execution path",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "Product Loop 004 Follow-Up Tracker",
            "`follow_up_tracker`",
            "`scripts/inspect_follow_up_tracker.py`",
            "reminders, messages, email/calendar fetch",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "`follow_up_tracker`",
            "scripts/inspect_follow_up_tracker.py",
            "docs/control_center/PRODUCT_LOOP_004_FOLLOW_UP_TRACKER.md",
            "no reminders, message sending",
            "hidden memory writes, context injection",
            "production authority",
        ],
        failures,
    )
    _require(
        TEST,
        [
            "test_follow_up_tracker_surfaces_from_storage_read_models",
            "test_follow_up_tracker_cli_inspection_is_read_only_and_redacted",
            "test_follow_up_tracker_item_rejects_runtime_authority_flags",
            "FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS",
        ],
        failures,
    )

    panel_text = _read(FRONTEND_PANEL).lower()
    forbidden_enabled_labels = [
        "message send enabled",
        "task creation enabled",
        "reminder enabled",
        "source fetch enabled",
    ]
    for label in forbidden_enabled_labels:
        if label in panel_text:
            failures.append(f"Control Center wording implies authority: {label}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Product Loop 004 follow-up tracker verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
