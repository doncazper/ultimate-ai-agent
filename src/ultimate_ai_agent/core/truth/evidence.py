from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.conflicts import SourceConflictReport
from ultimate_ai_agent.core.truth.enums import (
    EvidenceStrength,
    SourceFreshnessStatus,
    SourceRevocation,
    SourceStaleness,
    TruthSourceKind,
    TruthSourceType,
)


class EvidenceItem(BaseModel):
    evidence_id: str
    source_id: str
    source_type: TruthSourceType
    locator: Optional[str] = None
    quote: Optional[str] = Field(None, max_length=280)
    summary: str = Field(..., min_length=1)
    retrieved_at: datetime = Field(default_factory=utc_now)
    observed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    freshness_status: SourceFreshnessStatus = SourceFreshnessStatus.unknown
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    permission_ref: Optional[str] = None
    event_ref: Optional[str] = None
    file_ref: Optional[str] = None
    memory_ref: Optional[str] = None
    provider_result_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_locator_or_summary(self) -> Any:
        if not self.locator and not self.summary:
            raise ValueError("Evidence item requires locator or summary.")
        return self


class EvidenceManifest(BaseModel):
    manifest_id: str
    run_id: str
    answer_id: Optional[str] = None
    claims: List[ClaimEvidence] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    conflicts: List[SourceConflictReport] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)
    trace_id: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class EvidenceRef(BaseModel):
    evidence_ref: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    source_kind: TruthSourceKind
    evidence_strength: EvidenceStrength
    data_classification: str = "public"
    redaction_status: str = "redacted"
    safe_summary: str = Field(..., min_length=1)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m25_evidence_ref(self) -> Any:
        from ultimate_ai_agent.core.truth.validation import (
            assert_no_raw_truth_content,
            validate_structured_truth_ref,
        )

        validate_structured_truth_ref(self.evidence_ref, "evidence_ref")
        validate_structured_truth_ref(self.source_ref, "source_ref")
        assert_no_raw_truth_content(self.safe_summary)
        assert_no_raw_truth_content(self.metadata)
        return self


class EvidenceChain(BaseModel):
    chain_id: str = Field(..., min_length=1)
    claim_ref: str = Field(..., min_length=1)
    source_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    evidence_strength: EvidenceStrength = EvidenceStrength.none
    source_priority_summary: str = Field(..., min_length=1)
    conflict_refs: List[str] = Field(default_factory=list)
    stale_refs: List[str] = Field(default_factory=list)
    revoked_refs: List[str] = Field(default_factory=list)
    source_staleness: SourceStaleness = SourceStaleness.current
    source_revocation: SourceRevocation = SourceRevocation.active
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m25_evidence_chain(self) -> Any:
        from ultimate_ai_agent.core.truth.validation import assert_claim_not_self_verified, assert_no_raw_truth_content

        assert_claim_not_self_verified(self)
        assert_no_raw_truth_content(self.safe_summary)
        assert_no_raw_truth_content(self.source_priority_summary)
        assert_no_raw_truth_content(self.metadata)
        return self
