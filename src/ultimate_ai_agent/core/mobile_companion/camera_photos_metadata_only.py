from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


CAMERA_PHOTOS_METADATA_ONLY_DOCS = [
    "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_CONTRACT.md",
    "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_POLICY.md",
    "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_AUTHORITY_BOUNDARY.md",
    "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_RECEIPT_PLAN.md",
    "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_NON_GOALS.md",
    "docs/mobile/M103_TO_M104_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class CameraPhotosMediaClass(str, Enum):
    camera = "camera"
    photos = "photos"


class CameraPhotosMetadataOnlyStatus(str, Enum):
    contract_only = "contract_only"


class _CameraPhotosMetadataOnlyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CameraPhotosMetadataOnlyPolicy(_CameraPhotosMetadataOnlyModel):
    policy_ref: str = "camera-photos-metadata-only-policy:m103"
    contract_only: bool = True
    metadata_only_required: bool = True
    camera_photos_default_off_required: bool = True
    safe_metadata_refs_required: bool = True
    raw_media_denied_required: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    camera_runtime_access_enabled: bool = False
    photo_library_runtime_access_enabled: bool = False
    image_capture_enabled: bool = False
    video_capture_enabled: bool = False
    raw_media_content_enabled: bool = False
    exif_precise_location_enabled: bool = False
    face_recognition_enabled: bool = False
    ocr_enabled: bool = False
    media_export_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_media_collection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class CameraPhotosMetadataContract(_CameraPhotosMetadataOnlyModel):
    metadata_contract_ref: str
    media_class: CameraPhotosMediaClass
    safe_media_ref: str
    safe_metadata_ref: str
    safe_label: str
    safe_purpose_summary: str
    metadata_only: bool = True
    default_off: bool = True
    exact_scope_required: bool = True
    consent_required: bool = True
    revocable: bool = True
    audit_required: bool = True
    camera_runtime_access_enabled: bool = False
    photo_library_runtime_access_enabled: bool = False
    image_capture_enabled: bool = False
    video_capture_enabled: bool = False
    raw_media_content_enabled: bool = False
    raw_absolute_path_enabled: bool = False
    exif_precise_location_enabled: bool = False
    face_recognition_enabled: bool = False
    ocr_enabled: bool = False
    media_export_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.metadata_contract_ref, "metadata_contract_ref"),
            (self.safe_media_ref, "safe_media_ref"),
            (self.safe_metadata_ref, "safe_metadata_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_label)
        _validate_safe_payload(self.safe_purpose_summary)
        return self


class CameraPhotosMetadataOnlyReport(_CameraPhotosMetadataOnlyModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: CameraPhotosMetadataOnlyStatus = (
        CameraPhotosMetadataOnlyStatus.contract_only
    )
    contract_only: bool = True
    metadata_only: bool = True
    camera_photos_default_off: bool = True
    safe_metadata_refs_required: bool = True
    raw_media_denied: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    metadata_contracts: list[CameraPhotosMetadataContract]
    camera_runtime_access_enabled: bool = False
    photo_library_runtime_access_enabled: bool = False
    image_capture_enabled: bool = False
    video_capture_enabled: bool = False
    raw_media_content_enabled: bool = False
    exif_precise_location_enabled: bool = False
    face_recognition_enabled: bool = False
    ocr_enabled: bool = False
    media_export_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_media_collection_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_camera_photos_metadata_only_report(
    policy: CameraPhotosMetadataOnlyPolicy | None = None,
) -> CameraPhotosMetadataOnlyReport:
    active_policy = validate_camera_photos_metadata_only_policy(
        policy or CameraPhotosMetadataOnlyPolicy()
    )
    metadata_contracts = _default_camera_photos_metadata_contracts()
    report = CameraPhotosMetadataOnlyReport(
        report_ref="camera-photos-metadata-only-report:m103",
        baseline_ref="baseline:v1.6.0",
        actor_ref="actor:camera-photos-metadata-reviewer",
        contract_only=active_policy.contract_only,
        metadata_contracts=metadata_contracts,
        side_effects_performed=[],
        reason_codes=[
            "M103_CAMERA_PHOTOS_METADATA_ONLY",
            "M103_SAFE_METADATA_REFS_REQUIRED",
            "M103_RAW_MEDIA_DENIED",
            "M103_NO_CAMERA_OR_PHOTO_RUNTIME_ACCESS",
            "M103_NO_NATIVE_PERMISSION_PROMPT",
            "M104_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M103 defines camera and photos metadata-only contracts for future "
            "review. It adds no camera runtime access, photo library runtime "
            "access, image capture, video capture, raw media content, precise "
            "EXIF location, face recognition, OCR, media export, native "
            "permission prompt, background media collection, backend routes, "
            "Control Center controls, dependencies, memory writes, context "
            "injection, execution, M104 work, or production authority."
        ),
    )
    return validate_camera_photos_metadata_only_report(report)


def validate_camera_photos_metadata_only_policy(
    policy: CameraPhotosMetadataOnlyPolicy,
) -> CameraPhotosMetadataOnlyPolicy:
    validated = CameraPhotosMetadataOnlyPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M103_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M103_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m103_metadata(validated.metadata)
    return validated


def validate_camera_photos_metadata_contract(
    contract: CameraPhotosMetadataContract,
) -> CameraPhotosMetadataContract:
    payload = _model_payload(contract)
    for field_name, reason in _M103_CONTRACT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, CameraPhotosMetadataContract):
        raise ValueError("SECRET_LIKE_M103_MEDIA_CONTENT_DENIED")
    validated = CameraPhotosMetadataContract.model_validate(payload)
    for field_name, reason in _M103_CONTRACT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M103_CONTRACT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m103_metadata(validated.metadata)
    return validated


def validate_camera_photos_metadata_only_report(
    report: CameraPhotosMetadataOnlyReport,
) -> CameraPhotosMetadataOnlyReport:
    payload = _model_payload(report)
    for field_name, reason in _M103_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, CameraPhotosMetadataOnlyReport):
        raise ValueError("SECRET_LIKE_M103_MEDIA_CONTENT_DENIED")
    validated = CameraPhotosMetadataOnlyReport.model_validate(payload)
    for field_name, reason in _M103_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M103_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != CameraPhotosMetadataOnlyStatus.contract_only:
        raise ValueError("M103_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_metadata_contracts(validated.metadata_contracts)
    _validate_m103_metadata(validated.metadata)
    return validated


def _default_camera_photos_metadata_contracts() -> list[CameraPhotosMetadataContract]:
    return [
        CameraPhotosMetadataContract(
            metadata_contract_ref="camera-photos-metadata-contract:m103:camera",
            media_class=CameraPhotosMediaClass.camera,
            safe_media_ref="safe-media-ref:m103:camera-placeholder",
            safe_metadata_ref="safe-media-metadata:m103:camera-placeholder",
            safe_label="Camera metadata contract",
            safe_purpose_summary="Future review of safe camera metadata refs only.",
        ),
        CameraPhotosMetadataContract(
            metadata_contract_ref="camera-photos-metadata-contract:m103:photos",
            media_class=CameraPhotosMediaClass.photos,
            safe_media_ref="safe-media-ref:m103:photos-placeholder",
            safe_metadata_ref="safe-media-metadata:m103:photos-placeholder",
            safe_label="Photos metadata contract",
            safe_purpose_summary="Future review of safe photos metadata refs only.",
        ),
    ]


def _validate_metadata_contracts(contracts: list[CameraPhotosMetadataContract]) -> None:
    if not contracts:
        raise ValueError("M103_METADATA_CONTRACT_REQUIRED")
    seen_metadata_refs: set[str] = set()
    seen_classes: set[CameraPhotosMediaClass] = set()
    for contract in contracts:
        validated = validate_camera_photos_metadata_contract(contract)
        if validated.safe_metadata_ref in seen_metadata_refs:
            raise ValueError("M103_SAFE_METADATA_REF_DUPLICATE")
        seen_metadata_refs.add(validated.safe_metadata_ref)
        seen_classes.add(validated.media_class)
    if seen_classes != {CameraPhotosMediaClass.camera, CameraPhotosMediaClass.photos}:
        raise ValueError("M103_CAMERA_AND_PHOTOS_METADATA_CONTRACTS_REQUIRED")


def _validate_m103_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M103_MEDIA_CONTENT_DENIED") from exc


_M103_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("metadata_only_required", "M103_METADATA_ONLY_REQUIRED"),
    ("camera_photos_default_off_required", "M103_DEFAULT_OFF_REQUIRED"),
    ("safe_metadata_refs_required", "M103_SAFE_METADATA_REFS_REQUIRED"),
    ("raw_media_denied_required", "M103_RAW_MEDIA_DENIED_REQUIRED"),
    ("consent_required", "M103_CONSENT_REQUIRED"),
    ("revocation_required", "M103_REVOCATION_REQUIRED"),
    ("audit_required", "M103_AUDIT_REQUIRED"),
]

