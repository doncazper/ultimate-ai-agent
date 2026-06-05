from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.mobile_companion.enums import (
    MobileCapabilityKind,
    MobileCapabilityStatus,
    MobileClientPlatform,
    MobileCompanionSurface,
    MobileDataClassification,
    MobileApiBoundaryStatus,
    MobilePermissionDecision,
    MobileProductRole,
    MobileReceiptRequirement,
)


class _MobileContractModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid")


class MobileClientPlan(_MobileContractModel):
    platform: MobileClientPlatform
    surfaces: list[MobileCompanionSurface] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    implemented_now: bool = False
    authority_claimed: bool = False
    native_package_created: bool = False
    os_permission_integration_claimed: bool = False
    signing_or_store_workflow_claimed: bool = False


class MobileCapabilityPlan(_MobileContractModel):
    capability: MobileCapabilityKind
    status: MobileCapabilityStatus = MobileCapabilityStatus.planned_disabled
    safe_summary: str = Field(..., min_length=1)
    allowed_now: bool = False
    os_permission_integrated: bool = False
    background_service_enabled: bool = False
    requires_device_capability_broker: bool = True
    receipt_requirement: MobileReceiptRequirement = (
        MobileReceiptRequirement.redacted_receipt_required
    )
    metadata_refs: list[str] = Field(default_factory=list)


class MobilePermissionDecisionPlan(_MobileContractModel):
    capability: MobileCapabilityKind
    decision: MobilePermissionDecision = MobilePermissionDecision.not_implemented
    safe_summary: str = Field(..., min_length=1)
    receipt_requirement: MobileReceiptRequirement = (
        MobileReceiptRequirement.redacted_receipt_required
    )
    user_approval_required: bool = True


class MobilePermissionManifest(_MobileContractModel):
    milestone: str = "M19"
    version: str = "0.23.1"
    contract_only: bool = True
    os_permission_integration_implemented: bool = False
    background_service_implemented: bool = False
    decisions: list[MobilePermissionDecisionPlan] = Field(default_factory=list)
    safe_summary: str = "Mobile permission planning manifest; no OS permissions are integrated."


class MobileCaptureIntentPlan(_MobileContractModel):
    capture_ref: str = Field(..., min_length=1)
    capability: MobileCapabilityKind
    data_classification: MobileDataClassification
    safe_summary: str = Field(..., min_length=1)
    silent_capture: bool = False
    automatic_memory_write: bool = False
    external_send_allowed: bool = False
    storage_allowed: bool = False
    future_policy_ref: str | None = None
    receipt_requirement: MobileReceiptRequirement = (
        MobileReceiptRequirement.redacted_receipt_required
    )
    metadata_refs: list[str] = Field(default_factory=list)


class MobileReceiptPlan(_MobileContractModel):
    receipt_ref: str = Field(..., min_length=1)
    requirement: MobileReceiptRequirement = MobileReceiptRequirement.redacted_receipt_required
    safe_summary: str = Field(..., min_length=1)
    raw_payload_stored: bool = False
    secret_storage_allowed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)


class MobileCompanionManifest(_MobileContractModel):
    milestone: str = "M19"
    version: str = "0.23.1"
    contract_only: bool = True
    clients: list[MobileClientPlan] = Field(default_factory=list)
    capabilities: list[MobileCapabilityPlan] = Field(default_factory=list)
    capture_intents: list[MobileCaptureIntentPlan] = Field(default_factory=list)
    receipt_plans: list[MobileReceiptPlan] = Field(default_factory=list)
    safe_summary: str = "Mobile companion contract/API planning only."
    mobile_client_is_authority: bool = False
    mobile_approval_execution_implemented: bool = False
    device_capability_broker_required: bool = True
    sensor_access_enabled: bool = False
    os_permission_integration_implemented: bool = False
    background_service_implemented: bool = False
    arbitrary_strings_are_authority: bool = False
    secrets_allowed: bool = False

    @field_validator("clients", "capabilities", "capture_intents", "receipt_plans")
    @classmethod
    def _copy_collections(cls, value: list[Any]) -> list[Any]:
        return list(value)


class MobileProductSurfaceContract(_MobileContractModel):
    role: MobileProductRole
    surfaces: list[MobileCompanionSurface] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    review_only: bool = True
    read_only: bool = True
    authority_claimed: bool = False
    approval_execution_enabled: bool = False
    sensor_access_enabled: bool = False
    background_service_enabled: bool = False
    native_implementation_started: bool = False
    raw_payload_display_enabled: bool = False


class MobileApiBoundaryRefresh(_MobileContractModel):
    status: MobileApiBoundaryStatus = MobileApiBoundaryStatus.future_read_only
    safe_summary: str = Field(..., min_length=1)
    m43_boundary_only: bool = True
    backend_route_added: bool = False
    mutation_enabled: bool = False
    raw_data_enabled: bool = False
    sensor_endpoint_enabled: bool = False
    approval_execution_enabled: bool = False
    credential_handling_enabled: bool = False


class MobileProductContractRefresh(_MobileContractModel):
    milestone: str = "M42"
    version: str = "0.46.0"
    contract_refresh_only: bool = True
    safe_summary: str = "M42 mobile companion product contract refresh only."
    product_roles: list[MobileProductSurfaceContract] = Field(default_factory=list)
    api_boundary: MobileApiBoundaryRefresh
    m43_read_only_api_future: bool = True
    m44_ios_skeleton_future: bool = True
    native_app_implemented: bool = False
    mobile_api_implemented: bool = False
    mobile_sensor_access_enabled: bool = False
    os_permission_integration_enabled: bool = False
    background_service_enabled: bool = False
    signing_or_store_workflow_enabled: bool = False
    approval_capture_enabled: bool = False
    approval_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    raw_payload_exposure_enabled: bool = False
    production_authority_enabled: bool = False

    @field_validator("product_roles")
    @classmethod
    def _copy_product_roles(cls, value: list[MobileProductSurfaceContract]) -> list[MobileProductSurfaceContract]:
        return list(value)
