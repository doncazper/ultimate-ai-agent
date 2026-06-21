import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M54_DOC_REFS = [
    "docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md",
    "docs/media/SAFE_MEDIA_METADATA_POLICY.md",
    "docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md",
    "docs/media/M54_TO_M55_BOUNDARY.md",
]
M54_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SUPPORTED_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/quicktime",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
}


class MediaInspectionKind(str, Enum):
    image_metadata = "image_metadata"
    video_metadata = "video_metadata"
    audio_metadata = "audio_metadata"


class SafeMediaMetadataStatus(str, Enum):
    metadata_ready = "metadata_ready"
    denied = "denied"


class _M54MediaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class SafeMediaMetadataPolicy(_M54MediaModel):
    policy_ref: str = "safe-media-metadata-policy:m54"
    baseline_version: str = "0.58.0"
    metadata_only: bool = True
    review_only: bool = True
    raw_media_export_enabled: bool = False
    raw_media_storage_enabled: bool = False
    full_file_read_enabled: bool = False
    file_mutation_enabled: bool = False
    original_overwrite_enabled: bool = False
    ocio_transform_enabled: bool = False
    ai_gamut_expansion_enabled: bool = False
    model_call_enabled: bool = False
    context_injection_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    production_authority_enabled: bool = False
    m55_implemented: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M54_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M54", "version:v0.58.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self) -> Any:
        _validate_m54_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m54_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class SafeMediaMetadataRequest(_M54MediaModel):
    request_ref: str
    media_ref: str
    safe_path_ref: str
    inspection_kind: MediaInspectionKind
    declared_media_type: str
    declared_byte_size: int = Field(ge=0)
    declared_dimensions: str | None = None
    declared_duration_ms: int | None = Field(default=None, ge=0)
    metadata_refs: list[str] = Field(default_factory=list)
    raw_media_requested: bool = False
    full_file_read_requested: bool = False
    file_mutation_requested: bool = False
    original_overwrite_requested: bool = False
    ocio_transform_requested: bool = False
    ai_gamut_expansion_requested: bool = False
    model_call_requested: bool = False
    context_injection_requested: bool = False
    contains_secret_like_metadata: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self) -> Any:
        _validate_m54_ref(self.request_ref, "request_ref")
        _validate_m54_ref(self.media_ref, "media_ref")
        _validate_m54_ref(self.safe_path_ref, "safe_path_ref")
        _require_nonempty(self.declared_media_type, "declared_media_type")
        for ref in self.metadata_refs:
            _validate_m54_ref(ref, "metadata_ref")
        if self.declared_dimensions:
            _require_nonempty(self.declared_dimensions, "declared_dimensions")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class SafeMediaMetadataReceiptPlan(_M54MediaModel):
    receipt_plan_ref: str
    request_ref: str
    metadata_only: bool = True
    raw_media_stored: bool = False
    original_file_modified: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    network_call_performed: bool = False
    model_call_performed: bool = False
    context_injection_performed: bool = False
    safe_summary: str = "M54 metadata-only media inspection receipt plan."
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M54", "version:v0.58.0"])

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> Any:
        _validate_m54_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m54_ref(self.request_ref, "request_ref")
        if not self.metadata_only:
            raise ValueError("METADATA_ONLY_REQUIRED")
        for field_name, reason in [
            ("raw_media_stored", "RAW_MEDIA_STORAGE_DENIED"),
            ("original_file_modified", "ORIGINAL_OVERWRITE_DENIED"),
            ("network_call_performed", "NETWORK_CALL_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        for ref in self.metadata_refs:
            _validate_m54_ref(ref, "metadata_ref")
        return self


class SafeMediaMetadataDecision(_M54MediaModel):
    decision_ref: str
    request_ref: str
    status: SafeMediaMetadataStatus
    metadata_ready: bool
    media_ref: str
    safe_path_ref: str
    declared_media_type: str
    declared_byte_size: int
    declared_dimensions: str | None = None
    declared_duration_ms: int | None = None
    reason_codes: list[str] = Field(default_factory=list)
    raw_media_returned: bool = False
    raw_media_stored: bool = False
    original_file_modified: bool = False
    ocio_transform_performed: bool = False
    ai_gamut_expansion_performed: bool = False
    model_call_performed: bool = False
    context_injection_performed: bool = False
    safe_summary: str = "M54 media metadata inspection is metadata-only."
    receipt_plan: SafeMediaMetadataReceiptPlan | None = None
    docs_refs: list[str] = Field(default_factory=lambda: list(M54_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M54", "version:v0.58.0"])

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        _validate_m54_ref(self.decision_ref, "decision_ref")
        _validate_m54_ref(self.request_ref, "request_ref")
        _validate_m54_ref(self.media_ref, "media_ref")
        _validate_m54_ref(self.safe_path_ref, "safe_path_ref")
        if self.status == SafeMediaMetadataStatus.denied and self.metadata_ready:
            raise ValueError("DENIED_MEDIA_METADATA_MUST_NOT_BE_READY")
        if self.status == SafeMediaMetadataStatus.metadata_ready and not self.metadata_ready:
            raise ValueError("METADATA_READY_STATUS_REQUIRED")
        for field_name, reason in [
            ("raw_media_returned", "RAW_MEDIA_EXPORT_DENIED"),
            ("raw_media_stored", "RAW_MEDIA_STORAGE_DENIED"),
            ("original_file_modified", "ORIGINAL_OVERWRITE_DENIED"),
            ("ocio_transform_performed", "OCIO_TRANSFORM_DENIED"),
            ("ai_gamut_expansion_performed", "AI_GAMUT_EXPANSION_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m54_ref(ref, "metadata_ref")
        for reason in self.reason_codes:
            _require_nonempty(reason, "reason_code")
        return self


def validate_safe_media_metadata_policy(policy: SafeMediaMetadataPolicy) -> SafeMediaMetadataPolicy:
    validated = SafeMediaMetadataPolicy.model_validate(policy.model_dump())
    if not validated.metadata_only or not validated.review_only:
        raise ValueError("METADATA_ONLY_REQUIRED")
    for field_name, reason in [
        ("raw_media_export_enabled", "RAW_MEDIA_EXPORT_DENIED"),
        ("raw_media_storage_enabled", "RAW_MEDIA_STORAGE_DENIED"),
        ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
        ("file_mutation_enabled", "FILE_MUTATION_DENIED"),
        ("original_overwrite_enabled", "ORIGINAL_OVERWRITE_DENIED"),
        ("ocio_transform_enabled", "OCIO_TRANSFORM_DENIED"),
        ("ai_gamut_expansion_enabled", "AI_GAMUT_EXPANSION_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("m55_implemented", "M55_IMPLEMENTATION_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_safe_media_metadata_request(request: SafeMediaMetadataRequest) -> SafeMediaMetadataRequest:
    validated = SafeMediaMetadataRequest.model_validate(request.model_dump())
    for field_name, reason in [
        ("raw_media_requested", "RAW_MEDIA_EXPORT_DENIED"),
        ("full_file_read_requested", "FULL_FILE_READ_DENIED"),
        ("file_mutation_requested", "FILE_MUTATION_DENIED"),
        ("original_overwrite_requested", "ORIGINAL_OVERWRITE_DENIED"),
        ("ocio_transform_requested", "OCIO_TRANSFORM_DENIED"),
        ("ai_gamut_expansion_requested", "AI_GAMUT_EXPANSION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("contains_secret_like_metadata", "SECRET_LIKE_METADATA_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def inspect_safe_media_metadata(
    request: SafeMediaMetadataRequest,
    policy: SafeMediaMetadataPolicy | None = None,
) -> SafeMediaMetadataDecision:
    active_policy = validate_safe_media_metadata_policy(policy or SafeMediaMetadataPolicy())
    active_request = validate_safe_media_metadata_request(request)
    decision_ref = f"media-metadata-decision:{_ref_suffix(active_request.request_ref)}"
    metadata_refs = [*active_policy.metadata_refs, active_request.request_ref, active_request.media_ref]

    if active_request.declared_media_type.lower() not in SUPPORTED_MEDIA_TYPES:
        return SafeMediaMetadataDecision(
            decision_ref=decision_ref,
            request_ref=active_request.request_ref,
            status=SafeMediaMetadataStatus.denied,
            metadata_ready=False,
            media_ref=active_request.media_ref,
            safe_path_ref=active_request.safe_path_ref,
            declared_media_type=active_request.declared_media_type,
            declared_byte_size=active_request.declared_byte_size,
            declared_dimensions=active_request.declared_dimensions,
            declared_duration_ms=active_request.declared_duration_ms,
            reason_codes=["UNSUPPORTED_MEDIA_TYPE_DENIED"],
            safe_summary="Unsupported media type denied without raw media output.",
            receipt_plan=None,
            metadata_refs=metadata_refs,
        )

    receipt_plan = SafeMediaMetadataReceiptPlan(
        receipt_plan_ref=f"media-metadata-receipt:{_ref_suffix(active_request.request_ref)}",
        request_ref=active_request.request_ref,
        safe_summary="M54 records safe declared media metadata only.",
        metadata_refs=metadata_refs,
    )
    return SafeMediaMetadataDecision(
        decision_ref=decision_ref,
        request_ref=active_request.request_ref,
        status=SafeMediaMetadataStatus.metadata_ready,
        metadata_ready=True,
        media_ref=active_request.media_ref,
        safe_path_ref=active_request.safe_path_ref,
        declared_media_type=active_request.declared_media_type,
        declared_byte_size=active_request.declared_byte_size,
        declared_dimensions=active_request.declared_dimensions,
        declared_duration_ms=active_request.declared_duration_ms,
        reason_codes=["M54_METADATA_ONLY"],
        safe_summary="Safe media metadata is ready without reading or exporting raw media.",
        receipt_plan=receipt_plan,
        metadata_refs=metadata_refs,
    )


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_m54_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M54_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _ref_suffix(value: str) -> str:
    return value.split(":", 1)[1].replace("/", "-").replace("@", "-")
