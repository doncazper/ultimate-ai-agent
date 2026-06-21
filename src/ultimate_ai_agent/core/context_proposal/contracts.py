from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.context_proposal.enums import SafeContextProposalDecisionStatus


class SafeContextProposalPolicy(BaseModel):
    context_proposal_enabled: bool = True
    proposal_only_enabled: bool = True
    context_surface_enabled: bool = False
    context_handoff_enabled: bool = False
    context_injection_enabled: bool = False
    openwebui_handoff_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    raw_file_access_enabled: bool = False
    raw_content_enabled: bool = False
    full_file_read_enabled: bool = False
    unredacted_preview_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_surface_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        if not self.context_proposal_enabled:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_DISABLED")
        if not self.proposal_only_enabled:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_ONLY_REQUIRED")
        for field_name in _POLICY_BLOCKED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(_POLICY_BLOCKED_FLAGS[field_name])
        return self


class SafeContextProposalSource(BaseModel):
    approval_ref: str
    approval_record_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    actor_ref: str
    source_chain_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_source(self) -> Any:
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.approval_record_ref, "approval_record_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            validate_action_ref(value, field_name)
        for ref in self.source_chain_refs:
            validate_action_ref(ref, "source_chain_ref")
        return self


class SafeContextProposalBinding(BaseModel):
    approval_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    actor_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> Any:
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            validate_action_ref(value, field_name)
        return self


