from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m23_openapi_route_failures


def test_m23_foundation_gate_criterion_exists_and_passes() -> None:
    criteria_by_id = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m23_first_local_llm_call_safe" in criteria_by_id
    criterion = criteria_by_id["m23_first_local_llm_call_safe"]
    assert "manual/CLI-only" in criterion.pass_condition
    assert "fixed-prompt-only" in criterion.pass_condition
    assert "non-authoritative" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert str(report.overall_status) == "passed"


def test_m23_openapi_route_guard_rejects_execution_routes() -> None:
    failures = m23_openapi_route_failures(
        {
            "/api/manifest",
            "/runtime/local/call",
            "/model-runtime/local/generate",
            "/openwebui/bridge/run",
        },
        expected_path_count=4,
    )

    assert failures
    assert "forbidden" in failures[0].lower()
