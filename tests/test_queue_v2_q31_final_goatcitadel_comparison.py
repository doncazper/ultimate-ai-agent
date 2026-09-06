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
    data["comparison_ref"] = "queue-v2-q99-substituted-comparison"
    with pytest.raises(verifier.VerificationError, match="comparison ref drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["baselines"]["uaa"]["commit_ref"] = "git-sha:" + ("0" * 40)
    with pytest.raises(verifier.VerificationError, match="UAA baseline drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["expected_scores"]["systems"]["uaa"]["weighted_total_reported"] = 99
    with pytest.raises(
        verifier.VerificationError, match="reported weighted total drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    component = data["systems"]["uaa"]["authority"]
    component["validation_posture"] = "accepted"
    component["gates"]["independent_validation"] = 1
    component["acceptance_evidence_refs"] = ["acceptance-ref:substituted"]
    with pytest.raises(
        verifier.VerificationError, match="independent validation not available"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["method"]["independent_validation"] = "performed"
    with pytest.raises(
        verifier.VerificationError, match="independent validation posture drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["method"]["prior_score_policy"] = "carried_forward"
    with pytest.raises(verifier.VerificationError, match="prior score policy drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["method"]["winner_threshold_points"] = -1
    with pytest.raises(verifier.VerificationError, match="winner threshold drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["method"]["extra_policy"] = "unreviewed"
    with pytest.raises(verifier.VerificationError, match="method inventory drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["systems"]["uaa"]["reasoning"]["prior_verified_score"] = 10
    with pytest.raises(verifier.VerificationError, match="component shape drift"):
        verifier.verify_data(data, _report())


def test_q31_packet_binds_revision_refs_and_scorer() -> None:
    data = copy.deepcopy(_data())
    data["systems"]["uaa"]["authority"]["evidence_refs"][0] = (
        "repo-ref:uaa@deadbeef:src/ultimate_ai_agent/core/authority/contracts.py"
    )
    with pytest.raises(
        verifier.VerificationError, match="repository evidence baseline drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["systems"]["uaa"]["authority"]["evidence_refs"][0] = (
        "repo-ref:goat@41d0f2e5:packages/policy-engine/src/engine.ts"
    )
    with pytest.raises(
        verifier.VerificationError, match="repository evidence owner drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["systems"]["uaa"]["authority"]["evidence_refs"][0] = (
        "repo-ref:uaa@817d84d8:docs/benchmarks/"
        "Q31_FINAL_GOATCITADEL_COMPARISON_20260906.md"
    )
    with pytest.raises(
        verifier.VerificationError, match="missing UAA evidence file at baseline"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["common_evidence_refs"]["goat_policy_tests"] = (
        "test-run-ref:q31:goat-policy:266-passed-9-failed@deadbeef"
    )
    with pytest.raises(verifier.VerificationError, match="evidence ref baseline drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["expected_scores"]["scorer_ref"] = "repository-scorer-ref:substituted"
    with pytest.raises(verifier.VerificationError, match="scorer ref drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["systems"]["uaa"]["authority"]["evidence_refs"][0] = (
        "evidence-ref:q31:any-unrevisioned-claim"
    )
    with pytest.raises(verifier.VerificationError, match="lacks provenance"):
        verifier.verify_data(data, _report())


def test_q31_packet_rejects_unsafe_or_unowned_evidence() -> None:
    data = copy.deepcopy(_data())
    data["direct_observations"][0]["result"] = "/private/tmp/raw-observation"
    with pytest.raises(verifier.VerificationError, match="unsafe durable text"):
        verifier.verify_data(data, _report())

    for field_name in (
        "prompt_text",
        "raw_prompt_text",
        "raw_provider_payload",
        "username",
        "hostname",
    ):
        data = copy.deepcopy(_data())
        data[field_name] = "private-value"
        with pytest.raises(verifier.VerificationError, match="unsafe durable field"):
            verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["direct_observations"][0]["result"] = "/home/alice/result"
    with pytest.raises(verifier.VerificationError, match="unsafe durable text"):
        verifier.verify_data(data, _report())


def test_q31_packet_requires_complete_denials_and_finite_routes() -> None:
    data = copy.deepcopy(_data())
    del data["authority_granted"]["automatic_gap_fix"]
    with pytest.raises(
        verifier.VerificationError, match="authority denial inventory drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["authority_granted"]["automatic_gap_fix"] = 0
    with pytest.raises(
        verifier.VerificationError, match="comparison cannot grant authority"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["residual_gap_routes"].append(
        {
            "finding_ref": "finding-ref:q31:unbounded",
            "owner": "Q999",
            "dependency": "Q31",
            "priority": "P1",
        }
    )
    with pytest.raises(
        verifier.VerificationError, match="residual gap route inventory drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["blocked_follow_up"]["owner"] = "Q32"
    with pytest.raises(
        verifier.VerificationError, match="blocked follow-up posture drift"
    ):
        verifier.verify_data(data, _report())


def test_q31_packet_requires_exact_direct_observations() -> None:
    data = copy.deepcopy(_data())
    data["direct_observations"][1] = copy.deepcopy(data["direct_observations"][0])
    with pytest.raises(
        verifier.VerificationError, match="duplicate direct observation identity"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["direct_observations"][0]["status"] = "independently_accepted"
    with pytest.raises(
        verifier.VerificationError, match="direct observation inventory drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["direct_observations"][0]["evidence_refs"] = []
    with pytest.raises(
        verifier.VerificationError, match="evidence_refs cannot be empty"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["direct_observations"][0]["result"] = (
        "A provider executed successfully despite the blocked status."
    )
    with pytest.raises(
        verifier.VerificationError, match="direct observation evidence binding drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["direct_observations"][0]["evidence_refs"] = [
        "runtime-observation-ref:q31:uaa:invented"
        "@git-sha:817d84d8f0e4660de5dfcff9cb215e5330d8714c"
    ]
    with pytest.raises(
        verifier.VerificationError, match="direct observation evidence binding drift"
    ):
        verifier.verify_data(data, _report())


def test_q31_packet_requires_exact_finite_reciprocal_learning() -> None:
    data = copy.deepcopy(_data())
    data["reciprocal_learning"].append(copy.deepcopy(data["reciprocal_learning"][0]))
    with pytest.raises(
        verifier.VerificationError, match="reciprocal learning ledger incomplete"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    del data["reciprocal_learning"][0]["exit_test"]
    with pytest.raises(
        verifier.VerificationError, match="reciprocal learning entry shape drift"
    ):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["reciprocal_learning"][0]["transfer_score"] = 11
    with pytest.raises(verifier.VerificationError, match="learning score drift"):
        verifier.verify_data(data, _report())

    data = copy.deepcopy(_data())
    data["reciprocal_learning"][0]["pattern"] = "substituted pattern"
    with pytest.raises(
        verifier.VerificationError, match="reciprocal learning inventory drift"
    ):
        verifier.verify_data(data, _report())


def test_q31_packet_binds_human_report_claims_and_documentation_index() -> None:
    report = _report().replace(
        "The evidence-gated repository maturity score is **GoatCitadel 73, UAA 70**.",
        "The evidence-gated repository maturity score is **GoatCitadel 70, UAA 73**.",
    )
    with pytest.raises(
        verifier.VerificationError, match="report executive score drift"
    ):
        verifier.verify_data(_data(), report)

    report = _report().replace(
        "git-sha:817d84d8f0e4660de5dfcff9cb215e5330d8714c",
        "git-sha:" + ("0" * 40),
    )
    with pytest.raises(verifier.VerificationError, match="report projection drift"):
        verifier.verify_data(_data(), report)

    report = _report().replace(
        "No Q31 finding authorizes its own repair.",
        "A Q31 finding authorizes its own repair.",
    )
    with pytest.raises(
        verifier.VerificationError, match="report authority posture drift"
    ):
        verifier.verify_data(_data(), report)

    report = _report().replace(
        "| Reasoning (8) | 6 · Usable · partial · Medium |",
        "| Reasoning (8) | 10 · Exceptional · implemented · High |",
    )
    with pytest.raises(
        verifier.VerificationError, match="canonical report digest drift"
    ):
        verifier.verify_data(_data(), report)

    report = _report() + "\nQ31 grants provider and model authority.\n"
    with pytest.raises(
        verifier.VerificationError, match="canonical report digest drift"
    ):
        verifier.verify_data(_data(), report)

    index = (ROOT / "docs" / "DOCUMENTATION_INDEX.md").read_text(encoding="utf-8")
    docs_readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    board = (ROOT / "docs" / "kanban" / "current_board.md").read_text(encoding="utf-8")
    registry = json.loads(
        (ROOT / "docs" / "roadmap" / "UAA_PRODUCT_VISION_REGISTRY.json").read_text(
            encoding="utf-8"
        )
    )
    for required_path in (
        "docs/benchmarks/Q31_FINAL_GOATCITADEL_COMPARISON_20260906.md",
        "docs/benchmarks/q31_goat_maturity_input_20260906.json",
        "scripts/verify_queue_v2_q31_final_goatcitadel_comparison.py",
    ):
        assert required_path in index
        assert required_path in docs_readme
    assert verifier.QUEUE_TRUTH_SENTENCE in _report()
    assert "Q31 final GoatCitadel comparison candidate" in index
    assert "Q32 remains blocked until that receipt exists" in docs_readme
    assert (
        "Q32 CRM functional adoption — blocked until both Q15 and Q31 are completed"
        in board
    )
    q31 = next(item for item in registry["items"] if item["item_id"] == "Q31")
    assert q31["whole_vision"]["status"] == "planned"
    assert q31["whole_vision"]["completion_evidence_refs"] == []


def test_q31_verifier_cli_is_content_free_and_successful() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(
                ROOT / "scripts" / "verify_queue_v2_q31_final_goatcitadel_comparison.py"
            ),
        ],
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
