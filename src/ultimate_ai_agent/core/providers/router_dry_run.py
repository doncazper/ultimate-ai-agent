from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


PROVIDER_ROUTER_DRY_RUN_ROUTE = "/control-center/providers/router/dry-run"
PROVIDER_ROUTER_DRY_RUN_CONTRACT_REF = "provider-router-dry-run:proposal-only:v1"
PROVIDER_ROUTER_DRY_RUN_POLICY_REF = "policy-ref:provider-router:dry-run-only:v1"

_SAFE_REF_PREFIXES = (
    "approval-scope-ref:",
    "budget-decision-ref:",
    "capability-ref:",
    "cost-decision-ref:",
    "cost-estimate-ref:",
    "cost-governor-decision-ref:",
    "cost-governor-posture-ref:",
    "credential-ref:",
    "idempotency-ref:",
    "model-need-ref:",
    "model-ref:",
    "policy-ref:",
    "provider-manifest-ref:",
    "provider:",
    "provider-ref:",
    "provider-router-proposal-ref:",
    "provider-router-run-ref:",
    "receipt-ref:",
    "route-ref:",
    "task-ref:",
    "validation-ref:",
)


class ProviderRouterDryRunProviderStatus(str, Enum):
    eligible = "eligible"
    blocked = "blocked"
    degraded = "degraded"
    cost_risky = "cost_risky"


class _ProviderRouterDryRunModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


def _safe_ref_matches(value: str) -> bool:
    if not any(value.startswith(prefix) for prefix in _SAFE_REF_PREFIXES):
        return False
    return all(char.isalnum() or char in {":", "-", "_", "."} for char in value)


def _require_safe_refs(values: Iterable[str], error_code: str) -> None:
    for value in values:
        if not value or not _safe_ref_matches(value):
            raise ValueError(error_code)


def _ref_is_missing(value: str | None) -> bool:
    if value is None or not value.strip():
        return True
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in (
            ":missing",
            "not-bound",
            "not-configured",
            "not-selected",
            "reference_missing",
            "required",
        )
    )


def _reason_code(value: str) -> bool:
    return 1 <= len(value) <= 120 and all(
        char.isupper() or char.isdigit() or char == "_" for char in value
    )


def _slug_from_provider_ref(provider_ref: str) -> str:
    parts = [part for part in provider_ref.split(":") if part]
    if len(parts) >= 2:
        return parts[1]
    return "provider-runtime"


