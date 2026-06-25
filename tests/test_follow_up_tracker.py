from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.follow_up_tracker import (
    FOLLOW_UP_TRACKER_CATEGORY_ORDER,
    FOLLOW_UP_TRACKER_CONTRACT_REF,
    FOLLOW_UP_TRACKER_READ_MODEL_SOURCE,
    FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS,
    FollowUpTrackerItem,
    build_follow_up_tracker_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def _assert_follow_up_tracker(tracker: dict[str, object]) -> None:
    assert tracker["contract_ref"] == FOLLOW_UP_TRACKER_CONTRACT_REF
    assert tracker["source"] == FOLLOW_UP_TRACKER_READ_MODEL_SOURCE
    assert tracker["backend_owned"] is True
    assert tracker["local_read_model_only"] is True
    assert tracker["safe_refs_only"] is True
    assert tracker["raw_content_included"] is False
    assert tracker["category_order"] == list(FOLLOW_UP_TRACKER_CATEGORY_ORDER)
    assert set(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS) <= set(
        tracker["blocked_state_refs"]
    )
    for field_name in [
        "reminder_scheduler_enabled",
        "message_send_enabled",
        "connector_read_enabled",
        "connector_write_enabled",
        "email_calendar_fetch_enabled",
        "automatic_task_creation_enabled",
        "action_execution_enabled",
        "runtime_model_calls_enabled",
        "context_injection_authorized",
        "hidden_memory_write_authorized",
        "production_authority_enabled",
    ]:
        assert tracker[field_name] is False
    assert tracker["items"]
    categories = {item["category"] for item in tracker["items"]}
    assert "relationship_follow_up" in categories
    assert "promise" in categories
    assert "pending_reply" in categories
    for item in tracker["items"]:
        assert item["review_required"] is True
        assert item["local_review_only"] is True
        assert item["safe_refs_only"] is True
        assert set(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS) <= set(
            item["blocked_state_refs"]
        )
        for field_name in [
            "reminder_scheduler_enabled",
            "message_send_enabled",
            "connector_read_enabled",
            "connector_write_enabled",
            "email_calendar_fetch_enabled",
            "automatic_task_creation_enabled",
            "action_execution_enabled",
            "runtime_model_calls_enabled",
            "context_injection_authorized",
            "hidden_memory_write_authorized",
            "production_authority_enabled",
        ]:
            assert item[field_name] is False


def test_follow_up_tracker_surfaces_from_storage_read_models(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today = repo.today_summary()
    inbox = repo.actions_inbox()
    briefing = repo.morning_briefing()

    for payload in [today, inbox, briefing]:
        assert (
            payload["follow_up_tracker_contract_ref"] == FOLLOW_UP_TRACKER_CONTRACT_REF
        )
        _assert_follow_up_tracker(payload["follow_up_tracker"])


def test_follow_up_tracker_api_today_summary_returns_backend_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))

    for route in [
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
    ]:
        response = client.get(route)
        assert response.status_code == 200
        payload = response.json()["data"]

        assert (
            payload["follow_up_tracker_contract_ref"]
            == FOLLOW_UP_TRACKER_CONTRACT_REF
        )
        _assert_follow_up_tracker(payload["follow_up_tracker"])


