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
    MemorySourceProvenanceKind,
)


BUSINESS_MEMORY_QUALITY_CONTRACT_REF = (
    "contract-ref:business-memory-quality-controls:v1"
)

BusinessMemoryCandidateKind = Literal[
    "profile",
    "project",
    "relationship",
    "organization",
    "deal",
    "opportunity",
    "promise",
    "follow_up",
    "preference",
    "decision",
    "commitment",
]

BUSINESS_MEMORY_CANDIDATE_KINDS: list[BusinessMemoryCandidateKind] = [
    "profile",
    "project",
    "relationship",
    "organization",
    "deal",
    "opportunity",
    "promise",
    "follow_up",
    "preference",
    "decision",
    "commitment",
]

BusinessMemoryQualityState = Literal[
    "duplicate",
    "conflict",
    "stale_expired",
    "low_confidence",
    "source_missing",
    "evidence_missing",
    "blocked",
    "reviewed",
]

BUSINESS_MEMORY_QUALITY_STATES: list[BusinessMemoryQualityState] = [
    "duplicate",
    "conflict",
    "stale_expired",
    "low_confidence",
    "source_missing",
    "evidence_missing",
    "blocked",
    "reviewed",
]

BUSINESS_MEMORY_REQUIRED_REF_FIELDS = [
    "review_ref",
    "candidate_ref",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "quality_state_refs",
    "related_entity_refs",
    "blocker_refs",
]

BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-memory-delete",
    "blocked-state:no-memory-export",
    "blocked-state:no-context-injection",
    "blocked-state:no-external-crm-write",
    "blocked-state:no-account-sync",
    "blocked-state:no-automatic-recall",
    "blocked-state:no-connector-runtime",
    "blocked-state:no-account-auth",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-raw-source-display",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]

BUSINESS_MEMORY_SURFACES = [
    "Today",
    "Action Inbox",
    "Evidence Timeline",
    "Weekly CEO Review",
]

_DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "external_crm_write_authorized",
    "account_sync_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
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
    "private key",
    "private_key",
    "api key",
    "api_key",
    "authorization",
    "bearer",
    "oauth",
    "cookie",
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


def _kind_ref(candidate_kind: str) -> str:
    return f"business-memory-kind:{candidate_kind.replace('_', '-')}"


def _quality_ref(quality_state: str) -> str:
    return f"business-memory-quality:{quality_state.replace('_', '-')}"


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe business memory ref")


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe business memory text")


def _safe_refs(values: list[str], field_name: str, *, require: bool = False) -> None:
    if require and not values:
        raise ValueError(f"{field_name} is required")
    for value in values:
        _safe_ref(value, field_name)


def _expected_candidate_prefix(candidate_kind: str) -> str:
    return f"business-memory-candidate:{candidate_kind.replace('_', '-')}"


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _provenance_prefix(source_kind: str) -> str:
    return f"provenance-ref:{source_kind.replace('_', '-')}"


