from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


class ProviderCredentialVaultPosture(str, Enum):
    vault_not_configured = "vault_not_configured"
    vault_blocked = "vault_blocked"
    secret_ref_available = "secret_ref_available"
    secret_ref_revoked = "secret_ref_revoked"
    rotation_required = "rotation_required"
    validation_required_but_blocked = "validation_required_but_blocked"
    invocation_requires_approval = "invocation_requires_approval"


class _CredentialVaultContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


_REQUIRED_BLOCKER_CODES = {
    "CREDENTIAL_VAULT_METADATA_ONLY",
    "RAW_SECRET_MATERIAL_DENIED",
    "PROVIDER_VALIDATION_BLOCKED",
    "PROVIDER_INVOCATION_APPROVAL_REQUIRED",
    "PROVIDER_SDK_CALL_BLOCKED",
    "MODEL_INVOCATION_BLOCKED",
}
_AUTHORITY_DENIED_FIELDS = (
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
)
_REF_FIELDS = (
    "record_ref",
    "provider_ref",
    "model_ref",
    "credential_ref",
    "secret_ref",
    "policy_ref",
    "approval_scope_ref",
    "budget_decision_ref",
    "expected_receipt_ref",
    "revocation_ref",
)
_SAFE_REF_RE = re.compile(r"^[a-z][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)+$")
_PRIVATE_TEXT_MARKERS = (
    "raw_prompt",
    "raw prompt",
    "raw_response",
    "raw response",
    "provider_payload",
    "provider payload",
    "provider exchange",
    "username=",
    "user:",
    "hostname=",
    "host:",
    "env dump",
    "environment dump",
    ".env",
    ".log",
    "bearer ",
)
_PROVIDER_TOKEN_PREFIXES = (
    "sk-",
    "sk_",
    "rk-",
    "xoxb-",
    "xoxp-",
    "xoxa-",
    "xoxr-",
    "ghp-",
    "ghp_",
    "github-pat-",
    "github_pat_",
    "hf-",
    "hf_",
    "token-",
)
_AWS_TOKEN_RE = re.compile(r"(?i)(^|:)(akia|asia)[a-z0-9]{12,}")


def _ref_is_unbound(ref: str) -> bool:
    if not ref.strip():
        return True
    lowered = ref.lower()
    return any(
        marker in lowered
        for marker in (
            ":missing",
            "not-bound",
            "not-selected",
            "not-configured",
            "not-created",
            "not-granted",
            "not-active",
            "required",
        )
    )


def _ref_is_revoked(ref: str) -> bool:
    return "revoked" in ref.lower()


def _looks_like_path_or_private_text(value: str) -> bool:
    lowered = value.lower()
    if "/" in value or "\\" in value or lowered.startswith("~"):
        return True
    if _AWS_TOKEN_RE.search(value):
        return True
    normalized_segments = lowered.replace("_", "-").split(":")
    if any(
        segment.startswith(prefix.replace("_", "-"))
        for segment in normalized_segments
        for prefix in _PROVIDER_TOKEN_PREFIXES
    ):
        return True
    return any(marker in lowered for marker in _PRIVATE_TEXT_MARKERS)


def _scan_for_private_text(payload: object) -> bool:
    if isinstance(payload, str):
        return _looks_like_path_or_private_text(payload)
    if isinstance(payload, dict):
        return any(
            _scan_for_private_text(str(key)) or _scan_for_private_text(value)
            for key, value in payload.items()
        )
    if isinstance(payload, list):
        return any(_scan_for_private_text(value) for value in payload)
    return False


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if (
        contains_secret_like(payload)
        or contains_obvious_secret(payload)
        or _scan_for_private_text(payload)
    ):
        raise ValueError(error_code)


def _require_safe_ref(value: str, field_name: str) -> None:
    if (
        not value.strip()
        or not _SAFE_REF_RE.fullmatch(value)
        or _looks_like_path_or_private_text(value)
    ):
        raise ValueError(f"PROVIDER_CREDENTIAL_VAULT_{field_name.upper()}_SAFE_REF_REQUIRED")


