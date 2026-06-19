from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m31_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m31_tool_runtime_noop_contract_safe" in criterion_ids
    assert "m31_tool_runtime_openapi_routes_unchanged" in criterion_ids
    assert "m31_m32_remains_future" in criterion_ids


def test_m31_openapi_route_guard_rejects_tool_runtime_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M31_OPENAPI_PATH_COUNT, m31_openapi_route_failures

    failures = m31_openapi_route_failures(
        {
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/tool-broker/execute": {},
            "/plugins/enable": {},
        }
    )

    assert any("/tools/execute" in failure for failure in failures)
    assert any("/tool-runtime/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M31_OPENAPI_PATH_COUNT == 76
    assert m31_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m31_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m31_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
