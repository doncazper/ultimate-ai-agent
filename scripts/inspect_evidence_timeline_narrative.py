#!/usr/bin/env python3
"""Inspect local Evidence Timeline narrative posture without creating state."""
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

from ultimate_ai_agent.core.storage import (  # noqa: E402
    EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF,
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopEvidenceTimelineNarrativeReadModel,
    FounderLoopRepository,
)


def _default_state_dir() -> Path:
    configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _empty_read_model() -> dict:
    return FounderLoopEvidenceTimelineNarrativeReadModel().model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Product Loop 010 Evidence Timeline narrative posture."
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
        default=50,
        help="Maximum local safe refs to project into the read model.",
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
            payload = repo.evidence_timeline(limit=args.limit)
            read_model = payload["narrative_read_model"]
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:evidence-timeline-narrative:read-failed-redacted"
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-010-evidence-timeline-narrative.inspect.v1",
        "command_ref": "repo-local-command:inspect-evidence-timeline-narrative",
        "contract_ref": EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "narrative_read_model": read_model,
        "safe_refs_only": True,
        "redacted_summaries_only": True,
        "read_only": True,
        "narrative_from_existing_refs_only": True,
        "raw_content_omitted": True,
        "approval_ref_authority": False,
        "rollback_execution_enabled": False,
        "action_execution_enabled": False,
        "tool_execution_enabled": False,
        "workflow_execution_enabled": False,
        "connector_write_enabled": False,
        "connector_runtime_enabled": False,
        "provider_model_call_enabled": False,
        "runtime_model_calls_enabled": False,
        "provider_sdk_call_enabled": False,
        "live_web_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_execution_enabled": False,
        "public_beta_enabled": False,
        "distribution_enabled": False,
        "prompt_content_stored": False,
        "response_content_stored": False,
        "provider_exchange_content_stored": False,
        "memory_truth_authority": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
