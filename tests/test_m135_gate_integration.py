from typing import Any
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m135_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m135_autonomous_recovery_planner_contracts" in ids
    assert "m135_autonomous_recovery_planner_static_safety" in ids
    assert "m135_autonomous_recovery_planner_route_boundary" in ids
    assert "m135_roadmap_currentness" in ids


def test_m135_foundation_gate_evaluator_accepts_current_repo(
    foundation_gate_results: Any,
) -> None:
    for criterion_id in [
        "m135_autonomous_recovery_planner_contracts",
        "m135_autonomous_recovery_planner_static_safety",
        "m135_autonomous_recovery_planner_route_boundary",
        "m135_roadmap_currentness",
    ]:
        result = foundation_gate_results[criterion_id]
        assert result.status == "passed", result.failures


def test_m135_route_boundary_rejects_recovery_runtime_routes() -> None:
    failures = gate_evaluators.m135_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/autonomous-recovery-planner": {},
            "/autonomy/autonomous-recovery-planner/start": {},
            "/autonomy/recovery/execute": {},
            "/recovery/execute": {},
            "/recovery/retry": {},
            "/recovery/resume": {},
            "/recovery/rollback": {},
            "/supervisor/recover": {},
            "/supervisor/resume": {},
            "/supervisor/start": {},
            "/checkpoints/schedule": {},
            "/checkpoints/human/schedule": {},
            "/checkpoints/human/prompt": {},
            "/checkpoints/human/notify": {},
            "/scheduler/start": {},
            "/background/start": {},
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
        expected_path_count=33,
    )

    for forbidden in [
        "/autonomy/autonomous-recovery-planner",
        "/autonomy/autonomous-recovery-planner/start",
        "/autonomy/recovery/execute",
        "/recovery/execute",
        "/recovery/retry",
        "/recovery/resume",
        "/recovery/rollback",
        "/supervisor/recover",
        "/supervisor/resume",
        "/supervisor/start",
        "/checkpoints/schedule",
        "/checkpoints/human/schedule",
        "/checkpoints/human/prompt",
        "/checkpoints/human/notify",
        "/scheduler/start",
        "/background/start",
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
    assert not gate_evaluators.m135_openapi_route_failures(app.openapi().get("paths", {}))


def test_m135_static_safety_detects_recovery_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "recovery_planner_runtime_enabled=True\n"
        "recovery_execution_enabled=True\n"
        "retry_execution_enabled=True\n"
        "resume_execution_enabled=True\n"
        "rollback_execution_enabled=True\n"
        "supervisor_runtime_enabled=True\n"
        "checkpoint_scheduler_enabled=True\n"
        "human_checkpoint_scheduler_enabled=True\n"
        "human_checkpoint_prompt_enabled=True\n"
        "notification_delivery_enabled=True\n"
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
        "recovery_execution_requested=True\n"
        "retry_execution_requested=True\n"
        "resume_execution_requested=True\n"
        "rollback_execution_requested=True\n"
        "recovery_execution_authorized=True\n"
        "recovery_execution_performed=True\n"
        "retry_execution_performed=True\n"
        "resume_execution_performed=True\n"
        "rollback_execution_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/autonomous-recovery-planner/start\n"
        "/autonomy/recovery/execute\n"
        "/recovery/retry\n"
        "/recovery/resume\n"
        "/recovery/rollback\n"
        "/supervisor/recover\n"
        "/checkpoints/schedule\n"
        "/browser/form\n"
        "/plugins/execute\n"
        "/models/call\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m135_autonomous_recovery_planner_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m135_autonomous_recovery_planner_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "recovery_planner_runtime_enabled=True",
        "recovery_execution_enabled=True",
        "retry_execution_enabled=True",
        "resume_execution_enabled=True",
        "rollback_execution_enabled=True",
        "supervisor_runtime_enabled=True",
        "checkpoint_scheduler_enabled=True",
        "human_checkpoint_scheduler_enabled=True",
        "human_checkpoint_prompt_enabled=True",
        "notification_delivery_enabled=True",
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
        "recovery_execution_requested=True",
        "retry_execution_requested=True",
        "resume_execution_requested=True",
        "rollback_execution_requested=True",
        "recovery_execution_authorized=True",
        "recovery_execution_performed=True",
        "retry_execution_performed=True",
        "resume_execution_performed=True",
        "rollback_execution_performed=True",
        "tool_execution_performed=True",
        "/autonomy/autonomous-recovery-planner/start",
        "/autonomy/recovery/execute",
        "/recovery/retry",
        "/recovery/resume",
        "/recovery/rollback",
        "/supervisor/recover",
        "/checkpoints/schedule",
        "/browser/form",
        "/plugins/execute",
        "/models/call",
    ]:
        assert any(fragment in failure for failure in result.failures)
