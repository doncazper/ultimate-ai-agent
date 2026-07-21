"""Inactive exact contracts for purchases, bookings, and financial operations.

Queue 01 item 12 prepares a content-free plan for one exact financial
operation. Preparation uses the shared governed external-action kernel but
never resolves a payment handle, opens a checkout, calls a network, or performs
the described purchase, booking, payment, or transfer.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationInfo,
    model_validator,
)

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    governed_receipt_identity_payload,
    stable_governed_browser_ref,
)
from .replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    ExternalActionReplayValidationContext,
    _build_external_action_replay_validation_context,
    _require_operation_replay_evidence_envelope,
    replay_validation_context,
    require_external_action_replay_provenance,
)
from .transaction import (
    ExternalActionTransactionConflict,
    GovernedExternalActionKernel,
)


MAX_GOVERNED_FINANCIAL_RECIPE_LIFETIME = timedelta(minutes=10)
MAX_GOVERNED_FINANCIAL_AMOUNT_MINOR_UNITS = 1_000_000_000
_HASH_SUFFIX_RE = re.compile(r"sha256:[0-9a-f]{64}")
_AUTHORITY_PREFIX = "financial-operation-authority-ref:governed-browser:"
_FINANCIAL_REPLAY_LANE_REF = "lane-ref:governed-financial-operation"


class GovernedFinancialOperation(str, Enum):
    purchase = "purchase"
    booking = "booking"
    checkout_payment = "checkout_payment"
    financial_transaction = "financial_transaction"


class GovernedFinancialReversibility(str, Enum):
    manual_recovery = "manual_recovery"
    irreversible = "irreversible"


class GovernedFinancialContractStatus(str, Enum):
    contract_ready = "contract_ready"
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


def _required_capability(
    operation: GovernedFinancialOperation,
) -> AuthorityCapability:
    return {
        GovernedFinancialOperation.purchase: AuthorityCapability.purchase,
        GovernedFinancialOperation.booking: (AuthorityCapability.purchase_under_budget),
        GovernedFinancialOperation.checkout_payment: AuthorityCapability.purchase,
        GovernedFinancialOperation.financial_transaction: (
            AuthorityCapability.purchase_under_budget
        ),
    }[GovernedFinancialOperation(operation)]


def _validate_pinned_ref(value: str, *, label: str, prefix: str) -> None:
    validate_task_ref(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"GOVERNED_FINANCIAL_{label.upper()}_REQUIRED")
    if _HASH_SUFFIX_RE.fullmatch(value.removeprefix(prefix)) is None:
        raise ValueError("GOVERNED_FINANCIAL_HASH_PIN_REQUIRED")


def governed_financial_target_ref(
    *,
    operation: GovernedFinancialOperation,
    target_descriptor_ref: str,
) -> str:
    validate_task_ref(target_descriptor_ref, "target_descriptor_ref")
    return stable_governed_browser_ref(
        "financial-target-ref:governed-browser",
        {
            "operation": GovernedFinancialOperation(operation).value,
            "target_descriptor_ref": target_descriptor_ref,
        },
    )


def governed_financial_input_ref(
    *,
    operation: GovernedFinancialOperation,
    target_ref: str,
    quote_ref: str,
    currency_ref: str,
    payment_handle_ref: str,
    amount_minor_units: int,
    spend_limit_minor_units: int,
    artifact_refs: Sequence[str],
    booking_ref: str | None,
    checkout_ref: str | None,
    financial_instrument_ref: str | None,
    cancellation_policy_ref: str | None,
    refund_policy_ref: str | None,
) -> str:
    exact_operation = GovernedFinancialOperation(operation)
    exact_artifacts = list(artifact_refs)
    _validate_financial_refs(
        target_ref=target_ref,
        quote_ref=quote_ref,
        currency_ref=currency_ref,
        payment_handle_ref=payment_handle_ref,
        artifact_refs=exact_artifacts,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
    )
    _validate_amounts(
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
    )
    _validate_operation_scope(
        operation=exact_operation,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
    )
    return stable_governed_browser_ref(
        "financial-input-ref:governed-browser",
        {
            "operation": exact_operation.value,
            "target_ref": target_ref,
            "quote_ref": quote_ref,
            "currency_ref": currency_ref,
            "payment_handle_ref": payment_handle_ref,
            "amount_minor_units": amount_minor_units,
            "spend_limit_minor_units": spend_limit_minor_units,
            "artifact_refs": exact_artifacts,
            "booking_ref": booking_ref,
            "checkout_ref": checkout_ref,
            "financial_instrument_ref": financial_instrument_ref,
            "cancellation_policy_ref": cancellation_policy_ref,
            "refund_policy_ref": refund_policy_ref,
        },
    )


def governed_financial_schema_ref(
    *,
    operation: GovernedFinancialOperation,
    target_ref: str,
    financial_input_ref: str,
    quote_ref: str,
    currency_ref: str,
    payment_handle_ref: str,
    amount_minor_units: int,
    spend_limit_minor_units: int,
    artifact_refs: Sequence[str],
    booking_ref: str | None,
    checkout_ref: str | None,
    financial_instrument_ref: str | None,
    cancellation_policy_ref: str | None,
    refund_policy_ref: str | None,
    reversibility: GovernedFinancialReversibility,
    rollback_ref: str,
    reconciliation_ref: str,
) -> str:
    expected_input_ref = governed_financial_input_ref(
        operation=operation,
        target_ref=target_ref,
        quote_ref=quote_ref,
        currency_ref=currency_ref,
        payment_handle_ref=payment_handle_ref,
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
        artifact_refs=artifact_refs,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
    )
    if financial_input_ref != expected_input_ref:
        raise ValueError("GOVERNED_FINANCIAL_INPUT_REF_MISMATCH")
    _validate_pinned_ref(
        financial_input_ref,
        label="financial_input_ref",
        prefix="financial-input-ref:governed-browser:",
    )
    for value, label, prefix in (
        (
            rollback_ref,
            "rollback_ref",
            "financial-rollback-ref:governed-browser:",
        ),
        (
            reconciliation_ref,
            "reconciliation_ref",
            "financial-reconciliation-ref:governed-browser:",
        ),
    ):
        _validate_pinned_ref(value, label=label, prefix=prefix)
    exact_reversibility = GovernedFinancialReversibility(reversibility)
    _validate_reversibility(
        operation=GovernedFinancialOperation(operation),
        reversibility=exact_reversibility,
    )
    return stable_governed_browser_ref(
        "financial-schema-ref:governed-browser",
        {
            "financial_input_ref": financial_input_ref,
            "reversibility": exact_reversibility.value,
            "rollback_ref": rollback_ref,
            "reconciliation_ref": reconciliation_ref,
        },
    )


def governed_financial_authority_ref(
    *,
    operation: GovernedFinancialOperation,
    origin_ref: str,
    target_ref: str,
    schema_ref: str,
) -> str:
    validate_task_ref(origin_ref, "origin_ref")
    _validate_pinned_ref(
        target_ref,
        label="target_ref",
        prefix="financial-target-ref:governed-browser:",
    )
    _validate_pinned_ref(
        schema_ref,
        label="schema_ref",
        prefix="financial-schema-ref:governed-browser:",
    )
    return stable_governed_browser_ref(
        "financial-operation-authority-ref:governed-browser",
        {
            "operation": GovernedFinancialOperation(operation).value,
            "origin_ref": origin_ref,
            "target_ref": target_ref,
            "schema_ref": schema_ref,
        },
    )


def governed_financial_contract_ref(
    *,
    operation: GovernedFinancialOperation,
    origin_ref: str,
    page_snapshot_ref: str,
    authority_ref: str,
    scope: ExactGovernedFinancialScope,
    expires_at: datetime,
) -> str:
    validate_task_ref(origin_ref, "origin_ref")
    validate_task_ref(page_snapshot_ref, "page_snapshot_ref")
    if expires_at.tzinfo is None:
        raise ValueError("GOVERNED_FINANCIAL_TIMEZONE_REQUIRED")
    expected_authority_ref = governed_financial_authority_ref(
        operation=operation,
        origin_ref=origin_ref,
        target_ref=scope.target_ref,
        schema_ref=scope.schema_ref,
    )
    if authority_ref != expected_authority_ref:
        raise ValueError("GOVERNED_FINANCIAL_AUTHORITY_REF_MISMATCH")
    return stable_governed_browser_ref(
        "financial-contract-ref:governed-browser",
        {
            "operation": GovernedFinancialOperation(operation).value,
            "origin_ref": origin_ref,
            "page_snapshot_ref": page_snapshot_ref,
            "authority_ref": authority_ref,
            "scope": scope.model_dump(mode="json"),
            "expires_at": expires_at.isoformat(),
        },
    )


def _validate_amounts(
    *,
    amount_minor_units: int,
    spend_limit_minor_units: int,
) -> None:
    if type(amount_minor_units) is not int or type(spend_limit_minor_units) is not int:
        raise ValueError("GOVERNED_FINANCIAL_AMOUNT_INVALID")
    if (
        amount_minor_units <= 0
        or spend_limit_minor_units <= 0
        or amount_minor_units > spend_limit_minor_units
        or spend_limit_minor_units > MAX_GOVERNED_FINANCIAL_AMOUNT_MINOR_UNITS
    ):
        raise ValueError("GOVERNED_FINANCIAL_AMOUNT_OUTSIDE_EXACT_BUDGET")


def _validate_financial_refs(
    *,
    target_ref: str,
    quote_ref: str,
    currency_ref: str,
    payment_handle_ref: str,
    artifact_refs: Sequence[str],
    booking_ref: str | None,
    checkout_ref: str | None,
    financial_instrument_ref: str | None,
    cancellation_policy_ref: str | None,
    refund_policy_ref: str | None,
) -> None:
    required = (
        (target_ref, "target_ref", "financial-target-ref:governed-browser:"),
        (quote_ref, "quote_ref", "financial-quote-ref:governed-browser:"),
        (
            currency_ref,
            "currency_ref",
            "financial-currency-ref:governed-browser:",
        ),
        (
            payment_handle_ref,
            "payment_handle_ref",
            "payment-handle-ref:governed-browser:",
        ),
    )
    for value, label, prefix in required:
        _validate_pinned_ref(value, label=label, prefix=prefix)
    exact_artifacts = list(artifact_refs)
    if not exact_artifacts or len(exact_artifacts) > 8:
        raise ValueError("GOVERNED_FINANCIAL_ARTIFACT_SCOPE_INVALID")
    if len(set(exact_artifacts)) != len(exact_artifacts):
        raise ValueError("GOVERNED_FINANCIAL_ARTIFACT_DUPLICATE")
    for artifact_ref in exact_artifacts:
        _validate_pinned_ref(
            artifact_ref,
            label="artifact_ref",
            prefix="financial-artifact-ref:governed-browser:",
        )
    optional = (
        (booking_ref, "booking_ref", "booking-ref:governed-browser:"),
        (checkout_ref, "checkout_ref", "checkout-ref:governed-browser:"),
        (
            financial_instrument_ref,
            "financial_instrument_ref",
            "financial-instrument-ref:governed-browser:",
        ),
        (
            cancellation_policy_ref,
            "cancellation_policy_ref",
            "cancellation-policy-ref:governed-browser:",
        ),
        (
            refund_policy_ref,
            "refund_policy_ref",
            "refund-policy-ref:governed-browser:",
        ),
    )
    for value, label, prefix in optional:
        if value is not None:
            _validate_pinned_ref(value, label=label, prefix=prefix)


def _validate_operation_scope(
    *,
    operation: GovernedFinancialOperation,
    booking_ref: str | None,
    checkout_ref: str | None,
    financial_instrument_ref: str | None,
    cancellation_policy_ref: str | None,
    refund_policy_ref: str | None,
) -> None:
    exact_operation = GovernedFinancialOperation(operation)
    expected = {
        GovernedFinancialOperation.purchase: (
            False,
            False,
            False,
            False,
            True,
        ),
        GovernedFinancialOperation.booking: (
            True,
            False,
            False,
            True,
            False,
        ),
        GovernedFinancialOperation.checkout_payment: (
            False,
            True,
            False,
            False,
            True,
        ),
        GovernedFinancialOperation.financial_transaction: (
            False,
            False,
            True,
            False,
            False,
        ),
    }[exact_operation]
    actual = (
        booking_ref is not None,
        checkout_ref is not None,
        financial_instrument_ref is not None,
        cancellation_policy_ref is not None,
        refund_policy_ref is not None,
    )
    if actual != expected:
        raise ValueError("GOVERNED_FINANCIAL_OPERATION_SCOPE_MISMATCH")


def _validate_reversibility(
    *,
    operation: GovernedFinancialOperation,
    reversibility: GovernedFinancialReversibility,
) -> None:
    exact_operation = GovernedFinancialOperation(operation)
    expected = (
        GovernedFinancialReversibility.manual_recovery
        if exact_operation
        in {
            GovernedFinancialOperation.purchase,
            GovernedFinancialOperation.booking,
        }
        else GovernedFinancialReversibility.irreversible
    )
    if GovernedFinancialReversibility(reversibility) != expected:
        raise ValueError("GOVERNED_FINANCIAL_REVERSIBILITY_UNPROVEN")


class ExactGovernedFinancialScope(BaseModel):
    schema_version: Literal["uaa-governed-financial-scope.v1"] = (
        "uaa-governed-financial-scope.v1"
    )
    operation: GovernedFinancialOperation
    required_capability: AuthorityCapability
    target_ref: str
    quote_ref: str
    currency_ref: str
    payment_handle_ref: str
    amount_minor_units: StrictInt = Field(..., gt=0)
    spend_limit_minor_units: StrictInt = Field(..., gt=0)
    artifact_refs: list[str] = Field(..., min_length=1, max_length=8)
    booking_ref: str | None = None
    checkout_ref: str | None = None
    financial_instrument_ref: str | None = None
    cancellation_policy_ref: str | None = None
    refund_policy_ref: str | None = None
    reversibility: GovernedFinancialReversibility
    rollback_ref: str
    reconciliation_ref: str
    financial_input_ref: str
    schema_ref: str
    opaque_payment_handle_only: Literal[True] = True
    raw_payment_data_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_scope(self) -> ExactGovernedFinancialScope:
        operation = GovernedFinancialOperation(self.operation)
        if self.required_capability != _required_capability(operation).value:
            raise ValueError("GOVERNED_FINANCIAL_CAPABILITY_MISMATCH")
        expected_input_ref = governed_financial_input_ref(
            operation=operation,
            target_ref=self.target_ref,
            quote_ref=self.quote_ref,
            currency_ref=self.currency_ref,
            payment_handle_ref=self.payment_handle_ref,
            amount_minor_units=self.amount_minor_units,
            spend_limit_minor_units=self.spend_limit_minor_units,
            artifact_refs=self.artifact_refs,
            booking_ref=self.booking_ref,
            checkout_ref=self.checkout_ref,
            financial_instrument_ref=self.financial_instrument_ref,
            cancellation_policy_ref=self.cancellation_policy_ref,
            refund_policy_ref=self.refund_policy_ref,
        )
        if self.financial_input_ref != expected_input_ref:
            raise ValueError("GOVERNED_FINANCIAL_INPUT_REF_MISMATCH")
        expected_schema_ref = governed_financial_schema_ref(
            operation=operation,
            target_ref=self.target_ref,
            financial_input_ref=self.financial_input_ref,
            quote_ref=self.quote_ref,
            currency_ref=self.currency_ref,
            payment_handle_ref=self.payment_handle_ref,
            amount_minor_units=self.amount_minor_units,
            spend_limit_minor_units=self.spend_limit_minor_units,
            artifact_refs=self.artifact_refs,
            booking_ref=self.booking_ref,
            checkout_ref=self.checkout_ref,
            financial_instrument_ref=self.financial_instrument_ref,
            cancellation_policy_ref=self.cancellation_policy_ref,
            refund_policy_ref=self.refund_policy_ref,
            reversibility=GovernedFinancialReversibility(self.reversibility),
            rollback_ref=self.rollback_ref,
            reconciliation_ref=self.reconciliation_ref,
        )
        if self.schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_FINANCIAL_SCHEMA_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "exact_governed_financial_scope",
        )
        return self

    def exact_resource_refs(
        self,
        *,
        authority_ref: str,
        contract_ref: str,
    ) -> set[str]:
        refs = {
            authority_ref,
            contract_ref,
            self.financial_input_ref,
            self.quote_ref,
            self.currency_ref,
            self.payment_handle_ref,
            self.rollback_ref,
            self.reconciliation_ref,
        }
        for optional_ref in (
            self.booking_ref,
            self.checkout_ref,
            self.financial_instrument_ref,
            self.cancellation_policy_ref,
            self.refund_policy_ref,
        ):
            if optional_ref is not None:
                refs.add(optional_ref)
        return refs


def build_exact_governed_financial_scope(
    *,
    operation: GovernedFinancialOperation,
    target_ref: str,
    quote_ref: str,
    currency_ref: str,
    payment_handle_ref: str,
    amount_minor_units: int,
    spend_limit_minor_units: int,
    artifact_refs: Sequence[str],
    booking_ref: str | None,
    checkout_ref: str | None,
    financial_instrument_ref: str | None,
    cancellation_policy_ref: str | None,
    refund_policy_ref: str | None,
    reversibility: GovernedFinancialReversibility,
    rollback_ref: str,
    reconciliation_ref: str,
) -> ExactGovernedFinancialScope:
    financial_input_ref = governed_financial_input_ref(
        operation=operation,
        target_ref=target_ref,
        quote_ref=quote_ref,
        currency_ref=currency_ref,
        payment_handle_ref=payment_handle_ref,
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
        artifact_refs=artifact_refs,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
    )
    schema_ref = governed_financial_schema_ref(
        operation=operation,
        target_ref=target_ref,
        financial_input_ref=financial_input_ref,
        quote_ref=quote_ref,
        currency_ref=currency_ref,
        payment_handle_ref=payment_handle_ref,
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
        artifact_refs=artifact_refs,
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
    )
    return ExactGovernedFinancialScope(
        operation=operation,
        required_capability=_required_capability(operation),
        target_ref=target_ref,
        quote_ref=quote_ref,
        currency_ref=currency_ref,
        payment_handle_ref=payment_handle_ref,
        amount_minor_units=amount_minor_units,
        spend_limit_minor_units=spend_limit_minor_units,
        artifact_refs=list(artifact_refs),
        booking_ref=booking_ref,
        checkout_ref=checkout_ref,
        financial_instrument_ref=financial_instrument_ref,
        cancellation_policy_ref=cancellation_policy_ref,
        refund_policy_ref=refund_policy_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
        financial_input_ref=financial_input_ref,
        schema_ref=schema_ref,
    )


class GovernedFinancialRecipe(BaseModel):
    schema_version: Literal["uaa-governed-financial-recipe.v1"] = (
        "uaa-governed-financial-recipe.v1"
    )
    recipe_ref: str
    contract_ref: str
    authority_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    scope: ExactGovernedFinancialScope
    created_at: datetime
    expires_at: datetime
    registered_recipe_required: Literal[True] = True
    contract_plan_only: Literal[True] = True
    exact_approval_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    human_presence_required: Literal[True] = True
    separate_financial_execution_required: Literal[True] = True
    payment_handle_resolution_allowed: Literal[False] = False
    checkout_open_allowed: Literal[False] = False
    purchase_allowed: Literal[False] = False
    booking_allowed: Literal[False] = False
    payment_allowed: Literal[False] = False
    financial_transaction_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_recipe(self) -> GovernedFinancialRecipe:
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.authority_ref, "authority_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
        ):
            validate_task_ref(value, label)
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_FINANCIAL_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at
            > MAX_GOVERNED_FINANCIAL_RECIPE_LIFETIME
        ):
            raise ValueError("GOVERNED_FINANCIAL_LIFETIME_INVALID")
        expected_contract_ref = governed_financial_contract_ref(
            operation=GovernedFinancialOperation(self.scope.operation),
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            authority_ref=self.authority_ref,
            scope=self.scope,
            expires_at=self.expires_at,
        )
        if self.contract_ref != expected_contract_ref:
            raise ValueError("GOVERNED_FINANCIAL_CONTRACT_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "financial-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_FINANCIAL_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_financial_recipe",
        )
        return self


def build_governed_financial_recipe(
    request: ExternalActionExecutionRequest,
    *,
    scope: ExactGovernedFinancialScope,
    created_at: datetime,
    expires_at: datetime,
) -> GovernedFinancialRecipe:
    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    operation = GovernedFinancialOperation(scope.operation)
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_FINANCIAL_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != _required_capability(operation).value:
        raise ValueError("GOVERNED_FINANCIAL_EXACT_CAPABILITY_MISMATCH")
    if not binding.human_present:
        raise ValueError("GOVERNED_FINANCIAL_HUMAN_PRESENCE_REQUIRED")
    if binding.recipient_ref != scope.target_ref:
        raise ValueError("GOVERNED_FINANCIAL_TARGET_NOT_AUTHORITY_BOUND")
    if binding.field_schema_ref != scope.schema_ref:
        raise ValueError("GOVERNED_FINANCIAL_SCHEMA_NOT_AUTHORITY_BOUND")
    if binding.artifact_refs != tuple(scope.artifact_refs):
        raise ValueError("GOVERNED_FINANCIAL_ARTIFACT_NOT_AUTHORITY_BOUND")
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_FINANCIAL_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline or expires_at > binding.start_deadline:
        raise ValueError("GOVERNED_FINANCIAL_DEADLINE_EXCEEDED")
    authority_ref = governed_financial_authority_ref(
        operation=operation,
        origin_ref=binding.origin_ref,
        target_ref=scope.target_ref,
        schema_ref=scope.schema_ref,
    )
    contract_ref = governed_financial_contract_ref(
        operation=operation,
        origin_ref=binding.origin_ref,
        page_snapshot_ref=binding.page_snapshot_ref,
        authority_ref=authority_ref,
        scope=scope,
        expires_at=expires_at,
    )
    if set(binding.resource_refs) != scope.exact_resource_refs(
        authority_ref=authority_ref,
        contract_ref=contract_ref,
    ):
        raise ValueError("GOVERNED_FINANCIAL_RESOURCE_NOT_EXACTLY_BOUND")
    bound_authorities = tuple(
        ref for ref in binding.resource_refs if ref.startswith(_AUTHORITY_PREFIX)
    )
    if bound_authorities != (authority_ref,):
        raise ValueError("GOVERNED_FINANCIAL_AUTHORITY_NOT_EXACTLY_BOUND")
    payload = {
        "contract_ref": contract_ref,
        "authority_ref": authority_ref,
        "binding_ref": binding.binding_ref,
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "scope": scope,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedFinancialRecipe.model_construct(
        recipe_ref="financial-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "financial-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedFinancialRecipe(recipe_ref=recipe_ref, **payload)


class GovernedFinancialRecipeRegistry:
    def __init__(self, recipes: Sequence[GovernedFinancialRecipe]) -> None:
        validated = tuple(
            GovernedFinancialRecipe.model_validate(recipe.model_dump(mode="json"))
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_FINANCIAL_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_FINANCIAL_RECIPE_REGISTRY_TOO_LARGE")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_FINANCIAL_RECIPE_REF_DUPLICATE")
        by_authority = {recipe.authority_ref: recipe for recipe in validated}
        if len(by_authority) != len(validated):
            raise ValueError("GOVERNED_FINANCIAL_AUTHORITY_DUPLICATE")
        self._recipes = by_ref

    def resolve(self, recipe_ref: str) -> GovernedFinancialRecipe | None:
        return self._recipes.get(recipe_ref)


class ExactGovernedFinancialRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str
    contract_ref: str
    operation: GovernedFinancialOperation
    target_ref: str
    financial_input_ref: str

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_request(self) -> ExactGovernedFinancialRequest:
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.target_ref, "target_ref"),
            (self.financial_input_ref, "financial_input_ref"),
        ):
            validate_task_ref(value, label)
        return self


class ExactGovernedFinancialContract(BaseModel):
    schema_version: Literal["uaa-governed-financial-contract.v1"] = (
        "uaa-governed-financial-contract.v1"
    )
    contract_ref: str
    authority_ref: str
    origin_ref: str
    page_snapshot_ref: str
    scope: ExactGovernedFinancialScope
    expires_at: datetime
    contract_prepared: Literal[True] = True
    separate_financial_execution_required: Literal[True] = True
    monetary_execution_budget_revalidation_required: Literal[True] = True
    payment_handle_resolved: Literal[False] = False
    checkout_opened: Literal[False] = False
    purchase_performed: Literal[False] = False
    booking_performed: Literal[False] = False
    payment_performed: Literal[False] = False
    financial_transaction_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_contract(self) -> ExactGovernedFinancialContract:
        expected = governed_financial_contract_ref(
            operation=GovernedFinancialOperation(self.scope.operation),
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            authority_ref=self.authority_ref,
            scope=self.scope,
            expires_at=self.expires_at,
        )
        if self.contract_ref != expected:
            raise ValueError("GOVERNED_FINANCIAL_CONTRACT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "exact_governed_financial_contract",
        )
        return self


class GovernedFinancialReceipt(BaseModel):
    schema_version: Literal["uaa-governed-financial-receipt.v1"] = (
        "uaa-governed-financial-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    contract_ref: str
    authority_ref: str | None = None
    operation: GovernedFinancialOperation
    target_ref: str
    financial_input_ref: str | None = None
    quote_ref: str | None = None
    payment_handle_ref: str | None = None
    rollback_ref: str | None = None
    reconciliation_ref: str | None = None
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: GovernedFinancialContractStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    contract_plan_only: Literal[True] = True
    raw_payment_data_recorded: Literal[False] = False
    payment_handle_resolved: Literal[False] = False
    checkout_opened: Literal[False] = False
    financial_effect_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_receipt(
        self,
        info: ValidationInfo,
    ) -> GovernedFinancialReceipt:
        for value, label in (
            (self.receipt_ref, "receipt_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.authority_ref, "authority_ref"),
            (self.target_ref, "target_ref"),
            (self.financial_input_ref, "financial_input_ref"),
            (self.quote_ref, "quote_ref"),
            (self.payment_handle_ref, "payment_handle_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.reconciliation_ref, "reconciliation_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        status = GovernedFinancialContractStatus(self.status)
        state = ExternalActionState(self.external_action_state)
        successful = {
            GovernedFinancialContractStatus.contract_ready,
            GovernedFinancialContractStatus.replayed_content_free,
        }
        expected_states = {
            GovernedFinancialContractStatus.contract_ready: (
                ExternalActionState.succeeded,
            ),
            GovernedFinancialContractStatus.replayed_content_free: (
                ExternalActionState.succeeded,
            ),
            GovernedFinancialContractStatus.preflight_blocked: (
                ExternalActionState.blocked,
            ),
            GovernedFinancialContractStatus.transaction_blocked: (
                ExternalActionState.blocked,
            ),
            GovernedFinancialContractStatus.failed: (ExternalActionState.failed,),
            GovernedFinancialContractStatus.outcome_ambiguous: (
                ExternalActionState.outcome_ambiguous,
                ExternalActionState.started,
                ExternalActionState.prepared,
            ),
        }[status]
        if state not in expected_states:
            raise ValueError("GOVERNED_FINANCIAL_RECEIPT_STATE_MISMATCH")
        if status == GovernedFinancialContractStatus.contract_ready and (self.replayed):
            raise ValueError("GOVERNED_FINANCIAL_READY_STATE_MISMATCH")
        if status == GovernedFinancialContractStatus.replayed_content_free and (
            not self.replayed
        ):
            raise ValueError("GOVERNED_FINANCIAL_REPLAY_STATE_MISMATCH")
        external_kernel_proof_refs = (
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_release_ref,
            self.budget_settlement_ref,
        )
        external_proof_context_present = (
            self.external_action_receipt_ref is not None
            or any(ref is not None for ref in external_kernel_proof_refs)
            or bool(self.evidence_refs)
        )
        if (
            status == GovernedFinancialContractStatus.preflight_blocked
            and (external_proof_context_present or self.replayed)
        ):
            raise ValueError("GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_INVALID")
        if self.external_action_receipt_ref is None and (
            any(ref is not None for ref in external_kernel_proof_refs)
            or self.evidence_refs
        ):
            raise ValueError("GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_INVALID")
        if (
            status != GovernedFinancialContractStatus.preflight_blocked
            and self.external_action_receipt_ref is None
        ):
            raise ValueError("GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_REQUIRED")
        if status in successful:
            kernel_refs = (
                self.external_action_receipt_ref,
                self.approval_validation_ref,
                self.authority_decision_ref,
                self.budget_reservation_ref,
                self.budget_settlement_ref,
            )
            scope_refs = (
                self.authority_ref,
                self.financial_input_ref,
                self.quote_ref,
                self.payment_handle_ref,
                self.rollback_ref,
                self.reconciliation_ref,
            )
            if any(ref is None for ref in kernel_refs):
                raise ValueError("GOVERNED_FINANCIAL_SUCCESS_KERNEL_PROOF_REQUIRED")
            if any(ref is None for ref in scope_refs):
                raise ValueError("GOVERNED_FINANCIAL_SUCCESS_SCOPE_PROOF_REQUIRED")
            assert self.authority_ref is not None
            assert self.financial_input_ref is not None
            assert self.quote_ref is not None
            assert self.payment_handle_ref is not None
            assert self.rollback_ref is not None
            assert self.reconciliation_ref is not None
            for value, label, prefix in (
                (
                    self.recipe_ref,
                    "recipe_ref",
                    "financial-recipe-ref:governed-browser:",
                ),
                (
                    self.contract_ref,
                    "contract_ref",
                    "financial-contract-ref:governed-browser:",
                ),
                (
                    self.target_ref,
                    "target_ref",
                    "financial-target-ref:governed-browser:",
                ),
                (
                    self.authority_ref,
                    "authority_ref",
                    _AUTHORITY_PREFIX,
                ),
                (
                    self.financial_input_ref,
                    "financial_input_ref",
                    "financial-input-ref:governed-browser:",
                ),
                (
                    self.quote_ref,
                    "quote_ref",
                    "financial-quote-ref:governed-browser:",
                ),
                (
                    self.payment_handle_ref,
                    "payment_handle_ref",
                    "payment-handle-ref:governed-browser:",
                ),
                (
                    self.rollback_ref,
                    "rollback_ref",
                    "financial-rollback-ref:governed-browser:",
                ),
                (
                    self.reconciliation_ref,
                    "reconciliation_ref",
                    "financial-reconciliation-ref:governed-browser:",
                ),
            ):
                _validate_pinned_ref(value, label=label, prefix=prefix)
            expected_evidence = [
                self.contract_ref,
                self.authority_ref,
                self.financial_input_ref,
                self.quote_ref,
                self.payment_handle_ref,
                self.rollback_ref,
                self.reconciliation_ref,
            ]
            if self.evidence_refs != expected_evidence:
                raise ValueError("GOVERNED_FINANCIAL_SUCCESS_EVIDENCE_MISMATCH")
            if self.reason_refs:
                raise ValueError("GOVERNED_FINANCIAL_SUCCESS_REASON_MISMATCH")
        if self.external_action_receipt_ref is not None:
            external_reason_refs = tuple(self.reason_refs)
            if (
                status == GovernedFinancialContractStatus.failed
                and external_reason_refs
                == ("reason-ref:governed-financial:contract-preparation-failed",)
            ):
                external_reason_refs = ()
            try:
                external_receipt = ExternalActionReceipt(
                    receipt_ref=self.external_action_receipt_ref,
                    transaction_ref=self.transaction_ref,
                    intent_ref=self.intent_ref,
                    binding_ref=self.binding_ref,
                    state=self.external_action_state,
                    approval_validation_ref=self.approval_validation_ref,
                    authority_decision_ref=self.authority_decision_ref,
                    budget_reservation_ref=self.budget_reservation_ref,
                    budget_release_ref=self.budget_release_ref,
                    budget_settlement_ref=self.budget_settlement_ref,
                    evidence_refs=tuple(self.evidence_refs),
                    reason_refs=external_reason_refs,
                    replayed=self.replayed,
                )
            except ValueError as exc:
                raise ValueError(
                    "GOVERNED_FINANCIAL_EXTERNAL_RECEIPT_REF_MISMATCH"
                ) from exc
            if self.replayed:
                require_external_action_replay_provenance(
                    info,
                    lane_ref=_financial_replay_lane_ref(self.operation),
                    operation_ref=self.recipe_ref,
                    candidate=external_receipt,
                )
        expected_receipt_ref = stable_governed_browser_ref(
            "receipt-ref:governed-financial-contract",
            governed_receipt_identity_payload(self),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("GOVERNED_FINANCIAL_RECEIPT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_financial_receipt",
        )
        return self


class ExactGovernedFinancialResult(BaseModel):
    receipt: GovernedFinancialReceipt
    contract: ExactGovernedFinancialContract | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> ExactGovernedFinancialResult:
        ready = (
            self.receipt.status == GovernedFinancialContractStatus.contract_ready.value
        )
        if ready != (self.contract is not None):
            raise ValueError("GOVERNED_FINANCIAL_CONTRACT_PROJECTION_MISMATCH")
        if self.contract is not None and (
            self.contract.contract_ref != self.receipt.contract_ref
            or self.contract.authority_ref != self.receipt.authority_ref
            or self.contract.scope.operation != self.receipt.operation
            or self.contract.scope.target_ref != self.receipt.target_ref
            or self.contract.scope.financial_input_ref
            != self.receipt.financial_input_ref
            or self.contract.scope.quote_ref != self.receipt.quote_ref
            or self.contract.scope.payment_handle_ref != self.receipt.payment_handle_ref
            or self.contract.scope.rollback_ref != self.receipt.rollback_ref
            or self.contract.scope.reconciliation_ref != self.receipt.reconciliation_ref
        ):
            raise ValueError("GOVERNED_FINANCIAL_RECEIPT_SCOPE_MISMATCH")
        return self


class ExactGovernedFinancialService:
    def __init__(
        self,
        *,
        registry: GovernedFinancialRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._clock = clock

    def prepare(
        self,
        contract_request: ExactGovernedFinancialRequest,
    ) -> ExactGovernedFinancialResult:
        request = ExactGovernedFinancialRequest.model_validate(
            contract_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:recipe-unregistered",
            )
        if (
            request.contract_ref,
            request.operation,
            request.target_ref,
            request.financial_input_ref,
        ) != (
            recipe.contract_ref,
            recipe.scope.operation,
            recipe.scope.target_ref,
            recipe.scope.financial_input_ref,
        ):
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:request-scope-mismatch",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)
        kernel_execution = _kernel_execution(
            execution,
            recipe_ref=recipe.recipe_ref,
        )
        try:
            replay = self._kernel.replay_if_terminal(kernel_execution)
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:idempotency-conflict",
            )
        if replay is not None:
            replay_context = _financial_replay_validation_context(
                kernel=self._kernel,
                expected_execution=kernel_execution,
                recipe=recipe,
                replay_receipt=replay,
            )
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=replay,
                contract=None,
                replay_context=replay_context,
            )
        try:
            prior_start = self._kernel.recover_if_prior_start(kernel_execution)
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:idempotency-conflict",
            )
        if prior_start is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=prior_start,
                contract=None,
            )
        current_time, clock_reason = _read_clock(self._clock)
        if clock_reason is not None:
            return _preflight_blocked(request, clock_reason)
        assert current_time is not None
        if current_time < recipe.created_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:recipe-not-yet-valid",
            )
        if current_time >= recipe.expires_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:recipe-expired",
            )
        captured: dict[str, ExactGovernedFinancialContract] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            dispatch_time, dispatch_clock_reason = _read_clock(self._clock)
            if dispatch_clock_reason is not None:
                return _failed_dispatch(
                    dispatched_request,
                    "trusted-clock-invalid",
                )
            assert dispatch_time is not None
            if (
                dispatched_request.binding.binding_ref != recipe.binding_ref
                or not recipe.created_at <= dispatch_time < recipe.expires_at
            ):
                return _failed_dispatch(
                    dispatched_request,
                    "contract-revalidation-failed",
                )
            contract = _build_contract(recipe)
            captured["contract"] = contract
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=_success_evidence(recipe),
                verified=True,
            )

        try:
            external_receipt = self._kernel.execute(
                kernel_execution,
                dispatch=dispatch,
            )
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-financial:idempotency-conflict",
            )
        contract = captured.get("contract")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            contract = None
        replay_context = (
            _financial_replay_validation_context(
                kernel=self._kernel,
                expected_execution=kernel_execution,
                recipe=recipe,
                replay_receipt=external_receipt,
            )
            if external_receipt.replayed
            else None
        )
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            contract=contract,
            replay_context=replay_context,
        )


def _financial_replay_lane_ref(
    operation: GovernedFinancialOperation | str,
) -> str:
    exact_operation = GovernedFinancialOperation(operation)
    return f"{_FINANCIAL_REPLAY_LANE_REF}:{exact_operation.value}"


def _financial_replay_evidence_expectation(
    *,
    recipe: GovernedFinancialRecipe,
    replay_receipt: ExternalActionReceipt,
) -> ExternalActionReplayEvidenceExpectation:
    operation = GovernedFinancialOperation(recipe.scope.operation)
    evidence_refs = tuple(replay_receipt.evidence_refs)
    expected_failure_refs = {
        stable_governed_browser_ref(
            f"evidence-ref:governed-financial:{suffix}",
            {"intent_ref": replay_receipt.intent_ref},
        )
        for suffix in (
            "trusted-clock-invalid",
            "contract-revalidation-failed",
        )
    }
    _require_operation_replay_evidence_envelope(
        replay_receipt,
        success_evidence_valid=evidence_refs == tuple(_success_evidence(recipe)),
        failure_evidence_valid=(
            len(evidence_refs) == 1
            and evidence_refs[0] in expected_failure_refs
        ),
        mismatch_error="GOVERNED_FINANCIAL_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    )
    return ExternalActionReplayEvidenceExpectation(
        lane_ref=_financial_replay_lane_ref(operation),
        operation_ref=recipe.recipe_ref,
        evidence_refs=evidence_refs,
    )


def _financial_replay_validation_context(
    *,
    kernel: GovernedExternalActionKernel,
    expected_execution: ExternalActionExecutionRequest,
    recipe: GovernedFinancialRecipe,
    replay_receipt: ExternalActionReceipt,
) -> ExternalActionReplayValidationContext:
    return _build_external_action_replay_validation_context(
        kernel,
        expected_execution=expected_execution,
        replay_receipt=replay_receipt,
        expectation=_financial_replay_evidence_expectation(
            recipe=recipe,
            replay_receipt=replay_receipt,
        ),
    )


def _kernel_execution(
    request: ExternalActionExecutionRequest,
    *,
    recipe_ref: str,
) -> ExternalActionExecutionRequest:
    return ExternalActionExecutionRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-financial-contract",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe_ref,
                },
            ),
        }
    )


def _recipe_scope_reason(
    recipe: GovernedFinancialRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    expected_resources = recipe.scope.exact_resource_refs(
        authority_ref=recipe.authority_ref,
        contract_ref=recipe.contract_ref,
    )
    bound_authorities = tuple(
        ref for ref in binding.resource_refs if ref.startswith(_AUTHORITY_PREFIX)
    )
    checks = (
        (
            binding.binding_ref == recipe.binding_ref,
            "reason-ref:governed-financial:binding-mismatch",
        ),
        (
            binding.origin_ref == recipe.origin_ref,
            "reason-ref:governed-financial:origin-mismatch",
        ),
        (
            binding.page_snapshot_ref == recipe.page_snapshot_ref,
            "reason-ref:governed-financial:snapshot-mismatch",
        ),
        (
            binding.recipient_ref == recipe.scope.target_ref,
            "reason-ref:governed-financial:target-mismatch",
        ),
        (
            binding.field_schema_ref == recipe.scope.schema_ref,
            "reason-ref:governed-financial:schema-mismatch",
        ),
        (
            binding.artifact_refs == tuple(recipe.scope.artifact_refs),
            "reason-ref:governed-financial:artifact-mismatch",
        ),
        (
            binding.authority_capability
            == _required_capability(
                GovernedFinancialOperation(recipe.scope.operation)
            ).value,
            "reason-ref:governed-financial:capability-mismatch",
        ),
        (
            bound_authorities == (recipe.authority_ref,),
            "reason-ref:governed-financial:authority-mismatch",
        ),
        (
            set(binding.resource_refs) == expected_resources,
            "reason-ref:governed-financial:resource-scope-mismatch",
        ),
        (
            binding.human_present,
            "reason-ref:governed-financial:human-presence-required",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-financial:real-targets-inactive",
        ),
        (
            recipe.expires_at <= binding.start_deadline,
            "reason-ref:governed-financial:recipe-outlives-deadline",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _build_contract(
    recipe: GovernedFinancialRecipe,
) -> ExactGovernedFinancialContract:
    return ExactGovernedFinancialContract(
        contract_ref=recipe.contract_ref,
        authority_ref=recipe.authority_ref,
        origin_ref=recipe.origin_ref,
        page_snapshot_ref=recipe.page_snapshot_ref,
        scope=recipe.scope,
        expires_at=recipe.expires_at,
    )


def _read_clock(
    clock: Callable[[], datetime],
) -> tuple[datetime | None, str | None]:
    try:
        current_time = clock()
    except Exception:
        return None, "reason-ref:governed-financial:trusted-clock-failed"
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        return None, "reason-ref:governed-financial:trusted-clock-invalid"
    try:
        return current_time.astimezone(timezone.utc), None
    except Exception:
        return None, "reason-ref:governed-financial:trusted-clock-invalid"


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
    suffix: str,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                f"evidence-ref:governed-financial:{suffix}",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _success_evidence(recipe: GovernedFinancialRecipe) -> list[str]:
    return [
        recipe.contract_ref,
        recipe.authority_ref,
        recipe.scope.financial_input_ref,
        recipe.scope.quote_ref,
        recipe.scope.payment_handle_ref,
        recipe.scope.rollback_ref,
        recipe.scope.reconciliation_ref,
    ]


def _preflight_blocked(
    request: ExactGovernedFinancialRequest,
    reason_ref: str,
) -> ExactGovernedFinancialResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "contract_ref": request.contract_ref,
        "operation": request.operation,
        "target_ref": request.target_ref,
        "financial_input_ref": request.financial_input_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": GovernedFinancialContractStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(
                receipt_ref="receipt-ref:governed-financial-contract:pending",
                **payload,
            )
        ),
    )
    return ExactGovernedFinancialResult(
        receipt=GovernedFinancialReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactGovernedFinancialRequest,
    recipe: GovernedFinancialRecipe,
    external_receipt: ExternalActionReceipt,
    contract: ExactGovernedFinancialContract | None,
    replay_context: ExternalActionReplayValidationContext | None = None,
) -> ExactGovernedFinancialResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed and state == ExternalActionState.succeeded:
        status = GovernedFinancialContractStatus.replayed_content_free
    elif state == ExternalActionState.succeeded:
        status = GovernedFinancialContractStatus.contract_ready
    else:
        status = {
            ExternalActionState.blocked: (
                GovernedFinancialContractStatus.transaction_blocked
            ),
            ExternalActionState.failed: GovernedFinancialContractStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                GovernedFinancialContractStatus.outcome_ambiguous
            ),
            ExternalActionState.started: (
                GovernedFinancialContractStatus.outcome_ambiguous
            ),
            ExternalActionState.prepared: (
                GovernedFinancialContractStatus.outcome_ambiguous
            ),
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = ["reason-ref:governed-financial:contract-preparation-failed"]
    payload = {
        "recipe_ref": recipe.recipe_ref,
        "contract_ref": recipe.contract_ref,
        "authority_ref": recipe.authority_ref,
        "operation": recipe.scope.operation,
        "target_ref": recipe.scope.target_ref,
        "financial_input_ref": recipe.scope.financial_input_ref,
        "quote_ref": recipe.scope.quote_ref,
        "payment_handle_ref": recipe.scope.payment_handle_ref,
        "rollback_ref": recipe.scope.rollback_ref,
        "reconciliation_ref": recipe.scope.reconciliation_ref,
        "transaction_ref": external_receipt.transaction_ref,
        "intent_ref": external_receipt.intent_ref,
        "binding_ref": external_receipt.binding_ref,
        "status": status,
        "external_action_state": state,
        "external_action_receipt_ref": external_receipt.receipt_ref,
        "approval_validation_ref": external_receipt.approval_validation_ref,
        "authority_decision_ref": external_receipt.authority_decision_ref,
        "budget_reservation_ref": external_receipt.budget_reservation_ref,
        "budget_release_ref": external_receipt.budget_release_ref,
        "budget_settlement_ref": external_receipt.budget_settlement_ref,
        "evidence_refs": list(external_receipt.evidence_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-financial-contract",
        governed_receipt_identity_payload(
            GovernedFinancialReceipt.model_construct(
                receipt_ref="receipt-ref:governed-financial-contract:pending",
                **payload,
            )
        ),
    )
    return ExactGovernedFinancialResult.model_validate(
        {
            "receipt": {"receipt_ref": receipt_ref, **payload},
            "contract": (
                contract.model_dump(mode="json") if contract is not None else None
            ),
        },
        context=(
            replay_validation_context(replay_context)
            if replay_context is not None
            else None
        ),
    )
