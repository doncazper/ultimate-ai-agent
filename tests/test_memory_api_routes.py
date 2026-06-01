from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def actor_payload():
    return {
        "actor_type": "human_user",
        "actor_id": "user_123",
        "authority_source": "explicit_user_request",
        "workspace_id": "workspace_123",
        "project_id": "proj_123",
    }


def test_memory_record_validate_endpoint_blocks_secret():
    response = client.post(
        "/memory/records/validate",
        json={
            "memory_id": "mem_secret_api",
            "memory_type": "semantic",
            "scope": "user",
            "authority": "user_provided",
            "sensitivity": "user_private",
            "content": "api_key='abcdefghijklmnop'",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "MEMORY_RECORD_INVALID"
    assert "abcdefghijklmnop" not in response.text


def test_memory_write_evaluate_endpoint_returns_decision_without_persistence():
    response = client.post(
        "/memory/write/evaluate",
        json={
            "request_id": "mwr_api",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "memory_type": "preference",
            "scope": "user",
            "user_id": "user_123",
            "content": "User prefers compact summaries.",
            "authority": "user_provided",
            "sensitivity": "user_private",
            "idempotency_key": "idem_api",
            "consent_ref": "consent_123",
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["allowed"] is True


def test_memory_query_preview_endpoint_is_validation_only():
    response = client.post(
        "/memory/query/preview",
        json={
            "request_id": "mrr_api",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "query": "summaries",
            "scope": "user",
            "max_results": 3,
            "consent_ref": "consent_123",
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["allowed"] is True
    assert data["data"]["results"] == []
