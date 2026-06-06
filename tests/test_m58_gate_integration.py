from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m58_openapi_route_failures,
)


def test_m58_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m58_dry_run_execution_audit_harness" in ids
    assert "m58_dry_run_execution_static_safety" in ids
    assert "m58_dry_run_execution_route_boundary" in ids
    assert "m58_roadmap_currentness" in ids


def test_m58_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m58_dry_run_execution_audit_harness",
        "m58_dry_run_execution_static_safety",
        "m58_dry_run_execution_route_boundary",
        "m58_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m58_openapi_route_guard_denies_execution_audit_routes() -> None:
    failures = m58_openapi_route_failures(
        {
            "/dry-run/execute": {},
            "/dry-run/run": {},
            "/execution/audit/run": {},
            "/shell/execute": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        }
    )

    assert any("/dry-run/execute" in failure for failure in failures)
    assert any("/dry-run/run" in failure for failure in failures)
    assert any("/execution/audit/run" in failure for failure in failures)
    assert any("/shell/execute" in failure for failure in failures)
    assert any("/tools/execute" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert not m58_openapi_route_failures(app.openapi().get("paths", {}))
