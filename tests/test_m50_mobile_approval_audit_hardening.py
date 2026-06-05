from datetime import timedelta

from ultimate_ai_agent.core.mobile_companion import (
    MobileApprovalAuditStatus,
    MobileReviewApprovalCaptureDecisionStatus,
    MobileReviewApprovalDecisionKind,
    MobileReviewApprovalStore,
    audit_mobile_review_approval_records,
    audit_mobile_review_approval_store,
    capture_mobile_review_approval,
)
from ultimate_ai_agent.core.mobile_companion.approval_capture import (
    MobileReviewApprovalCaptureRequest,
)
from ultimate_ai_agent.core.time import utc_now


def _request(**overrides):
    data = {
        "approval_ref": "mobile-review-approval-capture:approval",
        "actor_ref": "user:mobile-reviewer",
        "mobile_surface_ref": "ccc-ios-review-surface:file-review-summary",
        "review_packet_ref": "file-review-packet:mobile-safe-review",
        "preview_result_ref": "redacted-file-preview-output:mobile-safe-review",
        "redaction_summary_ref": "file-review-redaction-summary:mobile-safe-review",
        "file_ref": "file-ref:mobile-safe-review",
        "safe_path_ref": "filesystem-preview-path:safe-root_mobile/docs/review.md",
        "receipt_plan_ref": "mobile-review-receipt-plan:mobile-safe-review",
        "decision": MobileReviewApprovalDecisionKind.approve_review_only,
        "idempotency_key": "mobile-review-approval-idempotency:mobile-safe-review",
        "issued_at": utc_now(),
        "expires_at": utc_now() + timedelta(minutes=5),
        "safe_reason": "User reviewed the redacted mobile review packet.",
        "expected_actor_ref": "user:mobile-reviewer",
        "expected_mobile_surface_ref": "ccc-ios-review-surface:file-review-summary",
        "expected_review_packet_ref": "file-review-packet:mobile-safe-review",
        "expected_preview_result_ref": "redacted-file-preview-output:mobile-safe-review",
        "expected_redaction_summary_ref": "file-review-redaction-summary:mobile-safe-review",
        "expected_file_ref": "file-ref:mobile-safe-review",
        "expected_safe_path_ref": "filesystem-preview-path:safe-root_mobile/docs/review.md",
    }
    data.update(overrides)
    return MobileReviewApprovalCaptureRequest(**data)


def _record(**overrides):
    decision = capture_mobile_review_approval(_request(**overrides), current_time=utc_now())
    assert decision.record is not None
    return decision.record


def test_mobile_approval_audit_accepts_safe_review_only_records() -> None:
    store = MobileReviewApprovalStore()
    capture_mobile_review_approval(_request(), store=store, current_time=utc_now())
    capture_mobile_review_approval(
        _request(
            approval_ref="mobile-review-approval-capture:denial",
            review_packet_ref="file-review-packet:mobile-safe-review-denied",
            preview_result_ref="redacted-file-preview-output:mobile-safe-review-denied",
            redaction_summary_ref="file-review-redaction-summary:mobile-safe-review-denied",
            file_ref="file-ref:mobile-safe-review-denied",
            safe_path_ref="filesystem-preview-path:safe-root_mobile/docs/denied.md",
            expected_review_packet_ref="file-review-packet:mobile-safe-review-denied",
            expected_preview_result_ref="redacted-file-preview-output:mobile-safe-review-denied",
            expected_redaction_summary_ref="file-review-redaction-summary:mobile-safe-review-denied",
            expected_file_ref="file-ref:mobile-safe-review-denied",
            expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/docs/denied.md",
            decision=MobileReviewApprovalDecisionKind.deny_review_only,
            idempotency_key="mobile-review-approval-idempotency:mobile-safe-review-denied",
        ),
        store=store,
        current_time=utc_now(),
    )

    report = audit_mobile_review_approval_store(store)

    assert report.status == MobileApprovalAuditStatus.passed
    assert report.review_only is True
    assert report.record_count == 2
    assert report.raw_content_found is False
    assert report.context_or_execution_authority_found is False
    assert report.export_performed is False
    assert report.execution_performed is False
    assert all(entry.safe_ref_only for entry in report.entries)
    dumped = report.model_dump(mode="json")
    assert "raw_content" not in dumped
    assert "full_file_content" not in dumped
    assert "unredacted_preview" not in dumped
    assert "absolute_path" not in dumped


