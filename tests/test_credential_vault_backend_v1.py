from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.secrets import (
    LocalCredentialVaultBackend,
    LocalCredentialVaultEnrollmentRequest,
    LocalCredentialVaultInspectionSnapshot,
    LocalCredentialVaultOperationReceipt,
    LocalCredentialVaultRecord,
    LocalCredentialVaultRevokeRequest,
    LocalCredentialVaultRotationRequiredRequest,
    ProviderCredentialVaultPosture,
    build_local_credential_vault_enrollment_approval_request,
    build_local_credential_vault_revoke_approval_request,
    build_local_credential_vault_rotation_approval_request,
)


def enrollment_request(**overrides: object) -> LocalCredentialVaultEnrollmentRequest:
    values: dict[str, object] = {
        "run_id": "run-ref:credential-vault:test",
        "provider_ref": "provider-ref:openai-compatible:reference",
        "model_ref": "model-ref:openai-compatible:review-only",
        "credential_ref": "credential-ref:openai-compatible:scoped-local",
        "policy_ref": "policy-ref:provider-runtime:disabled-by-default",
        "approval_ref": "approval-ref:credential-vault:enroll",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:required",
        "budget_decision_ref": "budget-decision-ref:openai-compatible:required",
        "expected_receipt_ref": "receipt-ref:credential-vault:enroll",
        "idempotency_ref": "idempotency-ref:credential-vault:enroll",
        "secret_value": SecretStr(f"transient-{uuid.uuid4().hex}"),
    }
    values.update(overrides)
    return LocalCredentialVaultEnrollmentRequest(**values)


