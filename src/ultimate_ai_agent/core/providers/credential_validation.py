from __future__ import annotations

import hashlib
import json
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    TrustMode,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel as CapabilityRiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


PROVIDER_CREDENTIAL_VALIDATION_ROUTE = "/control-center/providers/credentials/validate"
PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF = (
    "provider-ref:openai-compatible:credential-validation"
)
PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF = (
    "policy-ref:provider-credential-validation:exact-approved:v1"
)
PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID = (
    "provider.credential_validation.exact_approved"
)
PROVIDER_CREDENTIAL_VALIDATION_ACTION = "provider_credential_exact_approved_validation"
PROVIDER_CREDENTIAL_VALIDATION_NETWORK_SCOPE_REF = (
    "network-scope-ref:provider-credential-validation:models-index"
)
PROVIDER_CREDENTIAL_VALIDATION_ENDPOINT_REF = (
    "provider-endpoint-ref:openai-compatible:models-index"
)
PROVIDER_CREDENTIAL_VALIDATION_ALLOWED_ENDPOINT = "https://api.openai.com/v1/models"
PROVIDER_CREDENTIAL_VALIDATION_ALLOWED_ENDPOINTS = frozenset(
    {PROVIDER_CREDENTIAL_VALIDATION_ALLOWED_ENDPOINT}
)
PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY = (
    "Exact-approved provider credential validation recorded a redacted receipt."
)


class ProviderCredentialValidationStatus(str, Enum):
    credential_valid = "credential_valid"
    credential_invalid = "credential_invalid"
    validation_blocked = "validation_blocked"


class _ProviderCredentialValidationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _default_actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="operator:local",
        authority_source=AuthoritySource.manual_operator_action,
    )


def _default_data_classification() -> DataClassification:
    return DataClassification(
        classification=ClassificationValue.project_private,
        source="provider_credential_validation_lane",
        requires_redaction=True,
        requires_consent=True,
    )


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


def _safe_ref_matches(value: str, prefixes: tuple[str, ...]) -> bool:
    if not any(value.startswith(prefix) for prefix in prefixes):
        return False
    return all(char.isalnum() or char in {":", "-", "_"} for char in value)


def _reject_unsafe_ref_fields(
    values: dict[str, str],
    prefixes: dict[str, tuple[str, ...]],
    error_code: str,
) -> None:
    for field_name, field_value in values.items():
        if not _safe_ref_matches(field_value, prefixes[field_name]):
            raise ValueError(f"{error_code}:{field_name}")


def _ref_is_missing(ref: str | None) -> bool:
    if ref is None or not ref.strip():
        return True
    lowered = ref.lower()
    return any(
        marker in lowered
        for marker in (":missing", "not-bound", "not-selected", "not-configured")
    )


def _actor_context_is_local_operator(actor_context: ActorContext) -> bool:
    return (
        actor_context.actor_type == ActorType.human_user
        and actor_context.actor_id == "operator:local"
        and actor_context.authority_source == AuthoritySource.manual_operator_action
        and actor_context.on_behalf_of_user_id is None
        and actor_context.workspace_id is None
        and actor_context.project_id is None
        and actor_context.execution_contract_id is None
        and actor_context.consent_ref is None
        and actor_context.session_id is None
    )


def _suffix(ref: str) -> str:
    return ref.split(":")[-1].replace("_", "-")


