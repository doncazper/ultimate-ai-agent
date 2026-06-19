from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m30_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m30_execution_framework_contract_safe" in criterion_ids
    assert "m30_execution_openapi_routes_unchanged" in criterion_ids
    assert "m30_m31_remains_future" in criterion_ids

    criterion = next(item for item in criteria if item.criterion_id == "m30_execution_framework_contract_safe")
    assert "Multi-Step Execution Framework" in criterion.pass_condition
    assert "state-machine only" in criterion.pass_condition
    assert "no real task execution" in criterion.pass_condition
    assert "replay protection" in criterion.pass_condition


def test_m30_openapi_route_guard_rejects_execution_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M30_OPENAPI_PATH_COUNT, m30_openapi_route_failures

    failures = m30_openapi_route_failures(
        {
            "/execution/run": {},
            "/execution/execute": {},
            "/tasks/execute": {},
            "/actions/execute": {},
            "/tools/execute": {},
        }
    )

    assert any("/execution/run" in failure for failure in failures)
    assert any("/tasks/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M30_OPENAPI_PATH_COUNT == 75
    assert m30_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m30_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m30_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
