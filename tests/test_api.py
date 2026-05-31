from fastapi.testclient import TestClient
from ultimate_ai_agent.api.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.6.0"

def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.6.0"

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

def test_validate_event_endpoint():
    event_data = {
        "event_id": "evt_api_test",
        "event_type": "run",
        "event_name": "run.created",
        "run_id": "run_api_123",
        "trace_id": "trace_api",
        "span_id": "span_api",
        "correlation_id": "corr_api",
        "actor_context": {
            "actor_type": "orchestrator",
            "actor_id": "test_orchestrator",
            "authority_source": "explicit_user_request"
        },
        "temporal_context": {
            "current_time_utc": "2026-05-30T12:00:00",
            "freshness_class": "daily",
            "staleness_policy": "allow_with_label"
        },
        "data_classification": {
            "classification": "public",
            "source": "bootstrap"
        },
        "event_source": "test_source",
        "subject": "Agent Execution",
        "action": "start",
        "outcome": "started",
        "status": "success",
        "severity": "info"
    }
    response = client.post("/events/validate", json=event_data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True

def test_validate_transition_endpoint():
    payload = {
        "run_id": "run_api_123",
        "current_state": "created",
        "next_state": "contract_created"
    }
    response = client.post("/runs/state/transition/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True

def test_validate_transition_endpoint_invalid():
    payload = {
        "run_id": "run_api_123",
        "current_state": "created",
        "next_state": "planned"
    }
    response = client.post("/runs/state/transition/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is False
    assert res_json["error"]["code"] == "INVALID_STATE_TRANSITION"

def test_preview_receipt_endpoint():
    payload = {
        "run_id": "run_api_123",
        "events": [
            {
                "event_id": "evt_1",
                "event_type": "run",
                "event_name": "run.created",
                "run_id": "run_api_123",
                "trace_id": "trace_api",
                "span_id": "span_api",
                "correlation_id": "corr_api",
                "actor_context": {
                    "actor_type": "orchestrator",
                    "actor_id": "test_orchestrator",
                    "authority_source": "explicit_user_request"
                },
                "temporal_context": {
                    "current_time_utc": "2026-05-30T12:00:00",
                    "freshness_class": "daily",
                    "staleness_policy": "allow_with_label"
                },
                "data_classification": {
                    "classification": "public",
                    "source": "bootstrap"
                },
                "event_source": "test_source",
                "subject": "Agent Execution",
                "action": "start",
                "outcome": "started",
                "status": "success",
                "severity": "info"
            }
        ]
    }
    response = client.post("/receipts/preview", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["run_id"] == "run_api_123"
    assert res_json["data"]["event_count"] == 1

