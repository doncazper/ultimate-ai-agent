from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import ultimate_ai_agent.api.communications as communications_api
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_messaging import (
    MatrixMessagingOperation,
    build_default_matrix_messaging_posture,
    build_matrix_messaging_command,
    build_matrix_messaging_proposal,
)
from ultimate_ai_agent.core.communications.matrix_messaging.constants import (
    matrix_messaging_rollback_ref,
)
from ultimate_ai_agent.core.communications.matrix_messaging.contracts import (
    MatrixOutboxState,
)


LOCAL_BEARER = "msg-mx-008-local-bearer"
POSTURE_PATH = "/control-center/communications/matrix-messaging/posture"
PROPOSAL_PATH = "/control-center/communications/matrix-messaging/proposal"
SEND_PATH = "/control-center/communications/matrix-messaging/send"


def _send_command(*, operation: MatrixMessagingOperation = MatrixMessagingOperation.send):
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:msg-mx-008:api",
        "task_ref": "task-ref:msg-mx-008:api",
        "mission_ref": "mission-ref:msg-mx-008:api",
        "run_ref": "run-ref:msg-mx-008:api",
        "dispatch_ref": "dispatch-ref:msg-mx-008:api",
        "idempotency_ref": "idempotency-ref:msg-mx-008:api",
        "lease_ref": "authority-lease-ref:msg-mx-008:api",
        "account_ref": "account-ref:matrix:api",
        "homeserver_ref": "homeserver-ref:matrix:api",
        "device_ref": "device-ref:matrix:api",
        "room_ref": "room-ref:matrix:api",
        "event_ref": None,
        "transaction_ref": "transaction-ref:matrix:api",
        "content_fingerprint_ref": "content-fingerprint-ref:matrix:api",
        "outbox_ref": "outbox-ref:matrix:api",
        "outbox_generation_ref": "outbox-generation-ref:matrix:api",
        "expected_outbox_state": MatrixOutboxState.queued,
        "readiness_ref": "readiness-ref:matrix-messaging:api",
        "rollback_ref": matrix_messaging_rollback_ref(operation),
        "request_created_at": now,
        "start_deadline": now + timedelta(seconds=30),
    }
    if operation == MatrixMessagingOperation.typing:
        values.update(
            {
                "transaction_ref": None,
                "content_fingerprint_ref": None,
                "outbox_ref": None,
                "outbox_generation_ref": None,
                "expected_outbox_state": None,
            }
        )
    return build_matrix_messaging_command(**values)


def _auth_headers(command) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LOCAL_BEARER}",
        "x-uaa-idempotency-key": command.idempotency_ref,
    }


def test_messaging_posture_route_is_protected_no_store_and_content_free(
    monkeypatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    client = TestClient(app)
    assert client.get(POSTURE_PATH).status_code == 401
    response = client.get(
        POSTURE_PATH,
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.json()["data"]
    assert payload == build_default_matrix_messaging_posture().model_dump(mode="json")
    assert payload["runtime_status"] == "configuration_required"
    assert len(payload["authority_lane_refs"]) == 15
    assert len(payload["live_executor_operation_refs"]) == 15
    assert payload["autonomous_send_enabled"] is False
    assert payload["raw_content_included"] is False
    assert "private message body" not in json.dumps(payload).lower()


def test_messaging_proposal_never_authorizes_or_executes(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _send_command()
    response = TestClient(app).post(
        PROPOSAL_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == build_matrix_messaging_proposal(command).model_dump(mode="json")
    assert payload["execution_permitted"] is False
    assert payload["approval_ref_authorizes_execution"] is False
    assert payload["mutation_performed"] is False
    assert payload["autonomous_send_enabled"] is False


def test_exact_send_route_binds_operation_and_idempotency(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _send_command()
    monkeypatch.setattr(
        communications_api,
        "_MATRIX_MESSAGING_OPERATION_HANDLER",
        lambda payload: {
            "operation": payload.command.operation.value,
            "receipt_ref": "receipt-ref:matrix-messaging:content-free",
            "raw_content_included": False,
        },
    )
    client = TestClient(app)
    response = client.post(
        SEND_PATH,
        json={"command": command.model_dump(mode="json"), "confirmed": True},
        headers=_auth_headers(command),
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["data"] == {
        "operation": "send",
        "receipt_ref": "receipt-ref:matrix-messaging:content-free",
        "raw_content_included": False,
    }
    missing = client.post(
        SEND_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert missing.status_code == 428
    assert "idempotency" in missing.json()["detail"].lower()


def test_messaging_routes_manifest_openapi_and_side_effects_are_exact() -> None:
    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if "/matrix-messaging/" in route.path
    }
    assert len(routes) == 17
    assert routes[POSTURE_PATH].side_effect_class == "none"
    assert routes[PROPOSAL_PATH].side_effect_class == "validation_only"
    assert routes[SEND_PATH].side_effect_class == "authenticated_connector_mutation"
    assert routes[SEND_PATH].route_classification == "mutating_requires_authority"
    assert routes[SEND_PATH].idempotency_required is True
    assert routes[
        "/control-center/communications/matrix-messaging/redaction"
    ].side_effect_class == "destructive_external"
    assert routes[
        "/control-center/communications/matrix-messaging/outbox-discard"
    ].side_effect_class == "destructive_local_sensitive"
    openapi = app.openapi()["paths"]
    for path, route in routes.items():
        method = route.method.lower()
        assert openapi[path][method]["operationId"] == route.operation_id


def test_typing_route_requires_exact_transient_room_target(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _send_command(operation=MatrixMessagingOperation.typing)
    monkeypatch.setattr(
        communications_api,
        "_MATRIX_MESSAGING_OPERATION_HANDLER",
        lambda payload: {
            "operation": payload.command.operation.value,
            "raw_content_included": False,
        },
    )
    payload = {
        "command": command.model_dump(mode="json"),
        "confirmed": True,
        "transient": {
            "homeserver_url": "http://127.0.0.1:18008",
            "room_id": "!transient-room:localhost",
            "typing_active": True,
        },
    }
    client = TestClient(app)
    response = client.post(
        "/control-center/communications/matrix-messaging/typing",
        json=payload,
        headers=_auth_headers(command),
    )
    assert response.status_code == 200
    assert response.json()["data"]["operation"] == "typing"
    payload["transient"].pop("room_id")
    missing = client.post(
        "/control-center/communications/matrix-messaging/typing",
        json=payload,
        headers=_auth_headers(command),
    )
    assert missing.status_code == 422
    assert "transient-room" not in missing.text


def test_messaging_cli_status_and_proposal_share_core_truth(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [sys.executable, "scripts/dev/uaa_communications.py", "matrix-messaging-status"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix manual messaging" in human.stdout
    assert "Runtime: configuration_required" in human.stdout
    assert "Exact authority lanes: 15" in human.stdout
    assert "Autonomous or AI send: denied" in human.stdout
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-messaging-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == (
        build_default_matrix_messaging_posture().model_dump(mode="json")
    )

    command = _send_command()
    command_file = tmp_path / "matrix-messaging-command.json"
    command_file.write_text(command.model_dump_json())
    proposal = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-messaging",
            "propose",
            "--command-file",
            str(command_file),
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(proposal.stdout) == (
        build_matrix_messaging_proposal(command).model_dump(mode="json")
    )
    assert str(command_file) not in proposal.stdout
