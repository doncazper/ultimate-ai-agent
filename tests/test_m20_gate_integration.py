from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M20_OPENAPI_PATH_COUNT,
    M20_FORBIDDEN_BACKEND_ROUTES,
    m20_openapi_route_failures,
)


def test_m20_device_capability_contract_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m20_device_capability_broker_contract_safe" in criteria_by_id
    criterion = criteria_by_id["m20_device_capability_broker_contract_safe"]
    assert "contract-only" in criterion.pass_condition
    assert "no sensor access" in criterion.pass_condition
    assert "no OS permission integration" in criterion.pass_condition
    assert "no native app" in criterion.pass_condition
    assert "enabled and implemented capability flags are rejected" in criterion.pass_condition
    assert "notification runtime" in criterion.pass_condition
    assert "permission runtime claims" in criterion.pass_condition
    assert "OpenAPI path count at 78" in criterion.pass_condition
    assert "M21 planned" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m20_openapi_route_guard_rejects_device_runtime_expansion() -> None:
    failures = m20_openapi_route_failures(
        {
            "/health",
            "/device-capabilities",
            "/device-capabilities/execute",
            "/device-capabilities/camera",
            "/device-capabilities/location",
            "/mobile/sensors",
        },
        expected_path_count=EXPECTED_M20_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M20_OPENAPI_PATH_COUNT == 78
    assert "/device-capabilities" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/device-capabilities/execute" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/device-capabilities/bluetooth" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/device-capabilities/local-network" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/device-capabilities/screen-capture" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/mobile/permissions" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/mobile/background-service" in M20_FORBIDDEN_BACKEND_ROUTES
    assert "/mobile/sensors" in M20_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/device-capabilities" in failure for failure in failures)
    assert any("/device-capabilities/execute" in failure for failure in failures)
    assert any("/mobile/sensors" in failure for failure in failures)
