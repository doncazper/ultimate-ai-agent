from datetime import timedelta
import json

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileReviewApprovalCaptureDecisionStatus,
    MobileReviewApprovalDecisionKind,
    MobileReviewApprovalStore,
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


def test_mobile_review_approval_capture_persists_safe_review_only_record() -> None:
    request = _request()

    decision = capture_mobile_review_approval(request, current_time=utc_now())

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.approved_for_mobile_review_only
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.review_only is True
    assert decision.record is not None
    assert decision.record.review_packet_ref == request.review_packet_ref
    assert decision.record.mobile_surface_ref == request.mobile_surface_ref
    assert decision.record.preview_result_ref == request.preview_result_ref
    assert decision.record.redaction_summary_ref == request.redaction_summary_ref
    assert decision.raw_file_access_authorized is False
    assert decision.context_proposal_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
    dumped = decision.model_dump(mode="json")
    assert "raw_content" not in dumped
    assert "full_file_content" not in dumped
    assert "unredacted_preview" not in dumped
    assert "absolute_path" not in dumped


def test_mobile_review_denial_capture_persists_safe_denial_record() -> None:
    decision = capture_mobile_review_approval(
        _request(decision=MobileReviewApprovalDecisionKind.deny_review_only),
        current_time=utc_now(),
    )

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.denied_for_mobile_review
    assert decision.captured is True
    assert decision.persisted is True
    assert decision.record is not None
    assert decision.record.decision == MobileReviewApprovalDecisionKind.deny_review_only
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"actor_ref": "user:other"}, "MOBILE_REVIEW_APPROVAL_CAPTURE_ACTOR_MISMATCH"),
        (
            {"mobile_surface_ref": "ccc-ios-review-surface:other"},
            "MOBILE_REVIEW_APPROVAL_CAPTURE_SURFACE_MISMATCH",
        ),
        (
            {"review_packet_ref": "file-review-packet:other"},
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PACKET_MISMATCH",
        ),
        (
            {"preview_result_ref": "redacted-file-preview-output:other"},
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PREVIEW_RESULT_MISMATCH",
        ),
        (
            {"redaction_summary_ref": "file-review-redaction-summary:other"},
            "MOBILE_REVIEW_APPROVAL_CAPTURE_REDACTION_SUMMARY_MISMATCH",
        ),
        ({"file_ref": "file-ref:other"}, "MOBILE_REVIEW_APPROVAL_CAPTURE_FILE_REF_MISMATCH"),
        (
            {"safe_path_ref": "filesystem-preview-path:safe-root_mobile/docs/other.md"},
            "MOBILE_REVIEW_APPROVAL_CAPTURE_PATH_REF_MISMATCH",
        ),
        ({"approval_ref": "approval_test_mobile_m49"}, "MOBILE_REVIEW_APPROVAL_TEST_REF_DENIED"),
        ({"expires_at": utc_now() - timedelta(minutes=1)}, "MOBILE_REVIEW_APPROVAL_CAPTURE_EXPIRED"),
        ({"revoked_at": utc_now()}, "MOBILE_REVIEW_APPROVAL_CAPTURE_REVOKED"),
        (
            {
                "replay_nonce": "mobile-review-replay:1",
                "used_replay_nonces": ["mobile-review-replay:1"],
            },
            "MOBILE_REVIEW_APPROVAL_CAPTURE_REPLAY_DETECTED",
        ),
    ],
)
def test_mobile_review_capture_denies_binding_lifecycle_and_test_refs(override, reason) -> None:
    request = _request()
    if "approval_ref" in override and str(override["approval_ref"]).startswith("approval_test_"):
        request = request.model_copy(update=override)
    else:
        request = _request(**override)

    decision = capture_mobile_review_approval(request, current_time=utc_now())

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.captured is False
    assert decision.persisted is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("raw_file_access_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_ACCESS_DENIED"),
        ("raw_content_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED"),
        ("full_file_content_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_FULL_FILE_CONTENT_DENIED"),
        ("unredacted_preview_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_UNREDACTED_PREVIEW_DENIED"),
        ("context_proposal_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_PROPOSAL_DENIED"),
        ("context_injection_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_MEMORY_WRITE_DENIED"),
        ("export_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_EXPORT_DENIED"),
        ("execution_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_EXECUTION_DENIED"),
        ("approval_execution_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_APPROVAL_EXECUTION_DENIED"),
        ("mobile_sensor_access_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_SENSOR_DENIED"),
        ("background_collection_enabled", "MOBILE_REVIEW_APPROVAL_CAPTURE_BACKGROUND_DENIED"),
    ],
)
def test_mobile_review_model_copy_mutated_flags_are_revalidated(flag, reason) -> None:
    request = _request().model_copy(update={flag: True})

    decision = capture_mobile_review_approval(request, current_time=utc_now())

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.rejected
    assert reason in decision.reason_codes
    assert decision.execution_performed is False


def test_mobile_review_secret_metadata_is_denied_without_echoing_secret() -> None:
    request = _request().model_copy(update={"metadata": {"api_key": "abc123supersecret"}})

    decision = capture_mobile_review_approval(request, current_time=utc_now())

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.rejected
    assert "MOBILE_REVIEW_APPROVAL_CAPTURE_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "abc123supersecret" not in decision.safe_message
    assert "abc123supersecret" not in str(decision.model_dump(mode="json"))


def test_mobile_review_approval_store_writes_safe_jsonl_only(tmp_path) -> None:
    store_path = tmp_path / "mobile_review_approvals.jsonl"
    store = MobileReviewApprovalStore(store_path)
    request = _request()

    decision = capture_mobile_review_approval(request, store=store, current_time=utc_now())

    assert decision.persisted is True
    payload = json.loads(store_path.read_text(encoding="utf-8").strip())
    assert payload["review_packet_ref"] == request.review_packet_ref
    assert "raw_content" not in payload
    assert "full_file_content" not in payload
    assert "unredacted_preview" not in payload
    assert "absolute_path" not in payload
    assert "/Users/" not in store_path.read_text(encoding="utf-8")


def test_mobile_review_store_rejects_conflicting_replay(tmp_path) -> None:
    store = MobileReviewApprovalStore(tmp_path / "mobile_review_approvals.jsonl")
    first = _request()
    changed = _request(file_ref="file-ref:changed", expected_file_ref="file-ref:changed")

    capture_mobile_review_approval(first, store=store, current_time=utc_now())
    decision = capture_mobile_review_approval(changed, store=store, current_time=utc_now())

    assert decision.status == MobileReviewApprovalCaptureDecisionStatus.rejected
    assert decision.persisted is False
    assert "MOBILE_REVIEW_APPROVAL_CAPTURE_REPLAY_MISMATCH" in decision.reason_codes


def test_mobile_review_record_model_copy_raw_extra_is_denied(tmp_path) -> None:
    store = MobileReviewApprovalStore(tmp_path / "mobile_review_approvals.jsonl")
    request = _request()
    decision = capture_mobile_review_approval(request, current_time=utc_now())
    assert decision.record is not None
    record = decision.record.model_copy(update={"raw_content": "secret raw text"})

    replay = store.persist(record)

    assert replay.status == MobileReviewApprovalCaptureDecisionStatus.rejected
    assert "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED" in replay.reason_codes
    assert "secret raw text" not in replay.safe_message
