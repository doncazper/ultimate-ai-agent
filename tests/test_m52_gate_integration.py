from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m52_openapi_route_failures


def test_m52_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m52_openwebui_safe_conversation_surface" in criteria
    assert "m52_openwebui_safe_conversation_static_safety" in criteria
    assert "m52_openwebui_safe_conversation_route_boundary" in criteria
    assert "m52_roadmap_currentness" in criteria


def test_m52_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m52_openwebui_safe_conversation_surface",
        "m52_openwebui_safe_conversation_static_safety",
        "m52_openwebui_safe_conversation_route_boundary",
        "m52_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m52_route_guard_rejects_openwebui_conversation_runtime_routes() -> None:
    failures = m52_openapi_route_failures(
        {
            "/openwebui/conversation": {},
            "/openwebui/conversation/send": {},
            "/openwebui/conversation/raw": {},
            "/openwebui/runtime/call": {},
            "/openwebui/provider/call": {},
            "/openwebui/model/call": {},
            "/openwebui/tools/execute": {},
            "/openwebui/memory/write": {},
            "/openwebui/context/inject": {},
        }
    )

    assert any("/openwebui/conversation" in failure for failure in failures)
    assert any("/openwebui/conversation/send" in failure for failure in failures)
    assert any("/openwebui/conversation/raw" in failure for failure in failures)
    assert any("/openwebui/runtime/call" in failure for failure in failures)
    assert any("/openwebui/provider/call" in failure for failure in failures)
    assert any("/openwebui/model/call" in failure for failure in failures)
    assert any("/openwebui/tools/execute" in failure for failure in failures)
    assert any("/openwebui/memory/write" in failure for failure in failures)
    assert any("/openwebui/context/inject" in failure for failure in failures)
    assert not m52_openapi_route_failures(app.openapi().get("paths", {}))