class ProviderCredentialValidationReadiness(_ProviderCredentialValidationModel):
    lane_ref: str = "provider-credential-validation-lane:exact-approved:v1"
    route_ref: str = f"POST {PROVIDER_CREDENTIAL_VALIDATION_ROUTE}"
    provider_ref: str = PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF
    policy_ref: str = PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF
    status: ProviderCredentialValidationStatus = (
        ProviderCredentialValidationStatus.validation_blocked
    )
    validation_enabled: bool = False
    provider_network_call_enabled_by_default: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    chat_or_completions_enabled: bool = False
    broad_provider_router_enabled: bool = False
    fallback_enabled: bool = False
    billing_authority_granted: bool = False
    exact_approval_required: bool = True
    credential_ref_required: bool = True
    provider_ref_required: bool = True
    policy_ref_required: bool = True
    idempotency_ref_required: bool = True
    validation_receipt_ref_required: bool = True
    revocation_or_safe_disable_ref_required: bool = True
    redacted_receipts_only: bool = True
    ui_states: list[str] = Field(
        default_factory=lambda: [
            "validation blocked",
            "credential valid",
            "credential invalid",
            "approval required",
            "no provider authority",
        ]
    )
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "EXACT_APPROVAL_REQUIRED",
            "PROVIDER_REF_REQUIRED",
            "CREDENTIAL_REF_REQUIRED",
            "POLICY_REF_REQUIRED",
            "IDEMPOTENCY_REF_REQUIRED",
            "VALIDATION_RECEIPT_REF_REQUIRED",
            "REVOCATION_OR_SAFE_DISABLE_REF_REQUIRED",
            "VALIDATION_ADAPTER_DISABLED_BY_DEFAULT",
            "NO_MODEL_INVOCATION",
            "NO_PROVIDER_SDK",
            "NO_BILLING_AUTHORITY",
        ]
    )
    safe_summary: str = (
        "Provider credential validation is contract-wired for one exact-approved "
        "OpenAI-compatible provider ref. The app default remains validation-blocked: "
        "no provider SDK, model invocation, billing authority, fallback, broad router, "
        "or raw credential display is enabled."
    )

    @model_validator(mode="after")
    def readiness_must_be_blocked_and_exact_approval_bound(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_READINESS_SECRET_LIKE_VALUE_REJECTED",
        )
        denied_flags = [
            self.validation_enabled,
            self.provider_network_call_enabled_by_default,
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.chat_or_completions_enabled,
            self.broad_provider_router_enabled,
            self.fallback_enabled,
            self.billing_authority_granted,
        ]
        if any(denied_flags):
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_READINESS_AUTHORITY_DENIED"
            )
        required_flags = [
            self.exact_approval_required,
            self.credential_ref_required,
            self.provider_ref_required,
            self.policy_ref_required,
            self.idempotency_ref_required,
            self.validation_receipt_ref_required,
            self.revocation_or_safe_disable_ref_required,
            self.redacted_receipts_only,
        ]
        if not all(required_flags):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_READINESS_GATE_DENIED")
        required_ui_states = {
            "validation blocked",
            "credential valid",
            "credential invalid",
            "approval required",
            "no provider authority",
        }
        if set(self.ui_states) != required_ui_states:
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_READINESS_UI_STATES_DENIED"
            )
        required_codes = {
            "EXACT_APPROVAL_REQUIRED",
            "PROVIDER_REF_REQUIRED",
            "CREDENTIAL_REF_REQUIRED",
            "POLICY_REF_REQUIRED",
            "IDEMPOTENCY_REF_REQUIRED",
            "VALIDATION_RECEIPT_REF_REQUIRED",
            "REVOCATION_OR_SAFE_DISABLE_REF_REQUIRED",
            "VALIDATION_ADAPTER_DISABLED_BY_DEFAULT",
            "NO_MODEL_INVOCATION",
            "NO_PROVIDER_SDK",
            "NO_BILLING_AUTHORITY",
        }
        if not required_codes.issubset(set(self.blocker_codes)):
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_READINESS_BLOCKERS_REQUIRED"
            )
        return self


class ProviderCredentialValidationRequest(_ProviderCredentialValidationModel):
    validation_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    validation_receipt_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    provider_manifest_ref: str = Field(..., min_length=1)
    provider_allowlist_ref: str = Field(..., min_length=1)
    rate_budget_ref: str = Field(..., min_length=1)
    redacted_validation_summary_ref: str = Field(..., min_length=1)
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    data_classification: DataClassification = Field(
        default_factory=_default_data_classification
    )

    @model_validator(mode="after")
    def request_must_be_safe_refs_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "validation_ref": self.validation_ref,
                "run_id": self.run_id,
                "provider_ref": self.provider_ref,
                "credential_ref": self.credential_ref,
                "policy_ref": self.policy_ref,
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "idempotency_ref": self.idempotency_ref,
                "validation_receipt_ref": self.validation_receipt_ref,
                "revocation_ref": self.revocation_ref,
                "safe_disable_ref": self.safe_disable_ref,
                "provider_manifest_ref": self.provider_manifest_ref,
                "provider_allowlist_ref": self.provider_allowlist_ref,
                "rate_budget_ref": self.rate_budget_ref,
                "redacted_validation_summary_ref": self.redacted_validation_summary_ref,
            },
            {
                "validation_ref": ("provider-credential-validation-ref:",),
                "run_id": ("run-ref:",),
                "provider_ref": ("provider-ref:",),
                "credential_ref": ("credential-ref:",),
                "policy_ref": ("policy-ref:",),
                "approval_ref": ("approval-ref:",),
                "approval_scope_ref": ("approval-scope-ref:",),
                "idempotency_ref": ("idempotency:", "idempotency-ref:"),
                "validation_receipt_ref": ("receipt:", "receipt-ref:"),
                "revocation_ref": ("revocation-ref:",),
                "safe_disable_ref": ("safe-disable-ref:",),
                "provider_manifest_ref": ("provider-manifest-ref:",),
                "provider_allowlist_ref": ("provider-allowlist-ref:",),
                "rate_budget_ref": ("rate-budget-ref:",),
                "redacted_validation_summary_ref": (
                    "redacted-validation-summary-ref:",
                ),
            },
            "PROVIDER_CREDENTIAL_VALIDATION_REQUEST_UNSAFE_REF_REJECTED",
        )
        if not _actor_context_is_local_operator(self.actor_context):
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_REQUEST_ACTOR_CONTEXT_DENIED"
            )
        if self.data_classification != _default_data_classification():
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_REQUEST_DATA_CLASSIFICATION_DENIED"
            )
        return self


