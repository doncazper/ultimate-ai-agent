from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
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
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.decisions import CostDecision
from ultimate_ai_agent.core.costs.enums import BudgetScope, BudgetStatus
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.costs.governor import CostGovernor
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


TINY_PROVIDER_INVOCATION_ROUTE = "/control-center/providers/exact-approved-lanes/tiny"
TINY_PROVIDER_INVOCATION_PROVIDER_REF = "provider-ref:openai-compatible:tiny-exact-approved"
TINY_PROVIDER_INVOCATION_MODEL_REF = "model-ref:openai-compatible:tiny-contract-model"
TINY_PROVIDER_INVOCATION_POLICY_REF = "policy-ref:provider-runtime:tiny-exact-approved:v1"
SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF = (
    "provider-ref:anthropic-compatible:tiny-exact-approved"
)
SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF = (
    "model-ref:anthropic-compatible:tiny-contract-model"
)
SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF = (
    "policy-ref:provider-runtime:tiny-second-exact-approved:v1"
)
TINY_PROVIDER_INVOCATION_CAPABILITY_ID = "provider.invocation.tiny_exact_approved"
TINY_PROVIDER_INVOCATION_ACTION = "provider_model_tiny_exact_approved"
TINY_LIVE_PROVIDER_ADAPTER_REF = (
    "provider-adapter-ref:tiny-exact-approved:openai-compatible-live"
)
TINY_LIVE_PROVIDER_TRANSPORT_REF = "provider-transport-ref:tiny-live:openai-compatible"
TINY_LIVE_PROVIDER_ENDPOINT_REF = "provider-endpoint-ref:openai-compatible:responses"
TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT = "https://api.openai.com/v1/responses"
TINY_LIVE_PROVIDER_MODEL_NAME = "tiny-exact-approved-model"
SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF = (
    "provider-adapter-ref:tiny-exact-approved:anthropic-compatible-live"
)
SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF = (
    "provider-transport-ref:tiny-live:anthropic-compatible"
)
SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF = "provider-endpoint-ref:anthropic-compatible:messages"
SECOND_TINY_LIVE_PROVIDER_ALLOWED_ENDPOINT = "https://api.anthropic.com/v1/messages"
SECOND_TINY_LIVE_PROVIDER_MODEL_NAME = "tiny-second-exact-approved-model"
TINY_PROVIDER_INVOCATION_SCOPE_REFS = (
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
)
TINY_PROVIDER_RECEIPT_SUMMARY = (
    "Tiny exact-approved provider lane recorded a redacted receipt using a scoped adapter."
)
_TINY_PROVIDER_EXECUTION_GRANT_TOKEN = object()

_TINY_PROVIDER_INVOCATION_SCOPES = {
    TINY_PROVIDER_INVOCATION_PROVIDER_REF: {
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "policy_ref": TINY_PROVIDER_INVOCATION_POLICY_REF,
        "adapter_ref": TINY_LIVE_PROVIDER_ADAPTER_REF,
        "transport_ref": TINY_LIVE_PROVIDER_TRANSPORT_REF,
    },
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: {
        "model_ref": SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        "policy_ref": SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
        "adapter_ref": SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
        "transport_ref": SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    },
}


class TinyProviderInvocationStatus(str, Enum):
    disabled = "disabled"
    blocked_missing_provider_ref = "blocked_missing_provider_ref"
    blocked_missing_model_ref = "blocked_missing_model_ref"
    blocked_missing_credential_ref = "blocked_missing_credential_ref"
    blocked_missing_cost_estimate_ref = "blocked_missing_cost_estimate_ref"
    blocked_missing_budget_decision_ref = "blocked_missing_budget_decision_ref"
    blocked_missing_max_approved_usd = "blocked_missing_max_approved_usd"
    blocked_missing_expected_receipt_ref = "blocked_missing_expected_receipt_ref"
    blocked_missing_policy_validation = "blocked_missing_policy_validation"
    blocked_provider_not_allowed = "blocked_provider_not_allowed"
    blocked_model_not_allowed = "blocked_model_not_allowed"
    unknown_paid_cost_blocked = "unknown_paid_cost_blocked"
    cost_blocked = "cost_blocked"
    approval_required = "approval_required"
    approval_invalid = "approval_invalid"
    approved_no_execution = "approved_no_execution"
    live_adapter_blocked = "live_adapter_blocked"
    receipt_recorded = "receipt_recorded"


class TinyProviderReceiptCompletenessStatus(str, Enum):
    complete = "complete"
    incomplete_cost_requires_review = "incomplete_cost_requires_review"
    incomplete_usage_requires_review = "incomplete_usage_requires_review"


class _TinyProviderInvocationModel(BaseModel):
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
        source="tiny_provider_invocation_lane",
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


def _safe_reason_code_matches(value: str) -> bool:
    return 1 <= len(value) <= 120 and all(
        char.isupper() or char.isdigit() or char == "_" for char in value
    )


def _sanitize_reason_codes(values: object, *, fallback: str) -> list[str]:
    if not isinstance(values, list):
        return []
    sanitized: list[str] = []
    for value in values:
        reason_code = str(value)
        if _safe_reason_code_matches(reason_code):
            sanitized.append(reason_code)
        else:
            sanitized.append(fallback)
    return list(dict.fromkeys(sanitized))


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


def _tiny_provider_scope(provider_ref: str) -> dict[str, str] | None:
    return _TINY_PROVIDER_INVOCATION_SCOPES.get(provider_ref)


def _tiny_provider_scope_for_provider_model(
    provider_ref: str,
    model_ref: str,
) -> dict[str, str] | None:
    scope = _tiny_provider_scope(provider_ref)
    if scope is None or scope["model_ref"] != model_ref:
        return None
    return scope


def _tiny_provider_scope_for_request(
    request: "TinyProviderInvocationRequest",
) -> dict[str, str] | None:
    scope = _tiny_provider_scope_for_provider_model(
        request.provider_ref,
        request.model_ref,
    )
    if scope is None or scope["policy_ref"] != request.policy_ref:
        return None
    return scope


def _tiny_provider_scope_for_transport(
    receipt: "TinyProviderInvocationTransportReceipt",
) -> dict[str, str] | None:
    return _tiny_provider_scope_for_provider_model(
        receipt.provider_ref,
        receipt.model_ref,
    )


