from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
)
from ultimate_ai_agent.core.control_center.start_here import (
    CONTROL_CENTER_START_HERE_CONTRACT_REF,
    CONTROL_CENTER_START_HERE_ROUTE_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_start_here_binds_one_daily_loop_to_backend_owned_refs(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    summary = service.start_here_summary()

    assert summary["schema_version"] == "control-center-start-here-summary.v1"
    assert summary["contract_ref"] == CONTROL_CENTER_START_HERE_CONTRACT_REF
    assert summary["source"] == "python_core_control_center_start_here_read_model"
    assert summary["backend_owned"] is True
    assert summary["safe_refs_only"] is True
    assert summary["raw_content_included"] is False
    assert summary["primary_run_ref"] == FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    assert summary["primary_proof_ref"] == FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    assert summary["action_proposal_ref"].startswith("action-envelope:")
    assert summary["readiness_state"] == "ready_for_one_local_governed_loop"
    assert summary["local_loop_status"] == "one_governed_local_loop_available"
    assert summary["complete_daily_loop_available"] is True
    assert "route-ref:control-center:start" in summary["route_refs"]
    assert CONTROL_CENTER_START_HERE_ROUTE_REF in summary["backend_route_refs"]
    assert summary["missing_prerequisite_refs"] == []
    step_ids = {step["step_id"] for step in summary["steps"]}
    assert {
        "start",
        "today",
        "action_inbox",
        "decision_receipt",
        "evidence_timeline",
        "memory_review",
        "weekly_review",
    } <= step_ids
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "connector_write_enabled",
        "connector_send_enabled",
        "browser_execution_enabled",
        "shell_subprocess_execution_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ]:
        assert summary[flag] is False


def test_start_here_api_route_is_read_only_safe_refs() -> None:
    response = client.get("/control-center/start-here/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_start_here_summary"
    assert "safe_refs_only" in body["redactions_applied"]
    assert "raw_content_omitted" in body["redactions_applied"]
    assert body["data"]["backend_owned"] is True
    assert body["data"]["safe_refs_only"] is True
    assert body["data"]["connector_write_enabled"] is False
    assert body["data"]["production_authority_enabled"] is False


def test_start_here_cli_inspects_same_safe_read_model(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder_loop"
    FounderLoopRepository(state_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-start-here",
        ],
        check=True,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    output = json.loads(result.stdout)
    summary = output["start_here"]
    assert output["command_ref"] == "repo-local-command:founder-loop-inspect-start-here"
    assert output["safe_refs_only"] is True
    assert output["raw_paths_omitted"] is True
    assert summary["contract_ref"] == CONTROL_CENTER_START_HERE_CONTRACT_REF
    assert summary["safe_refs_only"] is True
    assert summary["raw_content_included"] is False
    assert summary["action_proposal_ref"].startswith("action-envelope:")
    assert summary["provider_model_call_enabled"] is False
    assert summary["connector_write_enabled"] is False
