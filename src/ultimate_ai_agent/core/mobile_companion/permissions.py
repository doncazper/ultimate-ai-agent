from ultimate_ai_agent.core.mobile_companion.contracts import (
    MobilePermissionDecisionPlan,
    MobilePermissionManifest,
)
from ultimate_ai_agent.core.mobile_companion.enums import (
    MobileCapabilityKind,
    MobilePermissionDecision,
)


def default_permission_decisions() -> list[MobilePermissionDecisionPlan]:
    return [
        MobilePermissionDecisionPlan(
            capability=MobileCapabilityKind.approvals_planned,
            decision=MobilePermissionDecision.not_implemented,
            safe_summary="Mobile approval execution is not implemented.",
        ),
        MobilePermissionDecisionPlan(
            capability=MobileCapabilityKind.camera_planned,
            decision=MobilePermissionDecision.requires_future_broker,
            safe_summary="Camera access requires a future Device Capability Broker.",
        ),
        MobilePermissionDecisionPlan(
            capability=MobileCapabilityKind.microphone_planned,
            decision=MobilePermissionDecision.requires_future_broker,
            safe_summary="microphone access requires a future Device Capability Broker.",
        ),
        MobilePermissionDecisionPlan(
            capability=MobileCapabilityKind.location_planned,
            decision=MobilePermissionDecision.requires_future_broker,
            safe_summary="Location access requires a future Device Capability Broker.",
        ),
    ]


def build_default_mobile_permission_manifest() -> MobilePermissionManifest:
    return MobilePermissionManifest(decisions=default_permission_decisions())
