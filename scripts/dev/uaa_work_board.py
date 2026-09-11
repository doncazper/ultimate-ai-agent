#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center import (  # noqa: E402
    WorkBoardStateStore,
    build_work_board_read_model,
)
from ultimate_ai_agent.core.control_center.work_board_adoption import (  # noqa: E402
    WorkBoardAdoptionStore,
)


def inspect_board(args: argparse.Namespace) -> int:
    board = build_work_board_read_model()
    payload = board.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_reorder_receipt(args: argparse.Namespace) -> int:
    receipt = WorkBoardStateStore().latest_receipt()
    payload = (
        receipt.model_dump(mode="json")
        if receipt is not None
        else {
            "status": "missing",
            "receipt_ref": None,
            "safe_summary": "No Work Board reorder receipt has been recorded.",
            "raw_paths_included": False,
            "raw_content_included": False,
        }
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_card_create_receipt(args: argparse.Namespace) -> int:
    receipt = WorkBoardStateStore().latest_card_create_receipt()
    payload = (
        receipt.model_dump(mode="json")
        if receipt is not None
        else {
            "status": "missing",
            "receipt_ref": None,
            "card_ref": None,
            "safe_summary": "No Work Board card-create receipt has been recorded.",
            "raw_paths_included": False,
            "raw_content_included": False,
        }
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_task_create_receipt(args: argparse.Namespace) -> int:
    receipt = WorkBoardStateStore().latest_task_create_receipt()
    payload = (
        receipt.model_dump(mode="json")
        if receipt is not None
        else {
            "status": "missing",
            "receipt_ref": None,
            "card_ref": None,
            "local_task_ref": None,
            "safe_summary": "No Work Board local task-create receipt has been recorded.",
            "raw_paths_included": False,
            "raw_content_included": False,
            "task_execution_performed": False,
        }
    )
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_adoption(args: argparse.Namespace) -> int:
    view = WorkBoardAdoptionStore(args.state_dir).read_view()
    if args.include_private:
        payload = {
            **view.model_dump(mode="json"),
            "private_values_included": True,
            "raw_paths_included": False,
        }
    else:
        payload = {
            "schema_version": "uaa-work-board-adoption-cli-inspection.v1",
            "contract_ref": view.contract_ref,
            "board_ref": view.board_ref,
            "status": view.status,
            "revision": view.revision,
            "current_state_ref": view.current_state_ref,
            "active_card_count": len(view.active_cards),
            "archived_card_count": len(view.archived_cards),
            "lane_refs": view.lane_refs,
            "can_undo": view.can_undo,
            "latest_receipt_ref": view.latest_receipt_ref,
            "next_safe_action": view.next_safe_action,
            "backend_owned": view.backend_owned,
            "local_only": view.local_only,
            "exact_approval_required": view.exact_approval_required,
            "backup_restore_available": view.backup_restore_available,
            "task_execution_enabled": view.task_execution_enabled,
            "connector_write_enabled": view.connector_write_enabled,
            "provider_model_call_enabled": view.provider_model_call_enabled,
            "shell_subprocess_execution_enabled": (
                view.shell_subprocess_execution_enabled
            ),
            "browser_automation_enabled": view.browser_automation_enabled,
            "background_autonomy_enabled": view.background_autonomy_enabled,
            "production_authority_enabled": view.production_authority_enabled,
            "private_values_included": False,
            "raw_paths_included": False,
        }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect UAA Work Board read-only Kanban state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser(
        "inspect-board",
        help="Print the backend-owned read-only Work Board Kanban read model.",
    )
    inspect.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    inspect.set_defaults(func=inspect_board)
    receipt = subparsers.add_parser(
        "inspect-reorder-receipt",
        help="Print the latest Work Board durable reorder receipt if present.",
    )
    receipt.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON receipt.",
    )
    receipt.set_defaults(func=inspect_reorder_receipt)
    card_receipt = subparsers.add_parser(
        "inspect-card-create-receipt",
        help="Print the latest Work Board local card-create receipt if present.",
    )
    card_receipt.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON receipt.",
    )
    card_receipt.set_defaults(func=inspect_card_create_receipt)
    task_receipt = subparsers.add_parser(
        "inspect-task-create-receipt",
        help="Print the latest Work Board local task-create receipt if present.",
    )
    task_receipt.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON receipt.",
    )
    task_receipt.set_defaults(func=inspect_task_create_receipt)
    adoption = subparsers.add_parser(
        "inspect-adoption",
        help="Inspect founder-private Work Board lifecycle state without changing it.",
    )
    adoption.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Use an explicit local Work Board state directory.",
    )
    adoption.add_argument(
        "--include-private",
        action="store_true",
        help="Include local card titles and descriptions in terminal output.",
    )
    adoption.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON inspection result.",
    )
    adoption.set_defaults(func=inspect_adoption)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
