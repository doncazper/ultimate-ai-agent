from ultimate_ai_agent.core.device_capabilities.contracts import (
    DeviceCapabilityReceiptPlan,
)
from ultimate_ai_agent.core.device_capabilities.enums import (
    DeviceCapabilityKind,
    DevicePlatform,
    DeviceReceiptRequirement,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    validate_device_receipt_plan,
)


def build_device_capability_receipt_plan(
    capability_kind: DeviceCapabilityKind,
    platform: DevicePlatform = DevicePlatform.unknown_planned,
) -> DeviceCapabilityReceiptPlan:
    plan = DeviceCapabilityReceiptPlan(
        receipt_plan_id=f"{platform.value}_{capability_kind.value}_receipt_plan",
        platform=platform,
        capability_kind=capability_kind,
        receipt_requirement=DeviceReceiptRequirement.redacted_receipt_required,
        redaction_required=True,
        storage_allowed=False,
        retention_summary="future receipt metadata only; no raw device payload storage",
        safe_summary="device capability receipt planning only",
    )
    return validate_device_receipt_plan(plan)
