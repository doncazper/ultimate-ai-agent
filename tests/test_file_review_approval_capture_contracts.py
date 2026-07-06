from typing import Any
from datetime import timedelta

import pytest

from ultimate_ai_agent.core.file_review import (
    FileReviewApprovalCaptureDecisionStatus,
    FileReviewApprovalCaptureRequest,
    FileReviewApprovalDecisionKind,
    build_file_review_packet,
    capture_file_review_approval,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)
from tests.authority_helpers import files_write_authority_lease


def _packet() -> Any:
    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:capture",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:capture",
        safe_path_ref="filesystem-preview-path:safe-root_capture/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    return build_file_review_packet(
        preview_output=preview,
        actor_ref="user:capture",
        request_ref="file-review-request:capture",
        file_ref="file-ref:capture-review",
        safe_summary="Review a redacted preview packet.",
    )


def _request(packet: Any, **overrides: Any) -> Any:
    data = {
        "approval_ref": "file-review-approval-capture:approval",
        "actor_ref": packet.source.actor_ref,
        "review_packet_ref": packet.review_packet_ref,
        "preview_result_ref": packet.source.preview_result_ref,
        "redaction_summary_ref": packet.redaction_verification.redaction_summary_ref,
        "file_ref": packet.source.file_ref,
        "safe_path_ref": packet.source.safe_path_ref,
        "decision": FileReviewApprovalDecisionKind.approve_review_only,
        "idempotency_key": "file-review-approval-idempotency:capture",
        "safe_reason": "User reviewed the redacted packet.",
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
    }
    data.update(overrides)
    return FileReviewApprovalCaptureRequest(**data)


def test_review_only_approval_capture_requires_files_write_authority() -> None:
    packet = _packet()
    request = _request(packet)

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert decision.captured is False
    assert decision.persisted is False
    assert "FILE_REVIEW_APPROVAL_CAPTURE_AUTHORITY_DENIED" in decision.reason_codes
    assert (
        "blocked-state:file-review-approval-capture-authority-lease-required"
        in decision.reason_codes
    )
    assert decision.authority_decision_outcome == "deny"
    assert decision.authority_lease_ref is None
    assert decision.execution_authorized is False


def test_review_only_approval_capture_persists_safe_record_with_files_write_lease() -> None:
    packet = _packet()
    request = _request(packet)

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[files_write_authority_lease()],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.approved_for_review_only
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.review_only is True
    assert decision.authority_decision_outcome == "ask"
    assert decision.authority_decision_ref is not None
    assert decision.authority_lease_ref == "authority-lease-ref:test-files-review-write"
    assert decision.record is not None
    assert decision.record.review_packet_ref == packet.review_packet_ref
    assert decision.record.preview_result_ref == packet.source.preview_result_ref
    assert decision.record.redaction_summary_ref == packet.redaction_verification.redaction_summary_ref
    assert decision.record.authority_decision_ref == decision.authority_decision_ref
    assert decision.record.authority_decision_outcome == "ask"
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.authority_lease_ref == decision.authority_lease_ref
    assert decision.raw_file_access_authorized is False
    assert decision.context_proposal_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    dumped = decision.model_dump(mode="json")
    assert "raw_content" not in dumped
    assert "unredacted_preview" not in dumped


def test_review_only_denial_capture_persists_safe_denial_record() -> None:
    packet = _packet()
    request = _request(packet, decision=FileReviewApprovalDecisionKind.deny_review_only)

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[files_write_authority_lease()],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.denied_for_review
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.authority_decision_outcome == "ask"
    assert decision.record is not None
    assert decision.record.decision == FileReviewApprovalDecisionKind.deny_review_only
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"actor_ref": "user:other"}, "FILE_REVIEW_APPROVAL_CAPTURE_ACTOR_MISMATCH"),
        ({"review_packet_ref": "file-review-packet:other"}, "FILE_REVIEW_APPROVAL_CAPTURE_PACKET_MISMATCH"),
        ({"preview_result_ref": "redacted-file-preview-output:other"}, "FILE_REVIEW_APPROVAL_CAPTURE_PREVIEW_RESULT_MISMATCH"),
        ({"redaction_summary_ref": "file-review-redaction-summary:other"}, "FILE_REVIEW_APPROVAL_CAPTURE_REDACTION_SUMMARY_MISMATCH"),
        ({"file_ref": "file-ref:other"}, "FILE_REVIEW_APPROVAL_CAPTURE_FILE_REF_MISMATCH"),
        ({"safe_path_ref": "filesystem-preview-path:safe-root_capture/docs/other.md"}, "FILE_REVIEW_APPROVAL_CAPTURE_PATH_REF_MISMATCH"),
        ({"approval_ref": "approval_test_m37"}, "FILE_REVIEW_APPROVAL_TEST_REF_DENIED"),
        ({"expires_at": utc_now() - timedelta(minutes=1)}, "FILE_REVIEW_APPROVAL_CAPTURE_EXPIRED"),
        ({"revoked_at": utc_now()}, "FILE_REVIEW_APPROVAL_CAPTURE_REVOKED"),
        ({"replay_nonce": "file-review-replay:1", "used_replay_nonces": ["file-review-replay:1"]}, "FILE_REVIEW_APPROVAL_CAPTURE_REPLAY_DETECTED"),
    ],
)
def test_capture_denies_binding_authority_and_lifecycle_failures(override: Any, reason: str) -> None:
    packet = _packet()
    request = _request(packet)
    if "approval_ref" in override and str(override["approval_ref"]).startswith("approval_test_"):
        request = request.model_copy(update=override)
    else:
        request = _request(packet, **override)

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[files_write_authority_lease()],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.captured is False
    assert decision.persisted is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "flag,reason",
    [
        ("raw_file_access_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_RAW_ACCESS_DENIED"),
        ("raw_content_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED"),
        ("full_file_content_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED"),
        ("unredacted_preview_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED"),
        ("context_proposal_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_PROPOSAL_DENIED"),
        ("context_injection_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_MEMORY_WRITE_DENIED"),
        ("export_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_EXPORT_DENIED"),
        ("execution_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_EXECUTION_DENIED"),
    ],
)
def test_model_copy_mutated_capture_request_flags_are_revalidated(flag: Any, reason: str) -> None:
    packet = _packet()
    request = _request(packet).model_copy(update={flag: True})

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[files_write_authority_lease()],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.captured is False
    assert decision.persisted is False
    assert decision.execution_performed is False


def test_model_copy_mutated_secret_metadata_is_denied_without_echoing_secret() -> None:
    packet = _packet()
    request = _request(packet).model_copy(update={"metadata": {"api_key": "abc123supersecret"}})

    decision = capture_file_review_approval(
        packet,
        request,
        current_time=utc_now(),
        active_authority_leases=[files_write_authority_lease()],
    )

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert "FILE_REVIEW_APPROVAL_CAPTURE_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "abc123supersecret" not in decision.safe_message
    assert "abc123supersecret" not in str(decision.model_dump(mode="json"))
