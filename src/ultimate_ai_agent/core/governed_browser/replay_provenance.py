"""Exact durable provenance for projected external-action replay receipts.

Content-addressed receipt refs prove that a payload is internally consistent;
they do not prove that the payload is the terminal receipt durably recorded by
the governed external-action kernel.  This module provides the read-only,
factory-authenticated context required to establish that provenance without
granting any execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)

from .contracts import (
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    stable_governed_browser_ref,
)


_REPLAY_CONTEXT_KEY = "uaa_external_action_replay_validation_context"
_REPLAY_CONTEXT_TOKEN = object()
_REPLAY_ENVELOPE_REF_PREFIX = (
    "replay-evidence-envelope-ref:governed-external-action"
)


class _ExternalActionReplayKernel(Protocol):
    def replay_if_terminal(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None: ...

    def terminal_receipt_by_ref(
        self,
        *,
        transaction_ref: str,
        receipt_ref: str,
    ) -> ExternalActionReceipt | None: ...


class ExternalActionReplayEvidenceExpectation(BaseModel):
    """Trusted operation-specific meaning of one exact ordered evidence tuple."""

    schema_version: Literal[
        "uaa-external-action-replay-evidence-expectation.v1"
    ] = "uaa-external-action-replay-evidence-expectation.v1"
    lane_ref: str
    operation_ref: str
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)

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
            *[(ref, "replay_evidence_ref") for ref in self.evidence_refs],
        ):
            validate_task_ref(value, label)
        validate_safe_task_payload(
            self.model_dump(mode="json"),
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
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    expected_request_fingerprint_ref: str
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
            (
                self.expected_request_fingerprint_ref,
                "expected_request_fingerprint_ref",
            ),
            (self.terminal_receipt_ref, "terminal_receipt_ref"),
            (self.terminal_transaction_ref, "terminal_transaction_ref"),
            *[(ref, "replay_evidence_ref") for ref in self.evidence_refs],
        ):
            validate_task_ref(value, label)
        expected_ref = stable_governed_browser_ref(
            _REPLAY_ENVELOPE_REF_PREFIX,
            self.model_dump(mode="json", exclude={"envelope_ref"}),
        )
        if self.envelope_ref != expected_ref:
            raise ValueError(
                "GOVERNED_EXTERNAL_ACTION_REPLAY_ENVELOPE_REF_MISMATCH"
            )
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "external_action_replay_evidence_envelope",
        )
        return self


@dataclass(frozen=True, slots=True, init=False)
class ExternalActionReplayValidationContext:
    """Opaque, in-process proof that one replay came from the exact terminal row."""

    envelope: ExternalActionReplayEvidenceEnvelope
    expected_execution: ExternalActionExecutionRequest = field(repr=False)
    terminal_receipt: ExternalActionReceipt = field(repr=False)
    _authentication_token: object = field(repr=False, compare=False)

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
            _REPLAY_CONTEXT_TOKEN,
        )
        return context


def _request_fingerprint(
    request: ExternalActionExecutionRequest,
) -> str:
    return stable_governed_browser_ref(
        "request-fingerprint-ref:governed-external-action",
        request.model_dump(mode="json"),
    )


def _validated_replay_copy(
    terminal_receipt: ExternalActionReceipt,
) -> ExternalActionReceipt:
    return ExternalActionReceipt.model_validate(
        {
            **terminal_receipt.model_dump(mode="json"),
            "replayed": True,
        }
    )


def _require_authenticated_context(
    context: object,
) -> ExternalActionReplayValidationContext:
    if not isinstance(context, ExternalActionReplayValidationContext):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED"
        )
    try:
        authenticated = context._authentication_token is _REPLAY_CONTEXT_TOKEN
    except AttributeError as exc:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        ) from exc
    if not authenticated:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        )
    return context


def build_external_action_replay_validation_context(
    kernel: _ExternalActionReplayKernel,
    *,
    expected_execution: ExternalActionExecutionRequest,
    replay_receipt: ExternalActionReceipt,
    expectation: ExternalActionReplayEvidenceExpectation,
) -> ExternalActionReplayValidationContext:
    """Prove one kernel-returned replay against its exact durable terminal row."""

    expected = ExternalActionExecutionRequest.model_validate(
        expected_execution.model_dump(mode="json")
    )
    replay = ExternalActionReceipt.model_validate(
        replay_receipt.model_dump(mode="json")
    )
    exact_expectation = ExternalActionReplayEvidenceExpectation.model_validate(
        expectation.model_dump(mode="json")
    )
    try:
        exact_replay = kernel.replay_if_terminal(expected)
        terminal = kernel.terminal_receipt_by_ref(
            transaction_ref=expected.binding.transaction_ref,
            receipt_ref=replay.receipt_ref,
        )
    except Exception as exc:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LOOKUP_FAILED"
        ) from exc
    if exact_replay is None or terminal is None:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_TERMINAL_REQUIRED"
        )
    exact_replay = ExternalActionReceipt.model_validate(
        exact_replay.model_dump(mode="json")
    )
    terminal = ExternalActionReceipt.model_validate(
        terminal.model_dump(mode="json")
    )
    if not replay.replayed or not exact_replay.replayed or terminal.replayed:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_REPLAY_STATE_INVALID"
        )
    expected_replay = _validated_replay_copy(terminal)
    if exact_replay != expected_replay or replay != expected_replay:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        )
    if (
        terminal.transaction_ref != expected.binding.transaction_ref
        or terminal.evidence_refs != exact_expectation.evidence_refs
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_EVIDENCE_MISMATCH"
        )

    envelope_payload = {
        "lane_ref": exact_expectation.lane_ref,
        "operation_ref": exact_expectation.operation_ref,
        "evidence_refs": exact_expectation.evidence_refs,
        "expected_request_fingerprint_ref": _request_fingerprint(expected),
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
    return ExternalActionReplayValidationContext._create(
        envelope=envelope,
        expected_execution=expected,
        terminal_receipt=terminal,
    )


def replay_validation_context(
    context: ExternalActionReplayValidationContext,
) -> dict[str, object]:
    """Wrap an authenticated replay context for Pydantic validation."""

    authenticated = _require_authenticated_context(context)
    return {_REPLAY_CONTEXT_KEY: authenticated}


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
    envelope = context.envelope
    if envelope.lane_ref != lane_ref:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_LANE_MISMATCH"
        )
    if envelope.operation_ref != operation_ref:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_OPERATION_MISMATCH"
        )
    expected_fingerprint = _request_fingerprint(context.expected_execution)
    if envelope.expected_request_fingerprint_ref != expected_fingerprint:
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_REQUEST_MISMATCH"
        )
    terminal = ExternalActionReceipt.model_validate(
        context.terminal_receipt.model_dump(mode="json")
    )
    if (
        terminal.replayed
        or envelope.terminal_receipt_ref != terminal.receipt_ref
        or envelope.terminal_transaction_ref != terminal.transaction_ref
        or envelope.evidence_refs != terminal.evidence_refs
    ):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_INVALID"
        )
    exact_candidate = ExternalActionReceipt.model_validate(
        candidate.model_dump(mode="json")
    )
    if exact_candidate != _validated_replay_copy(terminal):
        raise ValueError(
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        )
    return context
