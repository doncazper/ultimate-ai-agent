from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m98_openapi_route_failures,
)


def test_m98_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m98_scoped_recurring_low_risk_automation" in ids
    assert "m98_scoped_recurring_low_risk_automation_static_safety" in ids
    assert "m98_scoped_recurring_low_risk_automation_route_boundary" in ids
    assert "m98_roadmap_currentness" in ids


def test_m98_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m98_scoped_recurring_low_risk_automation",
        "m98_scoped_recurring_low_risk_automation_static_safety",
        "m98_scoped_recurring_low_risk_automation_route_boundary",
        "m98_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m98_route_boundary_rejects_recurring_runtime_routes() -> None:
    failures = m98_openapi_route_failures(
        {
            "/api/manifest": {},
            "/automation/recurring/run": {},
            "/automation/recurring/start": {},
            "/automation/recurring/execute": {},
            "/scheduler/start": {},
            "/cron/run": {},
            "/background-worker/start": {},
            "/automation/recurring/worker": {},
            "/automation/recurring/collect": {},
            "/tools/execute": {},
            "/memory/write": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/automation/recurring/run",
        "/automation/recurring/start",
        "/automation/recurring/execute",
        "/scheduler/start",
        "/cron/run",
        "/background-worker/start",
        "/automation/recurring/worker",
        "/automation/recurring/collect",
        "/tools/execute",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m98_openapi_route_failures(app.openapi().get("paths", {}))


def test_m98_static_safety_detects_recurring_runtime_enablement(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/scoped_recurring_low_risk_automation"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("scheduler_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m98_scoped_recurring_low_risk_automation_static_safety"
    )
    result = FoundationGateEvaluator(
        tmp_path
    ).check_m98_scoped_recurring_low_risk_automation_static_safety(criterion)

    assert result.status == "failed"
    assert any("scheduler_enabled=True" in failure for failure in result.failures)