class TinyProviderInvocationReadiness(_TinyProviderInvocationModel):
    lane_ref: str = "provider-invocation-lane:tiny-exact-approved:v1"
    route_ref: str = f"POST {TINY_PROVIDER_INVOCATION_ROUTE}"
    provider_ref: str = TINY_PROVIDER_INVOCATION_PROVIDER_REF
    model_ref: str = TINY_PROVIDER_INVOCATION_MODEL_REF
    provider_scope_refs: list[str] = Field(
        default_factory=lambda: list(_TINY_PROVIDER_INVOCATION_SCOPES.keys())
    )
    model_scope_refs: list[str] = Field(
        default_factory=lambda: [
            scope["model_ref"] for scope in _TINY_PROVIDER_INVOCATION_SCOPES.values()
        ]
    )
    policy_scope_refs: list[str] = Field(
        default_factory=lambda: [
            scope["policy_ref"] for scope in _TINY_PROVIDER_INVOCATION_SCOPES.values()
        ]
    )
    adapter_scope_refs: list[str] = Field(
        default_factory=lambda: list(TINY_PROVIDER_INVOCATION_SCOPE_REFS)
    )
    status: TinyProviderInvocationStatus = TinyProviderInvocationStatus.disabled
    invocation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    network_call_enabled: bool = False
    autonomous_model_call_enabled: bool = False
    background_execution_enabled: bool = False
    billing_authority_granted: bool = False
    exact_approval_required: bool = True
    credential_ref_required: bool = True
    provider_ref_required: bool = True
    model_ref_required: bool = True
    cost_estimate_ref_required: bool = True
    budget_decision_ref_required: bool = True
    max_approved_usd_required: bool = True
    expected_receipt_ref_required: bool = True
    idempotency_ref_required: bool = True
    unknown_paid_cost_blocks: bool = True
    redacted_receipts_only: bool = True
    actual_usage_ref_required: bool = True
    actual_cost_ref_required: bool = True
    receipt_completeness_required: bool = True
    incomplete_cost_requires_review: bool = True
    incomplete_cost_blocks_further_use: bool = True
    receipt_observation_ref: str = (
        "provider-invocation-receipt-observation-ref:tiny:no-receipt"
    )
    receipt_state_source: Literal["no_receipt_observed"] = "no_receipt_observed"
    usage_captured: bool = False
    cost_captured: bool = False
    cost_incomplete: bool = False
    review_required: bool = False
    further_use_blocked: bool = False
    prompt_persistence_allowed: bool = False
    response_persistence_allowed: bool = False
    provider_exchange_persistence_allowed: bool = False
    ui_states: list[str] = Field(
        default_factory=lambda: [
            "Cost blocked",
            "Unknown paid cost",
            "No provider authority",
            "Disabled no execution",
            "Live adapter blocked",
            "Live receipt required",
        ]
    )
    receipt_observation_supported_states: list[str] = Field(
        default_factory=lambda: [
            "Usage captured",
            "Cost captured",
            "Cost incomplete",
            "Review required",
            "Further use blocked",
        ]
    )
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "TINY_PROVIDER_LANE_DISABLED_BY_DEFAULT",
            "EXACT_APPROVAL_REQUIRED",
            "CREDENTIAL_REF_REQUIRED",
            "PROVIDER_MODEL_REFS_REQUIRED",
            "COST_ESTIMATE_REF_REQUIRED",
            "BUDGET_DECISION_REF_REQUIRED",
            "MAX_APPROVED_USD_REQUIRED",
            "EXPECTED_RECEIPT_REF_REQUIRED",
            "UNKNOWN_PAID_COST_BLOCKS",
            "REDACTED_RECEIPT_REQUIRED",
            "ACTUAL_USAGE_REF_REQUIRED",
            "ACTUAL_COST_REF_REQUIRED",
            "RECEIPT_COMPLETENESS_REQUIRED",
            "INCOMPLETE_COST_REQUIRES_REVIEW",
            "INCOMPLETE_COST_BLOCKS_FURTHER_USE",
            "LIVE_ADAPTER_DISABLED_BY_DEFAULT",
            "LIVE_PROVIDER_NETWORK_ONLY_INSIDE_SCOPED_ADAPTER",
        ]
    )
    safe_summary: str = (
        "Tiny exact-approved provider lane is contract-wired but disabled by default; "
        "provider execution requires exact approval, credential/provider/model/cost/budget "
        "refs, max approved USD, idempotency, expected receipts, redacted receipts, and "
        "a separate scoped adapter enablement gate. The lane now recognizes two named "
        "single-provider adapter scopes for future fallback prerequisites, but fallback "
        "execution remains blocked. Even with live adapter contracts "
        "present, the default readiness posture remains disabled-no-execution."
    )

    @model_validator(mode="after")
    def readiness_must_remain_disabled_default_and_receipt_bound(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_READINESS_SECRET_LIKE_VALUE_REJECTED",
        )
        denied_flags = [
            self.invocation_enabled,
            self.provider_sdk_call_enabled,
            self.network_call_enabled,
            self.autonomous_model_call_enabled,
            self.background_execution_enabled,
            self.billing_authority_granted,
            self.usage_captured,
            self.cost_captured,
            self.cost_incomplete,
            self.review_required,
            self.further_use_blocked,
            self.prompt_persistence_allowed,
            self.response_persistence_allowed,
            self.provider_exchange_persistence_allowed,
        ]
        if any(denied_flags):
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_AUTHORITY_DENIED")
        if not _safe_ref_matches(
            self.receipt_observation_ref,
            ("provider-invocation-receipt-observation-ref:",),
        ):
            raise ValueError(
                "TINY_PROVIDER_INVOCATION_READINESS_RECEIPT_OBSERVATION_REF_DENIED"
            )
        if self.adapter_scope_refs != list(TINY_PROVIDER_INVOCATION_SCOPE_REFS):
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_SCOPE_REFS_DENIED")
        if self.provider_scope_refs != list(_TINY_PROVIDER_INVOCATION_SCOPES.keys()):
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_PROVIDER_SCOPE_REFS_DENIED")
        if self.model_scope_refs != [
            scope["model_ref"] for scope in _TINY_PROVIDER_INVOCATION_SCOPES.values()
        ]:
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_MODEL_SCOPE_REFS_DENIED")
        if self.policy_scope_refs != [
            scope["policy_ref"] for scope in _TINY_PROVIDER_INVOCATION_SCOPES.values()
        ]:
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_POLICY_SCOPE_REFS_DENIED")
        for provider_scope_ref in self.provider_scope_refs:
            if not _safe_ref_matches(provider_scope_ref, ("provider-ref:",)):
                raise ValueError(
                    "TINY_PROVIDER_INVOCATION_READINESS_PROVIDER_SCOPE_REF_UNSAFE"
                )
        for model_scope_ref in self.model_scope_refs:
            if not _safe_ref_matches(model_scope_ref, ("model-ref:",)):
                raise ValueError(
                    "TINY_PROVIDER_INVOCATION_READINESS_MODEL_SCOPE_REF_UNSAFE"
                )
        for policy_scope_ref in self.policy_scope_refs:
            if not _safe_ref_matches(policy_scope_ref, ("policy-ref:",)):
                raise ValueError(
                    "TINY_PROVIDER_INVOCATION_READINESS_POLICY_SCOPE_REF_UNSAFE"
                )
        for adapter_scope_ref in self.adapter_scope_refs:
            if not _safe_ref_matches(adapter_scope_ref, ("provider-adapter-ref:",)):
                raise ValueError(
                    "TINY_PROVIDER_INVOCATION_READINESS_SCOPE_REF_UNSAFE"
                )
        required_flags = [
            self.exact_approval_required,
            self.credential_ref_required,
            self.provider_ref_required,
            self.model_ref_required,
            self.cost_estimate_ref_required,
            self.budget_decision_ref_required,
            self.max_approved_usd_required,
            self.expected_receipt_ref_required,
            self.idempotency_ref_required,
            self.unknown_paid_cost_blocks,
            self.redacted_receipts_only,
            self.actual_usage_ref_required,
            self.actual_cost_ref_required,
            self.receipt_completeness_required,
            self.incomplete_cost_requires_review,
            self.incomplete_cost_blocks_further_use,
        ]
        if not all(required_flags):
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_GATE_DENIED")
        required_codes = {
            "TINY_PROVIDER_LANE_DISABLED_BY_DEFAULT",
            "EXACT_APPROVAL_REQUIRED",
            "CREDENTIAL_REF_REQUIRED",
            "PROVIDER_MODEL_REFS_REQUIRED",
            "COST_ESTIMATE_REF_REQUIRED",
            "BUDGET_DECISION_REF_REQUIRED",
            "MAX_APPROVED_USD_REQUIRED",
            "EXPECTED_RECEIPT_REF_REQUIRED",
            "UNKNOWN_PAID_COST_BLOCKS",
            "REDACTED_RECEIPT_REQUIRED",
            "ACTUAL_USAGE_REF_REQUIRED",
            "ACTUAL_COST_REF_REQUIRED",
            "RECEIPT_COMPLETENESS_REQUIRED",
            "INCOMPLETE_COST_REQUIRES_REVIEW",
            "INCOMPLETE_COST_BLOCKS_FURTHER_USE",
            "LIVE_ADAPTER_DISABLED_BY_DEFAULT",
            "LIVE_PROVIDER_NETWORK_ONLY_INSIDE_SCOPED_ADAPTER",
        }
        if not required_codes.issubset(set(self.blocker_codes)):
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_BLOCKERS_REQUIRED")
        required_ui_states = {
            "Cost blocked",
            "Unknown paid cost",
            "No provider authority",
            "Disabled no execution",
            "Live adapter blocked",
            "Live receipt required",
        }
        if set(self.ui_states) != required_ui_states:
            raise ValueError("TINY_PROVIDER_INVOCATION_READINESS_UI_STATES_DENIED")
        required_observation_states = {
            "Usage captured",
            "Cost captured",
            "Cost incomplete",
            "Review required",
            "Further use blocked",
        }
        if set(self.receipt_observation_supported_states) != required_observation_states:
            raise ValueError(
                "TINY_PROVIDER_INVOCATION_READINESS_RECEIPT_OBSERVATION_STATES_DENIED"
            )
        return self


class TinyProviderInvocationRequest(_TinyProviderInvocationModel):
    invocation_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    model_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(..., min_length=1)
    cost_estimate_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    max_approved_usd_ref: str = Field(..., min_length=1)
    max_approved_usd: float | None = Field(..., ge=0)
    idempotency_ref: str = Field(..., min_length=1)
    expected_receipt_ref: str = Field(..., min_length=1)
    usage_receipt_ref: str = Field(..., min_length=1)
    cost_receipt_ref: str = Field(..., min_length=1)
    redacted_input_summary_ref: str = Field(..., min_length=1)
    redacted_output_summary_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    estimated_input_tokens: int = Field(..., ge=0)
    estimated_output_tokens: int = Field(..., ge=0)
    estimated_cost_usd: float | None = Field(..., ge=0)
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    data_classification: DataClassification = Field(
        default_factory=_default_data_classification
    )

    @model_validator(mode="after")
    def request_must_be_safe_refs_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "invocation_ref": self.invocation_ref,
                "run_id": self.run_id,
                "provider_ref": self.provider_ref,
                "model_ref": self.model_ref,
                "credential_ref": self.credential_ref,
                "policy_ref": self.policy_ref,
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "cost_estimate_ref": self.cost_estimate_ref,
                "budget_decision_ref": self.budget_decision_ref,
                "max_approved_usd_ref": self.max_approved_usd_ref,
                "idempotency_ref": self.idempotency_ref,
                "expected_receipt_ref": self.expected_receipt_ref,
                "usage_receipt_ref": self.usage_receipt_ref,
                "cost_receipt_ref": self.cost_receipt_ref,
                "redacted_input_summary_ref": self.redacted_input_summary_ref,
                "redacted_output_summary_ref": self.redacted_output_summary_ref,
                "safe_disable_ref": self.safe_disable_ref,
            },
            {
                "invocation_ref": ("provider-invocation-ref:",),
                "run_id": ("run-ref:",),
                "provider_ref": ("provider-ref:",),
                "model_ref": ("model-ref:",),
                "credential_ref": ("credential-ref:",),
                "policy_ref": ("policy-ref:",),
                "approval_ref": ("approval-ref:",),
                "approval_scope_ref": ("approval-scope-ref:",),
                "cost_estimate_ref": ("cost-estimate-ref:",),
                "budget_decision_ref": ("budget-decision-ref:",),
                "max_approved_usd_ref": ("max-approved-usd-ref:",),
                "idempotency_ref": ("idempotency:", "idempotency-ref:"),
                "expected_receipt_ref": ("receipt:", "receipt-ref:"),
                "usage_receipt_ref": ("usage-receipt-ref:",),
                "cost_receipt_ref": ("cost-receipt-ref:",),
                "redacted_input_summary_ref": ("redacted-input-summary-ref:",),
                "redacted_output_summary_ref": ("redacted-output-summary-ref:",),
                "safe_disable_ref": ("safe-disable-ref:",),
            },
            "TINY_PROVIDER_INVOCATION_REQUEST_UNSAFE_REF_REJECTED",
        )
        if not _actor_context_is_local_operator(self.actor_context):
            raise ValueError("TINY_PROVIDER_INVOCATION_REQUEST_ACTOR_CONTEXT_DENIED")
        return self


