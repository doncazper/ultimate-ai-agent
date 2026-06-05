from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.context_proposal.contracts import (
    SafeContextProposal,
    SafeContextProposalPolicy,
)
from ultimate_ai_agent.core.file_review.approval_capture import FileReviewApprovalRecord
from ultimate_ai_agent.core.file_review.contracts import FileReviewPacket
from ultimate_ai_agent.core.file_review.enums import (
    FileReviewApprovalCaptureDecisionStatus,
    FileReviewApprovalDecisionKind,
)
from ultimate_ai_agent.core.file_review.workflow import evaluate_file_review_packet
from ultimate_ai_agent.core.time import utc_now


def validate_safe_context_proposal_request(
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord | None,
    approval_ref: str | None = None,
    policy: SafeContextProposalPolicy | None = None,
) -> list[str]:
    reasons = []
    reasons.extend(_policy_reasons(policy or SafeContextProposalPolicy()))
    reasons.extend(_packet_reasons(packet))
    reasons.extend(_authority_ref_reasons(getattr(packet, "authority_refs", [])))
    if approval_ref:
        reasons.append("approval_ref_not_authority")
        if str(approval_ref).startswith("approval_test_"):
            reasons.append("approval_test_ref_denied")
    if approval_record is None:
        reasons.append("missing_approved_review")
        return _dedupe(reasons)
    reasons.extend(validate_approved_review_for_context_proposal(packet=packet, approval_record=approval_record))
    return _dedupe(reasons)


def validate_approved_review_for_context_proposal(
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
    current_time: datetime | None = None,
) -> list[str]:
    reasons = []
    reasons.extend(_approval_record_reasons(approval_record, current_time=current_time))
    reasons.extend(validate_context_proposal_source_binding(packet=packet, approval_record=approval_record))
    return _dedupe(reasons)


