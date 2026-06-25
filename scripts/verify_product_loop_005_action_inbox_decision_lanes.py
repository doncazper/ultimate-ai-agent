#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/action_inbox_decision_lanes.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_action_inbox_decision_lanes.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_005_ACTION_INBOX_DECISION_LANES.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
TEST = ROOT / "tests/test_action_inbox_decision_lanes.py"


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
        INDEX,
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
            "ACTION_INBOX_DECISION_LANE_CONTRACT_REF",
            "ACTION_INBOX_DECISION_LANE_ORDER",
            "needs_approval",
            "cost_blocked",
            "no_authority",
            "approved_no_execution",
            "approval_alone_executes",
            "action_execution_enabled: bool = False",
            "provider_model_call_enabled: bool = False",
            "frontier usage claims require cost telemetry refs",
            "missing envelope fields must fail closed",
            "build_action_inbox_decision_lane_read_model",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "ACTION_INBOX_DECISION_LANE_CONTRACT_REF",
            "build_action_inbox_decision_lane_read_model(",
            '"action_inbox_decision_lane_contract_ref"',
            '"action_inbox_decision_lane_read_model"',
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:inspect-action-inbox-decision-lanes",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "raw_paths_omitted",
            '"approval_alone_executes": False',
            '"action_execution_enabled": False',
            '"provider_model_call_authorized": False',
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopActionInboxDecisionLaneId",
            "FounderLoopActionInboxDecisionLaneReadModel",
            "action_inbox_decision_lane_contract_ref?: string",
            "action_inbox_decision_lane_read_model?: FounderLoopActionInboxDecisionLaneReadModel",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "normalizeFounderActionsInbox",
            "action_inbox_decision_lane_read_model",
            "delete withoutMockLanes.action_inbox_decision_lane_read_model",
            "delete withoutMockLanes.action_inbox_decision_lane_contract_ref",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "ActionInboxDecisionLanePanel",
            "backend decision lanes missing",
            "Cost blocked",
            "Cost approved",
            "Unknown paid cost",
            "No provider authority",
            "Approved / no execution",
            "Approval alone",
            "accounting readiness only; no provider calls",
            "Provider/model refs",
            "Expected receipts",
            "Missing envelope fields",
            "Blocked authority",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "backend decision lanes missing",
            "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
            "python_core_action_inbox_decision_lane_read_model",
            "action_inbox_decision_lane_read_model).toBeUndefined",
            "Cost blocked",
            "Approved / no execution",
            "approval_scope_ref:missing",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
            "scripts/inspect_action_inbox_decision_lanes.py",
            "approval alone does not execute",
            "Cost blocked",
            "No provider authority",
            "accounting readiness only",
            "safe-ref-only",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "Product Loop 005 Action Inbox Decision-Lane Polish",
            "`action_inbox_decision_lane_read_model`",
            "`scripts/inspect_action_inbox_decision_lanes.py`",
            "approval alone does not execute",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "`action_inbox_decision_lane_read_model`",
            "scripts/inspect_action_inbox_decision_lanes.py",
            "docs/control_center/PRODUCT_LOOP_005_ACTION_INBOX_DECISION_LANES.md",
            "cost-blocked, no-authority, and approved/no-execution",
            "approval alone does not execute",
        ],
        failures,
    )
    _require(
        INDEX,
        [
            "docs/control_center/PRODUCT_LOOP_005_ACTION_INBOX_DECISION_LANES.md",
        ],
        failures,
    )
    _require(
        TEST,
        [
            "test_action_inbox_decision_lanes_surface_from_storage",
            "test_action_inbox_decision_lanes_cover_canonical_operator_states",
            "test_action_inbox_decision_lanes_fail_safe_when_envelope_fields_are_missing",
            "test_action_inbox_decision_lane_cli_inspection_is_read_only_and_redacted",
        ],
        failures,
    )

    panel_text = _read(FRONTEND_PANEL).lower()
    forbidden_enabled_labels = [
        "approval alone executes",
        "action execution enabled",
        "provider model calls enabled",
        "connector writes enabled",
        "production authority enabled",
    ]
    for label in forbidden_enabled_labels:
        if label in panel_text:
            failures.append(f"Control Center wording implies authority: {label}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Product Loop 005 Action Inbox decision-lane verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
