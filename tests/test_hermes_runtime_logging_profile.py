import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_LOGGING_PROFILE_CONTRACT_REF,
    RuntimeLoggingProfileReadModel,
    RuntimeLoggingProfileRecord,
    build_runtime_logging_profile_read_model,
)


client = TestClient(app)


def test_logging_profile_is_quiet_default_read_model() -> None:
    read_model = build_runtime_logging_profile_read_model()

    assert read_model.schema_version == "runtime_logging_profile.v1"
    assert read_model.contract_ref == RUNTIME_LOGGING_PROFILE_CONTRACT_REF
    assert read_model.status == "quiet_default_redacted_troubleshooting_available"
    assert read_model.route_ref == "GET /api/runtime/logging-profile"
    assert read_model.cli_ref == "uaa runtime inspect-logging-profile"
    assert read_model.active_profile_ref == "logging-profile-ref:runtime:quiet-normal"
    assert read_model.profile_count == 3
    assert read_model.quiet_default_count == 1
    assert read_model.disabled_until_flagged_count == 1
    assert read_model.blocked_raw_detail_count == 1
    assert read_model.flag_scope_visible is True
    assert read_model.ttl_policy_visible is True
    assert read_model.redaction_rules_visible is True
    assert read_model.retention_policy_visible is True
    assert read_model.operator_proof_visible is True
    assert read_model.safe_disable_visible is True
    assert read_model.verbose_logging_enabled is False
    assert read_model.raw_logs_persisted is False
    assert read_model.raw_prompt_persisted is False
    assert read_model.raw_response_persisted is False
    assert read_model.provider_payload_persisted is False
    assert read_model.local_path_persisted is False
    assert read_model.credential_material_persisted is False
    assert read_model.remote_telemetry_export_enabled is False
    assert read_model.background_log_stream_enabled is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_logging_profiles_have_retention_and_redaction_contracts() -> None:
    read_model = build_runtime_logging_profile_read_model()
    statuses = {profile.profile_kind: profile.profile_status for profile in read_model.profiles}

    assert statuses == {
        "quiet_normal": "active_default",
        "redacted_troubleshooting": "disabled_until_flagged",
        "forensic_safe_refs": "blocked_raw_detail",
    }
    for profile in read_model.profiles:
        assert profile.profile_ref.startswith("logging-profile-ref:")
        assert profile.flag_scope_ref.startswith("logging-flag-scope-ref:")
        assert profile.ttl_policy_ref.startswith("ttl-policy-ref:")
        assert profile.retention_policy_ref.startswith("retention-policy-ref:")
        assert profile.redaction_policy_ref.startswith("redaction-policy-ref:")
        assert profile.redaction_verifier_ref.startswith("redaction-verifier-ref:")
        assert profile.proof_ref.startswith("proof-ref:")
        assert profile.visible_in_control_center is True
        assert profile.operator_flag_required is True
        assert profile.safe_disable_available is True
        assert profile.raw_logs_persisted is False
        assert profile.raw_prompt_persisted is False
        assert profile.raw_response_persisted is False
        assert profile.provider_payload_persisted is False
        assert profile.local_path_persisted is False
        assert profile.credential_material_persisted is False
        assert profile.remote_telemetry_export_enabled is False
        assert profile.background_log_stream_enabled is False
        assert profile.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "verbose_logging_enabled",
        "raw_logs_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "local_path_persisted",
        "credential_material_persisted",
        "remote_telemetry_export_enabled",
        "background_log_stream_enabled",
        "control_center_mints_authority",
    ],
)
def test_logging_profile_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_logging_profile_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_LOGGING_PROFILE_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeLoggingProfileReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "raw_logs_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "local_path_persisted",
        "credential_material_persisted",
        "remote_telemetry_export_enabled",
        "background_log_stream_enabled",
        "control_center_mints_authority",
    ],
)
def test_logging_profile_record_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_logging_profile_read_model()
        .profiles[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_LOGGING_PROFILE_RECORD_AUTHORITY_DENIED",
    ):
        RuntimeLoggingProfileRecord(**payload)


def test_logging_profile_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/logging-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_logging_profile"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/logging-profile"
    assert data["profile_count"] == 3
    assert data["verbose_logging_enabled"] is False
    assert data["raw_logs_persisted"] is False
    assert data["remote_telemetry_export_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "raw_log_value" not in serialized
    assert "raw_prompt_value" not in serialized
    assert "provider_payload_value" not in serialized


def test_logging_profile_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-logging-profile",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_logging_profile"]
    assert payload["metadata_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["verbose_logging_toggled"] is False
    assert payload["raw_logs_omitted"] is True
    assert payload["remote_telemetry_export_performed"] is False
    assert payload["background_log_stream_started"] is False
    assert read_model["route_ref"] == "GET /api/runtime/logging-profile"
    assert read_model["cli_ref"] == "uaa runtime inspect-logging-profile"
    assert read_model["profile_count"] == 3
