from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m51_openapi_route_failures


def test_m51_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m51_openwebui_bridge_adapter_pilot" in criteria
    assert "m51_openwebui_adapter_static_safety" in criteria
    assert "m51_openwebui_adapter_route_boundary" in criteria
    assert "m51_roadmap_currentness" in criteria


def test_m51_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m51_openwebui_bridge_adapter_pilot",
        "m51_openwebui_adapter_static_safety",
        "m51_openwebui_adapter_route_boundary",
        "m51_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m51_route_guard_rejects_openwebui_runtime_and_authority_routes() -> None:
    failures = m51_openapi_route_failures(
        {
            "/openwebui/handoff": {},
            "/openwebui/runtime/call": {},
            "/openwebui/provider/call": {},
            "/openwebui/tools/execute": {},
            "/openwebui/memory/write": {},
            "/openwebui/context/inject": {},
            "/openwebui/raw-payload": {},
        }
    )

    assert any("/openwebui/handoff" in failure for failure in failures)
    assert any("/openwebui/runtime/call" in failure for failure in failures)
    assert any("/openwebui/provider/call" in failure for failure in failures)
    assert any("/openwebui/tools/execute" in failure for failure in failures)
    assert any("/openwebui/memory/write" in failure for failure in failures)
    assert any("/openwebui/context/inject" in failure for failure in failures)
    assert any("/openwebui/raw-payload" in failure for failure in failures)
    assert not m51_openapi_route_failures(app.openapi().get("paths", {}))

