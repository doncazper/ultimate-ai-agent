from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


class _ProviderRuntimeContract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _require_codes(actual: list[str], required: set[str], error_code: str) -> None:
    if not required.issubset(set(actual)):
        raise ValueError(error_code)


class ProviderCredentialValidationReadiness(_ProviderRuntimeContract):
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
        "Provider credential-reference validation is not scoped; any future validation must use safe refs, "
        "explicit consent, policy, approval, revocation, and redacted receipts."
    )

    @model_validator(mode="after")
    def validation_readiness_must_remain_disabled(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.validation_enabled
            or self.external_validation_allowed
            or self.provider_response_persistence_allowed
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_AUTHORITY_DENIED")
        if self.readiness_status != "blocked_not_scoped":
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_STATUS_DENIED")
        _require_codes(
            self.blocker_codes,
            {
                "PROVIDER_KEY_VALIDATION_NOT_SCOPED",
                "PROVIDER_NETWORK_CALL_NOT_SCOPED",
                "REDACTED_VALIDATION_RECEIPT_REQUIRED",
            },
            "PROVIDER_CREDENTIAL_VALIDATION_BLOCKER_CODES_REQUIRED",
        )
        return self


class ProviderCredentialValidationRequest(_ProviderRuntimeContract):
    provider_manifest_ref: str = Field(..., min_length=1)
    provider_allowlist_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    consent_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    validation_receipt_ref: str = Field(..., min_length=1)
    rate_budget_ref: str = Field(..., min_length=1)
    validation_enabled: bool = False
    external_validation_allowed: bool = False
    network_validation_allowed: bool = False
    provider_sdk_allowed: bool = False

    @model_validator(mode="after")
    def validation_request_must_remain_blocked(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.validation_enabled
            or self.external_validation_allowed
            or self.network_validation_allowed
            or self.provider_sdk_allowed
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_REQUEST_AUTHORITY_DENIED")
        return self


class ProviderCredentialValidationReceipt(_ProviderRuntimeContract):
    receipt_ref: str = Field(..., min_length=1)
    provider_manifest_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    status: str = "blocked_not_scoped"
    validation_performed: bool = False
    provider_network_called: bool = False
    provider_sdk_used: bool = False
    provider_response_persisted: bool = False
    redacted_validation_receipt_ref: str = Field(..., min_length=1)
    safe_error_summary: str = "Provider credential validation is blocked until a scoped runtime milestone."
    reason_codes: list[str] = Field(
        default_factory=lambda: [
            "PROVIDER_KEY_VALIDATION_NOT_SCOPED",
            "PROVIDER_NETWORK_CALL_NOT_SCOPED",
        ]
    )

    @model_validator(mode="after")
    def validation_receipt_must_remain_blocked(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.validation_performed
            or self.provider_network_called
            or self.provider_sdk_used
            or self.provider_response_persisted
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_AUTHORITY_DENIED")
        if self.status != "blocked_not_scoped":
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_STATUS_DENIED")
        _require_codes(
            self.reason_codes,
            {
                "PROVIDER_KEY_VALIDATION_NOT_SCOPED",
                "PROVIDER_NETWORK_CALL_NOT_SCOPED",
            },
            "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_REASON_CODES_REQUIRED",
        )
        return self


class GovernedProviderInvocationReadiness(_ProviderRuntimeContract):
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

    @model_validator(mode="after")
    def invocation_readiness_must_remain_disabled(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "GOVERNED_PROVIDER_INVOCATION_SECRET_LIKE_VALUE_REJECTED",
        )
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
        if self.readiness_status != "blocked_not_scoped":
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_STATUS_DENIED")
        required_gates = [
            self.policy_engine_required,
            self.local_approval_required,
            self.credential_ref_required,
            self.provider_manifest_allowlist_required,
            self.redacted_request_summary_only,
            self.redacted_response_summary_only,
            self.receipt_refs_required,
            self.audit_refs_required,
            self.rollback_or_safe_disable_required,
            self.rate_budget_boundary_required,
        ]
        if not all(required_gates):
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_REQUIRED_GATE_DENIED")
        _require_codes(
            self.blocker_codes,
            {
                "PROVIDER_INVOCATION_NOT_SCOPED",
                "POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED",
                "PROVIDER_OUTPUT_NOT_AUTHORITY",
            },
            "GOVERNED_PROVIDER_INVOCATION_BLOCKER_CODES_REQUIRED",
        )
        return self


class GovernedProviderInvocationRequest(_ProviderRuntimeContract):
    policy_decision_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    provider_manifest_allowlist_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    consent_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    redacted_request_summary_ref: str = Field(..., min_length=1)
    redacted_response_summary_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    rollback_or_safe_disable_ref: str = Field(..., min_length=1)
    rate_budget_ref: str = Field(..., min_length=1)
    invocation_enabled: bool = False
    provider_model_call_allowed: bool = False
    streaming_enabled: bool = False
    tools_functions_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    connector_writes_enabled: bool = False
    browser_network_automation_enabled: bool = False
    model_output_authoritative: bool = False

    @model_validator(mode="after")
    def invocation_request_must_remain_blocked(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "GOVERNED_PROVIDER_INVOCATION_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        denied_flags = [
            self.invocation_enabled,
            self.provider_model_call_allowed,
            self.streaming_enabled,
            self.tools_functions_enabled,
            self.memory_write_enabled,
            self.context_injection_enabled,
            self.connector_writes_enabled,
            self.browser_network_automation_enabled,
            self.model_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_REQUEST_AUTHORITY_DENIED")
        return self


class GovernedProviderInvocationReceipt(_ProviderRuntimeContract):
    receipt_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    provider_manifest_allowlist_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    status: str = "blocked_not_scoped"
    invocation_performed: bool = False
    provider_model_called: bool = False
    provider_payload_persisted: bool = False
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    model_output_authoritative: bool = False
    redacted_request_summary_ref: str = Field(..., min_length=1)
    redacted_response_summary_ref: str = Field(..., min_length=1)
    rollback_or_safe_disable_ref: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(
        default_factory=lambda: [
            "PROVIDER_INVOCATION_NOT_SCOPED",
            "POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED",
            "PROVIDER_OUTPUT_NOT_AUTHORITY",
        ]
    )
    safe_error_summary: str = "Provider invocation is blocked until a scoped runtime milestone."

    @model_validator(mode="after")
    def invocation_receipt_must_remain_blocked(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "GOVERNED_PROVIDER_INVOCATION_RECEIPT_SECRET_LIKE_VALUE_REJECTED",
        )
        denied_flags = [
            self.invocation_performed,
            self.provider_model_called,
            self.provider_payload_persisted,
            self.prompt_content_persisted,
            self.response_content_persisted,
            self.model_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_RECEIPT_AUTHORITY_DENIED")
        if self.status != "blocked_not_scoped":
            raise ValueError("GOVERNED_PROVIDER_INVOCATION_RECEIPT_STATUS_DENIED")
        _require_codes(
            self.reason_codes,
            {
                "PROVIDER_INVOCATION_NOT_SCOPED",
                "POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED",
                "PROVIDER_OUTPUT_NOT_AUTHORITY",
            },
            "GOVERNED_PROVIDER_INVOCATION_RECEIPT_REASON_CODES_REQUIRED",
        )
        return self
