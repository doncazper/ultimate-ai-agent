from typing import Any
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.mattermost import (
    MATTERMOST_AUTO_CREATE_ROLES_ENV,
    MATTERMOST_BRIDGE_BEARER_ENV,
    MATTERMOST_BRIDGE_ENV,
    MATTERMOST_BRIDGE_STORAGE_DIR_ENV,
    MATTERMOST_REPLY_ENABLED_ENV,
)

client = TestClient(app)


def _headers() -> dict[str, Any]:
    return {
        "Authorization": "Bearer local-mattermost",
        "X-UAA-Idempotency-Key": "idempotency:mattermost-api",
    }


def _enable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, reply: bool = True, auto_create: bool = False) -> None:
    monkeypatch.setenv(MATTERMOST_BRIDGE_ENV, "1")
    monkeypatch.setenv(MATTERMOST_BRIDGE_BEARER_ENV, "local-mattermost")
    monkeypatch.setenv(MATTERMOST_BRIDGE_STORAGE_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(MATTERMOST_REPLY_ENABLED_ENV, "1" if reply else "0")
    monkeypatch.setenv(MATTERMOST_AUTO_CREATE_ROLES_ENV, "1" if auto_create else "0")


def _bind_payload(**updates: Any) -> Any:
    payload = {
        "workspace_ref": "mattermost-workspace:local",
        "channel_ref": "mattermost-channel:town-square",
        "role_ids": ["planner"],
        "trigger_policy": {"mode": "mention_command", "max_replies_per_thread": 2},
        "reply_enabled": True,
        "created_by_ref": "mattermost-user:admin",
    }
    payload.update(updates)
    return payload


def _event_payload(**updates: Any) -> Any:
    payload = {
        "event_ref": "mattermost-event:post1",
        "workspace_ref": "mattermost-workspace:local",
        "channel_ref": "mattermost-channel:town-square",
        "message_ref": "mattermost-message:post1",
        "thread_ref": "mattermost-thread:root1",
        "actor_ref": "mattermost-actor:plugin",
        "user_ref": "mattermost-user:alice",
        "message_preview": "@uaa-planner please plan this",
        "idempotency_key": "mattermost-idempotency:post1",
        "mentioned_role_ids": ["planner"],
        "is_direct_mention": True,
    }
    payload.update(updates)
    return payload


def test_mattermost_status_is_public_metadata_and_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MATTERMOST_BRIDGE_ENV, raising=False)

    response = client.get("/integrations/mattermost/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["enabled"] is False
    assert "mattermost_raw_transcript_storage" in body["data"]["capabilities_blocked"]


def test_mattermost_protected_routes_require_enabled_bridge_and_bearer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(MATTERMOST_BRIDGE_ENV, raising=False)
    disabled = client.get("/integrations/mattermost/audit")
    catalog_disabled = client.get("/integrations/mattermost/roles/catalog")

    _enable(monkeypatch, tmp_path)
    wrong = client.get("/integrations/mattermost/audit", headers={"Authorization": "Bearer wrong"})

    assert disabled.status_code == 403
    assert catalog_disabled.status_code == 403
    assert wrong.status_code == 401


def test_mattermost_role_catalog_and_suggestions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _enable(monkeypatch, tmp_path, auto_create=True)

    catalog = client.get("/integrations/mattermost/roles/catalog", headers=_headers())
    suggestions = client.post(
        "/integrations/mattermost/roles/suggest",
        headers=_headers(),
        json={
            "prompt_preview": "We need a planner and safety reviewer",
            "role_creation_mode": "proposal_then_approve",
            "desired_count": 2,
        },
    )
    auto_created = client.post(
        "/integrations/mattermost/roles/suggest",
        headers=_headers(),
        json={
            "prompt_preview": "Create incident commander role",
            "role_creation_mode": "auto_create",
            "auto_create_allowed": True,
            "desired_count": 1,
        },
    )

    assert catalog.status_code == 200
    assert [role["role_id"] for role in catalog.json()["data"]["roles"]][:2] == ["planner", "summarizer"]
    assert suggestions.status_code == 200
    assert suggestions.json()["data"]["suggestions"][0]["requires_approval"] is True
    assert auto_created.status_code == 200
    assert auto_created.json()["data"]["suggestions"][0]["status"] == "auto_created"


def test_mattermost_bind_message_receipts_and_audit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _enable(monkeypatch, tmp_path)

    bind = client.post("/integrations/mattermost/roles/bind", headers=_headers(), json=_bind_payload())
    event = client.post("/integrations/mattermost/events/message", headers=_headers(), json=_event_payload())
    audit = client.get("/integrations/mattermost/audit", headers=_headers())
    receipts = client.get("/integrations/mattermost/receipts", headers=_headers())

    assert bind.status_code == 200
    assert bind.json()["data"]["binding"]["reply_enabled"] is True
    assert event.status_code == 200
    body = event.json()
    assert body["data"]["status"] == "reply_proposed"
    assert body["data"]["reply_commands"][0]["role_id"] == "planner"
    assert body["data"]["receipt"]["stored_raw_transcript"] is False
    assert audit.json()["data"]["events"]
    assert receipts.json()["data"]["receipts"]
    stored = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.glob("*.jsonl"))
    assert "@uaa-planner please plan this" not in stored


def test_mattermost_tool_action_returns_approval_required(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _enable(monkeypatch, tmp_path)
    client.post(
        "/integrations/mattermost/roles/bind",
        headers=_headers(),
        json=_bind_payload(
            role_ids=["implementer"],
            trigger_policy={"mode": "enabled_room"},
        ),
    )

    response = client.post(
        "/integrations/mattermost/events/message",
        headers=_headers(),
        json=_event_payload(
            event_ref="mattermost-event:post2",
            message_ref="mattermost-message:post2",
            idempotency_key="mattermost-idempotency:post2",
            message_preview="@uaa-implementer execute external capability",
            mentioned_role_ids=["implementer"],
        ),
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["status"] == "approval_required"
    assert body["approval_required"] is True
    assert body["reply_commands"] == []


def test_mattermost_unbind_disables_channel(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _enable(monkeypatch, tmp_path)
    client.post("/integrations/mattermost/roles/bind", headers=_headers(), json=_bind_payload())

    response = client.post(
        "/integrations/mattermost/roles/unbind",
        headers=_headers(),
        json={
            "workspace_ref": "mattermost-workspace:local",
            "channel_ref": "mattermost-channel:town-square",
            "role_ids": ["planner"],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["binding"]["enabled"] is False
