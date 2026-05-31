from fastapi.testclient import TestClient
from ultimate_ai_agent.api.app import app

client = TestClient(app)

def test_validate_consent_grant_endpoint():
    payload = {
        "consent_id": "grant_api_test",
        "subject_type": "tool",
        "subject_id": "file_reader",
        "granted_to_actor": "orchestrator",
        "on_behalf_of_user_id": "user_123",
        "scope_type": "project",
        "allowed_actions": ["read"],
        "source": "api_test"
    }
    response = client.post("/consent/grants/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["consent_id"] == "grant_api_test"

def test_evaluate_consent_endpoint():
    payload = {
        "query": {
            "actor_id": "orchestrator",
            "action": "read",
            "resource": "file_reader",
            "purpose": "reading configuration"
        },
        "grants": [
            {
                "consent_id": "grant_api_test",
                "subject_type": "tool",
                "subject_id": "file_reader",
                "granted_to_actor": "orchestrator",
                "on_behalf_of_user_id": "user_123",
                "scope_type": "project",
                "allowed_actions": ["read"],
                "source": "api_test"
            }
        ]
    }
    response = client.post("/consent/evaluate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["allowed"] is True

def test_validate_tool_manifest_endpoint():
    payload = {
        "tool_id": "mock_validator",
        "display_name": "Mock Validator",
        "category": "mock",
        "description": "Dry-run validator tool",
        "execution_mode": "dry_run",
        "risk_level": "safe",
        "capability_flag": "mock_active",
        "owner": "orchestrator",
        "source": "system",
        "version": "1.0.0"
    }
    response = client.post("/tools/manifests/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["tool_id"] == "mock_validator"
