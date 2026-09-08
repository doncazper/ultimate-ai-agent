#!/usr/bin/env python3
"""Inspect content-free Chat workspace metadata without creating local state."""

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

from ultimate_ai_agent.core.chat.workspace import (  # noqa: E402
    CHAT_WORKSPACE_CONTRACT_REF,
    build_chat_workspace_read_model,
)
from ultimate_ai_agent.core.chat.workspace_repository import (  # noqa: E402
    ChatWorkspaceRepository,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FOUNDER_LOOP_STATE_DIR_ENV,
)


def _default_state_dir() -> Path:
    configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _empty_workspace() -> dict:
    return build_chat_workspace_read_model([]).model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Q33 content-free Chat workspace metadata."
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Founder Loop state directory to inspect read-only.",
    )
    args = parser.parse_args(argv)

    state_dir = (args.state_dir or _default_state_dir()).expanduser()
    sqlite_state = state_dir / "founder_loop.sqlite3"
    inspection_error_ref = None
    if sqlite_state.exists():
        try:
            repo = ChatWorkspaceRepository(
                state_dir,
                ensure_storage=False,
                read_only=True,
            )
            workspace = repo.workspace()
            storage_state = "existing_state_read_only"
        except Exception:
            workspace = _empty_workspace()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = "error-ref:chat-workspace:read-failed-redacted"
    else:
        workspace = _empty_workspace()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "chat-content-free-workspace.inspect.v1",
        "command_ref": "repo-local-command:inspect-chat-workspace",
        "contract_ref": CHAT_WORKSPACE_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "chat_workspace_read_model": workspace,
        "safe_refs_only": True,
        "draft_metadata_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "draft_body_stored": False,
        "model_call_enabled": False,
        "tool_execution_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "connector_write_enabled": False,
        "action_execution_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
