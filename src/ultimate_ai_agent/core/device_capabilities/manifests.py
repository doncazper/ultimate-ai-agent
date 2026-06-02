from ultimate_ai_agent.core.device_capabilities.contracts import (
    DeviceCapabilityDescriptor,
    DeviceCapabilityManifest,
)
from ultimate_ai_agent.core.device_capabilities.enums import (
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DeviceDataClassification,
    DevicePermissionScope,
    DevicePlatform,
    DeviceRiskLevel,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    assert_device_contract_only,
)


M20_DEVICE_CAPABILITY_DOCS = [
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
    "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
    "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
    "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
    "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
    "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
    "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
]


def build_default_device_capability_manifest(
    baseline_version: str = "0.24.0",
) -> DeviceCapabilityManifest:
    capabilities = [
        _capability(
            DeviceCapabilityKind.camera,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future camera capture planning only",
        ),
        _capability(
            DeviceCapabilityKind.microphone,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future microphone capture planning only",
        ),
        _capability(
            DeviceCapabilityKind.location,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future location context planning only",
        ),
        _capability(
            DeviceCapabilityKind.notifications,
            DeviceRiskLevel.medium,
            DeviceDataClassification.personal,
            "future notification display planning only",
        ),
        _capability(
            DeviceCapabilityKind.contacts,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future contacts planning only",
        ),
        _capability(
            DeviceCapabilityKind.calendar,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future calendar planning only",
        ),
        _capability(
            DeviceCapabilityKind.photos,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future selected photo planning only",
        ),
        _capability(
            DeviceCapabilityKind.files,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future selected file planning only",
        ),
        _capability(
            DeviceCapabilityKind.clipboard,
            DeviceRiskLevel.medium,
            DeviceDataClassification.personal,
            "future selected clipboard planning only",
        ),
        _capability(
            DeviceCapabilityKind.bluetooth,
            DeviceRiskLevel.medium,
            DeviceDataClassification.personal,
            "future bluetooth planning only",
        ),
        _capability(
            DeviceCapabilityKind.nfc,
            DeviceRiskLevel.medium,
            DeviceDataClassification.personal,
            "future nfc planning only",
        ),
        _capability(
            DeviceCapabilityKind.biometrics,
            DeviceRiskLevel.critical,
            DeviceDataClassification.regulated,
            "future biometric boundary planning only",
        ),
        _capability(
            DeviceCapabilityKind.local_network,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future local network planning only",
        ),
        _capability(
            DeviceCapabilityKind.motion,
            DeviceRiskLevel.medium,
            DeviceDataClassification.personal,
            "future motion signal planning only",
        ),
        _capability(
            DeviceCapabilityKind.health,
            DeviceRiskLevel.critical,
            DeviceDataClassification.regulated,
            "future health data boundary planning only",
        ),
        _capability(
            DeviceCapabilityKind.screen_capture,
            DeviceRiskLevel.high,
            DeviceDataClassification.sensitive,
            "future screen capture boundary planning only",
        ),
        DeviceCapabilityDescriptor(
            capability_id="background_service_contract",
            platform=DevicePlatform.unknown_planned,
            kind=DeviceCapabilityKind.background_service,
            status=DeviceCapabilityStatus.blocked,
            purpose="background services are blocked pending a reviewed future policy",
            risk_level=DeviceRiskLevel.forbidden,
            data_classification=DeviceDataClassification.forbidden,
            permission_scope=DevicePermissionScope.none,
            requires_explicit_user_gesture=True,
            safe_summary="background service planning is blocked in M20.",
        ),
        DeviceCapabilityDescriptor(
            capability_id="device_identity_contract",
            platform=DevicePlatform.unknown_planned,
            kind=DeviceCapabilityKind.device_identity,
            status=DeviceCapabilityStatus.future_requires_pairing,
            purpose="future device identity planning requires pairing and revocation policy",
            risk_level=DeviceRiskLevel.high,
            data_classification=DeviceDataClassification.personal,
            permission_scope=DevicePermissionScope.session_planned,
            requires_pairing=True,
            safe_summary="device identity planning requires future pairing.",
        ),
        DeviceCapabilityDescriptor(
            capability_id="device_pairing_contract",
            platform=DevicePlatform.unknown_planned,
            kind=DeviceCapabilityKind.device_pairing,
            status=DeviceCapabilityStatus.future_requires_pairing,
            purpose="future device pairing planning requires trust and revocation policy",
            risk_level=DeviceRiskLevel.high,
            data_classification=DeviceDataClassification.personal,
            permission_scope=DevicePermissionScope.session_planned,
            requires_pairing=True,
            safe_summary="device pairing planning requires future trust handshake.",
        ),
    ]
    manifest = DeviceCapabilityManifest(
        baseline_version=baseline_version,
        platforms=[
            DevicePlatform.ios_planned,
            DevicePlatform.android_planned,
            DevicePlatform.mobile_web_planned,
            DevicePlatform.macos_planned,
        ],
        capabilities=capabilities,
        blocked_capabilities=[DeviceCapabilityKind.background_service],
        future_capabilities=[capability.kind for capability in capabilities],
        docs_refs=M20_DEVICE_CAPABILITY_DOCS,
        warnings=[
            "M20 is contract-only.",
            "No sensors are implemented.",
            "Device outputs are not trusted control input by default.",
            "Capture cannot silently become memory or trigger external sends.",
        ],
        safe_summary=(
            "M20 Device Capability Broker contract-only manifest; future device "
            "capabilities remain planned and disabled."
        ),
    )
    assert_device_contract_only(manifest)
    return manifest


def _capability(
    kind: DeviceCapabilityKind,
    risk_level: DeviceRiskLevel,
    data_classification: DeviceDataClassification,
    purpose: str,
) -> DeviceCapabilityDescriptor:
    return DeviceCapabilityDescriptor(
        capability_id=f"{kind.value}_contract",
        platform=DevicePlatform.unknown_planned,
        kind=kind,
        status=DeviceCapabilityStatus.future_requires_broker,
        purpose=purpose,
        risk_level=risk_level,
        data_classification=data_classification,
        permission_scope=DevicePermissionScope.foreground_planned,
        safe_summary=f"{kind.value} planning metadata only; no device access is enabled.",
    )