class TinyProviderInvocationExecutionGrant(_TinyProviderInvocationModel):
    grant_ref: Literal[
        "provider-invocation-execution-grant:tiny-live:exact-approved:v1"
    ] = "provider-invocation-execution-grant:tiny-live:exact-approved:v1"
    adapter_ref: str = TINY_LIVE_PROVIDER_ADAPTER_REF
    provider_ref: str
    model_ref: str
    credential_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    cost_estimate_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    cost_governor_decision_ref: str
    receipt_store_required: bool = True
    _runtime_authority_token: object | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def grant_must_be_exact_and_safe(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "grant_ref": self.grant_ref,
                "adapter_ref": self.adapter_ref,
                "provider_ref": self.provider_ref,
                "model_ref": self.model_ref,
                "credential_ref": self.credential_ref,
                "policy_ref": self.policy_ref,
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "cost_estimate_ref": self.cost_estimate_ref,
                "budget_decision_ref": self.budget_decision_ref,
                "expected_receipt_ref": self.expected_receipt_ref,
                "cost_governor_decision_ref": self.cost_governor_decision_ref,
            },
            {
                "grant_ref": ("provider-invocation-execution-grant:",),
                "adapter_ref": ("provider-adapter-ref:",),
                "provider_ref": ("provider-ref:",),
                "model_ref": ("model-ref:",),
                "credential_ref": ("credential-ref:",),
                "policy_ref": ("policy-ref:",),
                "approval_ref": ("approval-ref:",),
                "approval_scope_ref": ("approval-scope-ref:",),
                "cost_estimate_ref": ("cost-estimate-ref:",),
                "budget_decision_ref": ("budget-decision-ref:",),
                "expected_receipt_ref": ("receipt:", "receipt-ref:"),
                "cost_governor_decision_ref": ("cost_", "cost-decision-ref:"),
            },
            "TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_UNSAFE_REF_REJECTED",
        )
        scope = _tiny_provider_scope(self.provider_ref)
        if scope is None:
            raise ValueError("TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_PROVIDER_DENIED")
        if self.model_ref != scope["model_ref"]:
            raise ValueError("TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_MODEL_DENIED")
        if self.policy_ref != scope["policy_ref"]:
            raise ValueError("TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_POLICY_DENIED")
        if self.adapter_ref != scope["adapter_ref"]:
            raise ValueError("TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_ADAPTER_DENIED")
        if not self.receipt_store_required:
            raise ValueError(
                "TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_RECEIPT_STORE_REQUIRED"
            )
        return self

    def matches_request(self, request: TinyProviderInvocationRequest) -> bool:
        return all(
            (
                self.provider_ref == request.provider_ref,
                self.model_ref == request.model_ref,
                self.credential_ref == request.credential_ref,
                self.policy_ref == request.policy_ref,
                self.approval_ref == request.approval_ref,
                self.approval_scope_ref == request.approval_scope_ref,
                self.cost_estimate_ref == request.cost_estimate_ref,
                self.budget_decision_ref == request.budget_decision_ref,
                self.expected_receipt_ref == request.expected_receipt_ref,
            )
        )

    @property
    def runtime_authority_bound(self) -> bool:
        return self._runtime_authority_token is _TINY_PROVIDER_EXECUTION_GRANT_TOKEN


class TinyProviderInvocationTransportReceipt(_TinyProviderInvocationModel):
    transport_ref: str = Field(..., min_length=1)
    adapter_ref: str = "provider-adapter-ref:tiny-exact-approved:generic"
    status: Literal["succeeded", "blocked"] = "succeeded"
    provider_ref: str = TINY_PROVIDER_INVOCATION_PROVIDER_REF
    model_ref: str = TINY_PROVIDER_INVOCATION_MODEL_REF
    redacted_output_summary_ref: str = Field(..., min_length=1)
    usage_receipt_ref: str = Field(..., min_length=1)
    cost_receipt_ref: str = Field(..., min_length=1)
    input_tokens_used: int = Field(..., ge=0)
    output_tokens_used: int = Field(..., ge=0)
    billed_cost_usd: float = Field(..., ge=0)
    provider_sdk_used: bool = False
    network_call_performed: bool = False
    raw_output_persisted: bool = False
    model_output_authoritative: bool = False
    block_reason_code: str | None = None

    @model_validator(mode="after")
    def transport_receipt_must_be_redacted_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_TRANSPORT_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "transport_ref": self.transport_ref,
                "adapter_ref": self.adapter_ref,
                "provider_ref": self.provider_ref,
                "model_ref": self.model_ref,
                "redacted_output_summary_ref": self.redacted_output_summary_ref,
                "usage_receipt_ref": self.usage_receipt_ref,
                "cost_receipt_ref": self.cost_receipt_ref,
            },
            {
                "transport_ref": ("provider-transport-ref:",),
                "adapter_ref": ("provider-adapter-ref:",),
                "provider_ref": ("provider-ref:",),
                "model_ref": ("model-ref:",),
                "redacted_output_summary_ref": ("redacted-output-summary-ref:",),
                "usage_receipt_ref": ("usage-receipt-ref:",),
                "cost_receipt_ref": ("cost-receipt-ref:",),
            },
            "TINY_PROVIDER_INVOCATION_TRANSPORT_UNSAFE_REF_REJECTED",
        )
        scope = _tiny_provider_scope_for_transport(self)
        if scope is None:
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_SCOPE_DENIED")
        if self.provider_sdk_used:
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_PROVIDER_SDK_DENIED")
        if self.network_call_performed and (
            self.adapter_ref != scope["adapter_ref"]
            or self.transport_ref != scope["transport_ref"]
        ):
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_NETWORK_SCOPE_DENIED")
        if self.raw_output_persisted or self.model_output_authoritative:
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_OUTPUT_AUTHORITY_DENIED")
        if self.status == "blocked" and not self.block_reason_code:
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_BLOCK_REASON_REQUIRED")
        if self.status == "succeeded" and self.block_reason_code:
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_BLOCK_REASON_DENIED")
        if self.block_reason_code and not _safe_reason_code_matches(
            self.block_reason_code
        ):
            raise ValueError("TINY_PROVIDER_INVOCATION_TRANSPORT_BLOCK_REASON_UNSAFE")
        return self


