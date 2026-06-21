from typing import Any
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m46_openapi_route_failures,
)


def _gate_result(criteria_id: str) -> Any:
    criteria_by_id = {
        criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()
    }
    report = FoundationGateEvaluator().evaluate([criteria_by_id[criteria_id]])
    return report.results[0]


def test_m46_foundation_gate_review_receipt_surfaces_pass() -> None:
    result = _gate_result("m46_ccc_ios_review_receipt_read_only_surfaces")

    assert result.status == "passed", result.failures


def test_m46_foundation_gate_static_safety_passes() -> None:
    result = _gate_result("m46_ios_review_receipt_static_safety")

    assert result.status == "passed", result.failures


def test_m46_foundation_gate_route_boundary_passes() -> None:
    result = _gate_result("m46_mobile_route_boundary")

    assert result.status == "passed", result.failures


def test_m46_foundation_gate_roadmap_currentness_passes() -> None:
    result = _gate_result("m46_roadmap_currentness")

    assert result.status == "passed", result.failures


def test_m46_openapi_route_guard_rejects_forbidden_mobile_review_receipt_routes() -> None:
    paths = {
        "/api/manifest",
        "/mobile/ios/review-receipts",
    }

    failures = m46_openapi_route_failures(paths, expected_path_count=2)

    assert any("/mobile/ios/review-receipts" in failure for failure in failures)
