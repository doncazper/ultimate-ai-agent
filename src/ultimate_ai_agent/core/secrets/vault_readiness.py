from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.secrets.vault_adapter import CredentialVaultAdapterCapabilityReport


class _VaultReadinessContract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update=None, deep: bool = False):
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class ProviderCredentialVaultAdapterReadiness(_VaultReadinessContract):
    credential_ref: str = "credential-ref:provider-runtime:not-bound"
    provider_id: str = "provider:reference-only"
    consent_ref: str = "consent-ref:provider-runtime:not-granted"
    policy_ref: str = "policy-ref:provider-runtime:disabled-by-default"
    approval_ref: str = "approval-ref:provider-runtime:not-granted"
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    storage_backend_kind: str = "vault_adapter_contract_not_configured"
    adapter_available: bool = False
    supports_write: bool = False
    supports_read_handle: bool = False
    supports_revoke: bool = False
    credential_material_stored_by_repo: bool = False
    raw_key_visible: bool = False
    adapter_runtime_enabled: bool = False
    last_validation_ref: str = "validation-ref:provider-runtime:not-run"
    readiness_status: str = "blocked_no_approved_backend"
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "NO_APPROVED_VAULT_BACKEND",
            "VAULT_ADAPTER_NOT_SCOPED",
            "CREDENTIAL_WRITE_NOT_SCOPED",
            "CREDENTIAL_READ_HANDLE_NOT_SCOPED",
            "CREDENTIAL_REVOCATION_NOT_SCOPED",
            "CREDENTIAL_MATERIAL_STORAGE_DENIED",
            "RAW_KEY_VISIBILITY_DENIED",
        ]
    )
    safe_summary: str = (
        "Vault adapter readiness is contract-only; the repo does not collect, store, "
        "or reveal provider credential material."
    )

    @model_validator(mode="after")
    def vault_adapter_readiness_must_remain_disabled(self):
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SECRET_LIKE_VALUE_REJECTED")
        if (
            self.credential_material_stored_by_repo
            or self.raw_key_visible
            or self.adapter_runtime_enabled
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_AUTHORITY_DENIED")
        if self.adapter_available or self.supports_write or self.supports_read_handle or self.supports_revoke:
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_BLOCKED_BACKEND_DENIED")
        if self.readiness_status != "blocked_no_approved_backend":
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_STATUS_DENIED")
        required_codes = {
            "NO_APPROVED_VAULT_BACKEND",
            "CREDENTIAL_WRITE_NOT_SCOPED",
            "CREDENTIAL_READ_HANDLE_NOT_SCOPED",
            "CREDENTIAL_REVOCATION_NOT_SCOPED",
        }
        if not required_codes.issubset(set(self.blocker_codes)):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_BLOCKER_CODES_REQUIRED")
        return self


def build_provider_credential_vault_adapter_readiness(
    capabilities: CredentialVaultAdapterCapabilityReport | None = None,
) -> ProviderCredentialVaultAdapterReadiness:
    report = capabilities or CredentialVaultAdapterCapabilityReport()
    return ProviderCredentialVaultAdapterReadiness(
        storage_backend_kind=report.backend_kind,
        adapter_available=report.adapter_available,
        supports_write=report.supports_write,
        supports_read_handle=report.supports_read_handle,
        supports_revoke=report.supports_revoke,
        credential_material_stored_by_repo=report.credential_material_stored_by_repo,
        raw_key_visible=report.raw_key_visible,
        adapter_runtime_enabled=False,
        readiness_status=report.readiness_status,
        blocker_codes=report.blocker_codes,
        safe_summary=report.safe_summary,
    )
