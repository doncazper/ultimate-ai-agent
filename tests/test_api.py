from fastapi.testclient import TestClient
from ultimate_ai_agent.api.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.10.1"

def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.10.1"


def test_openapi_schema_generation_reports_current_version():
    schema = app.openapi()

    assert schema["info"]["version"] == "0.10.1"
    assert "/health" in schema["paths"]
    assert "/version" in schema["paths"]
    assert "/gate/reports/validate" in schema["paths"]


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

def test_validate_world_state_endpoint():
    payload = {
        "world_state_id": "ws_api_test",
        "run_id": "run_api_123",
        "current_phase": "execution",
        "current_step": "step_1",
        "completed_steps": [],
        "last_event_id": "evt_abc",
        "created_at": "2026-05-31T12:00:00Z",
        "updated_at": "2026-05-31T12:00:00Z"
    }
    response = client.post("/world-state/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["world_state_id"] == "ws_api_test"

def test_validate_context_budget_endpoint():
    payload = {
        "model_context_limit": 8000,
        "system_prompt_tokens": 1000,
        "tool_schema_tokens": 500,
        "world_state_tokens": 200,
        "context_pack_tokens": 300,
        "completion_reserve_tokens": 2000,
        "safety_margin_tokens": 1000,
        "token_calibration_factor": 1.0,
        "unknown_limit_fails_closed": True
    }
    response = client.post("/context-budget/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["available_history_tokens"] == 3000

def test_validate_local_runtime_endpoint():
    payload = {
        "manifest": {
            "runtime_id": "rt_ollama",
            "runtime_type": "ollama",
            "model_profile": {
                "model_id": "llama3",
                "context_window": 8192
            },
            "privacy_mode": "local_only"
        }
    }
    response = client.post("/local-runtime/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True

def test_validate_adapter_manifest_endpoint():
    payload = {
        "manifest": {
            "adapter_id": "aider",
            "adapter_type": "aider",
            "version": "0.30.0"
        },
        "policy": {
            "policy_id": "p1"
        }
    }
    response = client.post("/adapter-manifest/validate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
