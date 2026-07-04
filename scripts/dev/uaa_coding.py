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

from ultimate_ai_agent.core.code import build_coding_cockpit_session_seed  # noqa: E402


def inspect_session(args: argparse.Namespace) -> int:
    session = build_coding_cockpit_session_seed()
    payload = session.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect UAA Coding Cockpit read-only session state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser(
        "inspect-session",
        help="Print the backend-owned read-only Coding Cockpit session seed.",
    )
    inspect.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    inspect.set_defaults(func=inspect_session)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
