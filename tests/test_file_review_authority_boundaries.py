import pytest

from ultimate_ai_agent.core.file_review import (
    FileReviewDecisionStatus,
    FileReviewWorkflowPolicy,
    build_file_review_packet,
    evaluate_file_review_packet,
)
from ultimate_ai_agent.core.tools.runtime import (
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewStatus,
)


def _packet(**overrides):
    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:authority",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:authority",
        safe_path_ref="filesystem-preview-path:safe-root_authority/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    packet = build_file_review_packet(
        preview_output=preview,
        actor_ref="user:authority",
        request_ref="file-review-request:authority",
        safe_summary="Review a redacted preview packet.",
    )
    return packet.model_copy(update=overrides) if overrides else packet


@pytest.mark.parametrize(
    "refs,reason",
    [
        (["model-output:abc"], "FILE_REVIEW_MODEL_OUTPUT_NOT_AUTHORITY"),
        (["memory:abc"], "FILE_REVIEW_MEMORY_REF_NOT_AUTHORITY"),
        (["context-pack:abc"], "FILE_REVIEW_CONTEXT_REF_NOT_AUTHORITY"),
        (["tool-intent:abc"], "FILE_REVIEW_TOOL_INTENT_REF_NOT_AUTHORITY"),
        (["approval:abc"], "FILE_REVIEW_APPROVAL_REF_NOT_AUTHORITY"),
        (["openwebui-output:abc"], "FILE_REVIEW_OPENWEBUI_OUTPUT_NOT_AUTHORITY"),
        (["control-center-preview:abc"], "FILE_REVIEW_CONTROL_CENTER_PREVIEW_NOT_AUTHORITY"),
    ],
)
def test_non_authoritative_refs_cannot_grant_file_review_authority(refs, reason):
    packet = _packet(authority_refs=refs)

    decision = evaluate_file_review_packet(packet)

    assert decision.status == FileReviewDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.raw_file_access_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False


@pytest.mark.parametrize(
    "field_name,reason",
    [
        ("raw_file_access_enabled", "FILE_REVIEW_RAW_FILE_ACCESS_DENIED"),
        ("context_proposal_enabled", "FILE_REVIEW_CONTEXT_PROPOSAL_DENIED"),
        ("context_injection_enabled", "FILE_REVIEW_CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "FILE_REVIEW_MEMORY_WRITE_DENIED"),
        ("export_enabled", "FILE_REVIEW_EXPORT_DENIED"),
        ("execution_enabled", "FILE_REVIEW_EXECUTION_DENIED"),
        ("approval_capture_enabled", "FILE_REVIEW_APPROVAL_CAPTURE_DENIED"),
        ("approval_persistence_enabled", "FILE_REVIEW_APPROVAL_PERSISTENCE_DENIED"),
        ("control_center_surface_enabled", "FILE_REVIEW_CONTROL_CENTER_SURFACE_DENIED"),
        ("backend_routes_enabled", "FILE_REVIEW_BACKEND_ROUTES_DENIED"),
    ],
)
def test_policy_denies_future_authority_flags(field_name, reason):
    with pytest.raises(ValueError, match=reason):
        FileReviewWorkflowPolicy(**{field_name: True})


def test_safe_review_packet_does_not_create_context_memory_export_or_execution_authority():
    decision = evaluate_file_review_packet(_packet())

    assert decision.status == FileReviewDecisionStatus.packet_valid_for_review
    assert decision.review_allowed is False
    assert decision.packet_valid_for_review is True
    assert decision.raw_file_access_authorized is False
    assert decision.context_proposal_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
