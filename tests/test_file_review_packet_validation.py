from typing import Any
import pytest

from ultimate_ai_agent.core.file_review import (
    FileReviewRedactionVerification,
    build_file_review_packet,
    evaluate_file_review_packet,
)
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)


def _preview_output(**overrides: Any) -> Any:
    data = {
        "output_ref": "redacted-file-preview-output:packet",
        "status": RedactedFilePreviewStatus.preview_generated,
        "root_ref": "safe-root:packet",
        "safe_path_ref": "filesystem-preview-path:safe-root_packet/docs/review.md",
        "redacted_preview": "Safe redacted preview.",
        "redaction_summary": FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        "preview_truncated": False,
        "preview_limit_bytes": 4096,
        "file_size_bytes": 64,
    }
    data.update(overrides)
    return RedactedFilePreviewOutput(**data)


def _packet() -> Any:
    return build_file_review_packet(
        preview_output=_preview_output(),
        actor_ref="user:packet",
        request_ref="file-review-request:packet",
        file_ref="file-ref:packet-review",
        safe_summary="Review a redacted preview packet.",
    )


@pytest.mark.parametrize(
    "field_name,reason",
    [
        ("raw_content", "FILE_REVIEW_RAW_CONTENT_DENIED"),
        ("full_file_content", "FILE_REVIEW_FULL_FILE_CONTENT_DENIED"),
        ("unredacted_preview", "FILE_REVIEW_UNREDACTED_PREVIEW_DENIED"),
        ("raw_absolute_path", "FILE_REVIEW_RAW_ABSOLUTE_PATH_DENIED"),
    ],
)
def test_evaluator_revalidates_model_copy_mutated_raw_packet_fields(field_name: str, reason: str) -> None:
    packet = _packet().model_copy(update={field_name: "/Users/sam/private/raw secret"})

    decision = evaluate_file_review_packet(packet)

    assert decision.review_allowed is False
    assert reason in decision.reason_codes
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


@pytest.mark.parametrize(
    "field_name,reason",
    [
        ("context_injection_enabled", "FILE_REVIEW_CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "FILE_REVIEW_MEMORY_WRITE_DENIED"),
        ("export_enabled", "FILE_REVIEW_EXPORT_DENIED"),
        ("execution_enabled", "FILE_REVIEW_EXECUTION_DENIED"),
    ],
)
def test_evaluator_revalidates_model_copy_mutated_authority_flags(field_name: str, reason: str) -> None:
    packet = _packet().model_copy(update={field_name: True})

    decision = evaluate_file_review_packet(packet)

    assert decision.review_allowed is False
    assert reason in decision.reason_codes
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


def test_missing_redaction_summary_is_denied() -> None:
    verification = FileReviewRedactionVerification(redaction_summary_ref="file-review-redaction-summary:packet")
    packet = _packet().model_copy(update={"redaction_verification": verification.model_copy(update={"redaction_summary_required": False})})

    decision = evaluate_file_review_packet(packet)

    assert decision.review_allowed is False
    assert "FILE_REVIEW_REDACTION_SUMMARY_REQUIRED" in decision.reason_codes


def test_secret_like_metadata_is_denied_without_echoing_secret() -> None:
    packet = _packet().model_copy(update={"metadata": {"token": "abc123supersecret"}})

    decision = evaluate_file_review_packet(packet)

    assert decision.review_allowed is False
    assert "FILE_REVIEW_SECRET_METADATA_DENIED" in decision.reason_codes
    assert "abc123supersecret" not in decision.safe_message
    assert "abc123supersecret" not in str(decision.model_dump())
