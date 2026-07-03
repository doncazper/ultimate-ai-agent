from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.source_provenance import (
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS,
    MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
)
from ultimate_ai_agent.core.time import utc_now


MEMORY_REVIEW_DECISION_CONTRACT_REF = "contract-ref:memory-review-decision:v1"
FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF = "contract-ref:fcc-v1-005-memory-review-decisions:v1"
MEMORY_REVIEW_DECISION_ROUTE_REFS = (
    "GET /control-center/memory/review",
    "GET /control-center/memory/review/{candidate_ref}/receipt",
    "POST /control-center/memory/review/{candidate_ref}/accept",
    "POST /control-center/memory/review/{candidate_ref}/correct",
    "POST /control-center/memory/review/{candidate_ref}/reject",
    "POST /control-center/memory/review/{candidate_ref}/defer",
    "POST /control-center/memory/review/{candidate_ref}/merge",
    "POST /control-center/memory/review/{candidate_ref}/supersede",
    "POST /control-center/memory/review/{candidate_ref}/forget-request",
)

MemoryReviewDecisionKind = Literal[
    "accept",
    "correct",
    "reject",
    "defer",
    "merge",
    "supersede",
    "forget_request",
]
MEMORY_REVIEW_DECISION_KINDS: list[MemoryReviewDecisionKind] = [
    "accept",
    "correct",
    "reject",
    "defer",
    "merge",
    "supersede",
    "forget_request",
]

MemoryReviewDecisionState = Literal[
    "accept",
    "correct",
    "reject",
    "defer",
    "merge",
    "supersede",
    "forget_request",
]

MEMORY_REVIEW_DECISION_STATES: list[MemoryReviewDecisionState] = [
    "accept",
    "correct",
    "reject",
    "defer",
    "merge",
    "supersede",
    "forget_request",
]

MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS = [
    "actor_ref",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "stale_state",
    "retention_posture",
    "audit_refs",
    "receipt_refs",
    "blocked_state_refs",
]

MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-memory-delete",
    "blocked-state:no-memory-export",
    "blocked-state:no-context-injection",
]
FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS = [
    *MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS,
    "blocked-state:no-connector-write",
    "blocked-state:no-external-crm-sync",
    "blocked-state:no-automatic-action-execution",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-public-beta-or-production-authority",
]
MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF = (
    "exact-scope-ref:memory-review:accept-correct-reviewed-recall-write"
)
MEMORY_REVIEW_RECEIPT_SCOPE_REF = (
    "exact-scope-ref:memory-review:receipt-state-no-recall-write"
)
MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF = (
    "safe-disable-ref:memory-review:accept-correct-reviewed-recall-write"
)
MEMORY_REVIEW_WRITE_ROLLBACK_REF = (
    "rollback-ref:memory-review:suppress-reviewed-recall-record"
)
MEMORY_REVIEW_WRITE_SAFE_DISABLE_POSTURE_REF = (
    "safe-disable-posture-ref:memory-review:accept-correct-write-enabled"
)
MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF = (
    "blocked-state:memory-review-rollback-execution-blocked"
)

_DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
    "retention_execution_authorized",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw-prompt",
    "raw response",
    "raw_response",
    "raw-response",
    "provider payload",
    "provider_payload",
    "provider-payload",
    "raw provider",
    "raw_provider",
    "raw-provider",
    "raw path",
    "raw_path",
    "raw-path",
    "raw log",
    "raw_log",
    "raw-log",
    "account identifier",
    "account_identifier",
    "account-identifier",
    "account id",
    "account_id",
    "account-id",
    "username",
    "username:",
    "hostname",
    "hostname:",
    "credential",
    "credential material",
    "credential_material",
    "credential-material",
    "raw private content",
    "raw_private_content",
    "raw-private-content",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory review ref")


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory review text")


def _safe_optional_text(value: str | None, field_name: str) -> None:
    if value is not None:
        _safe_text(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} is required")
    for value in values:
        _safe_ref(value, field_name)


def _safe_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        _safe_ref(value, field_name)


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _provenance_prefix(source_kind: str) -> str:
    return f"provenance-ref:{source_kind.replace('_', '-')}"


