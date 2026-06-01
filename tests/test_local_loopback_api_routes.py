from fastapi.testclient import TestClient

from tests.m9_helpers import local_manifest, local_runtime_request, loopback_endpoint, loopback_policy
from ultimate_ai_agent.api.app import app

client = TestClient(app)


def test_local_loopback_endpoint_validation_rejects_remote_credentials_and_secret_query():
    for url, code in [
        ("http://example.com/api/generate", "NON_LOOPBACK_HOST_DENIED"),
        ("http://user:pass@127.0.0.1:11434/api/generate", "URL_CREDENTIALS_DENIED"),
        ("http://127.0.0.1:11434/api/generate?token=abc", "SECRET_QUERY_DENIED"),
    ]:
        payload = {"endpoint": loopback_endpoint(base_url=url).model_dump(mode="json"), "policy": loopback_policy().model_dump(mode="json")}
        body = client.post("/model-runtime/local/endpoints/validate", json=payload).json()
        assert body["success"] is False
        assert code in body["data"]["reason_codes"]


def test_local_loopback_execution_validation_and_simulated_fallback_routes():
    validate_payload = {
        "request": local_runtime_request(approval_ref="human_approved_ref_123").model_dump(mode="json"),
        "manifest": local_manifest().model_dump(mode="json"),
        "endpoint": loopback_endpoint().model_dump(mode="json"),
        "policy": loopback_policy().model_dump(mode="json"),
    }
    validate_body = client.post("/model-runtime/local/execution/validate", json=validate_payload).json()
    fallback_body = client.post("/model-runtime/local/simulate-fallback", json=validate_payload).json()

    assert validate_body["success"] is False
    assert "APPROVAL_DECISION_REQUIRED" in validate_body["data"]["reason_codes"]
    assert fallback_body["success"] is True
    assert fallback_body["data"]["response_origin"] == "simulated"


def test_local_loopback_api_validation_errors_do_not_echo_secrets():
    secret = "sk_test_secret_value_12345"
    payload = {"endpoint": {**loopback_endpoint().model_dump(mode="json"), "metadata": {"note": f"api_key={secret}"}}}

    response = client.post("/model-runtime/local/endpoints/validate", json=payload)

    assert secret not in response.text
    assert "api_key" not in response.text
