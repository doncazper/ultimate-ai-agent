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
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def _assert_no_runtime_authority(payload: dict) -> None:
    text = json.dumps(payload, sort_keys=True)
    for forbidden in [
        "provider_model_call_enabled\": true",
        "runtime_model_call_enabled\": true",
        "connector_write_enabled\": true",
        "connector_send_enabled\": true",
        "browser_execution_enabled\": true",
        "shell_subprocess_execution_enabled\": true",
        "background_autonomy_enabled\": true",
        "production_authority_enabled\": true",
        "raw_content_included\": true",
    ]:
        assert forbidden not in text


def test_proof_index_covers_universal_product_event_kinds(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    index = service.proof_index()

    assert index["schema_version"] == "control-center-proof-index.v1"
    assert index["source"] == "python_core_control_center_proof_index"
    assert index["backend_owned"] is True
    assert index["safe_refs_only"] is True
    assert index["raw_content_included"] is False
    assert index["proof_count"] == len(index["records"])
    assert index["proof_refs"] == [record["proof_ref"] for record in index["records"]]
    assert {
        "daily_loop",
        "action_decision",
        "local_task_commit",
        "memory_decision",
        "evidence_event",
        "web_evidence",
        "source_readiness",
        "approval",
        "setup_package",
    }.issubset({record["proof_kind"] for record in index["records"]})
    for record in index["records"]:
        assert record["proof_ref"].startswith("proof-ref:")
        assert record["safe_refs_only"] is True
        assert record["raw_content_included"] is False
        assert record["blocked_authority_refs"]
        assert record["next_safe_action"]
    _assert_no_runtime_authority(index)


def test_proof_detail_returns_same_backend_owned_record(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    index = service.proof_index()
    proof_ref = index["proof_refs"][0]

    detail = service.proof_detail(proof_ref)

    assert detail["schema_version"] == "control-center-proof-detail.v1"
    assert detail["source"] == "python_core_control_center_proof_detail"
    assert detail["backend_owned"] is True
    assert detail["requested_proof_ref"] == proof_ref
    assert detail["record"]["proof_ref"] == proof_ref
    assert detail["record"] == index["records"][0]
    _assert_no_runtime_authority(detail)


def test_proof_api_routes_are_read_only_safe_refs() -> None:
    index_response = client.get("/control-center/proof/index")
    assert index_response.status_code == 200
    index_payload = index_response.json()["data"]
    proof_ref = index_payload["proof_refs"][0]

    detail_response = client.get(f"/control-center/proof/{proof_ref}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]

    assert index_payload["backend_owned"] is True
    assert detail_payload["record"]["proof_ref"] == proof_ref
    assert index_response.json()["redactions_applied"] == [
        "safe_refs_only",
        "bounded_summaries_only",
        "raw_content_omitted",
        "read_only_control_center_projection",
    ]
    _assert_no_runtime_authority(index_payload)
    _assert_no_runtime_authority(detail_payload)


def test_proof_detail_missing_ref_fails_closed() -> None:
    proof_ref = "proof-ref:test:not-present"
    response = client.get(f"/control-center/proof/{proof_ref}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["requested_proof_ref"] == proof_ref
    assert payload["record"]["status"] == "missing_proof_ref"
    assert "blocked-state:proof-detail:proof-ref-not-found" in (
        payload["record"]["blocked_authority_refs"]
    )
    _assert_no_runtime_authority(payload)


def test_proof_cli_inspects_index_and_detail() -> None:
    index_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "inspect-proof",
            "--limit",
            "4",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    index_payload = json.loads(index_result.stdout)
    proof_ref = index_payload["proof_index"]["proof_refs"][0]

    detail_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "inspect-proof",
            proof_ref,
            "--limit",
            "4",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    detail_payload = json.loads(detail_result.stdout)

    assert index_payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-proof-index"
    )
    assert detail_payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-proof-detail"
    )
    assert detail_payload["proof_detail"]["record"]["proof_ref"] == proof_ref
    _assert_no_runtime_authority(index_payload)
    _assert_no_runtime_authority(detail_payload)
