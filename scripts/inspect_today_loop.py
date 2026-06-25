#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center import (  # noqa: E402
    TODAY_LOOP_LANE_ORDER,
    TODAY_LOOP_REQUIRED_BLOCKED_REFS,
    TODAY_LOOP_TIGHTENING_CONTRACT_REF,
    TodayLoopLane,
    TodayLoopReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


LANE_LABELS = {
    "needs_review": "Needs review",
    "blocked_now": "Blocked now",
    "changed": "Changed",
    "follow_up": "Follow-ups",
    "stale_or_deferred": "Stale or deferred",
}


def _state_dir(args: argparse.Namespace) -> Path:
    if args.state_dir:
        return Path(args.state_dir)
    configured = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _repo(state_dir: Path) -> FounderLoopRepository:
    return FounderLoopRepository(
        state_dir,
        seed_defaults=False,
        ensure_storage=False,
        read_only=True,
    )


def _empty_read_model() -> dict[str, Any]:
    lanes = [
        TodayLoopLane(
            lane_id=lane_id,
            label=LANE_LABELS[lane_id],
            status="state_not_found_no_write",
            count=0,
            next_safe_action="Inspect existing local state before review.",
            blocked_state_refs=list(TODAY_LOOP_REQUIRED_BLOCKED_REFS),
        )
        for lane_id in TODAY_LOOP_LANE_ORDER
    ]
    return TodayLoopReadModel(
        status="metadata_only_no_state_found",
        lanes=lanes,
        blocked_state_refs=list(TODAY_LOOP_REQUIRED_BLOCKED_REFS),
    ).model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned Today loop decision/readiness posture."
    )
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)

    state_dir = _state_dir(args)
    db_path = state_dir / "founder_loop.sqlite3"
    inspection_error_ref: str | None = None
    if db_path.exists():
        try:
            repo = _repo(state_dir)
            today = repo.today_summary(limit=args.limit)
            today_loop_read_model = dict(
                today.get("today_loop_read_model") or _empty_read_model()
            )
            storage_state = "existing_state_read_only"
        except Exception:
            today_loop_read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:today-loop:read-failed-redacted"
    else:
        today_loop_read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-003-today-loop.inspect.v1",
        "command_ref": "repo-local-command:inspect-today-loop",
        "contract_ref": TODAY_LOOP_TIGHTENING_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "today_loop_read_model": today_loop_read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "connector_reads_enabled": False,
        "source_refresh_enabled": False,
        "action_execution_enabled": False,
        "model_provider_call_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
