from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.today_loop import (
    TODAY_LOOP_LANE_ORDER,
    TODAY_LOOP_REQUIRED_BLOCKED_REFS,
    TODAY_LOOP_TIGHTENING_CONTRACT_REF,
    build_today_loop_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def _assert_today_loop_read_model(today_loop: dict[str, object]) -> None:
    assert today_loop["contract_ref"] == TODAY_LOOP_TIGHTENING_CONTRACT_REF
    assert today_loop["source"] == "python_core_today_loop_read_model"
    assert today_loop["backend_owned"] is True
    assert today_loop["local_read_model_only"] is True
    assert today_loop["safe_refs_only"] is True
    assert today_loop["raw_content_included"] is False
    assert today_loop["lane_order"] == list(TODAY_LOOP_LANE_ORDER)
    assert {lane["lane_id"] for lane in today_loop["lanes"]} == set(
        TODAY_LOOP_LANE_ORDER
    )
    assert today_loop["digest_items"]
    assert today_loop["what_matters_now_refs"]
    assert today_loop["needs_review_refs"]
    assert today_loop["blocked_now_refs"]
    assert today_loop["follow_up_refs"]
    assert today_loop["stale_or_deferred_refs"]
    assert set(TODAY_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        today_loop["blocked_state_refs"]
    )
    for field_name in [
        "action_execution_enabled",
        "connector_runtime_enabled",
        "source_refresh_enabled",
        "runtime_model_calls_enabled",
        "automatic_memory_write_authorized",
        "context_injection_authorized",
        "production_authority_enabled",
    ]:
        assert today_loop[field_name] is False
    for item in today_loop["digest_items"]:
        assert item["safe_refs_only"] is True
        assert item["source_refs"] or item["evidence_refs"] or item["receipt_refs"]
        for field_name in [
            "action_execution_enabled",
            "connector_runtime_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            assert item[field_name] is False


def test_today_loop_storage_summary_returns_backend_owned_read_model(
    tmp_path: Path,
) -> None:
    today = FounderLoopRepository(tmp_path / "founder_loop").today_summary()

    assert (
        today["today_loop_tightening_contract_ref"]
        == TODAY_LOOP_TIGHTENING_CONTRACT_REF
    )
    _assert_today_loop_read_model(today["today_loop_read_model"])


def test_today_loop_api_summary_returns_backend_owned_read_model(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))

    response = client.get("/control-center/today/summary")
    assert response.status_code == 200
    today = response.json()["data"]

    assert (
        today["today_loop_tightening_contract_ref"]
        == TODAY_LOOP_TIGHTENING_CONTRACT_REF
    )
    _assert_today_loop_read_model(today["today_loop_read_model"])


def test_today_loop_cli_inspection_is_read_only_and_redacted(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder_loop"
    FounderLoopRepository(state_dir)
    before = {
        path.relative_to(state_dir): path.read_bytes()
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_today_loop.py"),
            "--state-dir",
            str(state_dir),
            "--limit",
            "5",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    after = {
        path.relative_to(state_dir): path.read_bytes()
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    assert before == after
    assert payload["contract_ref"] == TODAY_LOOP_TIGHTENING_CONTRACT_REF
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["action_execution_enabled"] is False
    assert payload["connector_reads_enabled"] is False
    assert payload["model_provider_call_authorized"] is False
    assert payload["automatic_memory_write_authorized"] is False
    assert payload["context_injection_authorized"] is False
    _assert_today_loop_read_model(payload["today_loop_read_model"])

    serialized = json.dumps(payload, sort_keys=True).lower()
    for forbidden in [
        str(tmp_path).lower(),
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "api_key",
        "authorization",
        "cookie",
        "password",
        "private_key",
        "username",
        "hostname",
    ]:
        assert forbidden not in serialized

    missing_state_dir = tmp_path / "missing_state"
    missing = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_today_loop.py"),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["today_loop_read_model"]["digest_items"] == []
    assert not missing_state_dir.exists()


def test_today_loop_read_model_redacts_dirty_memory_blocker_text() -> None:
    read_model = build_today_loop_read_model(
        actions=[],
        plans=[],
        memory_items=[
            {
                "review_ref": "memory-review:test-dirty-blockers",
                "title": "Username hostname blocker title",
                "safe_summary": "Reviewed memory candidate needs local review.",
                "review_state": "review_needed",
                "priority": "high",
                "source_refs": ["source-ref:test-dirty-blockers"],
                "provenance_refs": ["provenance-ref:test-dirty-blockers"],
                "evidence_refs": ["evidence-ref:test-dirty-blockers"],
                "receipt_refs": [],
                "blocked_states": [
                    "username value",
                    "hostname value",
                    "raw_prompt marker",
                    "/Users/example/raw-path",
                    "secret marker",
                ],
                "stale_state": "recheck_required",
                "next_safe_action": "Review safe refs before recall use.",
            }
        ],
        briefing_items=[],
        evidence_timeline=[],
        chat_turn_receipts=[],
        chat_handoff_receipts=[],
        memory_review_decisions=[],
        crm_lite_followups=[],
        source_readiness_items=[],
    )

    serialized = json.dumps(read_model, sort_keys=True).lower()
    for forbidden in [
        "username",
        "hostname",
        "raw_prompt",
        "/users/",
        "secret marker",
    ]:
        assert forbidden not in serialized
    assert "blocked-state:today-loop-memory:redacted" in serialized
    assert read_model["digest_items"][0]["title"] == "Memory review"
