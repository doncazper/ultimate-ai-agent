from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m32_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m32_filesystem_metadata_tool_safe" in criterion_ids
    assert "m32_filesystem_metadata_openapi_routes_unchanged" in criterion_ids
    assert "m32_m33_remains_future" in criterion_ids


def test_m32_openapi_route_guard_rejects_content_and_execution_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M32_OPENAPI_PATH_COUNT, m32_openapi_route_failures

    failures = m32_openapi_route_failures(
        {
            "/files/read/raw": {},
            "/files/write": {},
            "/filesystem/delete": {},
            "/tool-runtime/execute": {},
        }
    )

    assert any("/files/read/raw" in failure for failure in failures)
    assert any("/files/write" in failure for failure in failures)
    assert any("/tool-runtime/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M32_OPENAPI_PATH_COUNT == 78
    assert m32_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m32_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m32_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