class TinyProviderInvocationReceipt(_TinyProviderInvocationModel):
    receipt_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    provider_ref: str
    model_ref: str
    adapter_ref: str = "provider-adapter-ref:tiny-exact-approved:generic"
    credential_ref: str
    approval_ref: str
    approval_scope_ref: str
    cost_estimate_ref: str
    budget_decision_ref: str
    max_approved_usd_ref: str
    expected_receipt_ref: str
    usage_receipt_ref: str
    cost_receipt_ref: str
    cost_governor_decision_ref: str
    estimated_cost_ref: str
    actual_usage_ref: str
    actual_cost_ref: str
    idempotency_ref: str
    redacted_input_summary_ref: str
    redacted_output_summary_ref: str
    safe_disable_ref: str
    status: TinyProviderInvocationStatus
    invocation_performed: bool = False
    provider_sdk_used: bool = False
    network_call_performed: bool = False
    autonomous_model_call: bool = False
    background_execution: bool = False
    billing_authority_granted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_exchange_persisted: bool = False
    model_output_authoritative: bool = False
    input_tokens_used: int = Field(default=0, ge=0)
    output_tokens_used: int = Field(default=0, ge=0)
    estimated_cost_usd: float | None = Field(None, ge=0)
    billed_cost_usd: float | None = Field(None, ge=0)
    actual_usage_captured: bool
    actual_cost_captured: bool
    receipt_completeness_status: TinyProviderReceiptCompletenessStatus
    incomplete_cost_requires_review: bool
    further_provider_use_blocked: bool
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    created_at: str = Field(
        default_factory=lambda: utc_now().replace(microsecond=0).isoformat()
    )

    @model_validator(mode="after")
    def receipt_must_be_redacted_and_receipt_bound(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_RECEIPT_SECRET_LIKE_VALUE_REJECTED",
        )
        _reject_unsafe_ref_fields(
            {
                "receipt_ref": self.receipt_ref,
                "invocation_ref": self.invocation_ref,
                "run_id": self.run_id,
                "provider_ref": self.provider_ref,
                "model_ref": self.model_ref,
                "adapter_ref": self.adapter_ref,
                "credential_ref": self.credential_ref,
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "cost_estimate_ref": self.cost_estimate_ref,
                "budget_decision_ref": self.budget_decision_ref,
                "max_approved_usd_ref": self.max_approved_usd_ref,
                "expected_receipt_ref": self.expected_receipt_ref,
                "usage_receipt_ref": self.usage_receipt_ref,
                "cost_receipt_ref": self.cost_receipt_ref,
                "cost_governor_decision_ref": self.cost_governor_decision_ref,
                "estimated_cost_ref": self.estimated_cost_ref,
                "actual_usage_ref": self.actual_usage_ref,
                "actual_cost_ref": self.actual_cost_ref,
                "idempotency_ref": self.idempotency_ref,
                "redacted_input_summary_ref": self.redacted_input_summary_ref,
                "redacted_output_summary_ref": self.redacted_output_summary_ref,
                "safe_disable_ref": self.safe_disable_ref,
            },
            {
                "receipt_ref": ("receipt:", "receipt-ref:"),
                "invocation_ref": ("provider-invocation-ref:",),
                "run_id": ("run-ref:",),
                "provider_ref": ("provider-ref:",),
                "model_ref": ("model-ref:",),
                "adapter_ref": ("provider-adapter-ref:",),
                "credential_ref": ("credential-ref:",),
                "approval_ref": ("approval-ref:",),
                "approval_scope_ref": ("approval-scope-ref:",),
                "cost_estimate_ref": ("cost-estimate-ref:",),
                "budget_decision_ref": ("budget-decision-ref:",),
                "max_approved_usd_ref": ("max-approved-usd-ref:",),
                "expected_receipt_ref": ("receipt:", "receipt-ref:"),
                "usage_receipt_ref": ("usage-receipt-ref:",),
                "cost_receipt_ref": ("cost-receipt-ref:",),
                "cost_governor_decision_ref": ("cost_", "cost-decision-ref:"),
                "estimated_cost_ref": ("cost-estimate-ref:", "estimated-cost-ref:"),
                "actual_usage_ref": ("actual-usage-ref:",),
                "actual_cost_ref": ("actual-cost-ref:",),
                "idempotency_ref": ("idempotency:", "idempotency-ref:"),
                "redacted_input_summary_ref": ("redacted-input-summary-ref:",),
                "redacted_output_summary_ref": ("redacted-output-summary-ref:",),
                "safe_disable_ref": ("safe-disable-ref:",),
            },
            "TINY_PROVIDER_INVOCATION_RECEIPT_UNSAFE_REF_REJECTED",
        )
        denied_flags = [
            self.provider_sdk_used,
            self.autonomous_model_call,
            self.background_execution,
            self.billing_authority_granted,
            self.raw_prompt_persisted,
            self.raw_response_persisted,
            self.raw_provider_exchange_persisted,
            self.model_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_AUTHORITY_DENIED")
        scope = _tiny_provider_scope_for_provider_model(self.provider_ref, self.model_ref)
        if scope is None:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_SCOPE_DENIED")
        if self.network_call_performed and self.adapter_ref != scope["adapter_ref"]:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_NETWORK_SCOPE_DENIED")
        if self.safe_summary != TINY_PROVIDER_RECEIPT_SUMMARY:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_SAFE_SUMMARY_DENIED")
        if self.status == TinyProviderInvocationStatus.receipt_recorded and not self.invocation_performed:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_STATUS_MISMATCH")
        if self.status != TinyProviderInvocationStatus.receipt_recorded and self.invocation_performed:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_EXECUTION_STATUS_MISMATCH")
        if self.expected_receipt_ref != self.receipt_ref:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_EXPECTED_REF_MISMATCH")
        if self.estimated_cost_ref != self.cost_estimate_ref:
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_ESTIMATE_REF_MISMATCH")
        if self.status == TinyProviderInvocationStatus.receipt_recorded:
            if self.receipt_completeness_status != TinyProviderReceiptCompletenessStatus.complete:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_COMPLETENESS_REQUIRED")
            if self.incomplete_cost_requires_review or self.further_provider_use_blocked:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_REVIEW_BLOCK_DENIED")
            if self.network_call_performed and (
                self.billed_cost_usd is None or self.billed_cost_usd <= 0
            ):
                raise ValueError(
                    "TINY_PROVIDER_INVOCATION_RECEIPT_ACTUAL_COST_REQUIRED"
                )
        if self.receipt_completeness_status == TinyProviderReceiptCompletenessStatus.complete:
            if not self.actual_usage_captured or not self.actual_cost_captured:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_ACTUAL_REFS_REQUIRED")
            if self.incomplete_cost_requires_review or self.further_provider_use_blocked:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_INCOMPLETE_FLAG_DENIED")
        if (
            self.receipt_completeness_status
            == TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
        ):
            if self.actual_cost_captured:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_COST_CAPTURE_MISMATCH")
            if not self.incomplete_cost_requires_review or not self.further_provider_use_blocked:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_COST_REVIEW_REQUIRED")
        if (
            self.receipt_completeness_status
            == TinyProviderReceiptCompletenessStatus.incomplete_usage_requires_review
        ):
            if self.actual_usage_captured:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_USAGE_CAPTURE_MISMATCH")
            if not self.further_provider_use_blocked:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_USAGE_REVIEW_REQUIRED")
        if any(not _safe_reason_code_matches(reason) for reason in self.reason_codes):
            raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_REASON_CODE_UNSAFE")
        return self


class TinyProviderInvocationDecision(_TinyProviderInvocationModel):
    decision_ref: str = Field(..., min_length=1)
    allowed: bool
    status: TinyProviderInvocationStatus
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    required_next_action: str | None = None
    cost_decision: CostDecision | None = None
    receipt: TinyProviderInvocationReceipt | None = None

    @model_validator(mode="after")
    def decision_must_not_imply_authority_without_receipt(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "TINY_PROVIDER_INVOCATION_DECISION_SECRET_LIKE_VALUE_REJECTED",
        )
        if self.allowed and self.status != TinyProviderInvocationStatus.receipt_recorded:
            raise ValueError("TINY_PROVIDER_INVOCATION_DECISION_ALLOWED_STATUS_DENIED")
        if self.allowed and self.receipt is None:
            raise ValueError("TINY_PROVIDER_INVOCATION_DECISION_RECEIPT_REQUIRED")
        return self


class TinyProviderInvocationAdapter:
    adapter_ref: str = "provider-adapter-ref:tiny-exact-approved:disabled-default"
    provider_ref: str = TINY_PROVIDER_INVOCATION_PROVIDER_REF
    model_ref: str = TINY_PROVIDER_INVOCATION_MODEL_REF
    enabled: bool = False
    may_perform_network_call: bool = False
    requires_receipt_store_before_network: bool = False

    def execute(
        self, request: TinyProviderInvocationRequest
    ) -> TinyProviderInvocationTransportReceipt:
        raise RuntimeError("Tiny provider invocation adapter is disabled by default.")


class DisabledTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    enabled = False


class DeterministicTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    adapter_ref = "provider-adapter-ref:tiny-exact-approved:deterministic-test"
    enabled = True

    def execute(
        self, request: TinyProviderInvocationRequest
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=f"provider-transport-ref:tiny-provider:{_suffix(request.invocation_ref)}",
            adapter_ref=self.adapter_ref,
            provider_ref=request.provider_ref,
            model_ref=request.model_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=request.estimated_cost_usd,
        )


class TinyProviderInvocationReceiptStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> "TinyProviderInvocationReceiptStore":
        return cls(Path(".uaa/provider-invocation/receipts.jsonl"))

    def record(self, receipt: TinyProviderInvocationReceipt) -> TinyProviderInvocationReceipt:
        payload = receipt.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "TINY_PROVIDER_INVOCATION_RECEIPT_STORE_SECRET_LIKE_VALUE_REJECTED",
        )
        existing = self.find_by_idempotency_ref(receipt.idempotency_ref)
        if existing is not None:
            if existing.model_dump(mode="json") != payload:
                raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_IDEMPOTENCY_CONFLICT")
            return existing
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return receipt

    def find_by_idempotency_ref(
        self,
        idempotency_ref: str,
    ) -> TinyProviderInvocationReceipt | None:
        if not self.path.exists():
            return None
        for receipt in self.list_receipts():
            if receipt.idempotency_ref == idempotency_ref:
                return receipt
        return None

    def list_receipts(self) -> list[TinyProviderInvocationReceipt]:
        if not self.path.exists():
            return []
        receipts: list[TinyProviderInvocationReceipt] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                receipts.append(
                    TinyProviderInvocationReceipt.model_validate(
                        _normalize_receipt_payload_for_replay(payload)
                    )
                )
        return receipts

    def find_unreviewed_incomplete_cost_receipt(
        self,
    ) -> TinyProviderInvocationReceipt | None:
        for receipt in self.list_receipts():
            if (
                receipt.incomplete_cost_requires_review
                and receipt.further_provider_use_blocked
            ):
                return receipt
        return None

    def find_unreviewed_blocking_receipt(
        self,
    ) -> TinyProviderInvocationReceipt | None:
        for receipt in self.list_receipts():
            if receipt.further_provider_use_blocked:
                return receipt
        return None


def build_tiny_provider_invocation_readiness() -> TinyProviderInvocationReadiness:
    return TinyProviderInvocationReadiness()


def build_tiny_provider_invocation_approval_request(
    request: TinyProviderInvocationRequest,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"approval-request:{request.invocation_ref}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.provider_route,
        subject_id=request.invocation_ref,
        actor_context=request.actor_context,
        requested_action=TINY_PROVIDER_INVOCATION_ACTION,
        purpose="Approve one tiny exact-scoped provider/model lane using redacted refs only.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=required_provider_invocation_resource_refs(request),
        provider_id=request.provider_ref,
        model_profile_id=request.model_ref,
        cost_estimate_ref=request.cost_estimate_ref,
        trace_id=request.invocation_ref,
    )


def build_tiny_provider_invocation_policy_manifest(
    policy_ref: str = TINY_PROVIDER_INVOCATION_POLICY_REF,
) -> CapabilityManifest:
    if policy_ref not in {
        TINY_PROVIDER_INVOCATION_POLICY_REF,
        SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    }:
        raise ValueError("TINY_PROVIDER_INVOCATION_POLICY_REF_DENIED")
    return CapabilityManifest(
        id=TINY_PROVIDER_INVOCATION_CAPABILITY_ID,
        version="provider-invocation-v1",
        kind=CapabilityKind.tool,
        name=TINY_PROVIDER_INVOCATION_CAPABILITY_ID,
        description=(
            "Policy gate for one tiny exact-approved provider invocation lane; "
            "runtime remains disabled unless a separate scoped adapter milestone enables it."
        ),
        owner="core.providers",
        tags=["provider", "exact-approval", "cost-governor", "redacted-receipt"],
        examples=[
            "Evaluate exact provider/model/cost/budget/receipt refs before a scoped adapter can run."
        ],
        anti_examples=[
            "Broad provider routing, fallback execution, credential validation, billing authority, or raw payload persistence."
        ],
        input_schema={
            "type": "object",
            "required": [
                "provider_ref",
                "model_ref",
                "credential_ref",
                "policy_ref",
                "approval_scope_ref",
                "cost_estimate_ref",
                "budget_decision_ref",
                "idempotency_ref",
                "expected_receipt_ref",
            ],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["decision_ref", "status", "reason_codes"],
            "additionalProperties": True,
        },
        input_modes=["safe_refs_only", "redacted_summary_refs"],
        output_modes=["policy_decision", "blocked_state", "redacted_receipt_ref"],
        side_effects=SideEffectLevel.external,
        risk_level=CapabilityRiskLevel.high,
        approval_required=True,
        auth_scopes=[policy_ref],
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        single_writer_required=True,
        safety=SafetyPolicy(
            require_single_writer=True,
            approval_required=True,
            max_risk_level=CapabilityRiskLevel.high,
            max_side_effect_level=SideEffectLevel.external,
        ),
    )


