from typing import Any
import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.providers import (
    GovernedProviderInvocationReadiness,
    GovernedProviderInvocationReceipt,
    GovernedProviderInvocationRequest,
    ProviderCredentialValidationReceipt,
    ProviderCredentialValidationReadiness,
    ProviderCredentialValidationRequest,
)
from ultimate_ai_agent.core.secrets import (
    BlockedCredentialVaultAdapter,
    CredentialVaultAdapterCapabilityReport,
    CredentialVaultAdapterDecision,
    CredentialVaultResolveRequest,
    CredentialVaultRevokeRequest,
    CredentialVaultStoreRequest,
    ProviderCredentialEnrollmentReadiness,
    ProviderCredentialVaultAdapterReadiness,
)


def vault_store_request(**overrides: Any) -> CredentialVaultStoreRequest:
    values = {
        "credential_ref": "credential-ref:provider:test",
        "provider_id": "provider:test",
        "provider_manifest_ref": "provider-manifest-ref:provider:test",
        "consent_ref": "consent-ref:provider:test",
        "policy_ref": "policy-ref:provider:test",
        "approval_ref": "approval-ref:provider:test",
        "revocation_ref": "revocation-ref:provider:test",
        "idempotency_key": "idempotency-ref:provider:test",
        "audit_ref": "audit-ref:provider:test",
        "rollback_ref": "rollback-ref:provider:test",
        "safe_disable_ref": "safe-disable-ref:provider:test",
    }
    values.update(overrides)
    return CredentialVaultStoreRequest(**values)


def validation_request(**overrides: Any) -> ProviderCredentialValidationRequest:
    values = {
        "provider_manifest_ref": "provider-manifest-ref:provider:test",
        "provider_allowlist_ref": "provider-allowlist-ref:provider:test",
        "credential_ref": "credential-ref:provider:test",
        "consent_ref": "consent-ref:provider:test",
        "policy_ref": "policy-ref:provider:test",
        "approval_ref": "approval-ref:provider:test",
        "revocation_ref": "revocation-ref:provider:test",
        "validation_receipt_ref": "receipt-ref:provider-validation:test",
        "rate_budget_ref": "rate-budget-ref:provider:test",
    }
    values.update(overrides)
    return ProviderCredentialValidationRequest(**values)


def invocation_request(**overrides: Any) -> GovernedProviderInvocationRequest:
    values = {
        "policy_decision_ref": "policy-decision-ref:provider:test",
        "approval_ref": "approval-ref:provider:test",
        "provider_manifest_allowlist_ref": "provider-allowlist-ref:provider:test",
        "credential_ref": "credential-ref:provider:test",
        "consent_ref": "consent-ref:provider:test",
        "revocation_ref": "revocation-ref:provider:test",
        "redacted_request_summary_ref": "request-summary-ref:provider:test",
        "redacted_response_summary_ref": "response-summary-ref:provider:test",
        "audit_ref": "audit-ref:provider:test",
        "receipt_ref": "receipt-ref:provider:test",
        "rollback_or_safe_disable_ref": "safe-disable-ref:provider:test",
        "rate_budget_ref": "rate-budget-ref:provider:test",
    }
    values.update(overrides)
    return GovernedProviderInvocationRequest(**values)


def test_vault_adapter_readiness_is_disabled_and_safe_by_default() -> None:
    readiness = ProviderCredentialVaultAdapterReadiness()
    serialized = readiness.model_dump_json()

    assert readiness.adapter_runtime_enabled is False
    assert readiness.credential_material_stored_by_repo is False
    assert readiness.raw_key_visible is False
    assert readiness.readiness_status == "blocked_no_approved_backend"
    assert "VAULT_ADAPTER_NOT_SCOPED" in readiness.blocker_codes
    assert "api_key" not in serialized.lower()
    assert "token=" not in serialized.lower()


