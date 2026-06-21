from typing import Any
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m45_openapi_route_failures,
)
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria


def _gate_result(criteria_id: str) -> Any:
    criteria_by_id = {
        criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()
    }
    report = FoundationGateEvaluator().evaluate([criteria_by_id[criteria_id]])
    return report.results[0]


def test_m45_foundation_gate_local_connection_contract_passes() -> None:
    result = _gate_result("m45_ccc_ios_local_read_only_connection")

    assert result.status == "passed", result.failures


def test_m45_foundation_gate_static_safety_passes() -> None:
    result = _gate_result("m45_ios_local_connection_static_safety")

    assert result.status == "passed", result.failures


def test_m45_foundation_gate_route_boundary_passes() -> None:
    result = _gate_result("m45_mobile_route_boundary")

    assert result.status == "passed", result.failures


def test_m45_openapi_route_guard_rejects_forbidden_mobile_connection_routes() -> None:
    paths = {
        "/api/manifest",
        "/mobile/ios/connection",
    }

    failures = m45_openapi_route_failures(paths, expected_path_count=2)

    assert any("/mobile/ios/connection" in failure for failure in failures)