def build_tiny_provider_invocation_policy_task(
    request: TinyProviderInvocationRequest,
) -> TaskEnvelope:
    return TaskEnvelope(
        task_id=f"provider-invocation-policy:{_suffix(request.invocation_ref)}",
        user_request="Evaluate exact-approved provider invocation policy using safe refs only.",
        objective="Require PolicyEngine posture before any provider adapter can execute.",
        selected_capability_ids=[TINY_PROVIDER_INVOCATION_CAPABILITY_ID],
        allowed_tool_ids=[TINY_PROVIDER_INVOCATION_CAPABILITY_ID],
        context={
            "provider_ref": request.provider_ref,
            "model_ref": request.model_ref,
            "credential_ref": request.credential_ref,
            "policy_ref": request.policy_ref,
            "approval_scope_ref": request.approval_scope_ref,
            "cost_estimate_ref": request.cost_estimate_ref,
            "budget_decision_ref": request.budget_decision_ref,
            "idempotency_key": request.idempotency_ref,
            "expected_receipt_ref": request.expected_receipt_ref,
        },
    )


def evaluate_tiny_provider_policy_gate(
    request: TinyProviderInvocationRequest,
    *,
    policy_engine: PolicyEngine | None = None,
):
    policy_engine = policy_engine or PolicyEngine(default_max_risk=CapabilityRiskLevel.high)
    return policy_engine.can_execute(
        build_tiny_provider_invocation_policy_manifest(request.policy_ref),
        build_tiny_provider_invocation_policy_task(request),
        {
            "max_risk_level": CapabilityRiskLevel.high.value,
            "auth_scopes": [request.policy_ref],
            "allowed_capability_ids": [TINY_PROVIDER_INVOCATION_CAPABILITY_ID],
            "coordination_mode": CoordinationMode.direct_tool.value,
        },
    )


def required_provider_invocation_resource_refs(
    request: TinyProviderInvocationRequest,
) -> list[str]:
    refs = [
        request.provider_ref,
        request.model_ref,
        request.credential_ref,
        request.policy_ref,
        request.approval_scope_ref,
        request.cost_estimate_ref,
        request.budget_decision_ref,
        request.max_approved_usd_ref,
        request.idempotency_ref,
        request.expected_receipt_ref,
        request.usage_receipt_ref,
        request.cost_receipt_ref,
        request.redacted_input_summary_ref,
        request.redacted_output_summary_ref,
        request.safe_disable_ref,
        _money_scope_ref("estimated-cost-usd-ref", request.estimated_cost_usd),
        _money_scope_ref("max-approved-usd-value-ref", request.max_approved_usd),
        _metered_unit_scope_ref(request),
    ]
    return list(dict.fromkeys(refs))


