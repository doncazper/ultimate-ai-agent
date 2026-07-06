import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS,
    RUNTIME_MANAGED_SCOPE_POLICY_CONTRACT_REF,
    RuntimeManagedScopePolicyDriftWarning,
    RuntimeManagedScopePolicyPinSource,
    RuntimeManagedScopePolicyReadModel,
    build_runtime_managed_scope_policy_read_model,
)


client = TestClient(app)


def test_managed_scope_policy_is_read_only_local_policy_profile() -> None:
    read_model = build_runtime_managed_scope_policy_read_model()

    assert read_model.schema_version == "runtime_managed_scope_policy.v1"
    assert read_model.contract_ref == RUNTIME_MANAGED_SCOPE_POLICY_CONTRACT_REF
    assert read_model.status == "read_only_local_policy_profile_posture"
    assert read_model.route_ref == "GET /api/runtime/managed-scope-policy"
    assert read_model.cli_ref == "uaa runtime inspect-managed-scope-policy"
    assert read_model.pinned_source_count == 3
    assert read_model.active_pinned_source_count == 3
    assert read_model.drift_warning_count == 1
    assert read_model.blocked_drift_warning_count == 0
    assert read_model.local_config_source_visible is True
    assert read_model.precedence_visible is True
    assert read_model.verification_visible is True
    assert read_model.system_config_write_enabled is False
    assert read_model.privileged_write_enabled is False
    assert read_model.mdm_delivery_enabled is False
    assert read_model.managed_secrets_enabled is False
    assert read_model.unsigned_runtime_config_override_enabled is False
    assert read_model.production_enforcement_claimed is False
    assert read_model.control_center_mints_authority is False
    assert read_model.runtime_config_mutation_performed is False
    assert set(RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-managed-scope:"
    )


def test_managed_scope_sources_and_drift_warnings_are_review_only() -> None:
    read_model = build_runtime_managed_scope_policy_read_model()

    for source in read_model.pinned_sources:
        assert source.pinned is True
        assert source.verified is True
        assert source.system_config_write_performed is False
        assert source.privileged_write_performed is False
        assert source.mdm_delivery_performed is False
        assert source.managed_protected_material_performed is False
        assert source.unsigned_runtime_config_override_performed is False
        assert source.production_enforcement_claimed is False
        assert set(RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS).issubset(
            set(source.blocked_authority_refs)
        )

    for warning in read_model.drift_warnings:
        assert warning.operator_review_required is True
        assert warning.auto_remediation_performed is False
        assert warning.runtime_config_write_performed is False
        assert warning.unsigned_override_accepted is False
        assert warning.production_enforcement_claimed is False
        assert warning.proof_refs


@pytest.mark.parametrize(
    "field",
    [
        "system_config_write_enabled",
        "privileged_write_enabled",
        "mdm_delivery_enabled",
        "managed_secrets_enabled",
        "unsigned_runtime_config_override_enabled",
        "production_enforcement_claimed",
        "control_center_mints_authority",
        "runtime_config_mutation_performed",
        "raw_config_persisted",
        "raw_local_path_persisted",
        "account_material_persisted",
        "credential_material_persisted",
    ],
)
def test_managed_scope_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_managed_scope_policy_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MANAGED_SCOPE_AUTHORITY_DENIED"):
        RuntimeManagedScopePolicyReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "system_config_write_performed",
        "privileged_write_performed",
        "mdm_delivery_performed",
        "managed_protected_material_performed",
        "unsigned_runtime_config_override_performed",
        "production_enforcement_claimed",
    ],
)
def test_managed_scope_pin_source_denies_write_or_enforcement(field: str) -> None:
    payload = (
        build_runtime_managed_scope_policy_read_model()
        .pinned_sources[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MANAGED_SCOPE_PIN_AUTHORITY_DENIED"):
        RuntimeManagedScopePolicyPinSource(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "auto_remediation_performed",
        "runtime_config_write_performed",
        "unsigned_override_accepted",
        "production_enforcement_claimed",
    ],
)
def test_managed_scope_drift_warning_denies_auto_work(field: str) -> None:
    payload = (
        build_runtime_managed_scope_policy_read_model()
        .drift_warnings[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_MANAGED_SCOPE_DRIFT_AUTHORITY_DENIED"):
        RuntimeManagedScopePolicyDriftWarning(**payload)


def test_managed_scope_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/managed-scope-policy")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_managed_scope_policy"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/managed-scope-policy"
    assert data["system_config_write_enabled"] is False
    assert data["privileged_write_enabled"] is False
    assert data["mdm_delivery_enabled"] is False
    assert data["production_enforcement_claimed"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_config_payload" not in serialized
    assert "protected_material_value" not in serialized


def test_managed_scope_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-managed-scope-policy",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_managed_scope_policy"]
    assert payload["system_config_write_performed"] is False
    assert payload["privileged_write_performed"] is False
    assert payload["mdm_delivery_performed"] is False
    assert payload["runtime_config_mutation_performed"] is False
    assert payload["production_enforcement_claimed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/managed-scope-policy"
    assert read_model["cli_ref"] == "uaa runtime inspect-managed-scope-policy"
    assert read_model["pinned_source_count"] == 3
