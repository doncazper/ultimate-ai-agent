from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.platform_capabilities import (
    PlatformArchitectureBucket,
    PlatformCapabilityAuthority,
    PlatformCapabilityAuthorityState,
    PlatformCapabilityFamily,
    PlatformCapabilityRecord,
    PlatformCapabilitySnapshot,
    PlatformCapabilityState,
    PlatformIdentity,
    PlatformInstallerPosture,
    PlatformIntegrationPosture,
    PlatformOSBucket,
    build_platform_capability_snapshot,
    detect_platform_identity,
)


def test_detect_platform_identity_safe_buckets(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        ("Darwin", "arm64", "23.0.0", PlatformOSBucket.macos, PlatformArchitectureBucket.arm64),
        ("Windows", "AMD64", "10", PlatformOSBucket.windows, PlatformArchitectureBucket.x86_64),
        ("Linux", "x86_64", "6.8.0", PlatformOSBucket.linux, PlatformArchitectureBucket.x86_64),
        (
            "Linux",
            "x86_64",
            "5.15.90.1-microsoft-standard-WSL2",
            PlatformOSBucket.wsl,
            PlatformArchitectureBucket.x86_64,
        ),
        ("", "", "", PlatformOSBucket.unknown, PlatformArchitectureBucket.unknown),
    ]

    for system_value, machine_value, release_value, expected_os, expected_arch in cases:
        _patch_platform(monkeypatch, system_value, machine_value, release_value)
        identity = detect_platform_identity()

        assert identity.os == expected_os
        assert identity.architecture == expected_arch
        assert identity.raw_system_value_included is False
        assert identity.raw_machine_value_included is False
        assert identity.raw_hostname_included is False
        assert identity.raw_username_included is False
        assert identity.raw_path_included is False
        assert identity.env_dump_included is False
        assert identity.subprocess_execution_performed is False
        assert identity.filesystem_scan_performed is False
        assert identity.network_call_performed is False
        assert identity.credential_read_performed is False


def test_snapshot_contains_all_capability_families_for_macos_and_windows() -> None:
    for os_bucket in [PlatformOSBucket.macos, PlatformOSBucket.windows]:
        snapshot = build_platform_capability_snapshot(_identity(os_bucket))

        assert {record.family for record in snapshot.capabilities} == set(PlatformCapabilityFamily)
        assert snapshot.blocked_by_default is True
        assert snapshot.metadata_only is True
        assert snapshot.no_authority_granted is True
        assert snapshot.installer_side_effects_enabled is False
        assert snapshot.platform_probe_performed is False
        assert snapshot.summary["windows_first_class_posture"] is True
        assert all(record.platform_os == os_bucket for record in snapshot.capabilities)
        assert all(record.metadata_only is True for record in snapshot.capabilities)
        assert all(record.runtime_action_performed is False for record in snapshot.capabilities)
        assert all(record.install_action_performed is False for record in snapshot.capabilities)
        assert all(record.network_call_performed is False for record in snapshot.capabilities)
        assert all(record.credential_read_performed is False for record in snapshot.capabilities)
        assert all(record.provider_call_performed is False for record in snapshot.capabilities)


def test_snapshot_builder_uses_non_authorizing_states_only() -> None:
    allowed_states = {
        PlatformCapabilityState.metadata_only,
        PlatformCapabilityState.readiness_only,
        PlatformCapabilityState.blocked,
        PlatformCapabilityState.planned_disabled,
        PlatformCapabilityState.unsupported,
        PlatformCapabilityState.not_configured,
    }

    snapshot = build_platform_capability_snapshot(_identity(PlatformOSBucket.windows))

    assert set(PlatformCapabilityState) == allowed_states
    assert {record.state for record in snapshot.capabilities}.issubset(allowed_states)
    assert {record.authority.state for record in snapshot.capabilities}.issubset(
        {
            PlatformCapabilityAuthorityState.metadata_only,
            PlatformCapabilityAuthorityState.readiness_only,
            PlatformCapabilityAuthorityState.blocked,
        }
    )
    assert all(record.authority.runtime_authority_granted is False for record in snapshot.capabilities)
    assert all(record.authority.install_authority_granted is False for record in snapshot.capabilities)
    assert all(record.authority.read_authority_granted is False for record in snapshot.capabilities)
    assert all(record.authority.write_authority_granted is False for record in snapshot.capabilities)
    assert all(record.authority.provider_authority_granted is False for record in snapshot.capabilities)


