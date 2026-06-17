from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m41_openapi_route_failures


def test_m41_gate_criteria_are_registered_and_pass(foundation_gate_results) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m41_local_prototype_safety_freeze",
        "m41_local_prototype_route_boundary",
        "m41_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m41_route_boundary_rejects_post_freeze_runtime_routes() -> None:
    paths = {
        "/files/review/approvals/capture": {},
        "/files/read": {},
        "/files/read/raw": {},
        "/files/write": {},
        "/context/propose": {},
        "/context/handoff": {},
        "/context/inject": {},
        "/openwebui/handoff": {},
        "/memory/write": {},
        "/browser/execute": {},
        "/plugins/enable": {},
        "/tools/execute": {},
        "/tool-runtime/execute": {},
    }

    failures = m41_openapi_route_failures(paths, expected_path_count=len(paths))

    assert not any("/files/review/approvals/capture" in failure for failure in failures)
    for forbidden in [
        "/files/read",
        "/files/read/raw",
        "/files/write",
        "/context/propose",
        "/context/handoff",
        "/context/inject",
        "/openwebui/handoff",
        "/memory/write",
        "/browser/execute",
        "/plugins/enable",
        "/tools/execute",
        "/tool-runtime/execute",
    ]:
        assert any(forbidden in failure for failure in failures)


def test_m41_route_boundary_requires_m37_capture_route() -> None:
    failures = m41_openapi_route_failures({"/api/manifest": {}}, expected_path_count=1)

    assert any("M37 capture route missing" in failure for failure in failures)