def test_blocked_vault_adapter_reports_no_backend_or_runtime_capability() -> None:
    adapter = BlockedCredentialVaultAdapter()
    report = adapter.inspect_capabilities()

    assert report.backend_kind == "blocked_no_approved_backend"
    assert report.adapter_available is False
    assert report.supports_write is False
    assert report.supports_read_handle is False
    assert report.supports_revoke is False
    assert report.raw_key_return_supported is False
    assert report.environment_scan_enabled is False
    assert report.shell_keychain_cli_enabled is False


def test_vault_adapter_capability_report_rejects_unsafe_claims() -> None:
    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_UNSAFE_CAPABILITY_DENIED"):
        CredentialVaultAdapterCapabilityReport(raw_key_return_supported=True)

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_BLOCKED_BACKEND_DENIED"):
        CredentialVaultAdapterCapabilityReport(supports_write=True)

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_BLOCKED_BACKEND_DENIED"):
        CredentialVaultAdapterCapabilityReport(adapter_available=True)

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_STATUS_DENIED"):
        CredentialVaultAdapterCapabilityReport(readiness_status="ready")

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_BLOCKER_CODES_REQUIRED"):
        CredentialVaultAdapterCapabilityReport(blocker_codes=[])


def test_blocked_vault_adapter_denies_store_resolve_and_revoke_without_handles() -> None:
    adapter = BlockedCredentialVaultAdapter()
    store = vault_store_request()
    resolve = CredentialVaultResolveRequest(
        credential_ref=store.credential_ref,
        provider_id=store.provider_id,
        consent_ref=store.consent_ref,
        policy_ref=store.policy_ref,
        approval_ref=store.approval_ref,
        revocation_ref=store.revocation_ref,
        audit_ref=store.audit_ref,
        safe_disable_ref=store.safe_disable_ref,
        purpose="provider_lookup",
    )
    revoke = CredentialVaultRevokeRequest(
        credential_ref=store.credential_ref,
        provider_id=store.provider_id,
        consent_ref=store.consent_ref,
        policy_ref=store.policy_ref,
        approval_ref=store.approval_ref,
        revocation_ref=store.revocation_ref,
        audit_ref=store.audit_ref,
        safe_disable_ref=store.safe_disable_ref,
        idempotency_key=store.idempotency_key,
        rollback_ref=store.rollback_ref,
    )

    decisions = [
        adapter.store_credential_ref(store),
        adapter.resolve_credential_handle(resolve),
        adapter.revoke_credential_ref(revoke),
    ]

    for decision in decisions:
        assert decision.allowed is False
        assert decision.handle_ref is None
        assert decision.credential_material_returned is False
        assert decision.credential_material_persisted_by_repo is False
        assert "NO_APPROVED_VAULT_BACKEND" in decision.reason_codes


def test_vault_adapter_decision_rejects_allowed_backend_or_handle_spoofing() -> None:
    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_DECISION_ALLOWED_DENIED"):
        CredentialVaultAdapterDecision(
            decision_id="credential-vault-decision:test",
            action="resolve_credential_handle",
            allowed=True,
            credential_ref="credential-ref:provider:test",
            safe_message="blocked",
        )

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_DECISION_BACKEND_DENIED"):
        CredentialVaultAdapterDecision(
            decision_id="credential-vault-decision:test",
            action="resolve_credential_handle",
            backend_kind="approved_backend",
            credential_ref="credential-ref:provider:test",
            safe_message="blocked",
        )

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_DENIED_HANDLE_REF_DENIED"):
        CredentialVaultAdapterDecision(
            decision_id="credential-vault-decision:test",
            action="resolve_credential_handle",
            credential_ref="credential-ref:provider:test",
            handle_ref="secret-handle-ref:test",
            safe_message="blocked",
        )


