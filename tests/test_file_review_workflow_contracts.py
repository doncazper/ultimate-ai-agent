from typing import Any
from datetime import timedelta

from ultimate_ai_agent.core.file_review import (
    FileReviewDecisionStatus,
    FileReviewPacketStatus,
    FileReviewWorkflowPolicy,
    UserFileReviewApproval,
    build_file_review_packet,
    evaluate_file_review_gate,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)


def _preview_output(**overrides: Any) -> Any:
    data = {
        "output_ref": "redacted-file-preview-output:m35",
        "status": RedactedFilePreviewStatus.preview_generated,
        "root_ref": "safe-root:m35",
        "safe_path_ref": "filesystem-preview-path:safe-root_m35/docs/report.md",
        "redacted_preview": "Reviewed summary with [REDACTED:SECRET_ASSIGNMENT].",
        "redaction_summary": FilePreviewRedactionSummary(
            redaction_count=1,
            categories=["secret_assignment"],
        ),
        "preview_truncated": False,
        "preview_limit_bytes": 4096,
        "file_size_bytes": 128,
    }
    data.update(overrides)
    return RedactedFilePreviewOutput(**data)


def _packet(**overrides: Any) -> Any:
    return build_file_review_packet(
        preview_output=_preview_output(),
        actor_ref="user:m35",
        request_ref="file-review-request:m35",
        file_ref="file-ref:m35-report",
        safe_summary="Review the redacted preview packet.",
        **overrides,
    )


def _approval(packet: Any, **overrides: Any) -> Any:
    data = {
        "approval_ref": "file-review-approval:m35",
        "actor_ref": "user:m35",
        "review_packet_ref": packet.review_packet_ref,
        "preview_result_ref": packet.source.preview_result_ref,
        "redaction_summary_ref": packet.redaction_verification.redaction_summary_ref,
        "file_ref": packet.source.file_ref,
        "safe_path_ref": packet.source.safe_path_ref,
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
    }
    data.update(overrides)
    return UserFileReviewApproval(**data)


def test_default_file_review_policy_is_review_only_and_non_authoritative() -> None:
    policy = FileReviewWorkflowPolicy()

    assert policy.file_review_workflow_enabled is True
    assert policy.review_packet_enabled is True
    assert policy.user_approval_gate_enabled is True
    assert policy.raw_file_access_enabled is False
    assert policy.raw_content_enabled is False
    assert policy.full_file_read_enabled is False
    assert policy.unredacted_preview_enabled is False
    assert policy.context_proposal_enabled is False
    assert policy.context_injection_enabled is False
    assert policy.memory_write_enabled is False
    assert policy.export_enabled is False
    assert policy.execution_enabled is False
    assert policy.approval_capture_enabled is False
    assert policy.approval_persistence_enabled is False
    assert policy.control_center_surface_enabled is False
    assert policy.backend_routes_enabled is False


def test_review_packet_is_built_from_redacted_preview_output_only() -> None:
    packet = _packet()

    assert packet.status == FileReviewPacketStatus.ready_for_review
    assert packet.source.preview_result_ref == "redacted-file-preview-output:m35"
    assert packet.source.safe_path_ref == "filesystem-preview-path:safe-root_m35/docs/report.md"
    assert packet.source.file_ref == "file-ref:m35-report"
    assert packet.redacted_preview == "Reviewed summary with [REDACTED:SECRET_ASSIGNMENT]."
    assert packet.redaction_verification.redaction_performed is True
    assert packet.redaction_verification.raw_content_removed is True
    assert packet.redaction_verification.redaction_summary_ref == "file-review-redaction-summary:m35"
    assert packet.raw_content_stored is False
    assert packet.full_file_content_stored is False
    assert packet.unredacted_preview_stored is False
    assert packet.raw_absolute_path_stored is False
    assert packet.context_injection_enabled is False
    assert packet.memory_write_enabled is False
    assert packet.export_enabled is False
    assert packet.execution_enabled is False
    dumped = str(packet.model_dump())
    assert "/Users/" not in dumped
    assert "super-secret-value" not in dumped


def test_exact_approval_binding_allows_review_only_decision() -> None:
    packet = _packet()
    approval = _approval(packet)

    decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.review_allowed
    assert decision.review_allowed is True
    assert decision.review_only is True
    assert decision.reason_codes == ["FILE_REVIEW_ALLOWED_FOR_REVIEW_ONLY"]
    assert decision.raw_file_access_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.raw_content_stored is False
    assert decision.receipt_plan.receipt_is_authority is False


def test_mismatched_approval_packet_is_denied() -> None:
    packet = _packet()
    approval = _approval(packet).model_copy(update={"review_packet_ref": "file-review-packet:other"})

    decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert decision.review_allowed is False
    assert "FILE_REVIEW_APPROVAL_PACKET_MISMATCH" in decision.reason_codes
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


def test_model_copy_mutated_packet_file_ref_is_denied_at_gate() -> None:
    packet = _packet()
    approval = _approval(packet)
    mutated_packet = packet.model_copy(update={"source": packet.source.model_copy(update={"file_ref": "file-ref:m35-mutated"})})

    decision = evaluate_file_review_gate(mutated_packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH" in decision.reason_codes
    assert decision.review_allowed is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


def test_model_copy_mutated_packet_safe_path_ref_is_denied_at_gate() -> None:
    packet = _packet()
    approval = _approval(packet)
    mutated_packet = packet.model_copy(
        update={"source": packet.source.model_copy(update={"safe_path_ref": "filesystem-preview-path:safe-root_m35/docs/mutated.md"})}
    )

    decision = evaluate_file_review_gate(mutated_packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH" in decision.reason_codes
    assert decision.review_allowed is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
