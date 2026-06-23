from __future__ import annotations

from pathlib import Path

from scripts.verify_operational_maturity import (
    LADDER_LABELS,
    MANIFEST_PATH,
    SCHEMA_PATH,
    verify,
)
from scripts.verification.repo import load_json


def test_operational_maturity_manifest_passes_verifier() -> None:
    assert verify() == []


def test_operational_maturity_manifest_declares_canonical_ladder() -> None:
    manifest = load_json(MANIFEST_PATH)
    schema = load_json(SCHEMA_PATH)
    modules = {module["module_id"]: module for module in manifest["modules"]}

    assert manifest["schema_version"] == "uaa-control-center-operational-maturity.v1"
    assert schema["$defs"]["rank"]["minimum"] == 0
    assert schema["$defs"]["rank"]["maximum"] == 7
    assert set(LADDER_LABELS.values()) == {
        "docs_only",
        "read_only_status",
        "proposal_review",
        "decision_receipts",
        "execution_ready_contract",
        "local_execution_receipt_evidence",
        "rollback_safe_disable_verified",
        "routine_operational_loop",
    }
    assert modules["action_inbox"]["current_rank"] == 3
    local_task_lane = modules["action_inbox"]["graduated_lanes"][0]
    assert local_task_lane["lane_id"] == "local_task_create"
    assert local_task_lane["rank"] == 5
    assert (
        "POST /control-center/actions/{action_id}/local-task/commit"
        in local_task_lane["backend_routes"]
    )


def test_operational_maturity_gate_docs_exist() -> None:
    for path in [MANIFEST_PATH, SCHEMA_PATH]:
        assert Path(path).exists()