def test_vault_store_request_rejects_material_intake_and_secret_like_refs() -> None:
    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_STORE_MATERIAL_INTAKE_DENIED"):
        vault_store_request(credential_material_supplied_to_repo=True)

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_REQUEST_SECRET_LIKE_VALUE_REJECTED") as exc:
        CredentialVaultStoreRequest(
            credential_ref="token=" + ("D" * 16),
            provider_id="provider:test",
            provider_manifest_ref="provider-manifest-ref:provider:test",
            consent_ref="consent-ref:provider:test",
            policy_ref="policy-ref:provider:test",
            approval_ref="approval-ref:provider:test",
            revocation_ref="revocation-ref:provider:test",
            idempotency_key="idempotency-ref:provider:test",
            audit_ref="audit-ref:provider:test",
            rollback_ref="rollback-ref:provider:test",
            safe_disable_ref="safe-disable-ref:provider:test",
        )

    assert "D" * 16 not in str(exc.value)


def test_vault_adapter_readiness_rejects_runtime_storage_visibility_and_secret_refs() -> None:
    for field in [
        "adapter_runtime_enabled",
        "credential_material_stored_by_repo",
        "raw_key_visible",
    ]:
        with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VAULT_AUTHORITY_DENIED"):
            ProviderCredentialVaultAdapterReadiness(**{field: True})

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VAULT_SECRET_LIKE_VALUE_REJECTED") as exc:
        ProviderCredentialVaultAdapterReadiness(credential_ref="token=" + ("A" * 16))

    assert "A" * 16 not in str(exc.value)

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VAULT_STATUS_DENIED"):
        ProviderCredentialVaultAdapterReadiness(readiness_status="ready")

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VAULT_BLOCKER_CODES_REQUIRED"):
        ProviderCredentialVaultAdapterReadiness(blocker_codes=[])

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VAULT_BLOCKED_BACKEND_DENIED"):
        ProviderCredentialVaultAdapterReadiness(adapter_available=True)


def test_provider_credential_enrollment_readiness_is_disabled_and_safe() -> None:
    readiness = ProviderCredentialEnrollmentReadiness()

    assert readiness.enrollment_enabled is False
    assert readiness.raw_key_collection_enabled is False
    assert readiness.credential_material_stored_by_repo is False
    assert readiness.evidence_contains_credential_material is False
    assert readiness.readiness_status == "blocked_disabled_by_default"
    assert "CREDENTIAL_ENROLLMENT_NOT_SCOPED" in readiness.blocker_codes


def test_provider_credential_enrollment_rejects_authority_and_secret_refs() -> None:
    for field in [
        "enrollment_enabled",
        "raw_key_collection_enabled",
        "credential_material_stored_by_repo",
        "evidence_contains_credential_material",
    ]:
        with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_ENROLLMENT_AUTHORITY_DENIED"):
            ProviderCredentialEnrollmentReadiness(**{field: True})

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_ENROLLMENT_SECRET_LIKE_VALUE_REJECTED") as exc:
        ProviderCredentialEnrollmentReadiness(credential_ref="token=" + ("E" * 16))

    assert "E" * 16 not in str(exc.value)

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_ENROLLMENT_STATUS_DENIED"):
        ProviderCredentialEnrollmentReadiness(readiness_status="ready")

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_ENROLLMENT_BLOCKER_CODES_REQUIRED"):
        ProviderCredentialEnrollmentReadiness(blocker_codes=[])


def test_provider_validation_readiness_is_blocked_without_external_calls() -> None:
    readiness = ProviderCredentialValidationReadiness()

    assert readiness.validation_enabled is False
    assert readiness.external_validation_allowed is False
    assert readiness.provider_response_persistence_allowed is False
    assert readiness.readiness_status == "blocked_not_scoped"
    assert "PROVIDER_KEY_VALIDATION_NOT_SCOPED" in readiness.blocker_codes


