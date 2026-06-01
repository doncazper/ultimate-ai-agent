from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.memory.enums import MemoryAuthority, MemoryScope, MemorySensitivity, MemoryType
from ultimate_ai_agent.core.memory.records import MemorySourceRef


class MemoryWriteRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    memory_type: MemoryType
    scope: MemoryScope
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_refs: List[MemorySourceRef] = Field(default_factory=list)
    authority: MemoryAuthority
    sensitivity: MemorySensitivity
    consent_ref: Optional[str] = None
    event_ref: Optional[str] = None
    idempotency_key: Optional[str] = None
    proposed_supersedes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryReadRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    query: str = Field(default="")
    scope: MemoryScope
    scope_id: Optional[str] = None
    memory_types: List[MemoryType] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=0, le=50)
    include_superseded: bool = False
    consent_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
