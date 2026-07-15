from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from scripts import verify_msg_mx_004_local_synapse_harness as verifier
from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    default_foundation_gate_criteria,
)


def test_msg_mx_004_verifier_accepts_current_repository() -> None:
    assert verifier.verify() == []


def test_msg_mx_004_verifier_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_msg_mx_004_local_synapse_harness.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_msg_mx_004_foundation_gate_boundaries_pass() -> None:
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }
    selected = [
        criteria_by_id[criterion_id]
        for criterion_id in (
            "shell_execution_absent",
            "m12_control_center_api_read_only",
            "m13_backend_api_contract_unchanged",
            "m13_control_center_frontend_safety_verifier_passes",
            "m14_backend_api_contract_unchanged",
            "m152_local_model_management_static_safety",
            "m153_m165_local_model_management_progression",
        )
    ]

    report = FoundationGateEvaluator().evaluate(selected)

    assert report.overall_status == "passed", {
        result.criterion_id: result.failures
        for result in report.results
        if result.failures
    }


def test_msg_mx_004_verifier_rejects_missing_no_pull_marker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    backend = tmp_path / "backend.py"
    backend.write_text(
        verifier.BACKEND_PATH.read_text(encoding="utf-8").replace(
            '"--pull",\n                "never"',
            '"--pull-removed",\n                "never"',
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "BACKEND_PATH", backend)
    assert any("--pull" in failure for failure in verifier.verify())
