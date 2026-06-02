import re
from collections.abc import Iterable, Mapping
from typing import Any

from ultimate_ai_agent.core.device_capabilities.contracts import (
    DeviceCapabilityDescriptor,
    DeviceCapabilityManifest,
    DeviceCaptureIntentContract,
    DeviceCapabilityReceiptPlan,
    DevicePermissionRequestContract,
    DeviceRevocationPlan,
    DeviceTrustHandshakePlan,
)
from ultimate_ai_agent.core.device_capabilities.enums import (
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceCaptureMode,
    DevicePermissionScope,
)


SENSOR_CAPABILITIES = {
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
}

PAIRING_CAPABILITIES = {
    DeviceCapabilityKind.device_identity,
    DeviceCapabilityKind.device_pairing,
}

BLOCKED_RUNTIME_CAPABILITIES = {
    DeviceCapabilityKind.background_service,
}

SECRET_KEY = re.compile(
    r"(?i)(api[_-]?key|auth[_-]?token|authorization|cookie|credential|password|secret|token)"
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|auth[_-]?token|authorization|cookie|credential|password|secret|token)\s*[:=]"
)
PRIVATE_PATH = re.compile(
    r"(?i)(/users/[^/\s]+|/home/[^/\s]+|/private/|\\users\\[^\\\s]+|[a-z]:\\users\\[^\\\s]+)"
)
RAW_DEVICE_CONTENT = {
    "coordinates",
    "latitude",
    "longitude",
    "audio_buffer",
    "image_bytes",
    "contact_data",
    "calendar_entry",
    "photo_data",
    "biometric_data",
    "file_contents",
    "raw_payload",
    "raw_location",
    "raw_audio",
    "raw_image",
    "raw_contact",
    "raw_calendar",
    "raw_photo",
}


def validate_device_capability_descriptor(
    descriptor: DeviceCapabilityDescriptor,
) -> DeviceCapabilityDescriptor:
    _assert_safe_text(descriptor.safe_summary)
    _assert_safe_text(descriptor.purpose)
    _assert_metadata_refs_only(descriptor.metadata_refs)
    _assert_safe_metadata(descriptor.metadata)
    if descriptor.allowed_now:
        raise ValueError("device capability allowed_now must remain false in M20")
    if descriptor.implemented_now:
        raise ValueError("device capability implemented_now must remain false in M20")
    if descriptor.os_permission_integration_claimed:
        raise ValueError("OS permission integration is not implemented in M20")
    if descriptor.background_service_enabled:
        raise ValueError("background service is not implemented in M20")
    if descriptor.device_pairing_runtime_claimed:
        raise ValueError("device pairing runtime is not implemented in M20")
    if descriptor.device_identity_runtime_claimed:
        raise ValueError("device identity runtime is not implemented in M20")
    if descriptor.device_client_authority_claimed:
        raise ValueError("device client authority is not implemented")
    if descriptor.approval_execution_claimed:
        raise ValueError("approval/action execution is not implemented for device clients")
    if descriptor.capture_mode != DeviceCaptureMode.manual_selected_planned:
        raise ValueError("device capability capture mode must remain manual-selected planning only")
    if descriptor.permission_scope in {
        DevicePermissionScope.background_blocked,
        DevicePermissionScope.standing_blocked,
    }:
        raise ValueError("background or standing device permission scopes are blocked in M20")
    _validate_capability_status(descriptor)
    return descriptor


def validate_device_permission_request(
    request: DevicePermissionRequestContract,
) -> DevicePermissionRequestContract:
    _assert_safe_text(request.safe_summary)
    _assert_safe_text(request.purpose)
    _assert_safe_text(request.broker_ref)
    _assert_metadata_refs_only(request.consent_refs)
    _assert_metadata_refs_only(request.receipt_refs)
    _assert_metadata_refs_only(request.metadata_refs)
    _assert_safe_metadata(request.metadata)
    if request.user_gesture_present:
        raise ValueError("user_gesture_present would imply runtime device access in M20")
    if request.requested_scope in {
        DevicePermissionScope.background_blocked,
        DevicePermissionScope.standing_blocked,
    }:
        raise ValueError("background or standing device permissions are blocked in M20")
    if request.requested_capture_mode != DeviceCaptureMode.manual_selected_planned:
        raise ValueError("permission request capture mode is blocked in M20")
    return request


