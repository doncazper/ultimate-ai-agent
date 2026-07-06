import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS,
    RUNTIME_DOCTOR_DIAGNOSTICS_CONTRACT_REF,
    RuntimeDoctorDiagnosticItem,
    RuntimeDoctorDiagnosticsReadModel,
    build_runtime_doctor_diagnostics_read_model,
)


client = TestClient(app)


def test_doctor_diagnostics_are_read_only_redacted_status() -> None:
    read_model = build_runtime_doctor_diagnostics_read_model()

    assert read_model.schema_version == "runtime_doctor_diagnostics.v1"
    assert read_model.contract_ref == RUNTIME_DOCTOR_DIAGNOSTICS_CONTRACT_REF
    assert read_model.status == "read_only_diagnostics_posture"
    assert read_model.route_ref == "GET /api/runtime/doctor-diagnostics"
    assert read_model.cli_ref == "uaa runtime inspect-doctor-diagnostics"
    assert read_model.diagnostic_count == 8
    assert read_model.ok_count == 3
    assert read_model.review_count == 4
    assert read_model.blocked_count == 1
    assert read_model.unavailable_count == 0
    assert read_model.setup_visible is True
    assert read_model.runtime_readiness_visible is True
    assert read_model.provider_posture_visible is True
    assert read_model.tool_posture_visible is True
    assert read_model.protected_material_posture_visible is True
    assert read_model.service_posture_visible is True
    assert read_model.authority_posture_visible is True
    assert read_model.next_safe_actions_visible is True
    assert read_model.install_enabled is False
    assert read_model.service_start_enabled is False
    assert read_model.credential_write_enabled is False
    assert read_model.runtime_config_mutation_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_log_persisted is False
    assert read_model.raw_local_path_persisted is False
    assert read_model.provider_payload_persisted is False
    assert set(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-doctor:"
    )


def test_doctor_diagnostic_items_do_not_mutate_or_persist_raw_payloads() -> None:
    read_model = build_runtime_doctor_diagnostics_read_model()

    domains = {item.domain for item in read_model.diagnostics}
    assert domains == {
        "setup",
        "runtime_readiness",
        "providers",
        "tools",
        "protected_material",
        "local_services",
        "authority",
        "next_actions",
    }
    for item in read_model.diagnostics:
        assert item.install_performed is False
        assert item.service_start_performed is False
        assert item.credential_write_performed is False
        assert item.runtime_config_mutation_performed is False
        assert item.raw_log_persisted is False
        assert item.raw_local_path_persisted is False
        assert item.provider_payload_persisted is False
        assert item.proof_refs
        assert set(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS).issubset(
            set(item.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "install_enabled",
        "service_start_enabled",
        "credential_write_enabled",
        "runtime_config_mutation_enabled",
        "control_center_mints_authority",
        "raw_log_persisted",
        "raw_local_path_persisted",
        "provider_payload_persisted",
    ],
)
def test_doctor_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_doctor_diagnostics_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_DOCTOR_AUTHORITY_DENIED"):
        RuntimeDoctorDiagnosticsReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "install_performed",
        "service_start_performed",
        "credential_write_performed",
        "runtime_config_mutation_performed",
        "raw_log_persisted",
        "raw_local_path_persisted",
        "provider_payload_persisted",
    ],
)
def test_doctor_item_denies_mutation_flags(field: str) -> None:
    payload = (
        build_runtime_doctor_diagnostics_read_model()
        .diagnostics[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_DOCTOR_DIAGNOSTIC_AUTHORITY_DENIED",
    ):
        RuntimeDoctorDiagnosticItem(**payload)


def test_doctor_diagnostics_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/doctor-diagnostics")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_doctor_diagnostics"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/doctor-diagnostics"
    assert data["install_enabled"] is False
    assert data["service_start_enabled"] is False
    assert data["credential_write_enabled"] is False
    assert data["runtime_config_mutation_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_log_payload" not in serialized
    assert "provider_payload_value" not in serialized


def test_doctor_diagnostics_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-doctor-diagnostics",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_doctor_diagnostics"]
    assert payload["install_performed"] is False
    assert payload["service_start_performed"] is False
    assert payload["credential_write_performed"] is False
    assert payload["runtime_config_mutation_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/doctor-diagnostics"
    assert read_model["cli_ref"] == "uaa runtime inspect-doctor-diagnostics"
    assert read_model["diagnostic_count"] == 8
