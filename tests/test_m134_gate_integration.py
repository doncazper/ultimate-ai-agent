from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m134_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m134_human_checkpoint_scheduling_contracts" in ids
    assert "m134_human_checkpoint_scheduling_static_safety" in ids
    assert "m134_human_checkpoint_scheduling_route_boundary" in ids
    assert "m134_roadmap_currentness" in ids


def test_m134_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m134_human_checkpoint_scheduling_contracts",
        "m134_human_checkpoint_scheduling_static_safety",
        "m134_human_checkpoint_scheduling_route_boundary",
        "m134_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m134_route_boundary_rejects_checkpoint_runtime_routes() -> None:
    failures = gate_evaluators.m134_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/human-checkpoint-scheduling": {},
            "/autonomy/human-checkpoint-scheduling/start": {},
            "/checkpoints/human/schedule": {},
            "/checkpoints/human/prompt": {},
            "/checkpoints/human/notify": {},
            "/checkpoints/human/remind": {},
            "/calendar/write": {},
            "/approvals/capture": {},
            "/escalations/start": {},
            "/supervisor/recover": {},
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
        expected_path_count=30,
    )

    for forbidden in [
        "/autonomy/human-checkpoint-scheduling",
        "/autonomy/human-checkpoint-scheduling/start",
        "/checkpoints/human/schedule",
        "/checkpoints/human/prompt",
        "/checkpoints/human/notify",
        "/checkpoints/human/remind",
        "/calendar/write",
        "/approvals/capture",
        "/escalations/start",
        "/supervisor/recover",
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
    assert not gate_evaluators.m134_openapi_route_failures(app.openapi().get("paths", {}))


def test_m134_static_safety_detects_checkpoint_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "mode5_runtime_enabled=True\n"
        "human_checkpoint_scheduler_enabled=True\n"
        "human_checkpoint_prompt_enabled=True\n"
        "notification_delivery_enabled=True\n"
        "reminder_runtime_enabled=True\n"
        "calendar_write_enabled=True\n"
        "approval_capture_enabled=True\n"
        "escalation_runtime_enabled=True\n"
        "supervisor_runtime_enabled=True\n"
        "recovery_execution_enabled=True\n"
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
        "human_checkpoint_scheduler_requested=True\n"
        "human_checkpoint_prompt_requested=True\n"
        "notification_delivery_requested=True\n"
        "reminder_runtime_requested=True\n"
        "calendar_write_requested=True\n"
        "approval_capture_requested=True\n"
        "escalation_runtime_requested=True\n"
        "supervisor_runtime_started=True\n"
        "recovery_execution_performed=True\n"
        "checkpoint_scheduled=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/human-checkpoint-scheduling/start\n"
        "/checkpoints/human/schedule\n"
        "/checkpoints/human/prompt\n"
        "/checkpoints/human/notify\n"
        "/calendar/write\n"
        "/approvals/capture\n"
        "/supervisor/recover\n"
        "/browser/form\n"
        "/plugins/execute\n"
        "/models/call\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m134_human_checkpoint_scheduling_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m134_human_checkpoint_scheduling_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "human_checkpoint_scheduler_enabled=True",
        "human_checkpoint_prompt_enabled=True",
        "notification_delivery_enabled=True",
        "reminder_runtime_enabled=True",
        "calendar_write_enabled=True",
        "approval_capture_enabled=True",
        "escalation_runtime_enabled=True",
        "supervisor_runtime_enabled=True",
        "recovery_execution_enabled=True",
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
        "human_checkpoint_scheduler_requested=True",
        "human_checkpoint_prompt_requested=True",
        "notification_delivery_requested=True",
        "reminder_runtime_requested=True",
        "calendar_write_requested=True",
        "approval_capture_requested=True",
        "escalation_runtime_requested=True",
        "supervisor_runtime_started=True",
        "recovery_execution_performed=True",
        "checkpoint_scheduled=True",
        "tool_execution_performed=True",
        "/autonomy/human-checkpoint-scheduling/start",
        "/checkpoints/human/schedule",
        "/checkpoints/human/prompt",
        "/checkpoints/human/notify",
        "/calendar/write",
        "/approvals/capture",
        "/supervisor/recover",
        "/browser/form",
        "/plugins/execute",
        "/models/call",
    ]:
        assert any(fragment in failure for failure in result.failures)
