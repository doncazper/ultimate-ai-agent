from __future__ import annotations

import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.secrets import (
    ProviderCredentialVaultPosture,
    ProviderCredentialVaultRecord,
    ProviderCredentialVaultSnapshot,
    build_provider_credential_vault_snapshot,
)


EXPECTED_POSTURES = {
    "vault_not_configured",
    "vault_blocked",
    "secret_ref_available",
    "secret_ref_revoked",
    "rotation_required",
    "validation_required_but_blocked",
    "invocation_requires_approval",
}


def available_record(**overrides: object) -> ProviderCredentialVaultRecord:
    values: dict[str, object] = {
        "record_ref": "credential-vault-record-ref:openai-compatible:available",
        "posture": ProviderCredentialVaultPosture.secret_ref_available,
        "provider_ref": "provider-ref:openai-compatible:reference",
        "model_ref": "model-ref:openai-compatible:review-only",
        "credential_ref": "credential-ref:openai-compatible:reference",
        "secret_ref": "secret-ref:openai-compatible:metadata-only",
        "policy_ref": "policy-ref:provider-runtime:disabled-by-default",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:required",
        "budget_decision_ref": "budget-decision-ref:openai-compatible:required",
        "expected_receipt_ref": "receipt-ref:openai-compatible:future-required",
        "revocation_ref": "revocation-ref:openai-compatible:not-active",
    }
    values.update(overrides)
    return ProviderCredentialVaultRecord(**values)


def test_credential_vault_snapshot_is_metadata_only_and_safe_refs() -> None:
    snapshot = build_provider_credential_vault_snapshot()
    payload = snapshot.model_dump(mode="json")

    assert snapshot.status == "metadata_only"
    assert snapshot.metadata_only is True
    assert snapshot.safe_refs_only is True
    assert snapshot.secret_collection_enabled is False
    assert snapshot.raw_secret_storage_enabled is False
    assert snapshot.os_credential_backend_access_enabled is False
    assert snapshot.credential_validation_enabled is False
    assert snapshot.provider_invocation_enabled is False
    assert snapshot.provider_sdk_call_enabled is False
    assert snapshot.model_invocation_enabled is False
    assert snapshot.vault_presence_authorizes_validation is False
    assert snapshot.vault_presence_authorizes_invocation is False
    assert set(payload["supported_postures"]) == EXPECTED_POSTURES
    assert len(snapshot.records) >= 3
    assert all(record.metadata_only is True for record in snapshot.records)
    assert all(record.safe_refs_only is True for record in snapshot.records)
    assert all(record.vault_record_grants_authority is False for record in snapshot.records)
    assert all(record.validation_authority_granted is False for record in snapshot.records)
    assert all(record.invocation_authority_granted is False for record in snapshot.records)
    assert "RAW_SECRET_MATERIAL_DENIED" in snapshot.blocker_codes
    assert "PROVIDER_INVOCATION_APPROVAL_REQUIRED" in snapshot.blocker_codes


def test_secret_ref_available_posture_still_cannot_authorize_validation_or_invocation() -> None:
    record = available_record()

    assert record.posture == ProviderCredentialVaultPosture.secret_ref_available
    assert record.metadata_only is True
    assert record.safe_refs_only is True
    assert record.vault_record_grants_authority is False
    assert record.secret_collection_enabled is False
    assert record.raw_secret_material_available is False
    assert record.secret_material_persisted_by_repo is False
    assert record.credential_validation_call_enabled is False
    assert record.validation_authority_granted is False
    assert record.provider_sdk_call_enabled is False
    assert record.model_invocation_enabled is False
    assert record.invocation_authority_granted is False
    assert record.invocation_requires_approval is True
    assert record.exact_scope_required is True
    assert record.budget_decision_required is True
    assert record.expected_receipt_required is True
    assert record.revocation_ref_required is True


def test_credential_vault_record_rejects_authority_flags() -> None:
    denied_fields = [
        "vault_record_grants_authority",
        "secret_collection_enabled",
        "raw_secret_material_available",
        "secret_material_persisted_by_repo",
        "os_credential_backend_access_enabled",
        "credential_validation_call_enabled",
        "validation_authority_granted",
        "provider_sdk_call_enabled",
        "model_invocation_enabled",
        "invocation_authority_granted",
    ]

    for field in denied_fields:
        with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
            ProviderCredentialVaultRecord(**{field: True})


