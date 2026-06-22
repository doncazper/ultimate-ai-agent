from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import verify_fcc_v1_003_founder_loop_vertical_slice as verifier
from scripts.dev import uaa_founder_loop
from scripts.verification.repo import load_json


def test_founder_loop_cli_promotes_and_inspects_safe_refs(
    tmp_path: Path,
    capsys,
) -> None:
    state_dir = tmp_path / "founder_loop"
    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "promote-action-envelope",
            "--today-item-ref",
            verifier.TODAY_ITEM_REF,
            "--idempotency-ref",
            "idempotency-ref:test-fcc-v1-003-cli",
        ]
    )
    assert rc == 0
    promoted = json.loads(capsys.readouterr().out)
    assert promoted["receipt"]["action_executed"] is False
    assert promoted["receipt"]["action_envelope_ref"].startswith("action-envelope:")

    rc = uaa_founder_loop.main(["--state-dir", str(state_dir), "inspect", "--limit", "4"])
    assert rc == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["safe_refs_only"] is True
    assert inspected["raw_paths_omitted"] is True
    assert inspected["actions"][0]["receipt_refs"]
    assert "state_dir" not in inspected


def test_fcc_v1_003_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []


def test_fcc_v1_003_verifier_flags_release_surface_missing_today_route() -> None:
    release_surface = copy.deepcopy(load_json(verifier.RELEASE_SURFACE_PATH))
    today = next(route for route in release_surface["routes"] if route["path"] == "/today")
    today["backend_routes"] = [
        route
        for route in today["backend_routes"]
        if route["path"] != "/control-center/today/action-envelope"
    ]

    failures = verifier.verify(
        release_surface=release_surface,
        check_files=False,
        check_behavior=False,
    )

    assert any("/today missing route" in failure for failure in failures)


def test_fcc_v1_003_verifier_flags_milestone_overclaim() -> None:
    milestone_status = copy.deepcopy(load_json(verifier.MILESTONE_STATUS_PATH))
    milestone = next(
        item for item in milestone_status["milestones"] if item["id"] == "FCC-V1-003"
    )
    milestone["status"] = "planned"

    failures = verifier.verify(
        milestone_status=milestone_status,
        check_files=False,
        check_behavior=False,
    )

    assert any("FCC-V1-003 milestone status must be implemented" in failure for failure in failures)
