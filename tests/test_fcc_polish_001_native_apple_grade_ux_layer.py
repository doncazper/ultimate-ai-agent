from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_fcc_polish_001_native_apple_grade_ux_layer as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_polish_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_polish_001_native_apple_grade_ux_layer() == []


def test_polish_visual_manifest_covers_required_surfaces() -> None:
    manifest = json.loads(
        (ROOT / "docs/control_center/visual_regression_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {surface["surface"] for surface in manifest["surfaces"]}

    assert {
        "Overview",
        "Start Here",
        "Today",
        "Source Inbox",
        "Actions",
        "Plans",
        "Proof",
        "Trust",
        "Memory",
        "Evidence",
        "Settings",
        "Setup",
    }.issubset(surfaces)
    scenarios = {
        scenario["scenario"] for scenario in manifest.get("state_scenarios", [])
    }
    assert {
        "state-loading",
        "state-empty",
        "state-error",
        "state-blocked",
        "state-partial",
        "state-success",
    }.issubset(scenarios)
    assert manifest["baseline_policy"]["checked_in_redacted_baselines_required"] is True
    assert manifest["baseline_policy"]["raw_private_screenshots_allowed"] is False
    assert manifest["baseline_policy"]["absolute_paths_allowed"] is False
    assert manifest["baseline_policy"]["local_user_paths_allowed"] is False
    assert manifest["baseline_policy"]["secret_material_allowed"] is False
    for surface in manifest["surfaces"]:
        assert surface["raw_private_screenshot_included"] is False
        if "desktop_variants" in surface:
            assert set(surface["desktop_variants"]) == {"wide", "compact"}
            assert surface["desktop_variants"]["wide"]["baseline_hash"].startswith(
                "sha256:"
            )
            assert surface["desktop_variants"]["compact"][
                "baseline_hash"
            ].startswith("sha256:")
            assert "mobile" not in surface["desktop_variants"]
            continue
        assert surface["baseline_hashes"]["desktop"].startswith("sha256:")
        assert surface["baseline_hashes"]["mobile"].startswith("sha256:")


def test_setup_assistant_copy_keeps_native_authority_blocked() -> None:
    setup_panel = (
        ROOT / "apps/control-center/src/components/MacOSSetupAssistantPanel.tsx"
    ).read_text(encoding="utf-8")

    assert "Visual setup preview" in setup_panel
    assert "installer actions" in setup_panel
    assert "Blocked setup authority" in setup_panel
    assert "Dry-run approval envelopes" in setup_panel
    assert "recommendation only" in setup_panel
    assert "Receipts and rollback" in setup_panel
