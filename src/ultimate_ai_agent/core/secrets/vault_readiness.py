from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


class ProviderCredentialVaultAdapterReadiness(BaseModel):
    credential_ref: str = "credential-ref:provider-runtime:not-bound"
    provider_id: str = "provider:reference-only"
    consent_ref: str = "consent-ref:provider-runtime:not-granted"
    policy_ref: str = "policy-ref:provider-runtime:disabled-by-default"
    approval_ref: str = "approval-ref:provider-runtime:not-granted"
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    storage_backend_kind: str = "vault_adapter_contract_not_configured"
    credential_material_stored_by_repo: bool = False
    raw_key_visible: bool = False
    adapter_runtime_enabled: bool = False
    last_validation_ref: str = "validation-ref:provider-runtime:not-run"
    readiness_status: str = "blocked_contract_only"
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "VAULT_ADAPTER_NOT_SCOPED",
            "CREDENTIAL_MATERIAL_STORAGE_DENIED",
            "RAW_KEY_VISIBILITY_DENIED",
        ]
    )
    safe_summary: str = (
        "Vault adapter readiness is contract-only; the repo does not collect, store, "
        "or reveal provider credential material."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def vault_adapter_readiness_must_remain_disabled(self):
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SECRET_LIKE_VALUE_REJECTED")
        if self.credential_material_stored_by_repo or self.raw_key_visible or self.adapter_runtime_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_AUTHORITY_DENIED")
        return self
