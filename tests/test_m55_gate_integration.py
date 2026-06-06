from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m55_openapi_route_failures


def test_m55_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m55_redacted_observability_export" in criteria
    assert "m55_observability_export_static_safety" in criteria
    assert "m55_observability_export_route_boundary" in criteria
    assert "m55_roadmap_currentness" in criteria


def test_m55_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m55_redacted_observability_export",
        "m55_observability_export_static_safety",
        "m55_observability_export_route_boundary",
        "m55_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m55_route_guard_rejects_raw_observability_saas_network_and_authority_routes() -> None:
    failures = m55_openapi_route_failures(
        {
            "/observability/export": {},
            "/observability/export/raw": {},
            "/observability/export/prompts": {},
            "/observability/export/provider-payloads": {},
            "/observability/export/secrets": {},
            "/observability/export/saas": {},
            "/observability/export/network": {},
            "/otel/export": {},
            "/analytics/export": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        }
    )

    assert any("/observability/export" in failure for failure in failures)
    assert any("/observability/export/raw" in failure for failure in failures)
    assert any("/observability/export/prompts" in failure for failure in failures)
    assert any("/otel/export" in failure for failure in failures)
    assert any("/analytics/export" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert not m55_openapi_route_failures(app.openapi().get("paths", {}))