def validate_context_proposal_source_binding(
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
) -> list[str]:
    checks = [
        (getattr(approval_record, "actor_ref", None), packet.source.actor_ref, "actor_ref_mismatch"),
        (getattr(approval_record, "review_packet_ref", None), packet.review_packet_ref, "review_packet_mismatch"),
        (getattr(approval_record, "preview_result_ref", None), packet.source.preview_result_ref, "preview_result_mismatch"),
        (
            getattr(approval_record, "redaction_summary_ref", None),
            packet.redaction_verification.redaction_summary_ref,
            "redaction_summary_mismatch",
        ),
        (getattr(approval_record, "file_ref", None), packet.source.file_ref, "file_ref_mismatch"),
        (getattr(approval_record, "safe_path_ref", None), packet.source.safe_path_ref, "path_ref_mismatch"),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def validate_safe_context_proposal(
    proposal: SafeContextProposal,
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
    policy: SafeContextProposalPolicy | None = None,
) -> list[str]:
    reasons = []
    reasons.extend(_policy_reasons(policy or SafeContextProposalPolicy()))
    reasons.extend(validate_safe_context_proposal_request(packet=packet, approval_record=approval_record, policy=policy))
    reasons.extend(_proposal_reasons(proposal))
    reasons.extend(_proposal_binding_reasons(proposal, packet=packet, approval_record=approval_record))
    return _dedupe(reasons)


def assert_context_proposal_no_raw_content(proposal: SafeContextProposal) -> None:
    reasons = _proposal_raw_reasons(proposal)
    if reasons:
        raise ValueError(",".join(reasons))


def assert_context_proposal_no_injection(proposal: SafeContextProposal) -> None:
    if bool(_extra_value(proposal, "context_injection_enabled", False)) or not bool(_extra_value(proposal, "no_context_injection", False)):
        raise ValueError("context_injection_denied")


def assert_context_proposal_no_memory_write(proposal: SafeContextProposal) -> None:
    if bool(_extra_value(proposal, "memory_write_enabled", False)):
        raise ValueError("memory_write_denied")


def assert_context_proposal_no_export(proposal: SafeContextProposal) -> None:
    if bool(_extra_value(proposal, "export_enabled", False)):
        raise ValueError("export_denied")


def assert_context_proposal_no_execution(proposal: SafeContextProposal) -> None:
    if bool(_extra_value(proposal, "execution_enabled", False)):
        raise ValueError("execution_denied")


def assert_context_proposal_no_model_call(proposal: SafeContextProposal) -> None:
    if bool(_extra_value(proposal, "model_call_enabled", False)):
        raise ValueError("model_call_denied")


def assert_context_proposal_revalidated(
    proposal: SafeContextProposal,
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
) -> None:
    reasons = validate_safe_context_proposal(proposal, packet=packet, approval_record=approval_record)
    if reasons:
        raise ValueError(",".join(reasons))


def _policy_reasons(policy: SafeContextProposalPolicy) -> list[str]:
    reasons = []
    if not bool(_extra_value(policy, "context_proposal_enabled", False)):
        reasons.append("future_milestone_required")
    if not bool(_extra_value(policy, "proposal_only_enabled", False)):
        reasons.append("future_milestone_required")
    for field_name, reason in _POLICY_REASON_BY_FIELD.items():
        if bool(_extra_value(policy, field_name, False)):
            reasons.append(reason)
    return _dedupe(reasons)


def _packet_reasons(packet: FileReviewPacket) -> list[str]:
    reasons = []
    file_review_decision = evaluate_file_review_packet(packet)
    for reason in file_review_decision.reason_codes:
        reasons.extend(_map_file_review_reason(reason))
    if getattr(packet, "redaction_verification", None) is None:
        reasons.append("missing_redaction_summary")
    else:
        verification = packet.redaction_verification
        if not bool(_extra_value(verification, "redaction_summary_required", False)):
            reasons.append("missing_redaction_summary")
        if not getattr(verification, "redaction_summary_ref", None):
            reasons.append("missing_redaction_summary")
    reasons.extend(_raw_extra_reasons(packet))
    reasons.extend(_validate_payload_reason(getattr(packet, "metadata", {}), "metadata", "unsafe_section_content"))
    return _dedupe(reasons)


def _approval_record_reasons(record: FileReviewApprovalRecord, *, current_time: datetime | None = None) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(record, "approval_ref", None), "approval_ref"),
        (getattr(record, "actor_ref", None), "actor_ref"),
        (getattr(record, "review_packet_ref", None), "review_packet_ref"),
        (getattr(record, "preview_result_ref", None), "preview_result_ref"),
        (getattr(record, "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(record, "file_ref", None), "file_ref"),
        (getattr(record, "safe_path_ref", None), "safe_path_ref"),
        (getattr(record, "idempotency_key", None), "idempotency_key"),
    ]:
        reasons.extend(_validate_required_ref_reason(value, field_name, "approval_record_mismatch"))
    approval_ref = str(getattr(record, "approval_ref", ""))
    if approval_ref.startswith("approval_test_"):
        reasons.append("approval_test_ref_denied")
    if getattr(record, "decision", None) != FileReviewApprovalDecisionKind.approve_review_only:
        reasons.append("approval_denied")
    if getattr(record, "status", None) != FileReviewApprovalCaptureDecisionStatus.approved_for_review_only:
        reasons.append("approval_denied")
    if getattr(record, "revoked_at", None) is not None:
        reasons.append("approval_denied")
    if getattr(record, "expires_at", None) is not None and record.expires_at <= (current_time or utc_now()):
        reasons.append("approval_denied")
    active_replay_nonce = getattr(record, "replay_nonce", None)
    if active_replay_nonce and active_replay_nonce in list(getattr(record, "used_replay_nonces", [])):
        reasons.append("approval_denied")
    if getattr(record, "safe_reason", None):
        reasons.extend(_validate_safe_text_reason(record.safe_reason, "safe_reason", "approval_record_mismatch"))
    reasons.extend(_validate_payload_reason(getattr(record, "metadata", {}), "metadata", "approval_record_mismatch"))
    reasons.extend(_raw_extra_reasons(record))
    return _dedupe(reasons)


def _proposal_reasons(proposal: SafeContextProposal) -> list[str]:
    reasons = []
    reasons.extend(_raw_extra_reasons(proposal))
    reasons.extend(_proposal_raw_reasons(proposal))
    for field_name, reason in _PROPOSAL_REASON_BY_FIELD.items():
        if bool(_extra_value(proposal, field_name, False)):
            reasons.append(reason)
    if not bool(_extra_value(proposal, "non_authoritative", False)):
        reasons.append("future_milestone_required")
    if not bool(_extra_value(proposal, "proposal_only", False)):
        reasons.append("future_milestone_required")
    if not bool(_extra_value(proposal, "no_context_injection", False)):
        reasons.append("context_injection_denied")
    reasons.extend(_validate_safe_text_reason(getattr(proposal, "safe_summary", None), "safe_summary", "unsafe_section_content"))
    reasons.extend(_validate_payload_reason(getattr(proposal, "metadata", {}), "metadata", "unsafe_section_content"))
    for section in list(getattr(proposal, "sections", [])):
        reasons.extend(_section_reasons(section))
    return _dedupe(reasons)


def _proposal_binding_reasons(
    proposal: SafeContextProposal,
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
) -> list[str]:
    binding = getattr(proposal, "binding", None)
    if binding is None:
        return ["approval_record_mismatch"]
    checks = [
        (getattr(binding, "approval_ref", None), approval_record.approval_ref, "approval_record_mismatch"),
        (getattr(binding, "actor_ref", None), packet.source.actor_ref, "actor_ref_mismatch"),
        (getattr(binding, "review_packet_ref", None), packet.review_packet_ref, "review_packet_mismatch"),
        (getattr(binding, "preview_result_ref", None), packet.source.preview_result_ref, "preview_result_mismatch"),
        (
            getattr(binding, "redaction_summary_ref", None),
            packet.redaction_verification.redaction_summary_ref,
            "redaction_summary_mismatch",
        ),
        (getattr(binding, "file_ref", None), packet.source.file_ref, "file_ref_mismatch"),
        (getattr(binding, "safe_path_ref", None), packet.source.safe_path_ref, "path_ref_mismatch"),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _proposal_raw_reasons(proposal: SafeContextProposal) -> list[str]:
    reasons = []
    for field_name, reason in _RAW_FIELD_REASONS.items():
        if _extra_value(proposal, field_name, None) is not None:
            reasons.append(reason)
    if bool(_extra_value(proposal, "raw_content_stored", False)):
        reasons.append("raw_content_present")
    if bool(_extra_value(proposal, "full_file_content_stored", False)):
        reasons.append("full_file_content_present")
    if bool(_extra_value(proposal, "unredacted_preview_stored", False)):
        reasons.append("unredacted_preview_present")
    return reasons


def _section_reasons(section: Any) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(section, "section_ref", None), "section_ref"),
        (getattr(section, "source_ref", None), "source_ref"),
    ]:
        reasons.extend(_validate_required_ref_reason(value, field_name, "unsafe_section_content"))
    for value, field_name in [
        (getattr(section, "title", None), "title"),
        (_strip_redaction_markers(str(getattr(section, "content", ""))), "content"),
    ]:
        reasons.extend(_validate_safe_text_reason(value, field_name, "unsafe_section_content"))
    for field_name in ["redacted", "bounded", "non_authoritative"]:
        if not bool(_extra_value(section, field_name, False)):
            reasons.append("unsafe_section_content")
    return reasons