def test_provider_validation_request_and_receipt_remain_blocked() -> None:
    request = validation_request()
    receipt = ProviderCredentialValidationReceipt(
        receipt_ref=request.validation_receipt_ref,
        provider_manifest_ref=request.provider_manifest_ref,
        credential_ref=request.credential_ref,
        redacted_validation_receipt_ref="redacted-receipt-ref:provider-validation:test",
    )

    assert request.validation_enabled is False
    assert request.external_validation_allowed is False
    assert request.network_validation_allowed is False
    assert request.provider_sdk_allowed is False
    assert receipt.validation_performed is False
    assert receipt.provider_network_called is False
    assert receipt.provider_sdk_used is False
    assert receipt.provider_response_persisted is False


def test_provider_validation_request_and_receipt_reject_runtime_authority() -> None:
    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_REQUEST_AUTHORITY_DENIED"):
        validation_request(network_validation_allowed=True)

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_REQUEST_AUTHORITY_DENIED"):
        validation_request(provider_sdk_allowed=True)

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_AUTHORITY_DENIED"):
        ProviderCredentialValidationReceipt(
            receipt_ref="receipt-ref:provider-validation:test",
            provider_manifest_ref="provider-manifest-ref:provider:test",
            credential_ref="credential-ref:provider:test",
            redacted_validation_receipt_ref="redacted-receipt-ref:provider-validation:test",
            provider_network_called=True,
        )

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_STATUS_DENIED"):
        ProviderCredentialValidationReceipt(
            receipt_ref="receipt-ref:provider-validation:test",
            provider_manifest_ref="provider-manifest-ref:provider:test",
            credential_ref="credential-ref:provider:test",
            redacted_validation_receipt_ref="redacted-receipt-ref:provider-validation:test",
            status="ready",
        )


def test_provider_validation_readiness_rejects_calls_persistence_and_secret_refs() -> None:
    for field in [
        "validation_enabled",
        "external_validation_allowed",
        "provider_response_persistence_allowed",
    ]:
        with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_AUTHORITY_DENIED"):
            ProviderCredentialValidationReadiness(**{field: True})

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_SECRET_LIKE_VALUE_REJECTED") as exc:
        ProviderCredentialValidationReadiness(credential_ref="api_key=" + ("B" * 16))

    assert "B" * 16 not in str(exc.value)

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_STATUS_DENIED"):
        ProviderCredentialValidationReadiness(readiness_status="ready")

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_BLOCKER_CODES_REQUIRED"):
        ProviderCredentialValidationReadiness(blocker_codes=[])


def test_governed_provider_invocation_readiness_requires_future_exact_gates() -> None:
    readiness = GovernedProviderInvocationReadiness()

    assert readiness.invocation_enabled is False
    assert readiness.policy_engine_required is True
    assert readiness.local_approval_required is True
    assert readiness.credential_ref_required is True
    assert readiness.provider_manifest_allowlist_required is True
    assert readiness.redacted_request_summary_only is True
    assert readiness.redacted_response_summary_only is True
    assert readiness.model_output_authoritative is False
    assert "PROVIDER_INVOCATION_NOT_SCOPED" in readiness.blocker_codes


def test_governed_provider_invocation_readiness_rejects_invocation_or_expansion_flags() -> None:
    denied_flags = [
        "invocation_enabled",
        "model_output_authoritative",
        "streaming_enabled",
        "tools_functions_enabled",
        "memory_write_enabled",
        "context_injection_enabled",
        "browser_network_automation_enabled",
        "connector_writes_enabled",
    ]

    for field in denied_flags:
        with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_AUTHORITY_DENIED"):
            GovernedProviderInvocationReadiness(**{field: True})

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_SECRET_LIKE_VALUE_REJECTED") as exc:
        GovernedProviderInvocationReadiness(safe_summary="private_key=" + ("C" * 16))

    assert "C" * 16 not in str(exc.value)

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_STATUS_DENIED"):
        GovernedProviderInvocationReadiness(readiness_status="ready")

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_REQUIRED_GATE_DENIED"):
        GovernedProviderInvocationReadiness(policy_engine_required=False)

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_BLOCKER_CODES_REQUIRED"):
        GovernedProviderInvocationReadiness(blocker_codes=[])


