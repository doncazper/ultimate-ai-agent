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
    FOLLOW_UP_TRACKER_CONTRACT_REF,
    FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS,
    FollowUpTrackerReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


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
    return FollowUpTrackerReadModel(
        status="metadata_only_no_state_found",
        items=[],
        blocked_state_refs=list(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS),
    ).model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned follow-up tracker posture."
    )
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args(argv)

    state_dir = _state_dir(args)
    db_path = state_dir / "founder_loop.sqlite3"
    inspection_error_ref: str | None = None
    if db_path.exists():
        try:
            repo = _repo(state_dir)
            today = repo.today_summary(limit=args.limit)
            read_model = dict(today.get("follow_up_tracker") or _empty_read_model())
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:follow-up-tracker:read-failed-redacted"
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-004-follow-up-tracker.inspect.v1",
        "command_ref": "repo-local-command:inspect-follow-up-tracker",
        "contract_ref": FOLLOW_UP_TRACKER_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "follow_up_tracker": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "reminder_scheduler_enabled": False,
        "message_send_enabled": False,
        "connector_reads_enabled": False,
        "connector_writes_enabled": False,
        "email_calendar_fetch_enabled": False,
        "automatic_task_creation_enabled": False,
        "action_execution_enabled": False,
        "model_provider_call_authorized": False,
        "automatic_memory_write_authorized": False,
        "hidden_memory_write_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
