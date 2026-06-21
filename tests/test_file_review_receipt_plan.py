from typing import Any
import pytest

from ultimate_ai_agent.core.file_review import FileReviewReceiptPlan, build_file_review_packet, build_file_review_receipt_plan
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)


def _packet() -> Any:
    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:receipt",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:receipt",
        safe_path_ref="filesystem-preview-path:safe-root_receipt/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    return build_file_review_packet(
        preview_output=preview,
        actor_ref="user:receipt",
        request_ref="file-review-request:receipt",
        file_ref="file-ref:receipt-review",
        safe_summary="Review a redacted preview packet.",
    )


def test_receipt_plan_stores_refs_only_and_is_not_authority() -> None:
    packet = _packet()
    receipt_plan = build_file_review_receipt_plan(packet)

    assert receipt_plan.review_packet_ref == packet.review_packet_ref
    assert receipt_plan.preview_result_ref == packet.source.preview_result_ref
    assert receipt_plan.redaction_summary_ref == packet.redaction_verification.redaction_summary_ref
    assert receipt_plan.receipt_is_authority is False
    assert receipt_plan.raw_content_stored is False
    assert receipt_plan.unredacted_preview_stored is False
    assert receipt_plan.raw_absolute_path_stored is False
    assert receipt_plan.context_injection_performed is False
    assert receipt_plan.memory_write_performed is False
    assert receipt_plan.export_performed is False
    assert receipt_plan.execution_performed is False
    assert packet.redacted_preview not in str(receipt_plan.model_dump())


@pytest.mark.parametrize(
    "field_name",
    [
        "raw_content_stored",
        "unredacted_preview_stored",
        "raw_absolute_path_stored",
        "context_injection_performed",
        "memory_write_performed",
        "export_performed",
        "execution_performed",
        "receipt_is_authority",
    ],
)
def test_receipt_plan_rejects_authority_and_side_effect_flags(field_name: str) -> None:
    with pytest.raises(ValueError):
        FileReviewReceiptPlan(
            receipt_plan_ref="file-review-receipt-plan:unsafe",
            review_packet_ref="file-review-packet:unsafe",
            preview_result_ref="redacted-file-preview-output:unsafe",
            redaction_summary_ref="file-review-redaction-summary:unsafe",
            **{field_name: True},
        )
