from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M27_OPENAPI_PATH_COUNT,
    FoundationGateEvaluator,
    m27_openapi_route_failures,
)


def test_m27_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m27_tool_broker_v2_contract_safe" in criterion_ids
    assert "m27_tool_broker_v2_openapi_routes_unchanged" in criterion_ids
    assert "m27_m28_remains_future" in criterion_ids

    criterion = next(
        item for item in criteria if item.criterion_id == "m27_tool_broker_v2_contract_safe"
    )
    assert "Tool Broker v2" in criterion.pass_condition
    assert "preview-only" in criterion.pass_condition
    assert "no execution" in criterion.pass_condition
    assert "approval_ref is not authority" in criterion.pass_condition


def test_m27_openapi_route_guard_rejects_tool_execution_routes():
    failures = m27_openapi_route_failures(
        {
            "/tools/execute": {},
            "/tools/run": {},
            "/plugins/enable": {},
            "/browser/execute": {},
        }
    )

    assert any("/tools/execute" in failure for failure in failures)
    assert any("/plugins/enable" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M27_OPENAPI_PATH_COUNT == 78
    assert m27_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m27_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m27_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
