#!/usr/bin/env python3
"""Inspect the local Weekly CEO Review V1 posture without creating state."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.control_center.weekly_ceo_review import (  # noqa: E402
    WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
    WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS,
    WeeklyCeoReviewV1ReadModel,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopRepository,
)


def _default_state_dir() -> Path:
    configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _empty_read_model() -> dict:
    return WeeklyCeoReviewV1ReadModel(
        status="state_not_found_no_write",
        unresolved_count=1,
        evidence_event_count=1,
        completed_refs=[],
        deferred_refs=[],
        rejected_refs=[],
        blocked_refs=[],
        stale_refs=[],
        unresolved_refs=["weekly-review-ref:state-not-found"],
        carry_forward_refs=[],
        next_week_priority_refs=[],
        action_decision_refs=[],
        memory_decision_refs=[],
        follow_up_refs=[],
        evidence_event_refs=["evidence-event:weekly-ceo-review-v1:state-not-found"],
        evidence_refs=["evidence-ref:weekly-ceo-review-v1:state-not-found"],
        receipt_refs=[],
        missing_source_refs=[],
        blocked_authority_refs=list(WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS),
        next_safe_action="Create local Founder Loop state before inspecting weekly review refs.",
    ).model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Product Loop 008 Weekly CEO Review V1 posture."
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Founder Loop state directory to inspect.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum local safe refs to project into the review.",
    )
    args = parser.parse_args(argv)

    state_dir = (args.state_dir or _default_state_dir()).expanduser()
    sqlite_state = state_dir / "founder_loop.sqlite3"
    inspection_error_ref = None
    if sqlite_state.exists():
        try:
            repo = FounderLoopRepository(
                state_dir,
                seed_defaults=False,
                ensure_storage=False,
                read_only=True,
            )
            weekly = repo.weekly_ceo_review(limit=args.limit)
            read_model = weekly["weekly_ceo_review_v1_read_model"]
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:weekly-ceo-review-v1:read-failed-redacted"
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-008-weekly-ceo-review.inspect.v1",
        "command_ref": "repo-local-command:inspect-weekly-ceo-review",
        "contract_ref": WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "weekly_ceo_review_v1_read_model": read_model,
        "safe_refs_only": True,
        "safe_summary_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_logs_included": False,
        "prompt_content_included": False,
        "response_content_included": False,
        "provider_exchange_content_included": False,
        "connector_read_enabled": False,
        "connector_runtime_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_fetch_enabled": False,
        "live_web_enabled": False,
        "model_summary_enabled": False,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "action_execution_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_execution_enabled": False,
        "public_beta_claim_enabled": False,
        "production_claim_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
