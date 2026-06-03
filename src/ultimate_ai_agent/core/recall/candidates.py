from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.recall.enums import RecallCandidateStatus, RecallSourceKind
from ultimate_ai_agent.core.recall.policy import recall_source_identity_reason_codes
from ultimate_ai_agent.core.recall.validation import (
    validate_recall_ref,
    validate_safe_recall_payload,
    validate_safe_recall_text,
)


class RecallCandidate(BaseModel):
    candidate_ref: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    source_kind: RecallSourceKind
    safe_summary: str = Field(..., min_length=1)
    status: RecallCandidateStatus = RecallCandidateStatus.active
    reviewed: bool = False
    data_classification: str = "internal"
    redaction_status: str = "redacted_summary_only"
    token_estimate: int = Field(default=0, ge=0, le=20000)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_candidate(self):
        validate_recall_ref(self.candidate_ref, "candidate_ref")
        validate_recall_ref(self.source_ref, "source_ref")
        validate_safe_recall_text(self.safe_summary, "safe_summary")
        validate_safe_recall_payload(self.metadata_refs, "metadata_refs")
        validate_safe_recall_payload(self.metadata)
        for field_name in ["evidence_refs", "event_refs", "receipt_refs", "memory_refs", "file_refs"]:
            validate_safe_recall_payload(getattr(self, field_name), field_name)
        return self

    def source_identity_reason_codes(self) -> List[str]:
        return recall_source_identity_reason_codes(self.source_ref, self.source_kind)
