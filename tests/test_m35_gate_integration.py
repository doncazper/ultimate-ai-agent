from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m35_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m35_safe_file_review_workflow_contract_safe" in criterion_ids
    assert "m35_file_review_openapi_routes_unchanged" in criterion_ids
    assert "m35_m36_m37_m38_remain_future" in criterion_ids


def test_m35_openapi_route_guard_rejects_raw_review_mutation_and_execution_routes():
    from ultimate_ai_agent.core.gate.evaluators import EXPECTED_M35_OPENAPI_PATH_COUNT, m35_openapi_route_failures

    failures = m35_openapi_route_failures(
        {
            "/files/read/raw": {},
            "/files/review/approve": {},
            "/files/review/persist": {},
            "/context/propose": {},
            "/context/inject": {},
            "/memory/write": {},
            "/files/export": {},
            "/tool-runtime/execute": {},
        }
    )

    assert any("/files/read/raw" in failure for failure in failures)
    assert any("/files/review/approve" in failure for failure in failures)
    assert any("/files/review/persist" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/files/export" in failure for failure in failures)
    assert any("/tool-runtime/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M35_OPENAPI_PATH_COUNT == 74
    assert m35_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m35_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m35_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
