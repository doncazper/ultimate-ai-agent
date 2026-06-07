from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m97_openapi_route_failures,
)


def test_m97_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m97_recurring_automation_contracts" in ids
    assert "m97_recurring_automation_static_safety" in ids
    assert "m97_recurring_automation_route_boundary" in ids
    assert "m97_roadmap_currentness" in ids


def test_m97_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m97_recurring_automation_contracts",
        "m97_recurring_automation_static_safety",
        "m97_recurring_automation_route_boundary",
        "m97_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m97_route_boundary_rejects_recurring_runtime_routes() -> None:
    failures = m97_openapi_route_failures(
        {
            "/api/manifest": {},
            "/automation/recurring/run": {},
            "/automation/recurring/start": {},
            "/automation/recurring/execute": {},
            "/scheduler/start": {},
            "/cron/run": {},
            "/background-worker/start": {},
            "/tools/execute": {},
            "/memory/write": {},
        },
        expected_path_count=9,
    )

    for forbidden in [
        "/automation/recurring/run",
        "/automation/recurring/start",
        "/automation/recurring/execute",
        "/scheduler/start",
        "/cron/run",
        "/background-worker/start",
        "/tools/execute",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m97_openapi_route_failures(app.openapi().get("paths", {}))


def test_m97_static_safety_detects_background_runtime_enablement(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/recurring_automation_contracts"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("background_worker_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m97_recurring_automation_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m97_recurring_automation_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("background_worker_enabled=True" in failure for failure in result.failures)