def test_follow_up_tracker_cli_inspection_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
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
            str(ROOT / "scripts/inspect_follow_up_tracker.py"),
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
    assert payload["contract_ref"] == FOLLOW_UP_TRACKER_CONTRACT_REF
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["message_send_enabled"] is False
    assert payload["email_calendar_fetch_enabled"] is False
    assert payload["automatic_task_creation_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["model_provider_call_authorized"] is False
    assert payload["automatic_memory_write_authorized"] is False
    assert payload["context_injection_authorized"] is False
    _assert_follow_up_tracker(payload["follow_up_tracker"])

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
            str(ROOT / "scripts/inspect_follow_up_tracker.py"),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["follow_up_tracker"]["items"] == []
    assert not missing_state_dir.exists()


def test_follow_up_tracker_redacts_dirty_action_content() -> None:
    read_model = build_follow_up_tracker_read_model(
        actions=[
            {
                "item_ref": "founder-action:test-dirty-follow-up",
                "status": "deferred",
                "action_group_id": "username hostname raw_prompt /Users/example",
                "safe_summary": "provider_payload api_key secret username hostname",
                "evidence_refs": ["evidence-ref:test-dirty-follow-up"],
                "blocked_state_refs": [
                    "username value",
                    "hostname value",
                    "raw_prompt marker",
                    "raw prompt marker",
                    "raw log marker",
                    "/Users/example/raw-path",
                    "/home/example/raw-path",
                    "/tmp/example/raw-path",
                    "/var/example/raw-path",
                    "C:\\Users\\example\\raw-path",
                    "environment dump marker",
                    "serial marker",
                    "secret marker",
                ],
            }
        ],
        memory_items=[],
        memory_review_decisions=[],
        crm_lite_followups=[],
        source_readiness_items=[],
        evidence_timeline=[],
    )

    serialized = json.dumps(read_model, sort_keys=True).lower()
    for forbidden in [
        "username",
        "hostname",
        "raw_prompt",
        "raw prompt",
        "raw log",
        "/users/",
        "/home/",
        "/tmp/",
        "/var/",
        "c:\\",
        "environment dump",
        "serial",
        "provider_payload",
        "api_key",
        "secret marker",
    ]:
        assert forbidden not in serialized
    assert "founder-action:test-dirty-follow-up" in serialized
    assert "action inbox item remains reviewable local state" in serialized


def test_follow_up_tracker_derives_promise_refs_from_reviewed_memory_items() -> None:
    read_model = build_follow_up_tracker_read_model(
        actions=[],
        memory_items=[
            {
                "review_ref": "memory-review:test-promise",
                "business_memory_candidate_kind": "promise",
                "business_memory_candidate_ref": "business-memory-candidate:promise:test-promise",
                "review_state": "reviewed",
                "safe_summary": "Reviewed promise candidate remains local recall.",
                "source_refs": ["source-ref:test-promise"],
                "evidence_refs": ["evidence-ref:test-promise"],
                "business_memory_blocker_refs": ["blocked-state:no-memory-write"],
                "business_memory_next_safe_action": "Review evidence before follow-up.",
            }
        ],
        memory_review_decisions=[],
        crm_lite_followups=[],
        source_readiness_items=[],
        evidence_timeline=[],
    )

    assert read_model["promise_refs"] == [
        "business-memory-candidate:promise:test-promise"
    ]
    item = read_model["items"][0]
    assert item["category"] == "promise"
    assert item["promise_ref"] == "business-memory-candidate:promise:test-promise"
    assert item["memory_refs"] == [
        "memory-review:test-promise",
        "business-memory-candidate:promise:test-promise",
    ]
    assert item["action_execution_enabled"] is False
    assert item["message_send_enabled"] is False
    assert item["hidden_memory_write_authorized"] is False


def test_follow_up_tracker_item_rejects_runtime_authority_flags() -> None:
    base = {
        "item_ref": "follow-up-ref:test-authority-denied",
        "category": "open_loop",
        "title": "Open loop",
        "status": "review_only",
        "source_state": "reviewed_ref",
        "safe_summary": "Safe local follow-up ref.",
        "why_shown": "Operator review is required.",
        "next_safe_action": "Review safe refs only.",
        "authority_boundary": "No runtime authority is granted.",
        "blocked_state_refs": list(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS),
    }
    for field_name in [
        "reminder_scheduler_enabled",
        "message_send_enabled",
        "connector_read_enabled",
        "connector_write_enabled",
        "email_calendar_fetch_enabled",
        "automatic_task_creation_enabled",
        "action_execution_enabled",
        "runtime_model_calls_enabled",
        "context_injection_authorized",
        "hidden_memory_write_authorized",
        "production_authority_enabled",
    ]:
        with pytest.raises(ValueError):
            FollowUpTrackerItem(**{**base, field_name: True})
