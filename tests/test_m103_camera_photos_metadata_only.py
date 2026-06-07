import pytest

from ultimate_ai_agent.core.mobile_companion import (
    CameraPhotosMediaClass,
    CameraPhotosMetadataOnlyPolicy,
    CameraPhotosMetadataOnlyStatus,
    build_camera_photos_metadata_only_report,
    validate_camera_photos_metadata_contract,
    validate_camera_photos_metadata_only_policy,
    validate_camera_photos_metadata_only_report,
)


def test_m103_camera_photos_contract_is_metadata_only() -> None:
    report = build_camera_photos_metadata_only_report()

    assert report.status == CameraPhotosMetadataOnlyStatus.contract_only
    assert report.contract_only is True
    assert report.metadata_only is True
    assert report.camera_photos_default_off is True
    assert report.safe_metadata_refs_required is True
    assert report.raw_media_denied is True
    assert report.consent_required is True
    assert report.revocation_required is True
    assert report.audit_required is True
    assert report.camera_runtime_access_enabled is False
    assert report.photo_library_runtime_access_enabled is False
    assert report.image_capture_enabled is False
    assert report.video_capture_enabled is False
    assert report.raw_media_content_enabled is False
    assert report.exif_precise_location_enabled is False
    assert report.face_recognition_enabled is False
    assert report.ocr_enabled is False
    assert report.media_export_enabled is False
    assert report.native_permission_prompt_enabled is False
    assert report.background_media_collection_enabled is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M103_CAMERA_PHOTOS_METADATA_ONLY",
        "M103_SAFE_METADATA_REFS_REQUIRED",
        "M103_RAW_MEDIA_DENIED",
        "M103_NO_CAMERA_OR_PHOTO_RUNTIME_ACCESS",
        "M103_NO_NATIVE_PERMISSION_PROMPT",
        "M104_REMAINS_FUTURE",
    ]


def test_m103_metadata_contracts_are_safe_refs_only() -> None:
    report = build_camera_photos_metadata_only_report()

    assert {contract.media_class for contract in report.metadata_contracts} == {
        CameraPhotosMediaClass.camera,
        CameraPhotosMediaClass.photos,
    }
    for contract in report.metadata_contracts:
        assert contract.metadata_only is True
        assert contract.safe_metadata_ref.startswith("safe-media-metadata:")
        assert contract.raw_media_content_enabled is False
        assert contract.raw_absolute_path_enabled is False
        assert contract.exif_precise_location_enabled is False
        assert contract.face_recognition_enabled is False
        assert contract.ocr_enabled is False
        assert contract.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("camera_runtime_access_enabled", "CAMERA_RUNTIME_ACCESS_DENIED"),
        ("photo_library_runtime_access_enabled", "PHOTO_LIBRARY_RUNTIME_ACCESS_DENIED"),
        ("image_capture_enabled", "IMAGE_CAPTURE_DENIED"),
        ("video_capture_enabled", "VIDEO_CAPTURE_DENIED"),
        ("raw_media_content_enabled", "RAW_MEDIA_CONTENT_DENIED"),
        ("exif_precise_location_enabled", "EXIF_PRECISE_LOCATION_DENIED"),
        ("face_recognition_enabled", "FACE_RECOGNITION_DENIED"),
        ("ocr_enabled", "OCR_DENIED"),
        ("media_export_enabled", "MEDIA_EXPORT_DENIED"),
        ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
        ("background_media_collection_enabled", "BACKGROUND_MEDIA_COLLECTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m103_policy_denies_camera_photos_runtime_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_camera_photos_metadata_only_policy(
            CameraPhotosMetadataOnlyPolicy(**{field: True})
        )


def test_m103_metadata_contract_denies_raw_media_and_unsafe_analysis() -> None:
    report = build_camera_photos_metadata_only_report()
    contract = report.metadata_contracts[0]

    for update, reason in [
        ({"metadata_only": False}, "M103_METADATA_ONLY_REQUIRED"),
        ({"raw_media_content_enabled": True}, "RAW_MEDIA_CONTENT_DENIED"),
        ({"raw_absolute_path_enabled": True}, "RAW_ABSOLUTE_PATH_DENIED"),
        ({"exif_precise_location_enabled": True}, "EXIF_PRECISE_LOCATION_DENIED"),
        ({"face_recognition_enabled": True}, "FACE_RECOGNITION_DENIED"),
        ({"ocr_enabled": True}, "OCR_DENIED"),
        ({"side_effects_performed": ["read photo bytes"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_camera_photos_metadata_contract(contract.model_copy(update=update))


def test_m103_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_camera_photos_metadata_only_report()

    for update, reason in [
        ({"camera_runtime_access_enabled": True}, "CAMERA_RUNTIME_ACCESS_DENIED"),
        ({"photo_library_runtime_access_enabled": True}, "PHOTO_LIBRARY_RUNTIME_ACCESS_DENIED"),
        ({"image_capture_enabled": True}, "IMAGE_CAPTURE_DENIED"),
        ({"video_capture_enabled": True}, "VIDEO_CAPTURE_DENIED"),
        ({"raw_media_content_enabled": True}, "RAW_MEDIA_CONTENT_DENIED"),
        ({"exif_precise_location_enabled": True}, "EXIF_PRECISE_LOCATION_DENIED"),
        ({"face_recognition_enabled": True}, "FACE_RECOGNITION_DENIED"),
        ({"ocr_enabled": True}, "OCR_DENIED"),
        ({"media_export_enabled": True}, "MEDIA_EXPORT_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["captured media"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_camera_photos_metadata_only_report(report.model_copy(update=update))


def test_m103_rejects_duplicate_metadata_refs_and_secret_metadata() -> None:
    report = build_camera_photos_metadata_only_report()
    duplicate = report.model_copy(
        update={"metadata_contracts": [report.metadata_contracts[0], report.metadata_contracts[0]]}
    )

    with pytest.raises(ValueError, match="M103_SAFE_METADATA_REF_DUPLICATE"):
        validate_camera_photos_metadata_only_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M103_MEDIA_CONTENT_DENIED"):
        validate_camera_photos_metadata_only_report(
            report.model_copy(update={"metadata": {"api_key": "abc123supersecret"}})
        )
