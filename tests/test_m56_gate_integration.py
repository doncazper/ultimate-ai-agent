from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m56_openapi_route_failures


def test_m56_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m56_agent_eval_regression_harness" in criteria
    assert "m56_eval_regression_static_safety" in criteria
    assert "m56_eval_regression_route_boundary" in criteria
    assert "m56_roadmap_currentness" in criteria


def test_m56_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m56_agent_eval_regression_harness",
        "m56_eval_regression_static_safety",
        "m56_eval_regression_route_boundary",
        "m56_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m56_route_guard_rejects_eval_execution_and_authority_routes() -> None:
    failures = m56_openapi_route_failures(
        {
            "/evals/run": {},
            "/evals/execute": {},
            "/evals/model-call": {},
            "/evals/export/raw": {},
            "/models/call": {},
            "/provider/call": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/context/inject": {},
            "/memory/write": {},
            "/shell/execute": {},
            "/browser/click": {},
        }
    )

    assert any("/evals/run" in failure for failure in failures)
    assert any("/evals/execute" in failure for failure in failures)
    assert any("/evals/model-call" in failure for failure in failures)
    assert any("/evals/export/raw" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert not m56_openapi_route_failures(app.openapi().get("paths", {}))
