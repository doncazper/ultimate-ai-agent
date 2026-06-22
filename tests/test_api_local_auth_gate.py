from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_ENABLED_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.mattermost.api_safety import (
    MATTERMOST_BRIDGE_BEARER_ENV,
    MATTERMOST_BRIDGE_ENV,
)


LOCAL_TEST_BEARER = "p1-083-local-bearer"


def _client() -> TestClient:
    return TestClient(app)


def _headers(value: str = LOCAL_TEST_BEARER) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def test_public_metadata_routes_remain_open_when_local_gate_is_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = _client()

    for path in ["/health", "/version", "/api/manifest", "/openapi.json"]:
        response = client.get(path)
        assert response.status_code == 200


def test_protected_routes_require_configured_local_bearer(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = _client()

    missing = client.get("/control-center/routes")
    wrong = client.get("/control-center/routes", headers=_headers("wrong-local-bearer"))
    allowed = client.get("/control-center/routes", headers=_headers())

    assert missing.status_code == 401
    assert missing.json()["code"] == "LOCAL_API_AUTH_REQUIRED"
    assert missing.headers["X-Content-Type-Options"] == "nosniff"
    assert wrong.status_code == 401
    assert "wrong-local-bearer" not in wrong.text
    assert allowed.status_code == 200
    assert allowed.json()["success"] is True


def test_local_gate_denies_sensitive_post_before_validation(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = _client()

    response = client.post("/files/tree/preview", json={"unsafe": "shape"})

    assert response.status_code == 401
    assert response.json()["policy_ref"] == "auth:p1-083:local-protected-routes:v1"
    assert "unsafe" not in response.text


def test_local_gate_fails_closed_when_enabled_without_valid_bearer(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_AUTH_ENABLED_ENV, "1")
    monkeypatch.delenv(LOCAL_API_BEARER_ENV, raising=False)
    client = _client()

    response = client.get("/control-center/routes")

    assert response.status_code == 503
    assert response.json()["code"] == "LOCAL_API_AUTH_NOT_CONFIGURED"
    assert "UAA_API_LOCAL_BEARER" not in response.text


def test_local_gate_is_inactive_until_configured(monkeypatch) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_ENABLED_ENV, raising=False)
    monkeypatch.delenv(LOCAL_API_BEARER_ENV, raising=False)
    client = _client()

    response = client.get("/control-center/routes")

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_route_specific_local_bearer_does_not_require_second_global_bearer(
    monkeypatch,
) -> None:
    mattermost_bearer = "mattermost-local-bearer"
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    monkeypatch.setenv(MATTERMOST_BRIDGE_ENV, "1")
    monkeypatch.setenv(MATTERMOST_BRIDGE_BEARER_ENV, mattermost_bearer)
    client = _client()

    response = client.get(
        "/integrations/mattermost/roles/catalog",
        headers=_headers(mattermost_bearer),
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_cors_preflight_remains_browser_hardening_not_auth(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = _client()

    response = client.options(
        "/contracts/validate",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert "Authorization" in response.headers["Access-Control-Allow-Headers"]
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_manifest_declares_local_gate_without_broad_auth_claims() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")

    assert "local_protected_route_bearer_gate" in manifest["capabilities_declared"]
    for blocked in [
        "local_protected_route_gate_as_enterprise_auth",
        "local_protected_route_gate_as_multi_user_auth",
        "local_protected_route_gate_as_oauth",
        "local_protected_route_gate_as_password_flow",
        "local_protected_route_gate_as_production_authority",
    ]:
        assert blocked in manifest["capabilities_blocked"]

    for route in manifest["routes"]:
        expected_protected = route["route_classification"] != "public_metadata"
        assert route["protected_route"] is expected_protected
