from fastapi.testclient import TestClient
from ultimate_ai_agent.api.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.5.9"

def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.5.9"

def test_validate_contract_endpoint():
    contract_data = {
        "contract_id": "ec_test_api",
        "run_id": "run_api_123",
        "workspace_id": "ws_api",
        "user_id": "usr_api",
        "request_summary": "Test summary",
        "goal": "Verify API",
        "deliverable": "Valid payload",
        "mode": "answer",
        "acceptance_criteria": ["Criteria 1"]
    }
    response = client.post("/contracts/validate", json=contract_data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True

def test_validate_context_pack_endpoint():
    context_pack_data = {
        "context_pack_id": "cp_test_api",
        "contract_id": "ec_test_api",
        "run_id": "run_api_123",
        "workspace_id": "ws_api",
        "user_id": "usr_api",
        "active_goal": "Goal",
        "token_budget": 5000
    }
    response = client.post("/context-packs/validate", json=context_pack_data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
