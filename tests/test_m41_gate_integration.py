from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateReport,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import m41_openapi_route_failures


def test_m41_gate_criteria_are_registered_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m41_local_prototype_safety_freeze" in criterion_ids
    assert "m41_local_prototype_route_boundary" in criterion_ids
    assert "m41_roadmap_currentness" in criterion_ids

    report = FoundationGateEvaluator().evaluate(criteria)
    failed = [result for result in report.results if result.status == "failed"]

    assert not failed
    assert FoundationGateReport.model_validate(report.model_dump())


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
