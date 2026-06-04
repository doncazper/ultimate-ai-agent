from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.file_review.enums import FileReviewDecisionStatus, FileReviewPacketStatus
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime.file_preview import RedactedFilePreviewOutput


class FileReviewWorkflowPolicy(BaseModel):
    file_review_workflow_enabled: bool = True
    review_packet_enabled: bool = True
    user_approval_gate_enabled: bool = True
    redaction_verification_required: bool = True
    exact_approval_binding_required: bool = True
    raw_file_access_enabled: bool = False
    raw_content_enabled: bool = False
    full_file_read_enabled: bool = False
    unredacted_preview_enabled: bool = False
    context_proposal_enabled: bool = False
    context_injection_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    control_center_surface_enabled: bool = False
    backend_routes_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self):
        required_enabled = [
            "file_review_workflow_enabled",
            "review_packet_enabled",
            "user_approval_gate_enabled",
            "redaction_verification_required",
            "exact_approval_binding_required",
        ]
        for field_name in required_enabled:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must be True in M35")
        blocked_fields = {
            "raw_file_access_enabled": "FILE_REVIEW_RAW_FILE_ACCESS_DENIED",
            "raw_content_enabled": "FILE_REVIEW_RAW_CONTENT_DENIED",
            "full_file_read_enabled": "FILE_REVIEW_FULL_FILE_READ_DENIED",
            "unredacted_preview_enabled": "FILE_REVIEW_UNREDACTED_PREVIEW_DENIED",
            "context_proposal_enabled": "FILE_REVIEW_CONTEXT_PROPOSAL_DENIED",
            "context_injection_enabled": "FILE_REVIEW_CONTEXT_INJECTION_DENIED",
            "memory_write_enabled": "FILE_REVIEW_MEMORY_WRITE_DENIED",
            "export_enabled": "FILE_REVIEW_EXPORT_DENIED",
            "execution_enabled": "FILE_REVIEW_EXECUTION_DENIED",
            "approval_capture_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_DENIED",
            "approval_persistence_enabled": "FILE_REVIEW_APPROVAL_PERSISTENCE_DENIED",
            "control_center_surface_enabled": "FILE_REVIEW_CONTROL_CENTER_SURFACE_DENIED",
            "backend_routes_enabled": "FILE_REVIEW_BACKEND_ROUTES_DENIED",
            "production_authority_enabled": "FILE_REVIEW_PRODUCTION_AUTHORITY_DENIED",
        }
        for field_name, reason in blocked_fields.items():
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class FileReviewPacketSource(BaseModel):
    preview_result_ref: str = Field(..., min_length=1)
    safe_path_ref: str = Field(..., min_length=1)
    root_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    file_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_source(self):
        for value, field_name in [
            (self.preview_result_ref, "preview_result_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.root_ref, "root_ref"),
            (self.actor_ref, "actor_ref"),
            (self.request_ref, "request_ref"),
        ]:
            validate_action_ref(value, field_name)
        if self.file_ref:
            validate_action_ref(self.file_ref, "file_ref")
        return self


class FileReviewRedactionVerification(BaseModel):
    verification_ref: str = "file-review-redaction-verification:m35"
    redaction_summary_ref: str
    redaction_performed: bool = True
    raw_content_removed: bool = True
    secret_like_content_removed: bool = True
    redaction_summary_required: bool = True
    redaction_summary_contains_sensitive_values: bool = False
    redacted_preview_only: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_verification(self):
        validate_action_ref(self.verification_ref, "verification_ref")
        validate_action_ref(self.redaction_summary_ref, "redaction_summary_ref")
        required_true = [
            "redaction_performed",
            "raw_content_removed",
            "secret_like_content_removed",
            "redaction_summary_required",
            "redacted_preview_only",
        ]
        for field_name in required_true:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must be True in M35")
        if self.redaction_summary_contains_sensitive_values:
            raise ValueError("FILE_REVIEW_REDACTION_SUMMARY_SECRET_VALUES_DENIED")
        return self


class FileReviewRequest(BaseModel):
    request_ref: str = "file-review-request:m35"
    actor_ref: str
    preview_result_ref: str
    safe_summary: str
    approval_ref: Optional[str] = None
    authority_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.preview_result_ref, "preview_result_ref"),
        ]:
            validate_action_ref(value, field_name)
        validate_safe_action_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_action_text(self.approval_ref, "approval_ref")
        for ref in [*self.authority_refs, *self.metadata_refs]:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class FileReviewPacket(BaseModel):
    review_packet_ref: str
    status: FileReviewPacketStatus = FileReviewPacketStatus.ready_for_review
    source: FileReviewPacketSource
    redaction_verification: FileReviewRedactionVerification
    redacted_preview: str
    safe_summary: str
    approval_ref: Optional[str] = None
    authority_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    raw_absolute_path_stored: bool = False
    context_proposal_enabled: bool = False
    context_injection_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    control_center_surface_enabled: bool = False
    backend_routes_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_packet(self):
        validate_action_ref(self.review_packet_ref, "review_packet_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        _validate_redacted_preview_text(self.redacted_preview)
        if self.approval_ref:
            validate_safe_action_text(self.approval_ref, "approval_ref")
        for ref in [*self.authority_refs, *self.metadata_refs]:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        blocked_fields = [
            "raw_content_stored",
            "full_file_content_stored",
            "unredacted_preview_stored",
            "raw_absolute_path_stored",
            "context_proposal_enabled",
            "context_injection_enabled",
            "memory_write_enabled",
            "export_enabled",
            "execution_enabled",
            "approval_capture_enabled",
            "approval_persistence_enabled",
            "control_center_surface_enabled",
            "backend_routes_enabled",
        ]
        for field_name in blocked_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M35")
        return self


class UserFileReviewApproval(BaseModel):
    approval_ref: str
    actor_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    replay_nonce: Optional[str] = None
    used_replay_nonces: List[str] = Field(default_factory=list)
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_approval(self):
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
        ]:
            validate_action_ref(value, field_name)
        if self.replay_nonce:
            validate_action_ref(self.replay_nonce, "replay_nonce")
        for nonce in self.used_replay_nonces:
            validate_action_ref(nonce, "used_replay_nonce")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        if self.approval_capture_enabled:
            raise ValueError("FILE_REVIEW_APPROVAL_CAPTURE_DENIED")
        if self.approval_persistence_enabled:
            raise ValueError("FILE_REVIEW_APPROVAL_PERSISTENCE_DENIED")
        return self


