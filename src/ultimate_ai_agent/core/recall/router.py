from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.recall.candidates import RecallCandidate
from ultimate_ai_agent.core.recall.enums import RecallCandidateStatus, RecallDecisionStatus, RecallSourceKind
from ultimate_ai_agent.core.recall.policy import (
    BLOCKED_RECALL_OUTPUT_KINDS,
    infer_recall_source_kind,
    recall_source_priority_rank,
    trusted_recall_source_kind,
)
from ultimate_ai_agent.core.recall.validation import validate_safe_recall_payload, validate_safe_recall_text


class GroundedRecallRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    query_summary: str = Field(..., min_length=1)
    candidates: List[RecallCandidate] = Field(default_factory=list)
    max_candidates: int = Field(default=5, ge=0, le=50)
    max_context_tokens: int = Field(default=2000, ge=0, le=100000)
    include_unreviewed_memory: bool = False
    include_stale_sources: bool = False
    include_conflicted_sources: bool = False
    include_revoked_sources: bool = False
    allow_model_output: bool = False
    allow_runtime_output: bool = False
    allow_openwebui_output: bool = False
    allow_raw_content: bool = False
    enable_vector_search: bool = False
    enable_embeddings: bool = False
    enable_external_retrieval: bool = False
    enable_source_crawling: bool = False
    automatic_memory_write: bool = False
    context_injection_enabled: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_request(self):
        validate_safe_recall_text(self.query_summary, "query_summary")
        validate_safe_recall_payload(self.metadata_refs, "metadata_refs")
        validate_safe_recall_payload(self.metadata)
        blocked_true_fields = [
            "allow_model_output",
            "allow_runtime_output",
            "allow_openwebui_output",
            "allow_raw_content",
            "enable_vector_search",
            "enable_embeddings",
            "enable_external_retrieval",
            "enable_source_crawling",
            "automatic_memory_write",
            "context_injection_enabled",
        ]
        for field_name in blocked_true_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M26")
        return self


class RecallSelection(BaseModel):
    candidate_ref: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    source_kind: RecallSourceKind
    safe_summary: str = Field(..., min_length=1)
    priority_rank: int = Field(..., ge=0)
    token_estimate: int = Field(default=0, ge=0, le=20000)
    reason_codes: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    source_priority_summary: str = ""
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_selection(self):
        validate_safe_recall_text(self.safe_summary, "safe_summary")
        validate_safe_recall_payload(self.metadata_refs, "metadata_refs")
        validate_safe_recall_payload(self.metadata)
        return self


class GroundedRecallDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    status: RecallDecisionStatus = RecallDecisionStatus.empty
    selected: List[RecallSelection] = Field(default_factory=list)
    excluded: List[RecallSelection] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    no_memory_write_performed: bool = True
    no_external_retrieval_performed: bool = True
    no_vector_search_performed: bool = True
    no_context_injection_performed: bool = True
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_decision(self):
        if not self.no_memory_write_performed:
            raise ValueError("M26 recall decision must not write memory")
        if not self.no_external_retrieval_performed:
            raise ValueError("M26 recall decision must not perform external retrieval")
        if not self.no_vector_search_performed:
            raise ValueError("M26 recall decision must not perform vector search")
        if not self.no_context_injection_performed:
            raise ValueError("M26 recall decision must not inject context")
        validate_safe_recall_payload(self.metadata_refs, "metadata_refs")
        validate_safe_recall_payload(self.metadata)
        return self


