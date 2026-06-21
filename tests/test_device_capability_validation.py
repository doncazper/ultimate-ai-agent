from typing import Any
import pytest

from ultimate_ai_agent.core.device_capabilities import (
    DeviceCapabilityDescriptor,
    DeviceCapabilityDecisionStatus,
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceCapabilityValidationDecision,
    DeviceCaptureIntentContract,
    DeviceCaptureMode,
    DeviceDataClassification,
    DevicePermissionRequestContract,
    DevicePermissionScope,
    DevicePlatform,
    DeviceReceiptRequirement,
    DeviceRiskLevel,
    DeviceCapabilityReceiptPlan,
    DeviceRevocationPlan,
    build_default_device_capability_manifest,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    assert_no_automatic_memory_write,
    assert_no_background_service,
    assert_no_external_send,
    assert_no_os_permission_integration,
    assert_no_secret_metadata,
    assert_no_silent_capture,
    validate_device_capability_descriptor,
    validate_device_capability_decision,
    validate_device_capture_intent,
    validate_device_permission_request,
    validate_device_receipt_plan,
    validate_device_revocation_plan,
)


def _descriptor(**overrides: Any) -> Any:
    values = {
        "capability_id": "camera_contract",
        "platform": DevicePlatform.ios_planned,
        "kind": DeviceCapabilityKind.camera,
        "status": DeviceCapabilityStatus.future_requires_broker,
        "purpose": "future user-reviewed camera capture planning",
        "risk_level": DeviceRiskLevel.high,
        "data_classification": DeviceDataClassification.sensitive,
        "permission_scope": DevicePermissionScope.foreground_planned,
        "safe_summary": "camera planning metadata only",
    }
    values.update(overrides)
    return DeviceCapabilityDescriptor(**values)


def _capture_intent(**overrides: Any) -> Any:
    values = {
        "intent_id": "capture_intent_camera_001",
        "platform": DevicePlatform.ios_planned,
        "capability_kind": DeviceCapabilityKind.camera,
        "purpose": "future selected camera capture planning",
        "data_classification": DeviceDataClassification.sensitive,
        "retention_policy_ref": "retention_device_capture_planned",
        "redaction_policy_ref": "redaction_device_capture_planned",
        "safe_summary": "selected camera capture planning only",
    }
    values.update(overrides)
    return DeviceCaptureIntentContract(**values)


def _permission_request(**overrides: Any) -> Any:
    values = {
        "request_id": "permission_camera_001",
        "platform": DevicePlatform.ios_planned,
        "capability_kind": DeviceCapabilityKind.camera,
        "purpose": "future selected camera permission planning",
        "risk_level": DeviceRiskLevel.high,
        "data_classification": DeviceDataClassification.sensitive,
        "broker_ref": "dcb_contract_only",
        "safe_summary": "camera permission planning metadata only",
    }
    values.update(overrides)
    return DevicePermissionRequestContract(**values)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("allowed_now", "allowed_now"),
        ("implemented_now", "implemented_now"),
        ("os_permission_integration_claimed", "OS permission"),
        ("background_service_enabled", "background service"),
        ("device_pairing_runtime_claimed", "pairing runtime"),
        ("device_identity_runtime_claimed", "device identity runtime"),
        ("device_client_authority_claimed", "device client authority"),
        ("approval_execution_claimed", "approval/action execution"),
    ],
)
def test_descriptor_rejects_enabled_or_authority_flags(field: str, message: str) -> None:
    descriptor = _descriptor(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_device_capability_descriptor(descriptor)


@pytest.mark.parametrize(
    "capture_mode",
    [
        DeviceCaptureMode.passive_blocked,
        DeviceCaptureMode.background_blocked,
        DeviceCaptureMode.continuous_blocked,
    ],
)
def test_capture_intent_rejects_passive_background_and_continuous_modes(capture_mode: Any) -> None:
    intent = _capture_intent(requested_capture_mode=capture_mode)

    with pytest.raises(ValueError, match="capture mode"):
        validate_device_capture_intent(intent)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("silent_capture_allowed", "silent_capture_allowed"),
        ("automatic_memory_write_allowed", "automatic_memory_write_allowed"),
        ("external_send_allowed", "external_send_allowed"),
        ("raw_payload_allowed", "raw_payload_allowed"),
    ],
)
def test_capture_intent_rejects_raw_silent_memory_and_external_send(field: str, message: str) -> None:
    intent = _capture_intent(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_device_capture_intent(intent)


def test_metadata_refs_metadata_and_summary_reject_secrets_and_private_paths() -> None:
    descriptor = _descriptor(
        safe_summary="camera planning api_key=redacted",
        metadata_refs=["/Users/alice/private-photo.jpg"],
        metadata={"token": "redacted"},
    )

    with pytest.raises(ValueError, match="secret-like"):
        validate_device_capability_descriptor(descriptor)


def test_manifest_level_validation_helpers_pin_no_runtime_flags() -> None:
    manifest = build_default_device_capability_manifest()

    assert_no_silent_capture(_capture_intent())
    assert_no_automatic_memory_write(_capture_intent())
    assert_no_external_send(_capture_intent())
    assert_no_os_permission_integration(_descriptor())
    assert_no_background_service(_descriptor())
    assert_no_secret_metadata(manifest)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("os_permission_runtime_claimed", "OS permission"),
        ("notification_push_runtime_claimed", "notification push runtime"),
        ("background_service_runtime_claimed", "background service"),
    ],
)
def test_permission_request_rejects_runtime_permission_drift_flags(field: str, message: str) -> None:
    request = _permission_request(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_device_permission_request(request)


def test_validation_decision_cannot_allow_device_capability_runtime() -> None:
    decision = DeviceCapabilityValidationDecision(
        decision_id="decision_runtime_claim",
        subject_ref="camera_contract",
        allowed=True,
        status=DeviceCapabilityDecisionStatus.contract_valid,
        safe_message="camera contract is allowed now",
    )

    with pytest.raises(ValueError, match="allowed"):
        validate_device_capability_decision(decision)


def test_receipt_plan_requires_redacted_receipt_and_no_raw_storage() -> None:
    plan = DeviceCapabilityReceiptPlan(
        receipt_plan_id="receipt_plan_not_applicable",
        platform=DevicePlatform.ios_planned,
        capability_kind=DeviceCapabilityKind.camera,
        receipt_requirement=DeviceReceiptRequirement.not_applicable,
        retention_summary="redacted receipt planning only",
        safe_summary="camera receipt planning metadata only",
    )

    with pytest.raises(ValueError, match="redacted receipt"):
        validate_device_receipt_plan(plan)


def test_revocation_plan_remains_contract_only() -> None:
    plan = DeviceRevocationPlan(
        plan_id="revocation_runtime_claim",
        platform=DevicePlatform.android_planned,
        capability_kind=DeviceCapabilityKind.location,
        contract_only=False,
        safe_summary="location revocation runtime is available",
    )

    with pytest.raises(ValueError, match="contract-only"):
        validate_device_revocation_plan(plan)
