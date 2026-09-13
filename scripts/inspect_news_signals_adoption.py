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


def _content_safe_workspace(view: dict[str, object]) -> dict[str, object]:
    summary = view["summary"]
    active_page = view["active_items_page"]
    preferences = view["preferences"]
    archived_items = view["archived_items"]
    assert isinstance(summary, dict)
    assert isinstance(active_page, dict)
    assert isinstance(preferences, list)
    assert isinstance(archived_items, list)
    source_readiness = summary["source_readiness"]
    summary_items = summary["items"]
    today_projection = summary["today_projection"]
    briefing_projection = summary["morning_briefing_projection"]
    assert isinstance(source_readiness, list)
    assert isinstance(summary_items, list)
    assert isinstance(today_projection, dict)
    assert isinstance(briefing_projection, dict)
    return {
        "schema_version": view["schema_version"],
        "contract_ref": view["contract_ref"],
        "status": view["status"],
        "revision": view["revision"],
        "current_state_ref": view["current_state_ref"],
        "can_undo": view["can_undo"],
        "local_manual_intake_enabled": view["local_manual_intake_enabled"],
        "backend_owned": view["backend_owned"],
        "external_content_untrusted": view["external_content_untrusted"],
        "live_fetch_enabled": view["live_fetch_enabled"],
        "authenticated_source_enabled": view["authenticated_source_enabled"],
        "background_polling_enabled": view["background_polling_enabled"],
        "model_summarization_enabled": view["model_summarization_enabled"],
        "connector_write_enabled": view["connector_write_enabled"],
        "action_authority_granted": view["action_authority_granted"],
        "counts": {
            "sources": len(source_readiness),
            "ranked_summary_items": len(summary_items),
            "active_signals": active_page["total_items"],
            "returned_active_signal_refs": active_page["returned_items"],
            "preferences": len(preferences),
            "archived_signals": len(archived_items),
            "today_items": len(today_projection["item_refs"]),
            "briefing_candidates": len(briefing_projection["candidate_refs"]),
        },
        "source_refs": [item["source_ref"] for item in source_readiness],
        "active_signal_refs": [
            item["signal_ref"] for item in active_page["items"]
        ],
        "archived_signal_refs": [
            item["signal_ref"] for item in archived_items
        ],
        "today_item_refs": today_projection["item_refs"],
        "briefing_candidate_refs": briefing_projection["candidate_refs"],
        "blocked_state_refs": summary["blocked_state_refs"],
        "evidence_refs": view["evidence_refs"],
        "next_safe_action": view["next_safe_action"],
        "private_values_included": False,
    }


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
    workspace = store.read_view(limit=args.limit)
    payload = {
        "schema_version": "uaa-news-signals-adoption-inspection.v1",
        "command_ref": "repo-local-command:inspect-news-signals-adoption",
        "workspace": _content_safe_workspace(workspace),
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