def _matches_prefix(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(f"{prefix}:")


def _default_quality_refs() -> list[str]:
    return [
        _quality_ref("low_confidence"),
        _quality_ref("blocked"),
    ]


class BusinessMemoryQualityEnvelope(BaseModel):
    contract_ref: str = Field(default=BUSINESS_MEMORY_QUALITY_CONTRACT_REF)
    review_ref: str = Field(..., min_length=1)
    candidate_ref: str = Field(..., min_length=1)
    candidate_kind: BusinessMemoryCandidateKind
    safe_summary: str = Field(..., min_length=1, max_length=500)
    source_provenance_contract_ref: str = Field(
        default=MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    source_kind: MemorySourceProvenanceKind = "manual_note"
    source_trust_posture: str = Field(default=MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE)
    redaction_status: str = Field(default="redacted_summary_only")
    source_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    related_entity_refs: list[str] = Field(default_factory=list)
    quality_state_refs: list[str] = Field(default_factory=_default_quality_refs)
    duplicate_of_refs: list[str] = Field(default_factory=list)
    conflict_with_refs: list[str] = Field(default_factory=list)
    review_state: str = Field(default="review_needed", min_length=1, max_length=80)
    correction_path: str = Field(
        default="correction_requires_scoped_memory_write_contract",
        min_length=1,
        max_length=160,
    )
    stale_state: str = Field(
        default="recheck_source_refs_before_memory_use",
        min_length=1,
        max_length=160,
    )
    retention_posture: str = Field(
        default="retention_policy_not_bound",
        min_length=1,
        max_length=160,
    )
    delete_posture: str = Field(
        default="delete_execution_not_scoped",
        min_length=1,
        max_length=160,
    )
    export_posture: str = Field(
        default="export_execution_not_scoped",
        min_length=1,
        max_length=160,
    )
    blocker_refs: list[str] = Field(
        default_factory=lambda: list(BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS)
    )
    next_safe_action: str = Field(
        default=(
            "Review quality posture and safe refs; keep memory writes, CRM sync, "
            "and context injection blocked until scoped policy milestones exist."
        ),
        min_length=1,
        max_length=240,
    )
    feeds_today: bool = True
    feeds_action_inbox: bool = True
    feeds_evidence_timeline: bool = True
    feeds_weekly_ceo_review: bool = True
    safe_refs_only: bool = True
    review_required_before_recall: bool = True
    memory_write_authorized: bool = False
    memory_delete_authorized: bool = False
    memory_export_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    external_crm_write_authorized: bool = False
    account_sync_authorized: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    provider_or_model_authority_allowed: bool = False
    source_truth_authority: bool = False
    accepted_as_recall: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_business_memory_quality(self) -> "BusinessMemoryQualityEnvelope":
        if self.contract_ref != BUSINESS_MEMORY_QUALITY_CONTRACT_REF:
            raise ValueError("business memory quality contract ref drifted")
        _safe_ref(self.review_ref, "review_ref")
        _safe_ref(self.candidate_ref, "candidate_ref")
        expected_prefix = _expected_candidate_prefix(self.candidate_kind)
        if not _matches_prefix(self.candidate_ref, expected_prefix):
            raise ValueError("candidate_ref must match candidate_kind")
        _safe_text(self.safe_summary, "safe_summary")
        _safe_ref(
            self.source_provenance_contract_ref,
            "source_provenance_contract_ref",
        )
        if self.source_provenance_contract_ref != MEMORY_SOURCE_PROVENANCE_CONTRACT_REF:
            raise ValueError("business memory source provenance contract ref drifted")
        if self.source_kind not in MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS:
            raise ValueError("business memory source_kind is unsupported")
        if self.source_trust_posture != MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE:
            raise ValueError("business memory source must remain untrusted")
        if self.redaction_status != "redacted_summary_only":
            raise ValueError("business memory must remain redacted-summary-only")
        _safe_refs(self.source_refs, "source_refs", require=True)
        _safe_refs(self.provenance_refs, "provenance_refs", require=True)
        _safe_refs(self.evidence_refs, "evidence_refs", require=True)
        _safe_refs(self.related_entity_refs, "related_entity_refs", require=True)
        _safe_refs(self.duplicate_of_refs, "duplicate_of_refs")
        _safe_refs(self.conflict_with_refs, "conflict_with_refs")
        _safe_refs(self.blocker_refs, "blocker_refs", require=True)
        _safe_text(self.review_state, "review_state")
        _safe_text(self.correction_path, "correction_path")
        _safe_text(self.stale_state, "stale_state")
        _safe_text(self.retention_posture, "retention_posture")
        _safe_text(self.delete_posture, "delete_posture")
        _safe_text(self.export_posture, "export_posture")
        _safe_text(self.next_safe_action, "next_safe_action")
        allowed_quality_refs = {
            _quality_ref(state) for state in BUSINESS_MEMORY_QUALITY_STATES
        }
        if not self.quality_state_refs:
            raise ValueError("quality_state_refs are required")
        quality_refs = set(self.quality_state_refs)
        for quality_ref in self.quality_state_refs:
            _safe_ref(quality_ref, "quality_state_refs")
            if quality_ref not in allowed_quality_refs:
                raise ValueError("quality_state_refs contains unsupported state")
        for source_ref in self.source_refs:
            if not _matches_prefix(source_ref, _source_prefix(self.source_kind)):
                raise ValueError("business memory source ref kind mismatch")
        for provenance_ref in self.provenance_refs:
            if not _matches_prefix(
                provenance_ref,
                _provenance_prefix(self.source_kind),
            ):
                raise ValueError("business memory provenance ref kind mismatch")
        if _quality_ref("duplicate") in quality_refs and not self.duplicate_of_refs:
            raise ValueError("duplicate quality state requires duplicate_of_refs")
        if _quality_ref("conflict") in quality_refs and not self.conflict_with_refs:
            raise ValueError("conflict quality state requires conflict_with_refs")
        if (
            _quality_ref("source_missing") in quality_refs
            and "blocked-state:business-memory-source-missing" not in self.blocker_refs
        ):
            raise ValueError("source_missing quality state requires blocker ref")
        if (
            _quality_ref("evidence_missing") in quality_refs
            and "blocked-state:business-memory-evidence-missing"
            not in self.blocker_refs
        ):
            raise ValueError("evidence_missing quality state requires blocker ref")
        missing_blocker_refs = [
            blocked_ref
            for blocked_ref in BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS
            if blocked_ref not in self.blocker_refs
        ]
        if missing_blocker_refs:
            raise ValueError("business memory quality missing required blocker refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by business memory quality")
        for required_true in [
            "feeds_today",
            "feeds_action_inbox",
            "feeds_evidence_timeline",
            "feeds_weekly_ceo_review",
            "safe_refs_only",
            "review_required_before_recall",
        ]:
            if getattr(self, required_true) is not True:
                raise ValueError(f"{required_true} must stay true")
        return self


def build_business_memory_quality_envelope(
    *,
    review_ref: str,
    candidate_ref: str,
    candidate_kind: BusinessMemoryCandidateKind,
    safe_summary: str,
    source_refs: list[str],
    provenance_refs: list[str],
    evidence_refs: list[str],
    source_kind: MemorySourceProvenanceKind = "manual_note",
    related_entity_refs: list[str] | None = None,
    quality_state_refs: list[str] | None = None,
) -> BusinessMemoryQualityEnvelope:
    return BusinessMemoryQualityEnvelope(
        review_ref=review_ref,
        candidate_ref=candidate_ref,
        candidate_kind=candidate_kind,
        safe_summary=safe_summary,
        source_kind=source_kind,
        source_refs=source_refs,
        provenance_refs=provenance_refs,
        evidence_refs=evidence_refs,
        related_entity_refs=related_entity_refs or [],
        quality_state_refs=quality_state_refs or _default_quality_refs(),
    )


def validate_business_memory_quality_envelope(
    envelope: BusinessMemoryQualityEnvelope,
) -> bool:
    BusinessMemoryQualityEnvelope(**envelope.model_dump())
    return True


def business_memory_candidate_kind_rows() -> list[dict[str, object]]:
    return [
        {
            "candidate_kind": candidate_kind,
            "candidate_kind_ref": _kind_ref(candidate_kind),
            "review_required": True,
            "safe_summary_only": True,
            "source_refs_required": True,
            "provenance_refs_required": True,
            "evidence_refs_required": True,
            "quality_posture_required": True,
            "correction_path_required": True,
            "retention_delete_export_posture_required": True,
            "crm_write_authorized": False,
            "account_sync_authorized": False,
            "context_injection_authorized": False,
            "accepted_as_recall": False,
        }
        for candidate_kind in BUSINESS_MEMORY_CANDIDATE_KINDS
    ]


def business_memory_quality_state_rows() -> list[dict[str, object]]:
    blocking_states = {
        "duplicate",
        "conflict",
        "stale_expired",
        "low_confidence",
        "source_missing",
        "evidence_missing",
        "blocked",
    }
    return [
        {
            "quality_state": quality_state,
            "quality_state_ref": _quality_ref(quality_state),
            "blocks_unreviewed_recall": True,
            "requires_operator_review": True,
            "requires_safe_refs": True,
            "requires_correction_path": quality_state
            in {
                "duplicate",
                "conflict",
                "stale_expired",
                "low_confidence",
            },
            "is_blocking_posture": quality_state in blocking_states,
            "authorizes_memory_write": False,
            "authorizes_crm_write": False,
            "authorizes_context_injection": False,
        }
        for quality_state in BUSINESS_MEMORY_QUALITY_STATES
    ]


def business_memory_surface_bindings() -> list[dict[str, object]]:
    return [
        {
            "surface": "Today",
            "feed_status": "implemented_safe_ref_quality_summary",
            "feed_ref": "today-ref:memory-review-business-quality",
            "authority_boundary": "Quality posture can create blockers and follow-up refs only.",
        },
        {
            "surface": "Action Inbox",
            "feed_status": "implemented_follow_up_candidate_refs_only",
            "feed_ref": "action-inbox-ref:memory-follow-up-candidates",
            "authority_boundary": "Promises and follow-ups are review candidates, not execution tasks.",
        },
        {
            "surface": "Evidence Timeline",
            "feed_status": "implemented_history_refs_only",
            "feed_ref": "evidence-ref:memory-business-quality-history",
            "authority_boundary": "Quality changes must read as history with safe refs only.",
        },
        {
            "surface": "Weekly CEO Review",
            "feed_status": "implemented_carry_forward_refs_only",
            "feed_ref": "weekly-review-ref:business-memory-carry-forward",
            "authority_boundary": "Weekly review can carry decisions and blockers, not sync accounts.",
        },
    ]


def business_memory_authority_posture() -> dict[str, object]:
    return {
        "safe_refs_only": True,
        "review_required_before_recall": True,
        "memory_write_authorized": False,
        "memory_delete_authorized": False,
        "memory_export_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "external_crm_write_authorized": False,
        "account_sync_authorized": False,
        "connector_runtime_enabled": False,
        "account_auth_enabled": False,
        "provider_or_model_authority_allowed": False,
        "source_truth_authority": False,
        "accepted_as_recall": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


def business_memory_quality_ref(quality_state: BusinessMemoryQualityState) -> str:
    return _quality_ref(quality_state)


def business_memory_candidate_ref(
    candidate_kind: BusinessMemoryCandidateKind,
    suffix: str,
) -> str:
    candidate_ref = f"{_expected_candidate_prefix(candidate_kind)}:{suffix}"
    _safe_ref(candidate_ref, "candidate_ref")
    return candidate_ref


__all__ = [
    "BUSINESS_MEMORY_CANDIDATE_KINDS",
    "BUSINESS_MEMORY_QUALITY_CONTRACT_REF",
    "BUSINESS_MEMORY_QUALITY_STATES",
    "BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS",
    "BUSINESS_MEMORY_REQUIRED_REF_FIELDS",
    "BUSINESS_MEMORY_SURFACES",
    "BusinessMemoryCandidateKind",
    "BusinessMemoryQualityEnvelope",
    "BusinessMemoryQualityState",
    "build_business_memory_quality_envelope",
    "business_memory_authority_posture",
    "business_memory_candidate_kind_rows",
    "business_memory_candidate_ref",
    "business_memory_quality_ref",
    "business_memory_quality_state_rows",
    "business_memory_surface_bindings",
    "validate_business_memory_quality_envelope",
]
