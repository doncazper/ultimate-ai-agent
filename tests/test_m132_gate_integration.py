from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m132_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m132_trusted_recurring_workflow_contracts" in ids
    assert "m132_trusted_recurring_workflow_static_safety" in ids
    assert "m132_trusted_recurring_workflow_route_boundary" in ids
    assert "m132_roadmap_currentness" in ids


def test_m132_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m132_trusted_recurring_workflow_contracts",
        "m132_trusted_recurring_workflow_static_safety",
        "m132_trusted_recurring_workflow_route_boundary",
        "m132_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m132_route_boundary_rejects_mode5_scheduler_and_supervisor_routes() -> None:
    failures = gate_evaluators.m132_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/mode5": {},
            "/autonomy/mode5/start": {},
            "/autonomy/trusted-recurring-workflow": {},
            "/autonomy/trusted-recurring-workflow/start": {},
            "/autonomy/workflow/start": {},
            "/autonomy/recurrence/start": {},
            "/automation/trusted-recurring/start": {},
            "/automation/recurring/start": {},
            "/scheduler/create": {},
            "/scheduler/start": {},
            "/background/start": {},
            "/workers/start": {},
            "/supervisor/start": {},
            "/supervisor/long-running/start": {},
            "/shell/execute": {},
            "/commands/execute": {},
            "/browser/click": {},
            "/browser/form": {},
            "/browser/download": {},
            "/browser/upload": {},
            "/network/post": {},
            "/plugins/execute": {},
            "/connectors/runtime": {},
            "/connectors/auth": {},
            "/mobile/sensors": {},
            "/remote/execute": {},
            "/memory/write": {},
            "/context/inject": {},
            "/models/call": {},
        },
        expected_path_count=30,
    )

    for forbidden in [
        "/autonomy/mode5",
        "/autonomy/mode5/start",
        "/autonomy/trusted-recurring-workflow",
        "/autonomy/trusted-recurring-workflow/start",
        "/autonomy/workflow/start",
        "/autonomy/recurrence/start",
        "/automation/trusted-recurring/start",
        "/automation/recurring/start",
        "/scheduler/create",
        "/scheduler/start",
        "/background/start",
        "/workers/start",
        "/supervisor/start",
        "/supervisor/long-running/start",
        "/shell/execute",
        "/commands/execute",
        "/browser/click",
        "/browser/form",
        "/browser/download",
        "/browser/upload",
        "/network/post",
        "/plugins/execute",
        "/connectors/runtime",
        "/connectors/auth",
        "/mobile/sensors",
        "/remote/execute",
        "/memory/write",
        "/context/inject",
        "/models/call",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m132_openapi_route_failures(app.openapi().get("paths", {}))


def test_m132_static_safety_detects_recurring_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "mode5_runtime_enabled=True\n"
        "trusted_recurring_workflow_start_enabled=True\n"
        "recurring_runtime_enabled=True\n"
        "recurrence_active=True\n"
        "scheduler_enabled=True\n"
        "background_worker_enabled=True\n"
        "long_running_supervisor_enabled=True\n"
        "autonomous_actions_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "network_access_enabled=True\n"
        "browser_automation_enabled=True\n"
        "browser_form_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "mode5_runtime_requested=True\n"
        "trusted_recurring_workflow_start_requested=True\n"
        "workflow_started=True\n"
        "recurring_runtime_started=True\n"
        "scheduler_started=True\n"
        "long_running_supervisor_started=True\n"
        "autonomous_actions_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/mode5/start\n"
        "/autonomy/trusted-recurring-workflow/start\n"
        "/scheduler/start\n"
        "/supervisor/long-running/start\n"
        "/browser/form\n"
        "/plugins/execute\n"
        "/models/call\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m132_trusted_recurring_workflow_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m132_trusted_recurring_workflow_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "mode5_runtime_enabled=True",
        "trusted_recurring_workflow_start_enabled=True",
        "recurring_runtime_enabled=True",
        "recurrence_active=True",
        "scheduler_enabled=True",
        "background_worker_enabled=True",
        "long_running_supervisor_enabled=True",
        "autonomous_actions_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_access_enabled=True",
        "browser_automation_enabled=True",
        "browser_form_enabled=True",
        "plugin_execution_enabled=True",
        "connector_runtime_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "production_authority_granted=True",
        "mode5_runtime_requested=True",
        "trusted_recurring_workflow_start_requested=True",
        "workflow_started=True",
        "recurring_runtime_started=True",
        "scheduler_started=True",
        "long_running_supervisor_started=True",
        "autonomous_actions_performed=True",
        "tool_execution_performed=True",
        "/autonomy/mode5/start",
        "/autonomy/trusted-recurring-workflow/start",
        "/scheduler/start",
        "/supervisor/long-running/start",
        "/browser/form",
        "/plugins/execute",
        "/models/call",
    ]:
        assert any(fragment in failure for failure in result.failures)
