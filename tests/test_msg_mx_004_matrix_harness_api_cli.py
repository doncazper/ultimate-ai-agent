from __future__ import annotations

import argparse
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
from ultimate_ai_agent.core.communications.matrix_harness import (
    MatrixHarnessCommand,
    MatrixHarnessOperation,
    matrix_harness_generation_ref,
    matrix_harness_request_fingerprint_ref,
    matrix_harness_state_ref,
)
from ultimate_ai_agent.core.communications.matrix_harness.contracts import (
    MatrixHarnessRuntimeStatus,
)
from ultimate_ai_agent.core.time import utc_now


LOCAL_BEARER = "msg-mx-004-local-bearer"


class _ApiResult:
    def __init__(self, status: str = "succeeded") -> None:
        self.receipt = SimpleNamespace(status=status)
        self.status = status

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {
            "receipt": {
                "status": self.status,
                "receipt_ref": "receipt-ref:matrix-harness:api-test",
            },
            "raw_output_persisted": False,
            "raw_paths_persisted": False,
        }


def _command(operation: MatrixHarnessOperation) -> MatrixHarnessCommand:
    deadline = utc_now() + timedelta(minutes=2)
    generation_ref = matrix_harness_generation_ref(0)
    state_ref = matrix_harness_state_ref(MatrixHarnessRuntimeStatus.stopped, 0)
    values = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-harness:api:{operation.value}",
        "task_ref": f"task-ref:matrix-harness:api:{operation.value}",
        "mission_ref": f"mission-ref:matrix-harness:api:{operation.value}",
        "run_ref": f"run-ref:matrix-harness:api:{operation.value}",
        "dispatch_ref": f"dispatch-ref:matrix-harness:api:{operation.value}",
        "idempotency_ref": f"idempotency-ref:matrix-harness:api:{operation.value}",
        "lease_ref": f"authority-lease-ref:matrix-harness:api:{operation.value}",
        "lifecycle_generation_ref": generation_ref,
        "expected_state_ref": state_ref,
        "start_deadline": deadline,
    }
    values["request_fingerprint_ref"] = matrix_harness_request_fingerprint_ref(
        **values
    )
    return MatrixHarnessCommand(**values)


def _headers(command: MatrixHarnessCommand | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}
    if command is not None:
        headers["x-uaa-idempotency-key"] = command.idempotency_ref
    return headers


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    reset_api_rate_limit_state()
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    client = TestClient(app)
    yield client
    reset_api_rate_limit_state()


@pytest.mark.parametrize("operation", list(MatrixHarnessOperation))
def test_six_harness_routes_are_protected_no_store_and_operation_bound(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    operation: MatrixHarnessOperation,
) -> None:
    command = _command(operation)
    payload = {
        "command": command.model_dump(mode="json"),
        "confirmed": operation
        in {
            MatrixHarnessOperation.start,
            MatrixHarnessOperation.fixture_seed,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        },
    }
    path = f"/control-center/communications/harness/{operation.value.replace('_', '-')}"
    monkeypatch.setattr(
        communications_api,
        "_HARNESS_OPERATION_HANDLER",
        lambda request: _ApiResult(),
    )

    assert client.post(path, json=payload).status_code == 401
    response = client.post(path, json=payload, headers=_headers(command))

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["success"] is True
    lowered = response.text.lower()
    assert "access_token" not in lowered
    assert "password" not in lowered
    assert "/users/" not in lowered


@pytest.mark.parametrize(
    "operation",
    [
        MatrixHarnessOperation.start,
        MatrixHarnessOperation.fixture_seed,
        MatrixHarnessOperation.stop,
        MatrixHarnessOperation.reset,
    ],
)
def test_mutation_header_must_equal_typed_idempotency_ref(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    operation: MatrixHarnessOperation,
) -> None:
    command = _command(operation)
    path = f"/control-center/communications/harness/{operation.value.replace('_', '-')}"
    payload = {"command": command.model_dump(mode="json"), "confirmed": True}
    calls: list[str] = []
    monkeypatch.setattr(
        communications_api,
        "_HARNESS_OPERATION_HANDLER",
        lambda request: calls.append(request.command.dispatch_ref) or _ApiResult(),
    )

    missing = client.post(path, json=payload, headers=_headers())
    mismatch = client.post(
        path,
        json=payload,
        headers={
            **_headers(),
            "x-uaa-idempotency-key": "idempotency-ref:matrix-harness:different",
        },
    )
    conflict = client.post(
        path,
        json=payload,
        headers={
            **_headers(command),
            "x-uaa-idempotency-ref": "idempotency-ref:matrix-harness:different",
        },
    )

    assert missing.status_code == 428
    assert mismatch.status_code == 409
    assert conflict.status_code == 409
    assert mismatch.headers["Cache-Control"] == "no-store"
    assert calls == []


def test_operation_mismatch_denies_before_handler(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixHarnessOperation.smoke)
    calls: list[str] = []
    monkeypatch.setattr(
        communications_api,
        "_HARNESS_OPERATION_HANDLER",
        lambda request: calls.append(request.command.dispatch_ref) or _ApiResult(),
    )
    response = client.post(
        "/control-center/communications/harness/inspect",
        json={"command": command.model_dump(mode="json"), "confirmed": False},
        headers=_headers(),
    )

    assert response.status_code == 422
    assert response.headers["Cache-Control"] == "no-store"
    assert calls == []


