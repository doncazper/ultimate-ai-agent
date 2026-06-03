from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.claims import Claim
from ultimate_ai_agent.core.truth.enums import (
    ClaimStatus,
    EvidenceStrength,
    SourceRevocation,
    SourceStaleness,
    TruthSourceKind,
    VerificationDecisionStatus,
)
from ultimate_ai_agent.core.truth.evidence import EvidenceChain, EvidenceRef
from ultimate_ai_agent.core.truth.validation import (
    assert_memory_not_truth,
    assert_model_output_not_truth,
    assert_no_external_verification,
    assert_no_raw_truth_content,
)


PRIMARY_SOURCE_KINDS = {
    TruthSourceKind.canonical_document,
    TruthSourceKind.evidence_manifest,
    TruthSourceKind.receipt,
    TruthSourceKind.event_ledger,
    TruthSourceKind.user_reviewed_source,
}

MEMORY_SOURCE_KINDS = {
    TruthSourceKind.source_linked_memory,
    TruthSourceKind.reviewed_memory,
    TruthSourceKind.unreviewed_memory,
}

BLOCKED_OUTPUT_KINDS = {
    TruthSourceKind.model_output,
    TruthSourceKind.runtime_output,
    TruthSourceKind.openwebui_output,
}

RECOGNIZED_SOURCE_REF_PREFIXES = {
    "canonical": TruthSourceKind.canonical_document,
    "canonical_document": TruthSourceKind.canonical_document,
    "evidence": TruthSourceKind.evidence_manifest,
    "evidence_manifest": TruthSourceKind.evidence_manifest,
    "receipt": TruthSourceKind.receipt,
    "event": TruthSourceKind.event_ledger,
    "event_ledger": TruthSourceKind.event_ledger,
    "user-review": TruthSourceKind.user_reviewed_source,
    "user_reviewed_source": TruthSourceKind.user_reviewed_source,
    "memory": TruthSourceKind.reviewed_memory,
    "source_linked_memory": TruthSourceKind.source_linked_memory,
    "reviewed_memory": TruthSourceKind.reviewed_memory,
    "unreviewed_memory": TruthSourceKind.unreviewed_memory,
    "model": TruthSourceKind.model_output,
    "model_output": TruthSourceKind.model_output,
    "runtime": TruthSourceKind.runtime_output,
    "runtime_output": TruthSourceKind.runtime_output,
    "openwebui": TruthSourceKind.openwebui_output,
    "openwebui_output": TruthSourceKind.openwebui_output,
}


class VerificationRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    claim: Claim
    evidence_chain: EvidenceChain
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    requested_status: ClaimStatus = ClaimStatus.evidence_supported
    allow_memory_only: bool = False
    allow_model_output: bool = False
    allow_unreviewed_memory: bool = False
    allow_stale_sources: bool = False
    allow_conflicted_sources: bool = False
    allow_revoked_sources: bool = False
    allow_raw_content: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m25_request(self):
        assert_no_external_verification(
            external_verification_enabled=False,
            web_search_enabled=False,
            model_verification_enabled=False,
        )
        if self.allow_model_output:
            raise ValueError("allow_model_output must be False in M25.")
        if self.allow_raw_content:
            raise ValueError("allow_raw_content must be False in M25.")
        assert_no_raw_truth_content(self.metadata)
        return self


class VerificationDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    allowed: bool
    status: VerificationDecisionStatus
    claim_status: ClaimStatus
    evidence_strength: EvidenceStrength
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    required_next_action: Optional[str] = None
    source_priority_summary: str = ""
    warnings: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


def verify_claim_against_evidence_chain(request: VerificationRequest) -> VerificationDecision:
    chain = request.evidence_chain
    reasons: List[str] = []
    warnings: List[str] = []

    source_kinds = {evidence.source_kind for evidence in request.evidence_refs}
    if not source_kinds:
        source_kinds = _infer_source_kinds_from_refs(chain.source_refs)

    _append_blocking_source_reasons(source_kinds, reasons, warnings)
    _append_unknown_source_reasons(request, source_kinds, reasons)
    _append_chain_state_reasons(request, reasons, warnings)

    if not chain.evidence_refs:
        reasons.append("MISSING_EVIDENCE")
        return _decision(request, False, VerificationDecisionStatus.requires_evidence, ClaimStatus.unverified, reasons, warnings)

    if any(kind in BLOCKED_OUTPUT_KINDS for kind in source_kinds):
        assert_model_output_not_truth(chain)
        return _decision(request, False, VerificationDecisionStatus.blocked, ClaimStatus.blocked, reasons, warnings)

    if source_kinds and source_kinds.issubset(MEMORY_SOURCE_KINDS):
        assert_memory_not_truth(chain)
        if request.requested_status == ClaimStatus.verified_by_primary_source:
            reasons.append("MEMORY_ONLY_CANNOT_VERIFY_TRUTH")
        return _decision(request, False, VerificationDecisionStatus.denied, ClaimStatus.source_linked, reasons, warnings)

    if TruthSourceKind.unreviewed_memory in source_kinds and not request.allow_unreviewed_memory:
        reasons.append("UNREVIEWED_MEMORY_CANNOT_VERIFY_TRUTH")

    if request.requested_status == ClaimStatus.verified_by_primary_source and not source_kinds.intersection(PRIMARY_SOURCE_KINDS):
        reasons.append("PRIMARY_SOURCE_EVIDENCE_REQUIRED")

    if reasons:
        return _decision(request, False, _status_for_reasons(reasons), _claim_status_for_reasons(reasons), reasons, warnings)

    allowed_status = (
        ClaimStatus.verified_by_primary_source
        if request.requested_status == ClaimStatus.verified_by_primary_source
        else ClaimStatus.evidence_supported
    )
    return _decision(request, True, VerificationDecisionStatus.allowed, allowed_status, ["PRIMARY_SOURCE_EVIDENCE_ACCEPTED"], warnings)


