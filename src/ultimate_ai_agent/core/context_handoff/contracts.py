from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.context_handoff.enums import (
    ContextHandoffApprovalDecisionStatus,
    ContextHandoffApprovalKind,
)
from ultimate_ai_agent.core.time import utc_now


class ContextHandoffApprovalPolicy(BaseModel):
    context_handoff_approval_enabled: bool = True
    exact_proposal_binding_required: bool = True
    no_injection_required: bool = True
    context_handoff_execution_enabled: bool = False
    context_injection_enabled: bool = False
    openwebui_handoff_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    raw_file_access_enabled: bool = False
    raw_content_enabled: bool = False
    full_file_read_enabled: bool = False
    unredacted_preview_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_mutation_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        if not self.context_handoff_approval_enabled:
            raise ValueError("CONTEXT_HANDOFF_APPROVAL_DISABLED")
        if not self.exact_proposal_binding_required:
            raise ValueError("CONTEXT_HANDOFF_EXACT_PROPOSAL_BINDING_REQUIRED")
        if not self.no_injection_required:
            raise ValueError("CONTEXT_HANDOFF_NO_INJECTION_REQUIRED")
        for field_name, reason in _POLICY_BLOCKED_FLAGS.items():
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class ContextHandoffApprovalRequest(BaseModel):
    approval_ref: str
    actor_ref: str
    proposal_ref: str
    approval_record_ref: str
    review_packet_ref: str
    preview_result_ref: str
    redaction_summary_ref: str
    file_ref: str
    safe_path_ref: str
    decision: ContextHandoffApprovalKind
    idempotency_key: str
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    replay_nonce: str | None = None
    used_replay_nonces: list[str] = Field(default_factory=list)
    safe_reason: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    context_handoff_execution_enabled: bool = False
    context_injection_enabled: bool = False
    openwebui_handoff_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    export_enabled: bool = False
    execution_enabled: bool = False
    raw_file_access_enabled: bool = False
    raw_content_enabled: bool = False
    full_file_read_enabled: bool = False
    unredacted_preview_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_mutation_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.proposal_ref, "proposal_ref"),
            (self.approval_record_ref, "approval_record_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.idempotency_key, "idempotency_key"),
        ]:
            validate_action_ref(value, field_name)
        if self.replay_nonce:
            validate_action_ref(self.replay_nonce, "replay_nonce")
        for nonce in self.used_replay_nonces:
            validate_action_ref(nonce, "used_replay_nonce")
        for ref in self.metadata_refs:
            validate_action_ref(ref, "metadata_ref")
        if self.safe_reason:
            validate_safe_action_text(self.safe_reason, "safe_reason")
        validate_safe_action_payload(self.metadata, "metadata")
        for field_name, reason in _REQUEST_BLOCKED_FLAGS.items():
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class ContextHandoffApprovalReceiptPlan(BaseModel):
    receipt_plan_ref: str
    approval_ref: str
    proposal_ref: str
    approval_record_ref: str
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
    raw_absolute_path_stored: bool = False
    context_injection_performed: bool = False
    openwebui_handoff_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False
    safe_summary: str = "M40 handoff approval receipt stores safe refs only and performs no injection."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.approval_ref, "approval_ref"),
            (self.proposal_ref, "proposal_ref"),
            (self.approval_record_ref, "approval_record_ref"),
            (self.review_packet_ref, "review_packet_ref"),
            (self.preview_result_ref, "preview_result_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
            (self.file_ref, "file_ref"),
            (self.safe_path_ref, "safe_path_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            validate_action_ref(value, field_name)
        validate_safe_action_text(self.safe_summary, "safe_summary")
        for field_name in _RECEIPT_FALSE_FIELDS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M40")
        return self


class ContextHandoffApprovalDecision(BaseModel):
    decision_ref: str
    status: ContextHandoffApprovalDecisionStatus
    approval_ref: str | None = None
    proposal_ref: str | None = None
    handoff_approved_for_review: bool = False
    review_only: bool = True
    no_injection: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str
    receipt_plan: ContextHandoffApprovalReceiptPlan | None = None
    handoff_execution_authorized: bool = False
    context_injection_authorized: bool = False
    openwebui_handoff_authorized: bool = False
    model_call_authorized: bool = False
    memory_write_authorized: bool = False
    export_authorized: bool = False
    execution_authorized: bool = False
    context_injection_performed: bool = False
    openwebui_handoff_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    export_performed: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        validate_action_ref(self.decision_ref, "decision_ref")
        if self.approval_ref:
            validate_action_ref(self.approval_ref, "approval_ref")
        if self.proposal_ref:
            validate_action_ref(self.proposal_ref, "proposal_ref")
        validate_safe_action_text(self.safe_message, "safe_message")
        if not self.review_only:
            raise ValueError("CONTEXT_HANDOFF_DECISION_MUST_BE_REVIEW_ONLY")
        if not self.no_injection:
            raise ValueError("CONTEXT_HANDOFF_DECISION_NO_INJECTION_REQUIRED")
        for field_name in _DECISION_FALSE_FIELDS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M40")
        return self


_POLICY_BLOCKED_FLAGS = {
    "context_handoff_execution_enabled": "CONTEXT_HANDOFF_EXECUTION_DENIED",
    "context_injection_enabled": "CONTEXT_HANDOFF_INJECTION_DENIED",
    "openwebui_handoff_execution_enabled": "CONTEXT_HANDOFF_OPENWEBUI_DENIED",
    "model_call_enabled": "CONTEXT_HANDOFF_MODEL_CALL_DENIED",
    "memory_write_enabled": "CONTEXT_HANDOFF_MEMORY_WRITE_DENIED",
    "export_enabled": "CONTEXT_HANDOFF_EXPORT_DENIED",
    "execution_enabled": "CONTEXT_HANDOFF_EXECUTION_DENIED",
    "raw_file_access_enabled": "CONTEXT_HANDOFF_RAW_FILE_ACCESS_DENIED",
    "raw_content_enabled": "CONTEXT_HANDOFF_RAW_CONTENT_DENIED",
    "full_file_read_enabled": "CONTEXT_HANDOFF_FULL_FILE_DENIED",
    "unredacted_preview_enabled": "CONTEXT_HANDOFF_UNREDACTED_PREVIEW_DENIED",
    "backend_route_enabled": "CONTEXT_HANDOFF_BACKEND_ROUTE_DENIED",
    "control_center_mutation_enabled": "CONTEXT_HANDOFF_CONTROL_CENTER_MUTATION_DENIED",
    "production_authority_enabled": "CONTEXT_HANDOFF_PRODUCTION_AUTHORITY_DENIED",
}

_REQUEST_BLOCKED_FLAGS = _POLICY_BLOCKED_FLAGS

_RECEIPT_FALSE_FIELDS = [
    "receipt_is_authority",
    "raw_content_stored",
    "full_file_content_stored",
    "unredacted_preview_stored",
    "raw_absolute_path_stored",
    "context_injection_performed",
    "openwebui_handoff_performed",
    "model_call_performed",
    "memory_write_performed",
    "export_performed",
    "execution_performed",
]

_DECISION_FALSE_FIELDS = [
    "handoff_execution_authorized",
    "context_injection_authorized",
    "openwebui_handoff_authorized",
    "model_call_authorized",
    "memory_write_authorized",
    "export_authorized",
    "execution_authorized",
    "context_injection_performed",
    "openwebui_handoff_performed",
    "model_call_performed",
    "memory_write_performed",
    "export_performed",
    "execution_performed",
]
