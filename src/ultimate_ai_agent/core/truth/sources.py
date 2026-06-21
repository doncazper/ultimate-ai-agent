from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.enums import (
    TruthAuthorityLevel,
    TruthSourceKind,
    TruthSourcePriority,
    TruthSourceStatus,
    TruthSourceType,
)


AUTHORITY_RANK = {
    TruthAuthorityLevel.not_authority: 0,
    TruthAuthorityLevel.untrusted: 1,
    TruthAuthorityLevel.low: 2,
    TruthAuthorityLevel.medium: 3,
    TruthAuthorityLevel.high: 4,
    TruthAuthorityLevel.authoritative: 5,
}


SOURCE_TYPE_BASE_RANK = {
    TruthSourceType.model_output: 0,
    TruthSourceType.external_source: 1,
    TruthSourceType.memory: 2,
    TruthSourceType.user_instruction: 3,
    TruthSourceType.file: 3,
    TruthSourceType.world_state: 4,
    TruthSourceType.approved_document: 4,
    TruthSourceType.event_ledger: 4,
    TruthSourceType.provider_result: 5,
    TruthSourceType.api: 5,
    TruthSourceType.database: 5,
    TruthSourceType.canonical_file: 6,
}

SOURCE_PRIORITY_RANK = {
    TruthSourcePriority.canonical: 0,
    TruthSourcePriority.evidence: 1,
    TruthSourcePriority.receipt: 2,
    TruthSourcePriority.event: 3,
    TruthSourcePriority.user_reviewed: 4,
    TruthSourcePriority.source_linked_memory: 5,
    TruthSourcePriority.reviewed_memory: 6,
    TruthSourcePriority.unreviewed_memory: 7,
    TruthSourcePriority.model_output_blocked: 98,
    TruthSourcePriority.blocked: 99,
}


class TruthSourceManifest(BaseModel):
    source_id: str = Field(..., min_length=1)
    source_type: TruthSourceType
    authority_level: TruthAuthorityLevel
    display_name: str = Field(..., min_length=1)
    source_uri: Optional[str] = None
    owner: str = Field(..., min_length=1)
    allowed_scopes: List[str] = Field(default_factory=list)
    allowed_purposes: List[str] = Field(default_factory=list)
    data_classification: str
    freshness_policy: Optional[str] = None
    access_requires_consent: bool = False
    consent_ref: Optional[str] = None
    provider_id: Optional[str] = None
    file_ref: Optional[str] = None
    memory_ref: Optional[str] = None
    event_ref: Optional[str] = None
    canonical_priority: Optional[int] = None
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_authority(self) -> Any:
        if self.source_type == TruthSourceType.model_output and self.authority_level != TruthAuthorityLevel.not_authority:
            raise ValueError("model_output cannot be authoritative evidence.")
        if self.source_type == TruthSourceType.memory and self.authority_level == TruthAuthorityLevel.authoritative:
            raise ValueError("memory cannot be authoritative; it is supporting recall.")
        if self.data_classification == "credential_secret":
            raise ValueError("credential_secret sources are not valid user-visible evidence.")
        return self

    @property
    def authority_rank(self) -> int:
        return min(AUTHORITY_RANK[self.authority_level], SOURCE_TYPE_BASE_RANK[self.source_type])


def is_source_selectable(source: TruthSourceManifest, consent_refs: List[str]) -> bool:
    if source.data_classification == "credential_secret":
        return False
    if source.access_requires_consent:
        return bool(source.consent_ref and source.consent_ref in consent_refs)
    return True


class TruthSourceRef(BaseModel):
    source_ref: str = Field(..., min_length=1)
    source_kind: TruthSourceKind
    source_priority: TruthSourcePriority
    source_status: TruthSourceStatus
    safe_label: str = Field(..., min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    user_review_ref: Optional[str] = None
    canonical_refs: List[str] = Field(default_factory=list)
    authority_level: str = "non_authoritative"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m25_source_ref(self) -> Any:
        from ultimate_ai_agent.core.truth.validation import (
            assert_no_raw_truth_content,
            validate_structured_truth_ref,
        )

        validate_structured_truth_ref(self.source_ref, "source_ref")
        assert_no_raw_truth_content(self.safe_label)
        assert_no_raw_truth_content(self.metadata)
        if self.source_kind in {
            TruthSourceKind.source_linked_memory,
            TruthSourceKind.reviewed_memory,
            TruthSourceKind.unreviewed_memory,
        } and self.authority_level in {"authoritative", "authority"}:
            raise ValueError("Memory cannot be authoritative; it is recall only.")
        return self


def rank_truth_sources(sources: List[TruthSourceRef]) -> List[TruthSourceRef]:
    return sorted(
        sources,
        key=lambda source: (
            SOURCE_PRIORITY_RANK.get(source.source_priority, 100),
            source.source_ref,
        ),
    )