class SafeContextProposalRedactionVerification(BaseModel):
    verification_ref: str
    redaction_summary_ref: str
    redaction_performed: bool = True
    raw_content_removed: bool = True
    secret_like_content_removed: bool = True
    redaction_summary_required: bool = True
    redacted_review_material_only: bool = True
    no_raw_content_stored: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_redaction_verification(self) -> Any:
        validate_action_ref(self.verification_ref, "verification_ref")
        validate_action_ref(self.redaction_summary_ref, "redaction_summary_ref")
        for field_name in [
            "redaction_performed",
            "raw_content_removed",
            "secret_like_content_removed",
            "redaction_summary_required",
            "redacted_review_material_only",
            "no_raw_content_stored",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must be True in M38")
        return self


class SafeContextProposalSection(BaseModel):
    section_ref: str
    title: str
    content: str
    source_ref: str
    redacted: bool = True
    bounded: bool = True
    non_authoritative: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_section(self) -> Any:
        validate_action_ref(self.section_ref, "section_ref")
        validate_action_ref(self.source_ref, "source_ref")
        validate_safe_action_text(self.title, "title")
        validate_safe_action_text(_strip_redaction_markers(self.content), "content")
        if not self.redacted:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_SECTION_MUST_BE_REDACTED")
        if not self.bounded:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_SECTION_MUST_BE_BOUNDED")
        if not self.non_authoritative:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_SECTION_MUST_BE_NON_AUTHORITATIVE")
        return self


class SafeContextProposal(BaseModel):
    proposal_ref: str
    status: SafeContextProposalDecisionStatus = SafeContextProposalDecisionStatus.proposal_ready
    source: SafeContextProposalSource
    binding: SafeContextProposalBinding
    redaction_verification: SafeContextProposalRedactionVerification
    sections: list[SafeContextProposalSection] = Field(default_factory=list)
    safe_summary: str
    non_authoritative: bool = True
    proposal_only: bool = True
    no_context_injection: bool = True
    context_surface_enabled: bool = False
    context_handoff_enabled: bool = False
    context_injection_enabled: bool = False
    openwebui_handoff_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    raw_file_access_enabled: bool = False
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    truth_authority_claimed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> Any:
        validate_action_ref(self.proposal_ref, "proposal_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        if not self.non_authoritative:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_MUST_BE_NON_AUTHORITATIVE")
        if not self.proposal_only:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_MUST_BE_PROPOSAL_ONLY")
        if not self.no_context_injection:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_NO_CONTEXT_INJECTION_REQUIRED")
        for field_name in _PROPOSAL_BLOCKED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(_PROPOSAL_BLOCKED_FLAGS[field_name])
        if not self.sections:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_SECTION_REQUIRED")
        return self


class SafeContextProposalRequest(BaseModel):
    request_ref: str = "safe-context-proposal-request:m38"
    actor_ref: str
    review_packet_ref: str
    approval_ref: str | None = None
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.review_packet_ref, "review_packet_ref"),
        ]:
            validate_action_ref(value, field_name)
        if self.approval_ref:
            validate_action_ref(self.approval_ref, "approval_ref")
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class SafeContextProposalReceiptPlan(BaseModel):
    receipt_plan_ref: str
    proposal_ref: str
    approval_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    actor_ref: str
    receipt_is_authority: bool = False
    raw_content_stored: bool = False
    full_file_content_stored: bool = False
    unredacted_preview_stored: bool = False
    context_injection_performed: bool = False
    openwebui_handoff_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = "Non-authoritative M38 context proposal receipt plan stores safe refs only."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.proposal_ref, "proposal_ref"),
            (self.approval_ref, "approval_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            validate_action_ref(value, field_name)
        validate_safe_action_text(self.safe_summary, "safe_summary")
        for field_name in [
            "receipt_is_authority",
            "raw_content_stored",
            "full_file_content_stored",
            "unredacted_preview_stored",
            "context_injection_performed",
            "openwebui_handoff_performed",
            "model_call_performed",
            "memory_write_performed",
            "export_performed",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M38")
        return self


class SafeContextProposalDecision(BaseModel):
    decision_ref: str
    status: SafeContextProposalDecisionStatus
    proposal_ready: bool = False
    proposal_only: bool = True
    non_authoritative: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    proposal: SafeContextProposal | None = None
    receipt_plan: SafeContextProposalReceiptPlan | None = None
    context_surface_authorized: bool = False
    context_handoff_authorized: bool = False
    context_injection_authorized: bool = False
    openwebui_handoff_authorized: bool = False
    model_call_authorized: bool = False
    memory_write_authorized: bool = False
    export_authorized: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        validate_action_ref(self.decision_ref, "decision_ref")
        validate_safe_action_text(self.safe_message, "safe_message")
        if not self.proposal_only:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_DECISION_MUST_BE_PROPOSAL_ONLY")
        if not self.non_authoritative:
            raise ValueError("SAFE_CONTEXT_PROPOSAL_DECISION_MUST_BE_NON_AUTHORITATIVE")
        for field_name in [
            "context_surface_authorized",
            "context_handoff_authorized",
            "context_injection_authorized",
            "openwebui_handoff_authorized",
            "model_call_authorized",
            "memory_write_authorized",
            "export_authorized",
            "execution_authorized",
            "execution_performed",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M38")
        return self


def _strip_redaction_markers(value: str) -> str:
    return (
        value.replace("[REDACTED:SECRET_ASSIGNMENT]", "")
        .replace("[REDACTED:BEARER_TOKEN]", "")
        .replace("[REDACTED:PRIVATE_KEY_MARKER]", "")
        .replace("[REDACTED:HIGH_ENTROPY_TOKEN]", "")
        .replace("[REDACTED]", "")
        or "redacted"
    )


_POLICY_BLOCKED_FLAGS = {
    "context_surface_enabled": "SAFE_CONTEXT_SURFACE_DENIED",
    "context_handoff_enabled": "SAFE_CONTEXT_HANDOFF_DENIED",
    "context_injection_enabled": "SAFE_CONTEXT_INJECTION_DENIED",
    "openwebui_handoff_enabled": "SAFE_CONTEXT_OPENWEBUI_HANDOFF_DENIED",
    "model_call_enabled": "SAFE_CONTEXT_MODEL_CALL_DENIED",
    "memory_write_enabled": "SAFE_CONTEXT_MEMORY_WRITE_DENIED",
    "export_enabled": "SAFE_CONTEXT_EXPORT_DENIED",
    "execution_enabled": "SAFE_CONTEXT_EXECUTION_DENIED",
    "raw_file_access_enabled": "SAFE_CONTEXT_RAW_FILE_ACCESS_DENIED",
    "raw_content_enabled": "SAFE_CONTEXT_RAW_CONTENT_DENIED",
    "full_file_read_enabled": "SAFE_CONTEXT_FULL_FILE_READ_DENIED",
    "unredacted_preview_enabled": "SAFE_CONTEXT_UNREDACTED_PREVIEW_DENIED",
    "backend_route_enabled": "SAFE_CONTEXT_BACKEND_ROUTE_DENIED",
    "control_center_surface_enabled": "SAFE_CONTEXT_CONTROL_CENTER_SURFACE_DENIED",
    "production_authority_enabled": "SAFE_CONTEXT_PRODUCTION_AUTHORITY_DENIED",
}

_PROPOSAL_BLOCKED_FLAGS = {
    "context_surface_enabled": "SAFE_CONTEXT_SURFACE_DENIED",
    "context_handoff_enabled": "SAFE_CONTEXT_HANDOFF_DENIED",
    "context_injection_enabled": "SAFE_CONTEXT_INJECTION_DENIED",
    "openwebui_handoff_enabled": "SAFE_CONTEXT_OPENWEBUI_HANDOFF_DENIED",
    "model_call_enabled": "SAFE_CONTEXT_MODEL_CALL_DENIED",
    "memory_write_enabled": "SAFE_CONTEXT_MEMORY_WRITE_DENIED",
    "export_enabled": "SAFE_CONTEXT_EXPORT_DENIED",
    "execution_enabled": "SAFE_CONTEXT_EXECUTION_DENIED",
    "raw_file_access_enabled": "SAFE_CONTEXT_RAW_FILE_ACCESS_DENIED",
    "raw_content_stored": "SAFE_CONTEXT_RAW_CONTENT_DENIED",
    "full_file_content_stored": "SAFE_CONTEXT_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview_stored": "SAFE_CONTEXT_UNREDACTED_PREVIEW_DENIED",
    "truth_authority_claimed": "SAFE_CONTEXT_TRUTH_AUTHORITY_DENIED",
}
