from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest
from ultimate_ai_agent.core.execution.connector_delivery import (
    ConnectorDeliveryReviewQueueReadModel,
    build_connector_delivery_review_queue,
)
from ultimate_ai_agent.core.execution.run_storage import (
    AppendFirstRunStorage,
    DurableRunStorageEntryKind,
)
from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.time import utc_now


RUN_ATTACHED_APPROVAL_QUEUE_ITEM_SCHEMA_VERSION = "run_attached_approval_queue_item.v1"
RUN_ATTACHED_APPROVAL_QUEUE_SUMMARY_SCHEMA_VERSION = "run_attached_approval_queue_summary.v1"
RUN_ATTACHED_APPROVAL_QUEUE_SCHEMA_VERSION = "run_attached_approval_queue.v1"
RUN_ATTACHED_APPROVAL_EVENT_RECEIPT_SCHEMA_VERSION = "run_attached_approval_event_receipt.v1"
UNIFIED_APPROVAL_REVIEW_ITEM_SCHEMA_VERSION = "unified_approval_review_item.v1"
UNIFIED_APPROVAL_REVIEW_SCHEMA_VERSION = "unified_approval_review.v1"

RunAttachedApprovalState = Literal[
    "requested",
    "approved",
    "denied",
    "expired",
    "revoked",
    "scope_mismatch_blocked",
    "blocked",
]

RunAttachedApprovalEventType = Literal[
    "approval_required",
    "approval_attached",
    "approval_denied",
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
]

DurableApprovalAttachmentStatus = Literal[
    "attached",
    "durable_attachment_missing",
    "approval_state_missing",
]

UnifiedApprovalReviewSource = Literal[
    "durable_run",
    "provider_tool_contract",
    "connector_delivery",
    "coworker_handoff",
]

RUN_ATTACHED_APPROVAL_STATES: tuple[RunAttachedApprovalState, ...] = (
    "requested",
    "approved",
    "denied",
    "expired",
    "revoked",
    "scope_mismatch_blocked",
    "blocked",
)

RUN_ATTACHED_APPROVAL_EVENT_TYPES: tuple[RunAttachedApprovalEventType, ...] = (
    "approval_required",
    "approval_attached",
    "approval_denied",
    "approval_expired",
    "approval_revoked",
    "approval_scope_mismatch_blocked",
)

RUN_ATTACHED_APPROVAL_STATE_TO_EVENT: dict[
    RunAttachedApprovalState, RunAttachedApprovalEventType
] = {
    "requested": "approval_required",
    "approved": "approval_attached",
    "denied": "approval_denied",
    "expired": "approval_expired",
    "revoked": "approval_revoked",
    "scope_mismatch_blocked": "approval_scope_mismatch_blocked",
    "blocked": "approval_scope_mismatch_blocked",
}

PENDING_RUN_ATTACHED_APPROVAL_STATES = {
    "requested",
    "scope_mismatch_blocked",
    "blocked",
}
RESOLVED_RUN_ATTACHED_APPROVAL_STATES = {
    "approved",
    "denied",
    "expired",
    "revoked",
}
RUN_ATTACHED_APPROVAL_STATE_ORDER: dict[RunAttachedApprovalState, int] = {
    "requested": 10,
    "scope_mismatch_blocked": 20,
    "blocked": 30,
    "approved": 40,
    "denied": 50,
    "expired": 60,
    "revoked": 70,
}


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _safe_external_ref(prefix: str, value: str | None, fallback: str = "missing") -> str:
    candidate = (value or "").strip()
    if candidate:
        try:
            validate_execution_ref(candidate, prefix)
            return candidate
        except ValueError:
            return _stable_ref(prefix, candidate)
    return _stable_ref(prefix, fallback)


def _hashed_external_ref(prefix: str, value: str | None, fallback: str = "missing") -> str:
    candidate = (value or fallback).strip()
    seed = candidate or fallback
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    ref = f"{prefix}:{digest}"
    validate_execution_ref(ref, prefix)
    return ref