def _safe_get(value: object, field_name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


class ProviderRouterDryRunNeed(_ProviderRouterDryRunModel):
    task_ref: str = "task-ref:provider-router:local-review"
    model_need_ref: str = "model-need-ref:provider-router:text-generation"
    cost_posture_ref: str = "cost-governor-posture-ref:provider-router:required"
    validation_posture_ref: str = "validation-ref:provider-router:required"
    required_capability_refs: list[str] = Field(
        default_factory=lambda: ["capability-ref:provider-router:model-text"]
    )
    safe_refs_only: bool = True
    raw_task_content_included: bool = False
    prompt_content_included: bool = False
    response_content_included: bool = False
    provider_payload_included: bool = False
    invocation_requested: bool = False
    fallback_execution_requested: bool = False
    provider_sdk_call_requested: bool = False
    credential_validation_requested: bool = False
    model_call_requested: bool = False
    billing_authority_requested: bool = False
    background_execution_requested: bool = False

    @model_validator(mode="after")
    def need_must_remain_safe_ref_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTER_DRY_RUN_NEED_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.task_ref,
                self.model_need_ref,
                self.cost_posture_ref,
                self.validation_posture_ref,
                *self.required_capability_refs,
            ],
            "PROVIDER_ROUTER_DRY_RUN_NEED_REF_REQUIRED",
        )
        if not self.safe_refs_only:
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_NEED_SAFE_REFS_REQUIRED")
        denied_flags = [
            self.raw_task_content_included,
            self.prompt_content_included,
            self.response_content_included,
            self.provider_payload_included,
            self.invocation_requested,
            self.fallback_execution_requested,
            self.provider_sdk_call_requested,
            self.credential_validation_requested,
            self.model_call_requested,
            self.billing_authority_requested,
            self.background_execution_requested,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_NEED_EXECUTION_DENIED")
        return self


class ProviderRouterDryRunRequest(_ProviderRouterDryRunModel):
    router_run_ref: str = "provider-router-run-ref:dry-run:local"
    idempotency_ref: str = "idempotency-ref:provider-router:dry-run:local"
    need: ProviderRouterDryRunNeed = Field(default_factory=ProviderRouterDryRunNeed)
    candidate_provider_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    proposal_only: bool = True
    local_state_only: bool = True
    invocation_requested: bool = False
    fallback_execution_requested: bool = False
    network_call_requested: bool = False
    provider_sdk_call_requested: bool = False
    credential_validation_requested: bool = False
    model_call_requested: bool = False
    billing_authority_requested: bool = False
    autonomous_background_execution_requested: bool = False

    @model_validator(mode="after")
    def request_must_remain_dry_run_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTER_DRY_RUN_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.router_run_ref,
                self.idempotency_ref,
                *self.candidate_provider_refs,
            ],
            "PROVIDER_ROUTER_DRY_RUN_REQUEST_REF_REQUIRED",
        )
        if not self.safe_refs_only or not self.proposal_only or not self.local_state_only:
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_REQUEST_POSTURE_DENIED")
        denied_flags = [
            self.invocation_requested,
            self.fallback_execution_requested,
            self.network_call_requested,
            self.provider_sdk_call_requested,
            self.credential_validation_requested,
            self.model_call_requested,
            self.billing_authority_requested,
            self.autonomous_background_execution_requested,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_REQUEST_EXECUTION_DENIED")
        return self


class ProviderRouterDryRunRecommendedScope(_ProviderRouterDryRunModel):
    approval_scope_ref: str = "approval-scope-ref:provider-router:exact-scope-required"
    policy_ref: str = PROVIDER_ROUTER_DRY_RUN_POLICY_REF
    cost_estimate_ref: str = "cost-estimate-ref:provider-router:required"
    budget_decision_ref: str = "budget-decision-ref:provider-router:required"
    expected_receipt_ref: str = "receipt-ref:provider-router:future-required"
    exact_scope_required: bool = True
    provider_ref_required: bool = True
    model_ref_required: bool = True
    credential_ref_required: bool = True
    cost_governor_decision_required: bool = True
    max_approved_usd_required: bool = True
    idempotency_ref_required: bool = True
    receipt_ref_required: bool = True
    execution_authorized_by_scope: bool = False

    @model_validator(mode="after")
    def scope_must_not_authorize_execution(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTER_DRY_RUN_SCOPE_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.approval_scope_ref,
                self.policy_ref,
                self.cost_estimate_ref,
                self.budget_decision_ref,
                self.expected_receipt_ref,
            ],
            "PROVIDER_ROUTER_DRY_RUN_SCOPE_REF_REQUIRED",
        )
        required_flags = [
            self.exact_scope_required,
            self.provider_ref_required,
            self.model_ref_required,
            self.credential_ref_required,
            self.cost_governor_decision_required,
            self.max_approved_usd_required,
            self.idempotency_ref_required,
            self.receipt_ref_required,
        ]
        if not all(required_flags) or self.execution_authorized_by_scope:
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_SCOPE_AUTHORITY_DENIED")
        return self


