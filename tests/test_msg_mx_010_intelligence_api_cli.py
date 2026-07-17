from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import ultimate_ai_agent.api.communications as communications_api
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_intelligence import (
    MatrixIntelligenceOperation,
    build_default_matrix_intelligence_posture,
    build_matrix_intelligence_command,
    build_matrix_intelligence_command_proposal,
)
from ultimate_ai_agent.core.communications.matrix_intelligence.constants import (
    matrix_intelligence_rollback_ref,
)


LOCAL_BEARER = "msg-mx-010-local-bearer"
POSTURE_PATH = "/control-center/communications/matrix-intelligence/posture"
PROPOSAL_PATH = "/control-center/communications/matrix-intelligence/proposal"
POLICY_READ_PATH = (
    "/control-center/communications/matrix-intelligence/room-ai-policy-read"
)


def _policy_read_command():
    now = datetime.now(UTC)
    operation = MatrixIntelligenceOperation.room_ai_policy_read
    return build_matrix_intelligence_command(
        operation=operation,
        request_ref="request-ref:msg-mx-010:api",
        task_ref="task-ref:msg-mx-010:api",
        mission_ref="mission-ref:msg-mx-010:api",
        run_ref="run-ref:msg-mx-010:api",
        dispatch_ref="dispatch-ref:msg-mx-010:api",
        idempotency_ref="idempotency-ref:msg-mx-010:api",
        lease_ref="lease-ref:msg-mx-010:api",
        account_ref="account-ref:matrix:api",
        room_ref="room-ref:matrix:api",
        event_range_ref="event-range-ref:matrix:api",
        policy_ref="policy-ref:matrix-room-ai:api",
        readiness_ref="readiness-ref:matrix-intelligence:api",
        rollback_ref=matrix_intelligence_rollback_ref(operation),
        request_created_at=now,
        start_deadline=now + timedelta(seconds=30),
    )


def _headers(command) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LOCAL_BEARER}",
        "x-uaa-idempotency-key": command.idempotency_ref,
    }


def test_intelligence_posture_is_protected_content_free_and_truthful(
    monkeypatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    client = TestClient(app)
    assert client.get(POSTURE_PATH).status_code == 401
    response = client.get(
        POSTURE_PATH, headers={"Authorization": f"Bearer {LOCAL_BEARER}"}
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.json()["data"]
    assert payload == build_default_matrix_intelligence_posture().model_dump(
        mode="json"
    )
    assert payload["provider_invocation_enabled"] is False
    assert payload["attachment_analysis_enabled"] is False
    assert payload["automatic_memory_write_enabled"] is False
    assert payload["raw_content_persisted"] is False


def test_intelligence_proposal_and_operation_routes_bind_core_truth(
    monkeypatch,
) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _policy_read_command()
    client = TestClient(app)
    proposal_response = client.post(
        PROPOSAL_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert proposal_response.status_code == 200
    assert proposal_response.json()["data"] == (
        build_matrix_intelligence_command_proposal(command).model_dump(mode="json")
    )

    monkeypatch.setattr(
        communications_api,
        "_MATRIX_INTELLIGENCE_OPERATION_HANDLER",
        lambda payload: {
            "operation": payload.command.operation.value,
            "receipt_ref": "receipt-ref:matrix-intelligence:content-free",
            "raw_content_included": False,
        },
    )
    response = client.post(
        POLICY_READ_PATH,
        json={"command": command.model_dump(mode="json"), "confirmed": True},
        headers=_headers(command),
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["data"]["operation"] == "room_ai_policy_read"

    missing = client.post(
        POLICY_READ_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert missing.status_code == 428


def test_intelligence_routes_manifest_and_openapi_are_exact() -> None:
    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if "/matrix-intelligence/" in route.path
    }
    assert len(routes) == 8
    assert routes[POSTURE_PATH].side_effect_class == "none"
    assert routes[PROPOSAL_PATH].side_effect_class == "validation_only"
    assert routes[POLICY_READ_PATH].side_effect_class == "local_sensitive"
    assert routes[POLICY_READ_PATH].route_classification == (
        "mutating_requires_authority"
    )
    assert routes[POLICY_READ_PATH].idempotency_required is True
    delete_path = "/control-center/communications/matrix-intelligence/proposal-delete"
    assert routes[delete_path].side_effect_class == "destructive_local_sensitive"
    openapi = app.openapi()["paths"]
    for path, route in routes.items():
        assert openapi[path][route.method.lower()]["operationId"] == route.operation_id
    assert not any("provider" in path or "attachment" in path for path in routes)


def test_intelligence_cli_status_and_proposal_share_core_truth(tmp_path) -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-intelligence-status",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix intelligence and review-only proposals" in human.stdout
    assert "provider_invocation: blocked_missing_exact_authority" in human.stdout
    assert "Autonomous send and automatic Memory: denied" in human.stdout
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-intelligence-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == (
        build_default_matrix_intelligence_posture().model_dump(mode="json")
    )

    command = _policy_read_command()
    command_file = tmp_path / "matrix-intelligence-command.json"
    command_file.write_text(command.model_dump_json())
    proposal = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-intelligence",
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
        build_matrix_intelligence_command_proposal(command).model_dump(mode="json")
    )
    assert str(command_file) not in proposal.stdout
