from fastapi.testclient import TestClient

from tests.m8_helpers import runtime_request, simulated_manifest
from ultimate_ai_agent.api.app import app


client = TestClient(app)


def test_model_runtime_manifest_validate_endpoint_accepts_simulated_manifest():
    response = client.post("/model-runtime/manifests/validate", json=simulated_manifest().model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "validated"


def test_model_runtime_request_validate_endpoint_blocks_secret_prompt_summary():
    payload = runtime_request().model_dump(mode="json")
    payload["prompt_summary"] = "api_key='ABCDEFGHIJKLMNOP'"

    response = client.post(
        "/model-runtime/requests/validate",
        json={"request": payload, "manifest": simulated_manifest().model_dump(mode="json")},
    )

    assert response.status_code in {200, 422}
    assert "ABCDEFGHIJKLMNOP" not in response.text


def test_model_runtime_simulate_endpoint_returns_simulated_response():
    response = client.post(
        "/model-runtime/simulate",
        json={"request": runtime_request().model_dump(mode="json"), "manifest": simulated_manifest().model_dump(mode="json")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "simulated_success"
    assert "no model was called" in body["data"]["output_summary"]


def test_openapi_includes_m8_routes_with_unique_operation_ids():
    schema = app.openapi()
    paths = schema["paths"]
    operation_ids = [
        spec["operationId"]
        for methods in paths.values()
        for spec in methods.values()
        if isinstance(spec, dict) and "operationId" in spec
    ]

    assert "/model-runtime/manifests/validate" in paths
    assert "/model-runtime/requests/validate" in paths
    assert "/model-runtime/responses/validate" in paths
    assert "/model-runtime/simulate" in paths
    assert len(operation_ids) == len(set(operation_ids))
