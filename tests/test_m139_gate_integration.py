from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m139_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m139_autonomy_abuse_loop_detection_contracts" in ids
    assert "m139_autonomy_abuse_loop_detection_static_safety" in ids
    assert "m139_autonomy_abuse_loop_detection_route_boundary" in ids
    assert "m139_roadmap_currentness" in ids


def test_m139_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m139_autonomy_abuse_loop_detection_contracts",
        "m139_autonomy_abuse_loop_detection_static_safety",
        "m139_autonomy_abuse_loop_detection_route_boundary",
        "m139_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m139_route_boundary_rejects_abuse_loop_detection_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/autonomy/abuse-loop-detection": {},
        "/autonomy/abuse-loop-detection/start": {},
        "/autonomy/abuse-loop-detection/run": {},
        "/abuse-detection/run": {},
        "/abuse-detection/execute": {},
        "/loop-detection/run": {},
        "/loop-detection/execute": {},
        "/loop-detection/intervene": {},
        "/autonomy/loop-monitor/start": {},
        "/loop-monitor/start": {},
        "/loop-intervention/execute": {},
        "/loop-recovery/execute": {},
        "/recovery/execute": {},
        "/tools/execute": {},
        "/browser/click": {},
        "/connectors/write": {},
    }
    failures = gate_evaluators.m139_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/autonomy/abuse-loop-detection",
        "/autonomy/abuse-loop-detection/start",
        "/abuse-detection/run",
        "/loop-detection/run",
        "/loop-detection/intervene",
        "/loop-monitor/start",
        "/loop-intervention/execute",
        "/recovery/execute",
        "/tools/execute",
        "/browser/click",
        "/connectors/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m139_openapi_route_failures(app.openapi().get("paths", {}))


def test_m139_static_safety_detects_abuse_loop_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "abuse_detection_runtime_enabled=True\n"
        "loop_detection_runtime_enabled=True\n"
        "loop_monitor_enabled=True\n"
        "detector_runtime_enabled=True\n"
        "loop_intervention_enabled=True\n"
        "autonomous_recovery_execution_enabled=True\n"
        "retry_execution_enabled=True\n"
        "rollback_execution_enabled=True\n"
        "dependency_execution_enabled=True\n"
        "browser_action_enabled=True\n"
        "connector_action_enabled=True\n"
        "tool_execution_enabled=True\n"
        "execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "network_access_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "abuse_detection_runtime_authorized=True\n"
        "loop_detection_runtime_authorized=True\n"
        "loop_monitor_started=True\n"
        "detector_runtime_started=True\n"
        "loop_intervention_performed=True\n"
        "autonomous_recovery_execution_authorized=True\n"
        "retry_execution_performed=True\n"
        "rollback_execution_performed=True\n"
        "resume_execution_performed=True\n"
        "dependency_execution_performed=True\n"
        "browser_action_performed=True\n"
        "connector_action_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/abuse-loop-detection/start\n"
        "/abuse-detection/run\n"
        "/loop-detection/run\n"
        "/loop-detection/intervene\n"
        "/loop-monitor/start\n"
        "/loop-intervention/execute\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m139_autonomy_abuse_loop_detection_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m139_autonomy_abuse_loop_detection_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "abuse_detection_runtime_enabled=True",
        "loop_detection_runtime_enabled=True",
        "loop_monitor_enabled=True",
        "detector_runtime_enabled=True",
        "loop_intervention_enabled=True",
        "autonomous_recovery_execution_enabled=True",
        "retry_execution_enabled=True",
        "rollback_execution_enabled=True",
        "dependency_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "tool_execution_enabled=True",
        "backend_route_enabled=True",
        "production_authority_granted=True",
        "abuse_detection_runtime_authorized=True",
        "loop_detection_runtime_authorized=True",
        "loop_monitor_started=True",
        "detector_runtime_started=True",
        "loop_intervention_performed=True",
        "retry_execution_performed=True",
        "rollback_execution_performed=True",
        "resume_execution_performed=True",
        "/autonomy/abuse-loop-detection/start",
        "/abuse-detection/run",
        "/loop-detection/run",
        "/loop-detection/intervene",
        "/loop-monitor/start",
        "/loop-intervention/execute",
    ]:
        assert any(fragment in failure for failure in result.failures)
