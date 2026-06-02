import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.mobile_companion import (
    MobileCapabilityKind,
    MobileCapabilityStatus,
    MobileClientPlatform,
    MobileCompanionSurface,
    build_default_mobile_companion_manifest,
)
from ultimate_ai_agent.core.mobile_companion.contracts import MobileCapabilityPlan, MobileClientPlan
from ultimate_ai_agent.core.mobile_companion.planning import assert_mobile_contract_only


def test_default_mobile_companion_manifest_is_contract_only_and_not_authority():
    manifest = build_default_mobile_companion_manifest()

    assert manifest.milestone == "M19"
    assert manifest.version == "0.23.0"
    assert manifest.contract_only is True
    assert manifest.mobile_client_is_authority is False
    assert manifest.mobile_approval_execution_implemented is False
    assert manifest.device_capability_broker_required is True
    assert manifest.sensor_access_enabled is False
    assert {client.platform for client in manifest.clients} >= {
        MobileClientPlatform.ios_planned,
        MobileClientPlatform.android_planned,
        MobileClientPlatform.mobile_web_planned,
    }
    assert all(not capability.allowed_now for capability in manifest.capabilities)

    assert_mobile_contract_only(manifest)


def test_mobile_client_plan_forbids_extra_fields_and_authority_claims():
    with pytest.raises(ValidationError):
        MobileClientPlan(
            platform=MobileClientPlatform.ios_planned,
            surfaces=[MobileCompanionSurface.approval_status_planned],
            safe_summary="future iOS control surface",
            authority_claimed=False,
            implemented_now=False,
            unexpected_native_runtime=True,
        )


def test_mobile_capability_plan_defaults_to_disabled_contract_only():
    capability = MobileCapabilityPlan(
        capability=MobileCapabilityKind.notifications_planned,
        status=MobileCapabilityStatus.contract_only,
        safe_summary="notification planning metadata only",
    )

    assert capability.allowed_now is False
    assert capability.os_permission_integrated is False
    assert capability.background_service_enabled is False
    assert capability.requires_device_capability_broker is True
