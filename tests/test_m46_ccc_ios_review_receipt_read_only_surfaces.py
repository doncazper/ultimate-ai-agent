from pathlib import Path

import pytest

import scripts.verify_all as verify_all
from ultimate_ai_agent.core.mobile_companion import (
    CccIosReviewReceiptSurfaceKind,
    assert_ccc_ios_review_receipt_read_only_surfaces_safe,
    build_default_ccc_ios_review_receipt_read_only_surface_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "apps" / "ccc-ios"
SWIFT_ROOT = IOS_ROOT / "Sources" / "UltimateAIAgentCCC"


def test_default_m46_review_receipt_manifest_is_source_only_and_read_only() -> None:
    manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()

    assert manifest.milestone == "M46"
    assert manifest.version == "0.50.0"
    assert manifest.source_only is True
    assert manifest.read_only is True
    assert manifest.redacted_summary_only is True
    assert manifest.non_authoritative is True
    assert manifest.backend_routes_added is False
    assert manifest.network_runtime_enabled is False
    assert manifest.raw_data_enabled is False
    assert manifest.approval_capture_enabled is False
    assert manifest.approval_execution_enabled is False
    assert manifest.context_injection_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.export_enabled is False
    assert manifest.execution_enabled is False
    assert manifest.background_collection_enabled is False
    assert manifest.sensor_access_enabled is False
    assert manifest.credential_or_cookie_handling_enabled is False
    assert manifest.native_build_workflow_enabled is False
    assert manifest.signing_or_store_workflow_enabled is False
    assert manifest.testflight_pipeline_enabled is False
    assert manifest.production_authority_enabled is False
    assert manifest.m47_testflight_pipeline_future is True
    assert {surface.kind for surface in manifest.surfaces} >= {
        CccIosReviewReceiptSurfaceKind.review_packet_summary,
        CccIosReviewReceiptSurfaceKind.review_packet_detail,
        CccIosReviewReceiptSurfaceKind.receipt_summary,
        CccIosReviewReceiptSurfaceKind.receipt_detail,
        CccIosReviewReceiptSurfaceKind.authority_boundary,
    }

    assert_ccc_ios_review_receipt_read_only_surfaces_safe(manifest)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("source_only", False, "source-only"),
        ("read_only", False, "read-only"),
        ("redacted_summary_only", False, "redacted summary"),
        ("non_authoritative", False, "non-authoritative"),
        ("backend_routes_added", True, "backend route"),
        ("network_runtime_enabled", True, "network runtime"),
        ("raw_data_enabled", True, "raw data"),
        ("approval_capture_enabled", True, "approval capture"),
        ("approval_execution_enabled", True, "approval execution"),
        ("context_injection_enabled", True, "context injection"),
        ("memory_write_enabled", True, "memory write"),
        ("file_mutation_enabled", True, "file mutation"),
        ("export_enabled", True, "export"),
        ("execution_enabled", True, "execution"),
        ("background_collection_enabled", True, "background"),
        ("sensor_access_enabled", True, "sensor"),
        ("credential_or_cookie_handling_enabled", True, "credential"),
        ("native_build_workflow_enabled", True, "native build"),
        ("signing_or_store_workflow_enabled", True, "signing"),
        ("testflight_pipeline_enabled", True, "TestFlight"),
        ("production_authority_enabled", True, "production authority"),
        ("m47_testflight_pipeline_future", False, "M47"),
    ],
)
def test_m46_manifest_rejects_model_copy_mutated_unsafe_flags(
    field_name: str, value: bool, match: str
) -> None:
    manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()
    mutated = manifest.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_ccc_ios_review_receipt_read_only_surfaces_safe(mutated)


def test_m46_manifest_rejects_duplicate_or_mutating_surfaces() -> None:
    manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()
    duplicate = manifest.surfaces[0].model_copy()
    duplicate_manifest = manifest.model_copy(update={"surfaces": [*manifest.surfaces, duplicate]})

    with pytest.raises(ValueError, match="duplicate"):
        assert_ccc_ios_review_receipt_read_only_surfaces_safe(duplicate_manifest)

    unsafe_surface = manifest.surfaces[0].model_copy(
        update={"approval_capture_enabled": True, "raw_payload_display_enabled": True}
    )
    unsafe_manifest = manifest.model_copy(update={"surfaces": [unsafe_surface, *manifest.surfaces[1:]]})

    with pytest.raises(ValueError, match="raw payload"):
        assert_ccc_ios_review_receipt_read_only_surfaces_safe(unsafe_manifest)


def test_m46_swift_source_adds_review_receipt_surfaces_without_runtime_authority() -> None:
    assert (SWIFT_ROOT / "ReviewReceiptReadOnlyModels.swift").is_file()

    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in SWIFT_ROOT.rglob("*.swift"))
    lowered = swift_text.lower()
    assert "review/receipt read-only surfaces" in lowered
    assert "redacted review packet summary" in lowered
    assert "redacted receipt summary" in lowered
    assert "mock non-authoritative" in lowered
    assert "no approval capture" in lowered
    assert "no raw data" in lowered
    assert "no runtime network call" in lowered

    forbidden_fragments = [
        "URLSession",
        "Alamofire",
        "URLRequest",
        "NWConnection",
        "CL" + "Location" + "Manager",
        "AV" + "Capture",
        "UserNotifications",
        "Keychain",
        "SecItem",
        "FileManager.default",
        "Process(",
        "approvalCapture",
        "approvalExecution",
        "contextInjection",
        "memoryWrite",
        "backgroundTask",
        "ExportOptions",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in swift_text


def test_m46_no_native_project_build_signing_or_testflight_files() -> None:
    assert not (IOS_ROOT / "Package.swift").exists()
    assert not list(IOS_ROOT.glob("*.xcodeproj"))
    assert not list(IOS_ROOT.rglob("*.entitlements"))
    assert not list(IOS_ROOT.rglob("Info.plist"))
    assert not list(IOS_ROOT.rglob("ExportOptions.plist"))
    assert not list(IOS_ROOT.rglob("*.mobileprovision"))


def test_m46_verifier_allows_only_source_only_review_receipt_files() -> None:
    assert verify_all._is_m46_allowed_ccc_ios_review_receipt_file("apps/ccc-ios/README.md")
    assert verify_all._is_m46_allowed_ccc_ios_review_receipt_file(
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReviewReceiptReadOnlyModels.swift"
    )
    assert not verify_all._is_m46_allowed_ccc_ios_review_receipt_file("apps/ccc-ios/Package.swift")
    assert not verify_all._is_m46_allowed_ccc_ios_review_receipt_file("apps/ccc-ios/App.xcodeproj/project.pbxproj")
    assert not verify_all._is_m46_allowed_ccc_ios_review_receipt_file("apps/ccc-ios/Info.plist")
