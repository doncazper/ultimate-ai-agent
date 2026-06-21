from typing import Any
from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m42_openapi_route_failures


def test_m42_gate_criteria_are_registered_and_pass(foundation_gate_results: Any) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m42_mobile_product_contract_refresh",
        "m42_mobile_route_boundary",
        "m42_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m42_route_boundary_rejects_mobile_runtime_routes() -> None:
    paths = {
        "/files/review/approvals/capture": {},
        "/mobile": {},
        "/mobile/api": {},
        "/mobile/sensors": {},
        "/mobile/approvals/execute": {},
        "/control-center/mobile/capture": {},
        "/context/inject": {},
        "/tools/execute": {},
    }

    failures = m42_openapi_route_failures(paths, expected_path_count=len(paths))

    for forbidden in [
        "/mobile",
        "/mobile/api",
        "/mobile/sensors",
        "/mobile/approvals/execute",
        "/control-center/mobile/capture",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)


def test_m42_route_boundary_requires_m37_capture_route() -> None:
    failures = m42_openapi_route_failures({"/api/manifest": {}}, expected_path_count=1)

    assert any("M37 capture route missing" in failure for failure in failures)
