#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import uvicorn

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (
    DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,
    build_dogfood_live_loop_acceptance_read_model,
)
from ultimate_ai_agent.core.storage import (
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopRepository,
)


STATE_DIR_ENV = "UAA_BACKEND_TRUTH_TEST_STATE_DIR"
PORT_ENV = "UAA_BACKEND_TRUTH_TEST_PORT"
CORRUPT_RECEIPT_ENV = "UAA_BACKEND_TRUTH_TEST_CORRUPT_RECEIPT"


def _state_dir() -> Path:
    raw = os.environ.get(STATE_DIR_ENV, "")
    if not raw:
        raise SystemExit("BACKEND_TRUTH_TEST_STATE_DIR_REQUIRED")
    path = Path(raw).resolve()
    temporary_roots = {
        Path(tempfile.gettempdir()).resolve(),
        Path("/private/tmp").resolve(),
    }
    if any(path == root for root in temporary_roots) or not any(
        root in path.parents for root in temporary_roots
    ):
        raise SystemExit("BACKEND_TRUTH_TEST_STATE_DIR_MUST_BE_TEMPORARY")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def _corrupt_durable_receipt(state_dir: Path) -> None:
    """Corrupt one test fixture receipt after its valid durable seed is proven."""

    database = state_dir / "founder_loop.sqlite3"
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT receipt_json FROM local_task_commit_receipts WHERE receipt_ref = ?",
            (DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,),
        ).fetchone()
        if row is None:
            raise SystemExit("BACKEND_TRUTH_TEST_RECEIPT_NOT_FOUND")
        receipt = json.loads(str(row[0]))
        receipt["receipt_ref"] = "receipt:founder-loop-local-task:corrupt-test-proof"
        connection.execute(
            "UPDATE local_task_commit_receipts SET receipt_json = ? WHERE receipt_ref = ?",
            (
                json.dumps(receipt, sort_keys=True, separators=(",", ":")),
                DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,
            ),
        )


def main() -> int:
    state_dir = _state_dir()
    port = int(os.environ.get(PORT_ENV, "18117"))
    if port < 1024 or port > 65535:
        raise SystemExit("BACKEND_TRUTH_TEST_PORT_INVALID")
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-backend-truth-browser-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Browser acceptance lease permits only the local fixture commit.",
    )
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[lease],
    )
    build_dogfood_live_loop_acceptance_read_model(
        repo=repo,
        seed_fixture=True,
    )
    if os.environ.get(CORRUPT_RECEIPT_ENV) == "1":
        _corrupt_durable_receipt(state_dir)
    os.environ[FOUNDER_LOOP_STATE_DIR_ENV] = str(state_dir)
    os.environ["UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY"] = "1"
    uvicorn.run(
        "ultimate_ai_agent.api.app:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
