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

from ultimate_ai_agent.core.memory import (  # noqa: E402
    CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF,
    CrmLiteRelationshipFollowUp,
    crm_lite_relationship_authority_posture,
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


def _validated_followups(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return [
        CrmLiteRelationshipFollowUp(**item).model_dump()
        for item in items[: max(0, limit)]
    ]


def _empty_today_actions() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {"crm_lite_followups": [], "memory_why_shown_items": []},
        {"crm_lite_followups": []},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect review-only relationship / CRM-lite memory posture."
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
            actions = repo.actions_inbox(limit=args.limit)
            storage_state = "existing_state_read_only"
        except Exception:
            today, actions = _empty_today_actions()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = (
                "error-ref:relationship-crm-lite-memory:read-failed-redacted"
            )
    else:
        today, actions = _empty_today_actions()
        storage_state = "state_not_found_no_write"
    output = {
        "schema_version": "product-loop-001-relationship-crm-lite-memory.inspect.v1",
        "command_ref": "repo-local-command:inspect-relationship-crm-lite-memory",
        "contract_ref": CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "authority_posture": crm_lite_relationship_authority_posture(),
        "today_followups": _validated_followups(
            list(today.get("crm_lite_followups") or []),
            args.limit,
        ),
        "action_inbox_followups": _validated_followups(
            list(actions.get("crm_lite_followups") or []),
            args.limit,
        ),
        "memory_why_shown_items": list(today.get("memory_why_shown_items") or [])[
            : max(0, args.limit)
        ],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "connector_runtime_enabled": False,
        "crm_sync_enabled": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
