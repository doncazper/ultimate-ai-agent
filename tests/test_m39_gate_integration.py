from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m39_openapi_route_failures


def test_m39_gate_criteria_are_registered_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m39_ccc_context_proposal_surface_safe" in criterion_ids
    assert "m39_context_proposal_route_boundary" in criterion_ids
    assert "m39_roadmap_currentness" in criterion_ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [result for result in report.results if result.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


def test_m39_route_boundary_rejects_future_handoff_and_injection_routes() -> None:
    paths = {
        "/files/review/approvals/capture": {},
        "/context/propose": {},
        "/context/inject": {},
        "/context/handoff": {},
        "/openwebui/handoff": {},
        "/memory/write": {},
        "/tools/execute": {},
    }

    failures = m39_openapi_route_failures(paths, expected_path_count=len(paths))

    assert not any("/files/review/approvals/capture" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/context/handoff" in failure for failure in failures)
    assert any("/openwebui/handoff" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)


def test_m39_route_boundary_requires_m37_capture_route() -> None:
    failures = m39_openapi_route_failures({"/api/manifest": {}}, expected_path_count=1)

    assert any("M37 capture route missing" in failure for failure in failures)