def _authority_ref_reasons(refs: list[str]) -> list[str]:
    reasons = []
    for ref in refs:
        lowered = ref.lower()
        if lowered.startswith("approval") or lowered.startswith("consent"):
            reasons.append("approval_ref_not_authority")
        if lowered.startswith(("model", "memory", "context", "tool-intent", "openwebui", "control-center")):
            reasons.append("future_milestone_required")
    return reasons


def _raw_extra_reasons(model: Any) -> list[str]:
    reasons = []
    for field_name, reason in _RAW_FIELD_REASONS.items():
        if field_name in _extra_keys(model) or _extra_value(model, field_name, None) is not None:
            reasons.append(reason)
    return reasons


def _map_file_review_reason(reason: str) -> list[str]:
    lowered = reason.lower()
    mapped = []
    if "raw_content" in lowered:
        mapped.append("raw_content_present")
    if "full_file" in lowered or "full_file_content" in lowered:
        mapped.append("full_file_content_present")
    if "unredacted" in lowered:
        mapped.append("unredacted_preview_present")
    if "redaction_summary" in lowered:
        mapped.append("missing_redaction_summary")
    if "context_injection" in lowered:
        mapped.append("context_injection_denied")
    if "memory_write" in lowered:
        mapped.append("memory_write_denied")
    if "export" in lowered:
        mapped.append("export_denied")
    if "execution" in lowered:
        mapped.append("execution_denied")
    if "context_proposal" in lowered:
        mapped.append("future_milestone_required")
    return mapped


