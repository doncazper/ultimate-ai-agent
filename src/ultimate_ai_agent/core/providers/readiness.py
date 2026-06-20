from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


class ProviderCredentialValidationReadiness(BaseModel):
    provider_manifest_ref: str = "provider-manifest-ref:provider-runtime:required"
    credential_ref: str = "credential-ref:provider-runtime:not-bound"
    consent_ref: str = "consent-ref:provider-runtime:not-granted"
    policy_ref: str = "policy-ref:provider-runtime:disabled-by-default"
    approval_ref: str = "approval-ref:provider-runtime:not-granted"
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    validation_enabled: bool = False
    external_validation_allowed: bool = False
    provider_response_persistence_allowed: bool = False
    validation_receipt_ref: str = "receipt-ref:provider-validation:not-created"
    readiness_status: str = "blocked_not_scoped"
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "PROVIDER_KEY_VALIDATION_NOT_SCOPED",
            "PROVIDER_NETWORK_CALL_NOT_SCOPED",
            "REDACTED_VALIDATION_RECEIPT_REQUIRED",
        ]
    )
    safe_summary: str = (
        "Provider key validation is not scoped; any future validation must use safe refs, "
        "explicit consent, policy, approval, revocation, and redacted receipts."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validation_readiness_must_remain_disabled(self):
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_SECRET_LIKE_VALUE_REJECTED")
        if (
            self.validation_enabled
            or self.external_validation_allowed
            or self.provider_response_persistence_allowed
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_AUTHORITY_DENIED")
        return self


class GovernedProviderInvocationReadiness(BaseModel):
    readiness_status: str = "blocked_not_scoped"
    invocation_enabled: bool = False
    policy_engine_required: bool = True
    local_approval_required: bool = True
    credential_ref_required: bool = True
    provider_manifest_allowlist_required: bool = True
    redacted_request_summary_only: bool = True
    redacted_response_summary_only: bool = True
    receipt_refs_required: bool = True
    audit_refs_required: bool = True
    rollback_or_safe_disable_required: bool = True
    rate_budget_boundary_required: bool = True
    model_output_authoritative: bool = False
    streaming_enabled: bool = False
    tools_functions_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    browser_network_automation_enabled: bool = False
    connector_writes_enabled: bool = False
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "PROVIDER_INVOCATION_NOT_SCOPED",
            "POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED",
            "PROVIDER_OUTPUT_NOT_AUTHORITY",
        ]
    )
    safe_summary: str = (
        "Governed provider invocation remains disabled; any future invocation requires "
        "policy, approval, provider auth references, provider allowlists, redacted summaries, "
        "receipts, audit refs, safe-disable behavior, and rate or budget boundaries."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def invocation_readiness_must_remain_disabled(self):
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_SECRET_LIKE_VALUE_REJECTED")
        denied_flags = [
            self.invocation_enabled,
            self.model_output_authoritative,
            self.streaming_enabled,
            self.tools_functions_enabled,
            self.memory_write_enabled,
            self.context_injection_enabled,
            self.browser_network_automation_enabled,
            self.connector_writes_enabled,
        ]
        if any(denied_flags):
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_AUTHORITY_DENIED")
        return self
