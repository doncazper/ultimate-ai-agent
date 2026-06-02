import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.device_capabilities import (
    DeviceCapabilityDescriptor,
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceDataClassification,
    DevicePermissionScope,
    DevicePlatform,
    DeviceRiskLevel,
    build_default_device_capability_manifest,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    assert_device_contract_only,
    validate_device_capability_descriptor,
)


def test_default_device_capability_manifest_is_contract_only_and_not_authority():
    manifest = build_default_device_capability_manifest()

    assert manifest.milestone == "M20"
    assert manifest.baseline_version == "0.24.1"
    assert manifest.contract_only is True
    assert manifest.device_clients_are_authority is False
    assert manifest.device_output_is_trusted_control_input is False
    assert manifest.sensor_access_enabled is False
    assert manifest.os_permission_integration_implemented is False
    assert manifest.backend_routes_added is False
    assert manifest.runtime_broker_implemented is False
    assert manifest.native_client_implemented is False
    assert {platform for platform in manifest.platforms} >= {
        DevicePlatform.ios_planned,
        DevicePlatform.android_planned,
        DevicePlatform.mobile_web_planned,
        DevicePlatform.macos_planned,
    }

    assert_device_contract_only(manifest)


def test_device_capability_descriptor_forbids_extra_fields():
    with pytest.raises(ValidationError):
        DeviceCapabilityDescriptor(
            capability_id="camera_contract",
            platform=DevicePlatform.ios_planned,
            kind=DeviceCapabilityKind.camera,
            purpose="future user-reviewed camera capture planning",
            risk_level=DeviceRiskLevel.high,
            data_classification=DeviceDataClassification.sensitive,
            permission_scope=DevicePermissionScope.foreground_planned,
            safe_summary="camera planning metadata only",
            unexpected_sensor_runtime=True,
        )


def test_device_capability_descriptor_defaults_to_disabled_contract():
    descriptor = DeviceCapabilityDescriptor(
        capability_id="clipboard_contract",
        platform=DevicePlatform.mobile_web_planned,
        kind=DeviceCapabilityKind.clipboard,
        status=DeviceCapabilityStatus.future_requires_broker,
        purpose="future selected clipboard import planning",
        risk_level=DeviceRiskLevel.medium,
        data_classification=DeviceDataClassification.personal,
        safe_summary="clipboard planning metadata only",
    )

    assert descriptor.allowed_now is False
    assert descriptor.implemented_now is False
    assert descriptor.requires_device_capability_broker is True
    assert descriptor.requires_explicit_user_gesture is True
    assert descriptor.requires_receipt is True
    assert descriptor.requires_redaction is True

    validate_device_capability_descriptor(descriptor)
