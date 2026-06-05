from pathlib import Path

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    InternalTestFlightPipelineStageKind,
    assert_internal_testflight_pipeline_safe,
    build_default_internal_testflight_pipeline_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "apps" / "ccc-ios"


def test_default_m47_testflight_manifest_is_internal_contract_only() -> None:
    manifest = build_default_internal_testflight_pipeline_manifest()

    assert manifest.milestone == "M47"
    assert manifest.version == "0.51.0"
    assert manifest.internal_only is True
    assert manifest.pipeline_contract_only is True
    assert manifest.build_execution_enabled is False
    assert manifest.upload_execution_enabled is False
    assert manifest.signing_asset_storage_enabled is False
    assert manifest.signing_identity_configured is False
    assert manifest.provisioning_profile_configured is False
    assert manifest.app_store_connect_api_enabled is False
    assert manifest.credentials_or_cookies_handling_enabled is False
    assert manifest.external_beta_enabled is False
    assert manifest.public_distribution_enabled is False
    assert manifest.production_authority_enabled is False
    assert manifest.mobile_sensor_access_enabled is False
    assert manifest.background_collection_enabled is False
    assert manifest.approval_capture_enabled is False
    assert manifest.approval_execution_enabled is False
    assert manifest.context_injection_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.raw_data_enabled is False
    assert manifest.export_enabled is False
    assert manifest.execution_enabled is False
    assert manifest.m48_first_internal_build_future is True
    assert {stage.kind for stage in manifest.stages} >= {
        InternalTestFlightPipelineStageKind.source_snapshot,
        InternalTestFlightPipelineStageKind.build_archive_plan,
        InternalTestFlightPipelineStageKind.signing_asset_presence_check,
        InternalTestFlightPipelineStageKind.internal_distribution_review,
        InternalTestFlightPipelineStageKind.rollback_plan,
        InternalTestFlightPipelineStageKind.audit_receipt_plan,
    }

    assert_internal_testflight_pipeline_safe(manifest)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("internal_only", False, "internal-only"),
        ("pipeline_contract_only", False, "contract"),
        ("build_execution_enabled", True, "build execution"),
        ("upload_execution_enabled", True, "upload execution"),
        ("signing_asset_storage_enabled", True, "signing asset"),
        ("signing_identity_configured", True, "signing identity"),
        ("provisioning_profile_configured", True, "provisioning profile"),
        ("app_store_connect_api_enabled", True, "App Store Connect"),
        ("credentials_or_cookies_handling_enabled", True, "credential"),
        ("external_beta_enabled", True, "external beta"),
        ("public_distribution_enabled", True, "public distribution"),
        ("production_authority_enabled", True, "production authority"),
        ("mobile_sensor_access_enabled", True, "sensor"),
        ("background_collection_enabled", True, "background"),
        ("approval_capture_enabled", True, "approval capture"),
        ("approval_execution_enabled", True, "approval execution"),
        ("context_injection_enabled", True, "context injection"),
        ("memory_write_enabled", True, "memory write"),
        ("raw_data_enabled", True, "raw data"),
        ("export_enabled", True, "export"),
        ("execution_enabled", True, "execution"),
        ("m48_first_internal_build_future", False, "M48"),
    ],
)
def test_m47_manifest_rejects_model_copy_mutated_unsafe_flags(
    field_name: str, value: bool, match: str
) -> None:
    manifest = build_default_internal_testflight_pipeline_manifest()
    mutated = manifest.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_internal_testflight_pipeline_safe(mutated)


def test_m47_manifest_rejects_duplicate_or_executing_stages() -> None:
    manifest = build_default_internal_testflight_pipeline_manifest()
    duplicate = manifest.stages[0].model_copy()
    duplicate_manifest = manifest.model_copy(update={"stages": [*manifest.stages, duplicate]})

    with pytest.raises(ValueError, match="duplicate"):
        assert_internal_testflight_pipeline_safe(duplicate_manifest)

    unsafe_stage = manifest.stages[0].model_copy(
        update={"executes_build": True, "uploads_build": True}
    )
    unsafe_manifest = manifest.model_copy(update={"stages": [unsafe_stage, *manifest.stages[1:]]})

    with pytest.raises(ValueError, match="build execution"):
        assert_internal_testflight_pipeline_safe(unsafe_manifest)


def test_m47_no_signing_build_upload_or_testflight_artifacts_exist() -> None:
    assert not (IOS_ROOT / "Package.swift").exists()
    assert not list(IOS_ROOT.glob("*.xcodeproj"))
    assert not list(IOS_ROOT.rglob("*.xcworkspace"))
    assert not list(IOS_ROOT.rglob("*.entitlements"))
    assert not list(IOS_ROOT.rglob("Info.plist"))
    assert not list(IOS_ROOT.rglob("ExportOptions.plist"))
    assert not list(IOS_ROOT.rglob("*.mobileprovision"))
    assert not list(IOS_ROOT.rglob("*.p8"))
    assert not list(IOS_ROOT.rglob("*.cer"))
    assert not list(IOS_ROOT.rglob("*.p12"))
    assert not list(ROOT.rglob("fastlane"))
