from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.costs.governor import CostGovernor
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.providers.invocation import (
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TinyProviderInvocationAdapter,
    TinyProviderInvocationDecision,
    TinyProviderInvocationReceipt,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyProviderReceiptCompletenessStatus,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


EXACT_APPROVED_PROVIDER_FALLBACK_CONTRACT_REF = (
    "provider-fallback-contract-ref:exact-approved-two-adapter:v1"
)
EXACT_APPROVED_PROVIDER_FALLBACK_POLICY_REF = (
    "policy-ref:provider-fallback:exact-approved-two-adapter:v1"
)
EXACT_APPROVED_PROVIDER_FALLBACK_CLI_REF = (
    "cli-ref:inspect-exact-approved-provider-fallback"
)

_ALLOWED_FALLBACK_SCOPES: dict[str, dict[str, str]] = {
    TINY_PROVIDER_INVOCATION_PROVIDER_REF: {
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "policy_ref": TINY_PROVIDER_INVOCATION_POLICY_REF,
    },
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: {
        "model_ref": SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        "policy_ref": SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    },
}
_ALLOWED_PROVIDER_REFS = tuple(_ALLOWED_FALLBACK_SCOPES.keys())
_SAFE_REF_PREFIXES = (
    "approval-ref:",
    "approval-scope-ref:",
    "budget-decision-ref:",
    "cli-ref:",
    "cost-decision-ref:",
    "cost-estimate-ref:",
    "cost-governor-decision-ref:",
    "cost-receipt-ref:",
    "credential-ref:",
    "idempotency:",
    "idempotency-ref:",
    "max-approved-usd-ref:",
    "model-ref:",
    "policy-ref:",
    "provider-adapter-ref:",
    "provider-fallback-attempt-ref:",
    "provider-fallback-contract-ref:",
    "provider-fallback-decision-ref:",
    "provider-fallback-run-ref:",
    "provider-invocation-decision:",
    "provider-invocation-ref:",
    "provider-ref:",
    "receipt:",
    "receipt-ref:",
    "run-ref:",
    "safe-disable-ref:",
    "usage-receipt-ref:",
)
_PER_ATTEMPT_UNIQUE_FIELDS = (
    "attempt_ref",
    "provider_ref",
    "model_ref",
    "credential_ref",
    "approval_ref",
    "approval_scope_ref",
    "cost_estimate_ref",
    "budget_decision_ref",
    "max_approved_usd_ref",
    "idempotency_ref",
    "expected_receipt_ref",
    "usage_receipt_ref",
    "cost_receipt_ref",
)


class ExactApprovedProviderFallbackStatus(str, Enum):
    blocked_missing_receipt_store = "blocked_missing_receipt_store"
    blocked_adapter_scope = "blocked_adapter_scope"
    blocked_attempt_scope = "blocked_attempt_scope"
    blocked_missing_attempt_receipt = "blocked_missing_attempt_receipt"
    blocked_incomplete_attempt_receipt = "blocked_incomplete_attempt_receipt"
    blocked_all_attempts = "blocked_all_attempts"
    receipt_recorded = "receipt_recorded"


class _ExactApprovedProviderFallbackModel(BaseModel):
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


def _require_safe_ref(value: str, field_name: str) -> None:
    if not _safe_ref_matches(value):
        raise ValueError(f"EXACT_APPROVED_PROVIDER_FALLBACK_UNSAFE_REF:{field_name}")


def _safe_reason_code(value: str) -> bool:
    return 1 <= len(value) <= 140 and all(
        char.isupper() or char.isdigit() or char == "_" for char in value
    )


class ExactApprovedProviderFallbackAttempt(_ExactApprovedProviderFallbackModel):
    attempt_ref: str = Field(..., min_length=1)
    sequence_index: int = Field(..., ge=1, le=2)
    request: TinyProviderInvocationRequest

    @model_validator(mode="after")
    def attempt_must_be_exact_scoped(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "EXACT_APPROVED_PROVIDER_FALLBACK_ATTEMPT_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_ref(self.attempt_ref, "attempt_ref")
        expected_scope = _ALLOWED_FALLBACK_SCOPES.get(self.request.provider_ref)
        if expected_scope is None:
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_ATTEMPT_PROVIDER_DENIED")
        if self.request.model_ref != expected_scope["model_ref"]:
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_ATTEMPT_MODEL_DENIED")
        if self.request.policy_ref != expected_scope["policy_ref"]:
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_ATTEMPT_POLICY_DENIED")
        return self


class ExactApprovedProviderFallbackRequest(_ExactApprovedProviderFallbackModel):
    fallback_run_ref: str = "provider-fallback-run-ref:exact-approved:local"
    idempotency_ref: str = "idempotency-ref:provider-fallback:exact-approved:local"
    policy_ref: str = EXACT_APPROVED_PROVIDER_FALLBACK_POLICY_REF
    safe_disable_ref: str = "safe-disable-ref:provider-fallback:exact-approved"
    attempts: list[ExactApprovedProviderFallbackAttempt] = Field(
        ...,
        min_length=2,
        max_length=2,
    )
    exact_approval_required: bool = True
    per_attempt_approval_required: bool = True
    per_attempt_cost_governor_required: bool = True
    per_attempt_receipt_required: bool = True
    stop_on_first_complete_receipt: bool = True
    unknown_paid_cost_blocks_attempt: bool = True
    incomplete_cost_blocks_further_use: bool = True
    broad_router_allowed: bool = False
    autonomous_background_allowed: bool = False
    billing_authority_granted: bool = False
    raw_prompt_response_provider_payload_persistence_allowed: bool = False

    @model_validator(mode="after")
    def fallback_request_must_be_two_exact_attempts(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "EXACT_APPROVED_PROVIDER_FALLBACK_REQUEST_SECRET_LIKE_VALUE_REJECTED",
        )
        for field_name in (
            "fallback_run_ref",
            "idempotency_ref",
            "policy_ref",
            "safe_disable_ref",
        ):
            _require_safe_ref(str(getattr(self, field_name)), field_name)
        if self.policy_ref != EXACT_APPROVED_PROVIDER_FALLBACK_POLICY_REF:
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_POLICY_DENIED")
        if {attempt.sequence_index for attempt in self.attempts} != {1, 2}:
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_SEQUENCE_REQUIRED")
        provider_refs = [attempt.request.provider_ref for attempt in self.attempts]
        if set(provider_refs) != set(_ALLOWED_PROVIDER_REFS):
            raise ValueError(
                "EXACT_APPROVED_PROVIDER_FALLBACK_TWO_PROVIDER_SCOPE_REQUIRED"
            )
        for field_name in _PER_ATTEMPT_UNIQUE_FIELDS:
            values = [
                _per_attempt_unique_value(attempt, field_name)
                for attempt in self.attempts
            ]
            if len(set(values)) != len(values):
                raise ValueError(
                    "EXACT_APPROVED_PROVIDER_FALLBACK_PER_ATTEMPT_SCOPE_REQUIRED:"
                    f"{field_name}"
                )
        required_flags = [
            self.exact_approval_required,
            self.per_attempt_approval_required,
            self.per_attempt_cost_governor_required,
            self.per_attempt_receipt_required,
            self.stop_on_first_complete_receipt,
            self.unknown_paid_cost_blocks_attempt,
            self.incomplete_cost_blocks_further_use,
        ]
        denied_flags = [
            self.broad_router_allowed,
            self.autonomous_background_allowed,
            self.billing_authority_granted,
            self.raw_prompt_response_provider_payload_persistence_allowed,
        ]
        if not all(required_flags) or any(denied_flags):
            raise ValueError(
                "EXACT_APPROVED_PROVIDER_FALLBACK_AUTHORITY_POSTURE_DENIED"
            )
        return self


class ExactApprovedProviderFallbackAttemptResult(_ExactApprovedProviderFallbackModel):
    attempt_ref: str
    sequence_index: int = Field(..., ge=1, le=2)
    provider_ref: str
    model_ref: str
    credential_ref: str
    approval_ref: str
    approval_scope_ref: str
    cost_estimate_ref: str
    budget_decision_ref: str
    max_approved_usd_ref: str
    idempotency_ref: str
    expected_receipt_ref: str
    decision_ref: str
    allowed: bool = False
    status: TinyProviderInvocationStatus
    reason_codes: list[str] = Field(default_factory=list)
    receipt_ref: str | None = None
    prior_blocking_receipt_ref: str | None = None
    prior_blocking_receipt_requires_review: bool = False
    receipt_completeness_status: TinyProviderReceiptCompletenessStatus | None = None
    actual_usage_captured: bool = False
    actual_cost_captured: bool = False
    incomplete_cost_requires_review: bool = False
    further_provider_use_blocked: bool = False

    @model_validator(mode="after")
    def attempt_result_must_be_safe_refs_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "EXACT_APPROVED_PROVIDER_FALLBACK_RESULT_SECRET_LIKE_VALUE_REJECTED",
        )
        for field_name in (
            "attempt_ref",
            "provider_ref",
            "model_ref",
            "credential_ref",
            "approval_ref",
            "approval_scope_ref",
            "cost_estimate_ref",
            "budget_decision_ref",
            "max_approved_usd_ref",
            "idempotency_ref",
            "expected_receipt_ref",
            "decision_ref",
        ):
            _require_safe_ref(str(getattr(self, field_name)), field_name)
        if self.receipt_ref is not None:
            _require_safe_ref(self.receipt_ref, "receipt_ref")
        if self.prior_blocking_receipt_ref is not None:
            _require_safe_ref(
                self.prior_blocking_receipt_ref,
                "prior_blocking_receipt_ref",
            )
        if any(not _safe_reason_code(reason) for reason in self.reason_codes):
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_REASON_CODE_UNSAFE")
        if self.allowed and self.receipt_ref is None:
            raise ValueError(
                "EXACT_APPROVED_PROVIDER_FALLBACK_ALLOWED_RECEIPT_REQUIRED"
            )
        return self


class ExactApprovedProviderFallbackDecision(_ExactApprovedProviderFallbackModel):
    decision_ref: str
    contract_ref: str = EXACT_APPROVED_PROVIDER_FALLBACK_CONTRACT_REF
    cli_ref: str = EXACT_APPROVED_PROVIDER_FALLBACK_CLI_REF
    fallback_run_ref: str
    idempotency_ref: str
    status: ExactApprovedProviderFallbackStatus
    allowed: bool = False
    selected_attempt_ref: str | None = None
    selected_provider_ref: str | None = None
    selected_receipt_ref: str | None = None
    attempt_results: list[ExactApprovedProviderFallbackAttemptResult] = Field(
        default_factory=list
    )
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    broad_router_used: bool = False
    provider_sdk_used: bool = False
    autonomous_background_call: bool = False
    billing_authority_granted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    fallback_limited_to_two_adapters: bool = True
    per_attempt_scope_required: bool = True
    per_attempt_receipt_required: bool = True
    unknown_paid_cost_blocks: bool = True
    incomplete_cost_blocks_further_use: bool = True

    @model_validator(mode="after")
    def decision_must_not_broaden_authority(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "EXACT_APPROVED_PROVIDER_FALLBACK_DECISION_SECRET_LIKE_VALUE_REJECTED",
        )
        for field_name in (
            "decision_ref",
            "contract_ref",
            "cli_ref",
            "fallback_run_ref",
            "idempotency_ref",
        ):
            _require_safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "selected_attempt_ref",
            "selected_provider_ref",
            "selected_receipt_ref",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_safe_ref(value, field_name)
        if any(not _safe_reason_code(reason) for reason in self.reason_codes):
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_DECISION_REASON_UNSAFE")
        denied_flags = [
            self.broad_router_used,
            self.provider_sdk_used,
            self.autonomous_background_call,
            self.billing_authority_granted,
            self.raw_prompt_persisted,
            self.raw_response_persisted,
            self.provider_payload_persisted,
        ]
        required_flags = [
            self.fallback_limited_to_two_adapters,
            self.per_attempt_scope_required,
            self.per_attempt_receipt_required,
            self.unknown_paid_cost_blocks,
            self.incomplete_cost_blocks_further_use,
        ]
        if any(denied_flags) or not all(required_flags):
            raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_AUTHORITY_DENIED")
        if self.allowed:
            if self.status != ExactApprovedProviderFallbackStatus.receipt_recorded:
                raise ValueError(
                    "EXACT_APPROVED_PROVIDER_FALLBACK_ALLOWED_STATUS_DENIED"
                )
            if not all(
                (
                    self.selected_attempt_ref,
                    self.selected_provider_ref,
                    self.selected_receipt_ref,
                )
            ):
                raise ValueError("EXACT_APPROVED_PROVIDER_FALLBACK_SELECTION_REQUIRED")
        return self


def evaluate_exact_approved_provider_fallback(
    request: ExactApprovedProviderFallbackRequest,
    *,
    adapters_by_provider_ref: Mapping[str, TinyProviderInvocationAdapter] | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    receipt_store: TinyProviderInvocationReceiptStore | None = None,
    cost_governor: CostGovernor | None = None,
    policy_engine: PolicyEngine | None = None,
) -> ExactApprovedProviderFallbackDecision:
    if receipt_store is None:
        return _fallback_decision(
            request,
            status=ExactApprovedProviderFallbackStatus.blocked_missing_receipt_store,
            reason_codes=[
                "FALLBACK_DURABLE_RECEIPT_STORE_REQUIRED",
                "MISSING_RECEIPT_BLOCKS_FURTHER_FALLBACK",
            ],
            safe_message=(
                "Exact-approved provider fallback is blocked until durable "
                "receipt storage is supplied before any attempt."
            ),
        )

    adapters_by_provider_ref = adapters_by_provider_ref or {}
    if set(adapters_by_provider_ref.keys()) != set(_ALLOWED_PROVIDER_REFS):
        return _fallback_decision(
            request,
            status=ExactApprovedProviderFallbackStatus.blocked_adapter_scope,
            reason_codes=[
                "FALLBACK_REQUIRES_EXACTLY_TWO_PROVEN_ADAPTERS",
                "NO_BROAD_PROVIDER_ROUTER",
            ],
            safe_message=(
                "Exact-approved provider fallback is blocked because the adapter "
                "map is not exactly the two proven provider scopes."
            ),
        )

    approval_authority = approval_authority or LocalApprovalAuthority()
    cost_governor = cost_governor or CostGovernor()
    attempt_results: list[ExactApprovedProviderFallbackAttemptResult] = []
    for attempt in sorted(request.attempts, key=lambda item: item.sequence_index):
        adapter = adapters_by_provider_ref[attempt.request.provider_ref]
        if (
            adapter.provider_ref != attempt.request.provider_ref
            or adapter.model_ref != attempt.request.model_ref
        ):
            return _fallback_decision(
                request,
                status=ExactApprovedProviderFallbackStatus.blocked_adapter_scope,
                reason_codes=[
                    "FALLBACK_ADAPTER_SCOPE_MISMATCH",
                    "NO_BROAD_PROVIDER_ROUTER",
                ],
                safe_message=(
                    "Exact-approved provider fallback is blocked because an "
                    "adapter does not match the attempt provider/model scope."
                ),
                attempt_results=attempt_results,
            )
        try:
            decision = evaluate_tiny_provider_invocation(
                attempt.request,
                adapter=adapter,
                cost_governor=cost_governor,
                policy_engine=policy_engine,
                approval_authority=approval_authority,
                receipt_store=receipt_store,
            )
        except (ValueError, ValidationError):
            return _fallback_decision(
                request,
                status=ExactApprovedProviderFallbackStatus.blocked_attempt_scope,
                reason_codes=["FALLBACK_ATTEMPT_VALIDATION_BLOCKED"],
                safe_message=(
                    "Exact-approved provider fallback blocked fail-closed because "
                    "an attempt returned invalid safe-ref metadata."
                ),
                attempt_results=attempt_results,
            )
        current_attempt_receipt = _current_attempt_receipt(attempt.request, decision)
        attempt_result = _attempt_result_from_decision(
            attempt,
            decision,
            current_attempt_receipt=current_attempt_receipt,
        )
        attempt_results.append(attempt_result)

        if _decision_has_complete_success(decision, attempt.request):
            return _fallback_decision(
                request,
                status=ExactApprovedProviderFallbackStatus.receipt_recorded,
                reason_codes=[
                    "FALLBACK_STOPPED_ON_FIRST_COMPLETE_RECEIPT",
                    "PER_ATTEMPT_RECEIPT_RECORDED",
                ],
                safe_message=(
                    "Exact-approved provider fallback stopped after the first "
                    "successful complete redacted receipt."
                ),
                allowed=True,
                selected_attempt_ref=attempt.attempt_ref,
                selected_provider_ref=attempt.request.provider_ref,
                selected_receipt_ref=current_attempt_receipt.receipt_ref,
                attempt_results=attempt_results,
            )

        if current_attempt_receipt is None:
            if (
                decision.receipt is not None
                and decision.receipt.further_provider_use_blocked
            ):
                return _fallback_decision(
                    request,
                    status=ExactApprovedProviderFallbackStatus.blocked_incomplete_attempt_receipt,
                    reason_codes=list(
                        dict.fromkeys(
                            [
                                *decision.reason_codes,
                                "PRIOR_BLOCKING_RECEIPT_REQUIRES_REVIEW",
                                "FURTHER_PROVIDER_USE_BLOCKED",
                            ]
                        )
                    ),
                    safe_message=(
                        "Exact-approved provider fallback stopped because a prior "
                        "redacted receipt requires review before further provider use."
                    ),
                    attempt_results=attempt_results,
                )
            return _fallback_decision(
                request,
                status=ExactApprovedProviderFallbackStatus.blocked_missing_attempt_receipt,
                reason_codes=list(
                    dict.fromkeys(
                        [
                            *decision.reason_codes,
                            "FALLBACK_ATTEMPT_RECEIPT_REQUIRED_BEFORE_NEXT_ATTEMPT",
                            "MISSING_RECEIPT_BLOCKS_FURTHER_FALLBACK",
                        ]
                    )
                ),
                safe_message=(
                    "Exact-approved provider fallback stopped because the attempt "
                    "did not produce a redacted receipt."
                ),
                attempt_results=attempt_results,
            )

        if current_attempt_receipt.further_provider_use_blocked:
            return _fallback_decision(
                request,
                status=ExactApprovedProviderFallbackStatus.blocked_incomplete_attempt_receipt,
                reason_codes=list(
                    dict.fromkeys(
                        [
                            *decision.reason_codes,
                            "INCOMPLETE_COST_OR_USAGE_BLOCKS_FURTHER_FALLBACK",
                            "FURTHER_PROVIDER_USE_BLOCKED",
                        ]
                    )
                ),
                safe_message=(
                    "Exact-approved provider fallback stopped because a receipt "
                    "requires review before further provider use."
                ),
                attempt_results=attempt_results,
            )

    return _fallback_decision(
        request,
        status=ExactApprovedProviderFallbackStatus.blocked_all_attempts,
        reason_codes=[
            "FALLBACK_ATTEMPTS_EXHAUSTED_WITHOUT_COMPLETE_SUCCESS_RECEIPT",
            "PER_ATTEMPT_RECEIPTS_INSPECTABLE",
        ],
        safe_message=(
            "Exact-approved provider fallback exhausted the two scoped attempts "
            "without a successful complete receipt."
        ),
        attempt_results=attempt_results,
    )


def _decision_has_complete_success(
    decision: TinyProviderInvocationDecision,
    request: TinyProviderInvocationRequest,
) -> bool:
    receipt = _current_attempt_receipt(request, decision)
    return (
        decision.allowed
        and decision.status == TinyProviderInvocationStatus.receipt_recorded
        and receipt is not None
        and receipt.receipt_completeness_status
        == TinyProviderReceiptCompletenessStatus.complete
        and not receipt.further_provider_use_blocked
    )


def _attempt_result_from_decision(
    attempt: ExactApprovedProviderFallbackAttempt,
    decision: TinyProviderInvocationDecision,
    *,
    current_attempt_receipt: TinyProviderInvocationReceipt | None,
) -> ExactApprovedProviderFallbackAttemptResult:
    receipt = current_attempt_receipt
    prior_blocking_receipt_ref = None
    if (
        receipt is None
        and decision.receipt is not None
        and decision.receipt.further_provider_use_blocked
    ):
        prior_blocking_receipt_ref = decision.receipt.receipt_ref
    return ExactApprovedProviderFallbackAttemptResult(
        attempt_ref=attempt.attempt_ref,
        sequence_index=attempt.sequence_index,
        provider_ref=attempt.request.provider_ref,
        model_ref=attempt.request.model_ref,
        credential_ref=attempt.request.credential_ref,
        approval_ref=attempt.request.approval_ref,
        approval_scope_ref=attempt.request.approval_scope_ref,
        cost_estimate_ref=attempt.request.cost_estimate_ref,
        budget_decision_ref=attempt.request.budget_decision_ref,
        max_approved_usd_ref=attempt.request.max_approved_usd_ref,
        idempotency_ref=attempt.request.idempotency_ref,
        expected_receipt_ref=attempt.request.expected_receipt_ref,
        decision_ref=decision.decision_ref,
        allowed=decision.allowed,
        status=decision.status,
        reason_codes=list(decision.reason_codes),
        receipt_ref=receipt.receipt_ref if receipt is not None else None,
        prior_blocking_receipt_ref=prior_blocking_receipt_ref,
        prior_blocking_receipt_requires_review=prior_blocking_receipt_ref is not None,
        receipt_completeness_status=(
            receipt.receipt_completeness_status if receipt is not None else None
        ),
        actual_usage_captured=(
            receipt.actual_usage_captured if receipt is not None else False
        ),
        actual_cost_captured=receipt.actual_cost_captured
        if receipt is not None
        else False,
        incomplete_cost_requires_review=(
            receipt.incomplete_cost_requires_review if receipt is not None else False
        ),
        further_provider_use_blocked=(
            receipt.further_provider_use_blocked if receipt is not None else False
        ),
    )


def _per_attempt_unique_value(
    attempt: ExactApprovedProviderFallbackAttempt,
    field_name: str,
) -> str:
    if field_name == "attempt_ref":
        return attempt.attempt_ref
    return str(getattr(attempt.request, field_name))


def _current_attempt_receipt(
    request: TinyProviderInvocationRequest,
    decision: TinyProviderInvocationDecision,
) -> TinyProviderInvocationReceipt | None:
    receipt = decision.receipt
    if receipt is None:
        return None
    if _receipt_matches_attempt_request(receipt, request):
        return receipt
    return None


def _receipt_matches_attempt_request(
    receipt: TinyProviderInvocationReceipt,
    request: TinyProviderInvocationRequest,
) -> bool:
    expected_fields = {
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
        "idempotency_ref": request.idempotency_ref,
        "redacted_input_summary_ref": request.redacted_input_summary_ref,
        "safe_disable_ref": request.safe_disable_ref,
    }
    return all(
        getattr(receipt, field_name) == expected_value
        for field_name, expected_value in expected_fields.items()
    )


def _fallback_decision(
    request: ExactApprovedProviderFallbackRequest,
    *,
    status: ExactApprovedProviderFallbackStatus,
    reason_codes: list[str],
    safe_message: str,
    allowed: bool = False,
    selected_attempt_ref: str | None = None,
    selected_provider_ref: str | None = None,
    selected_receipt_ref: str | None = None,
    attempt_results: list[ExactApprovedProviderFallbackAttemptResult] | None = None,
) -> ExactApprovedProviderFallbackDecision:
    suffix = request.fallback_run_ref.removeprefix("provider-fallback-run-ref:")
    suffix = suffix.replace(":", "-")
    return ExactApprovedProviderFallbackDecision(
        decision_ref=f"provider-fallback-decision-ref:{suffix}",
        fallback_run_ref=request.fallback_run_ref,
        idempotency_ref=request.idempotency_ref,
        status=status,
        allowed=allowed,
        selected_attempt_ref=selected_attempt_ref,
        selected_provider_ref=selected_provider_ref,
        selected_receipt_ref=selected_receipt_ref,
        attempt_results=attempt_results or [],
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_message=safe_message,
    )
