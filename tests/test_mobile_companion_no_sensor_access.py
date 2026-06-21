from typing import Any
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


def test_sensor_capability_must_remain_disabled_or_future_broker_only() -> None:
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.camera_planned,
        status=MobileCapabilityStatus.contract_only,
        safe_summary="camera planning metadata only",
    )

    with pytest.raises(ValueError, match="Device Capability Broker"):
        validate_mobile_capability_plan(capability)


def test_sensor_capability_future_broker_status_is_contract_safe() -> None:
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.location_planned,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="location planning metadata only",
    )

    assert_no_sensor_access_enabled(capability)


@pytest.mark.parametrize(
    "capability_kind",
    [
        MobileCapabilityKind.contacts_planned,
        MobileCapabilityKind.calendar_planned,
    ],
)
def test_contacts_and_calendar_capabilities_cannot_be_enabled(capability_kind: Any) -> None:
    capability = MobileCapabilityPlan(
        capability=capability_kind,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="contact or calendar planning metadata only",
        allowed_now=True,
    )

    with pytest.raises(ValueError, match="allowed_now"):
        validate_mobile_capability_plan(capability)


@pytest.mark.parametrize(
    "capability_kind",
    [
        MobileCapabilityKind.contacts_planned,
        MobileCapabilityKind.calendar_planned,
    ],
)
def test_contacts_and_calendar_capabilities_require_future_broker(capability_kind: Any) -> None:
    capability = MobileCapabilityPlan(
        capability=capability_kind,
        status=MobileCapabilityStatus.planned_disabled,
        safe_summary="contact or calendar planning metadata only",
        requires_device_capability_broker=False,
    )

    with pytest.raises(ValueError, match="Device Capability Broker"):
        validate_mobile_capability_plan(capability)


@pytest.mark.parametrize(
    "capability_kind",
    [
        MobileCapabilityKind.contacts_planned,
        MobileCapabilityKind.calendar_planned,
    ],
)
def test_contacts_and_calendar_capabilities_cannot_be_contract_implemented(capability_kind: Any) -> None:
    capability = MobileCapabilityPlan(
        capability=capability_kind,
        status=MobileCapabilityStatus.contract_only,
        safe_summary="contact or calendar planning metadata only",
    )

    with pytest.raises(ValueError, match="Device Capability Broker"):
        validate_mobile_capability_plan(capability)


def test_silent_capture_and_external_send_are_rejected() -> None:
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


def test_external_send_allowed_is_rejected_independently() -> None:
    capture = MobileCaptureIntentPlan(
        capture_ref="capture_plan_external_send_001",
        capability=MobileCapabilityKind.photos_planned,
        data_classification=MobileDataClassification.personal,
        safe_summary="selected photo capture planning only",
        external_send_allowed=True,
    )

    with pytest.raises(ValueError, match="external_send_allowed"):
        validate_mobile_capture_intent_plan(capture)
