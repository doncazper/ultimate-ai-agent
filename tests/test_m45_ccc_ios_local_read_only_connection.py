from pathlib import Path

import pytest

import scripts.verify_all as verify_all
from ultimate_ai_agent.core.mobile_companion import (
    CccIosLocalConnectionEndpointKind,
    assert_ccc_ios_local_read_only_connection_safe,
    build_default_ccc_ios_local_read_only_connection_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "apps" / "ccc-ios"
SWIFT_ROOT = IOS_ROOT / "Sources" / "UltimateAIAgentCCC"


def test_default_m45_local_connection_manifest_is_read_only_and_local() -> None:
    manifest = build_default_ccc_ios_local_read_only_connection_manifest()

    assert manifest.milestone == "M45"
    assert manifest.version == "0.49.0"
    assert manifest.local_only is True
    assert manifest.read_only is True
    assert manifest.connection_runtime_enabled is False
    assert manifest.backend_routes_added is False
    assert manifest.network_runtime_enabled is False
    assert manifest.external_network_enabled is False
    assert manifest.approval_capture_enabled is False
    assert manifest.approval_execution_enabled is False
    assert manifest.raw_data_enabled is False
    assert manifest.context_injection_enabled is False
    assert manifest.memory_write_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.execution_enabled is False
    assert manifest.background_collection_enabled is False
    assert manifest.sensor_access_enabled is False
    assert manifest.credential_or_cookie_handling_enabled is False
    assert manifest.production_authority_enabled is False
    assert manifest.m46_review_receipt_surfaces_future is True
    assert {endpoint.kind for endpoint in manifest.endpoints} >= {
        CccIosLocalConnectionEndpointKind.manifest_summary,
        CccIosLocalConnectionEndpointKind.review_packet_summary,
        CccIosLocalConnectionEndpointKind.receipt_summary,
    }

    assert_ccc_ios_local_read_only_connection_safe(manifest)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("local_only", False, "local-only"),
        ("read_only", False, "read-only"),
        ("connection_runtime_enabled", True, "runtime"),
        ("backend_routes_added", True, "backend route"),
        ("network_runtime_enabled", True, "network runtime"),
        ("external_network_enabled", True, "external network"),
        ("approval_capture_enabled", True, "approval capture"),
        ("approval_execution_enabled", True, "approval execution"),
        ("raw_data_enabled", True, "raw data"),
        ("context_injection_enabled", True, "context injection"),
        ("memory_write_enabled", True, "memory write"),
        ("file_mutation_enabled", True, "file mutation"),
        ("execution_enabled", True, "execution"),
        ("background_collection_enabled", True, "background"),
        ("sensor_access_enabled", True, "sensor"),
        ("credential_or_cookie_handling_enabled", True, "credential"),
        ("production_authority_enabled", True, "production authority"),
        ("m46_review_receipt_surfaces_future", False, "M46"),
    ],
)
def test_m45_manifest_rejects_model_copy_mutated_unsafe_flags(
    field_name: str, value: bool, match: str
) -> None:
    manifest = build_default_ccc_ios_local_read_only_connection_manifest()
    mutated = manifest.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_ccc_ios_local_read_only_connection_safe(mutated)


@pytest.mark.parametrize(
    ("api_base_ref", "match"),
    [
        ("mobile_connection_base:0.0.0.0", "loopback"),
        ("mobile_connection_base:192.168.1.7", "loopback"),
        ("mobile_connection_base:10.0.0.4", "loopback"),
        ("mobile_connection_base:https-example-com", "loopback"),
        ("mobile_connection_base:localhost-token=abc123", "secret-like"),
        ("mobile_connection_base:localhost:8080/path", "raw paths"),
    ],
)
def test_m45_manifest_rejects_unsafe_base_refs(api_base_ref: str, match: str) -> None:
    manifest = build_default_ccc_ios_local_read_only_connection_manifest()
    mutated = manifest.model_copy(update={"api_base_ref": api_base_ref})

    with pytest.raises(ValueError, match=match):
        assert_ccc_ios_local_read_only_connection_safe(mutated)


def test_m45_manifest_rejects_duplicate_or_mutating_endpoint_contracts() -> None:
    manifest = build_default_ccc_ios_local_read_only_connection_manifest()
    duplicate = manifest.endpoints[0].model_copy()
    duplicate_manifest = manifest.model_copy(update={"endpoints": [*manifest.endpoints, duplicate]})

    with pytest.raises(ValueError, match="duplicate"):
        assert_ccc_ios_local_read_only_connection_safe(duplicate_manifest)

    unsafe_endpoint = manifest.endpoints[0].model_copy(
        update={"method": "POST", "mutation_enabled": True}
    )
    unsafe_manifest = manifest.model_copy(update={"endpoints": [unsafe_endpoint, *manifest.endpoints[1:]]})

    with pytest.raises(ValueError, match="GET"):
        assert_ccc_ios_local_read_only_connection_safe(unsafe_manifest)


def test_m45_swift_source_adds_connection_status_without_runtime_networking() -> None:
    assert (SWIFT_ROOT / "LocalReadOnlyConnectionModels.swift").is_file()

    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in SWIFT_ROOT.rglob("*.swift"))
    lowered = swift_text.lower()
    assert "local read-only connection" in lowered
    assert "loopback-only" in lowered
    assert "non-authoritative" in lowered
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
    ]
    for fragment in forbidden_fragments:
        assert fragment not in swift_text


def test_m45_no_native_project_or_build_workflow_files() -> None:
    assert not (IOS_ROOT / "Package.swift").exists()
    assert not list(IOS_ROOT.glob("*.xcodeproj"))
    assert not list(IOS_ROOT.rglob("*.entitlements"))
    assert not list(IOS_ROOT.rglob("Info.plist"))
    assert not list(IOS_ROOT.rglob("ExportOptions.plist"))


def test_m45_verifier_rejects_native_runtime_workflow_files() -> None:
    assert verify_all._is_m45_allowed_ccc_ios_local_connection_file("apps/ccc-ios/README.md")
    assert verify_all._is_m45_allowed_ccc_ios_local_connection_file(
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/LocalReadOnlyConnectionModels.swift"
    )
    assert not verify_all._is_m45_allowed_ccc_ios_local_connection_file("apps/ccc-ios/Package.swift")
    assert not verify_all._is_m45_allowed_ccc_ios_local_connection_file("apps/ccc-ios/App.xcodeproj/project.pbxproj")
    assert not verify_all._is_m45_allowed_ccc_ios_local_connection_file("apps/ccc-ios/Info.plist")