class ProviderRouterDryRunProviderProposal(_ProviderRouterDryRunModel):
    provider_ref: str
    provider_label: str = Field(..., min_length=1)
    provider_manifest_ref: str
    model_ref: str
    credential_ref: str
    credential_ref_status: str = "reference_missing"
    status: ProviderRouterDryRunProviderStatus
    readiness_status: str = "blocked_reference_only"
    eligible_for_exact_approval_scope: bool = False
    missing_credential_ref: str
    cost_risk_ref: str
    validation_required_ref: str
    no_authority_ref: str
    recommended_approval_scope_ref: str
    reason_codes: list[str] = Field(default_factory=list)
    proposal_only: bool = True
    execution_authorized: bool = False
    fallback_execution_authorized: bool = False
    network_call_performed: bool = False
    provider_sdk_call_performed: bool = False
    credential_validation_performed: bool = False
    model_invocation_performed: bool = False
    billing_authority_granted: bool = False
    provider_output_authoritative: bool = False

    @model_validator(mode="after")
    def provider_proposal_must_not_execute(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTER_DRY_RUN_PROVIDER_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.provider_ref,
                self.provider_manifest_ref,
                self.model_ref,
                self.credential_ref,
                self.missing_credential_ref,
                self.cost_risk_ref,
                self.validation_required_ref,
                self.no_authority_ref,
                self.recommended_approval_scope_ref,
            ],
            "PROVIDER_ROUTER_DRY_RUN_PROVIDER_REF_REQUIRED",
        )
        if self.status == ProviderRouterDryRunProviderStatus.eligible and not (
            self.eligible_for_exact_approval_scope
        ):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_PROVIDER_ELIGIBLE_SCOPE_REQUIRED")
        if self.status != ProviderRouterDryRunProviderStatus.eligible and (
            self.eligible_for_exact_approval_scope
        ):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_PROVIDER_ELIGIBLE_SCOPE_MISMATCH")
        denied_flags = [
            not self.proposal_only,
            self.execution_authorized,
            self.fallback_execution_authorized,
            self.network_call_performed,
            self.provider_sdk_call_performed,
            self.credential_validation_performed,
            self.model_invocation_performed,
            self.billing_authority_granted,
            self.provider_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_PROVIDER_AUTHORITY_DENIED")
        if not self.reason_codes or not all(_reason_code(code) for code in self.reason_codes):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_PROVIDER_REASON_CODES_REQUIRED")
        return self


class ProviderRouterDryRunProposal(_ProviderRouterDryRunModel):
    contract_ref: str = PROVIDER_ROUTER_DRY_RUN_CONTRACT_REF
    route_ref: str = f"POST {PROVIDER_ROUTER_DRY_RUN_ROUTE}"
    proposal_ref: str
    router_run_ref: str
    idempotency_ref: str
    status: Literal["proposal_only"] = "proposal_only"
    safe_summary: str = (
        "Provider router dry-run explains exact-approval candidate, blocked, degraded, "
        "and cost-risky provider refs without provider invocation, fallback execution, "
        "provider SDK calls, credential validation, model calls, billing authority, "
        "or background work."
    )
    safe_refs_only: bool = True
    proposal_only: bool = True
    local_state_only: bool = True
    invocation_authorized: bool = False
    fallback_execution_authorized: bool = False
    network_call_performed: bool = False
    provider_sdk_call_performed: bool = False
    credential_validation_performed: bool = False
    model_invocation_performed: bool = False
    billing_authority_granted: bool = False
    autonomous_background_execution_enabled: bool = False
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    provider_payload_content_persisted: bool = False
    provider_proposals: list[ProviderRouterDryRunProviderProposal] = Field(
        default_factory=list
    )
    eligible_provider_refs: list[str] = Field(default_factory=list)
    blocked_provider_refs: list[str] = Field(default_factory=list)
    degraded_provider_refs: list[str] = Field(default_factory=list)
    missing_credential_refs: list[str] = Field(default_factory=list)
    cost_risky_refs: list[str] = Field(default_factory=list)
    validation_required_refs: list[str] = Field(default_factory=list)
    no_authority_refs: list[str] = Field(default_factory=list)
    recommended_exact_approval_scope_ref: str = (
        "approval-scope-ref:provider-router:exact-scope-required"
    )
    recommended_exact_approval_scope: ProviderRouterDryRunRecommendedScope = Field(
        default_factory=ProviderRouterDryRunRecommendedScope
    )
    ui_states: list[str] = Field(
        default_factory=lambda: [
            "Provider router dry-run",
            "Proposal only",
            "Exact-approval candidate refs",
            "Blocked provider refs",
            "Degraded provider refs",
            "Cost risky",
            "Validation required",
            "No provider authority",
            "No fallback execution",
        ]
    )
    blocker_codes: list[str] = Field(
        default_factory=lambda: [
            "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY",
            "NO_PROVIDER_INVOCATION",
            "NO_FALLBACK_EXECUTION",
            "NO_NETWORK_CALLS",
            "NO_PROVIDER_SDK_CALL",
            "NO_CREDENTIAL_VALIDATION",
            "NO_MODEL_CALL",
            "NO_BILLING_AUTHORITY",
            "NO_AUTONOMOUS_BACKGROUND_CALLS",
            "COSTGOVERNOR_REQUIRED_BEFORE_INVOCATION",
            "UNKNOWN_PAID_COST_BLOCKS",
            "EXACT_APPROVAL_SCOPE_REQUIRED_FOR_ANY_FUTURE_USE",
        ]
    )

    @model_validator(mode="after")
    def proposal_must_remain_non_authorizing(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.proposal_ref,
                self.router_run_ref,
                self.idempotency_ref,
                self.recommended_exact_approval_scope_ref,
                *self.eligible_provider_refs,
                *self.blocked_provider_refs,
                *self.degraded_provider_refs,
                *self.missing_credential_refs,
                *self.cost_risky_refs,
                *self.validation_required_refs,
                *self.no_authority_refs,
            ],
            "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_REF_REQUIRED",
        )
        expected_provider_refs = {
            proposal.provider_ref
            for proposal in self.provider_proposals
            if proposal.status == ProviderRouterDryRunProviderStatus.eligible
        }
        if set(self.eligible_provider_refs) != expected_provider_refs:
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_ELIGIBLE_REFS_MISMATCH")
        denied_flags = [
            not self.safe_refs_only,
            not self.proposal_only,
            not self.local_state_only,
            self.invocation_authorized,
            self.fallback_execution_authorized,
            self.network_call_performed,
            self.provider_sdk_call_performed,
            self.credential_validation_performed,
            self.model_invocation_performed,
            self.billing_authority_granted,
            self.autonomous_background_execution_enabled,
            self.prompt_content_persisted,
            self.response_content_persisted,
            self.provider_payload_content_persisted,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_AUTHORITY_DENIED")
        required_ui_states = {
            "Provider router dry-run",
            "Proposal only",
            "Exact-approval candidate refs",
            "Blocked provider refs",
            "Degraded provider refs",
            "Cost risky",
            "Validation required",
            "No provider authority",
            "No fallback execution",
        }
        if set(self.ui_states) != required_ui_states:
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_UI_STATES_REQUIRED")
        required_blockers = {
            "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY",
            "NO_PROVIDER_INVOCATION",
            "NO_FALLBACK_EXECUTION",
            "NO_NETWORK_CALLS",
            "NO_PROVIDER_SDK_CALL",
            "NO_CREDENTIAL_VALIDATION",
            "NO_MODEL_CALL",
            "NO_BILLING_AUTHORITY",
            "NO_AUTONOMOUS_BACKGROUND_CALLS",
            "COSTGOVERNOR_REQUIRED_BEFORE_INVOCATION",
            "UNKNOWN_PAID_COST_BLOCKS",
            "EXACT_APPROVAL_SCOPE_REQUIRED_FOR_ANY_FUTURE_USE",
        }
        if not required_blockers.issubset(set(self.blocker_codes)):
            raise ValueError("PROVIDER_ROUTER_DRY_RUN_BLOCKER_CODES_REQUIRED")
        return self


def build_provider_router_dry_run_request() -> ProviderRouterDryRunRequest:
    return ProviderRouterDryRunRequest()


def evaluate_provider_router_dry_run(
    request: ProviderRouterDryRunRequest,
    *,
    provider_readiness_items: Iterable[object] = (),
) -> ProviderRouterDryRunProposal:
    proposals = [
        _proposal_from_provider_readiness(item, request)
        for item in provider_readiness_items
        if not request.candidate_provider_refs
        or _safe_get(item, "provider_id", "") in request.candidate_provider_refs
    ]
    eligible_provider_refs = [
        proposal.provider_ref
        for proposal in proposals
        if proposal.status == ProviderRouterDryRunProviderStatus.eligible
    ]
    return ProviderRouterDryRunProposal(
        proposal_ref=_proposal_ref_for_run(request.router_run_ref),
        router_run_ref=request.router_run_ref,
        idempotency_ref=request.idempotency_ref,
        provider_proposals=proposals,
        eligible_provider_refs=eligible_provider_refs,
        blocked_provider_refs=[
            proposal.provider_ref
            for proposal in proposals
            if proposal.status == ProviderRouterDryRunProviderStatus.blocked
        ],
        degraded_provider_refs=[
            proposal.provider_ref
            for proposal in proposals
            if proposal.status == ProviderRouterDryRunProviderStatus.degraded
        ],
        missing_credential_refs=[
            proposal.missing_credential_ref
            for proposal in proposals
            if "CREDENTIAL_REFERENCE_NOT_BOUND" in proposal.reason_codes
        ],
        cost_risky_refs=[
            proposal.cost_risk_ref
            for proposal in proposals
            if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in proposal.reason_codes
            or "COST_RISK_REVIEW_REQUIRED" in proposal.reason_codes
        ],
        validation_required_refs=[
            proposal.validation_required_ref
            for proposal in proposals
            if "CREDENTIAL_VALIDATION_REQUIRED_BEFORE_INVOCATION"
            in proposal.reason_codes
        ],
        no_authority_refs=[proposal.no_authority_ref for proposal in proposals],
    )


def build_provider_router_dry_run_readiness(
    *,
    provider_readiness_items: Iterable[object] = (),
) -> ProviderRouterDryRunProposal:
    return evaluate_provider_router_dry_run(
        build_provider_router_dry_run_request(),
        provider_readiness_items=provider_readiness_items,
    )


def _proposal_ref_for_run(router_run_ref: str) -> str:
    token = router_run_ref.removeprefix("provider-router-run-ref:")
    token = token.replace(":", "-")
    return f"provider-router-proposal-ref:{token}:proposal-only"


def _proposal_from_provider_readiness(
    item: object,
    request: ProviderRouterDryRunRequest,
) -> ProviderRouterDryRunProviderProposal:
    provider_ref = str(_safe_get(item, "provider_id", "provider-ref:provider-runtime:missing"))
    provider_label = str(_safe_get(item, "provider_label", "Provider"))
    provider_manifest_ref = str(
        _safe_get(
            item,
            "provider_manifest_ref",
            f"provider-manifest-ref:{_slug_from_provider_ref(provider_ref)}:missing",
        )
    )
    credential_ref = str(
        _safe_get(
            item,
            "credential_ref",
            f"credential-ref:{_slug_from_provider_ref(provider_ref)}:missing",
        )
    )
    credential_ref_status = str(_safe_get(item, "credential_ref_status", "reference_missing"))
    readiness_status = str(_safe_get(item, "readiness_status", "blocked_reference_only"))
    readiness_posture = str(_safe_get(item, "readiness_posture", ""))
    provider_model_refs_bound = bool(_safe_get(item, "provider_model_refs_bound", False))
    cost_binding = _safe_get(item, "cost_governor_binding", {})
    model_ref = str(
        _safe_get(
            cost_binding,
            "model_ref",
            f"model-ref:{_slug_from_provider_ref(provider_ref)}:not-selected",
        )
    )
    slug = _slug_from_provider_ref(provider_ref)
    reason_codes: list[str] = ["PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY"]
    credential_missing = credential_ref_status != "reference_available" or _ref_is_missing(
        credential_ref
    )
    if credential_missing:
        reason_codes.append("CREDENTIAL_REFERENCE_NOT_BOUND")
    if not provider_model_refs_bound or _ref_is_missing(model_ref):
        reason_codes.append("PROVIDER_MODEL_REFS_REQUIRED")
    cost_risky = bool(_safe_get(cost_binding, "unknown_paid_cost_requires_approval", True))
    cost_risky = cost_risky or bool(
        _safe_get(cost_binding, "estimated_cost_above_budget_blocks_use", True)
    )
    if cost_risky:
        reason_codes.append("UNKNOWN_PAID_COST_REQUIRES_APPROVAL")
        reason_codes.append("COST_RISK_REVIEW_REQUIRED")
    reason_codes.append("CREDENTIAL_VALIDATION_REQUIRED_BEFORE_INVOCATION")
    reason_codes.append("NO_PROVIDER_AUTHORITY")
    status = _status_for_provider(
        credential_missing=credential_missing,
        provider_model_refs_bound=provider_model_refs_bound,
        model_ref=model_ref,
        cost_risky=cost_risky,
        readiness_status=readiness_status,
        readiness_posture=readiness_posture,
    )
    return ProviderRouterDryRunProviderProposal(
        provider_ref=provider_ref,
        provider_label=provider_label,
        provider_manifest_ref=provider_manifest_ref,
        model_ref=model_ref,
        credential_ref=credential_ref,
        credential_ref_status=credential_ref_status,
        status=status,
        readiness_status=readiness_status,
        eligible_for_exact_approval_scope=status
        == ProviderRouterDryRunProviderStatus.eligible,
        missing_credential_ref=f"credential-ref:{slug}:missing-for-router-dry-run",
        cost_risk_ref=f"cost-estimate-ref:{slug}:router-review-required",
        validation_required_ref=f"validation-ref:{slug}:required-before-invocation",
        no_authority_ref=f"provider-ref:{slug}:router-no-runtime-authority",
        recommended_approval_scope_ref=request.need.cost_posture_ref.replace(
            "cost-governor-posture-ref:",
            "approval-scope-ref:",
        ),
        reason_codes=list(dict.fromkeys(reason_codes)),
    )


def _status_for_provider(
    *,
    credential_missing: bool,
    provider_model_refs_bound: bool,
    model_ref: str,
    cost_risky: bool,
    readiness_status: str = "",
    readiness_posture: str = "",
) -> ProviderRouterDryRunProviderStatus:
    if "degraded" in readiness_status.lower() or "degraded" in readiness_posture.lower():
        return ProviderRouterDryRunProviderStatus.degraded
    if credential_missing or not provider_model_refs_bound or _ref_is_missing(model_ref):
        return ProviderRouterDryRunProviderStatus.blocked
    if cost_risky:
        return ProviderRouterDryRunProviderStatus.cost_risky
    return ProviderRouterDryRunProviderStatus.eligible