def route_grounded_recall(request: GroundedRecallRequest) -> GroundedRecallDecision:
    selected: List[RecallSelection] = []
    excluded: List[RecallSelection] = []

    for candidate in request.candidates:
        reasons = _candidate_exclusion_reasons(candidate, request)
        selection = _selection_from_candidate(candidate, reasons)
        if reasons:
            excluded.append(selection)
        else:
            selected.append(selection)

    selected.sort(key=lambda item: (item.priority_rank, item.candidate_ref))
    selected = _cap_selected_by_budget(selected, request.max_candidates, request.max_context_tokens)

    status = RecallDecisionStatus.allowed if selected else RecallDecisionStatus.blocked if excluded else RecallDecisionStatus.empty
    reason_codes = ["GROUNDED_RECALL_CANDIDATES_SELECTED"] if selected else ["NO_ELIGIBLE_RECALL_CANDIDATES"]
    return GroundedRecallDecision(
        decision_id=f"recall:decision:{request.request_id}",
        request_id=request.request_id,
        status=status,
        selected=selected,
        excluded=excluded,
        reason_codes=reason_codes,
        safe_message=(
            "Grounded recall selected safe, evidence-linked summaries."
            if selected
            else "No eligible recall candidates were selected."
        ),
    )


def _candidate_exclusion_reasons(candidate: RecallCandidate, request: GroundedRecallRequest) -> List[str]:
    reasons: List[str] = candidate.source_identity_reason_codes()
    inferred_kind = infer_recall_source_kind(candidate.source_ref)
    effective_kind = trusted_recall_source_kind(candidate.source_ref, candidate.source_kind)
    if candidate.source_kind in BLOCKED_RECALL_OUTPUT_KINDS:
        reasons.append(f"{candidate.source_kind.value.upper()}_EXCLUDED")
    if inferred_kind in BLOCKED_RECALL_OUTPUT_KINDS:
        reasons.append(f"{inferred_kind.value.upper()}_EXCLUDED")
    if effective_kind == RecallSourceKind.unreviewed_memory and not request.include_unreviewed_memory:
        reasons.append("UNREVIEWED_MEMORY_EXCLUDED")
    if candidate.status == RecallCandidateStatus.stale and not request.include_stale_sources:
        reasons.append("STALE_SOURCE_EXCLUDED")
    if candidate.status == RecallCandidateStatus.conflicted and not request.include_conflicted_sources:
        reasons.append("CONFLICTED_SOURCE_EXCLUDED")
    if candidate.status == RecallCandidateStatus.revoked and not request.include_revoked_sources:
        reasons.append("REVOKED_SOURCE_EXCLUDED")
    if candidate.status == RecallCandidateStatus.deleted:
        reasons.append("DELETED_SOURCE_EXCLUDED")
    if candidate.status == RecallCandidateStatus.superseded:
        reasons.append("SUPERSEDED_SOURCE_EXCLUDED")
    if candidate.status == RecallCandidateStatus.blocked:
        reasons.append("BLOCKED_SOURCE_EXCLUDED")
    return list(dict.fromkeys(reasons))


def _selection_from_candidate(candidate: RecallCandidate, reason_codes: Optional[List[str]] = None) -> RecallSelection:
    source_kind = trusted_recall_source_kind(candidate.source_ref, candidate.source_kind)
    rank = recall_source_priority_rank(source_kind)
    return RecallSelection(
        candidate_ref=candidate.candidate_ref,
        source_ref=candidate.source_ref,
        source_kind=source_kind,
        safe_summary=candidate.safe_summary,
        priority_rank=rank,
        token_estimate=candidate.token_estimate or _estimate_tokens(candidate.safe_summary),
        reason_codes=reason_codes or [],
        evidence_refs=candidate.evidence_refs,
        event_refs=candidate.event_refs,
        receipt_refs=candidate.receipt_refs,
        memory_refs=candidate.memory_refs,
        file_refs=candidate.file_refs,
        source_priority_summary=f"{source_kind.value} priority rank {rank}",
        metadata_refs=candidate.metadata_refs,
        metadata=candidate.metadata,
    )


def _cap_selected_by_budget(
    selected: List[RecallSelection],
    max_candidates: int,
    max_context_tokens: int,
) -> List[RecallSelection]:
    capped: List[RecallSelection] = []
    used = 0
    for item in selected:
        if len(capped) >= max_candidates:
            break
        if used + item.token_estimate > max_context_tokens:
            continue
        used += item.token_estimate
        capped.append(item)
    return capped


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))
