"""Readable Action Inbox projection for exact governed external actions.

This module is a backend-owned read model.  It does not execute a browser,
activate an external target, validate an approval, or turn a handoff control
into authority.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    GOVERNED_EXTERNAL_ACTION_ADAPTER_REF,
    GOVERNED_EXTERNAL_ACTION_ROLLBACK_REF,
    GOVERNED_EXTERNAL_ACTION_SAFE_DISABLE_REF,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    build_external_action_approval_request,
    stable_governed_browser_ref,
)


GOVERNED_EXTERNAL_ACTION_INBOX_CONTRACT_REF = (
    "contract-ref:governed-external-action-inbox-envelope:v1"
)
_ACCOUNTING_RECONCILIATION_REASON_MARKERS = (
    "budget-release-unconfirmed",
    "budget-settlement-ambiguous",
)


class ExternalActionInboxStatus(str, Enum):
    review_required = "review_required"
    blocked_inactive = "blocked_inactive"
    expired = "expired"
    receipt_recorded = "receipt_recorded"
    reconciliation_required = "reconciliation_required"


class ExternalActionSideEffectPosture(str, Enum):
    validation_only = "validation_only"
    external_mutation_inactive = "external_mutation_inactive"


class ExternalActionReversibilityPosture(str, Enum):
    not_applicable_local_validation = "not_applicable_local_validation"
    unknown_manual_review_required = "unknown_manual_review_required"


class ExternalActionRetryPosture(str, Enum):
    fresh_approval_and_revalidation_required = (
        "fresh_approval_and_revalidation_required"
    )
    terminal_no_retry = "terminal_no_retry"
    manual_reconciliation_required_no_retry = (
        "manual_reconciliation_required_no_retry"
    )


class ExternalActionReconciliationStatus(str, Enum):
    pending_dispatch = "pending_dispatch"
    not_required = "not_required"
    verified = "verified"
    required = "required"


class ExternalActionHandoffKind(str, Enum):
    open_in_browser = "open_in_browser"
    human_takeover = "human_takeover"


class ExternalActionManualHandoff(BaseModel):
    """Visible operator control with no UAA execution handler."""

    handoff_ref: str = Field(..., min_length=1, max_length=240)
    kind: ExternalActionHandoffKind
    label: str = Field(..., min_length=1, max_length=80)
    status: Literal["manual_handoff_only", "request_expired"]
    target_ref: str = Field(..., min_length=1, max_length=240)
    human_presence_ref: str = Field(..., min_length=1, max_length=240)
    visible: Literal[True] = True
    available: StrictBool
    requires_human_presence: Literal[True] = True
    uaa_execution_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    external_mutation_enabled: Literal[False] = False
    performed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_handoff(self) -> "ExternalActionManualHandoff":
        for value, label in (
            (self.handoff_ref, "handoff_ref"),
            (self.target_ref, "target_ref"),
            (self.human_presence_ref, "human_presence_ref"),
        ):
            validate_task_ref(value, label)
        validate_safe_task_text(self.label, "label")
        expected_label = {
            ExternalActionHandoffKind.open_in_browser.value: "Open in browser",
            ExternalActionHandoffKind.human_takeover.value: "Human takeover",
        }[self.kind]
        if self.label != expected_label:
            raise ValueError("GOVERNED_BROWSER_HANDOFF_LABEL_MISMATCH")
        if self.status == "request_expired" and self.available:
            raise ValueError("GOVERNED_BROWSER_EXPIRED_HANDOFF_MUST_BE_UNAVAILABLE")
        return self


class ExternalActionInboxExecutionEnvelope(BaseModel):
    """Content-free Action Inbox contract for one exact external action."""

    schema_version: Literal["uaa-governed-external-action-inbox-envelope.v1"] = (
        "uaa-governed-external-action-inbox-envelope.v1"
    )
    contract_ref: Literal[
        "contract-ref:governed-external-action-inbox-envelope:v1"
    ] = GOVERNED_EXTERNAL_ACTION_INBOX_CONTRACT_REF
    envelope_ref: str = Field(..., min_length=1, max_length=240)
    intent_ref: str = Field(..., min_length=1, max_length=240)
    binding_ref: str = Field(..., min_length=1, max_length=240)
    transaction_ref: str = Field(..., min_length=1, max_length=240)
    exact_scope_refs: list[str] = Field(..., min_length=1, max_length=24)
    readable_scope: str = Field(..., min_length=1, max_length=400)
    side_effect_posture: ExternalActionSideEffectPosture
    data_classification: Literal["project_private"] = "project_private"
    expires_at: datetime
    expiry_posture: Literal["active", "expired"]
    reversibility_posture: ExternalActionReversibilityPosture
    retry_posture: ExternalActionRetryPosture
    approval_fingerprint_ref: str = Field(..., min_length=1, max_length=240)
    approval_ref_is_identifier_only: Literal[True] = True
    approval_validation_ref: str | None = Field(default=None, max_length=240)
    approval_revalidation_required_before_dispatch: Literal[True] = True
    expected_receipt_refs: list[str] = Field(..., min_length=1, max_length=4)
    receipt_refs: list[str] = Field(default_factory=list, max_length=8)
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reconciliation_ref: str = Field(..., min_length=1, max_length=240)
    reconciliation_status: ExternalActionReconciliationStatus
    reconciliation_required: StrictBool
    status: ExternalActionInboxStatus
    safe_disable_ref: Literal[
        "safe-disable-ref:governed-external-actions:inactive"
    ] = GOVERNED_EXTERNAL_ACTION_SAFE_DISABLE_REF
    safe_disable_active: StrictBool
    kill_switch_engaged: StrictBool
    rollback_ref: Literal[
        "rollback-ref:governed-external-action-manual-review"
    ] = GOVERNED_EXTERNAL_ACTION_ROLLBACK_REF
    reason_refs: list[str] = Field(default_factory=list, max_length=20)
    open_in_browser: ExternalActionManualHandoff
    human_takeover: ExternalActionManualHandoff
    backend_owned: Literal[True] = True
    content_free: Literal[True] = True
    raw_content_included: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False
    uaa_execution_enabled: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_envelope(self) -> "ExternalActionInboxExecutionEnvelope":
        for value, label in (
            (self.contract_ref, "contract_ref"),
            (self.envelope_ref, "envelope_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.approval_fingerprint_ref, "approval_fingerprint_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.reconciliation_ref, "reconciliation_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.rollback_ref, "rollback_ref"),
        ):
            if value is not None:
                validate_task_ref(value, label)
        for field_name in (
            "exact_scope_refs",
            "expected_receipt_refs",
            "receipt_refs",
            "evidence_refs",
            "reason_refs",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(
                    f"GOVERNED_BROWSER_INBOX_DUPLICATE_{field_name.upper()}"
                )
            for value in values:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.readable_scope, "readable_scope")
        if self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_BROWSER_INBOX_EXPIRY_TIMEZONE_REQUIRED")
        if (
            self.reconciliation_required
            != (
                self.reconciliation_status
                == ExternalActionReconciliationStatus.required.value
            )
        ):
            raise ValueError("GOVERNED_BROWSER_INBOX_RECONCILIATION_POSTURE_MISMATCH")
        if (
            self.status == ExternalActionInboxStatus.reconciliation_required.value
            and not self.reconciliation_required
        ):
            raise ValueError("GOVERNED_BROWSER_INBOX_RECONCILIATION_REQUIRED")
        if (
            self.expiry_posture == "expired"
            and self.status
            not in {
                ExternalActionInboxStatus.expired.value,
                ExternalActionInboxStatus.receipt_recorded.value,
                ExternalActionInboxStatus.reconciliation_required.value,
            }
        ):
            raise ValueError("GOVERNED_BROWSER_INBOX_EXPIRED_STATUS_REQUIRED")
        if self.open_in_browser.kind != ExternalActionHandoffKind.open_in_browser.value:
            raise ValueError("GOVERNED_BROWSER_OPEN_HANDOFF_REQUIRED")
        if self.human_takeover.kind != ExternalActionHandoffKind.human_takeover.value:
            raise ValueError("GOVERNED_BROWSER_TAKEOVER_HANDOFF_REQUIRED")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "governed_browser_action_inbox_envelope"
        )
        return self


def build_external_action_inbox_envelope(
    request: ExternalActionExecutionRequest,
    *,
    receipt: ExternalActionReceipt | None = None,
    safe_disable_active: bool,
    kill_switch_engaged: bool,
    now: datetime | None = None,
) -> ExternalActionInboxExecutionEnvelope:
    """Project one exact request and optional matching receipt into safe UI data."""

    observed_at = now or utc_now()
    if observed_at.tzinfo is None:
        raise ValueError("GOVERNED_BROWSER_INBOX_CLOCK_TIMEZONE_REQUIRED")
    if receipt is not None and (
        receipt.transaction_ref != request.binding.transaction_ref
        or receipt.intent_ref != request.intent_ref
        or receipt.binding_ref != request.binding.binding_ref
    ):
        raise ValueError("GOVERNED_BROWSER_INBOX_RECEIPT_BINDING_MISMATCH")

    approval = build_external_action_approval_request(request)
    approval_fingerprint_ref = stable_governed_browser_ref(
        "approval-fingerprint-ref:governed-external-action",
        {
            "approval_ref": request.approval_ref,
            "approval_request_id": approval.approval_request_id,
            "subject_id": approval.subject_id,
            "requested_action": approval.requested_action,
            "resource_refs": approval.resource_refs,
            "risk_level": approval.risk_level,
            "data_classification": approval.data_classification.model_dump(mode="json"),
            "expires_at": approval.expires_at,
        },
    )
    expiry_posture = (
        "expired" if observed_at >= request.binding.start_deadline else "active"
    )
    target_is_external = (
        request.binding.target_kind == ExternalActionTargetKind.external.value
    )
    side_effect_posture = (
        ExternalActionSideEffectPosture.external_mutation_inactive
        if target_is_external
        else ExternalActionSideEffectPosture.validation_only
    )
    reversibility_posture = (
        ExternalActionReversibilityPosture.unknown_manual_review_required
        if target_is_external
        else ExternalActionReversibilityPosture.not_applicable_local_validation
    )
    reason_refs: list[str] = []
    if target_is_external:
        reason_refs.append(
            "reason-ref:governed-external-action:real-targets-inactive"
        )
    if expiry_posture == "expired":
        reason_refs.append("reason-ref:governed-external-action:deadline-expired")
    if not request.binding.human_present:
        reason_refs.append(
            "reason-ref:governed-external-action:human-presence-required"
        )
    if safe_disable_active:
        reason_refs.append(
            "reason-ref:governed-external-action:safe-disable-active"
        )
    if kill_switch_engaged:
        reason_refs.append(
            "reason-ref:governed-external-action:kill-switch-engaged"
        )
    if receipt is not None:
        reason_refs.extend(receipt.reason_refs)
    reason_refs = list(dict.fromkeys(reason_refs))

    reconciliation_status, reconciliation_required = _reconciliation_posture(
        receipt
    )
    retry_posture = _retry_posture(receipt)
    status = _inbox_status(
        receipt=receipt,
        expiry_posture=expiry_posture,
        blocked=bool(reason_refs),
        reconciliation_required=reconciliation_required,
    )
    handoff_status = (
        "request_expired" if expiry_posture == "expired" else "manual_handoff_only"
    )
    handoff_available = (
        expiry_posture == "active" and request.binding.human_present
    )
    expected_receipt_refs = [
        stable_governed_browser_ref(
            "expected-receipt-ref:governed-external-action",
            {"intent_ref": request.intent_ref, "kind": "transaction"},
        ),
        stable_governed_browser_ref(
            "expected-receipt-ref:governed-external-action",
            {"intent_ref": request.intent_ref, "kind": "budget-settlement"},
        ),
    ]
    receipt_refs: list[str] = []
    evidence_refs: list[str] = []
    approval_validation_ref: str | None = None
    if receipt is not None:
        receipt_refs.append(receipt.receipt_ref)
        if receipt.budget_release_ref:
            receipt_refs.append(receipt.budget_release_ref)
        if receipt.budget_settlement_ref:
            receipt_refs.append(receipt.budget_settlement_ref)
        evidence_refs.extend(receipt.evidence_refs)
        approval_validation_ref = receipt.approval_validation_ref

    exact_scope_refs = [
        request.lease_ref,
        GOVERNED_EXTERNAL_ACTION_ADAPTER_REF,
        *request.binding.exact_resource_refs(),
    ]
    reconciliation_ref = stable_governed_browser_ref(
        "reconciliation-ref:governed-external-action",
        {
            "transaction_ref": request.binding.transaction_ref,
            "intent_ref": request.intent_ref,
        },
    )
    envelope_ref = stable_governed_browser_ref(
        "action-inbox-envelope-ref:governed-external-action",
        {
            "intent_ref": request.intent_ref,
            "approval_fingerprint_ref": approval_fingerprint_ref,
            "expiry_posture": expiry_posture,
            "receipt_ref": receipt.receipt_ref if receipt else None,
            "safe_disable_active": safe_disable_active,
            "kill_switch_engaged": kill_switch_engaged,
        },
    )
    return ExternalActionInboxExecutionEnvelope(
        envelope_ref=envelope_ref,
        intent_ref=request.intent_ref,
        binding_ref=request.binding.binding_ref,
        transaction_ref=request.binding.transaction_ref,
        exact_scope_refs=exact_scope_refs,
        readable_scope=(
            "One exact origin, recipient, field schema, transaction, artifact set, "
            "resource set, page snapshot, deadline, human-presence assertion, and "
            "single action."
        ),
        side_effect_posture=side_effect_posture,
        expires_at=request.binding.start_deadline,
        expiry_posture=expiry_posture,
        reversibility_posture=reversibility_posture,
        retry_posture=retry_posture,
        approval_fingerprint_ref=approval_fingerprint_ref,
        approval_validation_ref=approval_validation_ref,
        expected_receipt_refs=expected_receipt_refs,
        receipt_refs=list(dict.fromkeys(receipt_refs)),
        evidence_refs=list(dict.fromkeys(evidence_refs)),
        reconciliation_ref=reconciliation_ref,
        reconciliation_status=reconciliation_status,
        reconciliation_required=reconciliation_required,
        status=status,
        safe_disable_active=safe_disable_active,
        kill_switch_engaged=kill_switch_engaged,
        reason_refs=reason_refs,
        open_in_browser=_handoff(
            request,
            kind=ExternalActionHandoffKind.open_in_browser,
            label="Open in browser",
            status=handoff_status,
            available=handoff_available,
            target_ref=request.binding.origin_ref,
        ),
        human_takeover=_handoff(
            request,
            kind=ExternalActionHandoffKind.human_takeover,
            label="Human takeover",
            status=handoff_status,
            available=handoff_available,
            target_ref=request.binding.transaction_ref,
        ),
    )


def _handoff(
    request: ExternalActionExecutionRequest,
    *,
    kind: ExternalActionHandoffKind,
    label: str,
    status: Literal["manual_handoff_only", "request_expired"],
    available: bool,
    target_ref: str,
) -> ExternalActionManualHandoff:
    return ExternalActionManualHandoff(
        handoff_ref=stable_governed_browser_ref(
            "handoff-ref:governed-external-action",
            {
                "intent_ref": request.intent_ref,
                "kind": kind.value,
                "target_ref": target_ref,
            },
        ),
        kind=kind,
        label=label,
        status=status,
        target_ref=target_ref,
        human_presence_ref=request.binding.human_presence_ref,
        available=available,
    )


def _reconciliation_posture(
    receipt: ExternalActionReceipt | None,
) -> tuple[ExternalActionReconciliationStatus, bool]:
    if receipt is None:
        return ExternalActionReconciliationStatus.pending_dispatch, False
    if receipt.state == ExternalActionState.succeeded.value and receipt.evidence_refs:
        return ExternalActionReconciliationStatus.verified, False
    if any(
        marker in reason_ref
        for reason_ref in receipt.reason_refs
        for marker in _ACCOUNTING_RECONCILIATION_REASON_MARKERS
    ):
        return ExternalActionReconciliationStatus.required, True
    if receipt.state == ExternalActionState.blocked.value:
        return ExternalActionReconciliationStatus.not_required, False
    return ExternalActionReconciliationStatus.required, True


def _retry_posture(
    receipt: ExternalActionReceipt | None,
) -> ExternalActionRetryPosture:
    if receipt is None:
        return ExternalActionRetryPosture.fresh_approval_and_revalidation_required
    if receipt.state in {
        ExternalActionState.failed.value,
        ExternalActionState.outcome_ambiguous.value,
        ExternalActionState.prepared.value,
        ExternalActionState.started.value,
    }:
        return ExternalActionRetryPosture.manual_reconciliation_required_no_retry
    return ExternalActionRetryPosture.terminal_no_retry


def _inbox_status(
    *,
    receipt: ExternalActionReceipt | None,
    expiry_posture: str,
    blocked: bool,
    reconciliation_required: bool,
) -> ExternalActionInboxStatus:
    if reconciliation_required:
        return ExternalActionInboxStatus.reconciliation_required
    if receipt is not None:
        return ExternalActionInboxStatus.receipt_recorded
    if expiry_posture == "expired":
        return ExternalActionInboxStatus.expired
    if blocked:
        return ExternalActionInboxStatus.blocked_inactive
    return ExternalActionInboxStatus.review_required
