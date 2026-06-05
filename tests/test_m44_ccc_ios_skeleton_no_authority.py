from pathlib import Path

import pytest

from ultimate_ai_agent.core.mobile_companion import (
    CccIosSkeletonSurfaceKind,
    assert_ccc_ios_skeleton_no_authority,
    build_default_ccc_ios_skeleton_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "apps" / "ccc-ios"
SWIFT_ROOT = IOS_ROOT / "Sources" / "UltimateAIAgentCCC"


def test_default_m44_ccc_ios_skeleton_manifest_is_no_authority() -> None:
    manifest = build_default_ccc_ios_skeleton_manifest()

    assert manifest.milestone == "M44"
    assert manifest.version == "0.48.0"
    assert manifest.source_only_skeleton is True
    assert manifest.no_authority is True
    assert manifest.production_workflow_enabled is False
    assert manifest.signing_or_store_workflow_enabled is False
    assert manifest.network_access_enabled is False
    assert manifest.sensor_access_enabled is False
    assert manifest.os_permission_integration_enabled is False
    assert manifest.approval_capture_enabled is False
    assert manifest.approval_execution_enabled is False
    assert manifest.context_injection_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.execution_enabled is False
    assert manifest.credential_storage_enabled is False
    assert manifest.background_task_enabled is False
    assert manifest.m45_local_read_only_connection_future is True
    assert {surface.kind for surface in manifest.surfaces} >= {
        CccIosSkeletonSurfaceKind.status_overview,
        CccIosSkeletonSurfaceKind.review_packet_preview,
        CccIosSkeletonSurfaceKind.receipt_preview,
        CccIosSkeletonSurfaceKind.authority_boundary,
    }

    assert_ccc_ios_skeleton_no_authority(manifest)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("source_only_skeleton", "source-only"),
        ("no_authority", "no-authority"),
        ("production_workflow_enabled", "production workflow"),
        ("signing_or_store_workflow_enabled", "signing"),
        ("network_access_enabled", "network"),
        ("sensor_access_enabled", "sensor"),
        ("os_permission_integration_enabled", "OS permission"),
        ("approval_capture_enabled", "approval capture"),
        ("approval_execution_enabled", "approval execution"),
        ("context_injection_enabled", "context injection"),
        ("memory_write_enabled", "memory write"),
        ("file_mutation_enabled", "file mutation"),
        ("execution_enabled", "execution"),
        ("credential_storage_enabled", "credential"),
        ("background_task_enabled", "background"),
        ("m45_local_read_only_connection_future", "M45"),
    ],
)
def test_m44_manifest_rejects_model_copy_mutated_authority_flags(
    field_name: str, match: str
) -> None:
    manifest = build_default_ccc_ios_skeleton_manifest()
    value = False if field_name in {"source_only_skeleton", "no_authority", "m45_local_read_only_connection_future"} else True
    mutated = manifest.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_ccc_ios_skeleton_no_authority(mutated)


def test_m44_source_only_ios_skeleton_files_exist_without_build_project() -> None:
    assert (IOS_ROOT / "README.md").is_file()
    assert (SWIFT_ROOT / "UltimateAIAgentCCCApp.swift").is_file()
    assert (SWIFT_ROOT / "ReadOnlyDashboardView.swift").is_file()
    assert (SWIFT_ROOT / "SkeletonFixtures.swift").is_file()

    assert not (IOS_ROOT / "Package.swift").exists()
    assert not list(IOS_ROOT.glob("*.xcodeproj"))
    assert not list(IOS_ROOT.rglob("*.entitlements"))
    assert not list(IOS_ROOT.rglob("Info.plist"))


def test_m44_swift_skeleton_has_no_authority_apis() -> None:
    swift_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in SWIFT_ROOT.rglob("*.swift")
    ).lower()

    assert "swiftui" in swift_text
    assert "mock" in swift_text
    assert "non-authoritative" in swift_text
    assert "read-only" in swift_text

    forbidden_fragments = [
        "urlsession",
        "alamofire",
        "cllocationmanager",
        "avcapture",
        "phphoto",
        "contacts",
        "eventkit",
        "usernotifications",
        "keychain",
        "secitem",
        "filemanager.default",
        "process(",
        "wkwebview",
        "approvalcapture",
        "approvalexecution",
        "contextinjection",
        "memorywrite",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in swift_text
