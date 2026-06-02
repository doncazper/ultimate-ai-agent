import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileCapabilityKind,
    MobileCapabilityStatus,
    MobileDataClassification,
)
from ultimate_ai_agent.core.mobile_companion.contracts import MobileCapabilityPlan, MobileCaptureIntentPlan
from ultimate_ai_agent.core.mobile_companion.planning import (
    assert_no_sensor_access_enabled,
    validate_mobile_capability_plan,
    validate_mobile_capture_intent_plan,
)


def test_sensor_capability_must_remain_disabled_or_future_broker_only():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.camera_planned,
        status=MobileCapabilityStatus.contract_only,
        safe_summary="camera planning metadata only",
    )

    with pytest.raises(ValueError, match="Device Capability Broker"):
        validate_mobile_capability_plan(capability)


def test_sensor_capability_future_broker_status_is_contract_safe():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.location_planned,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="location planning metadata only",
    )

    assert_no_sensor_access_enabled(capability)


def test_silent_capture_and_external_send_are_rejected():
    capture = MobileCaptureIntentPlan(
        capture_ref="capture_plan_silent_001",
        capability=MobileCapabilityKind.microphone_planned,
        data_classification=MobileDataClassification.personal,
        safe_summary="microphone capture planning only",
        silent_capture=True,
        external_send_allowed=True,
    )

    with pytest.raises(ValueError, match="silent_capture"):
        validate_mobile_capture_intent_plan(capture)
