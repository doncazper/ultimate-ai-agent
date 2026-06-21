from typing import Any
from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m38_openapi_route_failures


def test_m38_gate_criteria_are_registered_and_pass(foundation_gate_results: Any) -> None:
    criteria = default_foundation_gate_criteria()
    ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m38_safe_context_proposal_contracts",
        "m38_safe_context_proposal_route_boundary",
        "m38_no_control_center_context_surface",
        "m38_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m38_route_boundary_rejects_future_context_and_openwebui_routes() -> None:
    failures = m38_openapi_route_failures(
        {
            "/api/manifest": {},
            "/files/review/approvals/capture": {},
            "/context/propose": {},
            "/context/inject": {},
            "/openwebui/handoff": {},
        }
    )

    assert not any("/files/review/approvals/capture" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/openwebui/handoff" in failure for failure in failures)
