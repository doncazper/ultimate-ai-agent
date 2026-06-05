from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m44_openapi_route_failures


def test_m44_gate_criteria_are_registered_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m44_ccc_ios_skeleton_no_authority" in criterion_ids
    assert "m44_ios_skeleton_static_safety" in criterion_ids
    assert "m44_mobile_route_boundary" in criterion_ids
    assert "m44_roadmap_currentness" in criterion_ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [result for result in report.results if result.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


def test_m44_route_boundary_rejects_mobile_and_native_authority_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/files/review/approvals/capture": {},
        "/mobile/app/build": {},
        "/mobile/ios/build": {},
        "/mobile/ios/sign": {},
        "/mobile/ios/sensors": {},
        "/mobile/ios/approvals/capture": {},
        "/mobile/ios/approvals/execute": {},
        "/mobile/ios/context/inject": {},
        "/mobile/ios/memory/write": {},
        "/mobile/ios/execute": {},
    }

    failures = m44_openapi_route_failures(paths, expected_path_count=len(paths))

    for forbidden in [
        "/mobile/app/build",
        "/mobile/ios/build",
        "/mobile/ios/sign",
        "/mobile/ios/sensors",
        "/mobile/ios/approvals/capture",
        "/mobile/ios/approvals/execute",
        "/mobile/ios/context/inject",
        "/mobile/ios/memory/write",
        "/mobile/ios/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
