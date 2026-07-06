#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Source Readiness read-only metadata contract refs."
    )
    parser.add_argument("--state-dir", default=None)
    args = parser.parse_args()

    state_dir = _state_dir(args)
    db_path = state_dir / "founder_loop.sqlite3"
    storage_state = "state_not_found_no_write"
    inspection_error_ref: str | None = None
    if db_path.exists():
        try:
            source_readiness = _repo(state_dir).source_readiness()
            storage_state = "existing_state_read_only"
        except Exception:
            source_readiness = _repo(state_dir).source_readiness(briefing_items=[])
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = (
                "error-ref:source-readiness-metadata-contracts:read-failed-redacted"
            )
    else:
        source_readiness = _repo(state_dir).source_readiness(briefing_items=[])
    payload = {
        "schema_version": "source_readiness_metadata_contracts_cli.v1",
        "command_ref": "repo-local-command:inspect-source-readiness-metadata-contracts",
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "source": source_readiness["source"],
        "backend_owned": source_readiness["backend_owned"],
        "route_ref": source_readiness["route_ref"],
        "contract_count": source_readiness["read_only_metadata_contract_count"],
        "contracts": source_readiness["read_only_metadata_contracts"],
        "blocked_authority_refs": source_readiness["blocked_authority_refs"],
        "connector_runtime_enabled": source_readiness["connector_runtime_enabled"],
        "account_auth_enabled": source_readiness["account_auth_enabled"],
        "raw_source_ingestion_enabled": source_readiness[
            "raw_source_ingestion_enabled"
        ],
        "write_authority_enabled": source_readiness["write_authority_enabled"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
