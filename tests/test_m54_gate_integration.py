from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m54_openapi_route_failures


def test_m54_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m54_safe_media_metadata_inspector" in criteria
    assert "m54_safe_media_metadata_static_safety" in criteria
    assert "m54_safe_media_metadata_route_boundary" in criteria
    assert "m54_roadmap_currentness" in criteria


def test_m54_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m54_safe_media_metadata_inspector",
        "m54_safe_media_metadata_static_safety",
        "m54_safe_media_metadata_route_boundary",
        "m54_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m54_route_guard_rejects_raw_media_transform_model_and_export_routes() -> None:
    failures = m54_openapi_route_failures(
        {
            "/media/read/raw": {},
            "/media/export": {},
            "/media/full-read": {},
            "/media/transform/ocio": {},
            "/media/gamut/expand": {},
            "/models/call": {},
            "/provider/call": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        }
    )

    assert any("/media/read/raw" in failure for failure in failures)
    assert any("/media/export" in failure for failure in failures)
    assert any("/media/transform/ocio" in failure for failure in failures)
    assert any("/media/gamut/expand" in failure for failure in failures)
    assert any("/models/call" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert not m54_openapi_route_failures(app.openapi().get("paths", {}))
