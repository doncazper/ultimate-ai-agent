from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M26_OPENAPI_PATH_COUNT,
    FoundationGateEvaluator,
    m26_openapi_route_failures,
)


def test_m26_foundation_gate_criteria_are_registered() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m26_grounded_recall_context_pack_safe" in criterion_ids
    assert "m26_recall_openapi_routes_unchanged" in criterion_ids
    assert "m26_m27_remains_future" in criterion_ids

    recall_criterion = next(
        criterion
        for criterion in criteria
        if criterion.criterion_id == "m26_grounded_recall_context_pack_safe"
    )
    assert "Grounded Recall Router" in recall_criterion.pass_condition
    assert "Context Pack Builder" in recall_criterion.pass_condition
    assert "source_ref/source_kind consistency" in recall_criterion.pass_condition
    assert "no vector" in recall_criterion.pass_condition
    assert "no context injection" in recall_criterion.pass_condition


def test_m26_openapi_route_guard_rejects_recall_execution_routes() -> None:
    failures = m26_openapi_route_failures(
        {
            "/recall/run": {},
            "/recall/search": {},
            "/context-pack/inject": {},
            "/memory/vector-search": {},
        }
    )

    assert any("/recall/run" in failure for failure in failures)
    assert any("/context-pack/inject" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M26_OPENAPI_PATH_COUNT == 80
    assert m26_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m26_foundation_gate_evaluator_passes_current_contracts() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m26_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
