#!/usr/bin/env python3
"""Inspect local Chat-to-loop handoff posture without creating state."""
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

from ultimate_ai_agent.core.control_center.chat_to_loop_handoff import (  # noqa: E402
    CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
    build_chat_to_loop_handoff_read_model,
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
    return build_chat_to_loop_handoff_read_model(
        chat_turn_receipts=[],
        chat_handoff_receipts=[],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Product Loop 009 Chat-to-loop handoff posture."
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
            payload = repo.chat_to_loop_handoff(limit=args.limit)
            read_model = payload["chat_to_loop_handoff_read_model"]
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:chat-to-loop-handoff:read-failed-redacted"
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "product-loop-009-chat-to-loop-handoff.inspect.v1",
        "command_ref": "repo-local-command:inspect-chat-to-loop-handoff",
        "contract_ref": CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "chat_to_loop_handoff_read_model": read_model,
        "safe_refs_only": True,
        "safe_summary_only": True,
        "proposal_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "model_output_authority": False,
        "direct_memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "tool_execution_enabled": False,
        "connector_write_enabled": False,
        "action_execution_enabled": False,
        "plan_execution_enabled": False,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "live_web_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "browser_execution_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
