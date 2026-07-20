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
from typing import Literal
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


@dataclass(frozen=True, slots=True, init=False, weakref_slot=True)
class ExternalActionReplayValidationContext:
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


def _kernel_ambiguity_evidence_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    evidence_refs = tuple(receipt.evidence_refs)
    reason_refs = tuple(receipt.reason_refs)
    if len(evidence_refs) != 1 or not reason_refs:
        return False
    evidence_ref = evidence_refs[0]
    common_payload = {
        "transaction_ref": receipt.transaction_ref,
        "intent_ref": receipt.intent_ref,
        "binding_ref": receipt.binding_ref,
    }
    for (
        evidence_suffix,
        required_reason_ref,
    ) in _KERNEL_AMBIGUITY_REASON_BY_EVIDENCE_SUFFIX.items():
        expected_ref = stable_governed_browser_ref(
            f"evidence-ref:governed-external-action:{evidence_suffix}",
            {"reason": evidence_suffix, **common_payload},
        )
        if evidence_ref == expected_ref:
            return reason_refs[0] == required_reason_ref
    prior_start_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:prior-start-recovery",
        common_payload,
    )
    if evidence_ref == prior_start_ref:
        return reason_refs[0] == _PRIOR_START_RECOVERY_REASON_REF
    if reason_refs[0] not in _POST_START_GUARD_REASON_REFS:
        return False
    expected_guard_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {
            "intent_ref": receipt.intent_ref,
            "reason_refs": list(reason_refs),
        },
    )
    return evidence_ref == expected_guard_ref


def _ambiguity_accounting_shape_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    reason_refs = tuple(receipt.reason_refs)
    if _BUDGET_RELEASE_UNCONFIRMED_REASON_REF in reason_refs and (
        receipt.budget_release_ref is not None
        or receipt.budget_settlement_ref is not None
    ):
        return False
    if _BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF in reason_refs and (
        receipt.budget_release_ref is not None
        or receipt.budget_settlement_ref is not None
    ):
        return False
    return True


def _post_dispatch_revalidation_reasons_valid(
    receipt: ExternalActionReceipt,
) -> bool:
    secondary_reasons = tuple(receipt.reason_refs[1:])
    if not secondary_reasons:
        return False
    settlement_marker_index = (
        secondary_reasons.index(_BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF)
        if _BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF in secondary_reasons
        else None
    )
    concrete_reasons = (
        secondary_reasons
        if settlement_marker_index is None
        else secondary_reasons[:settlement_marker_index]
    )
    if not concrete_reasons:
        return False
    for reason_ref in concrete_reasons:
        if reason_ref in _POST_DISPATCH_CONCRETE_REASON_REFS:
            continue
        if reason_ref.startswith(_ADVERSARIAL_REASON_REF_PREFIX):
            digest = reason_ref.removeprefix(_ADVERSARIAL_REASON_REF_PREFIX)
        elif reason_ref.startswith(_REASON_OVERFLOW_REF_PREFIX):
            digest = reason_ref.removeprefix(_REASON_OVERFLOW_REF_PREFIX)
        else:
            return False
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            return False
    if settlement_marker_index is None:
        return receipt.budget_settlement_ref is not None
    return receipt.budget_settlement_ref is None


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
    reason_refs = tuple(receipt.reason_refs)
    if not reason_refs or receipt.budget_reservation_ref is None:
        return False
    primary_reason_ref = reason_refs[0]
    if (
        operation_ambiguity_evidence_valid
        and primary_reason_ref == _DISPATCH_OUTCOME_AMBIGUOUS_REASON_REF
        and receipt.budget_release_ref is None
    ):
        return True
    if not lane_evidence_valid or receipt.budget_release_ref is not None:
        return False
    if primary_reason_ref == _BUDGET_SETTLEMENT_AMBIGUOUS_REASON_REF:
        return receipt.budget_settlement_ref is None
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
    evidence_refs = tuple(replay_receipt.evidence_refs)
    if state == ExternalActionState.succeeded:
        valid = success_evidence_valid
    elif state == ExternalActionState.failed:
        valid = failure_evidence_valid
    elif state == ExternalActionState.blocked:
        valid = not evidence_refs
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