def evaluate_tiny_provider_invocation(
    request: TinyProviderInvocationRequest,
    *,
    adapter: TinyProviderInvocationAdapter | None = None,
    cost_governor: CostGovernor | None = None,
    policy_engine: PolicyEngine | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    receipt_store: TinyProviderInvocationReceiptStore | None = None,
) -> TinyProviderInvocationDecision:
    adapter = adapter or DisabledTinyProviderInvocationAdapter()
    cost_governor = cost_governor or CostGovernor()
    approval_authority = approval_authority or LocalApprovalAuthority()

    missing_status = _missing_ref_status(request)
    if missing_status is not None:
        return _blocked_decision(
            request,
            status=missing_status,
            reason_codes=[missing_status.value.upper()],
            safe_message="Tiny provider invocation is blocked because an exact required ref is missing.",
            required_next_action="provide_exact_provider_model_credential_cost_budget_and_receipt_refs",
        )
    scope = _tiny_provider_scope(request.provider_ref)
    if scope is None:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.blocked_provider_not_allowed,
            reason_codes=["PROVIDER_REF_NOT_ALLOWED"],
            safe_message="Tiny provider lane is scoped to two named provider refs only.",
            required_next_action="use_an_allowlisted_single_provider_scope_ref",
        )
    if request.model_ref != scope["model_ref"]:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.blocked_model_not_allowed,
            reason_codes=["MODEL_REF_NOT_ALLOWED"],
            safe_message="Tiny provider lane requires the exact model ref for the selected provider scope.",
            required_next_action="use_the_exact_model_ref_for_the_selected_provider_scope",
        )
    if request.policy_ref != scope["policy_ref"]:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.blocked_missing_policy_validation,
            reason_codes=["POLICY_REF_NOT_ALLOWED"],
            safe_message="Tiny provider lane requires the exact PolicyEngine policy ref for the selected provider scope.",
            required_next_action="use_the_exact_policy_ref_for_the_selected_provider_scope",
        )

    estimate = CostEstimate(
        estimate_id=request.cost_estimate_ref,
        input_tokens=request.estimated_input_tokens,
        output_tokens=request.estimated_output_tokens,
        total_tokens=request.estimated_input_tokens + request.estimated_output_tokens,
        estimated_cost_usd=request.estimated_cost_usd,
        estimated_token_cost_usd=request.estimated_cost_usd,
        model_profile_id=request.model_ref,
        provider_id=request.provider_ref,
        unknown_cost=request.estimated_cost_usd is None,
    )
    budget = CostBudget(
        budget_id=request.budget_decision_ref,
        scope=BudgetScope.provider,
        scope_id=request.provider_ref,
        max_cost_usd=request.max_approved_usd,
        max_total_tokens=request.estimated_input_tokens + request.estimated_output_tokens,
        hard_limit=True,
    )
    cost_decision = cost_governor.evaluate(estimate, [budget])
    if estimate.unknown_cost or cost_decision.status == BudgetStatus.approval_required:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.unknown_paid_cost_blocked,
            reason_codes=list(
                dict.fromkeys(
                    [
                        *cost_decision.reason_codes,
                        "UNKNOWN_PAID_COST_BLOCKS",
                    ]
                )
            ),
            safe_message="Unknown paid provider cost is blocked by CostGovernor before invocation.",
            required_next_action="provide_known_cost_estimate_and_budget_decision",
            cost_decision=cost_decision,
        )
    if not cost_decision.allowed:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.cost_blocked,
            reason_codes=list(dict.fromkeys([*cost_decision.reason_codes, "COST_BLOCKED"])),
            safe_message="Provider estimate is above the exact approved budget.",
            required_next_action="lower_cost_or_request_a_new_exact_budget_approval",
            cost_decision=cost_decision,
        )

    policy_decision = evaluate_tiny_provider_policy_gate(
        request,
        policy_engine=policy_engine,
    )
    if (
        policy_decision.status != PolicyDecisionStatus.approval_required
        or not policy_decision.requires_approval
    ):
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.blocked_missing_policy_validation,
            reason_codes=list(
                dict.fromkeys(
                    [
                        *policy_decision.reason_codes,
                        "POLICY_ENGINE_APPROVAL_GATE_REQUIRED",
                    ]
                )
            ),
            safe_message="PolicyEngine must require exact approval before provider lane execution.",
            required_next_action="fix_provider_policy_scope_before_invocation",
            cost_decision=cost_decision,
        )

    approval_request = build_tiny_provider_invocation_approval_request(request)
    approval_decision = approval_authority.validate_for_request(
        approval_request,
        request.approval_ref,
    )
    if not approval_decision.allowed:
        status = (
            TinyProviderInvocationStatus.approval_required
            if "APPROVAL_REF_UNKNOWN" in approval_decision.reason_codes
            else TinyProviderInvocationStatus.approval_invalid
        )
        return _blocked_decision(
            request,
            status=status,
            reason_codes=list(approval_decision.reason_codes),
            safe_message="Exact LocalApprovalAuthority scope is required before provider lane execution.",
            required_next_action="request_exact_local_approval_for_provider_lane",
            cost_decision=cost_decision,
        )

    if receipt_store is not None:
        replay_receipt = receipt_store.find_by_idempotency_ref(request.idempotency_ref)
        if replay_receipt is not None:
            if not _receipt_matches_request(replay_receipt, request):
                return _blocked_decision(
                    request,
                    status=TinyProviderInvocationStatus.approval_invalid,
                    reason_codes=["IDEMPOTENCY_SCOPE_CONFLICT"],
                    safe_message="Tiny provider invocation idempotency ref already has a different receipt scope.",
                    required_next_action="use_a_new_exact_idempotency_ref_for_changed_scope",
                    cost_decision=cost_decision,
                )
            return TinyProviderInvocationDecision(
                decision_ref=f"provider-invocation-decision:{_suffix(request.invocation_ref)}",
                allowed=replay_receipt.status == TinyProviderInvocationStatus.receipt_recorded,
                status=replay_receipt.status,
                reason_codes=list(
                    dict.fromkeys(
                        [*replay_receipt.reason_codes, "IDEMPOTENCY_REPLAYED_RECEIPT"]
                    )
                ),
                safe_message="Tiny provider invocation returned an existing redacted receipt for the exact idempotency ref.",
                cost_decision=cost_decision,
                receipt=replay_receipt,
            )
        blocking_receipt = receipt_store.find_unreviewed_blocking_receipt()
        if blocking_receipt is not None:
            blocking_reason_codes = _receipt_review_block_reason_codes(blocking_receipt)
            return _blocked_decision(
                request,
                status=TinyProviderInvocationStatus.cost_blocked,
                reason_codes=blocking_reason_codes,
                safe_message=(
                    "Provider use is blocked because a prior redacted receipt "
                    "has incomplete usage or actual paid cost metadata awaiting review."
                ),
                required_next_action="review_incomplete_provider_receipt_before_retry",
                cost_decision=cost_decision,
            ).model_copy(update={"receipt": blocking_receipt})

    if not adapter.enabled:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.approved_no_execution,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "TINY_PROVIDER_ADAPTER_DISABLED_BY_DEFAULT",
            ],
            safe_message="Exact approval and cost gates validated, but the tiny provider adapter is disabled by default.",
            required_next_action="keep_provider_adapter_disabled_until_scoped_enablement",
            cost_decision=cost_decision,
        )

    if adapter.requires_receipt_store_before_network and receipt_store is None:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "COST_GOVERNOR_ALLOWED",
                "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIRED",
            ],
            safe_message="Scoped live provider adapter is blocked until durable receipt replay storage is available.",
            required_next_action="provide_tiny_provider_receipt_store_before_live_invocation",
            cost_decision=cost_decision,
        )

    if adapter.may_perform_network_call and not adapter.requires_receipt_store_before_network:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "COST_GOVERNOR_ALLOWED",
                "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIREMENT_REQUIRED",
            ],
            safe_message=(
                "Scoped live provider adapter is blocked because it does not "
                "require durable receipt replay storage before network use."
            ),
            required_next_action=(
                "enforce_tiny_provider_receipt_store_requirement_before_live_invocation"
            ),
            cost_decision=cost_decision,
        )

    request_scope = _tiny_provider_scope_for_request(request)
    if request_scope is None:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.blocked_provider_not_allowed,
            reason_codes=["PROVIDER_SCOPE_NOT_ALLOWED"],
            safe_message="Tiny provider lane requires one exact provider/model/policy scope.",
            required_next_action="use_an_allowlisted_single_provider_scope_ref",
            cost_decision=cost_decision,
        )
    if adapter.may_perform_network_call and adapter.adapter_ref != request_scope["adapter_ref"]:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "COST_GOVERNOR_ALLOWED",
                "TINY_LIVE_PROVIDER_ADAPTER_SCOPE_MISMATCH",
            ],
            safe_message=(
                "Scoped live provider adapter is blocked because its adapter ref "
                "does not match the exact provider/model scope."
            ),
            required_next_action="use_the_exact_live_adapter_for_the_provider_scope",
            cost_decision=cost_decision,
        )
    execution_grant = (
        _build_tiny_provider_execution_grant(request, cost_decision)
        if adapter.adapter_ref == request_scope["adapter_ref"]
        else None
    )
    try:
        if execution_grant is None:
            transport_receipt = adapter.execute(request)
        else:
            transport_receipt = adapter.execute(
                request,
                execution_grant=execution_grant,
            )
    except TypeError:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "COST_GOVERNOR_ALLOWED",
                "TINY_LIVE_PROVIDER_EXECUTION_GRANT_UNSUPPORTED",
            ],
            safe_message=(
                "Scoped live provider adapter is blocked because it cannot "
                "accept the exact execution grant contract."
            ),
            required_next_action="inspect_live_provider_adapter_execution_grant_contract",
            cost_decision=cost_decision,
        )
    transport_scope_reason = _transport_scope_reason(adapter, transport_receipt, receipt_store)
    if transport_scope_reason is not None:
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=[
                "EXACT_APPROVAL_VALIDATED",
                "COST_GOVERNOR_ALLOWED",
                transport_scope_reason,
            ],
            safe_message=(
                "Provider adapter transport was blocked because its network "
                "authority scope did not match the exact live adapter boundary."
            ),
            required_next_action="inspect_provider_adapter_transport_scope_before_retry",
            cost_decision=cost_decision,
        )
    if transport_receipt.status == "blocked":
        blocked_receipt = None
        if transport_receipt.network_call_performed:
            completeness = _receipt_completeness_from_transport(
                transport_receipt,
                status=TinyProviderInvocationStatus.live_adapter_blocked,
            )
            blocked_receipt = _receipt_from_transport(
                request,
                transport_receipt,
                cost_decision=cost_decision,
                status=TinyProviderInvocationStatus.live_adapter_blocked,
                invocation_performed=False,
                reason_codes=[
                    "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
                    "EXACT_APPROVAL_VALIDATED",
                    "COST_GOVERNOR_ALLOWED",
                    transport_receipt.block_reason_code
                    or "LIVE_PROVIDER_ADAPTER_BLOCKED",
                    *completeness["reason_codes"],
                    "REDACTED_BLOCKED_ATTEMPT_RECEIPT_RECORDED",
                ],
                completeness=completeness,
            )
            if receipt_store is not None:
                receipt_store.record(blocked_receipt)
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.live_adapter_blocked,
            reason_codes=list(
                dict.fromkeys(
                    [
                        "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
                        "EXACT_APPROVAL_VALIDATED",
                        "COST_GOVERNOR_ALLOWED",
                        transport_receipt.block_reason_code
                        or "LIVE_PROVIDER_ADAPTER_BLOCKED",
                    ]
                )
            ),
            safe_message=(
                "Exact approval and cost gates validated, but the scoped live "
                "provider adapter blocked before invocation."
            ),
            required_next_action="inspect_live_provider_adapter_posture_and_safe_disable_ref",
            cost_decision=cost_decision,
        ).model_copy(update={"receipt": blocked_receipt})
    completeness = _receipt_completeness_from_transport(
        transport_receipt,
        status=TinyProviderInvocationStatus.cost_blocked,
    )
    if (
        completeness["receipt_completeness_status"]
        != TinyProviderReceiptCompletenessStatus.complete
    ):
        blocked_receipt = _receipt_from_transport(
            request,
            transport_receipt,
            cost_decision=cost_decision,
            status=TinyProviderInvocationStatus.cost_blocked,
            invocation_performed=False,
            reason_codes=list(
                dict.fromkeys(
                    [
                        "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
                        "EXACT_APPROVAL_VALIDATED",
                        "COST_GOVERNOR_ALLOWED",
                        *completeness["reason_codes"],
                        "REDACTED_INCOMPLETE_COST_RECEIPT_RECORDED",
                    ]
                )
            ),
            completeness=completeness,
        )
        if receipt_store is not None:
            receipt_store.record(blocked_receipt)
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.cost_blocked,
            reason_codes=list(
                dict.fromkeys(
                    [
                        "ACTUAL_PROVIDER_COST_INCOMPLETE",
                        *completeness["reason_codes"],
                    ]
                )
            ),
            safe_message=(
                "Provider use is blocked because actual paid cost metadata "
                "was unavailable after the scoped adapter returned."
            ),
            required_next_action="review_incomplete_provider_cost_receipt_before_retry",
            cost_decision=cost_decision,
        ).model_copy(update={"receipt": blocked_receipt})
    actual_estimate = CostEstimate(
        estimate_id=f"{request.cost_estimate_ref}:actual",
        input_tokens=transport_receipt.input_tokens_used,
        output_tokens=transport_receipt.output_tokens_used,
        total_tokens=transport_receipt.input_tokens_used + transport_receipt.output_tokens_used,
        estimated_cost_usd=transport_receipt.billed_cost_usd,
        estimated_token_cost_usd=transport_receipt.billed_cost_usd,
        model_profile_id=request.model_ref,
        provider_id=request.provider_ref,
        unknown_cost=False,
    )
    actual_budget = CostBudget(
        budget_id=request.budget_decision_ref,
        scope=BudgetScope.provider,
        scope_id=request.provider_ref,
        max_cost_usd=request.max_approved_usd,
        max_total_tokens=request.estimated_input_tokens + request.estimated_output_tokens,
        hard_limit=True,
    )
    actual_cost_decision = cost_governor.evaluate(actual_estimate, [actual_budget])
    if not actual_cost_decision.allowed:
        blocked_receipt = None
        if transport_receipt.network_call_performed:
            completeness = _receipt_completeness_from_transport(
                transport_receipt,
                status=TinyProviderInvocationStatus.cost_blocked,
            )
            blocked_receipt = _receipt_from_transport(
                request,
                transport_receipt,
                cost_decision=actual_cost_decision,
                status=TinyProviderInvocationStatus.cost_blocked,
                invocation_performed=False,
                reason_codes=list(
                    dict.fromkeys(
                        [
                            "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
                            "EXACT_APPROVAL_VALIDATED",
                            *actual_cost_decision.reason_codes,
                            "ACTUAL_USAGE_OR_COST_EXCEEDED_APPROVED_SCOPE",
                            *completeness["reason_codes"],
                            "REDACTED_BLOCKED_ATTEMPT_RECEIPT_RECORDED",
                        ]
                    )
                ),
                completeness=completeness,
            )
            if receipt_store is not None:
                receipt_store.record(blocked_receipt)
        return _blocked_decision(
            request,
            status=TinyProviderInvocationStatus.cost_blocked,
            reason_codes=list(
                dict.fromkeys(
                    [
                        *actual_cost_decision.reason_codes,
                        "ACTUAL_USAGE_OR_COST_EXCEEDED_APPROVED_SCOPE",
                    ]
                )
            ),
            safe_message="Provider adapter usage or billed cost exceeded the exact approved budget.",
            required_next_action="review_actual_usage_and_request_new_exact_budget_approval",
            cost_decision=actual_cost_decision,
        ).model_copy(update={"receipt": blocked_receipt})
    receipt = _receipt_from_transport(
        request,
        transport_receipt,
        cost_decision=actual_cost_decision,
        status=TinyProviderInvocationStatus.receipt_recorded,
        invocation_performed=True,
        reason_codes=[
            "POLICY_ENGINE_APPROVAL_GATE_VALIDATED",
            "EXACT_APPROVAL_VALIDATED",
            "COST_GOVERNOR_ALLOWED",
            "USAGE_AND_ESTIMATED_COST_RECONCILED",
            "REDACTED_RECEIPT_RECORDED",
        ],
        completeness=_receipt_completeness_from_transport(
            transport_receipt,
            status=TinyProviderInvocationStatus.receipt_recorded,
        ),
    )
    if receipt_store is not None:
        receipt_store.record(receipt)
    return TinyProviderInvocationDecision(
        decision_ref=f"provider-invocation-decision:{_suffix(request.invocation_ref)}",
        allowed=True,
        status=TinyProviderInvocationStatus.receipt_recorded,
        reason_codes=list(receipt.reason_codes),
        safe_message="Tiny exact-approved provider lane produced a redacted receipt.",
        cost_decision=actual_cost_decision,
        receipt=receipt,
    )


