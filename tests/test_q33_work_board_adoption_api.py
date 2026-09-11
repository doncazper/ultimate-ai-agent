from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.control_center import (
    WORK_BOARD_ADOPTION_MAX_REQUEST_BODY_BYTES,
    WORK_BOARD_ADOPTION_MAX_REQUEST_NESTING_DEPTH,
)


def _headers(suffix: str, *, confirmed: bool = False) -> dict[str, str]:
    headers = {
        "X-UAA-Idempotency-Key": f"idempotency-ref:work-board-api:{suffix}"
    }
    if confirmed:
        headers["X-UAA-Operator-Confirmed"] = "true"
    return headers


def _create_mutation(revision: int = 0) -> dict[str, object]:
    return {
        "action": "create",
        "expected_revision": revision,
        "target_ref": None,
        "draft": {
            "title": "Prepare the founder briefing",
            "description": "Review the local evidence before Monday.",
            "priority": "high",
            "lane_ref": "work-board-lane:inbox",
            "tag_refs": ["tag-ref:founder"],
        },
        "lane_ref": None,
    }


def test_work_board_adoption_api_completes_exact_local_loop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_WORK_BOARD_STATE_DIR", str(tmp_path / "work-board"))
    client = TestClient(app)

    empty = client.get("/control-center/work-board/adoption")
    assert empty.status_code == 200
    assert empty.headers["Cache-Control"] == "no-store"
    assert empty.json()["data"]["status"] == "ready"
    assert empty.json()["data"]["backup_restore_available"] is True

    mutation = _create_mutation()
    headers = _headers("create")
    preview_response = client.post(
        "/control-center/work-board/adoption/preview",
        json=mutation,
        headers=headers,
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()["data"]
    scope = {
        "mutation": mutation,
        "preview_ref": preview["preview_ref"],
        "approval_ref": preview["approval_ref"],
    }

    missing_confirmation = client.post(
        "/control-center/work-board/adoption/approval",
        json=scope,
        headers=headers,
    )
    assert missing_confirmation.status_code == 403

    confirmed_headers = _headers("create", confirmed=True)
    approval = client.post(
        "/control-center/work-board/adoption/approval",
        json=scope,
        headers=confirmed_headers,
    )
    assert approval.status_code == 200
    assert approval.json()["data"]["mutation_performed"] is False

    committed = client.post(
        "/control-center/work-board/adoption/commit",
        json=scope,
        headers=confirmed_headers,
    )
    assert committed.status_code == 200
    receipt = committed.json()["data"]
    assert receipt["after_revision"] == 1
    assert receipt["task_execution_performed"] is False
    assert receipt["connector_write_performed"] is False

    populated = client.get("/control-center/work-board/adoption").json()["data"]
    assert populated["active_cards"][0]["title"] == (
        "Prepare the founder briefing"
    )

    backup_response = client.post(
        "/control-center/work-board/adoption/backup",
        json={"passphrase": "correct horse battery staple"},
        headers=_headers("backup"),
    )
    assert backup_response.status_code == 200
    backup = backup_response.json()["data"]
    assert "Prepare the founder briefing" not in json.dumps(backup)
    assert backup["private_values_encrypted"] is True


def test_work_board_adoption_restore_api_is_exact_approval_bound(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    monkeypatch.setenv("UAA_WORK_BOARD_STATE_DIR", str(source_dir))
    client = TestClient(app)
    mutation = _create_mutation()
    create_headers = _headers("restore-source", confirmed=True)
    preview = client.post(
        "/control-center/work-board/adoption/preview",
        json=mutation,
        headers=create_headers,
    ).json()["data"]
    scope = {
        "mutation": mutation,
        "preview_ref": preview["preview_ref"],
        "approval_ref": preview["approval_ref"],
    }
    assert client.post(
        "/control-center/work-board/adoption/approval",
        json=scope,
        headers=create_headers,
    ).status_code == 200
    assert client.post(
        "/control-center/work-board/adoption/commit",
        json=scope,
        headers=create_headers,
    ).status_code == 200
    backup = client.post(
        "/control-center/work-board/adoption/backup",
        json={"passphrase": "correct horse battery staple"},
        headers=_headers("restore-backup"),
    ).json()["data"]

    monkeypatch.setenv("UAA_WORK_BOARD_STATE_DIR", str(tmp_path / "target"))
    restore_headers = _headers("restore", confirmed=True)
    restore_request = {
        "passphrase": "correct horse battery staple",
        "backup": backup,
    }
    restore_preview_response = client.post(
        "/control-center/work-board/adoption/restore-preview",
        json=restore_request,
        headers=restore_headers,
    )
    assert restore_preview_response.status_code == 200
    restore_preview = restore_preview_response.json()["data"]
    restore_scope = {
        **restore_request,
        "preview_ref": restore_preview["preview_ref"],
        "approval_ref": restore_preview["approval_ref"],
    }
    denied = client.post(
        "/control-center/work-board/adoption/restore-commit",
        json=restore_scope,
        headers=restore_headers,
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == (
        "WORK_BOARD_ADOPTION_EXACT_APPROVAL_REQUIRED"
    )

    approved = client.post(
        "/control-center/work-board/adoption/restore-approval",
        json=restore_scope,
        headers=restore_headers,
    )
    assert approved.status_code == 200
    restored = client.post(
        "/control-center/work-board/adoption/restore-commit",
        json=restore_scope,
        headers=restore_headers,
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["action"] == "restore_backup"
    assert client.get("/control-center/work-board/adoption").json()["data"][
        "active_cards"
    ][0]["title"] == "Prepare the founder briefing"


def test_work_board_body_guard_rejects_oversize_and_deep_json_with_cors() -> None:
    client = TestClient(app)
    origin = "http://127.0.0.1:5173"
    oversized = client.post(
        "/control-center/work-board/adoption/restore-preview",
        content=b"{" + b"x" * WORK_BOARD_ADOPTION_MAX_REQUEST_BODY_BYTES,
        headers={
            "content-type": "application/json",
            "content-length": "1",
            "Origin": origin,
            **_headers("oversize"),
        },
    )
    assert oversized.status_code == 413
    assert oversized.headers["Cache-Control"] == "no-store"
    assert oversized.headers["Access-Control-Allow-Origin"] == origin
    assert oversized.json()["code"] == (
        "WORK_BOARD_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"
    )

    deeply_nested = b"[" * (WORK_BOARD_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    deeply_nested += b"]" * (WORK_BOARD_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    for route in (
        "/control-center/work-board/adoption/preview",
        "/control-center/work-board/adoption/approval",
        "/control-center/work-board/adoption/commit",
        "/control-center/work-board/adoption/backup",
        "/control-center/work-board/adoption/restore-preview",
        "/control-center/work-board/adoption/restore-approval",
        "/control-center/work-board/adoption/restore-commit",
    ):
        response = client.post(
            route,
            content=deeply_nested,
            headers={
                "content-type": "application/json",
                **_headers("body-guard", confirmed=True),
            },
        )
        assert response.status_code == 413, route
        assert response.json()["code"] == (
            "WORK_BOARD_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"
        )


def test_work_board_body_limit_is_published_for_every_json_route() -> None:
    paths = app.openapi()["paths"]
    for route in (
        "/control-center/work-board/adoption/preview",
        "/control-center/work-board/adoption/approval",
        "/control-center/work-board/adoption/commit",
        "/control-center/work-board/adoption/backup",
        "/control-center/work-board/adoption/restore-preview",
        "/control-center/work-board/adoption/restore-approval",
        "/control-center/work-board/adoption/restore-commit",
    ):
        schema = paths[route]["post"]["responses"]["413"]["content"][
            "application/json"
        ]["schema"]
        assert schema["$ref"].endswith("/WorkBoardAdoptionBodyLimitResponse")
