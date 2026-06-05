from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m47_openapi_route_failures


def test_m47_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m47_internal_testflight_pipeline_contract" in criteria
    assert "m47_testflight_static_safety" in criteria
    assert "m47_mobile_route_boundary" in criteria
    assert "m47_roadmap_currentness" in criteria


def test_m47_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m47_internal_testflight_pipeline_contract",
        "m47_testflight_static_safety",
        "m47_mobile_route_boundary",
        "m47_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m47_route_guard_rejects_mobile_testflight_runtime_routes() -> None:
    failures = m47_openapi_route_failures(
        {
            "/mobile/ios/testflight": {},
            "/mobile/ios/testflight/upload": {},
            "/mobile/ios/signing/assets": {},
        }
    )

    assert any("/mobile/ios/testflight" in failure for failure in failures)
    assert any("/mobile/ios/signing/assets" in failure for failure in failures)
    assert not m47_openapi_route_failures(app.openapi().get("paths", {}))
