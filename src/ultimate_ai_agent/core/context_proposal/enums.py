from enum import Enum


class SafeContextProposalStatus(str, Enum):
    proposal_ready = "proposal_ready"
    requires_approved_review = "requires_approved_review"
    denied = "denied"
    blocked = "blocked"
    future_context_surface_required = "future_context_surface_required"
    future_handoff_approval_required = "future_handoff_approval_required"
    future_context_injection_required = "future_context_injection_required"


SafeContextProposalDecisionStatus = SafeContextProposalStatus


class SafeContextProposalBlockReason(str, Enum):
    missing_approved_review = "missing_approved_review"
    approval_not_review_only = "approval_not_review_only"
    approval_denied = "approval_denied"
    approval_ref_not_authority = "approval_ref_not_authority"
    approval_test_ref_denied = "approval_test_ref_denied"
    approval_record_mismatch = "approval_record_mismatch"
    review_packet_mismatch = "review_packet_mismatch"
    preview_result_mismatch = "preview_result_mismatch"
    redaction_summary_mismatch = "redaction_summary_mismatch"
    file_ref_mismatch = "file_ref_mismatch"
    path_ref_mismatch = "path_ref_mismatch"
    actor_ref_mismatch = "actor_ref_mismatch"
    raw_content_present = "raw_content_present"
    full_file_content_present = "full_file_content_present"
    unredacted_preview_present = "unredacted_preview_present"
    missing_redaction_summary = "missing_redaction_summary"
    unsafe_section_content = "unsafe_section_content"
    context_injection_denied = "context_injection_denied"
    memory_write_denied = "memory_write_denied"
    export_denied = "export_denied"
    execution_denied = "execution_denied"
    model_call_denied = "model_call_denied"
    openwebui_handoff_denied = "openwebui_handoff_denied"
    future_milestone_required = "future_milestone_required"
