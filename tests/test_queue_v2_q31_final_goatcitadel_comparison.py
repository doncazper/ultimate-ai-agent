from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import verify_queue_v2_q31_final_goatcitadel_comparison as verifier


ROOT = Path(__file__).resolve().parents[1]


def _data() -> dict[str, object]:
    return json.loads(verifier.DEFAULT_ARTIFACT.read_text(encoding="utf-8"))


def _report() -> str:
    return verifier.DEFAULT_REPORT.read_text(encoding="utf-8")


def test_q31_packet_verifies_exact_scores_and_non_empirical_posture() -> None:
    data = verifier.verify()

    scores = data["expected_scores"]["systems"]
    assert scores["uaa"]["weighted_total_raw"] == 69.8387
    assert scores["uaa"]["weighted_total_reported"] == 70
    assert scores["goatcitadel"]["weighted_total_raw"] == 73.4677
    assert scores["goatcitadel"]["weighted_total_reported"] == 73
    assert data["method"]["controlled_model_task_trials"] == "not_measured"
    assert data["method"]["product_experience"] == "single_evaluator_formative_only"
    assert data["systems"]["goatcitadel"]["action"]["status"] == "partial"
    assert data["systems"]["goatcitadel"]["action"]["contradiction_refs"]


def test_q31_packet_rejects_baseline_score_and_acceptance_drift() -> None:
    data = copy.deepcopy(_data())
    data["baselines"]["uaa"]["commit_ref"] = "git-sha:" + ("0" * 40)
    with pytest.raises(verifier.VerificationError, match="UAA baseline drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["expected_scores"]["systems"]["uaa"]["weighted_total_reported"] = 99
    with pytest.raises(verifier.VerificationError, match="reported weighted total drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    component = data["systems"]["uaa"]["authority"]
    component["validation_posture"] = "accepted"
    component["gates"]["independent_validation"] = 1
    component["acceptance_evidence_refs"] = ["acceptance-ref:substituted"]
    with pytest.raises(verifier.VerificationError, match="independent validation not available"):
        verifier.verify_data(data, _report())


def test_q31_packet_rejects_unsafe_or_unowned_evidence() -> None:
    data = copy.deepcopy(_data())
    data["direct_observations"][0]["result"] = "/private/tmp/raw-observation"
    with pytest.raises(verifier.VerificationError, match="unsafe durable text"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["residual_gap_routes"] = [
        item for item in data["residual_gap_routes"] if item["owner"] != "Q33"
    ]
    with pytest.raises(verifier.VerificationError, match="required queue owner routing"):
        verifier.verify_data(data, _report())


def test_q31_verifier_cli_is_content_free_and_successful() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts" / "verify_queue_v2_q31_final_goatcitadel_comparison.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result == {
        "authority_granted": False,
        "comparison_ref": "queue-v2-q31-final-goatcitadel-comparison-20260906",
        "controlled_task_performance": "not_measured",
        "goatcitadel": 73,
        "status": "verified",
        "uaa": 70,
    }