def _validate_required_ref_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return [fallback_reason]
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_safe_text_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return [fallback_reason]
    try:
        validate_safe_action_text(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_payload_reason(value, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _extra_value(model: Any, field_name: str, default=None):
    return getattr(model, field_name, default)


def _extra_keys(model: Any) -> set[str]:
    if not isinstance(model, BaseModel):
        return set()
    return set(getattr(model, "__dict__", {})) - set(getattr(type(model), "model_fields", {}))


def _strip_redaction_markers(value: str) -> str:
    return (
        value.replace("[REDACTED:SECRET_ASSIGNMENT]", "")
        .replace("[REDACTED:BEARER_TOKEN]", "")
        .replace("[REDACTED:PRIVATE_KEY_MARKER]", "")
        .replace("[REDACTED:HIGH_ENTROPY_TOKEN]", "")
        .replace("[REDACTED]", "")
        or "redacted"
    )


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


_POLICY_REASON_BY_FIELD = {
    "context_surface_enabled": "future_milestone_required",
    "context_handoff_enabled": "future_milestone_required",
    "context_injection_enabled": "context_injection_denied",
    "openwebui_handoff_enabled": "openwebui_handoff_denied",
    "model_call_enabled": "model_call_denied",
    "memory_write_enabled": "memory_write_denied",
    "export_enabled": "export_denied",
    "execution_enabled": "execution_denied",
    "raw_file_access_enabled": "raw_content_present",
    "raw_content_enabled": "raw_content_present",
    "full_file_read_enabled": "full_file_content_present",
    "unredacted_preview_enabled": "unredacted_preview_present",
    "backend_route_enabled": "future_milestone_required",
    "control_center_surface_enabled": "future_milestone_required",
    "production_authority_enabled": "future_milestone_required",
}

_PROPOSAL_REASON_BY_FIELD = {
    "context_surface_enabled": "future_milestone_required",
    "context_handoff_enabled": "future_milestone_required",
    "context_injection_enabled": "context_injection_denied",
    "openwebui_handoff_enabled": "openwebui_handoff_denied",
    "model_call_enabled": "model_call_denied",
    "memory_write_enabled": "memory_write_denied",
    "export_enabled": "export_denied",
    "execution_enabled": "execution_denied",
    "raw_file_access_enabled": "raw_content_present",
    "truth_authority_claimed": "future_milestone_required",
}

_RAW_FIELD_REASONS = {
    "raw_content": "raw_content_present",
    "full_file_content": "full_file_content_present",
    "unredacted_preview": "unredacted_preview_present",
    "raw_absolute_path": "raw_content_present",
    "absolute_path": "raw_content_present",
}
