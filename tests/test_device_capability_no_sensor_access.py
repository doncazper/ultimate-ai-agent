from typing import Any
import pytest

from ultimate_ai_agent.core.device_capabilities import (
    DeviceCapabilityDescriptor,
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceDataClassification,
    DevicePermissionRequestContract,
    DevicePermissionScope,
    DevicePlatform,
    DeviceRiskLevel,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    assert_no_sensor_access_enabled,
    validate_device_capability_descriptor,
    validate_device_permission_request,
)

MAJOR_DEVICE_CAPABILITY_KINDS = [
    DeviceCapabilityKind.camera,
    DeviceCapabilityKind.microphone,
    DeviceCapabilityKind.location,
    DeviceCapabilityKind.notifications,
    DeviceCapabilityKind.contacts,
    DeviceCapabilityKind.calendar,
    DeviceCapabilityKind.photos,
    DeviceCapabilityKind.files,
    DeviceCapabilityKind.clipboard,
    DeviceCapabilityKind.bluetooth,
    DeviceCapabilityKind.nfc,
    DeviceCapabilityKind.biometrics,
    DeviceCapabilityKind.local_network,
    DeviceCapabilityKind.motion,
    DeviceCapabilityKind.health,
    DeviceCapabilityKind.screen_capture,
    DeviceCapabilityKind.background_service,
    DeviceCapabilityKind.device_identity,
    DeviceCapabilityKind.device_pairing,
]


def _descriptor_for_kind(capability_kind: Any, **overrides: Any) -> Any:
    values = {
        "capability_id": f"{capability_kind.value}_contract",
        "platform": DevicePlatform.android_planned,
        "kind": capability_kind,
        "status": DeviceCapabilityStatus.future_requires_broker,
        "purpose": f"future {capability_kind.value} planning only",
        "risk_level": DeviceRiskLevel.high,
        "data_classification": DeviceDataClassification.sensitive,
        "safe_summary": f"{capability_kind.value} planning metadata only",
    }
    if capability_kind == DeviceCapabilityKind.background_service:
        values["status"] = DeviceCapabilityStatus.blocked
    if capability_kind in {
        DeviceCapabilityKind.device_identity,
        DeviceCapabilityKind.device_pairing,
    }:
        values["status"] = DeviceCapabilityStatus.future_requires_pairing
        values["requires_pairing"] = True
    values.update(overrides)
    return DeviceCapabilityDescriptor(**values)


@pytest.mark.parametrize(
    "capability_kind",
    MAJOR_DEVICE_CAPABILITY_KINDS,
)
def test_future_device_capabilities_cannot_be_enabled_now(capability_kind: Any) -> None:
    descriptor = _descriptor_for_kind(capability_kind, allowed_now=True)

    with pytest.raises(ValueError, match="allowed_now"):
        assert_no_sensor_access_enabled(descriptor)


@pytest.mark.parametrize("capability_kind", MAJOR_DEVICE_CAPABILITY_KINDS)
def test_future_device_capabilities_cannot_be_implemented_now(capability_kind: Any) -> None:
    descriptor = _descriptor_for_kind(capability_kind, implemented_now=True)

    with pytest.raises(ValueError, match="implemented_now"):
        validate_device_capability_descriptor(descriptor)


def test_permission_request_rejects_user_gesture_present_as_runtime_claim() -> None:
    request = DevicePermissionRequestContract(
        request_id="permission_camera_001",
        platform=DevicePlatform.ios_planned,
        capability_kind=DeviceCapabilityKind.camera,
        purpose="future selected camera permission planning",
        risk_level=DeviceRiskLevel.high,
        data_classification=DeviceDataClassification.sensitive,
        requested_scope=DevicePermissionScope.foreground_planned,
        user_gesture_present=True,
        broker_ref="dcb_contract_only",
        safe_summary="camera permission planning metadata only",
    )

    with pytest.raises(ValueError, match="user_gesture_present"):
        validate_device_permission_request(request)


def test_background_permission_scope_is_blocked_for_sensitive_capabilities() -> None:
    request = DevicePermissionRequestContract(
        request_id="permission_location_001",
        platform=DevicePlatform.android_planned,
        capability_kind=DeviceCapabilityKind.location,
        purpose="future location permission planning",
        risk_level=DeviceRiskLevel.high,
        data_classification=DeviceDataClassification.sensitive,
        requested_scope=DevicePermissionScope.background_blocked,
        broker_ref="dcb_contract_only",
        safe_summary="location permission planning metadata only",
    )

    with pytest.raises(ValueError, match="background"):
        validate_device_permission_request(request)
