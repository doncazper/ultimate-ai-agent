import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_REMOTE_EXECUTION_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS,
    RUNTIME_REMOTE_EXECUTION_POSTURE_ROUTE_REF,
    RuntimeExecutionBackendCapability,
    RuntimeRemoteExecutionPostureReadModel,
    build_runtime_remote_execution_posture_read_model,
)


client = TestClient(app)


def test_remote_execution_is_capability_map_only() -> None:
    read_model = build_runtime_remote_execution_posture_read_model()

    assert read_model.schema_version == "runtime_remote_execution_posture.v1"
    assert read_model.status == "capability_map_only"
    assert read_model.route_ref == RUNTIME_REMOTE_EXECUTION_POSTURE_ROUTE_REF
    assert read_model.cli_ref == "uaa runtime inspect-remote-execution-posture"
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_REMOTE_EXECUTION_POSTURE_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_route_ref == "GET /api/runtime/authority-state"
    assert (
        read_model.authority_state_cli_ref
        == "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_status == "implemented_authority_bound_read_model"
    assert "reason-ref:authority:active-lease-grants-domain-capability" in (
        read_model.authority_state_reason_refs
    )
    assert "adapter-ref:remote-execution-ssh:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.backend_count == 6
    assert read_model.blocked_backend_count == 6
    assert read_model.remote_execution_enabled is False
    assert read_model.ssh_enabled is False
    assert read_model.cloud_sandbox_enabled is False
    assert read_model.remote_shell_enabled is False
    assert read_model.file_sync_enabled is False
    assert read_model.remote_secret_access_enabled is False
    assert read_model.remote_process_control_enabled is False
    assert read_model.credential_material_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_remote_execution_route_returns_authority_bound_read_model() -> None:
    response = client.get("/api/runtime/remote-execution-posture")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_remote_execution_posture"
    data = body["data"]
    assert data["schema_version"] == "runtime_remote_execution_posture.v1"
    assert data["route_ref"] == "GET /api/runtime/remote-execution-posture"
    assert (
        data["authority_state_mapping_ref"]
        == "lane-ref:runtime-remote-execution-posture-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["backend_count"] == 6
    assert data["blocked_backend_count"] == 6
    assert data["remote_execution_enabled"] is False
    assert data["ssh_enabled"] is False
    assert data["cloud_sandbox_enabled"] is False
    assert data["file_sync_enabled"] is False


def test_remote_execution_backend_map_is_blocked() -> None:
    read_model = build_runtime_remote_execution_posture_read_model()
    backend_kinds = {backend.backend_kind for backend in read_model.backends}

    assert backend_kinds == {
        "local_workspace",
        "local_container",
        "secure_host",
        "cloud_sandbox",
        "serverless_worker",
        "remote_gpu",
    }
    for backend in read_model.backends:
        assert backend.status == "blocked_until_authority"
        assert backend.backend_ref.startswith("execution-backend-ref:")
        assert backend.workspace_boundary_ref.startswith("workspace-boundary-ref:")
        assert backend.credential_policy_ref.startswith("credential-policy-ref:")
        assert backend.network_policy_ref.startswith("network-policy-ref:")
        assert backend.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert backend.budget_ref.startswith("budget-ref:")
        assert backend.rollback_ref.startswith("rollback-ref:")
        assert backend.kill_switch_ref.startswith("kill-switch-ref:")
        assert backend.remote_execution_enabled is False
        assert backend.ssh_enabled is False
        assert backend.cloud_sandbox_enabled is False
        assert backend.remote_shell_enabled is False
        assert backend.file_sync_enabled is False
        assert backend.remote_secret_access_enabled is False
        assert backend.remote_process_control_enabled is False
        assert backend.credential_material_persisted is False
        assert backend.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "remote_execution_enabled",
        "ssh_enabled",
        "cloud_sandbox_enabled",
        "remote_shell_enabled",
        "file_sync_enabled",
        "remote_secret_access_enabled",
        "remote_process_control_enabled",
        "credential_material_persisted",
        "control_center_mints_authority",
    ],
)
def test_remote_execution_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_remote_execution_posture_read_model().model_dump(
        mode="json"
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_REMOTE_EXECUTION_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeRemoteExecutionPostureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "remote_execution_enabled",
        "ssh_enabled",
        "cloud_sandbox_enabled",
        "remote_shell_enabled",
        "file_sync_enabled",
        "remote_secret_access_enabled",
        "remote_process_control_enabled",
        "credential_material_persisted",
        "control_center_mints_authority",
    ],
)
def test_remote_execution_backend_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_remote_execution_posture_read_model()
        .backends[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_REMOTE_EXECUTION_BACKEND_AUTHORITY_DENIED",
    ):
        RuntimeExecutionBackendCapability(**payload)


def test_remote_execution_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-remote-execution-posture",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "credential_value" not in result.stdout
    assert "remote_path_value" not in result.stdout
    payload = json.loads(result.stdout)
    read_model = payload["runtime_remote_execution_posture"]
    assert payload["remote_execution_performed"] is False
    assert payload["ssh_performed"] is False
    assert payload["remote_shell_performed"] is False
    assert payload["file_sync_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/remote-execution-posture"
    assert (
        read_model["authority_state_mapping_ref"]
        == "lane-ref:runtime-remote-execution-posture-read-model"
    )
    assert read_model["authority_state_decision_outcome"] == "allow"
    assert read_model["backend_count"] == 6
    assert read_model["blocked_backend_count"] == 6