def test_governed_provider_invocation_request_and_receipt_remain_blocked() -> None:
    request = invocation_request()
    receipt = GovernedProviderInvocationReceipt(
        receipt_ref=request.receipt_ref,
        policy_decision_ref=request.policy_decision_ref,
        approval_ref=request.approval_ref,
        provider_manifest_allowlist_ref=request.provider_manifest_allowlist_ref,
        credential_ref=request.credential_ref,
        audit_ref=request.audit_ref,
        redacted_request_summary_ref=request.redacted_request_summary_ref,
        redacted_response_summary_ref=request.redacted_response_summary_ref,
        rollback_or_safe_disable_ref=request.rollback_or_safe_disable_ref,
    )

    assert request.invocation_enabled is False
    assert request.provider_model_call_allowed is False
    assert request.streaming_enabled is False
    assert request.tools_functions_enabled is False
    assert request.memory_write_enabled is False
    assert request.context_injection_enabled is False
    assert request.model_output_authoritative is False
    assert receipt.invocation_performed is False
    assert receipt.provider_model_called is False
    assert receipt.provider_payload_persisted is False
    assert receipt.prompt_content_persisted is False
    assert receipt.response_content_persisted is False
    assert receipt.model_output_authoritative is False


def test_governed_provider_invocation_request_and_receipt_reject_runtime_authority() -> None:
    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_REQUEST_AUTHORITY_DENIED"):
        invocation_request(provider_model_call_allowed=True)

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_REQUEST_AUTHORITY_DENIED"):
        invocation_request(context_injection_enabled=True)

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_RECEIPT_AUTHORITY_DENIED"):
        GovernedProviderInvocationReceipt(
            receipt_ref="receipt-ref:provider:test",
            policy_decision_ref="policy-decision-ref:provider:test",
            approval_ref="approval-ref:provider:test",
            provider_manifest_allowlist_ref="provider-allowlist-ref:provider:test",
            credential_ref="credential-ref:provider:test",
            audit_ref="audit-ref:provider:test",
            redacted_request_summary_ref="request-summary-ref:provider:test",
            redacted_response_summary_ref="response-summary-ref:provider:test",
            rollback_or_safe_disable_ref="safe-disable-ref:provider:test",
            invocation_performed=True,
        )

    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_RECEIPT_STATUS_DENIED"):
        GovernedProviderInvocationReceipt(
            receipt_ref="receipt-ref:provider:test",
            policy_decision_ref="policy-decision-ref:provider:test",
            approval_ref="approval-ref:provider:test",
            provider_manifest_allowlist_ref="provider-allowlist-ref:provider:test",
            credential_ref="credential-ref:provider:test",
            audit_ref="audit-ref:provider:test",
            redacted_request_summary_ref="request-summary-ref:provider:test",
            redacted_response_summary_ref="response-summary-ref:provider:test",
            rollback_or_safe_disable_ref="safe-disable-ref:provider:test",
            status="ready",
        )


def test_provider_runtime_contracts_revalidate_model_copy_updates() -> None:
    with pytest.raises(ValidationError, match="GOVERNED_PROVIDER_INVOCATION_AUTHORITY_DENIED"):
        GovernedProviderInvocationReadiness().model_copy(update={"invocation_enabled": True})

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_VALIDATION_REQUEST_AUTHORITY_DENIED"):
        validation_request().model_copy(update={"external_validation_allowed": True})

    with pytest.raises(ValidationError, match="PROVIDER_CREDENTIAL_ENROLLMENT_AUTHORITY_DENIED"):
        ProviderCredentialEnrollmentReadiness().model_copy(update={"enrollment_enabled": True})

    with pytest.raises(ValidationError, match="CREDENTIAL_VAULT_ADAPTER_DECISION_ALLOWED_DENIED"):
        CredentialVaultAdapterDecision(
            decision_id="credential-vault-decision:test",
            action="resolve_credential_handle",
            credential_ref="credential-ref:provider:test",
            safe_message="blocked",
        ).model_copy(update={"allowed": True})
