from __future__ import annotations

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel

from ultimate_ai_agent.core.approvals.v2.validation import (
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.file_review.contracts import (
    FileReviewDecision,
    FileReviewGate,
    FileReviewPacket,
    FileReviewPacketSource,
    FileReviewReceiptPlan,
    FileReviewRedactionVerification,
    FileReviewWorkflowPolicy,
    UserFileReviewApproval,
    file_review_suffix,
    redaction_summary_ref_for_preview,
)
from ultimate_ai_agent.core.file_review.enums import FileReviewDecisionStatus
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime.file_preview import RedactedFilePreviewOutput


def build_file_review_packet(
    *,
    preview_output: RedactedFilePreviewOutput,
    actor_ref: str,
    request_ref: str,
    file_ref: str,
    safe_summary: str,
    policy: FileReviewWorkflowPolicy | None = None,
) -> FileReviewPacket:
    FileReviewWorkflowPolicy.model_validate((policy or FileReviewWorkflowPolicy()).model_dump())
    RedactedFilePreviewOutput.model_validate(preview_output.model_dump())
    suffix = file_review_suffix(preview_output.output_ref)
    redaction_summary_ref = redaction_summary_ref_for_preview(preview_output)
    return FileReviewPacket(
        review_packet_ref=f"file-review-packet:{suffix}",
        source=FileReviewPacketSource(
            preview_result_ref=preview_output.output_ref,
            safe_path_ref=preview_output.safe_path_ref,
            root_ref=preview_output.root_ref,
            actor_ref=actor_ref,
            request_ref=request_ref,
            file_ref=file_ref,
        ),
        redaction_verification=FileReviewRedactionVerification(
            verification_ref=f"file-review-redaction-verification:{suffix}",
            redaction_summary_ref=redaction_summary_ref,
            redaction_performed=True,
            raw_content_removed=not preview_output.raw_content_returned and not preview_output.raw_content_stored,
            secret_like_content_removed=not preview_output.redaction_summary.sensitive_values_returned,
            redaction_summary_required=True,
            redaction_summary_contains_sensitive_values=preview_output.redaction_summary.sensitive_values_returned,
            redacted_preview_only=preview_output.redacted_preview_returned,
        ),
        redacted_preview=preview_output.redacted_preview,
        safe_summary=safe_summary,
    )


def build_file_review_receipt_plan(
    packet: FileReviewPacket,
    *,
    approval_ref: str | None = None,
) -> FileReviewReceiptPlan:
    packet_ref = getattr(packet, "review_packet_ref", "file-review-packet:unknown")
    suffix = file_review_suffix(packet_ref)
    return FileReviewReceiptPlan(
        receipt_plan_ref=f"file-review-receipt-plan:{suffix}",
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        approval_ref=approval_ref,
    )


def evaluate_file_review_packet(
    packet: FileReviewPacket,
    *,
    policy: FileReviewWorkflowPolicy | None = None,
) -> FileReviewDecision:
    active_policy = policy or FileReviewWorkflowPolicy()
    reasons: list[str] = []
    reasons.extend(_revalidate_policy_for_evaluation(active_policy))
    reasons.extend(_revalidate_packet_for_evaluation(packet))
    reasons = _dedupe(reasons)
    if reasons:
        return _denied_packet_decision(packet, reasons)

    return FileReviewDecision(
        decision_ref=f"file-review-decision:{file_review_suffix(packet.review_packet_ref)}",
        review_packet_ref=packet.review_packet_ref,
        status=FileReviewDecisionStatus.packet_valid_for_review,
        packet_valid_for_review=True,
        review_allowed=False,
        review_only=True,
        reason_codes=["FILE_REVIEW_PACKET_VALID_FOR_REVIEW_ONLY"],
        safe_message="File review packet is valid for review only. No authority was granted.",
    )


def evaluate_file_review_gate(
    packet: FileReviewPacket,
    *,
    approval: UserFileReviewApproval | None = None,
    gate: FileReviewGate | None = None,
    policy: FileReviewWorkflowPolicy | None = None,
    current_time: datetime | None = None,
    replay_nonce: str | None = None,
) -> FileReviewDecision:
    reasons = []
    reasons.extend(_revalidate_policy_for_evaluation(policy or FileReviewWorkflowPolicy()))
    reasons.extend(_revalidate_packet_for_evaluation(packet))
    if getattr(packet, "approval_ref", None):
        reasons.append("FILE_REVIEW_APPROVAL_REF_NOT_AUTHORITY")
    if approval is None:
        reasons.append("FILE_REVIEW_APPROVAL_OBJECT_REQUIRED")
        return _denied_packet_decision(packet, _dedupe(reasons))

    reasons.extend(_revalidate_approval_for_evaluation(approval))
    active_gate = gate or FileReviewGate(
        expected_actor_ref=packet.source.actor_ref,
        expected_review_packet_ref=packet.review_packet_ref,
        expected_preview_result_ref=packet.source.preview_result_ref,
        expected_redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        expected_file_ref=packet.source.file_ref,
        expected_safe_path_ref=packet.source.safe_path_ref,
    )
    reasons.extend(_revalidate_gate_for_evaluation(active_gate))

    if approval.actor_ref != active_gate.expected_actor_ref:
        reasons.append("FILE_REVIEW_APPROVAL_ACTOR_MISMATCH")
    if approval.review_packet_ref != active_gate.expected_review_packet_ref:
        reasons.append("FILE_REVIEW_APPROVAL_PACKET_MISMATCH")
    if approval.preview_result_ref != active_gate.expected_preview_result_ref:
        reasons.append("FILE_REVIEW_APPROVAL_PREVIEW_RESULT_MISMATCH")
    if approval.redaction_summary_ref != active_gate.expected_redaction_summary_ref:
        reasons.append("FILE_REVIEW_APPROVAL_REDACTION_SUMMARY_MISMATCH")
    if approval.file_ref != active_gate.expected_file_ref:
        reasons.append("FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH")
    if approval.safe_path_ref != active_gate.expected_safe_path_ref:
        reasons.append("FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH")
    if approval.revoked_at is not None:
        reasons.append("FILE_REVIEW_APPROVAL_REVOKED")
    if approval.expires_at is not None and approval.expires_at <= (current_time or utc_now()):
        reasons.append("FILE_REVIEW_APPROVAL_EXPIRED")
    active_replay_nonce = replay_nonce or approval.replay_nonce
    if active_replay_nonce and active_replay_nonce in approval.used_replay_nonces:
        reasons.append("FILE_REVIEW_APPROVAL_REPLAY_DETECTED")

    reasons = _dedupe(reasons)
    if reasons:
        return _denied_packet_decision(packet, reasons, status=FileReviewDecisionStatus.denied)

    return FileReviewDecision(
        decision_ref=f"file-review-decision:{file_review_suffix(packet.review_packet_ref)}",
        review_packet_ref=packet.review_packet_ref,
        status=FileReviewDecisionStatus.review_allowed,
        packet_valid_for_review=True,
        review_allowed=True,
        review_only=True,
        reason_codes=["FILE_REVIEW_ALLOWED_FOR_REVIEW_ONLY"],
        safe_message="File review approval applies to the exact redacted packet for review only.",
        receipt_plan=build_file_review_receipt_plan(packet, approval_ref=approval.approval_ref),
    )


def _denied_packet_decision(
    packet: FileReviewPacket,
    reasons: List[str],
    *,
    status: FileReviewDecisionStatus = FileReviewDecisionStatus.denied,
) -> FileReviewDecision:
    packet_ref = getattr(packet, "review_packet_ref", "file-review-packet:invalid")
    return FileReviewDecision(
        decision_ref=f"file-review-decision:{file_review_suffix(packet_ref)}",
        review_packet_ref=packet_ref,
        status=status,
        packet_valid_for_review=False,
        review_allowed=False,
        review_only=True,
        reason_codes=_dedupe(reasons),
        safe_message="File review request denied. No raw access, context, memory, export, or execution authority was granted.",
    )


def _dedupe(reasons: List[str]) -> List[str]:
    return list(dict.fromkeys(reasons))


def _extra_value(model: Any, field_name: str, default: Any | None = None) -> Any:
    return getattr(model, field_name, default)


def _extra_keys(model: BaseModel) -> set[str]:
    return set(getattr(model, "__dict__", {})) - set(getattr(type(model), "model_fields", {}))


def _validate_ref_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return []
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_required_ref_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return [fallback_reason]
    return _validate_ref_reason(value, field_name, fallback_reason)


def _validate_safe_text_reason(value: str | None, field_name: str, fallback_reason: str) -> list[str]:
    if value is None:
        return []
    try:
        validate_safe_action_text(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _validate_payload_reason(value: str, field_name: str, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return [fallback_reason]
    return []


def _revalidate_policy_for_evaluation(policy: FileReviewWorkflowPolicy) -> list[str]:
    reasons = []
    for field_name, reason in _POLICY_BLOCKED_FLAGS.items():
        if bool(_extra_value(policy, field_name, False)):
            reasons.append(reason)
    for field_name in [
        "file_review_workflow_enabled",
        "review_packet_enabled",
        "user_approval_gate_enabled",
        "redaction_verification_required",
        "exact_approval_binding_required",
    ]:
        if not bool(_extra_value(policy, field_name, False)):
            reasons.append("FILE_REVIEW_POLICY_REVALIDATION_FAILED")
    return _dedupe(reasons)


def _revalidate_packet_for_evaluation(packet: FileReviewPacket) -> list[str]:
    reasons = []
    reasons.extend(_validate_ref_reason(getattr(packet, "review_packet_ref", None), "review_packet_ref", "FILE_REVIEW_PACKET_REVALIDATION_FAILED"))
    reasons.extend(_validate_safe_text_reason(getattr(packet, "safe_summary", None), "safe_summary", "FILE_REVIEW_PACKET_REVALIDATION_FAILED"))
    reasons.extend(_validate_payload_reason(getattr(packet, "metadata", {}), "metadata", "FILE_REVIEW_SECRET_METADATA_DENIED"))
    for ref in [*list(getattr(packet, "metadata_refs", [])), *list(getattr(packet, "authority_refs", []))]:
        reasons.extend(_validate_ref_reason(ref, "metadata_ref", "FILE_REVIEW_PACKET_REVALIDATION_FAILED"))
    reasons.extend(_packet_source_reasons(getattr(packet, "source", None)))
    reasons.extend(_redaction_verification_reasons(getattr(packet, "redaction_verification", None)))
    reasons.extend(_packet_boundary_reasons(packet))
    return _dedupe(reasons)


def _packet_source_reasons(source: FileReviewPacketSource | None) -> list[str]:
    if source is None:
        return ["FILE_REVIEW_PACKET_SOURCE_REQUIRED"]
    reasons = []
    for value, field_name in [
        (getattr(source, "preview_result_ref", None), "preview_result_ref"),
        (getattr(source, "safe_path_ref", None), "safe_path_ref"),
        (getattr(source, "root_ref", None), "root_ref"),
        (getattr(source, "actor_ref", None), "actor_ref"),
        (getattr(source, "request_ref", None), "request_ref"),
        (getattr(source, "file_ref", None), "file_ref"),
    ]:
        reasons.extend(_validate_required_ref_reason(value, field_name, "FILE_REVIEW_PACKET_SOURCE_REVALIDATION_FAILED"))
    if _looks_like_raw_path(getattr(source, "safe_path_ref", "")):
        reasons.append("FILE_REVIEW_RAW_ABSOLUTE_PATH_DENIED")
    return reasons


def _redaction_verification_reasons(verification: FileReviewRedactionVerification | None) -> list[str]:
    if verification is None:
        return ["FILE_REVIEW_REDACTION_VERIFICATION_REQUIRED"]
    reasons = []
    reasons.extend(_validate_ref_reason(getattr(verification, "verification_ref", None), "verification_ref", "FILE_REVIEW_REDACTION_VERIFICATION_INVALID"))
    reasons.extend(_validate_ref_reason(getattr(verification, "redaction_summary_ref", None), "redaction_summary_ref", "FILE_REVIEW_REDACTION_VERIFICATION_INVALID"))
    required_true = {
        "redaction_performed": "FILE_REVIEW_REDACTION_VERIFICATION_REQUIRED",
        "raw_content_removed": "FILE_REVIEW_RAW_CONTENT_DENIED",
        "secret_like_content_removed": "FILE_REVIEW_SECRET_CONTENT_DENIED",
        "redaction_summary_required": "FILE_REVIEW_REDACTION_SUMMARY_REQUIRED",
        "redacted_preview_only": "FILE_REVIEW_REDACTED_PREVIEW_REQUIRED",
    }
    for field_name, reason in required_true.items():
        if not bool(_extra_value(verification, field_name, False)):
            reasons.append(reason)
    if bool(_extra_value(verification, "redaction_summary_contains_sensitive_values", False)):
        reasons.append("FILE_REVIEW_REDACTION_SUMMARY_SECRET_VALUES_DENIED")
    return reasons


def _packet_boundary_reasons(packet: FileReviewPacket) -> list[str]:
    reasons = []
    if _extra_value(packet, "raw_content", None) is not None or bool(_extra_value(packet, "raw_content_stored", False)):
        reasons.append("FILE_REVIEW_RAW_CONTENT_DENIED")
    if _extra_value(packet, "full_file_content", None) is not None or bool(_extra_value(packet, "full_file_content_stored", False)):
        reasons.append("FILE_REVIEW_FULL_FILE_CONTENT_DENIED")
    if _extra_value(packet, "unredacted_preview", None) is not None or bool(_extra_value(packet, "unredacted_preview_stored", False)):
        reasons.append("FILE_REVIEW_UNREDACTED_PREVIEW_DENIED")
    if _extra_value(packet, "raw_absolute_path", None) is not None or bool(_extra_value(packet, "raw_absolute_path_stored", False)):
        reasons.append("FILE_REVIEW_RAW_ABSOLUTE_PATH_DENIED")
    for field_name, reason in _PACKET_BLOCKED_FLAGS.items():
        if bool(_extra_value(packet, field_name, False)):
            reasons.append(reason)
    if _looks_like_raw_path(str(_extra_value(packet, "raw_absolute_path", ""))):
        reasons.append("FILE_REVIEW_RAW_ABSOLUTE_PATH_DENIED")
    for extra_key in _extra_keys(packet):
        if extra_key in _EXTRA_PACKET_FIELD_REASONS:
            reasons.append(_EXTRA_PACKET_FIELD_REASONS[extra_key])
    reasons.extend(_authority_ref_reasons(getattr(packet, "authority_refs", [])))
    return reasons


def _revalidate_approval_for_evaluation(approval: UserFileReviewApproval) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(approval, "approval_ref", None), "approval_ref"),
        (getattr(approval, "actor_ref", None), "actor_ref"),
        (getattr(approval, "review_packet_ref", None), "review_packet_ref"),
        (getattr(approval, "preview_result_ref", None), "preview_result_ref"),
        (getattr(approval, "redaction_summary_ref", None), "redaction_summary_ref"),
        (getattr(approval, "file_ref", None), "file_ref"),
        (getattr(approval, "safe_path_ref", None), "safe_path_ref"),
        (getattr(approval, "replay_nonce", None), "replay_nonce"),
    ]:
        if field_name == "replay_nonce":
            reasons.extend(_validate_ref_reason(value, field_name, "FILE_REVIEW_APPROVAL_REVALIDATION_FAILED"))
        else:
            reasons.extend(_validate_required_ref_reason(value, field_name, "FILE_REVIEW_APPROVAL_REVALIDATION_FAILED"))
    approval_ref = str(getattr(approval, "approval_ref", ""))
    if approval_ref.startswith("approval_test_"):
        reasons.append("FILE_REVIEW_APPROVAL_TEST_REF_DENIED")
    for nonce in list(getattr(approval, "used_replay_nonces", [])):
        reasons.extend(_validate_ref_reason(nonce, "used_replay_nonce", "FILE_REVIEW_APPROVAL_REVALIDATION_FAILED"))
    for ref in list(getattr(approval, "metadata_refs", [])):
        reasons.extend(_validate_ref_reason(ref, "metadata_ref", "FILE_REVIEW_APPROVAL_REVALIDATION_FAILED"))
    reasons.extend(_validate_payload_reason(getattr(approval, "metadata", {}), "metadata", "FILE_REVIEW_APPROVAL_SECRET_METADATA_DENIED"))
    if bool(_extra_value(approval, "approval_capture_enabled", False)):
        reasons.append("FILE_REVIEW_APPROVAL_CAPTURE_DENIED")
    if bool(_extra_value(approval, "approval_persistence_enabled", False)):
        reasons.append("FILE_REVIEW_APPROVAL_PERSISTENCE_DENIED")
    return _dedupe(reasons)


def _revalidate_gate_for_evaluation(gate: FileReviewGate) -> list[str]:
    reasons = []
    for value, field_name in [
        (getattr(gate, "gate_ref", None), "gate_ref"),
        (getattr(gate, "expected_actor_ref", None), "expected_actor_ref"),
        (getattr(gate, "expected_review_packet_ref", None), "expected_review_packet_ref"),
        (getattr(gate, "expected_preview_result_ref", None), "expected_preview_result_ref"),
        (getattr(gate, "expected_redaction_summary_ref", None), "expected_redaction_summary_ref"),
        (getattr(gate, "expected_file_ref", None), "expected_file_ref"),
        (getattr(gate, "expected_safe_path_ref", None), "expected_safe_path_ref"),
    ]:
        reasons.extend(_validate_required_ref_reason(value, field_name, "FILE_REVIEW_GATE_REVALIDATION_FAILED"))
    return _dedupe(reasons)


def _authority_ref_reasons(refs: list[str]) -> list[str]:
    reasons = []
    for ref in refs:
        lowered = ref.lower()
        if lowered.startswith("model-output:") or lowered.startswith("model:"):
            reasons.append("FILE_REVIEW_MODEL_OUTPUT_NOT_AUTHORITY")
        if lowered.startswith("memory:"):
            reasons.append("FILE_REVIEW_MEMORY_REF_NOT_AUTHORITY")
        if lowered.startswith("context-pack:") or lowered.startswith("context:"):
            reasons.append("FILE_REVIEW_CONTEXT_REF_NOT_AUTHORITY")
        if lowered.startswith("tool-intent:"):
            reasons.append("FILE_REVIEW_TOOL_INTENT_REF_NOT_AUTHORITY")
        if lowered.startswith("approval:") or lowered.startswith("approval-ref:"):
            reasons.append("FILE_REVIEW_APPROVAL_REF_NOT_AUTHORITY")
        if lowered.startswith("openwebui-output:") or lowered.startswith("openwebui:"):
            reasons.append("FILE_REVIEW_OPENWEBUI_OUTPUT_NOT_AUTHORITY")
        if lowered.startswith("control-center-preview:"):
            reasons.append("FILE_REVIEW_CONTROL_CENTER_PREVIEW_NOT_AUTHORITY")
    return reasons


def _looks_like_raw_path(value: str) -> bool:
    return value.startswith(("/Users/", "/home/", "/var/", "/etc/")) or ":\\" in value


_POLICY_BLOCKED_FLAGS = {
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

_PACKET_BLOCKED_FLAGS = {
    "raw_file_access_enabled": "FILE_REVIEW_RAW_FILE_ACCESS_DENIED",
    "context_proposal_enabled": "FILE_REVIEW_CONTEXT_PROPOSAL_DENIED",
    "context_injection_enabled": "FILE_REVIEW_CONTEXT_INJECTION_DENIED",
    "memory_write_enabled": "FILE_REVIEW_MEMORY_WRITE_DENIED",
    "export_enabled": "FILE_REVIEW_EXPORT_DENIED",
    "execution_enabled": "FILE_REVIEW_EXECUTION_DENIED",
    "approval_capture_enabled": "FILE_REVIEW_APPROVAL_CAPTURE_DENIED",
    "approval_persistence_enabled": "FILE_REVIEW_APPROVAL_PERSISTENCE_DENIED",
    "control_center_surface_enabled": "FILE_REVIEW_CONTROL_CENTER_SURFACE_DENIED",
    "backend_routes_enabled": "FILE_REVIEW_BACKEND_ROUTES_DENIED",
}

_EXTRA_PACKET_FIELD_REASONS = {
    "raw_content": "FILE_REVIEW_RAW_CONTENT_DENIED",
    "full_file_content": "FILE_REVIEW_FULL_FILE_CONTENT_DENIED",
    "unredacted_preview": "FILE_REVIEW_UNREDACTED_PREVIEW_DENIED",
    "raw_absolute_path": "FILE_REVIEW_RAW_ABSOLUTE_PATH_DENIED",
}
