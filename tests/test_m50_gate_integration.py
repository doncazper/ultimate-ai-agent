from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator, m50_openapi_route_failures


def test_m50_foundation_gate_criteria_are_registered() -> None:
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    assert "m50_mobile_approval_audit_hardening" in criteria
    assert "m50_mobile_audit_static_safety" in criteria
    assert "m50_mobile_audit_route_boundary" in criteria
    assert "m50_roadmap_currentness" in criteria


def test_m50_evaluator_accepts_current_repository() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m50_mobile_approval_audit_hardening",
        "m50_mobile_audit_static_safety",
        "m50_mobile_audit_route_boundary",
        "m50_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m50_route_guard_rejects_mobile_audit_mutation_and_export_routes() -> None:
    failures = m50_openapi_route_failures(
        {
            "/mobile/review/audit": {},
            "/mobile/review/audit/export": {},
            "/mobile/review/audit/raw": {},
            "/mobile/approvals/audit/write": {},
            "/mobile/context/inject": {},
            "/mobile/memory/write": {},
            "/mobile/tools/execute": {},
        }
    )

    assert any("/mobile/review/audit" in failure for failure in failures)
    assert any("/mobile/review/audit/export" in failure for failure in failures)
    assert any("/mobile/review/audit/raw" in failure for failure in failures)
    assert any("/mobile/approvals/audit/write" in failure for failure in failures)
    assert any("/mobile/context/inject" in failure for failure in failures)
    assert any("/mobile/memory/write" in failure for failure in failures)
    assert any("/mobile/tools/execute" in failure for failure in failures)
    assert not m50_openapi_route_failures(app.openapi().get("paths", {}))