class FileReviewReceiptPlan(BaseModel):
    receipt_plan_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    approval_ref: Optional[str] = None
    receipt_is_authority: bool = False
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    raw_absolute_path_stored: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = "Non-authoritative M35 file review receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt_plan(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
        ]:
            validate_action_ref(value, field_name)
        if self.approval_ref:
            validate_action_ref(self.approval_ref, "approval_ref")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        blocked_fields = [
            "receipt_is_authority",
            "raw_content_stored",
            "full_file_content_stored",
            "unredacted_preview_stored",
            "raw_absolute_path_stored",
            "context_injection_performed",
            "memory_write_performed",
            "export_performed",
            "execution_performed",
        ]
        for field_name in blocked_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M35")
        return self


class FileReviewDecision(BaseModel):
    decision_ref: str
    review_packet_ref: str
    status: FileReviewDecisionStatus
    packet_valid_for_review: bool = False
    review_allowed: bool = False
    review_only: bool = True
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    raw_file_access_authorized: bool = False
    context_proposal_authorized: bool = False
    context_injection_authorized: bool = False
    memory_write_authorized: bool = False
    export_authorized: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    receipt_plan: Optional[FileReviewReceiptPlan] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self):
        validate_action_ref(self.decision_ref, "decision_ref")
        validate_action_ref(self.review_packet_ref, "review_packet_ref")
        validate_safe_action_text(self.safe_message, "safe_message")
        if not self.review_only:
            raise ValueError("FILE_REVIEW_MUST_BE_REVIEW_ONLY")
        blocked_fields = [
            "raw_file_access_authorized",
            "context_proposal_authorized",
            "context_injection_authorized",
            "memory_write_authorized",
            "export_authorized",
            "execution_authorized",
            "execution_performed",
        ]
        for field_name in blocked_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M35")
        return self


class FileReviewGate(BaseModel):
    gate_ref: str = "file-review-gate:m35"
    expected_actor_ref: str
    expected_review_packet_ref: str
    expected_preview_result_ref: str
    expected_redaction_summary_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_gate(self):
        for value, field_name in [
            (self.gate_ref, "gate_ref"),
            (self.expected_actor_ref, "expected_actor_ref"),
            (self.expected_review_packet_ref, "expected_review_packet_ref"),
            (self.expected_preview_result_ref, "expected_preview_result_ref"),
            (self.expected_redaction_summary_ref, "expected_redaction_summary_ref"),
        ]:
            validate_action_ref(value, field_name)
        return self


def _validate_redacted_preview_text(value: str) -> None:
    if not value or not value.strip():
        raise ValueError("FILE_REVIEW_REDACTED_PREVIEW_REQUIRED")
    preview_without_markers = (
        value.replace("[REDACTED:SECRET_ASSIGNMENT]", "")
        .replace("[REDACTED:BEARER_TOKEN]", "")
        .replace("[REDACTED:PRIVATE_KEY_MARKER]", "")
        .replace("[REDACTED:HIGH_ENTROPY_TOKEN]", "")
    )
    validate_safe_action_text(preview_without_markers or "redacted preview", "redacted_preview")


def file_review_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


def redaction_summary_ref_for_preview(preview_output: RedactedFilePreviewOutput) -> str:
    return f"file-review-redaction-summary:{file_review_suffix(preview_output.output_ref)}"
