from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.conflicts import SourceConflictReport
from ultimate_ai_agent.core.truth.enums import SourceFreshnessStatus, TruthSourceType


class EvidenceItem(BaseModel):
    evidence_id: str
    source_id: str
    source_type: TruthSourceType
    locator: Optional[str] = None
    quote: Optional[str] = Field(None, max_length=280)
    summary: str = Field(..., min_length=1)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
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
    def validate_locator_or_summary(self):
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
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
