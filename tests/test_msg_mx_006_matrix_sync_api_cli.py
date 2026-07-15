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
from ultimate_ai_agent.core.communications.matrix_sync import (
    build_default_matrix_sync_posture,
)


LOCAL_BEARER = "msg-mx-006-local-bearer"
PATH = "/control-center/communications/matrix-sync/posture"


def test_matrix_sync_posture_route_is_protected_no_store_and_content_free(
    monkeypatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    client = TestClient(app)
    assert client.get(PATH).status_code == 401
    response = client.get(PATH, headers={"Authorization": f"Bearer {LOCAL_BEARER}"})
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.json()["data"]
    assert payload == build_default_matrix_sync_posture().model_dump(mode="json")
    assert payload["runtime_status"] == "configuration_required"
    assert payload["content_untrusted"] is True
    assert payload["not_instruction_authority"] is True
    assert payload["raw_content_included"] is False
    assert len(payload["authority_lane_refs"]) == 12
    assert len(payload["concrete_transport_operation_refs"]) == 2
    assert len(payload["uncomposed_executor_operation_refs"]) == 10
    assert "blocker-ref:matrix-sync:canonical-operation-executors-required" in (
        payload["blocker_refs"]
    )
    serialized = json.dumps(payload).lower()
    for forbidden in (
        "private message body",
        "matrix access token",
        "raw provider payload",
        "@private-user",
        "!private-room",
    ):
        assert forbidden not in serialized


def test_matrix_sync_posture_manifest_and_openapi_are_exact() -> None:
    route = next(
        item for item in build_api_manifest(app).routes if item.path == PATH
    )
    assert route.method == "GET"
    assert route.operation_id == "get_control_center_communications_matrix_sync_posture"
    assert route.side_effect_class == "none"
    assert route.route_classification == "local_sensitive"
    assert route.protected_route is True
    assert route.idempotency_required is False
    assert app.openapi()["paths"][PATH]["get"]["operationId"] == route.operation_id


def test_matrix_sync_cli_human_and_json_outputs_share_core_truth() -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [sys.executable, "scripts/dev/uaa_communications.py", "matrix-sync-status"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix read-only sync" in human.stdout
    assert "Runtime: configuration_required" in human.stdout
    assert "Declared authority lanes: 12" in human.stdout
    assert "Concrete GET transports: 2" in human.stdout
    assert "Uncomposed exact executors: 10" in human.stdout
    assert "External writes: denied" in human.stdout
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-sync-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == build_default_matrix_sync_posture().model_dump(
        mode="json"
    )