class ProviderCredentialValidationAdapterRequest(ProviderCredentialValidationRequest):
    credential_secret: SecretStr = Field(..., exclude=True, repr=False)


class ProviderCredentialValidationTransportReceipt(_ProviderCredentialValidationModel):
    transport_ref: str = Field(..., min_length=1)
    provider_ref: str = PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF
    status: ProviderCredentialValidationStatus
    provider_http_status_class: Literal[
        "2xx",
        "401_or_403",
        "blocked_or_unknown",
    ]
    provider_network_called: bool = True
    provider_sdk_used: bool = False
    model_invocation_performed: bool = False
    chat_or_completions_called: bool = False
    provider_payload_persisted: bool = False
    block_reason_code: Literal[
        "PROVIDER_VALIDATION_ENDPOINT_NOT_ALLOWLISTED",
        "PROVIDER_VALIDATION_TRANSPORT_NOT_CONFIGURED",
    ] | None = None

    @model_validator(mode="after")
    def transport_receipt_must_not_claim_model_or_sdk_authority(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "transport_ref": self.transport_ref,
                "provider_ref": self.provider_ref,
            },
            {
                "transport_ref": ("provider-validation-transport-ref:",),
                "provider_ref": ("provider-ref:",),
            },
            "PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_UNSAFE_REF_REJECTED",
        )
        if self.provider_ref != PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_SCOPE_DENIED")
        if self.provider_sdk_used or self.model_invocation_performed:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_RUNTIME_DENIED")
        if self.chat_or_completions_called or self.provider_payload_persisted:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_PAYLOAD_DENIED")
        if self.status == ProviderCredentialValidationStatus.validation_blocked:
            if self.provider_http_status_class != "blocked_or_unknown":
                raise ValueError(
                    "PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_STATUS_MISMATCH"
                )
            if not self.provider_network_called and self.block_reason_code is None:
                raise ValueError(
                    "PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_BLOCK_REASON_REQUIRED"
                )
        elif self.block_reason_code is not None:
            raise ValueError(
                "PROVIDER_CREDENTIAL_VALIDATION_TRANSPORT_BLOCK_REASON_DENIED"
            )
        return self


