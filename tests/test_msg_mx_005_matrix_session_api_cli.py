from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_communications
from ultimate_ai_agent.api import communications as communications_api
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.core.communications.matrix_session import (
    MATRIX_SESSION_LANES,
    MatrixSessionCommand,
    MatrixSessionOperation,
    matrix_homeserver_ref,
    matrix_session_request_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


LOCAL_BEARER = "msg-mx-005-local-bearer"


class _ApiResult:
    def __init__(self, status: str = "succeeded") -> None:
        self.receipt = SimpleNamespace(status=status)

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {
            "receipt": {
                "status": self.receipt.status,
                "receipt_ref": "receipt-ref:matrix-session:api-test",
            },
            "credential_material_persisted": False,
            "provider_payload_persisted": False,
        }


def _command(operation: MatrixSessionOperation) -> MatrixSessionCommand:
    suffix = operation.value.replace("_", "-")
    request_created_at = utc_now()
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-session:api:{suffix}",
        "task_ref": f"task-ref:matrix-session:api:{suffix}",
        "mission_ref": "mission-ref:matrix-session:api",
        "run_ref": f"run-ref:matrix-session:api:{suffix}",
        "dispatch_ref": f"dispatch-ref:matrix-session:api:{suffix}",
        "idempotency_ref": f"idempotency-ref:matrix-session:api:{suffix}",
        "lease_ref": f"authority-lease-ref:matrix-session:api:{suffix}",
        "homeserver_ref": matrix_homeserver_ref("http://127.0.0.1:18008"),
        "endpoint_class_ref": "endpoint-class-ref:matrix:local-harness",
        "discovery_observation_ref": (
            "observation-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else "observation-ref:matrix-discovery:api-current"
        ),
        "discovery_freshness_ref": (
            "freshness-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else "freshness-ref:matrix-discovery:api-current"
        ),
        "readiness_ref": "readiness-ref:matrix-session:api-current",
        "target_refs": (),
        "request_created_at": request_created_at,
        "start_deadline": request_created_at + timedelta(minutes=2),
    }
    if operation not in {
        MatrixSessionOperation.discovery_read,
        MatrixSessionOperation.auth_methods_read,
        MatrixSessionOperation.sso_launch,
    }:
        values.update(
            account_ref="account-ref:matrix:api-primary",
            device_ref="device-ref:matrix:api-stable",
            session_ref="session-ref:matrix:api-primary",
            session_generation_ref="session-generation-ref:matrix:api-one",
            credential_item_ref="credential-item-ref:matrix:api-primary",
            credential_version_ref="credential-version-ref:matrix:api-one",
        )
    if operation == MatrixSessionOperation.credential_auth_create:
        values["crypto_store_ref"] = "crypto-store-ref:matrix:api-reserved"
    if operation in {
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.credential_store_rotate,
    }:
        values["next_credential_version_ref"] = "credential-version-ref:matrix:api-two"
    if operation in {
        MatrixSessionOperation.sso_launch,
        MatrixSessionOperation.sso_callback_consume,
    }:
        values["redirect_target_ref"] = "redirect-target-ref:matrix:api-loopback"
        values["callback_attempt_ref"] = "callback-attempt-ref:matrix:api-one"
    if operation == MatrixSessionOperation.revoke_all:
        values["target_refs"] = (
            "device-ref:matrix:api-stable",
            "device-set-fingerprint-ref:matrix:api-current",
        )
    values["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(**values)
    return MatrixSessionCommand(**values)


def _headers(command: MatrixSessionCommand | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}
    if command is not None:
        headers["x-uaa-idempotency-key"] = command.idempotency_ref
    return headers


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    reset_api_rate_limit_state()
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    yield TestClient(app)
    reset_api_rate_limit_state()


@pytest.mark.parametrize("operation", list(MatrixSessionOperation))
def test_routes_are_protected_no_store_safe_and_operation_bound(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    operation: MatrixSessionOperation,
) -> None:
    command = _command(operation)
    path = f"/control-center/communications/matrix/{operation.value.replace('_', '-')}"
    payload = {
        "command": command.model_dump(mode="json"),
        "confirmed": MATRIX_SESSION_LANES[operation].approval_required,
    }
    if operation == MatrixSessionOperation.discovery_read:
        payload["discovery_origin"] = "http://127.0.0.1:18008"
    else:
        payload["endpoint_url"] = "http://127.0.0.1:18008"
    if operation in {
        MatrixSessionOperation.sso_launch,
        MatrixSessionOperation.sso_callback_consume,
    }:
        payload["callback_url"] = "http://127.0.0.1:54321/uaa-matrix-callback"
    monkeypatch.setattr(
        communications_api,
        "_SESSION_OPERATION_HANDLER",
        lambda request: _ApiResult(),
    )
    assert client.post(path, json=payload).status_code == 401
    response = client.post(
        path,
        json=payload,
        headers=_headers(
            command if MATRIX_SESSION_LANES[operation].approval_required else None
        ),
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["success"] is True
    lowered = response.text.lower()
    assert "127.0.0.1" not in lowered
    assert "access_token" not in lowered
    assert "password" not in lowered


def test_mutation_requires_exact_idempotency_and_mismatch_denies_before_handler(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixSessionOperation.credential_delete)
    path = "/control-center/communications/matrix/credential-delete"
    payload = {
        "command": command.model_dump(mode="json"),
        "endpoint_url": "http://127.0.0.1:18008",
        "confirmed": True,
    }
    calls: list[str] = []
    monkeypatch.setattr(
        communications_api,
        "_SESSION_OPERATION_HANDLER",
        lambda request: calls.append(request.command.dispatch_ref) or _ApiResult(),
    )
    assert client.post(path, json=payload, headers=_headers()).status_code == 428
    mismatch = client.post(
        path,
        json=payload,
        headers={
            **_headers(),
            "x-uaa-idempotency-key": "idempotency-ref:matrix-session:different",
        },
    )
    assert mismatch.status_code == 409
    wrong = _command(MatrixSessionOperation.logout)
    wrong_payload = {**payload, "command": wrong.model_dump(mode="json")}
    operation_mismatch = client.post(path, json=wrong_payload, headers=_headers(wrong))
    assert operation_mismatch.status_code == 422
    assert calls == []


def test_manifest_and_openapi_expose_exact_session_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/matrix/")
    }
    assert len(routes) == len(MatrixSessionOperation)
    assert all(route.protected_route for route in routes.values())
    assert all(
        route.rate_limit_group == "communications_matrix_session"
        for route in routes.values()
    )
    for operation, lane in MATRIX_SESSION_LANES.items():
        path = (
            f"/control-center/communications/matrix/{operation.value.replace('_', '-')}"
        )
        route = routes[path]
        assert route.idempotency_required is lane.approval_required
        assert route.route_classification == (
            "mutating_requires_authority"
            if lane.approval_required
            else "local_sensitive"
        )
        assert route.side_effect_class == lane.side_effect_class
        assert app.openapi()["paths"][path]["post"]["operationId"] == (
            f"post_control_center_communications_matrix_{operation.value}"
        )


def test_cli_builds_same_typed_discovery_command_without_echoing_target() -> None:
    parser = uaa_communications.build_parser()
    args = parser.parse_args(
        [
            "matrix-session",
            "discovery-read",
            "--request-ref",
            "request-ref:matrix-session:cli",
            "--task-ref",
            "task-ref:matrix-session:cli",
            "--mission-ref",
            "mission-ref:matrix-session:cli",
            "--run-ref",
            "run-ref:matrix-session:cli",
            "--dispatch-ref",
            "dispatch-ref:matrix-session:cli",
            "--idempotency-ref",
            "idempotency-ref:matrix-session:cli",
            "--discovery-observation-ref",
            "observation-ref:matrix-session:cli",
            "--discovery-freshness-ref",
            "freshness-ref:matrix-session:cli-current",
            "--readiness-ref",
            "readiness-ref:matrix-session:cli-current",
            "--discovery-origin",
            "http://127.0.0.1:18008",
        ]
    )
    command = uaa_communications._matrix_session_command(args)
    assert command.operation == MatrixSessionOperation.discovery_read
    assert command.endpoint_class_ref == "endpoint-class-ref:matrix:local-harness"
    assert "127.0.0.1" not in command.model_dump_json()


def test_api_rejects_transient_aliases_and_caller_asserted_capability_truth(
    client: TestClient,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    path = "/control-center/communications/matrix/discovery-read"
    base = {"command": command.model_dump(mode="json"), "confirmed": False}
    alias = client.post(
        path,
        json={
            **base,
            "discovery_origin": "http://127.0.0.1:18008",
            "endpoint_url": "https://substituted.example.org",
        },
        headers=_headers(),
    )
    assert alias.status_code == 422
    asserted = client.post(
        path,
        json={
            **base,
            "discovery_origin": "http://127.0.0.1:18008",
            "oauth_advertised": True,
        },
        headers=_headers(),
    )
    assert asserted.status_code == 422
