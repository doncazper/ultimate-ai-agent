from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M18_OPENAPI_PATH_COUNT,
    M18_FORBIDDEN_BACKEND_ROUTES,
    m18_openapi_route_failures,
)


def test_m18_local_runtime_manual_smoke_surface_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m18_local_runtime_manual_smoke_surface_safe" in criteria_by_id
    criterion = criteria_by_id["m18_local_runtime_manual_smoke_surface_safe"]
    assert "read-only local runtime status" in criterion.pass_condition
    assert "manual smoke report validation-only" in criterion.pass_condition
    assert "OpenAPI path count at 78" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m18_openapi_route_guard_rejects_runtime_execution_expansion() -> None:
    failures = m18_openapi_route_failures(
        {
            "/health",
            "/runtime/readiness",
            "/runtime/capability-matrix",
            "/runtime/smoke-reports/validate",
            "/runtime/smoke-reports/execute",
            "/runtime/local/execute",
        },
        expected_path_count=EXPECTED_M18_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M18_OPENAPI_PATH_COUNT == 79
    assert "/runtime/smoke-reports/execute" in M18_FORBIDDEN_BACKEND_ROUTES
    assert "/runtime/local/execute" in M18_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/runtime/smoke-reports/execute" in failure for failure in failures)
    assert any("/runtime/local/execute" in failure for failure in failures)
