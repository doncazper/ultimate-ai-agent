from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest


LOCAL_TEST_BEARER = "msg-mx-003-local-bearer"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LOCAL_TEST_BEARER}"}


def test_communications_routes_are_protected_no_store_and_content_free(
    monkeypatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = TestClient(app)
    paths = [
        "/control-center/communications/providers",
        "/control-center/communications/session-posture",
        "/control-center/communications/rooms",
        "/control-center/communications/failed-sends",
        "/control-center/communications/security-posture",
        "/control-center/communications/receipts/receipt-ref:communications:contract-inspection",
    ]
    for path in paths:
        assert client.get(path).status_code == 401
        response = client.get(path, headers=_headers())
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        text = response.text.lower()
        for forbidden in (
            "private ordinary conversation",
            "matrix access token",
            "raw provider response",
        ):
            assert forbidden not in text


def test_communications_receipt_not_found_does_not_echo_rejected_input(
    monkeypatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    response = TestClient(app).get(
        "/control-center/communications/receipts/not-a-safe-ref",
        headers=_headers(),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "COMMUNICATIONS_RECEIPT_NOT_FOUND"
    assert response.headers["Cache-Control"] == "no-store"
    assert "not-a-safe-ref" not in response.text


def test_communications_manifest_and_openapi_contracts_are_exact() -> None:
    manifest = build_api_manifest(app)
    routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/")
    }
    assert set(routes) == {
        "/control-center/communications/providers",
        "/control-center/communications/session-posture",
        "/control-center/communications/rooms",
        "/control-center/communications/failed-sends",
        "/control-center/communications/security-posture",
        "/control-center/communications/receipts/{receipt_ref}",
    }
    assert all(route.method == "GET" for route in routes.values())
    assert all(route.side_effect_class == "none" for route in routes.values())
    assert all(
        route.route_classification == "local_sensitive" for route in routes.values()
    )
    assert all(route.protected_route for route in routes.values())
    assert all(route.blocked_from_production for route in routes.values())
    assert all(not route.idempotency_required for route in routes.values())
    assert all(not route.rate_limit_targeted for route in routes.values())
    assert all(route.rate_limit_group is None for route in routes.values())
    assert all(
        route.approval_posture == "not_required_for_route_classification"
        for route in routes.values()
    )
    assert (
        "communications_backend_owned_normalized_contracts"
        in manifest.capabilities_declared
    )
    assert (
        "communications_matrix_message_send_or_mutation"
        in manifest.capabilities_blocked
    )

    schema = app.openapi()
    operation_ids = {schema["paths"][path]["get"]["operationId"] for path in routes}
    assert operation_ids == {
        "get_control_center_communications_providers",
        "get_control_center_communications_session_posture",
        "get_control_center_communications_rooms",
        "get_control_center_communications_failed_sends",
        "get_control_center_communications_security_posture",
        "get_control_center_communications_receipt",
    }


def test_communications_cli_is_human_readable_and_json_matches_core_truth() -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [sys.executable, "scripts/dev/uaa_communications.py", "providers"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Communications providers" in human.stdout
    assert "No provider network operation was performed." in human.stdout

    machine = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "session",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(machine.stdout)
    assert payload["status"] == "not_configured"
    assert payload["network_performed"] is False
    assert payload["authentication_performed"] is False
    assert payload["sync_performed"] is False
    assert payload["blocker_codes"]
