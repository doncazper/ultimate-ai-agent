from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import ApprovalRiskLevel
from ultimate_ai_agent.core.files.enums import FileKind, FileOperation, FileOperationStatus, FileSensitivity
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.time import utc_now


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


class FileTreePreviewRequest(BaseModel):
    request_id: str
    run_id: str
    actor_context: ActorContext
    root_path: Optional[str] = None
    purpose: str
    max_depth: int = Field(default=1, ge=0, le=5)
    max_entries: int = Field(default=100, ge=1, le=500)
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FileTreeEntry(BaseModel):
    entry_ref: str
    parent_ref: Optional[str] = None
    entry_type: Literal["directory", "file"]
    safe_label: str
    kind: FileKind
    sensitivity: FileSensitivity
    size_bytes: int = Field(default=0, ge=0)
    child_count: int = Field(default=0, ge=0)
    preview_available: bool = False
    redactions_applied: List[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FileTreePreview(BaseModel):
    preview_id: str
    root_ref: str
    entries: List[FileTreeEntry] = Field(default_factory=list)
    max_depth: int = Field(ge=0)
    max_entries: int = Field(ge=1)
    truncated: bool = False
    blocked_entry_count: int = Field(default=0, ge=0)
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FilePatchProposal(BaseModel):
    proposal_id: str
    run_id: str
    actor_context: ActorContext
    file_ref: str
    target_path: str
    purpose: str
    new_content: str
    expected_existing_hash: str
    file_kind: FileKind
    sensitivity: FileSensitivity
    risk_class: ApprovalRiskLevel = ApprovalRiskLevel.medium
    idempotency_key: str
    audit_ref: str
    approval_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FilePatchProposalDecision(BaseModel):
    decision_id: str
    proposal_id: str
    allowed: bool
    status: FileOperationStatus
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    file_ref: str
    target_ref: str
    expected_existing_hash: str
    preview_ref: Optional[str] = None
    preview_summary: Optional[str] = None
    risk_class: ApprovalRiskLevel
    rollback_plan_ref: Optional[str] = None
    idempotency_key: str
    audit_ref: str
    approval_ref: Optional[str] = None
    expires_at: Optional[datetime] = None
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FilePatchMutationReceipt(BaseModel):
    receipt_ref: str
    proposal_id: str
    status: FileOperationStatus
    file_ref: str
    target_ref: str
    preimage_ref: Optional[str] = None
    postimage_ref: Optional[str] = None
    rollback_ref: Optional[str] = None
    idempotency_key: str
    audit_ref: str
    approval_ref: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    mutation_performed: bool = False
    raw_content_stored: bool = False
    raw_path_stored: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    redactions_applied: List[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FilePatchApplyResult(BaseModel):
    change_id: str
    proposal_id: str
    status: FileOperationStatus
    allowed: bool
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    file_ref: str
    target_ref: str
    before_hash: Optional[str] = None
    after_hash: Optional[str] = None
    rollback_ref: Optional[str] = None
    receipt_ref: Optional[str] = None
    preimage_ref: Optional[str] = None
    postimage_ref: Optional[str] = None
    idempotency_key: str
    audit_ref: str
    approval_ref: Optional[str] = None
    applied_at: Optional[datetime] = None
    redactions_applied: List[str] = Field(default_factory=list)
    receipt: Optional[FilePatchMutationReceipt] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FilePatchRollbackReceipt(BaseModel):
    receipt_ref: str
    rollback_ref: str
    status: FileOperationStatus
    target_ref: str
    preimage_ref: Optional[str] = None
    restored_image_ref: Optional[str] = None
    idempotency_key: str
    audit_ref: str
    approval_ref: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    rollback_performed: bool = False
    raw_content_stored: bool = False
    raw_path_stored: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    redactions_applied: List[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


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
