from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications import (
    CommunicationsSecurityPosture,
    build_default_communications_service,
)
from ultimate_ai_agent.core.communications.matrix_crypto import (
    MatrixCryptoCommand,
    MatrixCryptoOperation,
    build_default_matrix_crypto_posture,
    build_matrix_crypto_proposal,
    matrix_crypto_rollback_ref,
    matrix_crypto_request_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


LOCAL_BEARER = "msg-mx-007-local-bearer"
POSTURE_PATH = "/control-center/communications/matrix-crypto/posture"
PROPOSAL_PATH = "/control-center/communications/matrix-crypto/proposal"


def _command() -> MatrixCryptoCommand:
    now = utc_now()
    values: dict[str, object] = {
        "operation": MatrixCryptoOperation.backup_status_read,
        "request_ref": "request-ref:msg-mx-007:api",
        "task_ref": "task-ref:msg-mx-007:api",
        "mission_ref": "mission-ref:msg-mx-007:api",
        "run_ref": "run-ref:msg-mx-007:api",
        "dispatch_ref": "dispatch-ref:msg-mx-007:api",
        "idempotency_ref": "idempotency-ref:msg-mx-007:api",
        "lease_ref": "authority-lease-ref:msg-mx-007:api",
        "account_ref": "account-ref:matrix:api",
        "device_ref": "device-ref:matrix:api",
        "crypto_store_ref": "crypto-store-ref:matrix:api",
        "store_schema_ref": "store-schema-ref:matrix:api:v1",
        "store_generation_ref": "store-generation-ref:matrix:api:1",
        "crypto_key_item_ref": "crypto-key-item-ref:matrix:api",
        "crypto_key_version_ref": "crypto-key-version-ref:matrix:api:1",
        "cross_signing_generation_ref": "cross-signing-generation-ref:matrix:api:1",
        "backup_ref": "backup-ref:matrix:api",
        "backup_version_ref": "backup-version-ref:matrix:api:1",
        "backup_integrity_ref": "backup-integrity-ref:matrix:api:1",
        "backup_key_item_ref": "backup-key-item-ref:matrix:api",
        "backup_key_version_ref": "backup-key-version-ref:matrix:api:1",
        "recovery_target_ref": "recovery-target-ref:matrix:api",
        "recovery_attempt_ref": "recovery-attempt-ref:matrix:api:1",
        "readiness_ref": "readiness-ref:matrix-crypto:adapter-required",
        "rollback_ref": matrix_crypto_rollback_ref(
            MatrixCryptoOperation.backup_status_read
        ),
        "request_created_at": now,
        "start_deadline": now + timedelta(minutes=2),
    }
    values["request_fingerprint_ref"] = matrix_crypto_request_fingerprint_ref(**values)
    return MatrixCryptoCommand(**values)


def test_crypto_posture_route_is_protected_no_store_and_content_free(
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
    assert payload == build_default_matrix_crypto_posture().model_dump(mode="json")
    assert payload["runtime_status"] == "adapter_required"
    assert len(payload["authority_lane_refs"]) == 17
    assert len(payload["live_executor_operation_refs"]) == 0
    assert len(payload["blocked_operation_refs"]) == 17
    assert payload["recovery_material_included"] is False
    assert payload["raw_crypto_payload_included"] is False
    serialized = json.dumps(payload).lower()
    for forbidden in (
        "recovery key value",
        "private key material",
        "raw crypto payload",
        "matrix access token",
        "@private-user",
    ):
        assert forbidden not in serialized


def test_crypto_proposal_binds_idempotency_but_never_executes(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    command = _command()
    client = TestClient(app)
    headers = {
        "Authorization": f"Bearer {LOCAL_BEARER}",
        "x-uaa-idempotency-key": command.idempotency_ref,
    }
    response = client.post(
        PROPOSAL_PATH,
        json={"command": command.model_dump(mode="json")},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.json()["data"]
    assert payload == build_matrix_crypto_proposal(command).model_dump(mode="json")
    assert payload["execution_permitted"] is False
    assert payload["mutation_performed"] is False
    assert payload["approval_ref_authorizes_execution"] is False

    without_header = client.post(
        PROPOSAL_PATH,
        json={"command": command.model_dump(mode="json")},
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert without_header.status_code == 200


def test_crypto_routes_manifest_and_openapi_contracts_are_exact() -> None:
    routes = {route.path: route for route in build_api_manifest(app).routes}
    posture = routes[POSTURE_PATH]
    proposal = routes[PROPOSAL_PATH]
    assert posture.operation_id == (
        "get_control_center_communications_matrix_crypto_posture"
    )
    assert posture.side_effect_class == "none"
    assert posture.route_classification == "local_sensitive"
    assert posture.protected_route is True
    assert posture.idempotency_required is False
    assert proposal.operation_id == (
        "post_control_center_communications_matrix_crypto_proposal"
    )
    assert proposal.side_effect_class == "validation_only"
    assert proposal.route_classification == "local_sensitive"
    assert proposal.protected_route is True
    assert proposal.idempotency_required is False
    assert proposal.validation_only is True
    openapi = app.openapi()["paths"]
    assert openapi[POSTURE_PATH]["get"]["operationId"] == posture.operation_id
    assert openapi[PROPOSAL_PATH]["post"]["operationId"] == proposal.operation_id


def test_security_posture_exposes_same_backend_owned_crypto_truth() -> None:
    security = build_default_communications_service().inspect_security_posture()
    crypto = build_default_matrix_crypto_posture()
    assert security.crypto_runtime_status == "adapter_required"
    assert security.crypto_authority_lane_refs == list(crypto.authority_lane_refs)
    assert security.crypto_live_executor_refs == []
    assert security.crypto_blocked_operation_refs == list(crypto.blocked_operation_refs)
    assert security.recovery_material_included is False
    assert security.raw_crypto_payload_included is False


def test_security_posture_rejects_contradictory_crypto_truth() -> None:
    baseline = (
        build_default_communications_service()
        .inspect_security_posture()
        .model_dump(mode="python")
    )
    mutations = (
        ("crypto_runtime_status", "ready"),
        ("crypto_authority_lane_refs", []),
        ("crypto_blocked_operation_refs", []),
        (
            "crypto_authority_lane_refs",
            [baseline["crypto_authority_lane_refs"][0]] * 17,
        ),
        (
            "crypto_authority_lane_refs",
            [
                "authority-lane-ref:matrix-crypto-not-canonical",
                *baseline["crypto_authority_lane_refs"][1:],
            ],
        ),
        (
            "crypto_blocked_operation_refs",
            [
                "operation-ref:matrix-crypto:not-canonical",
                *baseline["crypto_blocked_operation_refs"][1:],
            ],
        ),
    )
    for field, value in mutations:
        payload = dict(baseline)
        payload[field] = value
        with pytest.raises(ValidationError):
            CommunicationsSecurityPosture.model_validate(payload)


def test_crypto_cli_human_and_json_outputs_share_core_truth() -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [sys.executable, "scripts/dev/uaa_communications.py", "matrix-crypto-status"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix encryption and recovery" in human.stdout
    assert "Runtime: adapter_required" in human.stdout
    assert "Accepted exact authority lanes: 17" in human.stdout
    assert "Live executors: 0" in human.stdout
    assert (
        "Recovery material and raw crypto payloads are never displayed" in human.stdout
    )
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-crypto-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == (
        build_default_matrix_crypto_posture().model_dump(mode="json")
    )


def test_crypto_cli_proposal_is_human_readable_and_non_executing() -> None:
    refs = {
        "request-ref": "request-ref:cli",
        "task-ref": "task-ref:cli",
        "mission-ref": "mission-ref:cli",
        "run-ref": "run-ref:cli",
        "dispatch-ref": "dispatch-ref:cli",
        "idempotency-ref": "idempotency-ref:cli",
        "lease-ref": "authority-lease-ref:cli",
        "account-ref": "account-ref:cli",
        "device-ref": "device-ref:cli",
        "crypto-store-ref": "crypto-store-ref:cli",
        "store-schema-ref": "store-schema-ref:cli",
        "store-generation-ref": "store-generation-ref:cli",
        "crypto-key-item-ref": "crypto-key-item-ref:cli",
        "crypto-key-version-ref": "crypto-key-version-ref:cli",
        "cross-signing-generation-ref": "cross-signing-generation-ref:cli",
        "backup-ref": "backup-ref:cli",
        "backup-version-ref": "backup-version-ref:cli",
        "backup-integrity-ref": "backup-integrity-ref:cli",
        "backup-key-item-ref": "backup-key-item-ref:cli",
        "backup-key-version-ref": "backup-key-version-ref:cli",
        "recovery-target-ref": "recovery-target-ref:cli",
        "recovery-attempt-ref": "recovery-attempt-ref:cli",
        "readiness-ref": "readiness-ref:cli",
    }
    argv = [
        sys.executable,
        "scripts/dev/uaa_communications.py",
        "matrix-crypto",
        "propose",
        "backup-status-read",
    ]
    for name, value in refs.items():
        argv.extend((f"--{name}", value))
    result = subprocess.run(argv, check=True, text=True, capture_output=True)
    assert "Matrix crypto proposal" in result.stdout
    assert "Execution permitted: false" in result.stdout
    assert "no key, recovery material" in result.stdout.lower()
    assert "{" not in result.stdout
