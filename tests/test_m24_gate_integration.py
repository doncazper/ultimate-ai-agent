from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m24_openapi_route_failures


def test_m24_foundation_gate_criterion_exists_and_passes():
    criteria_by_id = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m24_memory_provider_local_store_safe" in criteria_by_id
    criterion = criteria_by_id["m24_memory_provider_local_store_safe"]
    assert "MemoryProvider" in criterion.pass_condition
    assert "recall, not authority" in criterion.pass_condition
    assert "no automatic writes" in criterion.pass_condition
    assert "OpenAPI path count at 74" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert str(report.overall_status) == "passed"


def test_m24_openapi_route_guard_keeps_memory_mutation_routes_absent():
    failures = m24_openapi_route_failures(
        {
            "/api/manifest",
            "/memory/write",
            "/memory/vector-search",
            "/memory/inject",
        },
        expected_path_count=4,
    )

    assert failures
    assert "forbidden" in failures[0].lower()

    assert m24_openapi_route_failures(app.openapi().get("paths", {})) == []
