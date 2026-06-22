from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.security_headers import (
    FASTAPI_SECURITY_HEADERS,
    HTTPS_ONLY_SECURITY_HEADERS,
    SECURITY_HEADERS_POLICY_REF,
)


def _assert_core_security_headers(response) -> None:
    for name, value in FASTAPI_SECURITY_HEADERS.items():
        assert response.headers[name] == value
    assert response.headers["X-UAA-Security-Headers-Policy"] == SECURITY_HEADERS_POLICY_REF
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "object-src 'none'" in response.headers["Content-Security-Policy"]
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert "microphone=()" in response.headers["Permissions-Policy"]
    assert "geolocation=()" in response.headers["Permissions-Policy"]


def test_security_headers_apply_to_success_responses() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    _assert_core_security_headers(response)
    assert "Strict-Transport-Security" not in response.headers
    assert "access-control-allow-origin" not in {
        key.lower() for key in response.headers
    }


def test_security_headers_apply_to_handled_validation_errors() -> None:
    client = TestClient(app)

    response = client.post("/contracts/validate", json={"api_key": "ABCDEFGHIJKLMNOP"})

    assert response.status_code == 422
    _assert_core_security_headers(response)
    assert "ABCDEFGHIJKLMNOP" not in response.text


def test_hsts_is_added_only_for_https_requests() -> None:
    http_client = TestClient(app)
    https_client = TestClient(app, base_url="https://testserver")

    http_response = http_client.get("/version")
    https_response = https_client.get("/version")

    assert "Strict-Transport-Security" not in http_response.headers
    assert https_response.headers["Strict-Transport-Security"] == (
        HTTPS_ONLY_SECURITY_HEADERS["Strict-Transport-Security"]
    )