class ProviderCredentialVaultRecord(_CredentialVaultContractModel):
    record_ref: str = "credential-vault-record-ref:provider-runtime:not-configured"
    posture: ProviderCredentialVaultPosture = ProviderCredentialVaultPosture.vault_not_configured
    provider_ref: str = "provider-ref:provider-runtime:not-bound"
    model_ref: str = "model-ref:provider-runtime:not-bound"
    credential_ref: str = "credential-ref:provider-runtime:not-bound"
    secret_ref: str = "secret-ref:provider-runtime:not-configured"
    policy_ref: str = "policy-ref:provider-runtime:disabled-by-default"
    approval_scope_ref: str = "approval-scope-ref:provider-runtime:not-granted"
    budget_decision_ref: str = "budget-decision-ref:provider-runtime:required"
    expected_receipt_ref: str = "receipt-ref:provider-runtime:future-required"
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    metadata_only: bool = True
    safe_refs_only: bool = True
    vault_record_grants_authority: bool = False
    secret_collection_enabled: bool = False
    raw_secret_material_available: bool = False
    secret_material_persisted_by_repo: bool = False
    os_credential_backend_access_enabled: bool = False
    credential_validation_call_enabled: bool = False
    validation_authority_granted: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    invocation_authority_granted: bool = False
    invocation_requires_approval: bool = True
    exact_scope_required: bool = True
    budget_decision_required: bool = True
    expected_receipt_required: bool = True
    revocation_ref_required: bool = True
    blocker_codes: list[str] = Field(default_factory=lambda: sorted(_REQUIRED_BLOCKER_CODES))
    safe_summary: str = (
        "Provider credential vault record is metadata only; it stores safe refs "
        "for future scoped review and grants no validation or invocation authority."
    )

    @model_validator(mode="after")
    def vault_record_must_remain_metadata_only(self) -> Any:
        payload = self.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "PROVIDER_CREDENTIAL_VAULT_RECORD_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        for field_name in _REF_FIELDS:
            _require_safe_ref(getattr(self, field_name), field_name)
        if not self.metadata_only or not self.safe_refs_only:
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_METADATA_ONLY_REQUIRED")
        if any(getattr(self, field_name) for field_name in _AUTHORITY_DENIED_FIELDS):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_AUTHORITY_DENIED")
        required_flags = [
            self.invocation_requires_approval,
            self.exact_scope_required,
            self.budget_decision_required,
            self.expected_receipt_required,
            self.revocation_ref_required,
        ]
        if not all(required_flags):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_REQUIRED_GATE_DENIED")
        if not _REQUIRED_BLOCKER_CODES.issubset(set(self.blocker_codes)):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_BLOCKER_CODES_REQUIRED")
        if self.posture in {
            ProviderCredentialVaultPosture.secret_ref_available,
            ProviderCredentialVaultPosture.rotation_required,
            ProviderCredentialVaultPosture.validation_required_but_blocked,
            ProviderCredentialVaultPosture.invocation_requires_approval,
        }:
            if _ref_is_unbound(self.secret_ref) or _ref_is_revoked(self.secret_ref):
                raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_SECRET_REF_REQUIRED")
            if (
                _ref_is_unbound(self.provider_ref)
                or _ref_is_unbound(self.model_ref)
                or _ref_is_unbound(self.credential_ref)
            ):
                raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_EXACT_SCOPE_REQUIRED")
        if self.posture == ProviderCredentialVaultPosture.secret_ref_revoked:
            if not _ref_is_revoked(self.secret_ref):
                raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_REVOKED_REF_REQUIRED")
        if self.posture in {
            ProviderCredentialVaultPosture.vault_not_configured,
            ProviderCredentialVaultPosture.vault_blocked,
        } and not _ref_is_unbound(self.secret_ref):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_RECORD_UNSCOPED_SECRET_REF_DENIED")
        return self


class ProviderCredentialVaultSnapshot(_CredentialVaultContractModel):
    snapshot_ref: str = "credential-vault-snapshot-ref:provider-runtime:metadata-only"
    contract_ref: str = "contract-ref:provider-credential-vault-shell:v1"
    status: str = "metadata_only"
    supported_postures: list[ProviderCredentialVaultPosture] = Field(
        default_factory=lambda: list(ProviderCredentialVaultPosture)
    )
    records: list[ProviderCredentialVaultRecord] = Field(default_factory=list)
    metadata_only: bool = True
    safe_refs_only: bool = True
    secret_collection_enabled: bool = False
    raw_secret_storage_enabled: bool = False
    os_credential_backend_access_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_invocation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    vault_presence_authorizes_validation: bool = False
    vault_presence_authorizes_invocation: bool = False
    cli_inspection_ref: str = "cli-inspection-ref:provider-credential-vault-shell"
    blocker_codes: list[str] = Field(default_factory=lambda: sorted(_REQUIRED_BLOCKER_CODES))
    safe_summary: str = (
        "Credential vault shell is metadata only; vault records cannot authorize "
        "credential validation, provider SDK calls, or model invocation."
    )

    @model_validator(mode="after")
    def snapshot_must_remain_non_authorizing(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        if self.status != "metadata_only":
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_STATUS_METADATA_ONLY_REQUIRED")
        if set(self.supported_postures) != set(ProviderCredentialVaultPosture):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_POSTURES_DRIFTED")
        if not self.metadata_only or not self.safe_refs_only:
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_METADATA_ONLY_REQUIRED")
        denied_flags = [
            self.secret_collection_enabled,
            self.raw_secret_storage_enabled,
            self.os_credential_backend_access_enabled,
            self.credential_validation_enabled,
            self.provider_invocation_enabled,
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.vault_presence_authorizes_validation,
            self.vault_presence_authorizes_invocation,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_AUTHORITY_DENIED")
        if not _REQUIRED_BLOCKER_CODES.issubset(set(self.blocker_codes)):
            raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_BLOCKER_CODES_REQUIRED")
        for record in self.records:
            if not record.metadata_only or not record.safe_refs_only:
                raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_RECORD_METADATA_ONLY_REQUIRED")
            if record.validation_authority_granted or record.invocation_authority_granted:
                raise ValueError("PROVIDER_CREDENTIAL_VAULT_SNAPSHOT_RECORD_AUTHORITY_DENIED")
        return self


def build_provider_credential_vault_snapshot() -> ProviderCredentialVaultSnapshot:
    provider_slugs = [
        "openai-compatible",
        "anthropic-compatible",
        "local-openai-compatible",
    ]
    records = [
        ProviderCredentialVaultRecord(
            record_ref=f"credential-vault-record-ref:{slug}:metadata-only",
            provider_ref=f"provider-ref:{slug}:not-bound",
            model_ref=f"model-ref:{slug}:not-selected",
            credential_ref=f"credential-ref:{slug}:not-bound",
            secret_ref=f"secret-ref:{slug}:not-configured",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            approval_scope_ref="approval-scope-ref:provider-runtime:not-granted",
            budget_decision_ref=f"budget-decision-ref:{slug}:required",
            expected_receipt_ref=f"receipt-ref:{slug}:future-required",
            revocation_ref="revocation-ref:provider-runtime:not-active",
        )
        for slug in provider_slugs
    ]
    return ProviderCredentialVaultSnapshot(records=records)
