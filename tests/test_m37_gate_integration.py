from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import (
    m37_control_center_surface_failures,
    m37_openapi_route_failures,
)


def test_m37_gate_criteria_are_registered_and_pass():
    criteria = default_foundation_gate_criteria()
    ids = {criterion.criterion_id for criterion in criteria}

    assert "m37_file_review_approval_capture_contracts" in ids
    assert "m37_file_review_approval_capture_route_boundary" in ids
    assert "m37_control_center_review_only_approval_capture" in ids
    assert "m37_roadmap_currentness" in ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [item for item in report.results if item.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


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