def _append_blocking_source_reasons(
    source_kinds: set[TruthSourceKind],
    reasons: List[str],
    warnings: List[str],
) -> None:
    if TruthSourceKind.model_output in source_kinds:
        reasons.append("MODEL_OUTPUT_CANNOT_VERIFY_TRUTH")
    if TruthSourceKind.runtime_output in source_kinds:
        reasons.append("RUNTIME_OUTPUT_CANNOT_VERIFY_TRUTH")
    if TruthSourceKind.openwebui_output in source_kinds:
        reasons.append("OPENWEBUI_OUTPUT_CANNOT_VERIFY_TRUTH")
    if TruthSourceKind.unreviewed_memory in source_kinds:
        warnings.append("Unreviewed memory was present and cannot verify truth.")


def _append_unknown_source_reasons(
    request: VerificationRequest,
    source_kinds: set[TruthSourceKind],
    reasons: List[str],
) -> None:
    if TruthSourceKind.unknown in source_kinds:
        reasons.append("UNKNOWN_SOURCE_KIND_DENIED")

    source_refs = list(request.evidence_chain.source_refs)
    source_refs.extend(evidence.source_ref for evidence in request.evidence_refs)
    if any(_source_ref_prefix_kind(ref) is TruthSourceKind.unknown for ref in source_refs):
        reasons.append("ARBITRARY_SOURCE_REF_DENIED")


def _append_chain_state_reasons(request: VerificationRequest, reasons: List[str], warnings: List[str]) -> None:
    chain = request.evidence_chain
    if (chain.stale_refs or chain.source_staleness in {SourceStaleness.stale, SourceStaleness.expired}) and not request.allow_stale_sources:
        reasons.append("STALE_SOURCE_CANNOT_VERIFY_TRUTH")
    if chain.conflict_refs and not request.allow_conflicted_sources:
        reasons.append("CONFLICTED_SOURCE_CANNOT_VERIFY_TRUTH")
    if (
        chain.revoked_refs
        or chain.source_revocation in {SourceRevocation.revoked, SourceRevocation.deleted, SourceRevocation.superseded}
    ) and not request.allow_revoked_sources:
        reasons.append("REVOKED_SOURCE_CANNOT_VERIFY_TRUTH")
    if chain.memory_refs:
        warnings.append("Memory refs are recall context only, not truth authority.")


def _infer_source_kinds_from_refs(source_refs: List[str]) -> set[TruthSourceKind]:
    inferred: set[TruthSourceKind] = set()
    for ref in source_refs:
        inferred.add(_source_ref_prefix_kind(ref))
    return inferred


def _source_ref_prefix_kind(ref: str) -> TruthSourceKind:
    prefix = ref.split(":", 1)[0]
    return RECOGNIZED_SOURCE_REF_PREFIXES.get(prefix, TruthSourceKind.unknown)


def _status_for_reasons(reasons: List[str]) -> VerificationDecisionStatus:
    if any("OUTPUT_CANNOT_VERIFY_TRUTH" in reason for reason in reasons):
        return VerificationDecisionStatus.blocked
    return VerificationDecisionStatus.denied


def _claim_status_for_reasons(reasons: List[str]) -> ClaimStatus:
    if any(reason.startswith("STALE") for reason in reasons):
        return ClaimStatus.stale
    if any(reason.startswith("CONFLICTED") for reason in reasons):
        return ClaimStatus.conflicted
    if any(reason.startswith("REVOKED") for reason in reasons):
        return ClaimStatus.revoked
    if any("OUTPUT_CANNOT_VERIFY_TRUTH" in reason for reason in reasons):
        return ClaimStatus.blocked
    return ClaimStatus.rejected


def _decision(
    request: VerificationRequest,
    allowed: bool,
    status: VerificationDecisionStatus,
    claim_status: ClaimStatus,
    reason_codes: List[str],
    warnings: List[str],
) -> VerificationDecision:
    return VerificationDecision(
        decision_id=f"decision:{request.request_id}",
        request_id=request.request_id,
        allowed=allowed,
        status=status,
        claim_status=claim_status,
        evidence_strength=request.evidence_chain.evidence_strength,
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_message=(
            "Provided primary/source-backed evidence supports this claim."
            if allowed
            else "Provided evidence cannot verify this claim under M25 policy."
        ),
        required_next_action=None if allowed else "provide_primary_source_or_user_review",
        source_priority_summary=request.evidence_chain.source_priority_summary,
        warnings=list(dict.fromkeys(warnings)),
    )
