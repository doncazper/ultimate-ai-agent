from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m34_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m34_broader_file_capability_review_docs_present" in criterion_ids
    assert "m34_file_capability_openapi_routes_unchanged" in criterion_ids
    assert "m34_m35_m36_remain_future" in criterion_ids


def test_m34_openapi_route_guard_rejects_file_review_and_execution_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M34_OPENAPI_PATH_COUNT, m34_openapi_route_failures

    failures = m34_openapi_route_failures(
        {
            "/files/read/raw": {},
            "/files/review/approve": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tool-runtime/execute": {},
        }
    )

    assert any("/files/read/raw" in failure for failure in failures)
    assert any("/files/review/approve" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/tool-runtime/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M34_OPENAPI_PATH_COUNT == 74
    assert m34_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m34_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m34_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
