from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m48_openapi_route_failures


def test_m48_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m48_first_internal_testflight_build_candidate" in criteria
    assert "m48_testflight_build_static_safety" in criteria
    assert "m48_mobile_route_boundary" in criteria
    assert "m48_roadmap_currentness" in criteria


def test_m48_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m48_first_internal_testflight_build_candidate",
        "m48_testflight_build_static_safety",
        "m48_mobile_route_boundary",
        "m48_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m48_route_guard_rejects_mobile_testflight_build_and_upload_routes() -> None:
    failures = m48_openapi_route_failures(
        {
            "/mobile/ios/testflight/build": {},
            "/mobile/ios/testflight/upload": {},
            "/mobile/ios/signing/assets": {},
            "/mobile/ios/app-store-connect/upload": {},
        }
    )

    assert any("/mobile/ios/testflight/build" in failure for failure in failures)
    assert any("/mobile/ios/testflight/upload" in failure for failure in failures)
    assert any("/mobile/ios/signing/assets" in failure for failure in failures)
    assert any("/mobile/ios/app-store-connect/upload" in failure for failure in failures)
    assert not m48_openapi_route_failures(app.openapi().get("paths", {}))
