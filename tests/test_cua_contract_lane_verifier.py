from __future__ import annotations

import sys
from pathlib import Path

from scripts import verify_cua_contract_lane
from scripts.verification.repo import load_json


def test_cua_release_manifest_marks_lane_blocked_or_experimental() -> None:
    manifest = load_json("docs/cua/cua_release_surface_manifest.json")

    assert manifest["status"] in {"blocked", "experimental"}
    assert manifest["implementation_status"] == "contracts_verifiers_docs_only"
    assert manifest["driver_presence"] == "absent"
    assert manifest["proofs"]["no_runtime_driver"] is True
    assert manifest["proofs"]["no_click_type_route"] is True
    assert manifest["proofs"]["no_screenshot_capture"] is True
    assert manifest["proofs"]["no_os_accessibility_access"] is True


def test_cua_verifier_passes_current_contract_lane() -> None:
    assert str(verify_cua_contract_lane.ROOT / "src") in sys.path
    assert verify_cua_contract_lane.verify() == []


def test_cua_verifier_catches_fake_runtime_driver_addition(tmp_path: Path) -> None:
    fake = tmp_path / "fake_cua_runtime.py"
    fake.write_text("computer_use(action='click')\n", encoding="utf-8")

    failures = verify_cua_contract_lane.verify(extra_scan_paths=[fake])

    assert any("computer-use action invocation" in failure for failure in failures)


def test_cua_verifier_catches_fake_shipped_claim(tmp_path: Path) -> None:
    fake = tmp_path / "fake_release_claim.md"
    fake.write_text("CUA is shipped for real computer control.\n", encoding="utf-8")

    failures = verify_cua_contract_lane.verify(extra_scan_paths=[fake])

    assert any("CUA shipped claim" in failure for failure in failures)
