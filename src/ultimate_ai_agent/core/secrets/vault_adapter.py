from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


class _VaultAdapterContract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update=None, deep: bool = False):
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _require_codes(actual: list[str], required: set[str], error_code: str) -> None:
    if not required.issubset(set(actual)):
        raise ValueError(error_code)


class CredentialVaultAdapterCapabilityReport(_VaultAdapterContract):
    backend_kind: str = "blocked_no_approved_backend"
    adapter_available: bool = False
    supports_write: bool = False
    supports_read_handle: bool = False
    supports_revoke: bool = False
    credential_material_stored_by_repo: bool = False
    raw_key_visible: bool = False
    raw_key_return_supported: bool = False
    environment_scan_enabled: bool = False
    shell_keychain_cli_enabled: bool = False
    readiness_status: str = "blocked_no_approved_backend"
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "NO_APPROVED_VAULT_BACKEND",
            "CREDENTIAL_WRITE_NOT_SCOPED",
            "CREDENTIAL_READ_HANDLE_NOT_SCOPED",
            "CREDENTIAL_REVOCATION_NOT_SCOPED",
        ]
    )
    safe_summary: str = (
        "No approved vault or keychain backend is configured; credential material "
        "cannot be stored, read, returned, or inspected by the repo."
    )

    @model_validator(mode="after")
    def capability_report_must_not_claim_unsafe_authority(self):
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "CREDENTIAL_VAULT_ADAPTER_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.credential_material_stored_by_repo
            or self.raw_key_visible
            or self.raw_key_return_supported
            or self.environment_scan_enabled
            or self.shell_keychain_cli_enabled
        ):
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_UNSAFE_CAPABILITY_DENIED")
        if (
            self.adapter_available
            or self.supports_write
            or self.supports_read_handle
            or self.supports_revoke
        ):
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_BLOCKED_BACKEND_DENIED")
        if self.readiness_status != "blocked_no_approved_backend":
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_STATUS_DENIED")
        _require_codes(
            self.blocker_codes,
            {
                "NO_APPROVED_VAULT_BACKEND",
                "CREDENTIAL_WRITE_NOT_SCOPED",
                "CREDENTIAL_READ_HANDLE_NOT_SCOPED",
                "CREDENTIAL_REVOCATION_NOT_SCOPED",
            },
            "CREDENTIAL_VAULT_ADAPTER_BLOCKER_CODES_REQUIRED",
        )
        return self


class CredentialVaultAdapterRequestBase(_VaultAdapterContract):
    credential_ref: str = Field(..., min_length=1)
    provider_id: str = Field(..., min_length=1)
    consent_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def request_must_use_safe_refs(self):
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "CREDENTIAL_VAULT_ADAPTER_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        return self


class CredentialVaultStoreRequest(CredentialVaultAdapterRequestBase):
    provider_manifest_ref: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    credential_material_supplied_to_repo: bool = False

    @model_validator(mode="after")
    def store_request_must_not_include_material(self):
        if self.credential_material_supplied_to_repo:
            raise ValueError("CREDENTIAL_VAULT_STORE_MATERIAL_INTAKE_DENIED")
        return self


class CredentialVaultResolveRequest(CredentialVaultAdapterRequestBase):
    purpose: str = Field(..., min_length=1)


class CredentialVaultRevokeRequest(CredentialVaultAdapterRequestBase):
    idempotency_key: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)


class CredentialVaultAdapterDecision(_VaultAdapterContract):
    decision_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    allowed: bool = False
    backend_kind: str = "blocked_no_approved_backend"
    credential_ref: str = Field(..., min_length=1)
    handle_ref: str | None = None
    revocation_ref: str | None = None
    audit_ref: str | None = None
    receipt_ref: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    credential_material_returned: bool = False
    credential_material_persisted_by_repo: bool = False

    @model_validator(mode="after")
    def decision_must_remain_redacted(self):
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "CREDENTIAL_VAULT_ADAPTER_DECISION_SECRET_LIKE_VALUE_REJECTED",
        )
        if self.credential_material_returned or self.credential_material_persisted_by_repo:
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_DECISION_MATERIAL_DENIED")
        if self.allowed:
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_DECISION_ALLOWED_DENIED")
        if self.backend_kind != "blocked_no_approved_backend":
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_DECISION_BACKEND_DENIED")
        if not self.allowed and self.handle_ref:
            raise ValueError("CREDENTIAL_VAULT_ADAPTER_DENIED_HANDLE_REF_DENIED")
        return self


