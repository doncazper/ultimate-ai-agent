import copy
import json
from pathlib import Path

import scripts.verify_uaa_p1_088_agent_module_maturity_review_v2 as verifier
from scripts.verify_agent_module_maturity_map import REQUIRED_MODULE_IDS


ROOT = Path(__file__).resolve().parent.parent
REVIEW_PATH = ROOT / "docs/registry/agent_module_maturity_review_v2.json"
REQUIRED_DIMENSIONS = {
    "product_usefulness",
    "safety_boundary_clarity",
    "test_depth",
    "ui_visibility",
    "cli_parity",
    "evidence_quality",
    "operator_ergonomics",
    "implementation_maturity",
}


def _payload() -> dict:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def test_uaa_p1_088_verifier_passes_current_repo() -> None:
    assert verifier.verify(ROOT) == []


def test_uaa_p1_088_review_covers_required_modules_exactly() -> None:
    payload = _payload()
    module_ids = {module["module_id"] for module in payload["modules"]}

    assert module_ids == REQUIRED_MODULE_IDS


def test_uaa_p1_088_review_uses_required_operator_dimensions() -> None:
    payload = _payload()
    dimension_ids = {dimension["id"] for dimension in payload["dimension_definitions"]}

    assert dimension_ids == REQUIRED_DIMENSIONS
    assert all(set(module["dimension_scores"]) == REQUIRED_DIMENSIONS for module in payload["modules"])


def test_uaa_p1_088_review_records_post_mem_015_021_tracked_evidence_posture() -> None:
    payload = _payload()
    context = payload["post_fcc_mem_015_021_context"]

    assert context["requested_refresh_range"] == [
        "FCC-MEM-015",
        "FCC-MEM-016",
        "FCC-MEM-017",
        "FCC-MEM-018",
        "FCC-MEM-019",
        "FCC-MEM-020",
        "FCC-MEM-021",
    ]
    assert payload["summary_metrics"]["post_fcc_mem_015_021_tracked_artifacts_present"] is False
    assert "No tracked FCC-MEM-015 through FCC-MEM-021" in context["tracked_artifact_status"]


def test_uaa_p1_088_review_identifies_weak_router_and_decomposition_modules() -> None:
    payload = _payload()
    weak_ids = set(payload["summary_metrics"]["weakest_module_ids"])
    composites = {module["module_id"]: module["composite_score"] for module in payload["modules"]}
    lowest = min(composites.values())

    assert {"decision_router", "task_decomposition_module"} <= weak_ids
    assert composites["decision_router"] == lowest
    assert composites["task_decomposition_module"] == lowest


def test_uaa_p1_088_review_flags_bad_composite_score() -> None:
    broken = copy.deepcopy(_payload())
    broken["modules"][0]["composite_score"] += 1

    failures = verifier.verify_payload(broken, ROOT)

    assert any("does not match expected" in failure for failure in failures)


def test_uaa_p1_088_review_flags_authority_expansion() -> None:
    broken = copy.deepcopy(_payload())
    broken["authority_boundary"]["runtime_model_calls_added"] = True

    failures = verifier.verify_payload(broken, ROOT)

    assert any("runtime_model_calls_added must be false" in failure for failure in failures)


def test_uaa_p1_088_review_flags_v1_maturity_score_drift() -> None:
    broken = copy.deepcopy(_payload())
    broken["modules"][0]["current_maturity_score"] = 0

    failures = verifier.verify_payload(broken, ROOT)

    assert any("current_maturity_score must match V1 maturity map score" in failure for failure in failures)


def test_uaa_p1_088_review_flags_prior_score_drift() -> None:
    broken = copy.deepcopy(_payload())
    broken["modules"][0]["prior_score"] = 0

    failures = verifier.verify_payload(broken, ROOT)

    assert any("prior_score must match V1 maturity map score" in failure for failure in failures)


def test_uaa_p1_088_review_flags_current_score_drift() -> None:
    broken = copy.deepcopy(_payload())
    broken["modules"][0]["current_score"] += 1

    failures = verifier.verify_payload(broken, ROOT)

    assert any("current_score" in failure and "does not match expected" in failure for failure in failures)


def test_uaa_p1_088_review_flags_missing_referenced_path() -> None:
    broken = copy.deepcopy(_payload())
    broken["modules"][0]["evidence_refs"] = ["src/ultimate_ai_agent/core/not_real.py"]

    failures = verifier.verify_payload(broken, ROOT)

    assert any("references missing path" in failure for failure in failures)


def test_uaa_p1_088_review_requires_ranked_queue_order() -> None:
    broken = copy.deepcopy(_payload())
    broken["ranked_improvement_queue"][0], broken["ranked_improvement_queue"][1] = (
        broken["ranked_improvement_queue"][1],
        broken["ranked_improvement_queue"][0],
    )

    failures = verifier.verify_payload(broken, ROOT)

    assert any("ranked_improvement_queue first items" in failure for failure in failures)


def test_uaa_p1_088_review_requires_queue_evidence_and_safety_subagents() -> None:
    broken = copy.deepcopy(_payload())
    broken["ranked_improvement_queue"][0]["subagent_review_plan"] = [
        "Spawn one vague reviewer."
    ]

    failures = verifier.verify_payload(broken, ROOT)

    assert any("at least two reviewers" in failure for failure in failures)
    assert any("repo-evidence reviewer" in failure for failure in failures)
    assert any("safety/product-language reviewer" in failure for failure in failures)
