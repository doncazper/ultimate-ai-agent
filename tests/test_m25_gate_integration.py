from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M25_OPENAPI_PATH_COUNT,
    FoundationGateEvaluator,
    m25_openapi_route_failures,
)
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus


def test_m25_foundation_gate_criteria_are_registered():
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m25_truth_source_router_contracts_valid" in criterion_ids
    assert "m25_truth_openapi_routes_unchanged" in criterion_ids
    assert "v0292_local_dev_api_authority_and_preview_safe" in criterion_ids
    assert "m25_m26_remains_future" in criterion_ids

    truth_criterion = next(
        criterion for criterion in criteria if criterion.criterion_id == "m25_truth_source_router_contracts_valid"
    )
    assert "arbitrary" in truth_criterion.pass_condition
    assert "unknown" in truth_criterion.pass_condition
    assert "self-verifying" in truth_criterion.pass_condition

    v0292_criterion = next(
        criterion for criterion in criteria if criterion.criterion_id == "v0292_local_dev_api_authority_and_preview_safe"
    )
    assert "dry-run-only" in v0292_criterion.pass_condition
    assert "metadata-only file read previews" in v0292_criterion.pass_condition
    assert "raw exception-message echo" in v0292_criterion.pass_condition


def test_m25_openapi_route_guard_rejects_truth_execution_routes():
    failures = m25_openapi_route_failures(
        {
            "/truth/verify": {},
            "/claims/verify": {},
            "/evidence/verify": {},
            "/truth/web-search": {},
        }
    )

    assert any("/truth/verify" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M25_OPENAPI_PATH_COUNT == 74
    assert m25_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m25_foundation_gate_evaluator_passes_current_contracts():
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m25_") or criterion.criterion_id.startswith("v0292_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