def test_oversized_ref_and_non_strict_confirmation_reject_before_handler(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixHarnessOperation.inspect).model_dump(mode="json")
    command["request_ref"] = "request-ref:matrix-harness:" + ("x" * 300)
    calls: list[str] = []
    monkeypatch.setattr(
        communications_api,
        "_HARNESS_OPERATION_HANDLER",
        lambda request: calls.append(request.command.dispatch_ref) or _ApiResult(),
    )
    path = "/control-center/communications/harness/inspect"
    oversized = client.post(
        path,
        json={"command": command, "confirmed": False},
        headers=_headers(),
    )
    command = _command(MatrixHarnessOperation.inspect).model_dump(mode="json")
    non_strict = client.post(
        path,
        json={"command": command, "confirmed": 1},
        headers=_headers(),
    )
    inline_lease_issue = client.post(
        path,
        json={
            "command": command,
            "confirmed": False,
            "issue_exact_lease": True,
        },
        headers=_headers(),
    )

    assert oversized.status_code == 422
    assert non_strict.status_code == 422
    assert inline_lease_issue.status_code == 422
    assert calls == []


def test_denied_dispatch_is_not_wrapped_as_api_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixHarnessOperation.inspect)
    monkeypatch.setattr(
        communications_api,
        "_HARNESS_OPERATION_HANDLER",
        lambda request: _ApiResult("denied"),
    )
    response = client.post(
        "/control-center/communications/harness/inspect",
        json={"command": command.model_dump(mode="json"), "confirmed": False},
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "MATRIX_HARNESS_OPERATION_NOT_SUCCEEDED"


def test_manifest_and_openapi_expose_exact_harness_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/harness/")
    }
    assert len(routes) == 6
    assert all(route.protected_route for route in routes.values())
    assert all(route.rate_limit_group == "communications_matrix_harness" for route in routes.values())
    for operation in MatrixHarnessOperation:
        path = f"/control-center/communications/harness/{operation.value.replace('_', '-')}"
        route = routes[path]
        if operation in {MatrixHarnessOperation.inspect, MatrixHarnessOperation.smoke}:
            assert route.idempotency_required is False
        else:
            assert route.idempotency_required is True
            assert route.route_classification == "mutating_requires_authority"
        assert (
            app.openapi()["paths"][path]["post"]["operationId"]
            == f"post_control_center_communications_harness_{operation.value}"
        )


@pytest.mark.parametrize("operation", list(MatrixHarnessOperation))
def test_cli_builds_the_same_exact_typed_command(operation: MatrixHarnessOperation) -> None:
    parser = uaa_communications.build_parser()
    argv = [
        "harness",
        operation.value.replace("_", "-"),
        "--request-ref",
        "request-ref:matrix-harness:cli",
        "--task-ref",
        "task-ref:matrix-harness:cli",
        "--mission-ref",
        "mission-ref:matrix-harness:cli",
        "--run-ref",
        "run-ref:matrix-harness:cli",
        "--dispatch-ref",
        "dispatch-ref:matrix-harness:cli",
        "--idempotency-ref",
        "idempotency-ref:matrix-harness:cli",
        "--lease-ref",
        "authority-lease-ref:matrix-harness:cli",
        "--lifecycle-generation-ref",
        matrix_harness_generation_ref(0),
        "--expected-state-ref",
        matrix_harness_state_ref(MatrixHarnessRuntimeStatus.stopped, 0),
    ]
    if operation in {
        MatrixHarnessOperation.start,
        MatrixHarnessOperation.fixture_seed,
        MatrixHarnessOperation.stop,
        MatrixHarnessOperation.reset,
    }:
        argv.append("--confirm")
    args = parser.parse_args(argv)
    command = uaa_communications._matrix_harness_command(args)

    assert isinstance(args, argparse.Namespace)
    assert command.operation == operation
    assert command.request_fingerprint_ref.startswith(
        "request-fingerprint-ref:matrix-harness:sha256:"
    )
    assert command.lease_ref == "authority-lease-ref:matrix-harness:cli"


def test_cli_rejects_confirmation_for_read_lane() -> None:
    args = SimpleNamespace(
        harness_operation="inspect",
        deadline_seconds=120,
        confirm=True,
        request_ref="request-ref:matrix-harness:cli",
        task_ref="task-ref:matrix-harness:cli",
        mission_ref="mission-ref:matrix-harness:cli",
        run_ref="run-ref:matrix-harness:cli",
        dispatch_ref="dispatch-ref:matrix-harness:cli",
        idempotency_ref="idempotency-ref:matrix-harness:cli",
        lease_ref="authority-lease-ref:matrix-harness:cli",
        lifecycle_generation_ref=matrix_harness_generation_ref(0),
        expected_state_ref=matrix_harness_state_ref(
            MatrixHarnessRuntimeStatus.stopped, 0
        ),
    )
    with pytest.raises(ValueError, match="READ_CONFIRMATION_FORBIDDEN"):
        uaa_communications._matrix_harness_command(args)
