from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthority,
    MemoryAuthorityLevel,
    MemoryConflictState,
    MemoryDataClassification,
    MemoryDecayState,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecallEligibility,
    MemoryRecordKind,
    MemoryRetentionState,
    MemoryReviewState,
    MemoryScope,
    MemorySensitivity,
    MemorySourcePriority,
    MemoryStatus,
    MemoryType,
)


class MemorySourceRef(BaseModel):
    source_id: Optional[str] = Field(default=None, min_length=1)
    source_type: Optional[str] = Field(default=None, min_length=1)
    source_ref: Optional[str] = Field(default=None, min_length=1)
    source_kind: Optional[str] = Field(default=None, min_length=1)
    source_priority: MemorySourcePriority = MemorySourcePriority.source_linked_memory
    source_uri: Optional[str] = None
    event_ref: Optional[str] = None
    event_refs: List[str] = Field(default_factory=list)
    file_ref: Optional[str] = None
    file_refs: List[str] = Field(default_factory=list)
    evidence_ref: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    user_review_ref: Optional[str] = None
    locator: Optional[str] = None
    observed_at: Optional[datetime] = None
    trust_level: Optional[str] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_legacy_or_m24_source_identity(self):
        if not ((self.source_id and self.source_type) or (self.source_ref and self.source_kind)):
            raise ValueError("source_id/source_type or source_ref/source_kind is required")
        return self


class MemoryProvenance(BaseModel):
    provenance_id: str = Field(..., min_length=1)
    source_refs: List[MemorySourceRef] = Field(default_factory=list)
    created_by_ref: Optional[str] = None
    reviewed_by_ref: Optional[str] = None
    review_state: MemoryReviewState = MemoryReviewState.user_review_required
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    source_priority: MemorySourcePriority = MemorySourcePriority.source_linked_memory
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryRecallMetadata(BaseModel):
    recall_id: str = Field(..., min_length=1)
    recall_eligibility: MemoryRecallEligibility = MemoryRecallEligibility.eligible_metadata_only
    context_pack_eligible: bool = False
    injection_priority: int = Field(default=0, ge=0, le=10)
    recall_budget_tokens: int = Field(default=0, ge=0, le=10000)
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_referenced_at: Optional[datetime] = None
    retrieval_hint: Optional[str] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryLifecycleMetadata(BaseModel):
    dedup_key: Optional[str] = None
    decay_state: MemoryDecayState = MemoryDecayState.none
    archive_candidate: bool = False
    retention_state: MemoryRetentionState = MemoryRetentionState.active
    superseded_by: Optional[str] = None
    conflict_state: MemoryConflictState = MemoryConflictState.none
    stale_state: MemoryConflictState = MemoryConflictState.none
    last_verified_at: Optional[datetime] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryRecord(BaseModel):
    memory_id: str = Field(..., min_length=1)
    memory_type: MemoryType = MemoryType.semantic
    memory_kind: MemoryRecordKind = MemoryRecordKind.structured_fact
    memory_layer: MemoryLayer = MemoryLayer.record
    provider_kind: MemoryProviderKind = MemoryProviderKind.local_in_memory
    review_state: MemoryReviewState = MemoryReviewState.user_review_required
    authority_level: MemoryAuthorityLevel = MemoryAuthorityLevel.recall_only
    source_priority: MemorySourcePriority = MemorySourcePriority.source_linked_memory
    data_classification: MemoryDataClassification = MemoryDataClassification.internal
    safe_summary: Optional[str] = None
    provenance: Optional[MemoryProvenance] = None
    scope: MemoryScope = MemoryScope.project
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    status: MemoryStatus = MemoryStatus.active
    authority: MemoryAuthority = MemoryAuthority.user_provided
    sensitivity: MemorySensitivity = MemorySensitivity.project_private
    content: str = Field(default="", max_length=4000)
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_refs: List[MemorySourceRef] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    trust_score: float = Field(default=1.0, ge=0.0, le=1.0)
    recall_metadata: Optional[MemoryRecallMetadata] = None
    lifecycle: Optional[MemoryLifecycleMetadata] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retention_state: MemoryRetentionState = MemoryRetentionState.active
    conflict_state: MemoryConflictState = MemoryConflictState.none
    stale_state: MemoryConflictState = MemoryConflictState.none
    supersedes: List[str] = Field(default_factory=list)
    superseded_by: Optional[str] = None
    correction_of: Optional[str] = None
    deletion_ref: Optional[str] = None
    event_ref: Optional[str] = None
    redaction_status: str = "redacted_summary_only"
    provenance_note: Optional[str] = "Memory is recall, not authority; canonical sources outrank memory."
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def require_source_for_non_user_memory(self):
        if self.authority != MemoryAuthority.user_provided and not self.source_refs:
            raise ValueError("source_refs are required unless authority is user_provided")
        if not self.content and not self.safe_summary:
            raise ValueError("content or safe_summary is required")
        return self
