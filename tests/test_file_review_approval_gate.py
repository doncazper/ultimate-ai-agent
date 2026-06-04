from datetime import timedelta

import pytest

from ultimate_ai_agent.core.file_review import (
    FileReviewDecisionStatus,
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


def _packet():
    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:approval",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:approval",
        safe_path_ref="filesystem-preview-path:safe-root_approval/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    return build_file_review_packet(
        preview_output=preview,
        actor_ref="user:approval",
        request_ref="file-review-request:approval",
        file_ref="file-ref:approval-review",
        safe_summary="Review a redacted preview packet.",
    )


def _approval(packet, **overrides):
    data = {
        "approval_ref": "file-review-approval:approval",
        "actor_ref": "user:approval",
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


def test_approval_ref_alone_cannot_authorize_review():
    packet = _packet().model_copy(update={"approval_ref": "file-review-approval:approval"})

    decision = evaluate_file_review_gate(packet, approval=None, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert "FILE_REVIEW_APPROVAL_OBJECT_REQUIRED" in decision.reason_codes
    assert "FILE_REVIEW_APPROVAL_REF_NOT_AUTHORITY" in decision.reason_codes
    assert decision.raw_file_access_authorized is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "approval_ref",
    ["approval_test_packet", "approval_test_:packet", "approval_test_m35"],
)
def test_approval_test_refs_are_denied_at_gate(approval_ref):
    packet = _packet()
    approval = _approval(packet).model_copy(update={"approval_ref": approval_ref})

    decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert "FILE_REVIEW_APPROVAL_TEST_REF_DENIED" in decision.reason_codes
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"actor_ref": "user:other"}, "FILE_REVIEW_APPROVAL_ACTOR_MISMATCH"),
        ({"preview_result_ref": "redacted-file-preview-output:other"}, "FILE_REVIEW_APPROVAL_PREVIEW_RESULT_MISMATCH"),
        ({"redaction_summary_ref": "file-review-redaction-summary:other"}, "FILE_REVIEW_APPROVAL_REDACTION_SUMMARY_MISMATCH"),
        ({"file_ref": "file-ref:other-review"}, "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH"),
        ({"safe_path_ref": "filesystem-preview-path:safe-root_approval/docs/other.md"}, "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH"),
        ({"expires_at": utc_now() - timedelta(minutes=1)}, "FILE_REVIEW_APPROVAL_EXPIRED"),
        ({"revoked_at": utc_now()}, "FILE_REVIEW_APPROVAL_REVOKED"),
        ({"replay_nonce": "file-review-replay:1", "used_replay_nonces": ["file-review-replay:1"]}, "FILE_REVIEW_APPROVAL_REPLAY_DETECTED"),
    ],
)
def test_approval_binding_denies_mismatch_expiry_revocation_and_replay(override, reason):
    packet = _packet()
    approval = _approval(packet, **override)

    decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.review_allowed is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "source_update,reason",
    [
        ({"file_ref": "file-ref:mutated-review"}, "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH"),
        ({"safe_path_ref": "filesystem-preview-path:safe-root_approval/docs/mutated.md"}, "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH"),
    ],
)
def test_model_copy_mutated_packet_file_and_path_refs_are_denied(source_update, reason):
    packet = _packet()
    approval = _approval(packet)
    mutated_packet = packet.model_copy(update={"source": packet.source.model_copy(update=source_update)})

    decision = evaluate_file_review_gate(mutated_packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.review_allowed is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


def test_secret_like_approval_metadata_is_denied_without_echoing_secret():
    packet = _packet()
    approval = _approval(packet).model_copy(update={"metadata": {"api_key": "abc123supersecret"}})

    decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())

    assert decision.status == FileReviewDecisionStatus.denied
    assert "FILE_REVIEW_APPROVAL_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "abc123supersecret" not in decision.safe_message
    assert "abc123supersecret" not in str(decision.model_dump())