def test_credential_vault_record_rejects_missing_gates_and_bad_posture_refs() -> None:
    with pytest.raises(ValidationError, match="METADATA_ONLY_REQUIRED"):
        ProviderCredentialVaultRecord(metadata_only=False)

    with pytest.raises(ValidationError, match="REQUIRED_GATE_DENIED"):
        ProviderCredentialVaultRecord(invocation_requires_approval=False)

    with pytest.raises(ValidationError, match="SAFE_REF_REQUIRED"):
        ProviderCredentialVaultRecord(provider_ref="")

    with pytest.raises(ValidationError, match="PRIVATE_OR_SECRET_VALUE_REJECTED") as path_exc:
        ProviderCredentialVaultRecord(provider_ref="/Users/example/.env")
    assert "/Users/example/.env" not in str(path_exc.value)

    with pytest.raises(ValidationError, match="PRIVATE_OR_SECRET_VALUE_REJECTED") as user_exc:
        ProviderCredentialVaultRecord(model_ref="username=example-user")
    assert "example-user" not in str(user_exc.value)

    for raw_secret_ref in [
        "secret-ref:openai-compatible:sk-test-token",
        "secret-ref:openai-compatible:xoxb-test-token",
        "secret-ref:openai-compatible:token-test-secret",
    ]:
        with pytest.raises(ValidationError, match="PRIVATE_OR_SECRET_VALUE_REJECTED") as token_exc:
            ProviderCredentialVaultRecord(secret_ref=raw_secret_ref)
        assert raw_secret_ref not in str(token_exc.value)

    with pytest.raises(ValidationError, match="SECRET_REF_REQUIRED"):
        available_record(secret_ref="secret-ref:openai-compatible:not-configured")

    with pytest.raises(ValidationError, match="EXACT_SCOPE_REQUIRED"):
        available_record(model_ref="model-ref:openai-compatible:not-selected")

    with pytest.raises(ValidationError, match="REVOKED_REF_REQUIRED"):
        ProviderCredentialVaultRecord(
            posture=ProviderCredentialVaultPosture.secret_ref_revoked,
            secret_ref="secret-ref:openai-compatible:metadata-only",
        )

    with pytest.raises(ValidationError, match="UNSCOPED_SECRET_REF_DENIED"):
        ProviderCredentialVaultRecord(secret_ref="secret-ref:openai-compatible:metadata-only")


def test_credential_vault_snapshot_rejects_authority_or_posture_drift() -> None:
    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        ProviderCredentialVaultSnapshot(provider_invocation_enabled=True)

    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        ProviderCredentialVaultSnapshot(vault_presence_authorizes_validation=True)

    with pytest.raises(ValidationError, match="STATUS_METADATA_ONLY_REQUIRED"):
        ProviderCredentialVaultSnapshot(status="provider_connected")

    with pytest.raises(ValidationError, match="STATUS_METADATA_ONLY_REQUIRED"):
        ProviderCredentialVaultSnapshot(status="invocation_ready")

    with pytest.raises(ValidationError, match="POSTURES_DRIFTED"):
        ProviderCredentialVaultSnapshot(
            supported_postures=[ProviderCredentialVaultPosture.vault_not_configured]
        )

    invalid_payload = available_record().model_dump(mode="python")
    invalid_payload["validation_authority_granted"] = True
    invalid_record = ProviderCredentialVaultRecord.model_construct(**invalid_payload)
    with pytest.raises(ValidationError, match="RECORD_AUTHORITY_DENIED"):
        ProviderCredentialVaultSnapshot(records=[invalid_record])


def test_credential_vault_contract_cli_inspection_is_safe_schema() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_credential_vault_contract.py"],
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["contract_ref"] == "contract-ref:provider-credential-vault-shell:v1"
    assert set(payload["supported_postures"]) == EXPECTED_POSTURES
    assert payload["metadata_only"] is True
    assert payload["provider_invocation_enabled"] is False
    assert payload["vault_presence_authorizes_invocation"] is False
    assert "RAW_SECRET_MATERIAL_DENIED" in payload["blocker_codes"]
    text = result.stdout.lower()
    for forbidden in [
        "api_key=",
        "raw prompt",
        "raw response",
        "provider payload",
        "/users/",
        "username=",
        "hostname=",
    ]:
        assert forbidden not in text


def test_credential_vault_contracts_revalidate_model_copy_updates() -> None:
    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        available_record().model_copy(update={"invocation_authority_granted": True})

    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        build_provider_credential_vault_snapshot().model_copy(
            update={"credential_validation_enabled": True}
        )
