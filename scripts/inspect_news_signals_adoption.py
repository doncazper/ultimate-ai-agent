#!/usr/bin/env python3
"""Inspect the Q34 founder-private News adoption workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.news_signals import NewsSignalsAdoptionStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect local News adoption state without fetching sources, "
            "connecting accounts, or calling a model."
        )
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="Inspect a specific local state directory without printing its path.",
    )
    parser.add_argument("--limit", type=int, default=20, choices=range(1, 101))
    args = parser.parse_args()

    store = (
        NewsSignalsAdoptionStore(args.state_dir)
        if args.state_dir is not None
        else NewsSignalsAdoptionStore.from_env()
    )
    payload = {
        "schema_version": "uaa-news-signals-adoption-inspection.v1",
        "command_ref": "repo-local-command:inspect-news-signals-adoption",
        "workspace": store.read_view(limit=args.limit),
        "external_network_read_performed": False,
        "authenticated_source_access_performed": False,
        "model_call_performed": False,
        "external_write_performed": False,
        "raw_paths_included": False,
        "raw_source_content_included": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
