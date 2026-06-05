from __future__ import annotations

from datetime import datetime
from typing import Any

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.context_handoff.contracts import (
    ContextHandoffApprovalPolicy,
    ContextHandoffApprovalRequest,
)
from ultimate_ai_agent.core.context_proposal.contracts import SafeContextProposal
from ultimate_ai_agent.core.time import utc_now


def validate_context_handoff_approval(
    *,
    proposal: SafeContextProposal | None,
    request: ContextHandoffApprovalRequest | None,
    policy: ContextHandoffApprovalPolicy | None = None,
    request_ref: str | None = None,
    current_time: datetime | None = None,
) -> list[str]:
    reasons: list[str] = []
    reasons.extend(_policy_reasons(policy or ContextHandoffApprovalPolicy()))
    if proposal is None:
        reasons.append("proposal_required")
        if request_ref:
            reasons.extend(_validate_ref_reason(request_ref, "approval_ref", "approval_ref_not_authority"))
            reasons.append("approval_ref_not_authority")
            if request_ref.startswith("approval_test_"):
                reasons.append("approval_test_ref_denied")
        return _dedupe(reasons)
    reasons.extend(_proposal_reasons(proposal))
    if request is None:
        reasons.append("approval_ref_not_authority")
        return _dedupe(reasons)
    reasons.extend(_request_reasons(request, current_time=current_time))
    reasons.extend(_binding_reasons(proposal=proposal, request=request))
    return _dedupe(reasons)


def _policy_reasons(policy: ContextHandoffApprovalPolicy) -> list[str]:
    reasons = []
    if not bool(_extra_value(policy, "context_handoff_approval_enabled", False)):
        reasons.append("future_milestone_required")
    if not bool(_extra_value(policy, "exact_proposal_binding_required", False)):
        reasons.append("proposal_ref_mismatch")
    if not bool(_extra_value(policy, "no_injection_required", False)):
        reasons.append("context_injection_denied")
    for field_name, reason in _POLICY_REASON_BY_FIELD.items():
        if bool(_extra_value(policy, field_name, False)):
            reasons.append(reason)
    return _dedupe(reasons)


