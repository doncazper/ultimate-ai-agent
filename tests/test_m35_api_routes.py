from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def test_validate_secret_credential_endpoint():
    payload = {
        "credential_ref": "cred_api",
        "provider_id": "provider_api",
        "auth_type": "api_key",
        "scope": "user",
        "status": "active",
        "allowed_purposes": ["provider_lookup"],
    }

    response = client.post("/secrets/credentials/validate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "secret_value" not in str(data)


def test_secret_access_endpoint_never_returns_raw_secret():
    payload = {
        "reference": {
            "credential_ref": "cred_api_access",
            "provider_id": "provider_api",
            "auth_type": "api_key",
            "scope": "user",
            "status": "active",
            "allowed_purposes": ["provider_lookup"],
        },
        "access_request": {
            "credential_ref": "cred_api_access",
            "requester_actor_id": "actor",
            "provider_id": "provider_api",
            "purpose": "provider_lookup",
            "consent_ref": "consent_api",
        },
    }

    response = client.post("/secrets/access/evaluate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["allowed"] is True
    assert data["data"]["secret_handle"] is not None
    assert "raw_secret" not in response.text


def test_secret_access_endpoint_rejects_raw_secret_value_field_without_echoing_value():
    secret = "abcdefghijklmnop"
    payload = {
        "reference": {
            "credential_ref": "cred_api_access_raw",
            "provider_id": "provider_api",
            "auth_type": "api_key",
            "scope": "user",
            "status": "active",
            "allowed_purposes": ["provider_lookup"],
        },
        "access_request": {
            "credential_ref": "cred_api_access_raw",
            "requester_actor_id": "actor",
            "provider_id": "provider_api",
            "purpose": "provider_lookup",
            "consent_ref": "consent_api",
        },
        "secret_value": f"api_key='{secret}'",
    }

    response = client.post("/secrets/access/evaluate", json=payload)

    assert response.status_code == 422
    assert secret not in response.text
    assert "secret_value" not in response.text


def test_provider_manifest_and_resolve_endpoints_are_non_executing():
    manifest = {
        "provider_id": "weather_no_key_api",
        "display_name": "Weather No Key API",
        "domain": "weather",
        "status": "enabled",
        "auth_requirement": "none",
        "cost_class": "free_no_key",
        "capabilities": ["current_weather"],
        "owner": "core",
        "source": "tests",
        "version": "1.0.0",
    }

    validate_response = client.post("/providers/manifests/validate", json=manifest)
    resolve_response = client.post(
        "/providers/resolve",
        json={
            "domain": "weather",
            "capability": "current_weather",
            "policy": {"policy_id": "free_first"},
            "providers": [manifest],
        },
    )

    assert validate_response.status_code == 200
    assert validate_response.json()["success"] is True
    assert resolve_response.status_code == 200
    assert resolve_response.json()["data"]["selected_provider_id"] == "weather_no_key_api"


def test_provider_result_validate_endpoint_blocks_secret_leakage():
    response = client.post(
        "/providers/results/validate",
        json={
            "result_id": "res_api_secret",
            "provider_id": "weather_no_key_api",
            "domain": "weather",
            "capability": "current_weather",
            "input_summary": "api_key='abcdefghijklmnop'",
            "normalized": {"status": "ok"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PROVIDER_RESULT_SECRET_EXPOSURE"
