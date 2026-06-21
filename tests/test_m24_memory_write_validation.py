from typing import Any
import pytest

from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
    MemoryWriteDecisionStatus,
)
from ultimate_ai_agent.core.memory.provider import MemoryWriteRequest
from ultimate_ai_agent.core.memory.validation import validate_memory_export_request, validate_memory_write_request


def _safe_request(**overrides: Any) -> Any:
    payload = {
        "request_id": "mwr_m24_safe",
        "provider_ref": "local_dev_memory",
        "memory_kind": MemoryRecordKind.structured_fact,
        "memory_layer": MemoryLayer.record,
        "provider_kind": MemoryProviderKind.local_in_memory,
        "safe_summary": "Reviewed local-only memory summary with no raw content.",
        "source_refs": ["source:user-reviewed:m24"],
        "evidence_refs": ["evidence:m24"],
        "event_refs": ["event:m24"],
        "receipt_refs": ["receipt:m24"],
        "user_reviewed": True,
        "data_classification": MemoryDataClassification.internal,
        "confidence_score": 0.6,
        "trust_score": 0.5,
        "dedup_key": "reviewed-local-summary",
        "context_pack_eligible": True,
        "injection_priority": 2,
    }
    payload.update(overrides)
    return MemoryWriteRequest(**payload)


def test_m24_reviewed_safe_write_request_is_allowed_for_local_store() -> None:
    decision = validate_memory_write_request(_safe_request())

    assert decision.allowed is True
    assert decision.status == MemoryWriteDecisionStatus.allowed_for_local_store
    assert "MEMORY_RECALL_NOT_AUTHORITY" in decision.reason_codes
    assert "reviewed" in decision.safe_message.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("automatic_write", "AUTOMATIC_MEMORY_WRITE_BLOCKED"),
        ("model_output_source", "MODEL_OUTPUT_MEMORY_WRITE_BLOCKED"),
        ("local_llm_output_source", "LOCAL_LLM_OUTPUT_MEMORY_WRITE_BLOCKED"),
        ("openwebui_source", "OPENWEBUI_MEMORY_WRITE_BLOCKED"),
        ("mobile_capture_source", "MOBILE_CAPTURE_MEMORY_WRITE_BLOCKED"),
        ("tool_output_source", "TOOL_OUTPUT_MEMORY_WRITE_BLOCKED"),
        ("contains_secret_like_content", "SECRET_LIKE_MEMORY_BLOCKED"),
        ("contains_raw_prompt", "RAW_PROMPT_MEMORY_BLOCKED"),
        ("contains_raw_model_output", "RAW_MODEL_OUTPUT_MEMORY_BLOCKED"),
        ("contains_raw_file_content", "RAW_FILE_CONTENT_MEMORY_BLOCKED"),
        ("contains_raw_transcript", "RAW_TRANSCRIPT_MEMORY_BLOCKED"),
    ],
)
def test_m24_forbidden_write_sources_are_denied(field: str, reason: str) -> None:
    decision = validate_memory_write_request(_safe_request(**{field: True}))

    assert decision.allowed is False
    assert decision.status == MemoryWriteDecisionStatus.denied
    assert reason in decision.reason_codes


def test_m24_unreviewed_missing_source_or_forbidden_classification_denied() -> None:
    unreviewed = validate_memory_write_request(_safe_request(user_reviewed=False))
    missing_sources = validate_memory_write_request(_safe_request(source_refs=[]))
    forbidden = validate_memory_write_request(_safe_request(data_classification=MemoryDataClassification.forbidden))
    secret_summary = validate_memory_write_request(_safe_request(safe_summary="api_key=abc123"))
    secret_metadata = validate_memory_write_request(_safe_request(metadata={"token": "abc123"}))
    secret_ref = validate_memory_write_request(_safe_request(metadata_refs=["secret:abc123"]))
    secret_tag = validate_memory_write_request(_safe_request(tags=["password=abc123"]))

    assert unreviewed.status == MemoryWriteDecisionStatus.requires_user_review
    assert "USER_REVIEW_REQUIRED" in unreviewed.reason_codes
    assert missing_sources.status == MemoryWriteDecisionStatus.requires_evidence
    assert "SOURCE_REF_REQUIRED" in missing_sources.reason_codes
    assert forbidden.status == MemoryWriteDecisionStatus.denied
    assert "FORBIDDEN_DATA_CLASSIFICATION" in forbidden.reason_codes
    assert "SECRET_LIKE_MEMORY_BLOCKED" in secret_summary.reason_codes
    assert "SECRET_LIKE_METADATA_BLOCKED" in secret_metadata.reason_codes
    assert "SECRET_LIKE_METADATA_REF_BLOCKED" in secret_ref.reason_codes
    assert "SECRET_LIKE_TAG_BLOCKED" in secret_tag.reason_codes


def test_m24_source_refs_are_required_even_with_supplemental_refs() -> None:
    decision = validate_memory_write_request(
        _safe_request(
            source_refs=[],
            evidence_refs=["evidence:m24:supplemental"],
            event_refs=["event:m24:supplemental"],
            receipt_refs=["receipt:m24:supplemental"],
        )
    )

    assert decision.allowed is False
    assert decision.status == MemoryWriteDecisionStatus.requires_evidence
    assert "SOURCE_REF_REQUIRED" in decision.reason_codes
    assert "source_refs are required" in decision.safe_message
    assert "evidence, event, or receipt refs are required" not in decision.safe_message.lower()


def test_m24_required_write_guard_fields_exist_before_mutation_checks() -> None:
    required_guard_fields = {
        "automatic_write",
        "model_output_source",
        "local_llm_output_source",
        "openwebui_source",
        "mobile_capture_source",
        "tool_output_source",
        "contains_raw_prompt",
        "contains_raw_model_output",
        "contains_raw_file_content",
        "contains_raw_transcript",
    }

    assert required_guard_fields <= set(MemoryWriteRequest.model_fields)


def test_m24_export_raw_content_is_rejected() -> None:
    decision = validate_memory_export_request(
        {
            "request_id": "mer_m24_raw",
            "provider_ref": "local_dev_memory",
            "include_deleted": True,
            "include_raw_content": True,
            "redacted_only": False,
        }
    )

    assert decision.allowed is False
    assert decision.status == MemoryWriteDecisionStatus.denied
    assert "RAW_MEMORY_EXPORT_BLOCKED" in decision.reason_codes
