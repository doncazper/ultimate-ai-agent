from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m49_openapi_route_failures


def test_m49_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m49_mobile_review_approval_capture" in criteria
    assert "m49_mobile_approval_static_safety" in criteria
    assert "m49_mobile_route_boundary" in criteria
    assert "m49_roadmap_currentness" in criteria


def test_m49_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m49_mobile_review_approval_capture",
        "m49_mobile_approval_static_safety",
        "m49_mobile_route_boundary",
        "m49_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m49_route_guard_rejects_mobile_approval_mutation_and_execution_routes() -> None:
    failures = m49_openapi_route_failures(
        {
            "/mobile/review/approve": {},
            "/mobile/review/approvals/capture": {},
            "/mobile/review/approvals/execute": {},
            "/mobile/context/inject": {},
            "/mobile/memory/write": {},
            "/mobile/tools/execute": {},
        }
    )

    assert any("/mobile/review/approve" in failure for failure in failures)
    assert any("/mobile/review/approvals/capture" in failure for failure in failures)
    assert any("/mobile/review/approvals/execute" in failure for failure in failures)
    assert any("/mobile/context/inject" in failure for failure in failures)
    assert any("/mobile/memory/write" in failure for failure in failures)
    assert any("/mobile/tools/execute" in failure for failure in failures)
    assert not m49_openapi_route_failures(app.openapi().get("paths", {}))
