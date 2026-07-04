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

from ultimate_ai_agent.core.code import (  # noqa: E402
    build_coding_cockpit_session_seed,
    build_coding_git_review,
    build_coding_live_preview,
    build_coding_multi_agent_review,
    build_coding_patch_apply_readiness,
    build_coding_patch_proposal_preview,
    build_coding_test_command_readiness,
    build_coding_workspace_context_preview,
)


def inspect_session(args: argparse.Namespace) -> int:
    session = build_coding_cockpit_session_seed()
    payload = session.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_context(args: argparse.Namespace) -> int:
    context = build_coding_workspace_context_preview()
    payload = context.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_patch_proposal(args: argparse.Namespace) -> int:
    proposal = build_coding_patch_proposal_preview()
    payload = proposal.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_patch_apply_readiness(args: argparse.Namespace) -> int:
    readiness = build_coding_patch_apply_readiness()
    payload = readiness.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_test_command_readiness(args: argparse.Namespace) -> int:
    readiness = build_coding_test_command_readiness()
    payload = readiness.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_git_review(args: argparse.Namespace) -> int:
    review = build_coding_git_review()
    payload = review.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_live_preview(args: argparse.Namespace) -> int:
    preview = build_coding_live_preview()
    payload = preview.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def inspect_multi_agent_review(args: argparse.Namespace) -> int:
    review = build_coding_multi_agent_review()
    payload = review.model_dump(mode="json")
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
    context = subparsers.add_parser(
        "inspect-context",
        help="Print the backend-owned read-only Coding Cockpit context preview.",
    )
    context.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    context.set_defaults(func=inspect_context)
    patch_proposal = subparsers.add_parser(
        "inspect-patch-proposal",
        help="Print the backend-owned proposal-only Coding Cockpit patch preview.",
    )
    patch_proposal.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    patch_proposal.set_defaults(func=inspect_patch_proposal)
    patch_apply = subparsers.add_parser(
        "inspect-patch-apply-readiness",
        help="Print the blocked Coding Cockpit patch apply readiness model.",
    )
    patch_apply.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    patch_apply.set_defaults(func=inspect_patch_apply_readiness)
    test_command = subparsers.add_parser(
        "inspect-test-command-readiness",
        help="Print the blocked Coding Cockpit allowlisted test command readiness model.",
    )
    test_command.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    test_command.set_defaults(func=inspect_test_command_readiness)
    git_review = subparsers.add_parser(
        "inspect-git-review",
        help="Print the blocked Coding Cockpit Git review read model.",
    )
    git_review.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    git_review.set_defaults(func=inspect_git_review)
    live_preview = subparsers.add_parser(
        "inspect-live-preview",
        help="Print the blocked Coding Cockpit live preview read model.",
    )
    live_preview.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    live_preview.set_defaults(func=inspect_live_preview)
    multi_agent_review = subparsers.add_parser(
        "inspect-multi-agent-review",
        help="Print the blocked Coding Cockpit multi-agent review read model.",
    )
    multi_agent_review.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    multi_agent_review.set_defaults(func=inspect_multi_agent_review)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
