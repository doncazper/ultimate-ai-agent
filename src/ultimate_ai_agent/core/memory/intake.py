from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.business_memory import (
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    BusinessMemoryCandidateKind,
    business_memory_candidate_ref,
    business_memory_quality_ref,
)
from ultimate_ai_agent.core.memory.review_decisions import (
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
)
from ultimate_ai_agent.core.memory.source_provenance import (
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
    MemorySourceProvenanceKind,
)


CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF = (
    "contract-ref:cross-surface-memory-intake:v1"
)

CrossSurfaceMemoryIntakeSurface = Literal[
    "Today",
    "Chat",
    "Plans",
    "Actions",
    "Evidence",
    "Local Coding",
    "External Assistant Review",
]

CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES: list[
    CrossSurfaceMemoryIntakeSurface
] = [
    "Today",
    "Chat",
    "Plans",
    "Actions",
    "Evidence",
    "Local Coding",
    "External Assistant Review",
]

CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "candidate_ref",
    "review_queue_ref",
    "surface",
    "source_kind",
    "candidate_kind",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "quality_state_refs",
    "missing_evidence_refs",
    "stale_state",
    "next_safe_action",
    "blocked_state_refs",
]

CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-provider-call",
    "blocked-state:no-account-fetch",
    "blocked-state:no-browser-import",
    "blocked-state:no-shell-history-import",
    "blocked-state:no-raw-file-import",
    "blocked-state:no-connector-runtime",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]

_SOURCE_KIND_BY_SURFACE: dict[
    CrossSurfaceMemoryIntakeSurface, MemorySourceProvenanceKind
] = {
    "Today": "evidence_timeline_ref",
    "Chat": "local_chat_summary",
    "Plans": "task_plan",
    "Actions": "action_proposal",
    "Evidence": "evidence_timeline_ref",
    "Local Coding": "local_coding_summary",
    "External Assistant Review": "external_assistant_review_summary",
}

_CANDIDATE_KIND_BY_SURFACE: dict[
    CrossSurfaceMemoryIntakeSurface, BusinessMemoryCandidateKind
] = {
    "Today": "follow_up",
    "Chat": "preference",
    "Plans": "decision",
    "Actions": "commitment",
    "Evidence": "decision",
    "Local Coding": "project",
    "External Assistant Review": "opportunity",
}

_DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "provider_call_enabled",
    "account_fetch_enabled",
    "browser_import_enabled",
    "shell_history_import_enabled",
    "raw_file_import_enabled",
    "connector_runtime_enabled",
    "source_truth_authority",
    "accepted_as_recall",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw file",
    "raw_file",
    "shell history",
    "browser state",
    "account fetch",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "token",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class CrossSurfaceMemoryIntakeProposal(BaseModel):
    contract_ref: str = CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    surface: CrossSurfaceMemoryIntakeSurface
    source_kind: MemorySourceProvenanceKind
    candidate_kind: BusinessMemoryCandidateKind
    candidate_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=360)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    source_provenance_contract_ref: str = MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    memory_review_decision_contract_ref: str = MEMORY_REVIEW_DECISION_CONTRACT_REF
    business_memory_quality_contract_ref: str = BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    source_trust_posture: str = MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE
    provenance_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    quality_state_refs: list[str] = Field(default_factory=list, min_length=1)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    missing_evidence_posture: str = "missing_safe_evidence_until_reviewed"
    confidence_posture: str = "low_confidence_until_reviewed"
    stale_state: str = "recheck_source_refs_before_memory_intake"
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    review_queue_ref: str = Field(..., min_length=1)
    review_required: bool = True
    safe_summary_only: bool = True
    source_payload_storage_allowed: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    provider_call_enabled: bool = False
    account_fetch_enabled: bool = False
    browser_import_enabled: bool = False
    shell_history_import_enabled: bool = False
    raw_file_import_enabled: bool = False
    connector_runtime_enabled: bool = False
    source_truth_authority: bool = False
    accepted_as_recall: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intake_proposal(self) -> "CrossSurfaceMemoryIntakeProposal":
        if self.contract_ref != CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF:
            raise ValueError("cross-surface memory intake contract ref drifted")
        if self.source_kind != _SOURCE_KIND_BY_SURFACE[self.surface]:
            raise ValueError("memory intake source kind does not match surface")
        if self.candidate_kind != _CANDIDATE_KIND_BY_SURFACE[self.surface]:
            raise ValueError("memory intake candidate kind does not match surface")
        _safe_ref(self.contract_ref, "contract_ref")
        _safe_ref(self.proposal_ref, "proposal_ref")
        _safe_ref(self.candidate_ref, "candidate_ref")
        _safe_ref(self.review_queue_ref, "review_queue_ref")
        _safe_text(self.surface, "surface")
        _safe_text(self.source_kind, "source_kind")
        _safe_text(self.candidate_kind, "candidate_kind")
        _safe_text(self.safe_summary, "safe_summary")
        _safe_ref(self.source_provenance_contract_ref, "source_provenance_contract_ref")
        _safe_ref(
            self.memory_review_decision_contract_ref,
            "memory_review_decision_contract_ref",
        )
        _safe_ref(
            self.business_memory_quality_contract_ref,
            "business_memory_quality_contract_ref",
        )
        if self.source_provenance_contract_ref != MEMORY_SOURCE_PROVENANCE_CONTRACT_REF:
            raise ValueError("memory intake must bind memory source provenance")
        if self.memory_review_decision_contract_ref != MEMORY_REVIEW_DECISION_CONTRACT_REF:
            raise ValueError("memory intake must bind memory review decisions")
        if self.business_memory_quality_contract_ref != BUSINESS_MEMORY_QUALITY_CONTRACT_REF:
            raise ValueError("memory intake must bind business memory quality")
        if self.source_trust_posture != MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE:
            raise ValueError("memory intake source is untrusted until reviewed")
        if not _matches_prefix(
            self.candidate_ref,
            f"business-memory-candidate:{self.candidate_kind.replace('_', '-')}",
        ):
            raise ValueError("memory intake candidate ref kind mismatch")
        for field_name in [
            "source_refs",
            "provenance_refs",
            "evidence_refs",
            "quality_state_refs",
            "missing_evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        source_prefix = _source_prefix(self.source_kind)
        provenance_prefix = _provenance_prefix(self.source_kind)
        for source_ref in self.source_refs:
            if not _matches_prefix(source_ref, source_prefix):
                raise ValueError("memory intake source ref kind mismatch")
        for provenance_ref in self.provenance_refs:
            if not _matches_prefix(provenance_ref, provenance_prefix):
                raise ValueError("memory intake provenance ref kind mismatch")
        missing_blocked = set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("cross-surface memory intake missing blocked refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by cross-surface memory intake")
        if self.review_required is not True:
            raise ValueError("cross-surface memory intake requires review")
        if self.safe_summary_only is not True:
            raise ValueError("cross-surface memory intake requires safe summary only")
        _safe_text(self.missing_evidence_posture, "missing_evidence_posture")
        _safe_text(self.confidence_posture, "confidence_posture")
        _safe_text(self.stale_state, "stale_state")
        _safe_text(self.next_safe_action, "next_safe_action")
        return self


def build_cross_surface_memory_intake_proposal(
    *,
    surface: CrossSurfaceMemoryIntakeSurface,
    proposal_ref: str | None = None,
    safe_summary: str | None = None,
    evidence_refs: list[str] | None = None,
    missing_evidence_refs: list[str] | None = None,
) -> CrossSurfaceMemoryIntakeProposal:
    surface_slug = _surface_slug(surface)
    source_kind = _SOURCE_KIND_BY_SURFACE[surface]
    candidate_kind = _CANDIDATE_KIND_BY_SURFACE[surface]
    source_slug = source_kind.replace("_", "-")
    proposal = proposal_ref or f"memory-intake-proposal:{surface_slug}"
    return CrossSurfaceMemoryIntakeProposal(
        proposal_ref=proposal,
        surface=surface,
        source_kind=source_kind,
        candidate_kind=candidate_kind,
        candidate_ref=business_memory_candidate_ref(candidate_kind, surface_slug),
        safe_summary=safe_summary
        or (
            f"{surface} can propose a reviewed memory candidate using safe refs; "
            "no write or context injection is authorized."
        ),
        source_refs=[f"source-ref:{source_slug}:{surface_slug}"],
        provenance_refs=[f"provenance-ref:{source_slug}:{surface_slug}"],
        evidence_refs=evidence_refs or [f"evidence-ref:memory-intake:{surface_slug}"],
        quality_state_refs=[
            business_memory_quality_ref("low_confidence"),
            business_memory_quality_ref("blocked"),
        ],
        missing_evidence_refs=missing_evidence_refs
        or [f"missing-evidence-ref:memory-intake:{surface_slug}"],
        review_queue_ref=f"memory-review-queue-ref:intake:{surface_slug}",
        next_safe_action=(
            "Review source, provenance, confidence, stale-state, and evidence "
            "refs before any later memory decision."
        ),
    )


def cross_surface_memory_intake_proposals() -> list[CrossSurfaceMemoryIntakeProposal]:
    return [
        build_cross_surface_memory_intake_proposal(surface=surface)
        for surface in CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    ]


def cross_surface_memory_intake_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "review_required": True,
        "safe_summary_only": True,
        "source_payload_storage_allowed": False,
        "memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "provider_call_enabled": False,
        "account_fetch_enabled": False,
        "browser_import_enabled": False,
        "shell_history_import_enabled": False,
        "raw_file_import_enabled": False,
        "connector_runtime_enabled": False,
        "source_truth_authority": False,
        "accepted_as_recall": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


def cross_surface_memory_intake_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": "implemented_memory_intake_proposal_refs",
            "feed_ref": f"memory-intake-proposal:{_surface_slug(surface)}",
            "authority_boundary": (
                "Memory intake proposals are review-only and cannot write memory "
                "or inject context."
            ),
        }
        for surface in CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    ]


def _surface_slug(surface: str) -> str:
    return surface.lower().replace(" ", "-")


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _provenance_prefix(source_kind: str) -> str:
    return f"provenance-ref:{source_kind.replace('_', '-')}"


def _matches_prefix(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(f"{prefix}:")


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _reject_unsafe_text(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    _reject_unsafe_text(value, field_name)


def _reject_unsafe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory intake text")


__all__ = [
    "CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF",
    "CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS",
    "CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS",
    "CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES",
    "CrossSurfaceMemoryIntakeProposal",
    "CrossSurfaceMemoryIntakeSurface",
    "build_cross_surface_memory_intake_proposal",
    "cross_surface_memory_intake_authority_posture",
    "cross_surface_memory_intake_proposals",
    "cross_surface_memory_intake_surface_bindings",
]
