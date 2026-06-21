from typing import Any
from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m40_openapi_route_failures


def test_m40_gate_criteria_are_registered_and_pass(foundation_gate_results: Any) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m40_context_handoff_approval_contracts",
        "m40_context_handoff_route_boundary",
        "m40_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m40_route_boundary_rejects_injection_handoff_and_execution_routes() -> None:
    paths = {
        "/files/review/approvals/capture": {},
        "/context/propose": {},
        "/context/handoff": {},
        "/context/handoff/approve": {},
        "/context/inject": {},
        "/openwebui/handoff": {},
        "/memory/write": {},
        "/tools/execute": {},
    }

    failures = m40_openapi_route_failures(paths, expected_path_count=len(paths))

    assert not any("/files/review/approvals/capture" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)
    assert any("/context/handoff" in failure for failure in failures)
    assert any("/context/handoff/approve" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/openwebui/handoff" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)


def test_m40_route_boundary_requires_m37_capture_route() -> None:
    failures = m40_openapi_route_failures({"/api/manifest": {}}, expected_path_count=1)

    assert any("M37 capture route missing" in failure for failure in failures)
