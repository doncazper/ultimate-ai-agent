from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def actor_payload():
    return {
        "actor_type": "human_user",
        "actor_id": "user_123",
        "authority_source": "explicit_user_request",
    }


def test_file_ref_validate_endpoint_blocks_env_file():
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


def test_file_read_preview_endpoint_returns_metadata_only(tmp_path: Path):
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    response = client.post(
        "/files/read/preview",
        json={
            "workspace_root": str(tmp_path),
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
    assert data["data"]["content_hash"]
    assert "raw_content_omitted" in data["data"]["redactions_applied"]
    assert "hello" not in response.text


def test_file_read_preview_endpoint_does_not_echo_hostile_path_or_secret(tmp_path: Path):
    hostile_path = "notes/api_key=supersecretvalue123.txt"
    response = client.post(
        "/files/read/preview",
        json={
            "workspace_root": str(tmp_path),
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


def test_file_write_propose_and_diff_preview_endpoints_are_safe(tmp_path: Path):
    payload = {
        "workspace_root": str(tmp_path),
        "proposal": {
            "proposal_id": "fwp_api",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "target_path": "note.txt",
            "purpose": "proposal",
            "new_content": "hello\n",
            "file_kind": "artifact",
            "sensitivity": "project_private",
            "idempotency_key": "idem_api_file",
        },
    }

    propose_response = client.post("/files/write/propose", json=payload)
    diff_response = client.post("/files/diff/preview", json=payload)

    assert propose_response.status_code == 200
    assert propose_response.json()["data"]["allowed"] is True
    assert diff_response.status_code == 200
    assert "+hello" in diff_response.json()["data"]["diff"]
