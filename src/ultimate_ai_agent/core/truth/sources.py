from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.enums import TruthAuthorityLevel, TruthSourceType


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_authority(self):
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
