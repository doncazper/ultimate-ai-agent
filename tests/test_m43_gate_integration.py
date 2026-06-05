from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m43_openapi_route_failures


def test_m43_gate_criteria_are_registered_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m43_mobile_api_boundary_read_only" in criterion_ids
    assert "m43_mobile_route_boundary" in criterion_ids
    assert "m43_roadmap_currentness" in criterion_ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [result for result in report.results if result.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


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
