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
    MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS,
    MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
    build_memory_workbench,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


LANE_DEFINITIONS = [
    ("duplicate_review", "Duplicate review", "merge"),
    ("stale_review", "Stale review", "defer"),
    ("conflict_review", "Conflict review", "supersede"),
    ("corrected", "Corrected", "correct"),
    ("merged", "Merged", "merge"),
    ("superseded", "Superseded", "supersede"),
    ("forget_requested", "Forget request", "forget_request"),
]


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


def _empty_lane(lane_id: str, label: str, decision_kind: str) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "label": label,
        "posture_ref": f"memory-lifecycle-posture:{lane_id.replace('_', '-')}",
        "decision_kind": decision_kind,
        "count": 0,
        "item_refs": [],
        "receipt_refs": [],
        "receipt_backed": False,
        "review_only": True,
        "blocked_state_refs": list(MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS),
    }


def _empty_lifecycle_posture() -> dict[str, Any]:
    return {
        "schema_version": "product-loop-002-memory-merge-supersede-posture.v1",
        "contract_ref": MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
        "status": "metadata_only_no_state_found",
        "lanes": [
            _empty_lane(lane_id, label, decision_kind)
            for lane_id, label, decision_kind in LANE_DEFINITIONS
        ],
        "decision_receipt_refs_by_kind": {
            "correct": [],
            "defer": [],
            "merge": [],
            "supersede": [],
            "forget_request": [],
        },
        "receipt_truncation_posture": "bounded_by_workbench_limit_safe_refs_only",
        "receipt_backed_decision_kinds": [],
        "review_only": True,
        "safe_refs_only": True,
        "reversible_review_posture": (
            "merge_supersede_forget_are_review_posture_no_destructive_execution"
        ),
        "hard_delete_authorized": False,
        "memory_export_authorized": False,
        "automatic_merge_authorized": False,
        "automatic_supersede_authorized": False,
        "automatic_forget_authorized": False,
        "hidden_memory_write_authorized": False,
        "context_injection_authorized": False,
        "connector_write_authorized": False,
        "model_provider_call_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect review-only memory merge/supersede/forget posture."
    )
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    state_dir = _state_dir(args)
    db_path = state_dir / "founder_loop.sqlite3"
    inspection_error_ref: str | None = None
    if db_path.exists():
        try:
            repo = _repo(state_dir)
            workbench = build_memory_workbench(
                candidates=repo.list_memory_review_queue(limit=args.limit),
                decision_receipts=repo.list_memory_review_decisions(limit=args.limit),
                l1_index={"previews": []},
                l2_index={},
                l3_index={},
                context_packs={"proposals": []},
                loop_refs=[],
            )
            lifecycle_posture = dict(
                workbench.get("lifecycle_posture") or _empty_lifecycle_posture()
            )
            storage_state = "existing_state_read_only"
        except Exception:
            lifecycle_posture = _empty_lifecycle_posture()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = (
                "error-ref:memory-merge-supersede-posture:read-failed-redacted"
            )
    else:
        lifecycle_posture = _empty_lifecycle_posture()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-002-memory-merge-supersede.inspect.v1",
        "command_ref": "repo-local-command:inspect-memory-merge-supersede-posture",
        "contract_ref": MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "lifecycle_posture": lifecycle_posture,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "hard_delete_authorized": False,
        "memory_export_authorized": False,
        "automatic_merge_authorized": False,
        "automatic_supersede_authorized": False,
        "automatic_forget_authorized": False,
        "hidden_memory_write_authorized": False,
        "context_injection_authorized": False,
        "connector_write_authorized": False,
        "model_provider_call_authorized": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