def exact_authority_for_enrollment(
    request: LocalCredentialVaultEnrollmentRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_enrollment_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def exact_authority_for_revoke(
    request: LocalCredentialVaultRevokeRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_revoke_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def exact_authority_for_rotation(
    request: LocalCredentialVaultRotationRequiredRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_rotation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def test_backend_inspection_is_read_only_when_state_is_missing(tmp_path: Path) -> None:
    state_dir = tmp_path / "missing-vault-state"
    backend = LocalCredentialVaultBackend(state_dir)
    snapshot = backend.inspect()

    assert snapshot.posture == ProviderCredentialVaultPosture.vault_not_configured
    assert snapshot.record_count == 0
    assert snapshot.records == []
    assert snapshot.supports_enroll is True
    assert snapshot.supports_revoke is True
    assert snapshot.raw_secret_material_persisted is False
    assert snapshot.secret_resolution_enabled is False
    assert snapshot.credential_validation_enabled is False
    assert snapshot.provider_invocation_enabled is False
    assert not state_dir.exists()


def test_enroll_persists_only_safe_refs_and_returns_secret_ref(tmp_path: Path) -> None:
    backend = LocalCredentialVaultBackend(tmp_path / "vault")
    transient_value = f"transient-{uuid.uuid4().hex}"
    request = enrollment_request(secret_value=SecretStr(transient_value))
    receipt = backend.enroll_secret(
        request,
        approval_authority=exact_authority_for_enrollment(request),
    )
    snapshot = backend.inspect()
    ledger_text = backend.ledger_path.read_text(encoding="utf-8")

    assert receipt.allowed is True
    assert receipt.secret_ref.startswith("secret-ref:")
    assert receipt.posture == ProviderCredentialVaultPosture.secret_ref_available
    assert receipt.raw_secret_material_persisted is False
    assert receipt.raw_secret_material_returned is False
    assert receipt.recoverable_secret_material_available is False
    assert receipt.secret_resolution_enabled is False
    assert "PROVIDER_VALIDATION_BLOCKED" in receipt.reason_codes
    assert "PROVIDER_INVOCATION_BLOCKED" in receipt.reason_codes
    assert snapshot.posture == ProviderCredentialVaultPosture.secret_ref_available
    assert snapshot.record_count == 1
    assert snapshot.records[0].secret_ref == receipt.secret_ref
    assert transient_value not in ledger_text
    assert transient_value not in receipt.model_dump_json()
    assert transient_value not in snapshot.model_dump_json()


def test_mutating_operations_require_exact_local_approval(tmp_path: Path) -> None:
    backend = LocalCredentialVaultBackend(tmp_path / "vault")
    request = enrollment_request()

    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        backend.enroll_secret(request)
    assert not backend.ledger_path.exists()

    wrong_scope = enrollment_request(
        model_ref="model-ref:openai-compatible:different",
        secret_value=SecretStr(f"transient-{uuid.uuid4().hex}"),
    )
    wrong_authority = exact_authority_for_enrollment(wrong_scope)
    with pytest.raises(ValueError, match="APPROVAL_DENIED"):
        backend.enroll_secret(request, approval_authority=wrong_authority)
    assert not backend.ledger_path.exists()


def test_enroll_revoke_and_rotation_are_idempotent(tmp_path: Path) -> None:
    backend = LocalCredentialVaultBackend(tmp_path / "vault")
    request = enrollment_request()
    authority = exact_authority_for_enrollment(request)
    first = backend.enroll_secret(request, approval_authority=authority)
    replay = backend.enroll_secret(request, approval_authority=authority)

    assert replay == first
    assert len(backend.ledger_path.read_text(encoding="utf-8").splitlines()) == 1

    drifted_request = enrollment_request(
        expected_receipt_ref="receipt-ref:credential-vault:drifted",
        secret_value=SecretStr(f"transient-{uuid.uuid4().hex}"),
    )
    drifted_authority = exact_authority_for_enrollment(drifted_request)
    with pytest.raises(ValueError, match="IDEMPOTENCY_SCOPE_CONFLICT"):
        backend.enroll_secret(drifted_request, approval_authority=drifted_authority)

    drifted_rotation_ref = enrollment_request(
        rotation_required_ref="rotation-ref:credential-vault:drifted",
        secret_value=SecretStr(f"transient-{uuid.uuid4().hex}"),
    )
    drifted_rotation_authority = exact_authority_for_enrollment(drifted_rotation_ref)
    with pytest.raises(ValueError, match="IDEMPOTENCY_SCOPE_CONFLICT"):
        backend.enroll_secret(
            drifted_rotation_ref,
            approval_authority=drifted_rotation_authority,
        )

    rotation_request = LocalCredentialVaultRotationRequiredRequest(
        run_id=request.run_id,
        secret_ref=first.secret_ref,
        rotation_required_ref="rotation-ref:credential-vault:idempotent",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:idempotent-rotation",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        expected_receipt_ref="receipt-ref:credential-vault:idempotent-rotation",
        idempotency_ref="idempotency-ref:credential-vault:idempotent-rotation",
    )
    rotation_authority = exact_authority_for_rotation(rotation_request)
    rotation = backend.mark_rotation_required(rotation_request, approval_authority=rotation_authority)
    rotation_replay = backend.mark_rotation_required(
        rotation_request,
        approval_authority=rotation_authority,
    )
    assert rotation_replay == rotation

    revoke_request = LocalCredentialVaultRevokeRequest(
        run_id=request.run_id,
        secret_ref=first.secret_ref,
        revocation_ref="revocation-ref:credential-vault:idempotent",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:idempotent-revoke",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        expected_receipt_ref="receipt-ref:credential-vault:idempotent-revoke",
        idempotency_ref="idempotency-ref:credential-vault:idempotent-revoke",
    )
    revoke_authority = exact_authority_for_revoke(revoke_request)
    revoked = backend.revoke_secret_ref(revoke_request, approval_authority=revoke_authority)
    revoked_replay = backend.revoke_secret_ref(revoke_request, approval_authority=revoke_authority)
    assert revoked_replay == revoked
    assert len(backend.ledger_path.read_text(encoding="utf-8").splitlines()) == 3


def test_available_secret_ref_still_cannot_authorize_runtime() -> None:
    record = LocalCredentialVaultRecord(
        record_ref="credential-vault-record-ref:openai-compatible:available",
        run_id="run-ref:credential-vault:test",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        provider_ref="provider-ref:openai-compatible:reference",
        model_ref="model-ref:openai-compatible:review-only",
        credential_ref="credential-ref:openai-compatible:scoped-local",
        secret_ref="secret-ref:openai-compatible:scoped-local",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:available",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        budget_decision_ref="budget-decision-ref:openai-compatible:required",
        expected_receipt_ref="receipt-ref:credential-vault:available",
        revocation_ref="revocation-ref:provider-runtime:not-active",
        rotation_required_ref="rotation-ref:provider-runtime:not-required",
        enrollment_receipt_ref="receipt-ref:credential-vault:available",
        last_operation_receipt_ref="receipt-ref:credential-vault:available",
    )

    assert record.safe_refs_only is True
    assert record.transient_secret_discarded is True
    assert record.raw_secret_material_persisted is False
    assert record.raw_secret_material_returned is False
    assert record.secret_resolution_enabled is False
    assert record.credential_validation_enabled is False
    assert record.provider_sdk_call_enabled is False
    assert record.model_invocation_enabled is False
    assert record.provider_invocation_enabled is False
    assert record.billing_authority_granted is False
    assert record.vault_presence_authorizes_validation is False
    assert record.vault_presence_authorizes_invocation is False


def test_revoke_and_rotation_required_are_durable_safe_ref_postures(tmp_path: Path) -> None:
    backend = LocalCredentialVaultBackend(tmp_path / "vault")
    enrollment = enrollment_request()
    enroll = backend.enroll_secret(
        enrollment,
        approval_authority=exact_authority_for_enrollment(enrollment),
    )
    rotation_request = LocalCredentialVaultRotationRequiredRequest(
        run_id=enrollment.run_id,
        secret_ref=enroll.secret_ref,
        rotation_required_ref="rotation-ref:credential-vault:required",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:rotation",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        expected_receipt_ref="receipt-ref:credential-vault:rotation",
        idempotency_ref="idempotency-ref:credential-vault:rotation",
    )
    rotation = backend.mark_rotation_required(
        rotation_request,
        approval_authority=exact_authority_for_rotation(rotation_request),
    )
    revoke_request = LocalCredentialVaultRevokeRequest(
        run_id=enrollment.run_id,
        secret_ref=enroll.secret_ref,
        revocation_ref="revocation-ref:credential-vault:revoked",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:revoke",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        expected_receipt_ref="receipt-ref:credential-vault:revoke",
        idempotency_ref="idempotency-ref:credential-vault:revoke",
    )
    revoked = backend.revoke_secret_ref(
        revoke_request,
        approval_authority=exact_authority_for_revoke(revoke_request),
    )
    snapshot = backend.inspect()
    payload = json.loads(backend.ledger_path.read_text(encoding="utf-8").splitlines()[-1])

    assert rotation.posture == ProviderCredentialVaultPosture.rotation_required
    assert revoked.posture == ProviderCredentialVaultPosture.secret_ref_revoked
    assert snapshot.posture == ProviderCredentialVaultPosture.secret_ref_revoked
    assert snapshot.records[0].secret_ref == enroll.secret_ref
    assert payload["record"]["posture"] == "secret_ref_revoked"
    assert payload["receipt"]["raw_secret_material_persisted"] is False
    assert payload["receipt"]["provider_invocation_enabled"] is False


def test_backend_contracts_reject_authority_and_unsafe_refs() -> None:
    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        LocalCredentialVaultInspectionSnapshot(secret_resolution_enabled=True)

    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        LocalCredentialVaultOperationReceipt(
            receipt_ref="receipt-ref:credential-vault:unsafe",
            run_id="run-ref:credential-vault:test",
            operation="enroll",
            allowed=True,
            posture=ProviderCredentialVaultPosture.secret_ref_available,
            record_ref="credential-vault-record-ref:openai-compatible:unsafe",
            secret_ref="secret-ref:openai-compatible:unsafe",
            provider_ref="provider-ref:openai-compatible:reference",
            model_ref="model-ref:openai-compatible:review-only",
            credential_ref="credential-ref:openai-compatible:scoped-local",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            approval_ref="approval-ref:credential-vault:unsafe",
            approval_scope_ref="approval-scope-ref:provider-runtime:required",
            budget_decision_ref="budget-decision-ref:openai-compatible:required",
            expected_receipt_ref="receipt-ref:credential-vault:unsafe",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            rotation_required_ref="rotation-ref:provider-runtime:not-required",
            idempotency_ref="idempotency-ref:credential-vault:unsafe",
            provider_invocation_enabled=True,
        )

    with pytest.raises(ValidationError, match="SAFE_REF_REQUIRED"):
        enrollment_request(provider_ref="provider-ref:bad space")

    with pytest.raises(ValidationError, match="SECRET_VALUE_REQUIRED"):
        enrollment_request(secret_value=SecretStr(""))


def test_backend_cli_inspection_emits_safe_schema(tmp_path: Path) -> None:
    backend = LocalCredentialVaultBackend(tmp_path / "vault")
    transient_value = f"transient-{uuid.uuid4().hex}"
    request = enrollment_request(secret_value=SecretStr(transient_value))
    backend.enroll_secret(
        request,
        approval_authority=exact_authority_for_enrollment(request),
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_credential_vault_backend.py",
            "--state-dir",
            str(backend.state_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["backend_ref"] == "credential-vault-backend-ref:local-secret-ref:v1"
    assert payload["posture"] == "secret_ref_available"
    assert payload["record_count"] == 1
    assert payload["secret_resolution_enabled"] is False
    assert payload["credential_validation_enabled"] is False
    assert payload["provider_invocation_enabled"] is False
    assert transient_value not in result.stdout


def test_backend_v1_manifest_declares_backend_without_runtime_authority() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")

    assert "provider_credential_vault_local_secret_ref_backend_v1" in manifest["capabilities_declared"]
    assert "provider_credential_vault_backend_cli_inspection" in manifest["capabilities_declared"]
    assert "provider_credential_vault_secret_resolution_api" in manifest["capabilities_blocked"]
    assert "provider_credential_vault_validation_authority" in manifest["capabilities_blocked"]
    assert "provider_credential_vault_invocation_authority" in manifest["capabilities_blocked"]
