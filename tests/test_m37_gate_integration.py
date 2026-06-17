from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import (
    m37_control_center_surface_failures,
    m37_openapi_route_failures,
)


def test_m37_gate_criteria_are_registered_and_pass(foundation_gate_results):
    criteria = default_foundation_gate_criteria()
    ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m37_file_review_approval_capture_contracts",
        "m37_file_review_approval_capture_route_boundary",
        "m37_control_center_review_only_approval_capture",
        "m37_roadmap_currentness",
    ]

    for criterion_id in expected:
        assert criterion_id in ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m37_route_boundary_allows_only_capture_route():
    failures = m37_openapi_route_failures(
        {
            "/api/manifest": {},
            "/files/review/approvals/capture": {},
            "/files/read/raw": {},
            "/context/propose": {},
        }
    )

    assert not any("/files/review/approvals/capture" in failure for failure in failures)
    assert any("/files/read/raw" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)


def test_m37_frontend_surface_rejects_unsafe_capture_controls():
    failures = m37_control_center_surface_failures(
        component_text="""
        <button>Approve review-only</button>
        <button>Export raw file</button>
        <button>Inject context</button>
        <button>Execute tool</button>
        """
    )

    assert any("export" in failure.lower() for failure in failures)
    assert any("context" in failure.lower() for failure in failures)
    assert any("execute" in failure.lower() for failure in failures)