class ProviderCredentialEnrollmentReadiness(_VaultAdapterContract):
    provider_manifest_ref: str = "provider-manifest-ref:provider-runtime:required"
    credential_ref: str = "credential-ref:provider-runtime:not-bound"
    consent_ref: str = "consent-ref:provider-runtime:not-granted"
    policy_ref: str = "policy-ref:provider-runtime:disabled-by-default"
    approval_ref: str = "approval-ref:provider-runtime:not-granted"
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    idempotency_key_ref: str = "idempotency-ref:provider-enrollment:not-issued"
    audit_ref: str = "audit-ref:provider-enrollment:not-created"
    rollback_ref: str = "rollback-ref:provider-enrollment:not-created"
    safe_disable_ref: str = "safe-disable-ref:provider-enrollment:not-created"
    enrollment_enabled: bool = False
    raw_key_collection_enabled: bool = False
    credential_material_stored_by_repo: bool = False
    evidence_contains_credential_material: bool = False
    readiness_status: str = "blocked_disabled_by_default"
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "CREDENTIAL_ENROLLMENT_NOT_SCOPED",
            "TRANSIENT_SECRET_INTAKE_NOT_APPROVED",
            "APPROVED_VAULT_BACKEND_REQUIRED",
        ]
    )
    safe_summary: str = (
        "Credential enrollment is disabled; any future enrollment must use exact refs, "
        "approval, idempotency, audit, rollback, safe-disable, and an approved vault backend."
    )

    @model_validator(mode="after")
    def enrollment_readiness_must_remain_disabled(self):
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_ENROLLMENT_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.enrollment_enabled
            or self.raw_key_collection_enabled
            or self.credential_material_stored_by_repo
            or self.evidence_contains_credential_material
        ):
            raise ValueError("PROVIDER_CREDENTIAL_ENROLLMENT_AUTHORITY_DENIED")
        if self.readiness_status != "blocked_disabled_by_default":
            raise ValueError("PROVIDER_CREDENTIAL_ENROLLMENT_STATUS_DENIED")
        _require_codes(
            self.blocker_codes,
            {
                "CREDENTIAL_ENROLLMENT_NOT_SCOPED",
                "TRANSIENT_SECRET_INTAKE_NOT_APPROVED",
                "APPROVED_VAULT_BACKEND_REQUIRED",
            },
            "PROVIDER_CREDENTIAL_ENROLLMENT_BLOCKER_CODES_REQUIRED",
        )
        return self


class CredentialVaultAdapter(Protocol):
    @property
    def backend_kind(self) -> str: ...

    def inspect_capabilities(self) -> CredentialVaultAdapterCapabilityReport: ...

    def store_credential_ref(self, request: CredentialVaultStoreRequest) -> CredentialVaultAdapterDecision: ...

    def resolve_credential_handle(self, request: CredentialVaultResolveRequest) -> CredentialVaultAdapterDecision: ...

    def revoke_credential_ref(self, request: CredentialVaultRevokeRequest) -> CredentialVaultAdapterDecision: ...


class BlockedCredentialVaultAdapter:
    backend_kind = "blocked_no_approved_backend"

    def inspect_capabilities(self) -> CredentialVaultAdapterCapabilityReport:
        return CredentialVaultAdapterCapabilityReport(backend_kind=self.backend_kind)

    def store_credential_ref(self, request: CredentialVaultStoreRequest) -> CredentialVaultAdapterDecision:
        return self._blocked_decision(
            action="store_credential_ref",
            credential_ref=request.credential_ref,
            audit_ref=request.audit_ref,
            reason_codes=[
                "NO_APPROVED_VAULT_BACKEND",
                "CREDENTIAL_WRITE_NOT_SCOPED",
            ],
        )

    def resolve_credential_handle(self, request: CredentialVaultResolveRequest) -> CredentialVaultAdapterDecision:
        return self._blocked_decision(
            action="resolve_credential_handle",
            credential_ref=request.credential_ref,
            audit_ref=request.audit_ref,
            reason_codes=[
                "NO_APPROVED_VAULT_BACKEND",
                "CREDENTIAL_READ_HANDLE_NOT_SCOPED",
            ],
        )

    def revoke_credential_ref(self, request: CredentialVaultRevokeRequest) -> CredentialVaultAdapterDecision:
        return self._blocked_decision(
            action="revoke_credential_ref",
            credential_ref=request.credential_ref,
            audit_ref=request.audit_ref,
            revocation_ref=request.revocation_ref,
            reason_codes=[
                "NO_APPROVED_VAULT_BACKEND",
                "CREDENTIAL_REVOCATION_NOT_SCOPED",
            ],
        )

    def _blocked_decision(
        self,
        *,
        action: str,
        credential_ref: str,
        audit_ref: str,
        reason_codes: list[str],
        revocation_ref: str | None = None,
    ) -> CredentialVaultAdapterDecision:
        return CredentialVaultAdapterDecision(
            decision_id=f"credential-vault-decision:{action}:blocked",
            action=action,
            allowed=False,
            backend_kind=self.backend_kind,
            credential_ref=credential_ref,
            revocation_ref=revocation_ref,
            audit_ref=audit_ref,
            reason_codes=reason_codes,
            safe_message="Credential vault operation is blocked until an approved backend is scoped.",
        )
