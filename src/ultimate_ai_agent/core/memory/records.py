from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthority,
    MemoryScope,
    MemorySensitivity,
    MemoryStatus,
    MemoryType,
)


class MemorySourceRef(BaseModel):
    source_id: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    source_uri: Optional[str] = None
    event_ref: Optional[str] = None
    file_ref: Optional[str] = None
    evidence_ref: Optional[str] = None
    locator: Optional[str] = None
    observed_at: Optional[datetime] = None
    trust_level: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class MemoryRecord(BaseModel):
    memory_id: str = Field(..., min_length=1)
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    status: MemoryStatus = MemoryStatus.active
    authority: MemoryAuthority
    sensitivity: MemorySensitivity
    content: str = Field(..., min_length=1, max_length=4000)
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_refs: List[MemorySourceRef] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    supersedes: List[str] = Field(default_factory=list)
    superseded_by: Optional[str] = None
    correction_of: Optional[str] = None
    deletion_ref: Optional[str] = None
    event_ref: Optional[str] = None
    provenance_note: Optional[str] = "Memory is recall, not authority; canonical sources outrank memory."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def require_source_for_non_user_memory(self):
        if self.authority != MemoryAuthority.user_provided and not self.source_refs:
            raise ValueError("source_refs are required unless authority is user_provided")
        return self
