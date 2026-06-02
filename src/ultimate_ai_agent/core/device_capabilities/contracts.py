from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.device_capabilities.enums import (
    DeviceCapabilityDecisionStatus,
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceCaptureMode,
    DeviceDataClassification,
    DevicePermissionScope,
    DevicePlatform,
    DeviceReceiptRequirement,
    DeviceRiskLevel,
    DeviceTrustState,
)


class _DeviceCapabilityContractModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid")


class DeviceCapabilityDescriptor(_DeviceCapabilityContractModel):
    capability_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    kind: DeviceCapabilityKind
    status: DeviceCapabilityStatus = DeviceCapabilityStatus.planned_disabled
    purpose: str = Field(..., min_length=1)
    risk_level: DeviceRiskLevel
    data_classification: DeviceDataClassification
    allowed_now: bool = False
    implemented_now: bool = False
    requires_device_capability_broker: bool = True
    requires_pairing: bool = False
    requires_explicit_user_gesture: bool = True
    requires_receipt: bool = True
    requires_redaction: bool = True
    permission_scope: DevicePermissionScope = DevicePermissionScope.one_time_planned
    capture_mode: DeviceCaptureMode = DeviceCaptureMode.manual_selected_planned
    retention_policy_ref: str = "retention_device_contract_planned"
    redaction_policy_ref: str = "redaction_device_contract_planned"
    revocation_policy_ref: str = "revocation_device_contract_planned"
    safe_summary: str = Field(..., min_length=1)
    os_permission_integration_claimed: bool = False
    background_service_enabled: bool = False
    device_pairing_runtime_claimed: bool = False
    device_identity_runtime_claimed: bool = False
    device_client_authority_claimed: bool = False
    approval_execution_claimed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DevicePermissionRequestContract(_DeviceCapabilityContractModel):
    request_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    capability_kind: DeviceCapabilityKind
    purpose: str = Field(..., min_length=1)
    risk_level: DeviceRiskLevel
    data_classification: DeviceDataClassification
    requested_scope: DevicePermissionScope = DevicePermissionScope.one_time_planned
    requested_capture_mode: DeviceCaptureMode = DeviceCaptureMode.manual_selected_planned
    user_gesture_present: bool = False
    broker_ref: str = Field(..., min_length=1)
    consent_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCaptureIntentContract(_DeviceCapabilityContractModel):
    intent_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    capability_kind: DeviceCapabilityKind
    purpose: str = Field(..., min_length=1)
    data_classification: DeviceDataClassification
    user_gesture_required: bool = True
    user_gesture_present: bool = False
    requested_capture_mode: DeviceCaptureMode = DeviceCaptureMode.manual_selected_planned
    silent_capture_allowed: bool = False
    automatic_memory_write_allowed: bool = False
    external_send_allowed: bool = False
    raw_payload_allowed: bool = False
    retention_policy_ref: str = Field(..., min_length=1)
    redaction_policy_ref: str = Field(..., min_length=1)
    receipt_requirement: DeviceReceiptRequirement = (
        DeviceReceiptRequirement.redacted_receipt_required
    )
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCapabilityValidationDecision(_DeviceCapabilityContractModel):
    decision_id: str = Field(..., min_length=1)
    subject_ref: str = Field(..., min_length=1)
    allowed: bool = False
    status: DeviceCapabilityDecisionStatus = DeviceCapabilityDecisionStatus.not_implemented
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    required_next_action: str = "future_reviewed_milestone_required"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCapabilityManifest(_DeviceCapabilityContractModel):
    manifest_id: str = "device_capability_manifest_m20"
    milestone: str = "M20"
    baseline_version: str = "0.24.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contract_only: bool = True
    platforms: list[DevicePlatform] = Field(default_factory=list)
    capabilities: list[DeviceCapabilityDescriptor] = Field(default_factory=list)
    blocked_capabilities: list[DeviceCapabilityKind] = Field(default_factory=list)
    future_capabilities: list[DeviceCapabilityKind] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    safe_summary: str = "M20 Device Capability Broker contract-only manifest."
    sensor_access_enabled: bool = False
    os_permission_integration_implemented: bool = False
    backend_routes_added: bool = False
    runtime_broker_implemented: bool = False
    native_client_implemented: bool = False
    device_clients_are_authority: bool = False
    device_output_is_trusted_control_input: bool = False
    approval_execution_allowed: bool = False
    automatic_memory_write_allowed: bool = False
    external_send_allowed: bool = False
    raw_payload_allowed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("platforms", "capabilities", "blocked_capabilities", "future_capabilities", "docs_refs", "warnings")
    @classmethod
    def _copy_collections(cls, value: list[Any]) -> list[Any]:
        return list(value)


class DeviceTrustHandshakePlan(_DeviceCapabilityContractModel):
    plan_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    trust_state: DeviceTrustState = DeviceTrustState.unpaired_planned
    pairing_required: bool = True
    revocation_required: bool = True
    session_scope_required: bool = True
    local_approval_required: bool = True
    receipt_required: bool = True
    pairing_runtime_implemented: bool = False
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceRevocationPlan(_DeviceCapabilityContractModel):
    plan_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    capability_kind: DeviceCapabilityKind
    revocation_supported: bool = True
    receipt_required: bool = True
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCapabilityReceiptPlan(_DeviceCapabilityContractModel):
    receipt_plan_id: str = Field(..., min_length=1)
    platform: DevicePlatform
    capability_kind: DeviceCapabilityKind
    receipt_requirement: DeviceReceiptRequirement = (
        DeviceReceiptRequirement.redacted_receipt_required
    )
    redaction_required: bool = True
    storage_allowed: bool = False
    retention_summary: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
