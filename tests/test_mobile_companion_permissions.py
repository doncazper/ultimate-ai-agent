import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileCapabilityKind,
    MobileCapabilityStatus,
    MobileDataClassification,
    MobilePermissionDecision,
    build_default_mobile_permission_manifest,
)
from ultimate_ai_agent.core.mobile_companion.contracts import MobileCapabilityPlan, MobileCaptureIntentPlan
from ultimate_ai_agent.core.mobile_companion.planning import (
    assert_no_silent_memory_write,
    validate_mobile_capability_plan,
    validate_mobile_capture_intent_plan,
)


def test_default_mobile_permission_manifest_denies_runtime_access():
    manifest = build_default_mobile_permission_manifest()

    assert manifest.version == "0.23.1"
    assert manifest.contract_only is True
    assert manifest.os_permission_integration_implemented is False
    assert manifest.background_service_implemented is False
    assert all(decision.decision != MobilePermissionDecision.allowed_contract_only for decision in manifest.decisions)


def test_capability_allowed_now_is_rejected():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.approvals_planned,
        status=MobileCapabilityStatus.contract_only,
        safe_summary="approval status summary only",
        allowed_now=True,
    )

    with pytest.raises(ValueError, match="allowed_now"):
        validate_mobile_capability_plan(capability)


def test_metadata_refs_reject_secret_like_values():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.contacts_planned,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="contact planning metadata only",
        metadata_refs=[
            "api_key=redacted",
            "token=redacted",
            "secret=redacted",
            "password=redacted",
            "Authorization: redacted",
            "Cookie: redacted",
        ],
    )

    with pytest.raises(ValueError, match="secret-like"):
        validate_mobile_capability_plan(capability)


def test_os_permission_integration_flag_is_rejected():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.location_planned,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="location planning metadata only",
        os_permission_integrated=True,
    )

    with pytest.raises(ValueError, match="OS permission"):
        validate_mobile_capability_plan(capability)


def test_background_service_flag_is_rejected():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.location_planned,
        status=MobileCapabilityStatus.future_requires_device_capability_broker,
        safe_summary="location planning metadata only",
        background_service_enabled=True,
    )

    with pytest.raises(ValueError, match="background service"):
        validate_mobile_capability_plan(capability)


def test_sensitive_capture_storage_is_rejected_without_future_policy():
    capture = MobileCaptureIntentPlan(
        capture_ref="capture_plan_sensitive_001",
        capability=MobileCapabilityKind.files_planned,
        data_classification=MobileDataClassification.sensitive,
        safe_summary="sensitive document capture planning only",
        storage_allowed=True,
    )

    with pytest.raises(ValueError, match="storage_allowed"):
        validate_mobile_capture_intent_plan(capture)


def test_automatic_memory_write_is_rejected():
    capture = MobileCaptureIntentPlan(
        capture_ref="capture_plan_memory_001",
        capability=MobileCapabilityKind.photos_planned,
        data_classification=MobileDataClassification.personal,
        safe_summary="redacted photo capture summary only",
        automatic_memory_write=True,
    )

    with pytest.raises(ValueError, match="automatic_memory_write"):
        assert_no_silent_memory_write(capture)
