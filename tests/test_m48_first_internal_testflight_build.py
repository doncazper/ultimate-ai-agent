from pathlib import Path

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    FirstInternalTestFlightBuildStatus,
    assert_first_internal_testflight_build_candidate_safe,
    build_default_first_internal_testflight_build_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "apps" / "ccc-ios"


def test_default_m48_first_internal_testflight_build_candidate_is_review_only() -> None:
    candidate = build_default_first_internal_testflight_build_candidate()

    assert candidate.milestone == "M48"
    assert candidate.version == "0.52.0"
    assert candidate.status is FirstInternalTestFlightBuildStatus.reviewed_candidate
    assert candidate.internal_only is True
    assert candidate.review_only_record is True
    assert candidate.first_internal_build_candidate_record is True
    assert candidate.build_candidate_ref.startswith("internal_testflight_build_candidate:")
    assert candidate.pipeline_manifest_ref == "internal_testflight_pipeline_manifest:v0_51_0"
    assert candidate.source_snapshot_ref == "source_snapshot:v0_52_0"
    assert candidate.audit_receipt_ref == "mobile_audit_receipt_plan:v0_52_0_redacted"
    assert candidate.build_execution_performed is False
    assert candidate.archive_created_in_repo is False
    assert candidate.ipa_created_in_repo is False
    assert candidate.testflight_upload_performed is False
    assert candidate.app_store_connect_api_called is False
    assert candidate.signing_asset_storage_enabled is False
    assert candidate.signing_identity_material_stored is False
    assert candidate.provisioning_profile_material_stored is False
    assert candidate.certificate_or_private_key_stored is False
    assert candidate.fastlane_workflow_enabled is False
    assert candidate.ci_upload_workflow_enabled is False
    assert candidate.external_beta_enabled is False
    assert candidate.public_distribution_enabled is False
    assert candidate.production_authority_enabled is False
    assert candidate.mobile_sensor_access_enabled is False
    assert candidate.background_collection_enabled is False
    assert candidate.approval_capture_enabled is False
    assert candidate.approval_execution_enabled is False
    assert candidate.context_injection_enabled is False
    assert candidate.memory_write_enabled is False
    assert candidate.raw_data_export_enabled is False
    assert candidate.export_enabled is False
    assert candidate.execution_enabled is False
    assert candidate.m49_mobile_approval_capture_future is True

    assert_first_internal_testflight_build_candidate_safe(candidate)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("internal_only", False, "internal-only"),
        ("review_only_record", False, "review-only"),
        ("first_internal_build_candidate_record", False, "candidate record"),
        ("m49_mobile_approval_capture_future", False, "M49"),
        ("build_execution_performed", True, "build execution"),
        ("archive_created_in_repo", True, "archive artifact"),
        ("ipa_created_in_repo", True, "IPA artifact"),
        ("testflight_upload_performed", True, "TestFlight upload"),
        ("app_store_connect_api_called", True, "App Store Connect"),
        ("signing_asset_storage_enabled", True, "signing asset"),
        ("signing_identity_material_stored", True, "signing identity"),
        ("provisioning_profile_material_stored", True, "provisioning profile"),
        ("certificate_or_private_key_stored", True, "certificate"),
        ("fastlane_workflow_enabled", True, "Fastlane"),
        ("ci_upload_workflow_enabled", True, "CI upload"),
        ("external_beta_enabled", True, "external beta"),
        ("public_distribution_enabled", True, "public distribution"),
        ("production_authority_enabled", True, "production authority"),
        ("mobile_sensor_access_enabled", True, "sensor"),
        ("background_collection_enabled", True, "background"),
        ("approval_capture_enabled", True, "approval capture"),
        ("approval_execution_enabled", True, "approval execution"),
        ("context_injection_enabled", True, "context injection"),
        ("memory_write_enabled", True, "memory write"),
        ("raw_data_export_enabled", True, "raw data export"),
        ("export_enabled", True, "export"),
        ("execution_enabled", True, "execution"),
    ],
)
def test_m48_candidate_rejects_model_copy_mutated_unsafe_flags(
    field_name: str, value: bool, match: str
) -> None:
    candidate = build_default_first_internal_testflight_build_candidate()
    mutated = candidate.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_first_internal_testflight_build_candidate_safe(mutated)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("build_candidate_ref", "/Users/example/builds/app.ipa", "raw"),
        ("pipeline_manifest_ref", "../private/pipeline", "raw"),
        ("source_snapshot_ref", "source_snapshot:api_key=abc123", "secret"),
        ("audit_receipt_ref", "audit_receipt:password=abc123", "secret"),
        ("redacted_metadata_refs", ["metadata_ref:token=abc123"], "secret"),
        ("safe_summary", "Built from /Users/example/private/App.ipa", "raw"),
    ],
)
def test_m48_candidate_rejects_raw_path_or_secret_like_metadata(
    field_name: str, value: object, match: str
) -> None:
    candidate = build_default_first_internal_testflight_build_candidate()
    mutated = candidate.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_first_internal_testflight_build_candidate_safe(mutated)


def test_m48_no_native_build_upload_or_testflight_artifacts_are_tracked() -> None:
    assert not (IOS_ROOT / "Package.swift").exists()
    assert not list(IOS_ROOT.glob("*.xcodeproj"))
    assert not list(IOS_ROOT.rglob("*.xcworkspace"))
    assert not list(IOS_ROOT.rglob("*.entitlements"))
    assert not list(IOS_ROOT.rglob("Info.plist"))
    assert not list(IOS_ROOT.rglob("ExportOptions.plist"))
    assert not list(IOS_ROOT.rglob("*.xcarchive"))
    assert not list(IOS_ROOT.rglob("*.ipa"))
    assert not list(IOS_ROOT.rglob("*.mobileprovision"))
    assert not list(IOS_ROOT.rglob("*.p8"))
    assert not list(IOS_ROOT.rglob("*.cer"))
    assert not list(IOS_ROOT.rglob("*.p12"))
    assert not list(ROOT.rglob("fastlane"))
