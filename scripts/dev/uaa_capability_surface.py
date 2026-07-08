#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center.capability_surface import (  # noqa: E402
    build_control_center_capability_surface_read_model,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _inspect(_: argparse.Namespace) -> int:
    api_manifest = build_api_manifest(app)
    read_model = build_control_center_capability_surface_read_model(
        live_api_routes=api_manifest.routes,
    )
    _print_json(read_model.model_dump(mode="json"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the read-only Control Center capability-surface read model."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Print the bounded safe-ref capability-surface read model.",
    )
    inspect_parser.set_defaults(func=_inspect)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