class ProviderCredentialValidationReceipt(_ProviderCredentialValidationModel):
    receipt_ref: str = Field(..., min_length=1)
    validation_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    provider_ref: str
    credential_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    idempotency_ref: str
    validation_receipt_ref: str
    revocation_ref: str
    safe_disable_ref: str
    provider_manifest_ref: str
    provider_allowlist_ref: str
    rate_budget_ref: str
    redacted_validation_summary_ref: str
    status: ProviderCredentialValidationStatus
    validation_performed: bool = False
    provider_network_called: bool = False
    provider_sdk_used: bool = False
    model_invocation_performed: bool = False
    chat_or_completions_called: bool = False
    provider_payload_persisted: bool = False
    raw_credential_persisted: bool = False
    raw_credential_returned: bool = False
    billing_authority_granted: bool = False
    autonomous_background_call: bool = False
    provider_http_status_class: str = "blocked_or_unknown"
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    created_at: str = Field(
        default_factory=lambda: utc_now().replace(microsecond=0).isoformat()
    )

    @model_validator(mode="after")
    def receipt_must_be_redacted_safe_refs_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "receipt_ref": self.receipt_ref,
                "validation_ref": self.validation_ref,
                "run_id": self.run_id,
                "provider_ref": self.provider_ref,
                "credential_ref": self.credential_ref,
                "policy_ref": self.policy_ref,
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "idempotency_ref": self.idempotency_ref,
                "validation_receipt_ref": self.validation_receipt_ref,
                "revocation_ref": self.revocation_ref,
                "safe_disable_ref": self.safe_disable_ref,
                "provider_manifest_ref": self.provider_manifest_ref,
                "provider_allowlist_ref": self.provider_allowlist_ref,
                "rate_budget_ref": self.rate_budget_ref,
                "redacted_validation_summary_ref": self.redacted_validation_summary_ref,
            },
            {
                "receipt_ref": ("receipt:", "receipt-ref:"),
                "validation_ref": ("provider-credential-validation-ref:",),
                "run_id": ("run-ref:",),
                "provider_ref": ("provider-ref:",),
                "credential_ref": ("credential-ref:",),
                "policy_ref": ("policy-ref:",),
                "approval_ref": ("approval-ref:",),
                "approval_scope_ref": ("approval-scope-ref:",),
                "idempotency_ref": ("idempotency:", "idempotency-ref:"),
                "validation_receipt_ref": ("receipt:", "receipt-ref:"),
                "revocation_ref": ("revocation-ref:",),
                "safe_disable_ref": ("safe-disable-ref:",),
                "provider_manifest_ref": ("provider-manifest-ref:",),
                "provider_allowlist_ref": ("provider-allowlist-ref:",),
                "rate_budget_ref": ("rate-budget-ref:",),
                "redacted_validation_summary_ref": (
                    "redacted-validation-summary-ref:",
                ),
            },
            "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_UNSAFE_REF_REJECTED",
        )
        denied_flags = [
            self.provider_sdk_used,
            self.model_invocation_performed,
            self.chat_or_completions_called,
            self.provider_payload_persisted,
            self.raw_credential_persisted,
            self.raw_credential_returned,
            self.billing_authority_granted,
            self.autonomous_background_call,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_AUTHORITY_DENIED")
        if self.safe_summary != PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY_DENIED")
        if self.receipt_ref != self.validation_receipt_ref:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_REF_MISMATCH")
        if self.status in {
            ProviderCredentialValidationStatus.credential_valid,
            ProviderCredentialValidationStatus.credential_invalid,
        }:
            if not self.validation_performed or not self.provider_network_called:
                raise ValueError(
                    "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_STATUS_MISMATCH"
                )
        if self.status == ProviderCredentialValidationStatus.validation_blocked:
            if self.validation_performed:
                if not self.provider_network_called:
                    raise ValueError(
                        "PROVIDER_CREDENTIAL_VALIDATION_BLOCKED_RECEIPT_NETWORK_MISMATCH"
                    )
            if self.provider_http_status_class != "blocked_or_unknown":
                raise ValueError(
                    "PROVIDER_CREDENTIAL_VALIDATION_BLOCKED_RECEIPT_STATUS_DENIED"
                )
        return self


class ProviderCredentialValidationDecision(_ProviderCredentialValidationModel):
    decision_ref: str = Field(..., min_length=1)
    allowed: bool
    status: ProviderCredentialValidationStatus
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    required_next_action: str | None = None
    authority_decision: AuthorityPolicyDecision | None = None
    receipt: ProviderCredentialValidationReceipt | None = None

    @model_validator(mode="after")
    def decision_must_have_receipt_for_allowed_validation(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_CREDENTIAL_VALIDATION_DECISION_SECRET_LIKE_VALUE_REJECTED",
        )
        if (
            self.allowed
            and self.status == ProviderCredentialValidationStatus.validation_blocked
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_DECISION_ALLOWED_BLOCKED")
        if self.allowed and self.receipt is None:
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_DECISION_RECEIPT_REQUIRED")
        if self.allowed and (
            self.authority_decision is None
            or self.authority_decision.outcome != AuthorityDecisionOutcome.allow.value
        ):
            raise ValueError("PROVIDER_CREDENTIAL_VALIDATION_DECISION_AUTHORITY_REQUIRED")
        return self


class ProviderCredentialValidationAdapter:
    adapter_ref: str = "provider-validation-adapter-ref:disabled-default"
    provider_ref: str = PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF
    enabled: bool = False

    def validate(
        self,
        request: ProviderCredentialValidationAdapterRequest,
    ) -> ProviderCredentialValidationTransportReceipt:
        raise RuntimeError(
            "Provider credential validation adapter is disabled by default."
        )


class DisabledProviderCredentialValidationAdapter(ProviderCredentialValidationAdapter):
    enabled = False


class DeterministicProviderCredentialValidationAdapter(
    ProviderCredentialValidationAdapter
):
    adapter_ref = "provider-validation-adapter-ref:deterministic-test"
    enabled = True

    def __init__(
        self,
        status: ProviderCredentialValidationStatus = (
            ProviderCredentialValidationStatus.credential_valid
        ),
    ) -> None:
        self.status = status

    def validate(
        self,
        request: ProviderCredentialValidationAdapterRequest,
    ) -> ProviderCredentialValidationTransportReceipt:
        status_class = (
            "2xx"
            if self.status == ProviderCredentialValidationStatus.credential_valid
            else "401_or_403"
        )
        if self.status == ProviderCredentialValidationStatus.validation_blocked:
            status_class = "blocked_or_unknown"
        return ProviderCredentialValidationTransportReceipt(
            transport_ref=f"provider-validation-transport-ref:deterministic:{_suffix(request.validation_ref)}",
            status=self.status,
            provider_http_status_class=status_class,
        )


class OpenAICompatibleCredentialValidationAdapter(ProviderCredentialValidationAdapter):
    adapter_ref = "provider-validation-adapter-ref:openai-compatible:models-index"
    enabled = False

    def __init__(
        self,
        *,
        enabled: bool = False,
        endpoint_url: str = PROVIDER_CREDENTIAL_VALIDATION_ALLOWED_ENDPOINT,
        timeout_seconds: float = 10.0,
        transport: Callable[[str, str, float], int] | None = None,
    ) -> None:
        self.enabled = enabled
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    def validate(
        self,
        request: ProviderCredentialValidationAdapterRequest,
    ) -> ProviderCredentialValidationTransportReceipt:
        if not self.enabled:
            raise RuntimeError("Provider credential validation adapter is disabled.")
        if self.endpoint_url not in PROVIDER_CREDENTIAL_VALIDATION_ALLOWED_ENDPOINTS:
            return ProviderCredentialValidationTransportReceipt(
                transport_ref=f"provider-validation-transport-ref:openai-compatible:{_suffix(request.validation_ref)}",
                status=ProviderCredentialValidationStatus.validation_blocked,
                provider_http_status_class="blocked_or_unknown",
                provider_network_called=False,
                block_reason_code="PROVIDER_VALIDATION_ENDPOINT_NOT_ALLOWLISTED",
            )
        if self._transport is None:
            return ProviderCredentialValidationTransportReceipt(
                transport_ref=f"provider-validation-transport-ref:openai-compatible:{_suffix(request.validation_ref)}",
                status=ProviderCredentialValidationStatus.validation_blocked,
                provider_http_status_class="blocked_or_unknown",
                provider_network_called=False,
                block_reason_code="PROVIDER_VALIDATION_TRANSPORT_NOT_CONFIGURED",
            )
        status_code = self._transport(
            self.endpoint_url,
            request.credential_secret.get_secret_value(),
            self.timeout_seconds,
        )
        if 200 <= status_code < 300:
            status = ProviderCredentialValidationStatus.credential_valid
            status_class = "2xx"
        elif status_code in {401, 403}:
            status = ProviderCredentialValidationStatus.credential_invalid
            status_class = "401_or_403"
        else:
            status = ProviderCredentialValidationStatus.validation_blocked
            status_class = "blocked_or_unknown"
        return ProviderCredentialValidationTransportReceipt(
            transport_ref=f"provider-validation-transport-ref:openai-compatible:{_suffix(request.validation_ref)}",
            status=status,
            provider_http_status_class=status_class,
        )


class ProviderCredentialValidationReceiptStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> "ProviderCredentialValidationReceiptStore":
        return cls(Path(".uaa/provider-credential-validation/receipts.jsonl"))

    def record(
        self,
        receipt: ProviderCredentialValidationReceipt,
    ) -> ProviderCredentialValidationReceipt:
        payload = receipt.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_STORE_SECRET_LIKE_VALUE_REJECTED",
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return receipt

    def list_receipts(self) -> list[ProviderCredentialValidationReceipt]:
        if not self.path.exists():
            return []
        receipts: list[ProviderCredentialValidationReceipt] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                receipts.append(
                    ProviderCredentialValidationReceipt.model_validate_json(line)
                )
        return receipts


def build_provider_credential_validation_readiness() -> (
    ProviderCredentialValidationReadiness
):
    return ProviderCredentialValidationReadiness()


def required_provider_credential_validation_resource_refs(
    request: ProviderCredentialValidationRequest,
) -> list[str]:
    refs = [
        request.provider_ref,
        request.credential_ref,
        request.policy_ref,
        request.approval_scope_ref,
        request.idempotency_ref,
        request.validation_receipt_ref,
        request.revocation_ref,
        request.safe_disable_ref,
        request.provider_manifest_ref,
        request.provider_allowlist_ref,
        request.rate_budget_ref,
        request.redacted_validation_summary_ref,
        PROVIDER_CREDENTIAL_VALIDATION_NETWORK_SCOPE_REF,
        PROVIDER_CREDENTIAL_VALIDATION_ENDPOINT_REF,
    ]
    return list(dict.fromkeys(refs))


def build_provider_credential_validation_approval_request(
    request: ProviderCredentialValidationRequest,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"approval-request:{request.validation_ref}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.credential_access,
        subject_id=request.credential_ref,
        actor_context=request.actor_context,
        requested_action=PROVIDER_CREDENTIAL_VALIDATION_ACTION,
        purpose="Approve one exact-scoped provider credential validation using redacted refs only.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=required_provider_credential_validation_resource_refs(request),
        provider_id=request.provider_ref,
        trace_id=request.validation_ref,
    )


def build_provider_credential_validation_authority_request(
    request: ProviderCredentialValidationRequest,
) -> AuthorityActionRequest:
    action_digest = hashlib.sha256(request.validation_ref.encode("utf-8")).hexdigest()[
        :24
    ]
    scope_ref = f"authority-resource-ref:provider-credential-validation:{action_digest}"
    return AuthorityActionRequest(
        action_ref=f"authority-action-ref:provider-credential-validation:{action_digest}",
        domain=AuthorityDomain.provider_model_calls,
        capability=AuthorityCapability.execute,
        safe_summary=(
            "Evaluate the exact-approved provider credential validation lane "
            "using safe refs, transient credential handling, and redacted receipts."
        ),
        resource_refs=[
            request.provider_ref,
            request.policy_ref,
            PROVIDER_CREDENTIAL_VALIDATION_ENDPOINT_REF,
            scope_ref,
        ],
        route_ref=f"POST {PROVIDER_CREDENTIAL_VALIDATION_ROUTE}",
        lane_ref="provider-credential-validation-lane:exact-approved:v1",
        adapter_ref="provider-validation-adapter-ref:openai-compatible:models-index",
        requested_mode=TrustMode.full_machine_access_session,
        constraints={
            "provider_ref": request.provider_ref,
            "policy_ref": request.policy_ref,
            "provider_credential_validation_scope_ref": scope_ref,
            "model_invocation_allowed": False,
            "provider_payload_persistence_allowed": False,
        },
        draft_fallback_available=False,
        rollback_ref=request.safe_disable_ref,
        safe_disable_ref=request.safe_disable_ref,
    )


def build_provider_credential_validation_policy_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID,
        version="provider-credential-validation-v1",
        kind=CapabilityKind.tool,
        name=PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID,
        description=(
            "Policy gate for one exact-approved provider credential validation lane; "
            "model invocation, provider SDKs, fallback, and billing authority remain blocked."
        ),
        owner="core.providers",
        tags=[
            "provider",
            "credential-validation",
            "exact-approval",
            "redacted-receipt",
        ],
        examples=[
            "Validate one credential ref against one provider metadata endpoint after exact approval."
        ],
        anti_examples=[
            "Model invocation, chat/completions, broad provider routing, fallback execution, raw credential logging, or billing authority."
        ],
        input_schema={
            "type": "object",
            "required": [
                "provider_ref",
                "credential_ref",
                "policy_ref",
                "approval_scope_ref",
                "idempotency_ref",
                "validation_receipt_ref",
                "revocation_ref",
                "safe_disable_ref",
            ],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["decision_ref", "status", "reason_codes"],
            "additionalProperties": True,
        },
        input_modes=["safe_refs_only", "transient_secret_not_persisted"],
        output_modes=["policy_decision", "blocked_state", "redacted_receipt_ref"],
        side_effects=SideEffectLevel.external,
        risk_level=CapabilityRiskLevel.high,
        approval_required=True,
        auth_scopes=[PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF],
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        single_writer_required=True,
        safety=SafetyPolicy(
            require_single_writer=True,
            approval_required=True,
            max_risk_level=CapabilityRiskLevel.high,
            max_side_effect_level=SideEffectLevel.external,
        ),
    )


def build_provider_credential_validation_policy_task(
    request: ProviderCredentialValidationRequest,
) -> TaskEnvelope:
    return TaskEnvelope(
        task_id=f"provider-credential-validation-policy:{_suffix(request.validation_ref)}",
        user_request="Evaluate exact-approved provider credential validation policy using safe refs only.",
        objective="Require PolicyEngine posture before any credential validation adapter can run.",
        selected_capability_ids=[PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID],
        allowed_tool_ids=[PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID],
        context={
            "provider_ref": request.provider_ref,
            "credential_ref": request.credential_ref,
            "policy_ref": request.policy_ref,
            "approval_scope_ref": request.approval_scope_ref,
            "idempotency_key": request.idempotency_ref,
            "validation_receipt_ref": request.validation_receipt_ref,
            "revocation_ref": request.revocation_ref,
            "safe_disable_ref": request.safe_disable_ref,
        },
    )


def evaluate_provider_credential_validation_policy_gate(
    request: ProviderCredentialValidationRequest,
    *,
    policy_engine: PolicyEngine | None = None,
):
    policy_engine = policy_engine or PolicyEngine(
        default_max_risk=CapabilityRiskLevel.high
    )
    return policy_engine.can_execute(
        build_provider_credential_validation_policy_manifest(),
        build_provider_credential_validation_policy_task(request),
        {
            "max_risk_level": CapabilityRiskLevel.high.value,
            "auth_scopes": [request.policy_ref],
            "allowed_capability_ids": [PROVIDER_CREDENTIAL_VALIDATION_CAPABILITY_ID],
            "coordination_mode": CoordinationMode.direct_tool.value,
        },
    )


def evaluate_provider_credential_validation(
    request: ProviderCredentialValidationRequest,
    *,
    adapter: ProviderCredentialValidationAdapter | None = None,
    policy_engine: PolicyEngine | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    active_authority_leases: list[AuthorityLease] | None = None,
    receipt_store: ProviderCredentialValidationReceiptStore | None = None,
    credential_secret: SecretStr | str | None = None,
) -> ProviderCredentialValidationDecision:
    adapter = adapter or DisabledProviderCredentialValidationAdapter()
    approval_authority = approval_authority or LocalApprovalAuthority()

    missing = _missing_ref_reasons(request)
    if missing:
        return _blocked_decision(
            request,
            reason_codes=missing,
            safe_message="Provider credential validation is blocked because an exact required ref is missing.",
            required_next_action="provide_exact_provider_credential_policy_idempotency_receipt_and_revocation_refs",
        )
    if request.provider_ref != PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF:
        return _blocked_decision(
            request,
            reason_codes=["PROVIDER_REF_NOT_ALLOWED"],
            safe_message="Provider credential validation is scoped to one provider ref only.",
            required_next_action="use_the_single_allowlisted_provider_validation_ref",
        )
    if request.policy_ref != PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF:
        return _blocked_decision(
            request,
            reason_codes=["POLICY_REF_NOT_ALLOWED"],
            safe_message="Provider credential validation requires the exact PolicyEngine policy ref.",
            required_next_action="use_the_exact_provider_validation_policy_ref",
        )

    policy_decision = evaluate_provider_credential_validation_policy_gate(
        request,
        policy_engine=policy_engine,
    )
    if (
        policy_decision.status != PolicyDecisionStatus.approval_required
        or not policy_decision.requires_approval
    ):
        return _blocked_decision(
            request,
            reason_codes=list(
                dict.fromkeys(
                    [
                        *policy_decision.reason_codes,
                        "POLICY_ENGINE_APPROVAL_GATE_REQUIRED",
                    ]
                )
            ),
            safe_message="PolicyEngine must require exact approval before provider credential validation.",
            required_next_action="fix_provider_validation_policy_scope_before_validation",
        )

    authority_request = build_provider_credential_validation_authority_request(request)
    authority_leases = active_authority_leases
    if authority_leases is None:
        authority_leases = approval_authority.list_authority_leases(active_only=True)
    authority_decision = evaluate_authority_request(
        authority_request,
        authority_leases or build_default_authority_leases(),
    )
    if authority_decision.outcome != AuthorityDecisionOutcome.allow.value:
        return _blocked_decision(
            request,
            reason_codes=list(
                dict.fromkeys(
                    [
                        "AUTHORITY_LEASE_REQUIRED",
                        *[
                            ref.removeprefix("reason-ref:authority:")
                            .replace("-", "_")
                            .upper()
                            for ref in authority_decision.reason_refs
                        ],
                    ]
                )
            ),
            safe_message=(
                "Requires Full machine access for this session plus the "
                "provider_model_calls domain and execute capability before "
                "provider credential validation can proceed."
            ),
            required_next_action=(
                "select_full_machine_access_with_provider_model_calls_execute_scope"
            ),
            authority_decision=authority_decision,
        )

    approval_request = build_provider_credential_validation_approval_request(request)
    approval_decision = approval_authority.validate_for_request(
        approval_request,
        request.approval_ref,
    )
    if not approval_decision.allowed:
        required_next_action = (
            "request_exact_local_approval_for_provider_credential_validation"
            if "APPROVAL_REF_UNKNOWN" in approval_decision.reason_codes
            else "submit_exact_in_scope_provider_credential_validation_approval"
        )
        return _blocked_decision(
            request,
            reason_codes=list(approval_decision.reason_codes),
            safe_message="Exact LocalApprovalAuthority scope is required before provider credential validation.",
            required_next_action=required_next_action,
            authority_decision=authority_decision,
        )

    if not adapter.enabled:
        return _blocked_decision(
            request,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "PROVIDER_CREDENTIAL_VALIDATION_ADAPTER_DISABLED_BY_DEFAULT",
            ],
            safe_message="Exact approval validated, but provider credential validation adapter is disabled by default.",
            required_next_action="keep_validation_adapter_disabled_until_scoped_enablement",
            authority_decision=authority_decision,
        )

    if credential_secret is None:
        return _blocked_decision(
            request,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "TRANSIENT_CREDENTIAL_SECRET_REQUIRED_FOR_VALIDATION",
            ],
            safe_message="Provider credential validation requires transient credential material that is never persisted.",
            required_next_action="provide_transient_credential_material_inside_the_exact_validation_adapter_scope",
            authority_decision=authority_decision,
        )

    adapter_request = ProviderCredentialValidationAdapterRequest(
        **request.model_dump(mode="python"),
        credential_secret=credential_secret,
    )
    transport_receipt = adapter.validate(adapter_request)
    receipt = _receipt_for_transport(
        request,
        transport_receipt,
    )
    if receipt_store is not None:
        receipt_store.record(receipt)
    if (
        transport_receipt.status
        == ProviderCredentialValidationStatus.validation_blocked
    ):
        reason_codes = [
            *receipt.reason_codes,
            "PROVIDER_VALIDATION_TRANSPORT_BLOCKED_OR_UNKNOWN",
        ]
        if not transport_receipt.provider_network_called:
            reason_codes.append(
                transport_receipt.block_reason_code
                or "PROVIDER_VALIDATION_NETWORK_NOT_PERFORMED"
            )
        return ProviderCredentialValidationDecision(
            decision_ref=f"provider-credential-validation-decision:{_suffix(request.validation_ref)}",
            allowed=False,
            status=ProviderCredentialValidationStatus.validation_blocked,
            reason_codes=list(dict.fromkeys(reason_codes)),
            safe_message="Provider credential validation transport could not produce a valid or invalid credential result.",
            required_next_action="review_validation_transport_status_before_retry",
            authority_decision=authority_decision,
            receipt=receipt,
        )

    return ProviderCredentialValidationDecision(
        decision_ref=f"provider-credential-validation-decision:{_suffix(request.validation_ref)}",
        allowed=True,
        status=transport_receipt.status,
        reason_codes=list(receipt.reason_codes),
        safe_message="Provider credential validation produced a redacted receipt.",
        authority_decision=authority_decision,
        receipt=receipt,
    )


