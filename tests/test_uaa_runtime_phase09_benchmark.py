from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path

import pytest

from scripts import run_uaa_runtime_phase09_benchmark as runner
from scripts import verify_uaa_runtime_phase09_benchmark as verifier


ROOT = Path(__file__).resolve().parents[1]
RESULTS = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase09_scenario_results.json"
)


def _data() -> dict[str, object]:
    return json.loads(RESULTS.read_text(encoding="utf-8"))


def test_phase09_scenario_result_contract_verifies() -> None:
    data = verifier.verify(RESULTS)

    assert data["scenario_count"] == 12
    assert [row["scenario_id"] for row in data["scenarios"]] == [
        spec.scenario_id for spec in runner.SCENARIOS
    ]
    assert data["scenarios"][7]["status"] == "blocked"
    assert data["scenarios"][7]["blocker_code"] == "SANDBOX_FACILITY_NOT_PROVEN"
    assert data["registry_fingerprint"] == runner.scenario_registry_fingerprint()
    assert [row["execution_fingerprint"] for row in data["scenarios"]] == [
        runner.scenario_execution_fingerprint(spec) for spec in runner.SCENARIOS
    ]


def test_phase09_scenario_contract_rejects_authority_and_proof_drift() -> None:
    data = _data()
    data["scenarios"][0]["status"] = "authorized"
    with pytest.raises(verifier.VerificationError, match="identity"):
        verifier.verify_data(data)

    data = _data()
    data["scenarios"][0]["evidence_refs"] = []
    with pytest.raises(verifier.VerificationError, match="non-empty"):
        verifier.verify_data(data)

    data = _data()
    data["scenarios"][0]["evidence_refs"] = ["repo-ref:uaa:README.md"]
    data["scenarios"][0]["test_verifier_refs"] = ["repo-ref:uaa:README.md"]
    with pytest.raises(verifier.VerificationError, match="binding drift"):
        verifier.verify_data(data)

    data = _data()
    data["registry_fingerprint"] = "sha256:" + "0" * 64
    with pytest.raises(verifier.VerificationError, match="registry fingerprint"):
        verifier.verify_data(data)


def test_phase09_scenario_contract_rejects_raw_or_local_data() -> None:
    data = _data()
    data["scenarios"][0]["raw_prompt"] = "not allowed"
    with pytest.raises(verifier.VerificationError, match="unsafe durable field"):
        verifier.verify_data(data)

    data = _data()
    data["scenarios"][0]["evidence_refs"][0] = "repo-ref:uaa:/private/example"
    with pytest.raises(verifier.VerificationError, match="absolute local path"):
        verifier.verify_data(data)


def test_runner_contract_is_finite_and_sandbox_is_truthfully_blocked() -> None:
    assert len(runner.SCENARIOS) == 12
    assert len({spec.scenario_id for spec in runner.SCENARIOS}) == 12
    sandbox = runner.SCENARIOS[7]
    assert sandbox.expected_status == "blocked"
    assert sandbox.blocker_code == "SANDBOX_FACILITY_NOT_PROVEN"
    assert all(spec.expected_status in {"passed", "blocked"} for spec in runner.SCENARIOS)


def test_failed_result_cannot_replace_canonical_evidence() -> None:
    before = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
    failed = _data()
    failed["status"] = "failed"

    with pytest.raises(
        ValueError,
        match="FAILED_RESULTS_MUST_NOT_REPLACE_ACCEPTED_EVIDENCE",
    ):
        runner._write_result(RESULTS, failed)

    assert hashlib.sha256(RESULTS.read_bytes()).hexdigest() == before


def test_runner_rejects_noncanonical_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="CANONICAL_OUTPUT_ONLY"):
        runner._write_result(tmp_path / "result.json", _data())


def test_phase09_verifier_rejects_symlink_and_fifo(tmp_path: Path) -> None:
    symlink = tmp_path / "results-link.json"
    symlink.symlink_to(RESULTS)
    with pytest.raises(verifier.VerificationError, match="non-symlink"):
        verifier.verify(symlink)

    fifo = tmp_path / "results-fifo.json"
    os.mkfifo(fifo)
    with pytest.raises(verifier.VerificationError, match="regular"):
        verifier.verify(fifo)


def test_phase09_verifier_rejects_symlink_parent(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    copied_result = real_parent / "result.json"
    copied_result.write_bytes(RESULTS.read_bytes())
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(verifier.VerificationError, match="parent"):
        verifier.verify(linked_parent / "result.json")