def _missing_ref_status(
    request: TinyProviderInvocationRequest,
) -> TinyProviderInvocationStatus | None:
    checks: list[tuple[str | None, TinyProviderInvocationStatus]] = [
        (request.provider_ref, TinyProviderInvocationStatus.blocked_missing_provider_ref),
        (request.model_ref, TinyProviderInvocationStatus.blocked_missing_model_ref),
        (request.credential_ref, TinyProviderInvocationStatus.blocked_missing_credential_ref),
        (request.policy_ref, TinyProviderInvocationStatus.blocked_missing_policy_validation),
        (request.cost_estimate_ref, TinyProviderInvocationStatus.blocked_missing_cost_estimate_ref),
        (
            request.budget_decision_ref,
            TinyProviderInvocationStatus.blocked_missing_budget_decision_ref,
        ),
        (
            request.max_approved_usd_ref,
            TinyProviderInvocationStatus.blocked_missing_max_approved_usd,
        ),
        (
            request.expected_receipt_ref,
            TinyProviderInvocationStatus.blocked_missing_expected_receipt_ref,
        ),
    ]
    for ref, status in checks:
        if _ref_is_missing(ref):
            return status
    if request.max_approved_usd is None:
        return TinyProviderInvocationStatus.blocked_missing_max_approved_usd
    return None


def _blocked_decision(
    request: TinyProviderInvocationRequest,
    *,
    status: TinyProviderInvocationStatus,
    reason_codes: list[str],
    safe_message: str,
    required_next_action: str,
    cost_decision: CostDecision | None = None,
) -> TinyProviderInvocationDecision:
    return TinyProviderInvocationDecision(
        decision_ref=f"provider-invocation-decision:{_suffix(request.invocation_ref)}",
        allowed=False,
        status=status,
        reason_codes=reason_codes,
        safe_message=safe_message,
        required_next_action=required_next_action,
        cost_decision=cost_decision,
    )


def _build_tiny_provider_execution_grant(
    request: TinyProviderInvocationRequest,
    cost_decision: CostDecision,
) -> TinyProviderInvocationExecutionGrant:
    scope = _tiny_provider_scope_for_request(request)
    if scope is None:
        raise ValueError("TINY_PROVIDER_INVOCATION_EXECUTION_GRANT_SCOPE_DENIED")
    grant = TinyProviderInvocationExecutionGrant(
        adapter_ref=scope["adapter_ref"],
        provider_ref=request.provider_ref,
        model_ref=request.model_ref,
        credential_ref=request.credential_ref,
        policy_ref=request.policy_ref,
        approval_ref=request.approval_ref,
        approval_scope_ref=request.approval_scope_ref,
        cost_estimate_ref=request.cost_estimate_ref,
        budget_decision_ref=request.budget_decision_ref,
        expected_receipt_ref=request.expected_receipt_ref,
        cost_governor_decision_ref=cost_decision.decision_id,
        receipt_store_required=True,
    )
    grant._runtime_authority_token = _TINY_PROVIDER_EXECUTION_GRANT_TOKEN
    return grant


def _transport_scope_reason(
    adapter: TinyProviderInvocationAdapter,
    transport_receipt: TinyProviderInvocationTransportReceipt,
    receipt_store: TinyProviderInvocationReceiptStore | None,
) -> str | None:
    if transport_receipt.adapter_ref != adapter.adapter_ref:
        return "TINY_PROVIDER_TRANSPORT_ADAPTER_REF_MISMATCH"
    if not transport_receipt.network_call_performed:
        return None
    scope = _tiny_provider_scope_for_transport(transport_receipt)
    if scope is None:
        return "TINY_LIVE_PROVIDER_SCOPE_REQUIRED"
    if adapter.adapter_ref != scope["adapter_ref"]:
        return "TINY_LIVE_PROVIDER_ADAPTER_SCOPE_REQUIRED"
    if transport_receipt.transport_ref != scope["transport_ref"]:
        return "TINY_LIVE_PROVIDER_TRANSPORT_SCOPE_REQUIRED"
    if not adapter.may_perform_network_call:
        return "TINY_LIVE_PROVIDER_ADAPTER_NETWORK_FLAG_REQUIRED"
    if not adapter.requires_receipt_store_before_network:
        return "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIREMENT_REQUIRED"
    if receipt_store is None:
        return "TINY_LIVE_PROVIDER_RECEIPT_STORE_REQUIRED"
    return None


def _receipt_from_transport(
    request: TinyProviderInvocationRequest,
    transport_receipt: TinyProviderInvocationTransportReceipt,
    *,
    cost_decision: CostDecision,
    status: TinyProviderInvocationStatus,
    invocation_performed: bool,
    reason_codes: list[str],
    completeness: dict[str, object] | None = None,
) -> TinyProviderInvocationReceipt:
    completeness = completeness or _receipt_completeness_from_transport(
        transport_receipt,
        status=status,
    )
    return TinyProviderInvocationReceipt(
        receipt_ref=request.expected_receipt_ref,
        invocation_ref=request.invocation_ref,
        run_id=request.run_id,
        provider_ref=request.provider_ref,
        model_ref=request.model_ref,
        adapter_ref=transport_receipt.adapter_ref,
        credential_ref=request.credential_ref,
        approval_ref=request.approval_ref,
        approval_scope_ref=request.approval_scope_ref,
        cost_estimate_ref=request.cost_estimate_ref,
        budget_decision_ref=request.budget_decision_ref,
        max_approved_usd_ref=request.max_approved_usd_ref,
        expected_receipt_ref=request.expected_receipt_ref,
        usage_receipt_ref=transport_receipt.usage_receipt_ref,
        cost_receipt_ref=transport_receipt.cost_receipt_ref,
        cost_governor_decision_ref=cost_decision.decision_id,
        estimated_cost_ref=request.cost_estimate_ref,
        actual_usage_ref=_actual_usage_ref(request),
        actual_cost_ref=_actual_cost_ref(request),
        idempotency_ref=request.idempotency_ref,
        redacted_input_summary_ref=request.redacted_input_summary_ref,
        redacted_output_summary_ref=transport_receipt.redacted_output_summary_ref,
        safe_disable_ref=request.safe_disable_ref,
        status=status,
        invocation_performed=invocation_performed,
        provider_sdk_used=transport_receipt.provider_sdk_used,
        network_call_performed=transport_receipt.network_call_performed,
        input_tokens_used=transport_receipt.input_tokens_used,
        output_tokens_used=transport_receipt.output_tokens_used,
        estimated_cost_usd=request.estimated_cost_usd,
        billed_cost_usd=transport_receipt.billed_cost_usd,
        actual_usage_captured=bool(completeness["actual_usage_captured"]),
        actual_cost_captured=bool(completeness["actual_cost_captured"]),
        receipt_completeness_status=completeness["receipt_completeness_status"],
        incomplete_cost_requires_review=bool(
            completeness["incomplete_cost_requires_review"]
        ),
        further_provider_use_blocked=bool(
            completeness["further_provider_use_blocked"]
        ),
        reason_codes=reason_codes,
        safe_summary=TINY_PROVIDER_RECEIPT_SUMMARY,
    )


def _receipt_completeness_from_transport(
    transport_receipt: TinyProviderInvocationTransportReceipt,
    *,
    status: TinyProviderInvocationStatus,
) -> dict[str, object]:
    usage_captured = (
        not transport_receipt.network_call_performed
        or transport_receipt.input_tokens_used > 0
        or transport_receipt.output_tokens_used > 0
    )
    cost_incomplete = (
        transport_receipt.network_call_performed
        and status != TinyProviderInvocationStatus.receipt_recorded
        and (
            transport_receipt.block_reason_code
            == "TINY_LIVE_PROVIDER_BILLED_COST_UNAVAILABLE"
            or transport_receipt.billed_cost_usd == 0
        )
    )
    usage_incomplete = transport_receipt.network_call_performed and not usage_captured
    if cost_incomplete:
        return {
            "actual_usage_captured": usage_captured,
            "actual_cost_captured": False,
            "receipt_completeness_status": (
                TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review
            ),
            "incomplete_cost_requires_review": True,
            "further_provider_use_blocked": True,
            "reason_codes": [
                "ACTUAL_COST_INCOMPLETE",
                "INCOMPLETE_COST_REQUIRES_REVIEW",
                "FURTHER_PROVIDER_USE_BLOCKED",
            ],
        }
    if usage_incomplete:
        return {
            "actual_usage_captured": False,
            "actual_cost_captured": True,
            "receipt_completeness_status": (
                TinyProviderReceiptCompletenessStatus.incomplete_usage_requires_review
            ),
            "incomplete_cost_requires_review": False,
            "further_provider_use_blocked": True,
            "reason_codes": [
                "ACTUAL_USAGE_INCOMPLETE",
                "REVIEW_REQUIRED",
                "FURTHER_PROVIDER_USE_BLOCKED",
            ],
        }
    return {
        "actual_usage_captured": True,
        "actual_cost_captured": True,
        "receipt_completeness_status": TinyProviderReceiptCompletenessStatus.complete,
        "incomplete_cost_requires_review": False,
        "further_provider_use_blocked": False,
        "reason_codes": ["ACTUAL_USAGE_CAPTURED", "ACTUAL_COST_CAPTURED"],
    }


