from __future__ import annotations
from typing import Any

from ultimate_ai_agent.core.file_review import (
    FileReviewApprovalCaptureDecisionStatus,
    FileReviewApprovalDecisionKind,
    FileReviewApprovalRecord,
    build_file_review_packet,
)
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)


def context_proposal_packet() -> Any:
    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:context-proposal",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:context-proposal",
        safe_path_ref="filesystem-preview-path:safe-root_context_proposal/docs/review.md",
        redacted_preview="Redacted preview only for context proposal.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=1, categories=["secret_assignment"]),
        file_size_bytes=64,
    )
    return build_file_review_packet(
        preview_output=preview,
        actor_ref="user:context-proposal",
        request_ref="file-review-request:context-proposal",
        file_ref="file-ref:context-proposal-review",
        safe_summary="Review a redacted packet for a future context proposal.",
    )


def approved_context_proposal_record(packet: Any | None = None, **overrides: Any) -> Any:
    active_packet = packet or context_proposal_packet()
    data = {
        "approval_ref": "file-review-approval-capture:context-proposal",
        "actor_ref": active_packet.source.actor_ref,
        "review_packet_ref": active_packet.review_packet_ref,
        "preview_result_ref": active_packet.source.preview_result_ref,
        "redaction_summary_ref": active_packet.redaction_verification.redaction_summary_ref,
        "file_ref": active_packet.source.file_ref,
        "safe_path_ref": active_packet.source.safe_path_ref,
        "decision": FileReviewApprovalDecisionKind.approve_review_only,
        "status": FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
        "idempotency_key": "file-review-approval-idempotency:context-proposal",
        "safe_reason": "User approved the redacted review packet for review-only follow-up.",
        "receipt_plan_ref": "file-review-approval-capture-receipt:context-proposal",
    }
    data.update(overrides)
    return FileReviewApprovalRecord(**data)


def denied_context_proposal_record(packet: Any | None = None, **overrides: Any) -> Any:
    return approved_context_proposal_record(
        packet,
        decision=FileReviewApprovalDecisionKind.deny_review_only,
        status=FileReviewApprovalCaptureDecisionStatus.denied_for_review,
        **overrides,
    )
