from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m53_openapi_route_failures


def test_m53_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m53_controlled_tool_expansion_review" in criteria
    assert "m53_controlled_tool_expansion_static_safety" in criteria
    assert "m53_controlled_tool_expansion_route_boundary" in criteria
    assert "m53_roadmap_currentness" in criteria


def test_m53_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m53_controlled_tool_expansion_review",
        "m53_controlled_tool_expansion_static_safety",
        "m53_controlled_tool_expansion_route_boundary",
        "m53_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m53_route_guard_rejects_tool_expansion_runtime_routes() -> None:
    failures = m53_openapi_route_failures(
        {
            "/tools/expand": {},
            "/tools/register": {},
            "/tools/enable": {},
            "/tools/run": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/network/request": {},
            "/provider/call": {},
            "/models/call": {},
            "/browser/click": {},
            "/plugins/enable": {},
            "/memory/write": {},
            "/context/inject": {},
        }
    )

    assert any("/tools/expand" in failure for failure in failures)
    assert any("/tools/register" in failure for failure in failures)
    assert any("/tools/enable" in failure for failure in failures)
    assert any("/tools/run" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert any("/shell/execute" in failure for failure in failures)
    assert any("/network/request" in failure for failure in failures)
    assert any("/provider/call" in failure for failure in failures)
    assert any("/models/call" in failure for failure in failures)
    assert any("/browser/click" in failure for failure in failures)
    assert any("/plugins/enable" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert not m53_openapi_route_failures(app.openapi().get("paths", {}))
