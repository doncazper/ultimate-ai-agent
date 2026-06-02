from ultimate_ai_agent.core.device_capabilities.enums import (
    DeviceCapabilityDecisionStatus,
    DeviceCapabilityKind,
    DeviceRiskLevel,
)


HIGH_RISK_DEVICE_CAPABILITIES = {
    DeviceCapabilityKind.camera,
    DeviceCapabilityKind.microphone,
    DeviceCapabilityKind.location,
    DeviceCapabilityKind.contacts,
    DeviceCapabilityKind.calendar,
    DeviceCapabilityKind.photos,
    DeviceCapabilityKind.files,
    DeviceCapabilityKind.local_network,
    DeviceCapabilityKind.screen_capture,
}

CRITICAL_DEVICE_CAPABILITIES = {
    DeviceCapabilityKind.biometrics,
    DeviceCapabilityKind.health,
}


def classify_device_capability_risk(kind: DeviceCapabilityKind) -> DeviceRiskLevel:
    if kind in CRITICAL_DEVICE_CAPABILITIES:
        return DeviceRiskLevel.critical
    if kind in HIGH_RISK_DEVICE_CAPABILITIES:
        return DeviceRiskLevel.high
    if kind == DeviceCapabilityKind.background_service:
        return DeviceRiskLevel.forbidden
    return DeviceRiskLevel.medium


def default_device_capability_decision_status(
    kind: DeviceCapabilityKind,
) -> DeviceCapabilityDecisionStatus:
    if kind == DeviceCapabilityKind.background_service:
        return DeviceCapabilityDecisionStatus.blocked
    if kind in {
        DeviceCapabilityKind.device_identity,
        DeviceCapabilityKind.device_pairing,
    }:
        return DeviceCapabilityDecisionStatus.requires_future_pairing
    return DeviceCapabilityDecisionStatus.requires_future_broker