def validate_device_capture_intent(
    intent: DeviceCaptureIntentContract,
) -> DeviceCaptureIntentContract:
    _assert_safe_text(intent.safe_summary)
    _assert_safe_text(intent.purpose)
    _assert_safe_text(intent.retention_policy_ref)
    _assert_safe_text(intent.redaction_policy_ref)
    _assert_metadata_refs_only(intent.metadata_refs)
    _assert_safe_metadata(intent.metadata)
    if not intent.user_gesture_required:
        raise ValueError("device capture requires an explicit future user gesture")
    if intent.user_gesture_present:
        raise ValueError("user_gesture_present would imply runtime capture in M20")
    if intent.requested_capture_mode != DeviceCaptureMode.manual_selected_planned:
        raise ValueError("device capture mode is blocked in M20")
    if intent.silent_capture_allowed:
        raise ValueError("silent_capture_allowed is not allowed in M20")
    if intent.automatic_memory_write_allowed:
        raise ValueError("automatic_memory_write_allowed is not allowed in M20")
    if intent.external_send_allowed:
        raise ValueError("external_send_allowed is not allowed in M20")
    if intent.raw_payload_allowed:
        raise ValueError("raw_payload_allowed is not allowed in M20")
    return intent


def validate_device_trust_handshake_plan(
    plan: DeviceTrustHandshakePlan,
) -> DeviceTrustHandshakePlan:
    _assert_safe_text(plan.safe_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    _assert_safe_metadata(plan.metadata)
    if plan.pairing_runtime_implemented:
        raise ValueError("device pairing runtime is not implemented in M20")
    if not plan.local_approval_required:
        raise ValueError("future device trust handshakes require local approval")
    if not plan.receipt_required:
        raise ValueError("future device trust handshakes require receipts")
    return plan


def validate_device_revocation_plan(plan: DeviceRevocationPlan) -> DeviceRevocationPlan:
    _assert_safe_text(plan.safe_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    _assert_safe_metadata(plan.metadata)
    if not plan.revocation_supported:
        raise ValueError("future device capability plans must support revocation")
    if not plan.receipt_required:
        raise ValueError("future device revocation requires a receipt")
    return plan


def validate_device_receipt_plan(
    plan: DeviceCapabilityReceiptPlan,
) -> DeviceCapabilityReceiptPlan:
    _assert_safe_text(plan.safe_summary)
    _assert_safe_text(plan.retention_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    _assert_safe_metadata(plan.metadata)
    if not plan.redaction_required:
        raise ValueError("device capability receipts require redaction")
    if plan.storage_allowed:
        raise ValueError("device capability receipt plans cannot allow raw storage in M20")
    return plan


def assert_device_contract_only(manifest: DeviceCapabilityManifest) -> DeviceCapabilityManifest:
    _assert_safe_text(manifest.safe_summary)
    _assert_metadata_refs_only(manifest.metadata_refs)
    _assert_safe_metadata(manifest.metadata)
    if not manifest.contract_only:
        raise ValueError("Device Capability Broker manifest must remain contract-only")
    if manifest.sensor_access_enabled:
        raise ValueError("sensor access is not implemented in M20")
    if manifest.os_permission_integration_implemented:
        raise ValueError("OS permission integration is not implemented in M20")
    if manifest.backend_routes_added:
        raise ValueError("backend routes are not added for M20")
    if manifest.runtime_broker_implemented:
        raise ValueError("Device Capability Broker runtime is not implemented in M20")
    if manifest.native_client_implemented:
        raise ValueError("native device client implementation is not part of M20")
    if manifest.device_clients_are_authority:
        raise ValueError("device clients are not authority")
    if manifest.device_output_is_trusted_control_input:
        raise ValueError("device output is not trusted control input by default")
    if manifest.approval_execution_allowed:
        raise ValueError("device clients cannot execute approvals")
    if manifest.automatic_memory_write_allowed:
        raise ValueError("device capture cannot silently become memory")
    if manifest.external_send_allowed:
        raise ValueError("device capture cannot trigger external sends")
    if manifest.raw_payload_allowed:
        raise ValueError("raw device payloads are not allowed in M20")
    for descriptor in manifest.capabilities:
        validate_device_capability_descriptor(descriptor)
    for warning in manifest.warnings:
        _assert_safe_text(warning)
    for ref in manifest.docs_refs:
        _assert_safe_text(ref)
    return manifest


def assert_no_sensor_access_enabled(
    descriptor: DeviceCapabilityDescriptor,
) -> DeviceCapabilityDescriptor:
    return validate_device_capability_descriptor(descriptor)


def assert_no_silent_capture(intent: DeviceCaptureIntentContract) -> DeviceCaptureIntentContract:
    return validate_device_capture_intent(intent)


def assert_no_automatic_memory_write(
    intent: DeviceCaptureIntentContract,
) -> DeviceCaptureIntentContract:
    return validate_device_capture_intent(intent)


def assert_no_external_send(intent: DeviceCaptureIntentContract) -> DeviceCaptureIntentContract:
    return validate_device_capture_intent(intent)


def assert_no_background_service(
    descriptor: DeviceCapabilityDescriptor,
) -> DeviceCapabilityDescriptor:
    return validate_device_capability_descriptor(descriptor)


def assert_no_os_permission_integration(
    descriptor: DeviceCapabilityDescriptor,
) -> DeviceCapabilityDescriptor:
    return validate_device_capability_descriptor(descriptor)


def assert_no_secret_metadata(value: Any) -> Any:
    if isinstance(value, DeviceCapabilityManifest):
        _assert_metadata_refs_only(value.metadata_refs)
        _assert_safe_metadata(value.metadata)
        for descriptor in value.capabilities:
            assert_no_secret_metadata(descriptor)
        return value
    if isinstance(value, DeviceCapabilityDescriptor):
        _assert_safe_text(value.safe_summary)
        _assert_metadata_refs_only(value.metadata_refs)
        _assert_safe_metadata(value.metadata)
        return value
    _assert_safe_metadata(value)
    return value


def _validate_capability_status(descriptor: DeviceCapabilityDescriptor) -> None:
    if descriptor.kind in SENSOR_CAPABILITIES:
        allowed_statuses = {
            DeviceCapabilityStatus.planned_disabled,
            DeviceCapabilityStatus.future_requires_broker,
            DeviceCapabilityStatus.blocked,
        }
        if descriptor.status not in allowed_statuses:
            raise ValueError("device sensor capabilities require a future broker")
        if not descriptor.requires_device_capability_broker:
            raise ValueError("device sensor capabilities require Device Capability Broker")
    if descriptor.kind in PAIRING_CAPABILITIES:
        if descriptor.status not in {
            DeviceCapabilityStatus.future_requires_pairing,
            DeviceCapabilityStatus.planned_disabled,
            DeviceCapabilityStatus.blocked,
        }:
            raise ValueError("device identity and pairing require future pairing contracts")
        if not descriptor.requires_pairing:
            raise ValueError("device identity and pairing must require future pairing")
    if descriptor.kind in BLOCKED_RUNTIME_CAPABILITIES:
        if descriptor.status not in {
            DeviceCapabilityStatus.blocked,
            DeviceCapabilityStatus.planned_disabled,
        }:
            raise ValueError("background service capabilities are blocked in M20")


def _assert_metadata_refs_only(refs: Iterable[str]) -> None:
    for ref in refs:
        _assert_safe_text(ref)
        if "\n" in ref or len(ref) > 160:
            raise ValueError("device metadata refs must be short string/ref-only values")


def _assert_safe_metadata(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            _assert_safe_text(key_text)
            if SECRET_KEY.search(key_text):
                raise ValueError("secret-like metadata is not allowed in device contracts")
            if key_text.lower() in RAW_DEVICE_CONTENT:
                raise ValueError("raw device content metadata is not allowed")
            _assert_safe_metadata(item)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            _assert_safe_metadata(item)
        return
    if isinstance(value, str):
        _assert_safe_text(value)


def _assert_safe_text(text: str) -> None:
    if SECRET_ASSIGNMENT.search(text) or SECRET_KEY.fullmatch(text.strip()):
        raise ValueError("secret-like text is not allowed in device contracts")
    lowered = text.lower()
    if PRIVATE_PATH.search(text):
        raise ValueError("private/home path values are not allowed in device contracts")
    for key in RAW_DEVICE_CONTENT:
        if key.replace("_", " ") in lowered or key in lowered:
            raise ValueError("raw device content fields are not allowed")