def _sorted_unique(refs: Iterable[str | None]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        if not ref:
            continue
        validate_execution_ref(ref, "approval_queue_ref")
        safe_refs.append(ref)
    return sorted(dict.fromkeys(safe_refs))


def _state_for_grant(grant: ApprovalGrant, *, now: datetime | None = None) -> RunAttachedApprovalState:
    status = str(grant.status)
    if grant.revoked_at is not None or status == "revoked":
        return "revoked"
    effective_now = now or utc_now()
    if grant.expires_at is not None and grant.expires_at <= effective_now:
        return "expired"
    return "approved"


def run_attached_approval_event_type(
    approval_state: RunAttachedApprovalState,
) -> RunAttachedApprovalEventType:
    return RUN_ATTACHED_APPROVAL_STATE_TO_EVENT[approval_state]


class RunAttachedApprovalQueueItemReadModel(BaseModel):
    schema_version: str = RUN_ATTACHED_APPROVAL_QUEUE_ITEM_SCHEMA_VERSION
    item_ref: str = Field(..., min_length=1)
    approval_request_ref: str = Field(..., min_length=1)
    approval_grant_ref: str | None = None
    run_ref: str = Field(..., min_length=1)
    step_ref: str = Field(..., min_length=1)
    requested_scope_ref: str = Field(..., min_length=1)
    approval_state: RunAttachedApprovalState
    approval_event_type: RunAttachedApprovalEventType
    approval_decision_ref: str | None = None
    approval_receipt_ref: str | None = None
    approval_scope_validation_ref: str | None = None
    expiry_ref: str | None = None
    revocation_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    idempotency_key_refs: list[str] = Field(default_factory=list)
    durable_attachment_status: DurableApprovalAttachmentStatus = "durable_attachment_missing"
    safe_summary: str = Field(..., min_length=1)
    required_next_action: str = "inspect_only_no_ui_mutation"
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_refs_are_identifiers_only: bool = True
    approval_authority_enabled: bool = False
    execution_authority_enabled: bool = False
    ui_mutation_controls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    model_call_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> Any:
        refs = [
            (self.item_ref, "item_ref"),
            (self.approval_request_ref, "approval_request_ref"),
            (self.run_ref, "run_ref"),
            (self.step_ref, "step_ref"),
            (self.requested_scope_ref, "requested_scope_ref"),
        ]
        optional_refs = [
            (self.approval_grant_ref, "approval_grant_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.approval_receipt_ref, "approval_receipt_ref"),
            (self.approval_scope_validation_ref, "approval_scope_validation_ref"),
            (self.expiry_ref, "expiry_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]
        for value, field_name in refs:
            validate_execution_ref(value, field_name)
        for value, field_name in optional_refs:
            if value:
                validate_execution_ref(value, field_name)
        for ref in [
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.receipt_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.idempotency_key_refs,
        ]:
            validate_execution_ref(ref, "run_attached_approval_queue_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.approval_state, "approval_state"),
            (self.approval_event_type, "approval_event_type"),
            (self.durable_attachment_status, "durable_attachment_status"),
            (self.safe_summary, "safe_summary"),
            (self.required_next_action, "required_next_action"),
        ]:
            validate_safe_execution_text(text, field_name)
        if self.approval_event_type != run_attached_approval_event_type(self.approval_state):
            raise ValueError("RUN_ATTACHED_APPROVAL_EVENT_TYPE_MISMATCH")
        if self.approval_state == "approved":
            if not self.approval_decision_ref or not self.approval_receipt_ref:
                raise ValueError("RUN_ATTACHED_APPROVAL_APPROVED_REFS_REQUIRED")
        if self.approval_state == "denied" and not self.approval_decision_ref:
            raise ValueError("RUN_ATTACHED_APPROVAL_DENIAL_DECISION_REF_REQUIRED")
        if self.approval_state == "expired" and not self.expiry_ref:
            raise ValueError("RUN_ATTACHED_APPROVAL_EXPIRY_REF_REQUIRED")
        if self.approval_state == "revoked" and not self.revocation_ref:
            raise ValueError("RUN_ATTACHED_APPROVAL_REVOCATION_REF_REQUIRED")
        if self.approval_state in {"scope_mismatch_blocked", "blocked"} and not self.blocked_authority_refs:
            raise ValueError("RUN_ATTACHED_APPROVAL_BLOCKED_REFS_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("RUN_ATTACHED_APPROVAL_RAW_PAYLOADS_DENIED")
        if not self.approval_refs_are_identifiers_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_IDENTIFIER_ONLY_REFS_REQUIRED")
        if any(
            [
                self.approval_authority_enabled,
                self.execution_authority_enabled,
                self.ui_mutation_controls_enabled,
                self.tool_execution_enabled,
                self.connector_writes_enabled,
                self.model_call_enabled,
            ]
        ):
            raise ValueError("RUN_ATTACHED_APPROVAL_AUTHORITY_DENIED")
        return self

    def to_receipt_summary(self) -> dict[str, Any]:
        return {
            "schema_version": RUN_ATTACHED_APPROVAL_EVENT_RECEIPT_SCHEMA_VERSION,
            "run_approval_event_type": self.approval_event_type,
            "approval_state": self.approval_state,
            "approval_request_ref": self.approval_request_ref,
            "approval_grant_ref": self.approval_grant_ref,
            "run_ref": self.run_ref,
            "step_ref": self.step_ref,
            "requested_scope_ref": self.requested_scope_ref,
            "approval_decision_ref": self.approval_decision_ref,
            "approval_receipt_ref": self.approval_receipt_ref,
            "approval_scope_validation_ref": self.approval_scope_validation_ref,
            "expiry_ref": self.expiry_ref,
            "revocation_ref": self.revocation_ref,
            "evidence_refs": list(self.evidence_refs),
            "blocked_authority_refs": list(self.blocked_authority_refs),
            "safe_refs_only": True,
            "raw_payloads_persisted": False,
            "approval_refs_are_identifiers_only": True,
            "approval_authority_enabled": False,
            "execution_authority_enabled": False,
            "ui_mutation_controls_enabled": False,
        }


class RunAttachedApprovalRunBucketReadModel(BaseModel):
    run_ref: str = Field(..., min_length=1)
    pending_approval_refs: list[str] = Field(default_factory=list)
    approval_history_refs: list[str] = Field(default_factory=list)
    latest_approval_state: RunAttachedApprovalState | None = None
    durable_attachment_statuses: list[DurableApprovalAttachmentStatus] = Field(default_factory=list)
    safe_refs_only: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_bucket(self) -> Any:
        validate_execution_ref(self.run_ref, "run_ref")
        for ref in [*self.pending_approval_refs, *self.approval_history_refs]:
            validate_execution_ref(ref, "approval_ref")
        for status in self.durable_attachment_statuses:
            validate_safe_execution_text(status, "durable_attachment_status")
        if not self.safe_refs_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_BUCKET_SAFE_REFS_REQUIRED")
        return self


class RunAttachedApprovalQueueSummaryReadModel(BaseModel):
    schema_version: str = RUN_ATTACHED_APPROVAL_QUEUE_SUMMARY_SCHEMA_VERSION
    queue_ref: str = Field(..., min_length=1)
    queue_item_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    pending_count: int = Field(..., ge=0)
    requested_count: int = Field(..., ge=0)
    approved_count: int = Field(..., ge=0)
    denied_count: int = Field(..., ge=0)
    expired_count: int = Field(..., ge=0)
    revoked_count: int = Field(..., ge=0)
    scope_mismatch_blocked_count: int = Field(..., ge=0)
    blocked_count: int = Field(..., ge=0)
    durable_attachment_missing_count: int = Field(..., ge=0)
    approval_grants_created: bool = False
    arbitrary_approval_ref_authority: bool = False
    safe_summary: str = Field(..., min_length=1)
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_refs_are_identifiers_only: bool = True
    execution_authority_enabled: bool = False
    ui_mutation_controls_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_summary(self) -> Any:
        validate_execution_ref(self.queue_ref, "queue_ref")
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.arbitrary_approval_ref_authority:
            raise ValueError("RUN_ATTACHED_APPROVAL_ARBITRARY_REF_AUTHORITY_DENIED")
        if not self.safe_refs_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_SUMMARY_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("RUN_ATTACHED_APPROVAL_SUMMARY_RAW_PAYLOADS_DENIED")
        if not self.approval_refs_are_identifiers_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_SUMMARY_IDENTIFIER_ONLY_REFS_REQUIRED")
        if self.execution_authority_enabled or self.ui_mutation_controls_enabled:
            raise ValueError("RUN_ATTACHED_APPROVAL_SUMMARY_AUTHORITY_DENIED")
        return self


class UnifiedApprovalReviewItemReadModel(BaseModel):
    schema_version: str = UNIFIED_APPROVAL_REVIEW_ITEM_SCHEMA_VERSION
    item_ref: str = Field(..., min_length=1)
    source_type: UnifiedApprovalReviewSource
    title: str = Field(..., min_length=1)
    approval_state: RunAttachedApprovalState
    run_ref: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    approval_ref: str | None = None
    approval_request_ref: str | None = None
    approval_decision_ref: str | None = None
    approval_receipt_ref: str | None = None
    requested_scope_ref: str | None = None
    expiry_ref: str | None = None
    revocation_ref: str | None = None
    provider_tool_contract_refs: list[str] = Field(default_factory=list)
    connector_delivery_refs: list[str] = Field(default_factory=list)
    coworker_handoff_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    next_safe_action: str = "inspect_only_no_ui_mutation"
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_refs_are_identifiers_only: bool = True
    approval_ref_grants_authority: bool = False
    local_approval_authority_scope_validated: bool = False
    ui_mutation_controls_enabled: bool = False
    execution_authority_enabled: bool = False
    provider_model_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_review_item(self) -> Any:
        for value, field_name in [
            (self.item_ref, "item_ref"),
            (self.run_ref, "run_ref"),
            (self.source_ref, "source_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.approval_request_ref, "approval_request_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.approval_receipt_ref, "approval_receipt_ref"),
            (self.requested_scope_ref, "requested_scope_ref"),
            (self.expiry_ref, "expiry_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            if value:
                validate_execution_ref(value, field_name)
        for ref in [
            *self.provider_tool_contract_refs,
            *self.connector_delivery_refs,
            *self.coworker_handoff_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.receipt_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "unified_approval_review_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source_type, "source_type"),
            (self.title, "title"),
            (self.approval_state, "approval_state"),
            (self.safe_summary, "safe_summary"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            validate_safe_execution_text(text, field_name)
        for route_ref in self.route_refs:
            validate_safe_execution_text(route_ref, "route_ref")
        if self.approval_state in {"scope_mismatch_blocked", "blocked"} and not self.blocked_authority_refs:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_BLOCKED_REFS_REQUIRED")
        if self.approval_state == "expired" and not self.expiry_ref:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_EXPIRY_REF_REQUIRED")
        if self.approval_state == "revoked" and not self.revocation_ref:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_REVOCATION_REF_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_RAW_PAYLOADS_DENIED")
        if not self.approval_refs_are_identifiers_only or self.approval_ref_grants_authority:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_IDENTIFIER_ONLY_REFS_REQUIRED")
        if any(
            [
                self.local_approval_authority_scope_validated,
                self.ui_mutation_controls_enabled,
                self.execution_authority_enabled,
                self.provider_model_calls_enabled,
                self.tool_execution_enabled,
                self.connector_writes_enabled,
                self.connector_sends_enabled,
                self.background_worker_enabled,
                self.scheduler_enabled,
            ]
        ):
            raise ValueError("UNIFIED_APPROVAL_REVIEW_AUTHORITY_DENIED")
        return self


class UnifiedApprovalReviewReadModel(BaseModel):
    schema_version: str = UNIFIED_APPROVAL_REVIEW_SCHEMA_VERSION
    source: str = "python_core_unified_approval_review_read_model"
    backend_owned: bool = True
    review_ref: str = Field(..., min_length=1)
    route_ref: str = "/control-center/approvals/queue"
    route_refs: list[str] = Field(
        default_factory=lambda: ["GET /control-center/approvals/queue"]
    )
    cli_ref: str = "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-approval-review"
    review_items: list[UnifiedApprovalReviewItemReadModel] = Field(default_factory=list)
    pending_approval_refs: list[str] = Field(default_factory=list)
    approval_history_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    provider_tool_contract_refs: list[str] = Field(default_factory=list)
    connector_delivery_refs: list[str] = Field(default_factory=list)
    coworker_handoff_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    pending_count: int = Field(..., ge=0)
    history_count: int = Field(..., ge=0)
    blocked_count: int = Field(..., ge=0)
    expired_count: int = Field(..., ge=0)
    revoked_count: int = Field(..., ge=0)
    scope_mismatch_blocked_count: int = Field(..., ge=0)
    safe_summary: str = Field(..., min_length=1)
    next_safe_action: str = "inspect_only_no_ui_mutation"
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_refs_are_identifiers_only: bool = True
    approval_ref_grants_authority: bool = False
    ui_mutation_controls_enabled: bool = False
    execution_authority_enabled: bool = False
    provider_model_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_review(self) -> Any:
        validate_execution_ref(self.review_ref, "review_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            validate_safe_execution_text(text, field_name)
        for route_ref in self.route_refs:
            validate_safe_execution_text(route_ref, "route_ref")
        for ref in [
            *self.pending_approval_refs,
            *self.approval_history_refs,
            *self.run_refs,
            *self.provider_tool_contract_refs,
            *self.connector_delivery_refs,
            *self.coworker_handoff_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.receipt_refs,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "unified_approval_review_ref")
        if not self.backend_owned:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_BACKEND_OWNED_REQUIRED")
        if self.history_count != len(self.review_items):
            raise ValueError("UNIFIED_APPROVAL_REVIEW_HISTORY_COUNT_MISMATCH")
        if self.pending_count != len(self.pending_approval_refs):
            raise ValueError("UNIFIED_APPROVAL_REVIEW_PENDING_COUNT_MISMATCH")
        if not self.safe_refs_only:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_RAW_PAYLOADS_DENIED")
        if not self.approval_refs_are_identifiers_only or self.approval_ref_grants_authority:
            raise ValueError("UNIFIED_APPROVAL_REVIEW_IDENTIFIER_ONLY_REFS_REQUIRED")
        if any(
            [
                self.ui_mutation_controls_enabled,
                self.execution_authority_enabled,
                self.provider_model_calls_enabled,
                self.tool_execution_enabled,
                self.connector_writes_enabled,
                self.connector_sends_enabled,
                self.background_worker_enabled,
                self.scheduler_enabled,
            ]
        ):
            raise ValueError("UNIFIED_APPROVAL_REVIEW_AUTHORITY_DENIED")
        return self


class RunAttachedApprovalQueueReadModel(BaseModel):
    schema_version: str = RUN_ATTACHED_APPROVAL_QUEUE_SCHEMA_VERSION
    source: str = "python_core_run_attached_approval_queue_read_model"
    backend_owned: bool = True
    queue_ref: str = Field(..., min_length=1)
    route_ref: str = "/control-center/approvals/queue"
    route_refs: list[str] = Field(
        default_factory=lambda: ["GET /control-center/approvals/queue"]
    )
    cli_ref: str = "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-approvals"
    supported_approval_states: list[RunAttachedApprovalState] = Field(
        default_factory=lambda: list(RUN_ATTACHED_APPROVAL_STATES)
    )
    supported_approval_event_types: list[RunAttachedApprovalEventType] = Field(
        default_factory=lambda: list(RUN_ATTACHED_APPROVAL_EVENT_TYPES)
    )
    queue_items: list[RunAttachedApprovalQueueItemReadModel] = Field(default_factory=list)
    pending_approvals_by_run: list[RunAttachedApprovalRunBucketReadModel] = Field(default_factory=list)
    approval_history_by_run: list[RunAttachedApprovalRunBucketReadModel] = Field(default_factory=list)
    summary: RunAttachedApprovalQueueSummaryReadModel
    unified_review: UnifiedApprovalReviewReadModel
    connector_delivery_review_queue: ConnectorDeliveryReviewQueueReadModel
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_refs_are_identifiers_only: bool = True
    approval_authority_enabled: bool = False
    execution_authority_enabled: bool = False
    ui_mutation_controls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    model_call_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        validate_execution_ref(self.queue_ref, "queue_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
        ]:
            validate_safe_execution_text(text, field_name)
        for ref in self.route_refs:
            validate_safe_execution_text(ref, "route_ref")
        if not self.backend_owned:
            raise ValueError("RUN_ATTACHED_APPROVAL_QUEUE_BACKEND_OWNED_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_QUEUE_SAFE_REFS_REQUIRED")
        if self.raw_payloads_persisted:
            raise ValueError("RUN_ATTACHED_APPROVAL_QUEUE_RAW_PAYLOADS_DENIED")
        if not self.approval_refs_are_identifiers_only:
            raise ValueError("RUN_ATTACHED_APPROVAL_QUEUE_IDENTIFIER_ONLY_REFS_REQUIRED")
        if any(
            [
                self.approval_authority_enabled,
                self.execution_authority_enabled,
                self.ui_mutation_controls_enabled,
                self.tool_execution_enabled,
                self.connector_writes_enabled,
                self.model_call_enabled,
            ]
        ):
            raise ValueError("RUN_ATTACHED_APPROVAL_QUEUE_AUTHORITY_DENIED")
        return self


def run_attached_approval_item_from_request(
    request: ApprovalRequest,
    *,
    durable_attachment_status: DurableApprovalAttachmentStatus = "durable_attachment_missing",
) -> RunAttachedApprovalQueueItemReadModel:
    run_ref = _safe_external_ref("run", request.run_id)
    approval_request_ref = _hashed_external_ref("approval-request", request.approval_request_id)
    step_ref = _hashed_external_ref("step", request.subject_id)
    requested_scope_ref = _stable_ref(
        "approval-scope",
        request.run_id,
        request.requested_action,
        *request.resource_refs,
    )
    evidence_refs = _sorted_unique([request.event_ref])
    return RunAttachedApprovalQueueItemReadModel(
        item_ref=_stable_ref("run-approval-queue-item", approval_request_ref, "requested"),
        approval_request_ref=approval_request_ref,
        run_ref=run_ref,
        step_ref=step_ref,
        requested_scope_ref=requested_scope_ref,
        approval_state="requested",
        approval_event_type="approval_required",
        evidence_refs=evidence_refs,
        durable_attachment_status=durable_attachment_status,
        safe_summary="Approval request is visible as an identifier-only durable run ref.",
    )


def run_attached_approval_item_from_grant(
    grant: ApprovalGrant,
    *,
    durable_attachment_status: DurableApprovalAttachmentStatus = "durable_attachment_missing",
    now: datetime | None = None,
) -> RunAttachedApprovalQueueItemReadModel:
    run_ref = _safe_external_ref("run", grant.run_id)
    approval_request_ref = _hashed_external_ref("approval-request", grant.approval_request_id)
    approval_ref = _hashed_external_ref("approval", grant.approval_ref)
    state = _state_for_grant(grant, now=now)
    evidence_refs = _sorted_unique([grant.event_ref])
    expiry_ref = (
        _stable_ref("approval-expiry", grant.approval_ref, grant.expires_at.isoformat())
        if grant.expires_at
        else None
    )
    revocation_ref = (
        _stable_ref("approval-revocation", grant.approval_ref, grant.revoked_at.isoformat())
        if grant.revoked_at
        else None
    )
    return RunAttachedApprovalQueueItemReadModel(
        item_ref=_stable_ref("run-approval-queue-item", approval_ref, state),
        approval_request_ref=approval_request_ref,
        approval_grant_ref=approval_ref,
        run_ref=run_ref,
        step_ref=_hashed_external_ref("step", grant.subject_id),
        requested_scope_ref=_stable_ref(
            "approval-scope",
            grant.run_id,
            *grant.approved_actions,
            *grant.approved_resource_refs,
        ),
        approval_state=state,
        approval_event_type=run_attached_approval_event_type(state),
        approval_decision_ref=_stable_ref("approval-decision", grant.approval_ref, state),
        approval_receipt_ref=_stable_ref("approval-receipt", grant.approval_ref),
        expiry_ref=expiry_ref,
        revocation_ref=revocation_ref,
        evidence_refs=evidence_refs,
        receipt_refs=[_stable_ref("receipt", grant.approval_ref, state)],
        durable_attachment_status=durable_attachment_status,
        safe_summary="Approval grant state is visible as an identifier-only durable run ref; execution remains blocked here.",
    )


def run_attached_approval_item_from_receipt_summary(
    receipt_summary: dict[str, Any],
) -> RunAttachedApprovalQueueItemReadModel | None:
    if receipt_summary.get("schema_version") != RUN_ATTACHED_APPROVAL_EVENT_RECEIPT_SCHEMA_VERSION:
        return None
    state = receipt_summary.get("approval_state")
    if state not in RUN_ATTACHED_APPROVAL_STATES:
        return None
    item_ref_seed = receipt_summary.get("approval_grant_ref") or receipt_summary.get("approval_request_ref")
    return RunAttachedApprovalQueueItemReadModel(
        item_ref=_stable_ref(
            "run-approval-queue-item",
            str(item_ref_seed),
            str(state),
        ),
        approval_request_ref=str(receipt_summary["approval_request_ref"]),
        approval_grant_ref=receipt_summary.get("approval_grant_ref"),
        run_ref=str(receipt_summary["run_ref"]),
        step_ref=str(receipt_summary["step_ref"]),
        requested_scope_ref=str(receipt_summary["requested_scope_ref"]),
        approval_state=state,
        approval_event_type=run_attached_approval_event_type(state),
        approval_decision_ref=receipt_summary.get("approval_decision_ref"),
        approval_receipt_ref=receipt_summary.get("approval_receipt_ref"),
        approval_scope_validation_ref=receipt_summary.get("approval_scope_validation_ref"),
        expiry_ref=receipt_summary.get("expiry_ref"),
        revocation_ref=receipt_summary.get("revocation_ref"),
        evidence_refs=_sorted_unique(receipt_summary.get("evidence_refs", [])),
        blocked_authority_refs=_sorted_unique(receipt_summary.get("blocked_authority_refs", [])),
        durable_attachment_status="attached",
        safe_summary="Run-attached approval queue event was restored from a safe receipt summary.",
    )


def record_run_attached_approval_event(
    storage: AppendFirstRunStorage,
    item: RunAttachedApprovalQueueItemReadModel,
    *,
    idempotency_key_ref: str,
    audit_ref: str,
    receipt_ref: str,
    rollback_ref: str,
) -> None:
    storage.append_receipt_summary(
        run_id=item.run_ref,
        receipt_ref=receipt_ref,
        idempotency_key=idempotency_key_ref,
        audit_ref=audit_ref,
        rollback_ref=rollback_ref,
        safe_summary="Run-attached approval queue event was recorded as safe refs only.",
        receipt_summary=item.to_receipt_summary(),
        evidence_refs=item.evidence_refs,
    )


def run_attached_approval_items_from_storage(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
) -> list[RunAttachedApprovalQueueItemReadModel]:
    items: list[RunAttachedApprovalQueueItemReadModel] = []
    for entry in storage.list_entries(run_ref):
        if entry.kind != DurableRunStorageEntryKind.receipt or not entry.receipt_summary:
            continue
        item = run_attached_approval_item_from_receipt_summary(entry.receipt_summary)
        if item is not None:
            items.append(
                item.model_copy(
                    update={
                        "receipt_refs": _sorted_unique([entry.receipt_ref, *item.receipt_refs]),
                        "audit_refs": _sorted_unique([entry.audit_ref, *item.audit_refs]),
                        "replay_refs": _sorted_unique(
                            [entry.replay_validation_ref, *item.replay_refs]
                        ),
                        "rollback_refs": _sorted_unique([entry.rollback_ref, *item.rollback_refs]),
                        "idempotency_key_refs": _sorted_unique(
                            [entry.idempotency_key, *item.idempotency_key_refs]
                        ),
                    }
                )
            )
    return items


def _proof_ref(*parts: str) -> str:
    return _stable_ref("proof-ref", *parts)


def _default_unified_blocked_authority_refs() -> list[str]:
    return [
        "blocked-state:no-ui-approval-authority",
        "blocked-state:no-broad-approve-all",
        "blocked-state:no-provider-model-call",
        "blocked-state:no-tool-execution",
        "blocked-state:no-connector-write",
        "blocked-state:no-background-worker",
        "blocked-state:no-scheduler",
    ]


def _unified_review_item_from_queue_item(
    item: RunAttachedApprovalQueueItemReadModel,
) -> UnifiedApprovalReviewItemReadModel:
    blocked_refs = _sorted_unique(
        [
            *item.blocked_authority_refs,
            *_default_unified_blocked_authority_refs(),
        ]
    )
    return UnifiedApprovalReviewItemReadModel(
        item_ref=_stable_ref("unified-approval-review-item", item.item_ref),
        source_type="durable_run",
        title="Durable run approval",
        approval_state=item.approval_state,
        run_ref=item.run_ref,
        source_ref=item.item_ref,
        approval_ref=item.approval_grant_ref,
        approval_request_ref=item.approval_request_ref,
        approval_decision_ref=item.approval_decision_ref,
        approval_receipt_ref=item.approval_receipt_ref,
        requested_scope_ref=item.requested_scope_ref,
        expiry_ref=item.expiry_ref,
        revocation_ref=item.revocation_ref,
        proof_refs=[_proof_ref(item.item_ref)],
        evidence_refs=item.evidence_refs,
        receipt_refs=item.receipt_refs,
        audit_refs=item.audit_refs,
        replay_refs=item.replay_refs,
        rollback_refs=item.rollback_refs,
        blocked_authority_refs=blocked_refs,
        route_refs=[
            "GET /control-center/approvals/queue",
            "GET /task-decomposition/runs/{run_id}/approvals",
        ],
        safe_summary=item.safe_summary,
        next_safe_action=item.required_next_action,
    )


def _provider_tool_contract_review_item() -> UnifiedApprovalReviewItemReadModel:
    return UnifiedApprovalReviewItemReadModel(
        item_ref="unified-approval-review-item:provider-tool-contract",
        source_type="provider_tool_contract",
        title="Provider/tool exact approval contract",
        approval_state="blocked",
        run_ref="task-decomposition-run:provider-tool-contract-review",
        source_ref="contract-ref:provider-tool-runtime-safety",
        requested_scope_ref="approval-scope-ref:provider-tool-runtime:exact-required",
        provider_tool_contract_refs=[
            "contract-ref:provider-tool-runtime-safety",
            "contract-ref:provider-tool-runtime-exact-approval",
        ],
        proof_refs=["proof-ref:provider-tool-runtime-safety-contract"],
        blocked_authority_refs=[
            "blocked-state:no-provider-model-call",
            "blocked-state:no-tool-execution",
            "blocked-state:approval-ref-alone-no-authority",
        ],
        route_refs=["POST /model-runtime/local/execution/validate"],
        safe_summary=(
            "Provider/tool approval posture is contract-only here; exact "
            "LocalApprovalAuthority validation is required before any separate "
            "runtime lane could act."
        ),
        next_safe_action="inspect_provider_tool_contract_only",
    )


def _connector_review_items(
    durable_run_storage: AppendFirstRunStorage | None,
    *,
    run_ref: str | None,
    limit: int,
) -> list[UnifiedApprovalReviewItemReadModel]:
    if durable_run_storage is None:
        return []
    from ultimate_ai_agent.core.execution.connector_delivery import (
        build_connector_delivery_read_model,
    )

    model = build_connector_delivery_read_model(
        durable_run_storage,
        run_ref=run_ref,
        limit=limit,
    )
    items: list[UnifiedApprovalReviewItemReadModel] = []
    for status in model.delivery_statuses:
        state: RunAttachedApprovalState
        if status.pending_approval_visible:
            state = "requested"
        elif status.delivery_blocked_visible or status.sent_not_supported_visible:
            state = "blocked"
        else:
            state = "requested"
        approval_ref = status.outbound_approval_refs[0] if status.outbound_approval_refs else None
        blocked_refs = _sorted_unique(
            [
                *status.blocked_reason_refs,
                "blocked-state:no-connector-write",
                "blocked-state:no-connector-send",
                "blocked-state:approval-ref-alone-no-authority",
            ]
        )
        items.append(
            UnifiedApprovalReviewItemReadModel(
                item_ref=_stable_ref("unified-approval-review-item", status.delivery_ref),
                source_type="connector_delivery",
                title="Connector delivery review",
                approval_state=state,
                run_ref=status.run_ref,
                source_ref=status.delivery_ref,
                approval_ref=approval_ref,
                requested_scope_ref=_stable_ref(
                    "approval-scope",
                    status.delivery_ref,
                    status.connector_ref,
                    status.channel_ref,
                ),
                connector_delivery_refs=[
                    status.delivery_ref,
                    status.connector_ref,
                    status.channel_ref,
                    status.target_session_ref,
                ],
                proof_refs=[_proof_ref(status.delivery_ref)],
                evidence_refs=status.event_refs,
                receipt_refs=[*status.expected_receipt_refs, *status.failure_receipt_refs],
                blocked_authority_refs=blocked_refs,
                route_refs=[
                    "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-connector-deliveries"
                ],
                safe_summary=(
                    "Connector delivery approval posture is review-only; no "
                    "send, write, account sync, retry worker, or scheduler is enabled."
                ),
                next_safe_action="inspect_connector_delivery_refs_only",
            )
        )
    return items


def _coworker_review_items(
    durable_run_storage: AppendFirstRunStorage | None,
    *,
    run_ref: str | None,
    limit: int,
) -> list[UnifiedApprovalReviewItemReadModel]:
    if durable_run_storage is None:
        return []
    from ultimate_ai_agent.core.execution.background_coworker import (
        build_background_coworker_read_model,
    )

    model = build_background_coworker_read_model(
        durable_run_storage,
        run_ref=run_ref,
        limit=limit,
    )
    items: list[UnifiedApprovalReviewItemReadModel] = []
    for event in model.events:
        if event.handoff_ref:
            source_ref = event.handoff_ref
            title = "Coworker handoff review"
        else:
            source_ref = event.event_ref
            title = "Coworker worker review"
        state: RunAttachedApprovalState = (
            "blocked" if event.event_type == "worker_blocked" else "requested"
        )
        blocked_refs = _sorted_unique(
            [
                *event.blocked_authority_refs,
                "blocked-state:no-background-worker",
                "blocked-state:no-scheduler",
                "blocked-state:approval-ref-alone-no-authority",
            ]
        )
        items.append(
            UnifiedApprovalReviewItemReadModel(
                item_ref=_stable_ref("unified-approval-review-item", source_ref),
                source_type="coworker_handoff",
                title=title,
                approval_state=state,
                run_ref=event.run_ref,
                source_ref=source_ref,
                requested_scope_ref=_stable_ref(
                    "approval-scope",
                    event.worker_ref,
                    source_ref,
                ),
                coworker_handoff_refs=_sorted_unique(
                    [event.worker_ref, event.handoff_ref, event.parent_run_ref, event.child_run_ref]
                ),
                proof_refs=[_proof_ref(source_ref)],
                evidence_refs=event.evidence_refs,
                receipt_refs=event.receipt_refs,
                audit_refs=event.audit_refs,
                replay_refs=event.replay_refs,
                rollback_refs=event.rollback_refs,
                blocked_authority_refs=blocked_refs,
                route_refs=[
                    "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-coworker-workers"
                ],
                safe_summary=(
                    "Coworker approval posture is metadata-only; no worker, "
                    "queue consumer, process, scheduler, provider call, or tool execution is enabled."
                ),
                next_safe_action="inspect_coworker_handoff_refs_only",
            )
        )
    return items


def _build_unified_approval_review(
    queue_items: list[RunAttachedApprovalQueueItemReadModel],
    *,
    durable_run_storage: AppendFirstRunStorage | None,
    run_ref: str | None,
    limit: int,
) -> UnifiedApprovalReviewReadModel:
    review_items = [
        _unified_review_item_from_queue_item(item)
        for item in queue_items
    ]
    review_items.append(_provider_tool_contract_review_item())
    review_items.extend(
        _connector_review_items(durable_run_storage, run_ref=run_ref, limit=limit)
    )
    review_items.extend(
        _coworker_review_items(durable_run_storage, run_ref=run_ref, limit=limit)
    )
    review_items = sorted(
        review_items,
        key=lambda item: (item.source_type, item.run_ref, item.item_ref),
    )[:limit]
    pending_refs = [
        item.item_ref
        for item in review_items
        if item.approval_state in PENDING_RUN_ATTACHED_APPROVAL_STATES
    ]
    counts = Counter(item.approval_state for item in review_items)
    review_ref = _stable_ref(
        "unified-approval-review",
        run_ref or "all-runs",
        str(len(review_items)),
    )
    return UnifiedApprovalReviewReadModel(
        review_ref=review_ref,
        review_items=review_items,
        pending_approval_refs=pending_refs,
        approval_history_refs=[item.item_ref for item in review_items],
        run_refs=_sorted_unique(item.run_ref for item in review_items),
        provider_tool_contract_refs=_sorted_unique(
            ref for item in review_items for ref in item.provider_tool_contract_refs
        ),
        connector_delivery_refs=_sorted_unique(
            ref for item in review_items for ref in item.connector_delivery_refs
        ),
        coworker_handoff_refs=_sorted_unique(
            ref for item in review_items for ref in item.coworker_handoff_refs
        ),
        proof_refs=_sorted_unique(ref for item in review_items for ref in item.proof_refs),
        evidence_refs=_sorted_unique(ref for item in review_items for ref in item.evidence_refs),
        receipt_refs=_sorted_unique(ref for item in review_items for ref in item.receipt_refs),
        blocked_authority_refs=_sorted_unique(
            ref for item in review_items for ref in item.blocked_authority_refs
        ),
        pending_count=len(pending_refs),
        history_count=len(review_items),
        blocked_count=counts["blocked"],
        expired_count=counts["expired"],
        revoked_count=counts["revoked"],
        scope_mismatch_blocked_count=counts["scope_mismatch_blocked"],
        safe_summary=(
            "Unified approval review is backend-owned and read-only. It joins "
            "durable run approvals, provider/tool contract posture, connector "
            "delivery refs, and coworker handoff refs without granting authority."
        ),
    )


def _durable_approval_refs(storage: AppendFirstRunStorage) -> set[str]:
    refs: set[str] = set()
    for entry in storage.list_entries():
        if entry.kind == DurableRunStorageEntryKind.run_record and entry.record_snapshot:
            metadata = entry.record_snapshot.record.metadata
            values = metadata.get("approval_refs", []) if isinstance(metadata, dict) else []
            if isinstance(values, list):
                refs.update(str(value) for value in values if isinstance(value, str))
        if entry.kind == DurableRunStorageEntryKind.receipt and entry.receipt_summary:
            for key in ("approval_request_ref", "approval_receipt_ref"):
                value = entry.receipt_summary.get(key)
                if isinstance(value, str):
                    refs.add(value)
    return refs


def build_run_attached_approval_queue_read_model(
    *,
    approval_requests: Iterable[ApprovalRequest] = (),
    approval_grants: Iterable[ApprovalGrant] = (),
    durable_run_storage: AppendFirstRunStorage | None = None,
    run_ref: str | None = None,
    limit: int = 50,
) -> RunAttachedApprovalQueueReadModel:
    storage_refs = _durable_approval_refs(durable_run_storage) if durable_run_storage else set()
    queue_items: list[RunAttachedApprovalQueueItemReadModel] = []
    for request in approval_requests:
        item = run_attached_approval_item_from_request(request)
        status: DurableApprovalAttachmentStatus = (
            "attached" if item.approval_request_ref in storage_refs else "durable_attachment_missing"
        )
        queue_items.append(item.model_copy(update={"durable_attachment_status": status}))
    for grant in approval_grants:
        item = run_attached_approval_item_from_grant(grant)
        status = (
            "attached"
            if item.approval_grant_ref in storage_refs or item.approval_receipt_ref in storage_refs
            else "durable_attachment_missing"
        )
        queue_items.append(item.model_copy(update={"durable_attachment_status": status}))
    if durable_run_storage is not None:
        queue_items.extend(run_attached_approval_items_from_storage(durable_run_storage, run_ref=run_ref))

    if run_ref:
        safe_run_ref = _safe_external_ref("run", run_ref)
        queue_items = [item for item in queue_items if item.run_ref == safe_run_ref]

    deduped: dict[str, RunAttachedApprovalQueueItemReadModel] = {}
    for item in queue_items:
        deduped[item.item_ref] = item
    ordered_items = sorted(
        deduped.values(),
        key=lambda item: (
            item.run_ref,
            item.approval_request_ref,
            RUN_ATTACHED_APPROVAL_STATE_ORDER[item.approval_state],
            item.item_ref,
        ),
    )[:limit]

    counts = Counter(item.approval_state for item in ordered_items)
    resolved_request_refs = {
        item.approval_request_ref
        for item in ordered_items
        if item.approval_state in RESOLVED_RUN_ATTACHED_APPROVAL_STATES
    }
    missing_count = sum(
        1 for item in ordered_items if item.durable_attachment_status == "durable_attachment_missing"
    )
    pending_items: list[RunAttachedApprovalQueueItemReadModel] = []
    pending_by_run: dict[str, list[RunAttachedApprovalQueueItemReadModel]] = defaultdict(list)
    history_by_run: dict[str, list[RunAttachedApprovalQueueItemReadModel]] = defaultdict(list)
    for item in ordered_items:
        history_by_run[item.run_ref].append(item)
        if (
            item.approval_state in PENDING_RUN_ATTACHED_APPROVAL_STATES
            and item.approval_request_ref not in resolved_request_refs
        ):
            pending_items.append(item)
            pending_by_run[item.run_ref].append(item)

    history_buckets = [
        RunAttachedApprovalRunBucketReadModel(
            run_ref=run,
            pending_approval_refs=[item.item_ref for item in pending_by_run.get(run, [])],
            approval_history_refs=[item.item_ref for item in items],
            latest_approval_state=items[-1].approval_state if items else None,
            durable_attachment_statuses=dedupe_reasons(
                [item.durable_attachment_status for item in items]
            ),
        )
        for run, items in sorted(history_by_run.items())
    ]
    pending_buckets = [
        bucket
        for bucket in history_buckets
        if bucket.pending_approval_refs
    ]
    queue_ref = _stable_ref(
        "run-attached-approval-queue",
        run_ref or "all-runs",
        str(len(ordered_items)),
    )
    summary = RunAttachedApprovalQueueSummaryReadModel(
        queue_ref=queue_ref,
        queue_item_count=len(ordered_items),
        run_count=len(history_by_run),
        pending_count=len(pending_items),
        requested_count=counts["requested"],
        approved_count=counts["approved"],
        denied_count=counts["denied"],
        expired_count=counts["expired"],
        revoked_count=counts["revoked"],
        scope_mismatch_blocked_count=counts["scope_mismatch_blocked"],
        blocked_count=counts["blocked"],
        durable_attachment_missing_count=missing_count,
        approval_grants_created=any(
            counts[state] > 0 for state in ("approved", "expired", "revoked")
        ),
        safe_summary=(
            "Run-attached approval queue is read-only and safe-ref-only; "
            "approval refs are identifiers and do not grant execution authority."
        ),
    )
    unified_review = _build_unified_approval_review(
        ordered_items,
        durable_run_storage=durable_run_storage,
        run_ref=run_ref,
        limit=limit,
    )
    connector_delivery_review_queue = (
        build_connector_delivery_review_queue(
            durable_run_storage,
            run_ref=run_ref,
            limit=limit,
        )
        if durable_run_storage is not None
        else ConnectorDeliveryReviewQueueReadModel(
            review_ref=_stable_ref(
                "connector-delivery-review-queue",
                run_ref or "all-runs",
                "0",
            ),
            delivery_count=0,
        )
    )
    return RunAttachedApprovalQueueReadModel(
        queue_ref=queue_ref,
        queue_items=ordered_items,
        pending_approvals_by_run=pending_buckets,
        approval_history_by_run=history_buckets,
        summary=summary,
        unified_review=unified_review,
        connector_delivery_review_queue=connector_delivery_review_queue,
    )
