from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.files.enums import FileKind, FileOperation, FileOperationStatus, FileSensitivity
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext


class FileReadRequest(BaseModel):
    request_id: str
    run_id: str
    actor_context: ActorContext
    file_ref: Optional[str] = None
    path: Optional[str] = None
    purpose: str
    max_bytes: int = Field(default=4096, ge=0)
    consent_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FileReadPreview(BaseModel):
    preview_id: str
    path: str
    size_bytes: int = Field(ge=0)
    content_hash: str
    text_preview: str
    redactions_applied: List[str] = Field(default_factory=list)
    truncated: bool = False
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FileWriteProposal(BaseModel):
    proposal_id: str
    run_id: str
    actor_context: ActorContext
    target_path: str
    purpose: str
    new_content: str
    expected_existing_hash: Optional[str] = None
    file_kind: FileKind
    sensitivity: FileSensitivity
    idempotency_key: Optional[str] = None
    approval_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FileWriteDecision(BaseModel):
    decision_id: str
    proposal_id: str
    allowed: bool
    status: FileOperationStatus
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    diff_ref: Optional[str] = None
    rollback_ref: Optional[str] = None
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FileChange(BaseModel):
    change_id: str
    target_path: str
    operation: FileOperation
    before_hash: Optional[str] = None
    after_hash: Optional[str] = None
    diff_summary: str
    applied_at: Optional[datetime] = None
    rollback_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
