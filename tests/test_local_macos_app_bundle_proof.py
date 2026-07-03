import json
import plistlib
import subprocess
import sys

from scripts.build_local_macos_app_bundle_proof import (
    APP_NAME,
    EXECUTABLE_NAME,
    FORBIDDEN_LAUNCHER_FRAGMENTS,
    build_local_macos_app_bundle_proof,
    validate_summary,
)


def test_local_macos_app_bundle_proof_is_safe_and_unsigned(tmp_path) -> None:
    summary = build_local_macos_app_bundle_proof(tmp_path)

    assert validate_summary(summary) == []
    assert summary["launch_executed"] is False
    assert summary["signed"] is False
    assert summary["notarized"] is False
    assert summary["distribution_claims_allowed"] is False
    assert summary["public_installer_created"] is False
    assert summary["daemon_or_launchagent_created"] is False
    assert summary["auto_update_enabled"] is False
    assert summary["raw_path_included"] is False
    assert summary["credential_material_included"] is False

    bundle_root = tmp_path / f"{APP_NAME}.app"
    executable = bundle_root / "Contents" / "MacOS" / EXECUTABLE_NAME
    info_plist = bundle_root / "Contents" / "Info.plist"
    boundary_readme = bundle_root / "Contents" / "Resources" / "README.txt"

    assert bundle_root.exists()
    assert executable.exists()
    assert info_plist.exists()
    assert boundary_readme.exists()

    launcher = executable.read_text(encoding="utf-8")
    assert "./scripts/dev/uaa trial-boot" in launcher
    for fragment in FORBIDDEN_LAUNCHER_FRAGMENTS:
        assert fragment.lower() not in launcher.lower()

    with info_plist.open("rb") as handle:
        plist = plistlib.load(handle)
    assert plist["CFBundlePackageType"] == "APPL"
    assert plist["UAADistributionClaimsAllowed"] is False
    assert "not signed" in plist["UAAAuthorityBoundary"]
    assert "not notarized" in plist["UAAAuthorityBoundary"]
    assert "not public" in plist["UAAAuthorityBoundary"]


def test_local_macos_app_bundle_cli_outputs_safe_refs_only(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_local_macos_app_bundle_proof.py",
            "--output-root",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    output = result.stdout.strip()
    summary = json.loads(output)
    assert validate_summary(summary) == []
    assert str(tmp_path) not in output
    assert "/Users/" not in output
    assert "password" not in output.lower()
    assert "cookie" not in output.lower()
    assert "private_key" not in output.lower()
