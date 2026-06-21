from ultimate_ai_agent.core.device_capabilities import (
    DeviceCapabilityKind,
    DeviceCapabilityStatus,
    DevicePlatform,
    build_default_device_capability_manifest,
)


def test_default_manifest_includes_all_planned_platforms_and_major_capabilities() -> None:
    manifest = build_default_device_capability_manifest()

    assert set(manifest.platforms) >= {
        DevicePlatform.ios_planned,
        DevicePlatform.android_planned,
        DevicePlatform.mobile_web_planned,
        DevicePlatform.macos_planned,
    }

    capabilities_by_kind = {capability.kind: capability for capability in manifest.capabilities}
    for capability_kind in [
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
        DeviceCapabilityKind.background_service,
        DeviceCapabilityKind.device_identity,
        DeviceCapabilityKind.device_pairing,
    ]:
        capability = capabilities_by_kind[capability_kind]
        assert capability.status in {
            DeviceCapabilityStatus.planned_disabled,
            DeviceCapabilityStatus.future_requires_broker,
            DeviceCapabilityStatus.future_requires_pairing,
            DeviceCapabilityStatus.blocked,
        }
        assert capability.allowed_now is False
        assert capability.implemented_now is False
        assert capability.requires_device_capability_broker is True
        assert capability.requires_receipt is True
        assert capability.requires_redaction is True


def test_default_manifest_has_safe_docs_and_warning_refs() -> None:
    manifest = build_default_device_capability_manifest()

    assert "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md" in manifest.docs_refs
    assert "contract-only" in " ".join(manifest.warnings).lower()
    assert "no sensors" in " ".join(manifest.warnings).lower()