def _receipt_for_transport(
    request: ProviderCredentialValidationRequest,
    transport_receipt: ProviderCredentialValidationTransportReceipt,
) -> ProviderCredentialValidationReceipt:
    reason_codes = [
        "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
        "EXACT_APPROVAL_VALIDATED",
        "REDACTED_VALIDATION_RECEIPT_RECORDED",
    ]
    if transport_receipt.status == ProviderCredentialValidationStatus.credential_valid:
        reason_codes.append("CREDENTIAL_VALIDATED")
    elif (
        transport_receipt.status
        == ProviderCredentialValidationStatus.credential_invalid
    ):
        reason_codes.append("CREDENTIAL_REJECTED_BY_PROVIDER_AUTH_CHECK")
    else:
        reason_codes.extend(
            [
                "EXACT_APPROVAL_VALIDATED",
                "PROVIDER_VALIDATION_TRANSPORT_BLOCKED_OR_UNKNOWN",
            ]
        )
        if not transport_receipt.provider_network_called:
            reason_codes.append(
                transport_receipt.block_reason_code
                or "PROVIDER_VALIDATION_NETWORK_NOT_PERFORMED"
            )
    return ProviderCredentialValidationReceipt(
        receipt_ref=request.validation_receipt_ref,
        validation_ref=request.validation_ref,
        run_id=request.run_id,
        provider_ref=request.provider_ref,
        credential_ref=request.credential_ref,
        policy_ref=request.policy_ref,
        approval_ref=request.approval_ref,
        approval_scope_ref=request.approval_scope_ref,
        idempotency_ref=request.idempotency_ref,
        validation_receipt_ref=request.validation_receipt_ref,
        revocation_ref=request.revocation_ref,
        safe_disable_ref=request.safe_disable_ref,
        provider_manifest_ref=request.provider_manifest_ref,
        provider_allowlist_ref=request.provider_allowlist_ref,
        rate_budget_ref=request.rate_budget_ref,
        redacted_validation_summary_ref=request.redacted_validation_summary_ref,
        status=transport_receipt.status,
        validation_performed=transport_receipt.provider_network_called,
        provider_network_called=transport_receipt.provider_network_called,
        provider_http_status_class=transport_receipt.provider_http_status_class,
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_summary=PROVIDER_CREDENTIAL_VALIDATION_RECEIPT_SUMMARY,
    )


