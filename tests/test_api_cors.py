from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.cors import (
    CONTROL_CENTER_LOOPBACK_CORS_HEADERS,
    CONTROL_CENTER_LOOPBACK_CORS_METHODS,
    CONTROL_CENTER_LOOPBACK_CORS_ORIGINS,
)
from ultimate_ai_agent.api.security_headers import FASTAPI_SECURITY_HEADERS


client = TestClient(app)


def _preflight(origin: str, method: str = "POST"):
    return client.options(
        "/contracts/validate",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_loopback_cors_allowlist_is_explicit_and_non_credentialed() -> None:
    assert "*" not in CONTROL_CENTER_LOOPBACK_CORS_ORIGINS
    assert CONTROL_CENTER_LOOPBACK_CORS_ORIGINS == (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://[::1]:4173",
    )
    assert CONTROL_CENTER_LOOPBACK_CORS_METHODS == ("GET", "POST")
    assert CONTROL_CENTER_LOOPBACK_CORS_HEADERS == (
        "Content-Type",
        "X-Requested-With",
    )


def test_allowed_loopback_origin_get_receives_specific_origin_only() -> None:
    origin = "http://127.0.0.1:5173"

    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert response.headers["Access-Control-Expose-Headers"] == (
        "X-UAA-Security-Headers-Policy"
    )
    assert response.headers.get("Access-Control-Allow-Credentials") is None
    assert response.headers["Access-Control-Allow-Origin"] != "*"
    assert response.headers["Vary"] == "Origin"


def test_allowed_loopback_preflight_is_scoped_and_security_hardened() -> None:
    origin = "http://localhost:5173"

    response = _preflight(origin)

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
    assert response.headers.get("Access-Control-Allow-Credentials") is None
    assert response.headers["Access-Control-Allow-Origin"] != "*"
    for name, value in FASTAPI_SECURITY_HEADERS.items():
        assert response.headers[name] == value


def test_disallowed_origins_do_not_receive_cors_authority() -> None:
    for origin in [
        "https://example.com",
        "http://localhost:9999",
        "http://192.168.1.2:5173",
        "null",
    ]:
        response = client.get("/health", headers={"Origin": origin})
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" not in response.headers


def test_disallowed_preflight_is_rejected_without_wildcard() -> None:
    response = _preflight("https://example.com")

    assert response.status_code == 400
    assert "Access-Control-Allow-Origin" not in response.headers
    assert response.headers.get("Access-Control-Allow-Credentials") is None
    for name, value in FASTAPI_SECURITY_HEADERS.items():
        assert response.headers[name] == value
