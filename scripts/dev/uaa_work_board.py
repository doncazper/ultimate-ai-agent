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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
