from __future__ import annotations

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


MEMORY_REVIEW_DECISION_CONTRACT_REF = "contract-ref:memory-review-decision:v1"

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


def _safe_refs(values: list[str], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} is required")
    for value in values:
        _safe_ref(value, field_name)


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _provenance_prefix(source_kind: str) -> str:
    return f"provenance-ref:{source_kind.replace('_', '-')}"


def _matches_prefix(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(f"{prefix}:")


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
            "writes_authorized": False,
            "deletes_authorized": False,
            "exports_authorized": False,
            "context_injection_authorized": False,
            "accepted_as_recall": False,
        }
        for state in MEMORY_REVIEW_DECISION_STATES
    ]


def memory_review_decision_authority_posture() -> dict[str, object]:
    return {
        "review_only": True,
        "memory_write_authorized": False,
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
    "MEMORY_REVIEW_DECISION_CONTRACT_REF",
    "MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS",
    "MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS",
    "MEMORY_REVIEW_DECISION_STATES",
    "MemoryReviewDecisionEnvelope",
    "MemoryReviewDecisionState",
    "build_memory_review_decision_envelope",
    "memory_review_decision_authority_posture",
    "memory_review_decision_state_rows",
    "validate_memory_review_decision_envelope",
]
