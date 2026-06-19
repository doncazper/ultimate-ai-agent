from fastapi.testclient import TestClient

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import active_baseline_label
from ultimate_ai_agent.api.openapi import forbidden_raw_provider_schema_fields, forbidden_raw_secret_schema_fields


client = TestClient(app)


def test_api_manifest_endpoint_is_metadata_only_and_versioned():
    response = client.get("/api/manifest")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["api_version"] == __version__
    assert manifest["package_version"] == __version__
    assert manifest["active_baseline"] == active_baseline_label()
    assert manifest["no_runtime_integrations"] is True
    assert "runtime_model_calls" in manifest["capabilities_blocked"]
    assert "web_fetching" in manifest["capabilities_blocked"]
    assert "api_contract_metadata" in manifest["capabilities_declared"]
    assert "local_loopback_gateway_explicit_bearer_required" in manifest["capabilities_declared"]
    assert "local_loopback_gateway_allowlisted_response_shape" in manifest["capabilities_declared"]
    assert manifest["route_count"] >= 43
    assert any(route["path"] == "/api/manifest" and route["method"] == "GET" for route in manifest["routes"])


def test_api_manifest_route_inventory_has_stable_operation_ids_and_side_effect_classes():
    manifest = client.get("/api/manifest").json()
    operation_ids = [route["operation_id"] for route in manifest["routes"]]

    assert len(operation_ids) == len(set(operation_ids))
    assert "get_api_manifest" in operation_ids
    assert all(route["side_effect_class"] != "production_runtime" for route in manifest["routes"])
    assert all(route["requires_auth_future"] is True for route in manifest["routes"])
    assert all(route["blocked_from_production"] is True for route in manifest["routes"])
    routes_by_path = {route["path"]: route for route in manifest["routes"]}
    assert routes_by_path["/v1/chat/completions"]["side_effect_class"] == "local_dev_workspace_only"
    assert routes_by_path["/files/read/preview"]["side_effect_class"] == "local_dev_workspace_only"
    assert "file_api_caller_selected_roots" in manifest["capabilities_blocked"]
    assert "file_api_raw_content_write_payload" in manifest["capabilities_blocked"]
    assert "secret_api_raw_secret_values" in manifest["capabilities_blocked"]
    assert "local_loopback_default_bearer" in manifest["capabilities_blocked"]
    assert "local_loopback_raw_provider_payload_passthrough" in manifest["capabilities_blocked"]
    assert "task_decomposition_raw_request_echo" in manifest["capabilities_blocked"]


def test_validation_error_response_does_not_echo_secret_like_payload():
    secret_value = "ABCDEFGHIJKLMNOP"
    payload = {
        "event_id": "evt_api_secret",
        "event_type": "run",
        "event_name": "run.created",
        "run_id": "run_api_secret",
        "trace_id": "trace_api",
        "span_id": "span_api",
        "correlation_id": "corr_api",
        "actor_context": {
            "actor_type": "orchestrator",
            "actor_id": "test_orchestrator",
            "authority_source": "explicit_user_request",
        },
        "temporal_context": {
            "current_time_utc": "2026-05-30T12:00:00",
            "freshness_class": "daily",
            "staleness_policy": "allow_with_label",
        },
        "data_classification": {
            "classification": "project_private",
            "source": "api_contract_test",
        },
        "event_source": "test_source",
        "subject": "Agent Execution",
        "action": "start",
        "outcome": "blocked",
        "status": "failed",
        "severity": "warning",
        "metadata": {"note": f"api_key='{secret_value}'"},
    }

    response = client.post("/events/validate", json=payload)

    assert response.status_code == 200
    body_text = response.text
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "SECRET_EXPOSURE_BLOCKED"
    assert secret_value not in body_text


def test_openapi_schema_has_no_raw_secret_request_fields():
    findings = forbidden_raw_secret_schema_fields(app.openapi())

    assert findings == []


def test_openapi_schema_has_no_raw_provider_payload_fields():
    schema = app.openapi()
    findings = forbidden_raw_provider_schema_fields(schema)
    chat_schema = schema["components"]["schemas"]["V1ChatCompletionAPIRequest"]

    assert findings == []
    assert "model" in chat_schema["properties"]
    assert "messages" in chat_schema["properties"]
