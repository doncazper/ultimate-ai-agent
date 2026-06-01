from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.enums import ClaimVerificationStatus, SourceFreshnessStatus


class ClaimEvidence(BaseModel):
    claim_id: str
    claim_text: str
    verification_status: ClaimVerificationStatus
    evidence_refs: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_status: SourceFreshnessStatus = SourceFreshnessStatus.unknown
    checked_at: datetime = Field(default_factory=datetime.utcnow)
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
