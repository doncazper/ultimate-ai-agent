from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m105_openapi_route_failures,
)


def test_m105_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m105_background_task_contract_no_execution_contracts" in ids
    assert "m105_background_task_contract_no_execution_static_safety" in ids
    assert "m105_background_task_contract_no_execution_route_boundary" in ids
    assert "m105_roadmap_currentness" in ids


def test_m105_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m105_background_task_contract_no_execution_contracts",
        "m105_background_task_contract_no_execution_static_safety",
        "m105_background_task_contract_no_execution_route_boundary",
        "m105_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m105_route_boundary_rejects_background_runtime_routes() -> None:
    failures = m105_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/background/tasks": {},
            "/mobile/background/tasks/start": {},
            "/mobile/background/tasks/schedule": {},
            "/mobile/background/workers": {},
            "/mobile/background/daemon": {},
            "/mobile/permissions/background/prompt": {},
            "/mobile/notifications/push": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/mobile/background/tasks",
        "/mobile/background/tasks/start",
        "/mobile/background/tasks/schedule",
        "/mobile/background/workers",
        "/mobile/background/daemon",
        "/mobile/permissions/background/prompt",
        "/mobile/notifications/push",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m105_openapi_route_failures(app.openapi().get("paths", {}))


def test_m105_static_safety_detects_background_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "background_worker_enabled=True\nscheduler_enabled=True\ndaemon_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m105_background_task_contract_no_execution_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m105_background_task_contract_no_execution_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("background_worker_enabled=True" in failure for failure in result.failures)
    assert any("scheduler_enabled=True" in failure for failure in result.failures)
    assert any("daemon_enabled=True" in failure for failure in result.failures)
