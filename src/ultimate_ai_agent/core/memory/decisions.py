from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.memory.enums import MemorySensitivity, MemoryStatus, MemoryWriteDecisionStatus, MemoryWriteDisposition
from ultimate_ai_agent.core.memory.records import MemorySourceRef


class MemoryWriteDecision(BaseModel):
    decision_id: str
    request_id: str
    disposition: MemoryWriteDisposition
    allowed: bool
    status: Optional[MemoryWriteDecisionStatus] = None
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    required_next_action: Optional[str] = None
    memory_id: Optional[str] = None
    redactions_applied: List[str] = Field(default_factory=list)
    quarantine_ref: Optional[str] = None
    event_ref: Optional[str] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemorySearchResult(BaseModel):
    memory_id: str
    score: float
    match_reasons: List[str] = Field(default_factory=list)
    record_summary: str
    source_refs: List[MemorySourceRef] = Field(default_factory=list)
    sensitivity: MemorySensitivity
    status: MemoryStatus

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryReadDecision(BaseModel):
    decision_id: str
    request_id: str
    allowed: bool
    results: List[MemorySearchResult] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class MemoryExportDecision(BaseModel):
    decision_id: str
    request_id: str
    allowed: bool
    status: MemoryWriteDecisionStatus
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    records: List[Dict[str, Any]] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