def _missing_ref_reasons(request: ProviderCredentialValidationRequest) -> list[str]:
    checks: list[tuple[str | None, str]] = [
        (request.provider_ref, "PROVIDER_REF_REQUIRED"),
        (request.credential_ref, "CREDENTIAL_REF_REQUIRED"),
        (request.policy_ref, "POLICY_REF_REQUIRED"),
        (request.approval_ref, "APPROVAL_REF_REQUIRED"),
        (request.approval_scope_ref, "APPROVAL_SCOPE_REF_REQUIRED"),
        (request.idempotency_ref, "IDEMPOTENCY_REF_REQUIRED"),
        (request.validation_receipt_ref, "VALIDATION_RECEIPT_REF_REQUIRED"),
        (request.revocation_ref, "REVOCATION_REF_REQUIRED"),
        (request.safe_disable_ref, "SAFE_DISABLE_REF_REQUIRED"),
        (request.provider_manifest_ref, "PROVIDER_MANIFEST_REF_REQUIRED"),
        (request.provider_allowlist_ref, "PROVIDER_ALLOWLIST_REF_REQUIRED"),
        (request.rate_budget_ref, "RATE_BUDGET_REF_REQUIRED"),
        (
            request.redacted_validation_summary_ref,
            "REDACTED_VALIDATION_SUMMARY_REF_REQUIRED",
        ),
    ]
    return [reason for ref, reason in checks if _ref_is_missing(ref)]


def _blocked_decision(
    request: ProviderCredentialValidationRequest,
    *,
    reason_codes: list[str],
    safe_message: str,
    required_next_action: str,
    authority_decision: AuthorityPolicyDecision | None = None,
) -> ProviderCredentialValidationDecision:
    return ProviderCredentialValidationDecision(
        decision_ref=f"provider-credential-validation-decision:{_suffix(request.validation_ref)}",
        allowed=False,
        status=ProviderCredentialValidationStatus.validation_blocked,
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_message=safe_message,
        required_next_action=required_next_action,
        authority_decision=authority_decision,
        receipt=None,
    )


def generate_provider_credential_validation_receipt_ref() -> str:
    return f"receipt:provider-credential-validation:{uuid.uuid4().hex[:16]}"
