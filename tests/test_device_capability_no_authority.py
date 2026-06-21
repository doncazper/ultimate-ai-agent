import pytest

from ultimate_ai_agent.core.device_capabilities import (
    DeviceCapabilityManifest,
    DevicePlatform,
    DeviceTrustHandshakePlan,
    DeviceTrustState,
)
from ultimate_ai_agent.core.device_capabilities.validation import (
    assert_device_contract_only,
    validate_device_trust_handshake_plan,
)


def test_manifest_rejects_device_client_authority() -> None:
    manifest = DeviceCapabilityManifest(
        manifest_id="device_capability_manifest_authority",
        baseline_version="0.24.0",
        platforms=[DevicePlatform.ios_planned],
        safe_summary="device capability contract manifest",
        device_clients_are_authority=True,
    )

    with pytest.raises(ValueError, match="device clients are not authority"):
        assert_device_contract_only(manifest)


def test_manifest_rejects_trusted_control_input_claim() -> None:
    manifest = DeviceCapabilityManifest(
        manifest_id="device_capability_manifest_trusted_output",
        baseline_version="0.24.0",
        platforms=[DevicePlatform.android_planned],
        safe_summary="device capability contract manifest",
        device_output_is_trusted_control_input=True,
    )

    with pytest.raises(ValueError, match="trusted control input"):
        assert_device_contract_only(manifest)


def test_trust_handshake_plan_rejects_runtime_pairing_claims() -> None:
    plan = DeviceTrustHandshakePlan(
        plan_id="trust_handshake_runtime_claim",
        platform=DevicePlatform.mobile_web_planned,
        trust_state=DeviceTrustState.paired_planned,
        pairing_required=True,
        pairing_runtime_implemented=True,
        safe_summary="future pairing planning only",
    )

    with pytest.raises(ValueError, match="pairing runtime"):
        validate_device_trust_handshake_plan(plan)


def test_trust_handshake_plan_keeps_receipt_and_local_approval_required() -> None:
    plan = DeviceTrustHandshakePlan(
        plan_id="trust_handshake_contract",
        platform=DevicePlatform.macos_planned,
        trust_state=DeviceTrustState.unpaired_planned,
        pairing_required=True,
        local_approval_required=True,
        receipt_required=True,
        safe_summary="future trust handshake planning only",
    )

    validate_device_trust_handshake_plan(plan)