def test_capability_records_reject_authority_and_side_effect_claims() -> None:
    with pytest.raises(ValidationError, match="PLATFORM_CAPABILITY_CREDENTIAL_READ_DENIED"):
        _safe_record(credential_read_performed=True)

    with pytest.raises(ValidationError, match="PLATFORM_CAPABILITY_RAW_PROVIDER_PAYLOAD_DENIED"):
        _safe_record(raw_provider_payload_included=True)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("raw_system_value_included", "PLATFORM_IDENTITY_RAW_SYSTEM_DENIED"),
        ("raw_machine_value_included", "PLATFORM_IDENTITY_RAW_MACHINE_DENIED"),
        ("raw_release_value_included", "PLATFORM_IDENTITY_RAW_RELEASE_DENIED"),
        ("raw_hostname_included", "PLATFORM_IDENTITY_HOSTNAME_DENIED"),
        ("raw_username_included", "PLATFORM_IDENTITY_USERNAME_DENIED"),
        ("raw_path_included", "PLATFORM_IDENTITY_RAW_PATH_DENIED"),
        ("env_dump_included", "PLATFORM_IDENTITY_ENV_DUMP_DENIED"),
        ("raw_serial_included", "PLATFORM_IDENTITY_SERIAL_DENIED"),
        ("filesystem_scan_performed", "PLATFORM_IDENTITY_FILESYSTEM_SCAN_DENIED"),
        ("subprocess_execution_performed", "PLATFORM_IDENTITY_SUBPROCESS_DENIED"),
        ("network_call_performed", "PLATFORM_IDENTITY_NETWORK_DENIED"),
        ("credential_read_performed", "PLATFORM_IDENTITY_CREDENTIAL_READ_DENIED"),
    ],
)
def test_identity_rejects_every_raw_private_or_probe_flag(field_name: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        PlatformIdentity(
            os=PlatformOSBucket.macos,
            architecture=PlatformArchitectureBucket.arm64,
            **{field_name: True},
        )


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("runtime_authority_granted", "PLATFORM_AUTHORITY_RUNTIME_DENIED"),
        ("install_authority_granted", "PLATFORM_AUTHORITY_INSTALL_DENIED"),
        ("read_authority_granted", "PLATFORM_AUTHORITY_READ_DENIED"),
        ("write_authority_granted", "PLATFORM_AUTHORITY_WRITE_DENIED"),
        ("credential_authority_granted", "PLATFORM_AUTHORITY_CREDENTIAL_DENIED"),
        ("provider_authority_granted", "PLATFORM_AUTHORITY_PROVIDER_DENIED"),
        ("service_authority_granted", "PLATFORM_AUTHORITY_SERVICE_DENIED"),
        ("permission_grant_captured", "PLATFORM_AUTHORITY_PERMISSION_CAPTURE_DENIED"),
        ("approval_ref_as_authority", "PLATFORM_AUTHORITY_APPROVAL_REF_DENIED"),
        ("production_authority_granted", "PLATFORM_AUTHORITY_PRODUCTION_DENIED"),
    ],
)
def test_authority_rejects_every_grant_flag(field_name: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        PlatformCapabilityAuthority(
            authority_ref="platform-authority:test",
            **{field_name: True},
        )


@pytest.mark.parametrize("state", list(PlatformCapabilityAuthorityState))
def test_authority_states_are_non_authorizing_placeholders(
    state: PlatformCapabilityAuthorityState,
) -> None:
    authority = PlatformCapabilityAuthority(
        authority_ref=f"platform-authority:test-{state.value}",
        state=state,
    )

    assert authority.runtime_authority_granted is False
    assert authority.install_authority_granted is False
    assert authority.read_authority_granted is False
    assert authority.write_authority_granted is False
    assert authority.credential_authority_granted is False
    assert authority.provider_authority_granted is False
    assert authority.service_authority_granted is False
    assert authority.permission_grant_captured is False
    assert authority.approval_ref_as_authority is False
    assert authority.production_authority_granted is False


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("side_effects_enabled", "PLATFORM_INSTALLER_SIDE_EFFECTS_DENIED"),
        ("installer_executed", "PLATFORM_INSTALLER_EXECUTION_DENIED"),
        ("file_write_performed", "PLATFORM_INSTALLER_FILE_WRITE_DENIED"),
        ("service_changed", "PLATFORM_INSTALLER_SERVICE_CHANGE_DENIED"),
        ("startup_item_changed", "PLATFORM_INSTALLER_STARTUP_CHANGE_DENIED"),
        ("subprocess_execution_performed", "PLATFORM_INSTALLER_SUBPROCESS_DENIED"),
        ("provider_call_performed", "PLATFORM_INSTALLER_PROVIDER_CALL_DENIED"),
    ],
)
def test_installer_posture_rejects_every_side_effect_flag(field_name: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        PlatformInstallerPosture(
            posture_ref="platform-installer-posture:test",
            channel_ref="platform-installer-channel:test",
            safe_summary="Safe metadata only installer posture for validation tests.",
            **{field_name: True},
        )

    with pytest.raises(ValidationError, match="PLATFORM_INSTALLER_METADATA_ONLY_REQUIRED"):
        PlatformInstallerPosture(
            posture_ref="platform-installer-posture:test",
            channel_ref="platform-installer-channel:test",
            safe_summary="Safe metadata only installer posture for validation tests.",
            metadata_only=False,
        )


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("configured", "PLATFORM_INTEGRATION_CONFIGURED_CLAIM_DENIED"),
        ("permission_prompted", "PLATFORM_INTEGRATION_PERMISSION_PROMPT_DENIED"),
        ("os_data_read_performed", "PLATFORM_INTEGRATION_OS_DATA_READ_DENIED"),
        ("credential_read_performed", "PLATFORM_INTEGRATION_CREDENTIAL_READ_DENIED"),
        ("provider_call_performed", "PLATFORM_INTEGRATION_PROVIDER_CALL_DENIED"),
        ("network_call_performed", "PLATFORM_INTEGRATION_NETWORK_DENIED"),
        ("service_check_performed", "PLATFORM_INTEGRATION_SERVICE_CHECK_DENIED"),
        ("raw_payload_included", "PLATFORM_INTEGRATION_RAW_PAYLOAD_DENIED"),
    ],
)
def test_integration_posture_rejects_every_probe_or_config_claim(field_name: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        PlatformIntegrationPosture(
            integration_ref="platform-integration:test",
            adapter_ref="platform-adapter:test",
            safe_summary="Safe metadata only integration posture for validation tests.",
            **{field_name: True},
        )

    with pytest.raises(ValidationError, match="PLATFORM_INTEGRATION_METADATA_ONLY_REQUIRED"):
        PlatformIntegrationPosture(
            integration_ref="platform-integration:test",
            adapter_ref="platform-adapter:test",
            safe_summary="Safe metadata only integration posture for validation tests.",
            metadata_only=False,
        )


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("runtime_action_performed", "PLATFORM_CAPABILITY_RUNTIME_ACTION_DENIED"),
        ("install_action_performed", "PLATFORM_CAPABILITY_INSTALL_ACTION_DENIED"),
        ("filesystem_scan_performed", "PLATFORM_CAPABILITY_FILESYSTEM_SCAN_DENIED"),
        ("subprocess_execution_performed", "PLATFORM_CAPABILITY_SUBPROCESS_DENIED"),
        ("network_call_performed", "PLATFORM_CAPABILITY_NETWORK_DENIED"),
        ("credential_read_performed", "PLATFORM_CAPABILITY_CREDENTIAL_READ_DENIED"),
        ("calendar_read_performed", "PLATFORM_CAPABILITY_CALENDAR_READ_DENIED"),
        ("email_read_performed", "PLATFORM_CAPABILITY_EMAIL_READ_DENIED"),
        ("message_read_performed", "PLATFORM_CAPABILITY_MESSAGE_READ_DENIED"),
        ("service_started", "PLATFORM_CAPABILITY_SERVICE_START_DENIED"),
        ("provider_call_performed", "PLATFORM_CAPABILITY_PROVIDER_CALL_DENIED"),
        ("file_write_performed", "PLATFORM_CAPABILITY_FILE_WRITE_DENIED"),
        ("permission_prompted", "PLATFORM_CAPABILITY_PERMISSION_PROMPT_DENIED"),
        ("authentication_performed", "PLATFORM_CAPABILITY_AUTH_DENIED"),
        ("raw_username_included", "PLATFORM_CAPABILITY_USERNAME_DENIED"),
        ("raw_hostname_included", "PLATFORM_CAPABILITY_HOSTNAME_DENIED"),
        ("raw_path_included", "PLATFORM_CAPABILITY_RAW_PATH_DENIED"),
        ("env_dump_included", "PLATFORM_CAPABILITY_ENV_DUMP_DENIED"),
        ("raw_log_included", "PLATFORM_CAPABILITY_RAW_LOG_DENIED"),
        ("credential_material_included", "PLATFORM_CAPABILITY_CREDENTIAL_MATERIAL_DENIED"),
        ("raw_prompt_included", "PLATFORM_CAPABILITY_RAW_PROMPT_DENIED"),
        ("raw_response_included", "PLATFORM_CAPABILITY_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_included", "PLATFORM_CAPABILITY_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("production_authority_granted", "PLATFORM_CAPABILITY_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_capability_record_rejects_every_probe_private_or_authority_flag(
    field_name: str,
    reason: str,
) -> None:
    with pytest.raises(ValidationError, match=reason):
        _safe_record(**{field_name: True})


def test_capability_record_rejects_metadata_authority_and_private_metadata() -> None:
    with pytest.raises(ValidationError, match="PLATFORM_CAPABILITY_METADATA_ONLY_REQUIRED"):
        _safe_record(metadata_only=False)

    with pytest.raises(ValidationError, match="METADATA_RAW_PATH_DENIED"):
        _safe_record(metadata={"diagnostic": "/Users/example/private path should not appear"})

    with pytest.raises(ValidationError, match="METADATA_SECRET_LIKE"):
        _safe_record(metadata={"diagnostic": "api_key = abcdefghijklmnopqrst"})


def test_private_or_raw_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="PLATFORM_IDENTITY_HOSTNAME_DENIED"):
        PlatformIdentity(
            os=PlatformOSBucket.macos,
            architecture=PlatformArchitectureBucket.arm64,
            raw_hostname_included=True,
        )

    with pytest.raises(ValidationError, match="SAFE_SUMMARY_RAW_PATH_DENIED"):
        PlatformIntegrationPosture(
            integration_ref="platform-integration:test",
            adapter_ref="platform-adapter:test",
            safe_summary="/Users/example/private path should not appear",
        )

    with pytest.raises(ValidationError, match="SAFE_SUMMARY_SECRET_LIKE"):
        PlatformIntegrationPosture(
            integration_ref="platform-integration:test",
            adapter_ref="platform-adapter:test",
            safe_summary="token = abcdefghijklmnopqrst",
        )


def test_snapshot_rejects_missing_canonical_family() -> None:
    full_snapshot = build_platform_capability_snapshot(_identity(PlatformOSBucket.macos))

    with pytest.raises(ValidationError, match="PLATFORM_SNAPSHOT_CANONICAL_FAMILIES_REQUIRED"):
        PlatformCapabilitySnapshot(
            platform_identity=full_snapshot.platform_identity,
            capabilities=full_snapshot.capabilities[:-1],
        )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"blocked_by_default": False}, "PLATFORM_SNAPSHOT_BLOCKED_BY_DEFAULT_REQUIRED"),
        ({"metadata_only": False}, "PLATFORM_SNAPSHOT_METADATA_ONLY_REQUIRED"),
        ({"no_authority_granted": False}, "PLATFORM_SNAPSHOT_NO_AUTHORITY_REQUIRED"),
        ({"installer_side_effects_enabled": True}, "PLATFORM_SNAPSHOT_INSTALLER_SIDE_EFFECTS_DENIED"),
        ({"platform_probe_performed": True}, "PLATFORM_SNAPSHOT_PLATFORM_PROBE_DENIED"),
    ],
)
def test_snapshot_rejects_authority_probe_and_side_effect_claims(
    overrides: dict[str, Any],
    reason: str,
) -> None:
    full_snapshot = build_platform_capability_snapshot(_identity(PlatformOSBucket.macos))

    with pytest.raises(ValidationError, match=reason):
        PlatformCapabilitySnapshot(
            platform_identity=full_snapshot.platform_identity,
            capabilities=full_snapshot.capabilities,
            **overrides,
        )


