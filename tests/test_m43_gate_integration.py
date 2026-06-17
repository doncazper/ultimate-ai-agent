from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m43_openapi_route_failures


def test_m43_gate_criteria_are_registered_and_pass(foundation_gate_results) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m43_mobile_api_boundary_read_only",
        "m43_mobile_route_boundary",
        "m43_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m43_route_boundary_rejects_mobile_mutation_and_raw_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/mobile": {},
        "/mobile/api": {},
        "/mobile/api/write": {},
        "/mobile/sensors": {},
        "/mobile/approvals/capture": {},
        "/mobile/approvals/execute": {},
        "/mobile/files/raw": {},
        "/context/inject": {},
        "/memory/write": {},
        "/tools/execute": {},
    }

    failures = m43_openapi_route_failures(paths, expected_path_count=len(paths))

    for forbidden in [
        "/mobile",
        "/mobile/api",
        "/mobile/api/write",
        "/mobile/sensors",
        "/mobile/approvals/capture",
        "/mobile/approvals/execute",
        "/mobile/files/raw",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)


def test_m43_route_boundary_requires_m37_capture_route() -> None:
    failures = m43_openapi_route_failures({"/api/manifest": {}}, expected_path_count=1)

    assert any("M37 capture route missing" in failure for failure in failures)
