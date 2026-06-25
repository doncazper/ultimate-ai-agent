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
    MORNING_BRIEFING_V1_CONTRACT_REF,
    build_morning_briefing_v1_read_model,
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
    read_model = build_morning_briefing_v1_read_model(
        briefing={
            "items": [],
            "daily_loop_sections": [],
            "source_readiness_items": [],
            "source_readiness_posture": {},
            "crm_lite_followups": [],
            "evidence_refs": ["evidence-ref:morning-briefing-v1:no-state"],
            "blocked_states": [],
        },
        actions=[],
        memory_items=[],
        evidence_timeline=[],
        storage_status={
            "storage_ref": "storage-ref:founder-loop:not-found",
            "sqlite_state_ref": "sqlite-ref:founder-loop:not-found",
            "backup_manifest_ref": "backup-manifest-ref:founder-loop:not-found",
            "jsonl_log_refs": {},
        },
        memory_workbench={
            "contract_ref": "contract-ref:memory-workbench:not-loaded",
            "status": "not_loaded",
            "health": {},
            "blocked_state_refs": [],
        },
    )
    read_model["status"] = "metadata_only_no_state_found"
    return read_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned Morning Briefing V1 posture."
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
            briefing = repo.morning_briefing(limit=args.limit)
            read_model = dict(
                briefing.get("morning_briefing_v1_read_model")
                or _empty_read_model()
            )
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = (
                "error-ref:morning-briefing-v1:read-failed-redacted"
            )
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-007-morning-briefing.inspect.v1",
        "command_ref": "repo-local-command:inspect-morning-briefing-v1",
        "contract_ref": MORNING_BRIEFING_V1_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "morning_briefing_v1_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "connector_read_enabled": False,
        "connector_runtime_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_fetch_enabled": False,
        "account_auth_enabled": False,
        "live_web_enabled": False,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "automatic_recommendations_enabled": False,
        "hidden_memory_write_authorized": False,
        "memory_write_authorized": False,
        "action_execution_enabled": False,
        "context_injection_authorized": False,
        "repo_write_enabled": False,
        "workbench_apply_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_execution_enabled": False,
        "notification_delivery_enabled": False,
        "source_refresh_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