def test_mobile_approval_audit_rejects_model_copy_raw_extra_without_echoing() -> None:
    record = _record().model_copy(update={"raw_content": "secret raw mobile review"})

    report = audit_mobile_review_approval_records([record])

    assert report.status == MobileApprovalAuditStatus.failed
    assert "MOBILE_APPROVAL_AUDIT_RAW_CONTENT_DENIED" in report.reason_codes
    assert "secret raw mobile review" not in report.safe_message
    assert "secret raw mobile review" not in str(report.model_dump(mode="json"))


def test_mobile_approval_audit_rejects_secret_metadata_and_raw_paths() -> None:
    record = _record().model_copy(
        update={
            "metadata": {"api_key": "abc123supersecret"},
            "safe_path_ref": "/Users/sambehdjou/private/raw.txt",
        }
    )

    report = audit_mobile_review_approval_records([record])

    assert report.status == MobileApprovalAuditStatus.failed
    assert "MOBILE_APPROVAL_AUDIT_SECRET_METADATA_DENIED" in report.reason_codes
    assert "MOBILE_APPROVAL_AUDIT_RAW_PATH_DENIED" in report.reason_codes
    assert "abc123supersecret" not in str(report.model_dump(mode="json"))


def test_mobile_approval_audit_rejects_status_decision_mismatch() -> None:
    record = _record().model_copy(
        update={"status": MobileReviewApprovalCaptureDecisionStatus.denied_for_mobile_review}
    )

    report = audit_mobile_review_approval_records([record])

    assert report.status == MobileApprovalAuditStatus.failed
    assert "MOBILE_APPROVAL_AUDIT_STATUS_DECISION_MISMATCH" in report.reason_codes


def test_mobile_approval_audit_rejects_duplicate_idempotency_mismatch() -> None:
    first = _record()
    second = _record(
        approval_ref="mobile-review-approval-capture:approval-two",
        review_packet_ref="file-review-packet:mobile-safe-review-two",
        preview_result_ref="redacted-file-preview-output:mobile-safe-review-two",
        redaction_summary_ref="file-review-redaction-summary:mobile-safe-review-two",
        file_ref="file-ref:mobile-safe-review-two",
        safe_path_ref="filesystem-preview-path:safe-root_mobile/docs/two.md",
        expected_review_packet_ref="file-review-packet:mobile-safe-review-two",
        expected_preview_result_ref="redacted-file-preview-output:mobile-safe-review-two",
        expected_redaction_summary_ref="file-review-redaction-summary:mobile-safe-review-two",
        expected_file_ref="file-ref:mobile-safe-review-two",
        expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/docs/two.md",
    ).model_copy(update={"idempotency_key": first.idempotency_key})

    report = audit_mobile_review_approval_records([first, second])

    assert report.status == MobileApprovalAuditStatus.failed
    assert "MOBILE_APPROVAL_AUDIT_DUPLICATE_IDEMPOTENCY_MISMATCH" in report.reason_codes


def test_mobile_approval_audit_rejects_authority_extra_fields() -> None:
    record = _record().model_copy(
        update={
            "context_injection_enabled": True,
            "memory_write_enabled": True,
            "export_enabled": True,
            "execution_enabled": True,
        }
    )

    report = audit_mobile_review_approval_records([record])

    assert report.status == MobileApprovalAuditStatus.failed
    assert "MOBILE_APPROVAL_AUDIT_CONTEXT_INJECTION_DENIED" in report.reason_codes
    assert "MOBILE_APPROVAL_AUDIT_MEMORY_WRITE_DENIED" in report.reason_codes
    assert "MOBILE_APPROVAL_AUDIT_EXPORT_DENIED" in report.reason_codes
    assert "MOBILE_APPROVAL_AUDIT_EXECUTION_DENIED" in report.reason_codes
    assert report.context_or_execution_authority_found is True
    assert report.execution_performed is False
