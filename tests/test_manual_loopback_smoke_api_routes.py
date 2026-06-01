from fastapi.testclient import TestClient

from tests.m10_helpers import approval_for_smoke, smoke_request
from tests.m9_helpers import loopback_endpoint
from ultimate_ai_agent.api.app import app

client = TestClient(app)


def test_smoke_validate_endpoint_accepts_safe_request_with_valid_approval():
    request = smoke_request()
    _, _, grant, decision = approval_for_smoke(request)
    request = request.model_copy(update={"approval_ref": grant.approval_ref})

    body = client.post(
        "/model-runtime/local/smoke/validate",
        json={"request": request.model_dump(mode="json"), "approval_decision": decision.model_dump(mode="json")},
    ).json()

    assert body["success"] is True
    assert body["data"]["reason_codes"] == ["MANUAL_LOOPBACK_SMOKE_ALLOWED", "APPROVAL_VALIDATED"]


def test_smoke_validate_endpoint_rejects_remote_and_secret_query_safely():
    for endpoint, expected in [
        (loopback_endpoint(base_url="http://example.com/api/generate", allowed_hosts=["example.com"]), "MODEL_RUNTIME_VALIDATION_FAILED"),
        (loopback_endpoint(base_url="http://127.0.0.1/api/generate?token=abc"), "MODEL_RUNTIME_VALIDATION_FAILED"),
    ]:
        payload = smoke_request().model_dump(mode="json")
        payload["endpoint"] = endpoint.model_dump(mode="json")
        response = client.post("/model-runtime/local/smoke/validate", json={"request": payload})
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == expected
        assert "token=abc" not in response.text


def test_public_api_has_no_smoke_execute_route():
    paths = {route.path for route in app.routes}

    assert "/model-runtime/local/smoke/validate" in paths
    assert "/model-runtime/local/smoke/execute" not in paths
    assert "/model-runtime/local/execute" not in paths
