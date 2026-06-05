from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m38_openapi_route_failures


def test_m38_gate_criteria_are_registered_and_pass():
    criteria = default_foundation_gate_criteria()
    ids = {criterion.criterion_id for criterion in criteria}

    assert "m38_safe_context_proposal_contracts" in ids
    assert "m38_safe_context_proposal_route_boundary" in ids
    assert "m38_no_control_center_context_surface" in ids
    assert "m38_roadmap_currentness" in ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [item for item in report.results if item.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


def test_m38_route_boundary_rejects_future_context_and_openwebui_routes():
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
