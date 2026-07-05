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

from ultimate_ai_agent.core.decision_router import (  # noqa: E402
    TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS,
    TurnRouterPreviewRequest,
    build_turn_router_preview,
)


def preview(args: argparse.Namespace) -> int:
    request = (
        TurnRouterPreviewRequest(sample_id=args.sample)
        if args.sample is not None
        else TurnRouterPreviewRequest(text=args.text)
    )
    payload = build_turn_router_preview(request).model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def golden_cases(args: argparse.Namespace) -> int:
    payload = {
        sample_id: build_turn_router_preview(
            TurnRouterPreviewRequest(sample_id=sample_id)
        ).model_dump(mode="json")
        for sample_id in sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS)
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect UAA Turn Contract Router no-effect previews."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    preview_parser = subparsers.add_parser(
        "preview",
        help="Print a backend-owned no-effect router preview.",
    )
    preview_source = preview_parser.add_mutually_exclusive_group(required=True)
    preview_source.add_argument(
        "--sample",
        choices=sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS),
        help="Preview a protected sample prompt without printing raw prompt text.",
    )
    preview_source.add_argument(
        "--text",
        help="Preview ephemeral text. The output omits the raw submitted text.",
    )
    preview_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    preview_parser.set_defaults(func=preview)
    golden = subparsers.add_parser(
        "golden-cases",
        help="Print all protected sample previews as safe read models.",
    )
    golden.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read models.",
    )
    golden.set_defaults(func=golden_cases)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