def test_cli_inspection_script_returns_same_safe_schema() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "inspect_platform_capabilities.py"
    spec = importlib.util.spec_from_file_location("inspect_platform_capabilities", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    payload = module.build_cli_payload()

    assert payload["snapshot_ref"] == "platform-capability-snapshot:metadata-readiness"
    assert payload["metadata_only"] is True
    assert payload["no_authority_granted"] is True
    assert payload["installer_side_effects_enabled"] is False
    assert payload["platform_probe_performed"] is False
    assert {record["family"] for record in payload["capabilities"]} == {
        family.value for family in PlatformCapabilityFamily
    }
    assert all(record["metadata_only"] is True for record in payload["capabilities"])
    assert all(record["authority"]["runtime_authority_granted"] is False for record in payload["capabilities"])
    assert all(record["authority"]["install_authority_granted"] is False for record in payload["capabilities"])


def _patch_platform(
    monkeypatch: pytest.MonkeyPatch,
    system_value: str,
    machine_value: str,
    release_value: str,
) -> None:
    monkeypatch.setattr(
        "ultimate_ai_agent.core.platform_capabilities.contracts.platform.system",
        lambda: system_value,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.core.platform_capabilities.contracts.platform.machine",
        lambda: machine_value,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.core.platform_capabilities.contracts.platform.release",
        lambda: release_value,
    )


def _identity(os_bucket: PlatformOSBucket) -> PlatformIdentity:
    return PlatformIdentity(
        os=os_bucket,
        architecture=PlatformArchitectureBucket.arm64
        if os_bucket == PlatformOSBucket.macos
        else PlatformArchitectureBucket.x86_64,
    )


def _safe_record(**overrides: Any) -> PlatformCapabilityRecord:
    payload: dict[str, Any] = {
        "record_ref": "platform-capability:test",
        "family": PlatformCapabilityFamily.secure_credential_store,
        "platform_os": PlatformOSBucket.macos,
        "state": PlatformCapabilityState.metadata_only,
        "safe_label": "Test capability",
        "safe_summary": "Safe metadata only capability record for validation tests.",
        "authority": PlatformCapabilityAuthority(
            authority_ref="platform-authority:test",
            state=PlatformCapabilityAuthorityState.metadata_only,
        ),
        "integration_posture": PlatformIntegrationPosture(
            integration_ref="platform-integration:test",
            state=PlatformCapabilityState.metadata_only,
            adapter_ref="platform-adapter:test",
            safe_summary="Safe metadata only integration posture for validation tests.",
        ),
    }
    payload.update(overrides)
    return PlatformCapabilityRecord(**payload)
