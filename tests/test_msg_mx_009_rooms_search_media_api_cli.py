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
from ultimate_ai_agent.core.communications.matrix_rooms_media import (
    MatrixRoomsMediaOperation,
    build_default_matrix_rooms_media_posture,
    build_matrix_rooms_media_command,
    build_matrix_rooms_media_proposal,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.constants import (
    matrix_rooms_media_rollback_ref,
)


LOCAL_BEARER = "msg-mx-009-local-bearer"
POSTURE_PATH = "/control-center/communications/matrix-rooms-media/posture"
PROPOSAL_PATH = "/control-center/communications/matrix-rooms-media/proposal"
ROOM_JOIN_PATH = "/control-center/communications/matrix-rooms-media/room-join"


def _room_join_command():
    now = datetime.now(UTC)
    operation = MatrixRoomsMediaOperation.room_join
    return build_matrix_rooms_media_command(
        operation=operation,
        request_ref="request-ref:msg-mx-009:api",
        task_ref="task-ref:msg-mx-009:api",
        mission_ref="mission-ref:msg-mx-009:api",
        run_ref="run-ref:msg-mx-009:api",
        dispatch_ref="dispatch-ref:msg-mx-009:api",
        idempotency_ref="idempotency-ref:msg-mx-009:api",
        lease_ref="authority-lease-ref:msg-mx-009:api",
        account_ref="account-ref:matrix:api",
        homeserver_ref="homeserver-ref:matrix:api",
        device_ref="device-ref:matrix:api",
        room_ref="room-ref:matrix:api",
        transaction_ref="transaction-ref:matrix:api",
        prior_state_ref="state-ref:matrix:api",
        readiness_ref="readiness-ref:matrix-rooms-media:api",
        rollback_ref=matrix_rooms_media_rollback_ref(operation),
        request_created_at=now,
        start_deadline=now + timedelta(seconds=30),
    )


def _auth_headers(command) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LOCAL_BEARER}",
        "x-uaa-idempotency-key": command.idempotency_ref,
    }


def test_rooms_media_posture_is_protected_no_store_and_content_free(
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
    assert payload == build_default_matrix_rooms_media_posture().model_dump(mode="json")
    assert payload["runtime_status"] == "configuration_required"
    assert len(payload["authority_lane_refs"]) == 20
    assert len(payload["implemented_core_operation_refs"]) == 20
    assert len(payload["blocked_live_operation_refs"]) == 20
    assert payload["standing_authority_granted"] is False
    assert payload["raw_content_included"] is False


def test_rooms_media_proposal_never_authorizes_or_executes(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _room_join_command()
    response = TestClient(app).post(
        PROPOSAL_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == build_matrix_rooms_media_proposal(command).model_dump(mode="json")
    assert payload["execution_permitted"] is False
    assert payload["approval_ref_authorizes_execution"] is False
    assert payload["mutation_performed"] is False


def test_exact_room_join_route_binds_operation_and_idempotency(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _room_join_command()
    monkeypatch.setattr(
        communications_api,
        "_MATRIX_ROOMS_MEDIA_OPERATION_HANDLER",
        lambda payload: {
            "operation": payload.command.operation.value,
            "receipt_ref": "receipt-ref:matrix-rooms-media:content-free",
            "raw_content_included": False,
        },
    )
    client = TestClient(app)
    response = client.post(
        ROOM_JOIN_PATH,
        json={"command": command.model_dump(mode="json"), "confirmed": True},
        headers=_auth_headers(command),
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["data"]["operation"] == "room_join"

    missing = client.post(
        ROOM_JOIN_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert missing.status_code == 428
    assert "idempotency" in missing.json()["detail"].lower()


def test_rooms_media_routes_manifest_openapi_and_side_effects_are_exact() -> None:
    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if "/matrix-rooms-media/" in route.path
    }
    assert len(routes) == 22
    assert routes[POSTURE_PATH].side_effect_class == "none"
    assert routes[PROPOSAL_PATH].side_effect_class == "validation_only"
    assert (
        routes[ROOM_JOIN_PATH].side_effect_class == "authenticated_connector_mutation"
    )
    assert routes[ROOM_JOIN_PATH].route_classification == "mutating_requires_authority"
    assert routes[ROOM_JOIN_PATH].idempotency_required is True
    assert (
        routes[
            "/control-center/communications/matrix-rooms-media/room-leave"
        ].side_effect_class
        == "destructive_external"
    )
    assert (
        routes[
            "/control-center/communications/matrix-rooms-media/media-cleanup"
        ].side_effect_class
        == "destructive_local_sensitive"
    )
    assert (
        routes[
            "/control-center/communications/matrix-rooms-media/search-local-read"
        ].side_effect_class
        == "local_sensitive"
    )
    openapi = app.openapi()["paths"]
    for path, route in routes.items():
        assert openapi[path][route.method.lower()]["operationId"] == route.operation_id


def test_rooms_media_cli_status_and_proposal_share_core_truth(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-rooms-media-status",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix rooms, encrypted local search, and bounded media" in human.stdout
    assert "Runtime: configuration_required" in human.stdout
    assert "Exact authority lanes: 20" in human.stdout
    assert "Standing room, filesystem, or search authority: denied" in human.stdout
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-rooms-media-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == (
        build_default_matrix_rooms_media_posture().model_dump(mode="json")
    )

    command = _room_join_command()
    command_file = tmp_path / "matrix-rooms-media-command.json"
    command_file.write_text(command.model_dump_json())
    proposal = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-rooms-media",
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
        build_matrix_rooms_media_proposal(command).model_dump(mode="json")
    )
    assert str(command_file) not in proposal.stdout
