import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.providers import (
    GovernedProviderInvocationReadiness,
    ProviderCredentialValidationReadiness,
)
from ultimate_ai_agent.core.secrets import ProviderCredentialVaultAdapterReadiness


def test_vault_adapter_readiness_is_disabled_and_safe_by_default():
    readiness = ProviderCredentialVaultAdapterReadiness()
    serialized = readiness.model_dump_json()

    assert readiness.adapter_runtime_enabled is False
    assert readiness.credential_material_stored_by_repo is False
    assert readiness.raw_key_visible is False
    assert readiness.readiness_status == "blocked_contract_only"
    assert "VAULT_ADAPTER_NOT_SCOPED" in readiness.blocker_codes
    assert "api_key" not in serialized.lower()
    assert "token=" not in serialized.lower()


def test_vault_adapter_readiness_rejects_runtime_storage_visibility_and_secret_refs():
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


def test_provider_validation_readiness_is_blocked_without_external_calls():
    readiness = ProviderCredentialValidationReadiness()

    assert readiness.validation_enabled is False
    assert readiness.external_validation_allowed is False
    assert readiness.provider_response_persistence_allowed is False
    assert readiness.readiness_status == "blocked_not_scoped"
    assert "PROVIDER_KEY_VALIDATION_NOT_SCOPED" in readiness.blocker_codes


def test_provider_validation_readiness_rejects_calls_persistence_and_secret_refs():
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


def test_governed_provider_invocation_readiness_requires_future_exact_gates():
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


def test_governed_provider_invocation_readiness_rejects_invocation_or_expansion_flags():
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
