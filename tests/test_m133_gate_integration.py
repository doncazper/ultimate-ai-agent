from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m133_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m133_long_running_task_supervisor_contracts" in ids
    assert "m133_long_running_task_supervisor_static_safety" in ids
    assert "m133_long_running_task_supervisor_route_boundary" in ids
    assert "m133_roadmap_currentness" in ids


def test_m133_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m133_long_running_task_supervisor_contracts",
        "m133_long_running_task_supervisor_static_safety",
        "m133_long_running_task_supervisor_route_boundary",
        "m133_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m133_route_boundary_rejects_supervisor_runtime_routes() -> None:
    failures = gate_evaluators.m133_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/long-running-supervisor": {},
            "/autonomy/long-running-supervisor/start": {},
            "/supervisor/long-running": {},
            "/supervisor/long-running/start": {},
            "/supervisor/tasks/start": {},
            "/supervisor/heartbeat/start": {},
            "/supervisor/checkpoints/schedule": {},
            "/supervisor/resume": {},
            "/supervisor/recover": {},
            "/checkpoints/human/schedule": {},
            "/tasks/long-running/start": {},
            "/background/supervisor/start": {},
            "/scheduler/start": {},
            "/workers/start": {},
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
        "/autonomy/long-running-supervisor",
        "/autonomy/long-running-supervisor/start",
        "/supervisor/long-running",
        "/supervisor/long-running/start",
        "/supervisor/tasks/start",
        "/supervisor/heartbeat/start",
        "/supervisor/checkpoints/schedule",
        "/supervisor/resume",
        "/supervisor/recover",
        "/checkpoints/human/schedule",
        "/tasks/long-running/start",
        "/background/supervisor/start",
        "/scheduler/start",
        "/workers/start",
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
    assert not gate_evaluators.m133_openapi_route_failures(app.openapi().get("paths", {}))


def test_m133_static_safety_detects_supervisor_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "supervisor_runtime_enabled=True\n"
        "long_running_supervisor_start_enabled=True\n"
        "task_supervision_enabled=True\n"
        "heartbeat_monitor_enabled=True\n"
        "checkpoint_scheduler_enabled=True\n"
        "resume_execution_enabled=True\n"
        "recovery_execution_enabled=True\n"
        "human_checkpoint_scheduling_enabled=True\n"
        "scheduler_enabled=True\n"
        "background_worker_enabled=True\n"
        "autonomous_actions_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "network_access_enabled=True\n"
        "browser_automation_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "supervisor_runtime_requested=True\n"
        "long_running_supervisor_start_requested=True\n"
        "supervisor_started=True\n"
        "task_supervision_active=True\n"
        "heartbeat_monitor_started=True\n"
        "checkpoint_scheduler_started=True\n"
        "resume_execution_performed=True\n"
        "recovery_execution_performed=True\n"
        "human_checkpoint_scheduling_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/long-running-supervisor/start\n"
        "/supervisor/heartbeat/start\n"
        "/supervisor/checkpoints/schedule\n"
        "/supervisor/recover\n"
        "/checkpoints/human/schedule\n"
        "/browser/form\n"
        "/plugins/execute\n"
        "/models/call\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m133_long_running_task_supervisor_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m133_long_running_task_supervisor_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "supervisor_runtime_enabled=True",
        "long_running_supervisor_start_enabled=True",
        "task_supervision_enabled=True",
        "heartbeat_monitor_enabled=True",
        "checkpoint_scheduler_enabled=True",
        "resume_execution_enabled=True",
        "recovery_execution_enabled=True",
        "human_checkpoint_scheduling_enabled=True",
        "scheduler_enabled=True",
        "background_worker_enabled=True",
        "autonomous_actions_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_access_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "connector_runtime_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "production_authority_granted=True",
        "supervisor_runtime_requested=True",
        "long_running_supervisor_start_requested=True",
        "supervisor_started=True",
        "task_supervision_active=True",
        "heartbeat_monitor_started=True",
        "checkpoint_scheduler_started=True",
        "resume_execution_performed=True",
        "recovery_execution_performed=True",
        "human_checkpoint_scheduling_performed=True",
        "tool_execution_performed=True",
        "/autonomy/long-running-supervisor/start",
        "/supervisor/heartbeat/start",
        "/supervisor/checkpoints/schedule",
        "/supervisor/recover",
        "/checkpoints/human/schedule",
        "/browser/form",
        "/plugins/execute",
        "/models/call",
    ]:
        assert any(fragment in failure for failure in result.failures)
