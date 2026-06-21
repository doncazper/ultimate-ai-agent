from typing import Any
import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def actor_payload() -> dict[str, Any]:
    return {
        "actor_type": "human_user",
        "actor_id": "user_123",
        "authority_source": "explicit_user_request",
    }


def test_file_ref_validate_endpoint_blocks_env_file() -> None:
    response = client.post(
        "/files/refs/validate",
        json={
            "file_ref": "file_env",
            "path": ".env",
            "kind": "artifact",
            "sensitivity": "credential_secret",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False


def test_file_read_preview_endpoint_returns_metadata_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    response = client.post(
        "/files/read/preview",
        json={
            "request": {
                "request_id": "frr_api",
                "run_id": "run_123",
                "actor_context": actor_payload(),
                "path": "note.txt",
                "purpose": "preview",
                "max_bytes": 100,
            },
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["text_preview"] == ""
    assert data["data"]["size_bytes"] == 5
    assert data["data"]["content_hash"] == "redacted"
    assert "raw_content_omitted" in data["data"]["redactions_applied"]
    assert "hello" not in response.text


def test_file_read_preview_endpoint_rejects_caller_selected_workspace_root(tmp_path: Path) -> None:
    response = client.post(
        "/files/read/preview",
        json={
            "workspace_root": str(tmp_path),
            "request": {
                "request_id": "frr_caller_root",
                "run_id": "run_123",
                "actor_context": actor_payload(),
                "path": "note.txt",
                "purpose": "preview",
                "max_bytes": 100,
            },
        },
    )

    assert response.status_code == 422
    assert str(tmp_path) not in response.text


def test_file_read_preview_endpoint_does_not_echo_hostile_path_or_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    hostile_path = "notes/api_key=supersecretvalue123.txt"
    response = client.post(
        "/files/read/preview",
        json={
            "request": {
                "request_id": "frr_hostile",
                "run_id": "run_123",
                "actor_context": actor_payload(),
                "path": hostile_path,
                "purpose": "preview",
                "max_bytes": 100,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "supersecretvalue123" not in response.text
    assert hostile_path not in response.text


def test_file_tree_preview_endpoint_returns_safe_refs_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "visible.txt").write_text("hello", encoding="utf-8")

    response = client.post(
        "/files/tree/preview",
        json={
            "request": {
                "request_id": "ftp_api",
                "run_id": "run_123",
                "actor_context": actor_payload(),
                "root_path": "docs",
                "purpose": "safe tree preview",
                "max_depth": 1,
                "max_entries": 10,
            },
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["root_ref"].startswith("file_tree_")
    assert body["data"]["entries"][0]["entry_ref"].startswith("file_tree_")
    assert "raw_paths_omitted" in body["data"]["redactions_applied"]
    assert "safe_refs_only" in body["data"]["redactions_applied"]
    assert "docs" not in response.text
    assert "visible.txt" not in response.text
    assert "hello" not in response.text


def test_file_tree_preview_endpoint_does_not_echo_hostile_root_or_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    hostile_root = "notes/api_key=supersecretvalue123"

    response = client.post(
        "/files/tree/preview",
        json={
            "request": {
                "request_id": "ftp_hostile",
                "run_id": "run_123",
                "actor_context": actor_payload(),
                "root_path": hostile_root,
                "purpose": "safe tree preview",
                "max_depth": 1,
                "max_entries": 10,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "supersecretvalue123" not in response.text
    assert hostile_root not in response.text


def test_file_write_propose_and_diff_preview_endpoints_are_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    payload = {
        "proposal": {
            "proposal_id": "fwp_api",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "target_path": "note.txt",
            "purpose": "proposal",
            "new_content_ref": "content-ref:fwp-api",
            "file_kind": "artifact",
            "sensitivity": "project_private",
            "idempotency_key": "idem_api_file",
        },
    }

    propose_response = client.post("/files/write/propose", json=payload)
    diff_response = client.post("/files/diff/preview", json=payload)

    assert propose_response.status_code == 200
    assert propose_response.json()["success"] is True
    assert propose_response.json()["data"]["allowed"] is True
    assert diff_response.status_code == 200
    assert diff_response.json()["data"]["raw_diff_omitted"] is True
    assert "content_ref_only=True" in diff_response.json()["data"]["diff_summary"]
    assert "hello" not in diff_response.text


def test_file_write_propose_endpoint_reports_failure_when_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FILE_API_SAFE_ROOT", str(tmp_path))
    payload = {
        "proposal": {
            "proposal_id": "fwp_api_blocked",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "target_path": "note.txt",
            "purpose": "proposal",
            "new_content_ref": "content-ref:fwp-api",
            "file_kind": "artifact",
            "sensitivity": "credential_secret",
            "idempotency_key": "idem_api_file_blocked",
        },
    }

    response = client.post("/files/write/propose", json=payload)

    # A blocked proposal must not report success at the envelope level.
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["allowed"] is False
    assert body["success"] is False
