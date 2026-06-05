import pytest

from ultimate_ai_agent.core.media import (
    MediaInspectionKind,
    SafeMediaMetadataPolicy,
    SafeMediaMetadataRequest,
    SafeMediaMetadataStatus,
    inspect_safe_media_metadata,
    validate_safe_media_metadata_policy,
    validate_safe_media_metadata_request,
)


def _request(**overrides):
    data = {
        "request_ref": "media-metadata-request:m54-sample",
        "media_ref": "media:m54-sample",
        "safe_path_ref": "safe-path:m54-sample.jpg",
        "inspection_kind": MediaInspectionKind.image_metadata,
        "declared_media_type": "image/jpeg",
        "declared_byte_size": 2048,
        "metadata_refs": ["source:fixture/m54-sample"],
    }
    data.update(overrides)
    return SafeMediaMetadataRequest(**data)


def test_safe_media_metadata_inspection_returns_metadata_only() -> None:
    decision = inspect_safe_media_metadata(_request())

    assert decision.status == SafeMediaMetadataStatus.metadata_ready
    assert decision.metadata_ready is True
    assert decision.raw_media_returned is False
    assert decision.raw_media_stored is False
    assert decision.original_file_modified is False
    assert decision.ocio_transform_performed is False
    assert decision.ai_gamut_expansion_performed is False
    assert decision.model_call_performed is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.side_effects_performed == []
    assert decision.receipt_plan.raw_media_stored is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("raw_media_requested", "RAW_MEDIA_EXPORT_DENIED"),
        ("full_file_read_requested", "FULL_FILE_READ_DENIED"),
        ("file_mutation_requested", "FILE_MUTATION_DENIED"),
        ("original_overwrite_requested", "ORIGINAL_OVERWRITE_DENIED"),
        ("ocio_transform_requested", "OCIO_TRANSFORM_DENIED"),
        ("ai_gamut_expansion_requested", "AI_GAMUT_EXPANSION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("contains_secret_like_metadata", "SECRET_LIKE_METADATA_DENIED"),
    ],
)
def test_media_metadata_request_rejects_raw_mutating_transform_or_model_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_safe_media_metadata_request(_request(**{field: True}))


def test_media_metadata_revalidates_model_copy_mutated_flags() -> None:
    request = _request().model_copy(
        update={
            "raw_media_requested": True,
            "full_file_read_requested": True,
            "model_call_requested": True,
        }
    )

    with pytest.raises(ValueError, match="RAW_MEDIA_EXPORT_DENIED"):
        inspect_safe_media_metadata(request)


def test_unsupported_media_type_is_denied_without_raw_output() -> None:
    decision = inspect_safe_media_metadata(
        _request(
            request_ref="media-metadata-request:m54-unsupported",
            media_ref="media:m54-unsupported",
            declared_media_type="application/octet-stream",
        )
    )

    assert decision.status == SafeMediaMetadataStatus.denied
    assert decision.metadata_ready is False
    assert decision.raw_media_returned is False
    assert "UNSUPPORTED_MEDIA_TYPE_DENIED" in decision.reason_codes


def test_safe_media_metadata_policy_rejects_runtime_authority_flags() -> None:
    policy = SafeMediaMetadataPolicy(
        raw_media_export_enabled=True,
        full_file_read_enabled=True,
        file_mutation_enabled=True,
        ocio_transform_enabled=True,
        ai_gamut_expansion_enabled=True,
        model_call_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="RAW_MEDIA_EXPORT_DENIED"):
        validate_safe_media_metadata_policy(policy)
