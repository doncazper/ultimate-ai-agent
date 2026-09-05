"""Exact durable provenance for projected external-action replay receipts.

Content-addressed receipt refs prove that a payload is internally consistent;
they do not prove that the payload is the terminal receipt durably recorded by
the governed external-action kernel.  This module provides the read-only,
factory-authenticated context required to establish that provenance without
granting any execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Callable, Literal
from weakref import ReferenceType, ref as weakref_ref

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)

from .contracts import (
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    stable_governed_browser_ref,
)


_REPLAY_CONTEXT_KEY = "uaa_external_action_replay_validation_context"
_REPLAY_ENVELOPE_REF_PREFIX = (
    "replay-evidence-envelope-ref:governed-external-action"
)
_KERNEL_AMBIGUITY_REASON_BY_EVIDENCE_SUFFIX = {
    "dispatch-capacity-check-failed": (
        "reason-ref:governed-external-action:dispatch-capacity-check-failed"
    ),
    "dispatch-capacity-bounded": (
        "reason-ref:governed-external-action:dispatch-capacity-bounded"
    ),
    "dispatch-start-revalidation-denied": (
        "reason-ref:governed-external-action:post-start-revalidation-denied"
    ),
    "dispatch-timeout": "reason-ref:governed-external-action:dispatch-timeout",
    "dispatch-exception": (
        "reason-ref:governed-external-action:dispatch-exception"
    ),
    "dispatch-result-invalid": (
        "reason-ref:governed-external-action:dispatch-result-invalid"
    ),
    "dispatch-worker-start-failed": (
        "reason-ref:governed-external-action:dispatch-worker-start-failed"
    ),
}


class _WeakrefableSlots:
    """Supply a Python 3.10-compatible weak-reference slot."""

    __slots__ = ("__weakref__",)
_POST_START_GUARD_REASON_REFS = (
    "reason-ref:governed-external-action:post-start-revalidation-denied",
    (
        "reason-ref:governed-external-action:"
        "dispatch-wait-interrupted-before-start"
    ),
)
_PRIOR_START_RECOVERY_REASON_REF = (
    "reason-ref:governed-external-action:prior-start-unsettled"
)
_BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF = (
    "reason-ref:governed-external-action:budget-settlement-ambiguous"
)
_POST_DISPATCH_REVALIDATION_REASON_REF = (
    "reason-ref:governed-external-action:post-dispatch-revalidation-denied"
)
_POST_DISPATCH_CONCRETE_REASON_REFS = frozenset(
    {
        "reason-ref:governed-external-action:trusted-clock-failed",
        "reason-ref:governed-external-action:trusted-clock-invalid",
        "reason-ref:governed-external-action:deadline-expired",
        "reason-ref:governed-external-action:human-presence-required",
        "reason-ref:governed-external-action:readiness-invalid",
        "reason-ref:governed-external-action:readiness-binding-mismatch",
        "reason-ref:governed-external-action:observed-origin-mismatch",
        "reason-ref:governed-external-action:observed-recipient-mismatch",
        "reason-ref:governed-external-action:observed-field-schema-mismatch",
        "reason-ref:governed-external-action:observed-transaction-mismatch",
        "reason-ref:governed-external-action:observed-artifact-scope-mismatch",
        "reason-ref:governed-external-action:observed-resource-scope-mismatch",
        "reason-ref:governed-external-action:snapshot-changed",
        "reason-ref:governed-external-action:readiness-fail-closed",
        "reason-ref:governed-external-action:safe-disable-active",
        "reason-ref:governed-external-action:kill-switch-engaged",
        "reason-ref:governed-external-action:"
        "approval-changed-before-dispatch",
        "reason-ref:governed-external-action:approval-revalidation-failed",
        "reason-ref:governed-external-action:lease-changed-before-dispatch",
        "reason-ref:governed-external-action:authority-revalidation-failed",
        "reason-ref:governed-external-action:adversarial:cleanup-unverified",
    }
)
_ADVERSARIAL_REASON_REF_PREFIX = (
    "reason-ref:governed-external-action:adversarial:sha256:"
)
_REASON_OVERFLOW_REF_PREFIX = (
    "reason-ref:governed-external-action:reason-overflow:sha256:"
)
_DISPATCH_OUTCOME_AMBIGUOUS_REASON_REF = (
    "reason-ref:governed-external-action:dispatch-outcome-ambiguous"
)
_BUDGET_RELEASE_UNCONFIRMED_REASON_REF = (
    "reason-ref:governed-external-action:budget-release-unconfirmed"
)
_BUDGET_RESERVATION_PROOF_MISSING_REASON_REF = (
    "reason-ref:governed-external-action:budget-reservation-proof-missing"
)
_PRIOR_START_RELEASE_RECONCILED_REASON_REF = (
    "reason-ref:governed-external-action:prior-start-release-reconciled"
)
_BUDGET_RELEASE_DETAIL_REASON_REFS = frozenset(
    {
        "reason-ref:governed-external-action:budget-release-failed",
        "reason-ref:authority-budget:dispatch-owner-required",
        "reason-ref:authority-budget:reservation-not-active",
    }
)
_BUDGET_SETTLEMENT_DETAIL_REASON_REFS = frozenset(
    {
        "reason-ref:governed-external-action:budget-settlement-failed",
        "reason-ref:authority-budget:actual-cost-unresolved",
        "reason-ref:authority-budget:dispatch-owner-required",
        "reason-ref:authority-budget:dispatch-start-required",
        "reason-ref:authority-budget:execution-binding-mismatch",
        "reason-ref:authority-budget:operation-reservation-overage",
        "reason-ref:authority-budget:reservation-not-active",
        "reason-ref:authority-budget:settlement-after-kill-switch",
        "reason-ref:authority-budget:settlement-after-lease-inactive",
        "reason-ref:authority-budget:settlement-overage",
    }
)
_BUDGET_RESERVATION_DETAIL_REASON_REFS = frozenset(
    {
        "reason-ref:governed-external-action:budget-gate-missing",
        "reason-ref:governed-external-action:budget-reservation-failed",
        "reason-ref:governed-external-action:budget-reservation-not-active",
        "reason-ref:authority-budget:actual-cost-unresolved",
        "reason-ref:authority-budget:approval-action-mismatch",
        "reason-ref:authority-budget:approval-missing",
        "reason-ref:authority-budget:approval-not-valid",
        "reason-ref:authority-budget:approval-resource-mismatch",
        "reason-ref:authority-budget:approval-subject-mismatch",
        "reason-ref:authority-budget:approval-subject-type-mismatch",
        "reason-ref:authority-budget:approval-validator-failed",
        "reason-ref:authority-budget:approval-validator-missing",
        "reason-ref:authority-budget:cost-budget-exhausted",
        "reason-ref:authority-budget:cost-budget-missing",
        "reason-ref:authority-budget:cost-claim-mismatch",
        "reason-ref:authority-budget:cost-governor-denied",
        "reason-ref:authority-budget:estimated-cost-unknown",
        "reason-ref:authority-budget:kill-switch-engaged",
        "reason-ref:authority-budget:lease-binding-mismatch",
        "reason-ref:authority-budget:operation-budget-exhausted",
        "reason-ref:authority-budget:operation-budget-missing",
        "reason-ref:authority-budget:operation-claim-mismatch",
        "reason-ref:authority-budget:policy-not-allow",
        "reason-ref:authority-budget:settlement-overage-unreviewed",
    }
)
_APPROVAL_VALIDATION_REF_PREFIX = (
    "approval-validation-ref:governed-external-action:sha256:"
)
_AUTHORITY_DECISION_REF_PREFIX = "authority-policy-decision-ref:sha256:"
_APPROVAL_REASON_REF_PREFIX = (
    "approval-reason-ref:governed-external-action:sha256:"
)
_BLOCKED_STAGE_BY_PRIMARY_REASON = {
    **{
        reason: (False, False, "none")
        for reason in (
        "reason-ref:governed-external-action:real-targets-inactive",
        "reason-ref:governed-external-action:local-validation-disabled",
        "reason-ref:governed-external-action:invalid-activation-state",
        "reason-ref:governed-external-action:policy-evaluation-failed",
        "reason-ref:governed-external-action:policy-denied",
        "reason-ref:governed-external-action:approval-validation-failed",
        )
    },
    "reason-ref:governed-external-action:approval-invalid": (
        True,
        False,
        "none",
    ),
    "reason-ref:governed-external-action:authority-evaluation-failed": (
        True,
        False,
        "none",
    ),
    "reason-ref:governed-external-action:exact-lease-required": (
        True,
        True,
        "none",
    ),
    "reason-ref:governed-external-action:budget-reservation-denied": (
        True,
        True,
        "reservation",
    ),
    "reason-ref:governed-external-action:start-persistence-failed": (
        True,
        True,
        "release",
    ),
    (
        "reason-ref:governed-external-action:"
        "preclaim-revalidation-interrupted"
    ): (True, True, "release"),
}
_BLOCKED_APPROVAL_INVALID_REASON_REF = (
    "reason-ref:governed-external-action:approval-invalid"
)


class ExternalActionReplayEvidenceExpectation(BaseModel):
    """Trusted operation-specific meaning of one exact ordered evidence tuple."""

    schema_version: Literal[
        "uaa-external-action-replay-evidence-expectation.v1"
    ] = "uaa-external-action-replay-evidence-expectation.v1"
    lane_ref: str
    operation_ref: str
    scope_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    operation_proof_ref: str | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_expectation(self) -> "ExternalActionReplayEvidenceExpectation":
        for value, label in (
            (self.lane_ref, "replay_lane_ref"),
            (self.operation_ref, "replay_operation_ref"),
            *[(ref, "replay_scope_ref") for ref in self.scope_refs],
            *[(ref, "replay_evidence_ref") for ref in self.evidence_refs],
            *(
                [(self.operation_proof_ref, "operation_proof_ref")]
                if self.operation_proof_ref is not None
                else []
            ),
        ):
            validate_task_ref(value, label)
        if self.operation_proof_ref is not None and (
            not self.evidence_refs
            or self.evidence_refs[-1] != self.operation_proof_ref
        ):
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_POSITION_INVALID"
            )
        validate_safe_task_payload(
            ExternalActionReplayEvidenceExpectation.model_dump(
                self,
                mode="json",
            ),
            "external_action_replay_evidence_expectation",
        )
        return self


class ExternalActionReplayEvidenceEnvelope(BaseModel):
    """Content-free binding from trusted operation evidence to a terminal row."""

    schema_version: Literal[
        "uaa-external-action-replay-evidence-envelope.v1"
    ] = "uaa-external-action-replay-evidence-envelope.v1"
    envelope_ref: str
    lane_ref: str
    operation_ref: str
    scope_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    operation_proof_ref: str | None = None
    expected_request_fingerprint_ref: str
    terminal_binding_ref: str
    terminal_receipt_ref: str
    terminal_transaction_ref: str

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_envelope(self) -> "ExternalActionReplayEvidenceEnvelope":
        for value, label in (
            (self.envelope_ref, "replay_envelope_ref"),
            (self.lane_ref, "replay_lane_ref"),
            (self.operation_ref, "replay_operation_ref"),
            *[(ref, "replay_scope_ref") for ref in self.scope_refs],
            (
                self.expected_request_fingerprint_ref,
                "expected_request_fingerprint_ref",
            ),
            (self.terminal_binding_ref, "terminal_binding_ref"),
            (self.terminal_receipt_ref, "terminal_receipt_ref"),
            (self.terminal_transaction_ref, "terminal_transaction_ref"),
            *[(ref, "replay_evidence_ref") for ref in self.evidence_refs],
            *(
                [(self.operation_proof_ref, "operation_proof_ref")]
                if self.operation_proof_ref is not None
                else []
            ),
        ):
            validate_task_ref(value, label)
        if self.operation_proof_ref is not None and (
            not self.evidence_refs
            or self.evidence_refs[-1] != self.operation_proof_ref
        ):
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_POSITION_INVALID"
            )
        expected_ref = stable_governed_browser_ref(
            _REPLAY_ENVELOPE_REF_PREFIX,
            ExternalActionReplayEvidenceEnvelope.model_dump(
                self,
                mode="json",
                exclude={"envelope_ref"},
            ),
        )
        if self.envelope_ref != expected_ref:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_ENVELOPE_REF_MISMATCH"
            )
        validate_safe_task_payload(
            ExternalActionReplayEvidenceEnvelope.model_dump(
                self,
                mode="json",
            ),
            "external_action_replay_evidence_envelope",
        )
        return self


class _ReplayContextToken:
    __slots__ = ()


@dataclass(frozen=True, slots=True, init=False)
class ExternalActionReplayValidationContext(_WeakrefableSlots):
    """Opaque, in-process proof that one replay came from the exact terminal row."""

    envelope: ExternalActionReplayEvidenceEnvelope
    expected_execution: ExternalActionExecutionRequest = field(repr=False)
    terminal_receipt: ExternalActionReceipt = field(repr=False)
    _authentication_token: _ReplayContextToken = field(
        repr=False,
        compare=False,
    )

    @classmethod
    def _create(
        cls,
        *,
        envelope: ExternalActionReplayEvidenceEnvelope,
        expected_execution: ExternalActionExecutionRequest,
        terminal_receipt: ExternalActionReceipt,
    ) -> "ExternalActionReplayValidationContext":
        context = object.__new__(cls)
        object.__setattr__(context, "envelope", envelope)
        object.__setattr__(context, "expected_execution", expected_execution)
        object.__setattr__(context, "terminal_receipt", terminal_receipt)
        object.__setattr__(
            context,
            "_authentication_token",
            _ReplayContextToken(),
        )
        return context


@dataclass(frozen=True, slots=True)
class _ReplayContextIssuance:
    context_ref: ReferenceType[ExternalActionReplayValidationContext] = field(
        repr=False,
        compare=False,
    )
    envelope_json: str
    expected_execution_json: str = field(repr=False)
    terminal_receipt_json: str = field(repr=False)


_REPLAY_CONTEXT_ISSUANCE_LOCK = RLock()
_REPLAY_CONTEXT_ISSUANCES: dict[_ReplayContextToken, _ReplayContextIssuance] = {}


def _discard_replay_context_issuance(token: _ReplayContextToken) -> None:
    with _REPLAY_CONTEXT_ISSUANCE_LOCK:
        _REPLAY_CONTEXT_ISSUANCES.pop(token, None)


def _register_replay_context_issuance(
    context: ExternalActionReplayValidationContext,
) -> None:
    token = context._authentication_token
    issuance = _ReplayContextIssuance(
        context_ref=weakref_ref(
            context,
            lambda _context_ref: _discard_replay_context_issuance(token),
        ),
        envelope_json=ExternalActionReplayEvidenceEnvelope.model_dump_json(
            context.envelope
        ),
        expected_execution_json=ExternalActionExecutionRequest.model_dump_json(
            context.expected_execution
        ),
        terminal_receipt_json=ExternalActionReceipt.model_dump_json(
            context.terminal_receipt
        ),
    )
    with _REPLAY_CONTEXT_ISSUANCE_LOCK:
        if token in _REPLAY_CONTEXT_ISSUANCES:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
            )
        _REPLAY_CONTEXT_ISSUANCES[token] = issuance


def _request_fingerprint(
    request: ExternalActionExecutionRequest,
) -> str:
    return stable_governed_browser_ref(
        "request-fingerprint-ref:governed-external-action",
        ExternalActionExecutionRequest.model_dump(request, mode="json"),
    )


def _validated_replay_copy(
    terminal_receipt: ExternalActionReceipt,
) -> ExternalActionReceipt:
    return ExternalActionReceipt.model_validate(
        {
            **ExternalActionReceipt.model_dump(
                terminal_receipt,
                mode="json",
            ),
            "replayed": True,
        }
    )


def _digest_ref_valid(
    value: str | None,
    prefix: str,
    digest_length: int,
) -> bool:
    if value is None or not value.startswith(prefix):
        return False
    digest = value.removeprefix(prefix)
    return len(digest) == digest_length and all(
        character in "0123456789abcdef" for character in digest
    )


def _governance_stage_refs_valid(
    receipt: ExternalActionReceipt,
    *,
    approval_required: bool,
    authority_required: bool,
) -> bool:
    approval_valid = (
        _digest_ref_valid(
            receipt.approval_validation_ref,
            _APPROVAL_VALIDATION_REF_PREFIX,
            64,
        )
        if approval_required
        else receipt.approval_validation_ref is None
    )
    authority_valid = (
        _digest_ref_valid(
            receipt.authority_decision_ref,
            _AUTHORITY_DECISION_REF_PREFIX,
            24,
        )
        if authority_required
        else receipt.authority_decision_ref is None
    )
    return approval_valid and authority_valid


def _hashed_reason_ref_valid(reason_ref: str, prefix: str) -> bool:
    return _digest_ref_valid(reason_ref, prefix, 64)


def _revalidation_reason_valid(reason_ref: str) -> bool:
    return (
        reason_ref in _POST_DISPATCH_CONCRETE_REASON_REFS
        or _hashed_reason_ref_valid(reason_ref, _ADVERSARIAL_REASON_REF_PREFIX)
    )


def _release_detail_reason_valid(reason_ref: str) -> bool:
    return reason_ref in _BUDGET_RELEASE_DETAIL_REASON_REFS


def _settlement_detail_reason_valid(reason_ref: str) -> bool:
    return reason_ref in _BUDGET_SETTLEMENT_DETAIL_REASON_REFS


def _reservation_detail_reason_valid(reason_ref: str) -> bool:
    return reason_ref in _BUDGET_RESERVATION_DETAIL_REASON_REFS


def _bounded_detail_sequence_valid(
    reason_refs: tuple[str, ...],
    *,
    predicate: Callable[[str], bool],
) -> bool:
    overflow_indexes = [
        index
        for index, reason_ref in enumerate(reason_refs)
        if _hashed_reason_ref_valid(
            reason_ref,
            _REASON_OVERFLOW_REF_PREFIX,
        )
    ]
    if len(overflow_indexes) > 1 or (
        overflow_indexes and overflow_indexes[0] != len(reason_refs) - 1
    ):
        return False
    ordinary_refs = (
        reason_refs[:-1] if overflow_indexes else reason_refs
    )
    return all(predicate(reason_ref) for reason_ref in ordinary_refs)


def _segmented_detail_sequence_valid(
    reason_refs: tuple[str, ...],
    *,
    allow_lifecycle: bool,
    require_lifecycle: bool,
    accounting_predicate: Callable[[str], bool] | None,
) -> bool:
    overflow_indexes = [
        index
        for index, reason_ref in enumerate(reason_refs)
        if _hashed_reason_ref_valid(
            reason_ref,
            _REASON_OVERFLOW_REF_PREFIX,
        )
    ]
    if len(overflow_indexes) > 1 or (
        overflow_indexes and overflow_indexes[0] != len(reason_refs) - 1
    ):
        return False
    ordinary_refs = reason_refs[:-1] if overflow_indexes else reason_refs
    lifecycle_count = 0
    if allow_lifecycle:
        while (
            lifecycle_count < len(ordinary_refs)
            and _revalidation_reason_valid(
                ordinary_refs[lifecycle_count]
            )
        ):
            lifecycle_count += 1
    if require_lifecycle and lifecycle_count == 0:
        return False
    accounting_refs = ordinary_refs[lifecycle_count:]
    if accounting_predicate is None:
        return not accounting_refs
    return all(accounting_predicate(ref) for ref in accounting_refs)


def _completed_dispatch_provenance_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    return (
        _governance_stage_refs_valid(
            receipt,
            approval_required=True,
            authority_required=True,
        )
        and receipt.budget_reservation_ref is not None
        and receipt.budget_release_ref is None
        and receipt.budget_settlement_ref is not None
        and not receipt.reason_refs
    )


def _release_accounting_valid(receipt: ExternalActionReceipt) -> bool:
    reasons = tuple(receipt.reason_refs)
    marker_count = reasons.count(_BUDGET_RELEASE_UNCONFIRMED_REASON_REF)
    if (
        receipt.budget_reservation_ref is None
        or receipt.budget_settlement_ref is not None
    ):
        return False
    if receipt.budget_release_ref is not None:
        return marker_count == 0
    return (
        marker_count == 1
        and reasons[-1] == _BUDGET_RELEASE_UNCONFIRMED_REASON_REF
    )


def _settlement_resolution_valid(receipt: ExternalActionReceipt) -> bool:
    reasons = tuple(receipt.reason_refs)
    marker_count = reasons.count(_BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF)
    if (
        receipt.budget_reservation_ref is None
        or receipt.budget_release_ref is not None
    ):
        return False
    if receipt.budget_settlement_ref is not None:
        return marker_count == 0
    return (
        marker_count == 1
        and reasons[-1] == _BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF
    )


def _release_path_valid(
    receipt: ExternalActionReceipt,
    *,
    primary_reason_ref: str,
    allow_revalidation_details: bool = False,
    require_revalidation_detail: bool = False,
    reasons: tuple[str, ...] | None = None,
) -> bool:
    if not _release_accounting_valid(receipt):
        return False
    reasons = tuple(receipt.reason_refs) if reasons is None else reasons
    body = (
        reasons[:-1]
        if receipt.budget_release_ref is None
        else reasons
    )
    if not body or body[0] != primary_reason_ref:
        return False
    details = body[1:]
    if require_revalidation_detail and (
        not details or not _revalidation_reason_valid(details[0])
    ):
        return False
    if receipt.budget_release_ref is not None:
        return _segmented_detail_sequence_valid(
            details,
            allow_lifecycle=(
                allow_revalidation_details or require_revalidation_detail
            ),
            require_lifecycle=require_revalidation_detail,
            accounting_predicate=None,
        )
    return _segmented_detail_sequence_valid(
        details,
        allow_lifecycle=(
            allow_revalidation_details or require_revalidation_detail
        ),
        require_lifecycle=require_revalidation_detail,
        accounting_predicate=_release_detail_reason_valid,
    )


def _settlement_path_valid(
    receipt: ExternalActionReceipt,
    *,
    primary_reason_ref: str,
    allow_revalidation_details: bool = False,
    allow_post_dispatch_segment: bool = False,
    require_revalidation_detail: bool = False,
    reasons: tuple[str, ...] | None = None,
) -> bool:
    if not _settlement_resolution_valid(receipt):
        return False
    reasons = tuple(receipt.reason_refs) if reasons is None else reasons
    body = (
        reasons[:-1]
        if receipt.budget_settlement_ref is None
        else reasons
    )
    if not body or body[0] != primary_reason_ref:
        return False
    details = body[1:]
    if (
        allow_post_dispatch_segment
        and details
        and details[0] == _POST_DISPATCH_REVALIDATION_REASON_REF
    ):
        post_dispatch_details = details[1:]
        if (
            not post_dispatch_details
            or not _revalidation_reason_valid(post_dispatch_details[0])
        ):
            return False
        return _segmented_detail_sequence_valid(
            post_dispatch_details,
            allow_lifecycle=True,
            require_lifecycle=True,
            accounting_predicate=(
                _settlement_detail_reason_valid
                if receipt.budget_settlement_ref is None
                else None
            ),
        )
    if require_revalidation_detail and (
        not details or not _revalidation_reason_valid(details[0])
    ):
        return False
    if receipt.budget_settlement_ref is not None:
        return _segmented_detail_sequence_valid(
            details,
            allow_lifecycle=(
                allow_revalidation_details or require_revalidation_detail
            ),
            require_lifecycle=require_revalidation_detail,
            accounting_predicate=None,
        )
    return _segmented_detail_sequence_valid(
        details,
        allow_lifecycle=(
            allow_revalidation_details or require_revalidation_detail
        ),
        require_lifecycle=require_revalidation_detail,
        accounting_predicate=_settlement_detail_reason_valid,
    )


def _prior_start_recovery_valid(receipt: ExternalActionReceipt) -> bool:
    reasons = tuple(receipt.reason_refs)
    if receipt.budget_reservation_ref is None:
        return (
            reasons
            == (
                _PRIOR_START_RECOVERY_REASON_REF,
                _BUDGET_RESERVATION_PROOF_MISSING_REASON_REF,
            )
            and receipt.budget_release_ref is None
            and receipt.budget_settlement_ref is None
        )
    if receipt.budget_release_ref is not None:
        return (
            receipt.budget_settlement_ref is None
            and reasons
            == (
                _PRIOR_START_RECOVERY_REASON_REF,
                _PRIOR_START_RELEASE_RECONCILED_REASON_REF,
            )
        )
    return _settlement_path_valid(
        receipt,
        primary_reason_ref=_PRIOR_START_RECOVERY_REASON_REF,
    )


def _kernel_ambiguity_accounting_valid(
    receipt: ExternalActionReceipt,
    *,
    evidence_suffix: str,
    required_reason_ref: str,
    reasons: tuple[str, ...] | None = None,
) -> bool:
    reasons = tuple(receipt.reason_refs) if reasons is None else reasons
    if evidence_suffix in {
        "dispatch-capacity-check-failed",
        "dispatch-capacity-bounded",
    }:
        return (
            reasons == (required_reason_ref,)
            and receipt.budget_reservation_ref is None
            and receipt.budget_release_ref is None
            and receipt.budget_settlement_ref is None
        )
    if evidence_suffix == "prior-start-recovery":
        return _prior_start_recovery_valid(receipt)
    if evidence_suffix in {
        "dispatch-start-revalidation-denied",
    }:
        return _release_path_valid(
            receipt,
            primary_reason_ref=required_reason_ref,
            require_revalidation_detail=True,
        )
    if evidence_suffix == "dispatch-worker-start-failed":
        return _release_path_valid(
            receipt,
            primary_reason_ref=required_reason_ref,
        )
    if evidence_suffix == "dispatch-timeout":
        if receipt.budget_release_ref is not None or (
            _BUDGET_RELEASE_UNCONFIRMED_REASON_REF in reasons
        ):
            return _release_path_valid(
                receipt,
                primary_reason_ref=required_reason_ref,
                reasons=reasons,
            )
        return _settlement_path_valid(
            receipt,
            primary_reason_ref=required_reason_ref,
            allow_post_dispatch_segment=True,
        )
    return _settlement_path_valid(
        receipt,
        primary_reason_ref=required_reason_ref,
        allow_post_dispatch_segment=True,
        reasons=reasons,
    )

def _kernel_ambiguity_evidence_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    evidence_refs = tuple(receipt.evidence_refs)
    reasons = tuple(receipt.reason_refs)
    if len(evidence_refs) != 1 or not reasons:
        return False
    evidence_ref = evidence_refs[0]
    common_payload = {
        "transaction_ref": receipt.transaction_ref,
        "intent_ref": receipt.intent_ref,
        "binding_ref": receipt.binding_ref,
    }
    for suffix, required_reason in (
        _KERNEL_AMBIGUITY_REASON_BY_EVIDENCE_SUFFIX.items()
    ):
        expected_ref = stable_governed_browser_ref(
            f"evidence-ref:governed-external-action:{suffix}",
            {"reason": suffix, **common_payload},
        )
        if evidence_ref == expected_ref:
            body_reasons = (
                reasons[1:]
                if (
                    len(reasons) >= 2
                    and reasons[0] == _DISPATCH_OUTCOME_AMBIGUOUS_REASON_REF
                    and reasons[1] == required_reason
                )
                else reasons
            )
            if not body_reasons:
                return False
            governance_valid = (
                _governance_stage_refs_valid(
                    receipt,
                    approval_required=True,
                    authority_required=True,
                )
            )
            return (
                body_reasons[0] == required_reason
                and governance_valid
                and _kernel_ambiguity_accounting_valid(
                    receipt,
                    evidence_suffix=suffix,
                    required_reason_ref=required_reason,
                    reasons=body_reasons,
                )
            )
    prior_start_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:prior-start-recovery",
        common_payload,
    )
    if evidence_ref == prior_start_ref:
        return (
            _governance_stage_refs_valid(
                receipt,
                approval_required=False,
                authority_required=False,
            )
            and _prior_start_recovery_valid(receipt)
        )
    post_start_reasons = (
        reasons[1:]
        if (
            len(reasons) >= 2
            and reasons[0] == _DISPATCH_OUTCOME_AMBIGUOUS_REASON_REF
            and reasons[1] in _POST_START_GUARD_REASON_REFS
        )
        else reasons
    )
    if not post_start_reasons or post_start_reasons[0] not in _POST_START_GUARD_REASON_REFS:
        return False
    expected_guard_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {"intent_ref": receipt.intent_ref, "reason_refs": list(post_start_reasons)},
    )
    return (
        evidence_ref == expected_guard_ref
        and _governance_stage_refs_valid(
            receipt,
            approval_required=True,
            authority_required=True,
        )
        and _release_path_valid(
            receipt,
            primary_reason_ref=post_start_reasons[0],
            require_revalidation_detail=(
                post_start_reasons[0] == _POST_START_GUARD_REASON_REFS[0]
            ),
        )
    )


def _ambiguity_accounting_shape_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    reasons = tuple(receipt.reason_refs)
    release_markers = reasons.count(_BUDGET_RELEASE_UNCONFIRMED_REASON_REF)
    settlement_markers = reasons.count(
        _BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF
    )
    if (
        len(reasons) != len(set(reasons))
        or release_markers > 1
        or settlement_markers > 1
        or (release_markers and settlement_markers)
    ):
        return False
    accounting_proof = (
        receipt.budget_release_ref or receipt.budget_settlement_ref
    )
    return not (
        (
            receipt.budget_reservation_ref is None
            and (accounting_proof or release_markers or settlement_markers)
        )
        or ((release_markers or settlement_markers) and accounting_proof)
    )


def _post_dispatch_revalidation_reasons_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    return _settlement_path_valid(
        receipt,
        primary_reason_ref=_POST_DISPATCH_REVALIDATION_REASON_REF,
        require_revalidation_detail=True,
    )


def _settled_ambiguity_provenance_valid(
    receipt: ExternalActionReceipt,
    *,
    primary_reason_ref: str,
) -> bool:
    return _settlement_path_valid(
        receipt,
        primary_reason_ref=primary_reason_ref,
        allow_post_dispatch_segment=True,
    )


def _accounting_only_settlement_ambiguity_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    if (
        not _settlement_resolution_valid(receipt)
        or receipt.budget_settlement_ref is not None
    ):
        return False
    reasons = tuple(receipt.reason_refs)
    return _bounded_detail_sequence_valid(
        reasons[:-1],
        predicate=_settlement_detail_reason_valid,
    )


def _blocked_provenance_valid(receipt: ExternalActionReceipt) -> bool:
    reasons = tuple(receipt.reason_refs)
    if (
        receipt.evidence_refs
        or not reasons
        or len(reasons) != len(set(reasons))
        or receipt.budget_settlement_ref is not None
    ):
        return False
    primary = reasons[0]
    stage = _BLOCKED_STAGE_BY_PRIMARY_REASON.get(primary)
    if stage is None and _revalidation_reason_valid(primary):
        stage = (True, True, "release")
    if stage is None:
        return False
    approval_required, authority_required, accounting = stage
    if not _governance_stage_refs_valid(
        receipt,
        approval_required=approval_required,
        authority_required=authority_required,
    ):
        return False
    if accounting == "none":
        if receipt.budget_reservation_ref or receipt.budget_release_ref:
            return False
        if primary == _BLOCKED_APPROVAL_INVALID_REASON_REF:
            return all(
                _hashed_reason_ref_valid(reason, _APPROVAL_REASON_REF_PREFIX)
                for reason in reasons[1:]
            )
        return len(reasons) == 1
    if accounting == "reservation":
        if receipt.budget_reservation_ref is None:
            return (
                receipt.budget_release_ref is None
                and len(reasons) >= 1
                and _bounded_detail_sequence_valid(
                    reasons[1:],
                    predicate=_reservation_detail_reason_valid,
                )
            )
        if not _release_accounting_valid(receipt) or reasons.count(
            _BUDGET_RESERVATION_PROOF_MISSING_REASON_REF
        ) != 1:
            return False
        body = (
            reasons[:-1]
            if receipt.budget_release_ref is None
            else reasons
        )
        proof_index = body.index(
            _BUDGET_RESERVATION_PROOF_MISSING_REASON_REF
        )
        if proof_index < 1:
            return False
        reservation_details = body[1:proof_index]
        release_details = body[proof_index + 1 :]
        return (
            _bounded_detail_sequence_valid(
                reservation_details,
                predicate=_reservation_detail_reason_valid,
            )
            and _bounded_detail_sequence_valid(
                release_details,
                predicate=_release_detail_reason_valid,
            )
        )
    if primary in {
        "reason-ref:governed-external-action:start-persistence-failed",
        (
            "reason-ref:governed-external-action:"
            "preclaim-revalidation-interrupted"
        ),
    }:
        return _release_path_valid(
            receipt,
            primary_reason_ref=primary,
        )
    return _release_path_valid(
        receipt,
        primary_reason_ref=primary,
        allow_revalidation_details=True,
    )


def _ambiguity_provenance_valid(
    receipt: ExternalActionReceipt,
    *,
    lane_evidence_valid: bool,
    operation_ambiguity_evidence_valid: bool,
) -> bool:
    if not _ambiguity_accounting_shape_valid(receipt):
        return False
    if _kernel_ambiguity_evidence_valid(receipt):
        return True
    if not _governance_stage_refs_valid(
        receipt,
        approval_required=True,
        authority_required=True,
    ):
        return False
    reason_refs = tuple(receipt.reason_refs)
    if not reason_refs or receipt.budget_reservation_ref is None:
        return False
    primary_reason_ref = reason_refs[0]
    if (
        operation_ambiguity_evidence_valid
        and primary_reason_ref == _DISPATCH_OUTCOME_AMBIGUOUS_REASON_REF
    ):
        return _settled_ambiguity_provenance_valid(
            receipt,
            primary_reason_ref=primary_reason_ref,
        )
    if (
        (lane_evidence_valid or operation_ambiguity_evidence_valid)
        and primary_reason_ref
        == _KERNEL_AMBIGUITY_REASON_BY_EVIDENCE_SUFFIX["dispatch-timeout"]
    ):
        return _settled_ambiguity_provenance_valid(
            receipt,
            primary_reason_ref=primary_reason_ref,
        )
    if not lane_evidence_valid or receipt.budget_release_ref is not None:
        return False
    if lane_evidence_valid and _accounting_only_settlement_ambiguity_valid(
        receipt
    ):
        return True
    if primary_reason_ref == _POST_DISPATCH_REVALIDATION_REASON_REF:
        return _post_dispatch_revalidation_reasons_valid(receipt)
    return False


def _require_operation_replay_evidence_envelope(
    replay_receipt: ExternalActionReceipt,
    *,
    success_evidence_valid: bool,
    failure_evidence_valid: bool,
    operation_ambiguity_evidence_valid: bool = False,
    mismatch_error: str,
) -> None:
    """Require one complete lane envelope for every durable terminal state."""

    state = ExternalActionState(replay_receipt.state)
    if state == ExternalActionState.succeeded:
        valid = (
            success_evidence_valid
            and _completed_dispatch_provenance_valid(replay_receipt)
        )
    elif state == ExternalActionState.failed:
        valid = (
            failure_evidence_valid
            and _completed_dispatch_provenance_valid(replay_receipt)
        )
    elif state == ExternalActionState.blocked:
        valid = _blocked_provenance_valid(replay_receipt)
    elif state == ExternalActionState.outcome_ambiguous:
        valid = _ambiguity_provenance_valid(
            replay_receipt,
            lane_evidence_valid=(
                success_evidence_valid or failure_evidence_valid
            ),
            operation_ambiguity_evidence_valid=(
                operation_ambiguity_evidence_valid
            ),
        )
    else:
        valid = False
    if not valid:
        raise ValueError(mismatch_error)


def _authenticated_context_issuance(
    context: object,
) -> _ReplayContextIssuance:
    if not isinstance(context, ExternalActionReplayValidationContext):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED"
        )
    try:
        token = context._authentication_token
    except AttributeError as exc:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        ) from exc
    if not isinstance(token, _ReplayContextToken):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        )
    with _REPLAY_CONTEXT_ISSUANCE_LOCK:
        issuance = _REPLAY_CONTEXT_ISSUANCES.get(token)
    try:
        context_matches_issuance = (
            issuance is not None
            and issuance.context_ref() is context
            and ExternalActionReplayEvidenceEnvelope.model_dump_json(
                context.envelope
            )
            == issuance.envelope_json
            and ExternalActionExecutionRequest.model_dump_json(
                context.expected_execution
            )
            == issuance.expected_execution_json
            and ExternalActionReceipt.model_dump_json(
                context.terminal_receipt
            )
            == issuance.terminal_receipt_json
        )
    except (AttributeError, TypeError, ValueError):
        context_matches_issuance = False
    if not context_matches_issuance:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        )
    assert issuance is not None
    return issuance


def _require_authenticated_context(
    context: object,
) -> ExternalActionReplayValidationContext:
    if not isinstance(context, ExternalActionReplayValidationContext):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED"
        )
    _authenticated_context_issuance(context)
    return context


def _build_external_action_replay_validation_context(
    kernel: object,
    *,
    expected_execution: ExternalActionExecutionRequest,
    replay_receipt: ExternalActionReceipt,
    expectation: ExternalActionReplayEvidenceExpectation,
) -> ExternalActionReplayValidationContext:
    """Prove one replay against an atomically attested concrete kernel row.

    This package-internal issuer is intentionally not part of the governed
    browser public API. Operation wrappers own the lane/operation expectation;
    untrusted callers may only present the resulting opaque validation context.
    """

    # A structurally compatible object is not a durable proof source. Importing
    # locally avoids a module cycle while requiring the exact production kernel
    # and its concrete SQLite store to own the attestation.
    from .transaction import (  # noqa: PLC0415
        ExternalActionTransactionStore,
        GovernedExternalActionKernel,
        _bound_external_action_replay_store,
    )

    store = _bound_external_action_replay_store(kernel)
    if (
        type(kernel) is not GovernedExternalActionKernel
        or type(store) is not ExternalActionTransactionStore
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_SOURCE_INVALID"
        )

    expected = ExternalActionExecutionRequest.model_validate(
        ExternalActionExecutionRequest.model_dump(
            expected_execution,
            mode="json",
        )
    )
    replay = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_dump(replay_receipt, mode="json")
    )
    exact_expectation = ExternalActionReplayEvidenceExpectation.model_validate(
        ExternalActionReplayEvidenceExpectation.model_dump(
            expectation,
            mode="json",
        )
    )
    try:
        terminal = ExternalActionTransactionStore.attest_terminal_replay(
            store,
            expected,
            receipt_ref=replay.receipt_ref,
        )
    except Exception as exc:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LOOKUP_FAILED"
        ) from exc
    if terminal is None:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_TERMINAL_REQUIRED"
        )
    terminal = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_dump(terminal, mode="json")
    )
    if not replay.replayed or terminal.replayed:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_REPLAY_STATE_INVALID"
        )
    expected_replay = _validated_replay_copy(terminal)
    if replay != expected_replay:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        )
    from .operation_proofs import (  # noqa: PLC0415
        _attest_terminal_receipt_binding,
    )

    try:
        terminal_binding = _attest_terminal_receipt_binding(
            store,
            expected_execution=expected,
            terminal_receipt=terminal,
        )
    except Exception as exc:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID"
        ) from exc
    if (
        terminal.transaction_ref != expected.binding.transaction_ref
        or terminal.evidence_refs != exact_expectation.evidence_refs
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_EVIDENCE_MISMATCH"
        )
    proof_ref = exact_expectation.operation_proof_ref
    if proof_ref is not None:
        from .operation_proofs import (  # noqa: PLC0415
            _attest_operation_proof,
        )

        try:
            _attest_operation_proof(
                kernel,
                expected_execution=expected,
                proof_ref=proof_ref,
                lane_ref=exact_expectation.lane_ref,
                operation_ref=exact_expectation.operation_ref,
                scope_refs=exact_expectation.scope_refs,
                base_evidence_refs=exact_expectation.evidence_refs[:-1],
            )
        except Exception as exc:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_INVALID"
            ) from exc
    elif any(
        ref.startswith("operation-proof-ref:governed-browser:")
        for ref in terminal.evidence_refs
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_UNBOUND"
        )

    envelope_payload = {
        "lane_ref": exact_expectation.lane_ref,
        "operation_ref": exact_expectation.operation_ref,
        "scope_refs": exact_expectation.scope_refs,
        "evidence_refs": exact_expectation.evidence_refs,
        "operation_proof_ref": proof_ref,
        "expected_request_fingerprint_ref": _request_fingerprint(expected),
        "terminal_binding_ref": terminal_binding.terminal_binding_ref,
        "terminal_receipt_ref": terminal.receipt_ref,
        "terminal_transaction_ref": terminal.transaction_ref,
    }
    envelope = ExternalActionReplayEvidenceEnvelope(
        envelope_ref=stable_governed_browser_ref(
            _REPLAY_ENVELOPE_REF_PREFIX,
            {
                "schema_version": (
                    "uaa-external-action-replay-evidence-envelope.v1"
                ),
                **envelope_payload,
            },
        ),
        **envelope_payload,
    )
    context = ExternalActionReplayValidationContext._create(
        envelope=envelope,
        expected_execution=expected,
        terminal_receipt=terminal,
    )
    _register_replay_context_issuance(context)
    return context


def replay_validation_context(
    context: ExternalActionReplayValidationContext,
) -> dict[str, object]:
    """Wrap an authenticated replay context for Pydantic validation."""

    authenticated = _require_authenticated_context(context)
    return {_REPLAY_CONTEXT_KEY: authenticated}


def _authenticated_replay_evidence_envelope(
    context: ExternalActionReplayValidationContext,
) -> ExternalActionReplayEvidenceEnvelope:
    issuance = _authenticated_context_issuance(context)
    return ExternalActionReplayEvidenceEnvelope.model_validate_json(
        issuance.envelope_json
    )


def require_external_action_replay_provenance(
    info_or_context: object,
    *,
    lane_ref: str,
    operation_ref: str,
    candidate: ExternalActionReceipt,
) -> ExternalActionReplayValidationContext:
    """Require exact whole-model provenance for a projected replay receipt."""

    validate_task_ref(lane_ref, "replay_lane_ref")
    validate_task_ref(operation_ref, "replay_operation_ref")
    raw_context = getattr(info_or_context, "context", info_or_context)
    if isinstance(raw_context, ExternalActionReplayValidationContext):
        context = _require_authenticated_context(raw_context)
    elif isinstance(raw_context, dict):
        context = _require_authenticated_context(raw_context.get(_REPLAY_CONTEXT_KEY))
    else:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED"
        )
    issuance = _authenticated_context_issuance(context)
    envelope = ExternalActionReplayEvidenceEnvelope.model_validate_json(
        issuance.envelope_json
    )
    if envelope.lane_ref != lane_ref:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH"
        )
    if envelope.operation_ref != operation_ref:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_OPERATION_MISMATCH"
        )
    expected_execution = ExternalActionExecutionRequest.model_validate_json(
        issuance.expected_execution_json
    )
    expected_fingerprint = _request_fingerprint(expected_execution)
    if envelope.expected_request_fingerprint_ref != expected_fingerprint:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_REQUEST_MISMATCH"
        )
    terminal = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_validate_json(
            issuance.terminal_receipt_json
        ).model_dump(mode="json")
    )
    if (
        terminal.replayed
        or envelope.terminal_receipt_ref != terminal.receipt_ref
        or envelope.terminal_transaction_ref != terminal.transaction_ref
        or envelope.evidence_refs != terminal.evidence_refs
        or (
            envelope.operation_proof_ref is not None
            and (
                not terminal.evidence_refs
                or terminal.evidence_refs[-1]
                != envelope.operation_proof_ref
            )
        )
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        )
    exact_candidate = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_dump(candidate, mode="json")
    )
    if exact_candidate != _validated_replay_copy(terminal):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        )
    return context
