from abc import ABC, abstractmethod
from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.memory.decisions import MemoryExportDecision, MemoryWriteDecision
from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryEpistemicRole,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
    MemoryWriteDecisionStatus,
    MemoryWriteDisposition,
)
from ultimate_ai_agent.core.time import utc_now


class MemoryProviderWriteRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    memory_kind: MemoryRecordKind
    memory_layer: MemoryLayer = MemoryLayer.record
    epistemic_role: MemoryEpistemicRole = MemoryEpistemicRole.unknown
    provider_kind: MemoryProviderKind = MemoryProviderKind.local_in_memory
    safe_summary: str = Field(..., min_length=1, max_length=4000)
    source_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    user_reviewed: bool = False
    model_output_source: bool = False
    local_llm_output_source: bool = False
    openwebui_source: bool = False
    mobile_capture_source: bool = False
    tool_output_source: bool = False
    automatic_write: bool = False
    contains_secret_like_content: bool = False
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    data_classification: MemoryDataClassification = MemoryDataClassification.internal
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    trust_score: float = Field(default=1.0, ge=0.0, le=1.0)
    dedup_key: Optional[str] = None
    context_pack_eligible: bool = False
    injection_priority: int = Field(default=0, ge=0, le=10)
    tags: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


MemoryWriteRequest = MemoryProviderWriteRequest


class MemoryDeleteRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    memory_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    user_requested: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class MemoryExportRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    include_deleted: bool = False
    include_raw_content: bool = False
    redacted_only: bool = True
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


def build_memory_write_decision(
    request_id: str,
    allowed: bool,
    status: MemoryWriteDecisionStatus,
    reason_codes: List[str],
    safe_message: str,
    memory_id: Optional[str] = None,
    required_next_action: Optional[str] = None,
) -> MemoryWriteDecision:
    return MemoryWriteDecision(
        decision_id=f"mwd_{uuid.uuid4().hex[:8]}",
        request_id=request_id,
        disposition=MemoryWriteDisposition.retain if allowed else MemoryWriteDisposition.reject,
        allowed=allowed,
        status=status,
        reason_codes=reason_codes,
        safe_message=safe_message,
        memory_id=memory_id,
        required_next_action=required_next_action,
    )


def build_memory_export_decision(
    request_id: str,
    allowed: bool,
    status: MemoryWriteDecisionStatus,
    reason_codes: List[str],
    safe_message: str,
    records: Optional[List[Dict[str, Any]]] = None,
) -> MemoryExportDecision:
    return MemoryExportDecision(
        decision_id=f"med_{uuid.uuid4().hex[:8]}",
        request_id=request_id,
        allowed=allowed,
        status=status,
        reason_codes=reason_codes,
        safe_message=safe_message,
        records=records or [],
        redactions_applied=["raw_content_omitted"] if allowed else [],
    )


class MemoryProvider(ABC):
    """Governed local memory provider contract for reviewed recall records only."""

    @abstractmethod
    def put_record(self, request: MemoryWriteRequest) -> MemoryWriteDecision:
        raise NotImplementedError

    @abstractmethod
    def get_record(self, memory_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_records(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_deleted(self, request: MemoryDeleteRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def export_records(self, request: MemoryExportRequest) -> MemoryExportDecision:
        raise NotImplementedError
