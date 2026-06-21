from typing import Any
from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m44_openapi_route_failures


def test_m44_gate_criteria_are_registered_and_pass(foundation_gate_results: Any) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m44_ccc_ios_skeleton_no_authority",
        "m44_ios_skeleton_static_safety",
        "m44_mobile_route_boundary",
        "m44_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


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
