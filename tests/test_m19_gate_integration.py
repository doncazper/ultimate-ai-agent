from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M19_OPENAPI_PATH_COUNT,
    M19_FORBIDDEN_BACKEND_ROUTES,
    m19_openapi_route_failures,
)


def test_m19_mobile_companion_contract_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m19_mobile_companion_contract_planning_safe" in criteria_by_id
    criterion = criteria_by_id["m19_mobile_companion_contract_planning_safe"]
    assert "contract/API planning only" in criterion.pass_condition
    assert "no mobile app" in criterion.pass_condition
    assert "contacts/calendar" in criterion.pass_condition
    assert "metadata refs" in criterion.pass_condition
    assert "external sends" in criterion.pass_condition
    assert "OS permission integration" in criterion.pass_condition
    assert "background services" in criterion.pass_condition
    assert "OpenAPI path count at 78" in criterion.pass_condition
    assert "M20 planned" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m19_openapi_route_guard_rejects_mobile_runtime_expansion():
    failures = m19_openapi_route_failures(
        {
            "/health",
            "/mobile/sensors",
            "/mobile/register",
            "/mobile/capture",
            "/mobile/approvals/execute",
            "/device-capabilities/execute",
        },
        expected_path_count=EXPECTED_M19_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M19_OPENAPI_PATH_COUNT == 78
    assert "/mobile/register" in M19_FORBIDDEN_BACKEND_ROUTES
    assert "/mobile/sensors" in M19_FORBIDDEN_BACKEND_ROUTES
    assert "/mobile/approvals/execute" in M19_FORBIDDEN_BACKEND_ROUTES
    assert "/device-capabilities/execute" in M19_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/mobile/register" in failure for failure in failures)
    assert any("/mobile/sensors" in failure for failure in failures)
    assert any("/mobile/approvals/execute" in failure for failure in failures)
    assert any("/device-capabilities/execute" in failure for failure in failures)