def _receipt_review_block_reason_codes(
    receipt: TinyProviderInvocationReceipt,
) -> list[str]:
    reason_codes = []
    if receipt.incomplete_cost_requires_review:
        reason_codes.append("INCOMPLETE_COST_REQUIRES_REVIEW")
    if (
        receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.incomplete_usage_requires_review
    ):
        reason_codes.extend(["ACTUAL_USAGE_INCOMPLETE", "REVIEW_REQUIRED"])
    reason_codes.append("FURTHER_PROVIDER_USE_BLOCKED")
    return list(dict.fromkeys(reason_codes))


def _normalize_receipt_payload_for_replay(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("TINY_PROVIDER_INVOCATION_RECEIPT_STORE_PAYLOAD_DENIED")
    normalized = dict(payload)
    normalized["reason_codes"] = _sanitize_reason_codes(
        normalized.get("reason_codes"),
        fallback="REDACTED_LEGACY_RECEIPT_REASON",
    )
    required_completeness_fields = {
        "estimated_cost_ref",
        "actual_usage_ref",
        "actual_cost_ref",
        "actual_usage_captured",
        "actual_cost_captured",
        "receipt_completeness_status",
        "incomplete_cost_requires_review",
        "further_provider_use_blocked",
    }
    if required_completeness_fields.issubset(normalized):
        review_reasons = _replayed_receipt_completeness_review_reasons(normalized)
        if review_reasons:
            return _mark_replayed_receipt_payload_review_blocked(
                normalized,
                reason_codes=review_reasons,
            )
        return normalized
    return _mark_replayed_receipt_payload_review_blocked(
        normalized,
        reason_codes=["LEGACY_RECEIPT_COMPLETENESS_MISSING"],
    )


def _mark_replayed_receipt_payload_review_blocked(
    normalized: dict[str, object],
    *,
    reason_codes: list[str],
) -> dict[str, object]:
    cost_estimate_ref = str(normalized.get("cost_estimate_ref", "missing"))
    usage_receipt_ref = str(normalized.get("usage_receipt_ref", "missing"))
    cost_receipt_ref = str(normalized.get("cost_receipt_ref", "missing"))
    existing_reasons = _sanitize_reason_codes(
        normalized.get("reason_codes"),
        fallback="REDACTED_LEGACY_RECEIPT_REASON",
    )
    normalized.update(
        {
            "estimated_cost_ref": cost_estimate_ref,
            "actual_usage_ref": (
                f"actual-usage-ref:provider-runtime:{_suffix(usage_receipt_ref)}"
            ),
            "actual_cost_ref": (
                f"actual-cost-ref:provider-runtime:{_suffix(cost_receipt_ref)}"
            ),
            "status": TinyProviderInvocationStatus.cost_blocked.value,
            "invocation_performed": False,
            "actual_usage_captured": _receipt_payload_has_usage(normalized),
            "actual_cost_captured": False,
            "receipt_completeness_status": (
                TinyProviderReceiptCompletenessStatus.incomplete_cost_requires_review.value
            ),
            "incomplete_cost_requires_review": True,
            "further_provider_use_blocked": True,
            "reason_codes": list(
                dict.fromkeys(
                    [
                        *existing_reasons,
                        *reason_codes,
                        "ACTUAL_COST_INCOMPLETE",
                        "INCOMPLETE_COST_REQUIRES_REVIEW",
                        "FURTHER_PROVIDER_USE_BLOCKED",
                    ]
                )
            ),
        }
    )
    return normalized


def _receipt_payload_has_usage(payload: dict[str, object]) -> bool:
    for field_name in ("input_tokens_used", "output_tokens_used"):
        try:
            if int(payload.get(field_name) or 0) > 0:
                return True
        except (TypeError, ValueError):
            return False
    return False


def _receipt_payload_cost_is_missing(payload: dict[str, object]) -> bool:
    try:
        billed_cost = float(payload.get("billed_cost_usd") or 0)
    except (TypeError, ValueError):
        return True
    return billed_cost <= 0


def _replayed_receipt_completeness_review_reasons(
    payload: dict[str, object],
) -> list[str]:
    reasons: list[str] = []
    usage_receipt_ref = str(payload.get("usage_receipt_ref", "missing"))
    cost_receipt_ref = str(payload.get("cost_receipt_ref", "missing"))
    if payload.get("actual_usage_ref") != (
        f"actual-usage-ref:provider-runtime:{_suffix(usage_receipt_ref)}"
    ):
        reasons.append("REPLAYED_RECEIPT_ACTUAL_USAGE_REF_MISMATCH")
    if payload.get("actual_cost_ref") != (
        f"actual-cost-ref:provider-runtime:{_suffix(cost_receipt_ref)}"
    ):
        reasons.append("REPLAYED_RECEIPT_ACTUAL_COST_REF_MISMATCH")
    if (
        payload.get("status") == TinyProviderInvocationStatus.receipt_recorded.value
        and payload.get("receipt_completeness_status")
        == TinyProviderReceiptCompletenessStatus.complete.value
    ):
        if payload.get("network_call_performed") and _receipt_payload_cost_is_missing(
            payload
        ):
            reasons.append("REPLAYED_RECEIPT_ACTUAL_COST_MISSING")
        if payload.get("actual_usage_captured") is not True:
            reasons.append("REPLAYED_RECEIPT_ACTUAL_USAGE_CAPTURE_MISSING")
        if payload.get("actual_cost_captured") is not True:
            reasons.append("REPLAYED_RECEIPT_ACTUAL_COST_CAPTURE_MISSING")
    return reasons


def _actual_usage_ref(request: TinyProviderInvocationRequest) -> str:
    return f"actual-usage-ref:provider-runtime:{_suffix(request.usage_receipt_ref)}"


def _actual_cost_ref(request: TinyProviderInvocationRequest) -> str:
    return f"actual-cost-ref:provider-runtime:{_suffix(request.cost_receipt_ref)}"


def _receipt_matches_request(
    receipt: TinyProviderInvocationReceipt,
    request: TinyProviderInvocationRequest,
) -> bool:
    expected = {
        "receipt_ref": request.expected_receipt_ref,
        "invocation_ref": request.invocation_ref,
        "run_id": request.run_id,
        "provider_ref": request.provider_ref,
        "model_ref": request.model_ref,
        "credential_ref": request.credential_ref,
        "approval_ref": request.approval_ref,
        "approval_scope_ref": request.approval_scope_ref,
        "cost_estimate_ref": request.cost_estimate_ref,
        "budget_decision_ref": request.budget_decision_ref,
        "max_approved_usd_ref": request.max_approved_usd_ref,
        "expected_receipt_ref": request.expected_receipt_ref,
        "usage_receipt_ref": request.usage_receipt_ref,
        "cost_receipt_ref": request.cost_receipt_ref,
        "estimated_cost_ref": request.cost_estimate_ref,
        "actual_usage_ref": _actual_usage_ref(request),
        "actual_cost_ref": _actual_cost_ref(request),
        "idempotency_ref": request.idempotency_ref,
        "redacted_input_summary_ref": request.redacted_input_summary_ref,
        "redacted_output_summary_ref": request.redacted_output_summary_ref,
        "safe_disable_ref": request.safe_disable_ref,
    }
    for field_name, expected_value in expected.items():
        if getattr(receipt, field_name) != expected_value:
            return False
    if (
        receipt.status == TinyProviderInvocationStatus.receipt_recorded
        and receipt.network_call_performed
        and (receipt.billed_cost_usd is None or receipt.billed_cost_usd <= 0)
    ):
        return False
    return receipt.estimated_cost_usd == request.estimated_cost_usd


def _suffix(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")
    return normalized[-48:] or "local"


def _money_scope_ref(prefix: str, value: float | None) -> str:
    if value is None:
        return f"{prefix}:unknown"
    normalized = f"{value:.6f}".rstrip("0").rstrip(".")
    return f"{prefix}:usd-{normalized or '0'}"


def _metered_unit_scope_ref(request: TinyProviderInvocationRequest) -> str:
    total_tokens = request.estimated_input_tokens + request.estimated_output_tokens
    return (
        "metered-unit-estimate-ref:"
        f"input-{request.estimated_input_tokens}:"
        f"output-{request.estimated_output_tokens}:"
        f"total-{total_tokens}"
    )


def _actor_context_is_local_operator(actor_context: ActorContext) -> bool:
    return (
        actor_context.actor_type in (ActorType.human_user, ActorType.human_user.value)
        and actor_context.actor_id == "operator:local"
        and actor_context.authority_source in (
            AuthoritySource.manual_operator_action,
            AuthoritySource.manual_operator_action.value,
        )
        and actor_context.actor_display_name is None
        and actor_context.on_behalf_of_user_id is None
        and actor_context.workspace_id is None
        and actor_context.project_id is None
        and actor_context.execution_contract_id is None
        and actor_context.consent_ref is None
        and actor_context.approval_ref is None
        and actor_context.session_id is None
    )