_M103_DENIALS = [
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
]

_M103_CONTRACT_REQUIRED_TRUE = [
    ("metadata_only", "M103_METADATA_ONLY_REQUIRED"),
    ("default_off", "M103_DEFAULT_OFF_REQUIRED"),
    ("exact_scope_required", "M103_EXACT_SCOPE_REQUIRED"),
    ("consent_required", "M103_CONSENT_REQUIRED"),
    ("revocable", "M103_REVOCATION_REQUIRED"),
    ("audit_required", "M103_AUDIT_REQUIRED"),
]

_M103_CONTRACT_DENIALS = [
    ("camera_runtime_access_enabled", "CAMERA_RUNTIME_ACCESS_DENIED"),
    ("photo_library_runtime_access_enabled", "PHOTO_LIBRARY_RUNTIME_ACCESS_DENIED"),
    ("image_capture_enabled", "IMAGE_CAPTURE_DENIED"),
    ("video_capture_enabled", "VIDEO_CAPTURE_DENIED"),
    ("raw_media_content_enabled", "RAW_MEDIA_CONTENT_DENIED"),
    ("raw_absolute_path_enabled", "RAW_ABSOLUTE_PATH_DENIED"),
    ("exif_precise_location_enabled", "EXIF_PRECISE_LOCATION_DENIED"),
    ("face_recognition_enabled", "FACE_RECOGNITION_DENIED"),
    ("ocr_enabled", "OCR_DENIED"),
    ("media_export_enabled", "MEDIA_EXPORT_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M103_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("metadata_only", "M103_METADATA_ONLY_REQUIRED"),
    ("camera_photos_default_off", "M103_DEFAULT_OFF_REQUIRED"),
    ("safe_metadata_refs_required", "M103_SAFE_METADATA_REFS_REQUIRED"),
    ("raw_media_denied", "M103_RAW_MEDIA_DENIED_REQUIRED"),
    ("consent_required", "M103_CONSENT_REQUIRED"),
    ("revocation_required", "M103_REVOCATION_REQUIRED"),
    ("audit_required", "M103_AUDIT_REQUIRED"),
]

_M103_REPORT_DENIALS = [
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
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