def _matches_prefix(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(f"{prefix}:")


def _safe_suffix(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in "._-" else "-"
        for character in value.lower()
    ).strip("-") or "missing"


def _short_ref_suffix(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{_safe_suffix(value)[:48].strip('-') or 'ref'}-{digest}"


def _validate_kind_refs(values: list[str], field_name: str, prefix: str) -> None:
    for value in values:
        if not _matches_prefix(value, prefix):
            raise ValueError(f"{field_name} must match source kind prefix")


class MemoryReviewDecisionEnvelope(BaseModel):
    contract_ref: str = Field(default=MEMORY_REVIEW_DECISION_CONTRACT_REF)
    decision_ref: str = Field(..., min_length=1)
    review_ref: str = Field(..., min_length=1)
    decision_state: MemoryReviewDecisionState
    actor_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    source_refs: list[str] = Field(default_factory=list)
    source_provenance_contract_ref: str = Field(
        default=MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    source_kind: str = Field(default="manual_note")
    source_trust_posture: str = Field(
        default=MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE
    )
    redaction_status: str = Field(default="redacted_summary_only")
    evidence_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: [
            *MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS,
            "blocked-state:no-connector-runtime",
            "blocked-state:no-account-auth",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-public-beta-or-production-authority",
        ]
    )
    merge_refs: list[str] = Field(default_factory=list)
    supersedes_refs: list[str] = Field(default_factory=list)
    stale_state: str = Field(default="recheck_source_refs_before_memory_use")
    retention_posture: str = Field(default="retention_policy_not_bound")
    correction_posture: str = Field(
        default="correction_requires_scoped_memory_write_contract"
    )
    authority_boundary: str = Field(
        default=(
            "Memory review decisions are review metadata only; writes, deletes, "
            "exports, context injection, connector runtime, account auth, and "
            "production authority remain unscoped."
        ),
        min_length=1,
        max_length=240,
    )
    review_only: bool = True
    memory_write_authorized: bool = False
    memory_delete_authorized: bool = False
    memory_export_authorized: bool = False
    context_injection_authorized: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    provider_or_model_authority_allowed: bool = False
    source_truth_authority: bool = False
    accepted_as_recall: bool = False
    retention_execution_authorized: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision_envelope(self) -> "MemoryReviewDecisionEnvelope":
        if self.contract_ref != MEMORY_REVIEW_DECISION_CONTRACT_REF:
            raise ValueError("memory review decision contract ref drifted")
        _safe_ref(self.decision_ref, "decision_ref")
        _safe_ref(self.review_ref, "review_ref")
        _safe_ref(self.actor_ref, "actor_ref")
        _safe_text(self.safe_summary, "safe_summary")
        _safe_refs(self.source_refs, "source_refs")
        if self.source_provenance_contract_ref != MEMORY_SOURCE_PROVENANCE_CONTRACT_REF:
            raise ValueError("memory review decision must bind source provenance")
        if self.source_kind not in MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS:
            raise ValueError("memory review decision uses unknown source kind")
        _validate_kind_refs(
            self.source_refs,
            "source_refs",
            _source_prefix(self.source_kind),
        )
        if self.source_trust_posture != MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE:
            raise ValueError("memory review decision source is untrusted until reviewed")
        if self.redaction_status != "redacted_summary_only":
            raise ValueError("memory review decision must stay redacted-summary-only")
        _safe_refs(self.evidence_refs, "evidence_refs")
        _safe_refs(self.provenance_refs, "provenance_refs")
        _validate_kind_refs(
            self.provenance_refs,
            "provenance_refs",
            _provenance_prefix(self.source_kind),
        )
        _safe_refs(self.audit_refs, "audit_refs")
        _safe_refs(self.receipt_refs, "receipt_refs")
        _safe_refs(self.blocked_state_refs, "blocked_state_refs")
        missing_blocked_refs = [
            ref
            for ref in MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing_blocked_refs:
            raise ValueError("memory review decision missing required blocked states")
        for field_name in ["merge_refs", "supersedes_refs"]:
            for value in getattr(self, field_name):
                _safe_ref(value, field_name)
        for field_name in [
            "source_kind",
            "source_trust_posture",
            "redaction_status",
            "stale_state",
            "retention_posture",
            "correction_posture",
            "authority_boundary",
        ]:
            _safe_text(getattr(self, field_name), field_name)
        if self.review_only is not True:
            raise ValueError("memory review decisions are review-only")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by memory review decisions")
        return self


class MemoryReviewDecisionRequest(BaseModel):
    reviewer_ref: str = Field(default="actor-ref:local-operator", min_length=1)
    corrected_summary_ref: str | None = Field(default=None, min_length=1)
    corrected_safe_summary: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    merge_refs: list[str] = Field(default_factory=list)
    supersedes_refs: list[str] = Field(default_factory=list)
    forget_request_ref: str | None = Field(default=None, min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "MemoryReviewDecisionRequest":
        _safe_ref(self.reviewer_ref, "reviewer_ref")
        _safe_optional_ref(self.corrected_summary_ref, "corrected_summary_ref")
        _safe_optional_text(self.corrected_safe_summary, "corrected_safe_summary")
        for field_name in [
            "source_refs",
            "evidence_refs",
            "metadata_refs",
            "merge_refs",
            "supersedes_refs",
            "blocked_state_refs",
        ]:
            for value in getattr(self, field_name):
                _safe_ref(value, field_name)
        _safe_optional_ref(self.forget_request_ref, "forget_request_ref")
        missing_blocked_refs = [
            ref
            for ref in FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing_blocked_refs:
            raise ValueError("memory review decision request missing blocked states")
        return self


class MemoryReviewDecisionReceipt(BaseModel):
    contract_ref: str = Field(default=FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF)
    candidate_ref: str = Field(..., min_length=1)
    review_ref: str = Field(..., min_length=1)
    decision: MemoryReviewDecisionKind
    corrected_summary_ref: str | None = Field(default=None, min_length=1)
    corrected_safe_summary: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    reviewer_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    decision_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    evidence_timeline_event_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(default=MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF)
    approval_status: str = Field(default="approved", min_length=1)
    approval_reason_refs: list[str] = Field(
        default_factory=lambda: ["approval-reason:local-memory-review-scope-validated"]
    )
    safe_disable_ref: str = Field(default=MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF)
    rollback_ref: str = Field(default=MEMORY_REVIEW_WRITE_ROLLBACK_REF)
    safe_disable_posture_ref: str = Field(
        default=MEMORY_REVIEW_WRITE_SAFE_DISABLE_POSTURE_REF
    )
    safe_disable_enabled: bool = True
    rollback_execution_enabled: bool = False
    rollback_blocker_refs: list[str] = Field(
        default_factory=lambda: [MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF]
    )
    reviewed_recall_ref: str | None = Field(default=None, min_length=1)
    reviewed_recall_record_ref: str | None = Field(default=None, min_length=1)
    reviewed_recall_write_performed: bool = False
    correction_ref: str | None = Field(default=None, min_length=1)
    rejection_ref: str | None = Field(default=None, min_length=1)
    defer_ref: str | None = Field(default=None, min_length=1)
    merge_ref: str | None = Field(default=None, min_length=1)
    supersede_ref: str | None = Field(default=None, min_length=1)
    forget_request_ref: str | None = Field(default=None, min_length=1)
    merge_refs: list[str] = Field(default_factory=list)
    supersedes_refs: list[str] = Field(default_factory=list)
    suppressed_recall_record_refs: list[str] = Field(default_factory=list)
    safe_summary_ref: str = Field(..., min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS)
    )
    authority_boundary: str = Field(
        default=(
            "Memory Review decisions create backend-owned safe receipts; accept/correct "
            "may create recall-only local records. Recall is not truth and context "
            "injection, connector writes, CRM sync, automatic action execution, public "
            "beta, and production authority remain blocked."
        ),
        min_length=1,
        max_length=360,
    )
    context_injection_authorized: bool = False
    connector_write_authorized: bool = False
    external_crm_sync_authorized: bool = False
    account_sync_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    model_provider_authority_allowed: bool = False
    source_truth_authority: bool = False
    memory_truth_authority: bool = False
    production_authority_enabled: bool = False
    replayed: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> "MemoryReviewDecisionReceipt":
        if self.contract_ref != FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF:
            raise ValueError("FCC memory review decision contract ref drifted")
        for field_name in [
            "candidate_ref",
            "review_ref",
            "reviewer_ref",
            "receipt_ref",
            "decision_ref",
            "audit_ref",
            "idempotency_key_ref",
            "payload_fingerprint_ref",
            "evidence_timeline_event_ref",
            "safe_summary_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        _safe_ref(self.approval_ref, "approval_ref")
        _safe_ref(self.approval_scope_ref, "approval_scope_ref")
        _safe_text(self.approval_status, "approval_status")
        _safe_ref(self.safe_disable_ref, "safe_disable_ref")
        _safe_ref(self.rollback_ref, "rollback_ref")
        _safe_ref(self.safe_disable_posture_ref, "safe_disable_posture_ref")
        for field_name in [
            "source_refs",
            "evidence_refs",
            "approval_reason_refs",
            "rollback_blocker_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        if self.rollback_execution_enabled:
            raise ValueError("memory review rollback execution is blocked")
        for field_name in [
            "corrected_summary_ref",
            "reviewed_recall_ref",
            "reviewed_recall_record_ref",
            "correction_ref",
            "rejection_ref",
            "defer_ref",
            "merge_ref",
            "supersede_ref",
            "forget_request_ref",
        ]:
            _safe_optional_ref(getattr(self, field_name), field_name)
        _safe_optional_text(self.corrected_safe_summary, "corrected_safe_summary")
        for field_name in [
            "merge_refs",
            "supersedes_refs",
            "suppressed_recall_record_refs",
        ]:
            for ref in getattr(self, field_name):
                _safe_ref(ref, field_name)
        _safe_text(self.authority_boundary, "authority_boundary")
        missing_blocked_refs = [
            ref
            for ref in FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing_blocked_refs:
            raise ValueError("FCC memory review decision missing blocked states")
        if self.decision == "correct" and self.corrected_summary_ref is None:
            raise ValueError("correct memory review decisions require corrected_summary_ref")
        if self.decision == "correct" and self.corrected_safe_summary is None:
            raise ValueError("correct memory review decisions require corrected_safe_summary")
        if self.decision != "correct" and self.corrected_summary_ref is not None:
            raise ValueError("corrected_summary_ref belongs only to correct decisions")
        if self.decision != "correct" and self.corrected_safe_summary is not None:
            raise ValueError("corrected_safe_summary belongs only to correct decisions")
        if self.decision in {"accept", "correct"} and self.reviewed_recall_ref is None:
            raise ValueError("accept/correct decisions require reviewed recall ref")
        if self.decision in {"accept", "correct"} and self.reviewed_recall_record_ref is None:
            raise ValueError("accept/correct decisions require reviewed recall record ref")
        if self.decision in {"accept", "correct"} and self.reviewed_recall_write_performed is not True:
            raise ValueError("accept/correct decisions require reviewed recall write proof")
        if self.decision not in {"accept", "correct"} and self.reviewed_recall_write_performed:
            raise ValueError("non-write memory review decisions must not claim recall writes")
        if self.decision == "reject" and self.reviewed_recall_record_ref is not None:
            raise ValueError("reject decisions must not create reviewed recall records")
        if self.decision == "reject" and self.rejection_ref is None:
            raise ValueError("reject decisions require rejection ref")
        if self.decision == "defer" and self.defer_ref is None:
            raise ValueError("defer decisions require defer ref")
        if self.decision == "merge" and (self.merge_ref is None or not self.merge_refs):
            raise ValueError("merge decisions require merge refs")
        if (
            self.decision == "supersede"
            and (self.supersede_ref is None or not self.supersedes_refs)
        ):
            raise ValueError("supersede decisions require supersede refs")
        if self.decision == "forget_request" and self.forget_request_ref is None:
            raise ValueError("forget_request decisions require forget request ref")
        if self.decision not in {"accept", "correct"} and (
            self.reviewed_recall_ref is not None
            or self.reviewed_recall_record_ref is not None
        ):
            raise ValueError("non-accept/correct decisions must not create recall records")
        denied_flags = [
            "context_injection_authorized",
            "connector_write_authorized",
            "external_crm_sync_authorized",
            "account_sync_authorized",
            "automatic_action_execution_authorized",
            "model_provider_authority_allowed",
            "source_truth_authority",
            "memory_truth_authority",
            "production_authority_enabled",
        ]
        for flag in denied_flags:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by FCC memory review decisions")
        return self


MemoryReviewDecision = MemoryReviewDecisionReceipt


def build_memory_review_decision_envelope(
    *,
    decision_ref: str,
    review_ref: str,
    decision_state: MemoryReviewDecisionState,
    actor_ref: str,
    safe_summary: str,
    source_refs: list[str],
    evidence_refs: list[str],
    audit_refs: list[str],
    receipt_refs: list[str],
    provenance_refs: list[str],
    source_kind: str = "manual_note",
    blocked_state_refs: list[str] | None = None,
    merge_refs: list[str] | None = None,
    supersedes_refs: list[str] | None = None,
) -> MemoryReviewDecisionEnvelope:
    return MemoryReviewDecisionEnvelope(
        decision_ref=decision_ref,
        review_ref=review_ref,
        decision_state=decision_state,
        actor_ref=actor_ref,
        safe_summary=safe_summary,
        source_refs=source_refs,
        source_kind=source_kind,
        evidence_refs=evidence_refs,
        audit_refs=audit_refs,
        receipt_refs=receipt_refs,
        provenance_refs=provenance_refs,
        blocked_state_refs=blocked_state_refs
        or [
            *MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS,
            "blocked-state:no-connector-runtime",
            "blocked-state:no-account-auth",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-public-beta-or-production-authority",
        ],
        merge_refs=merge_refs or [],
        supersedes_refs=supersedes_refs or [],
    )


def memory_review_decision_payload_for_fingerprint(
    *,
    candidate_ref: str,
    decision: MemoryReviewDecisionKind,
    request: MemoryReviewDecisionRequest,
) -> dict[str, object]:
    return {
        "candidate_ref": candidate_ref,
        "decision": decision,
        "reviewer_ref": request.reviewer_ref,
        "corrected_summary_ref": request.corrected_summary_ref,
        "corrected_safe_summary": request.corrected_safe_summary,
        "source_refs": list(request.source_refs),
        "evidence_refs": list(request.evidence_refs),
        "metadata_refs": list(request.metadata_refs),
        "merge_refs": list(request.merge_refs),
        "supersedes_refs": list(request.supersedes_refs),
        "forget_request_ref": request.forget_request_ref,
        "blocked_state_refs": list(request.blocked_state_refs),
    }


def memory_review_payload_fingerprint_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8", errors="replace")).hexdigest()
    return f"payload-fingerprint:memory-review-decision:{digest[:24]}"


def memory_review_decision_ref(
    candidate_ref: str,
    decision: MemoryReviewDecisionKind,
    idempotency_ref: str,
) -> str:
    return (
        f"memory-review-decision:{decision}:"
        f"{_short_ref_suffix(candidate_ref)}:{_safe_suffix(idempotency_ref)}"
    )


def memory_review_decision_receipt_ref(
    candidate_ref: str,
    decision: MemoryReviewDecisionKind,
    idempotency_ref: str,
) -> str:
    return (
        f"receipt:memory-review:{decision}:"
        f"{_short_ref_suffix(candidate_ref)}:{_safe_suffix(idempotency_ref)}"
    )


def memory_review_decision_audit_ref(
    candidate_ref: str,
    decision: MemoryReviewDecisionKind,
    idempotency_ref: str,
) -> str:
    return (
        f"audit-ref:memory-review:{decision}:"
        f"{_short_ref_suffix(candidate_ref)}:{_safe_suffix(idempotency_ref)}"
    )


def memory_review_decision_evidence_ref(
    candidate_ref: str,
    decision: MemoryReviewDecisionKind,
) -> str:
    return f"evidence-ref:memory-review:{decision}:{_short_ref_suffix(candidate_ref)}"


def memory_review_reviewed_recall_ref(candidate_ref: str) -> str:
    return f"reviewed-recall-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_correction_ref(candidate_ref: str) -> str:
    return f"correction-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_rejection_ref(candidate_ref: str) -> str:
    return f"rejected-memory-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_defer_ref(candidate_ref: str) -> str:
    return f"deferred-memory-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_merge_ref(candidate_ref: str) -> str:
    return f"merged-memory-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_supersede_ref(candidate_ref: str) -> str:
    return f"superseded-memory-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def memory_review_forget_request_ref(candidate_ref: str) -> str:
    return f"forget-request-ref:memory-review:{_short_ref_suffix(candidate_ref)}"


def validate_memory_review_decision_envelope(
    envelope: MemoryReviewDecisionEnvelope,
) -> bool:
    MemoryReviewDecisionEnvelope(**envelope.model_dump())
    return True


def memory_review_decision_state_rows() -> list[dict[str, object]]:
    return [
        {
            "decision_state": state,
            "decision_state_ref": f"memory-review-decision-state:{state.replace('_', '-')}",
            "review_required": True,
            "actor_ref_required": True,
            "source_refs_required": True,
            "provenance_refs_required": True,
            "evidence_refs_required": True,
            "audit_refs_required": True,
            "receipt_refs_required": True,
            "blocked_state_refs_required": True,
            "writes_authorized": state in {"accept", "correct"},
            "write_scope_ref": (
                MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
                if state in {"accept", "correct"}
                else "blocked-state:no-memory-write"
            ),
            "deletes_authorized": False,
            "exports_authorized": False,
            "context_injection_authorized": False,
            "accepted_as_recall": state in {"accept", "correct"},
        }
        for state in MEMORY_REVIEW_DECISION_STATES
    ]


def memory_review_decision_authority_posture() -> dict[str, object]:
    return {
        "review_only": True,
        "memory_write_authorized": False,
        "reviewed_recall_write_authorized": True,
        "reviewed_recall_write_scope_ref": MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
        "reviewed_recall_write_scope": "accept_correct_reviewed_recall_only",
        "automatic_memory_write_authorized": False,
        "memory_delete_authorized": False,
        "memory_export_authorized": False,
        "context_injection_authorized": False,
        "connector_runtime_enabled": False,
        "account_auth_enabled": False,
        "provider_or_model_authority_allowed": False,
        "source_truth_authority": False,
        "accepted_as_recall": False,
        "retention_execution_authorized": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


__all__ = [
    "FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS",
    "FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF",
    "MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF",
    "MEMORY_REVIEW_RECEIPT_SCOPE_REF",
    "MEMORY_REVIEW_DECISION_CONTRACT_REF",
    "MEMORY_REVIEW_DECISION_KINDS",
    "MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS",
    "MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS",
    "MEMORY_REVIEW_DECISION_ROUTE_REFS",
    "MEMORY_REVIEW_DECISION_STATES",
    "MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF",
    "MEMORY_REVIEW_WRITE_ROLLBACK_REF",
    "MEMORY_REVIEW_WRITE_SAFE_DISABLE_POSTURE_REF",
    "MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF",
    "MemoryReviewDecisionEnvelope",
    "MemoryReviewDecisionKind",
    "MemoryReviewDecisionRequest",
    "MemoryReviewDecisionReceipt",
    "MemoryReviewDecisionState",
    "build_memory_review_decision_envelope",
    "memory_review_correction_ref",
    "memory_review_defer_ref",
    "memory_review_decision_audit_ref",
    "memory_review_decision_authority_posture",
    "memory_review_decision_evidence_ref",
    "memory_review_decision_payload_for_fingerprint",
    "memory_review_decision_receipt_ref",
    "memory_review_decision_ref",
    "memory_review_decision_state_rows",
    "memory_review_forget_request_ref",
    "memory_review_merge_ref",
    "memory_review_payload_fingerprint_ref",
    "memory_review_rejection_ref",
    "memory_review_reviewed_recall_ref",
    "memory_review_supersede_ref",
    "validate_memory_review_decision_envelope",
]
