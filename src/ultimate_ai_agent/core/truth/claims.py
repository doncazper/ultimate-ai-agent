from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.enums import ClaimRiskLevel, ClaimStatus, ClaimVerificationStatus, SourceFreshnessStatus


class ClaimEvidence(BaseModel):
    claim_id: str
    claim_text: str
    verification_status: ClaimVerificationStatus
    evidence_refs: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_status: SourceFreshnessStatus = SourceFreshnessStatus.unknown
    checked_at: datetime = Field(default_factory=utc_now)
    unsupported_reason: Optional[str] = None
    conflict_report_ref: Optional[str] = None
    human_review_required: bool = False
    notes: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_status(self):
        if self.verification_status == ClaimVerificationStatus.supported and not self.evidence_refs:
            raise ValueError("supported claims require at least one evidence_ref.")
        if self.verification_status == ClaimVerificationStatus.unsupported and not self.unsupported_reason:
            raise ValueError("unsupported claims require unsupported_reason.")
        return self


class ClaimRef(BaseModel):
    claim_ref: str = Field(..., min_length=1)
    safe_claim_summary: str = Field(..., min_length=1)
    claim_type: str = "factual"
    data_classification: str = "public"
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_claim_ref(self):
        from ultimate_ai_agent.core.truth.validation import assert_no_raw_truth_content, validate_structured_truth_ref

        validate_structured_truth_ref(self.claim_ref, "claim_ref")
        assert_no_raw_truth_content(self.safe_claim_summary)
        assert_no_raw_truth_content(self.metadata)
        return self


class Claim(BaseModel):
    claim_id: str = Field(..., min_length=1)
    safe_claim_summary: str = Field(..., min_length=1)
    claim_text_hash: str = Field(..., min_length=1)
    claim_status: ClaimStatus = ClaimStatus.unverified
    claim_risk: ClaimRiskLevel = ClaimRiskLevel.low
    data_classification: str = "public"
    source_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    conflict_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_claim(self):
        from ultimate_ai_agent.core.truth.validation import assert_no_raw_truth_content

        assert_no_raw_truth_content(self.safe_claim_summary)
        assert_no_raw_truth_content(self.metadata)
        return self