def _request_reasons(request: ContextHandoffApprovalRequest, *, current_time: datetime | None = None) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(request, "approval_ref", None), "approval_ref"),
        (getattr(request, "actor_ref", None), "actor_ref"),
        (getattr(request, "proposal_ref", None), "proposal_ref"),
        (getattr(request, "approval_record_ref", None), "approval_record_ref"),
        (getattr(request, "review_packet_ref", None), "review_packet_ref"),
        (getattr(request, "preview_result_ref", None), "preview_result_ref"),
        (getattr(request, "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(request, "file_ref", None), "file_ref"),
        (getattr(request, "safe_path_ref", None), "safe_path_ref"),
        (getattr(request, "idempotency_key", None), "idempotency_key"),
    ]:
        reasons.extend(_validate_ref_reason(value, field_name, "approval_record_mismatch"))
    approval_ref = str(getattr(request, "approval_ref", ""))
    if approval_ref.startswith("approval_test_"):
        reasons.append("approval_test_ref_denied")
    if getattr(request, "expires_at", None) is not None and request.expires_at <= (current_time or utc_now()):
        reasons.append("approval_expired")
    if getattr(request, "revoked_at", None) is not None:
        reasons.append("approval_revoked")
    replay_nonce = getattr(request, "replay_nonce", None)
    if replay_nonce and replay_nonce in list(getattr(request, "used_replay_nonces", [])):
        reasons.append("approval_replayed")
    if getattr(request, "safe_reason", None):
        reasons.extend(_validate_text_reason(request.safe_reason, "safe_reason", "approval_record_mismatch"))
    for ref in list(getattr(request, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref", "approval_record_mismatch"))
    reasons.extend(_validate_payload_reason(getattr(request, "metadata", {}), "metadata", "approval_record_mismatch"))
    for field_name, reason in _REQUEST_REASON_BY_FIELD.items():
        if bool(_extra_value(request, field_name, False)):
            reasons.append(reason)
    return _dedupe(reasons)


def _proposal_reasons(proposal: SafeContextProposal) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(proposal, "proposal_ref", None), "proposal_ref"),
        (getattr(getattr(proposal, "source", None), "approval_record_ref", None), "approval_record_ref"),
        (getattr(getattr(proposal, "binding", None), "approval_ref", None), "approval_ref"),
        (getattr(getattr(proposal, "binding", None), "review_packet_ref", None), "review_packet_ref"),
        (getattr(getattr(proposal, "binding", None), "preview_result_ref", None), "preview_result_ref"),
        (getattr(getattr(proposal, "binding", None), "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(getattr(proposal, "binding", None), "file_ref", None), "file_ref"),
        (getattr(getattr(proposal, "binding", None), "safe_path_ref", None), "safe_path_ref"),
        (getattr(getattr(proposal, "binding", None), "actor_ref", None), "actor_ref"),
    ]:
        reasons.extend(_validate_ref_reason(value, field_name, "proposal_ref_mismatch"))
    if not bool(_extra_value(proposal, "non_authoritative", False)):
        reasons.append("proposal_not_safe")
    if not bool(_extra_value(proposal, "proposal_only", False)):
        reasons.append("proposal_not_safe")
    if not bool(_extra_value(proposal, "no_context_injection", False)):
        reasons.append("context_injection_denied")
    for field_name, reason in _PROPOSAL_REASON_BY_FIELD.items():
        if bool(_extra_value(proposal, field_name, False)):
            reasons.append(reason)
    if getattr(proposal, "safe_summary", None):
        reasons.extend(_validate_text_reason(proposal.safe_summary, "safe_summary", "proposal_not_safe"))
    reasons.extend(_validate_payload_reason(getattr(proposal, "metadata", {}), "metadata", "proposal_not_safe"))
    return _dedupe(reasons)


def _binding_reasons(*, proposal: SafeContextProposal, request: ContextHandoffApprovalRequest) -> list[str]:
    checks = [
        (request.actor_ref, proposal.binding.actor_ref, "actor_ref_mismatch"),
        (request.proposal_ref, proposal.proposal_ref, "proposal_ref_mismatch"),
        (request.approval_record_ref, proposal.source.approval_record_ref, "approval_record_mismatch"),
        (request.review_packet_ref, proposal.binding.review_packet_ref, "review_packet_mismatch"),
        (request.preview_result_ref, proposal.binding.preview_result_ref, "preview_result_mismatch"),
        (request.redaction_summary_ref, proposal.binding.redaction_summary_ref, "redaction_summary_mismatch"),
        (request.file_ref, proposal.binding.file_ref, "file_ref_mismatch"),
        (request.safe_path_ref, proposal.binding.safe_path_ref, "path_ref_mismatch"),
    ]
    return [reason for actual, expected, reason in checks if actual != expected]


def _validate_ref_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return [fallback_reason]
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_text_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return [fallback_reason]
    try:
        validate_safe_action_text(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_payload_reason(value: Any, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _extra_value(model: Any, field_name: str, default=None):
    return getattr(model, field_name, default)


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


_POLICY_REASON_BY_FIELD = {
    "context_handoff_execution_enabled": "handoff_execution_denied",
    "context_injection_enabled": "context_injection_denied",
    "openwebui_handoff_execution_enabled": "openwebui_handoff_denied",
    "model_call_enabled": "model_call_denied",
    "memory_write_enabled": "memory_write_denied",
    "export_enabled": "export_denied",
    "execution_enabled": "execution_denied",
    "raw_file_access_enabled": "raw_content_present",
    "raw_content_enabled": "raw_content_present",
    "full_file_read_enabled": "full_file_content_present",
    "unredacted_preview_enabled": "unredacted_preview_present",
    "backend_route_enabled": "future_milestone_required",
    "control_center_mutation_enabled": "future_milestone_required",
    "production_authority_enabled": "future_milestone_required",
}

_REQUEST_REASON_BY_FIELD = _POLICY_REASON_BY_FIELD

_PROPOSAL_REASON_BY_FIELD = {
    "context_handoff_enabled": "handoff_execution_denied",
    "context_injection_enabled": "context_injection_denied",
    "openwebui_handoff_enabled": "openwebui_handoff_denied",
    "model_call_enabled": "model_call_denied",
    "memory_write_enabled": "memory_write_denied",
    "export_enabled": "export_denied",
    "execution_enabled": "execution_denied",
    "raw_file_access_enabled": "raw_content_present",
    "raw_content_stored": "raw_content_present",
    "full_file_content_stored": "full_file_content_present",
    "unredacted_preview_stored": "unredacted_preview_present",
    "truth_authority_claimed": "future_milestone_required",
}
