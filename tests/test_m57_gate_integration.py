from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m57_openapi_route_failures


def test_m57_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m57_runtime_sandbox_architecture_review" in criteria
    assert "m57_runtime_sandbox_static_safety" in criteria
    assert "m57_runtime_sandbox_route_boundary" in criteria
    assert "m57_roadmap_currentness" in criteria


def test_m57_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m57_runtime_sandbox_architecture_review",
        "m57_runtime_sandbox_static_safety",
        "m57_runtime_sandbox_route_boundary",
        "m57_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m57_route_guard_rejects_runtime_sandbox_execution_routes() -> None:
    failures = m57_openapi_route_failures(
        {
            "/sandbox/run": {},
            "/sandbox/execute": {},
            "/sandbox/subprocess": {},
            "/process/spawn": {},
            "/shell/execute": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/context/inject": {},
            "/memory/write": {},
            "/browser/click": {},
            "/plugins/execute": {},
        }
    )

    assert any("/sandbox/run" in failure for failure in failures)
    assert any("/sandbox/execute" in failure for failure in failures)
    assert any("/process/spawn" in failure for failure in failures)
    assert any("/shell/execute" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert not m57_openapi_route_failures(app.openapi().get("paths", {}))
