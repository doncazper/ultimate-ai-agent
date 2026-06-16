from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m136_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m136_cross_tool_dependency_execution_contracts" in ids
    assert "m136_cross_tool_dependency_execution_static_safety" in ids
    assert "m136_cross_tool_dependency_execution_route_boundary" in ids
    assert "m136_roadmap_currentness" in ids


def test_m136_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m136_cross_tool_dependency_execution_contracts",
        "m136_cross_tool_dependency_execution_static_safety",
        "m136_cross_tool_dependency_execution_route_boundary",
        "m136_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m136_route_boundary_rejects_cross_tool_dependency_runtime_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/autonomy/cross-tool-dependency-execution": {},
        "/autonomy/cross-tool-dependency-execution/start": {},
        "/autonomy/cross-tool-dependency-execution/run": {},
        "/dependency-execution/execute": {},
        "/dependency-execution/run": {},
        "/dependency-execution/resolve": {},
        "/dependency-resolver/start": {},
        "/cross-tool/runtime": {},
        "/cross-tool/run": {},
        "/tools/execute": {},
        "/tools/run": {},
        "/tool-runtime/execute": {},
        "/tool-state/handoff": {},
        "/tool-output/route": {},
        "/connectors/runtime": {},
        "/connectors/write": {},
        "/browser/click": {},
        "/browser/form": {},
        "/browser/download": {},
        "/browser/upload": {},
        "/network/post": {},
        "/plugins/execute": {},
        "/scheduler/start": {},
        "/background/start": {},
        "/workers/start": {},
    }
    failures = gate_evaluators.m136_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/autonomy/cross-tool-dependency-execution",
        "/autonomy/cross-tool-dependency-execution/start",
        "/autonomy/cross-tool-dependency-execution/run",
        "/dependency-execution/execute",
        "/dependency-execution/run",
        "/dependency-execution/resolve",
        "/dependency-resolver/start",
        "/cross-tool/runtime",
        "/cross-tool/run",
        "/tools/execute",
        "/tools/run",
        "/tool-runtime/execute",
        "/tool-state/handoff",
        "/tool-output/route",
        "/connectors/runtime",
        "/connectors/write",
        "/browser/click",
        "/browser/form",
        "/browser/download",
        "/browser/upload",
        "/network/post",
        "/plugins/execute",
        "/scheduler/start",
        "/background/start",
        "/workers/start",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m136_openapi_route_failures(app.openapi().get("paths", {}))


def test_m136_static_safety_detects_cross_tool_dependency_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "mode5_runtime_enabled=True\n"
        "cross_tool_dependency_runtime_enabled=True\n"
        "dependency_execution_enabled=True\n"
        "dependency_resolver_runtime_enabled=True\n"
        "cross_tool_runtime_enabled=True\n"
        "parallel_tool_execution_enabled=True\n"
        "tool_state_handoff_enabled=True\n"
        "tool_output_routing_enabled=True\n"
        "recovery_execution_enabled=True\n"
        "supervisor_runtime_enabled=True\n"
        "checkpoint_scheduler_enabled=True\n"
        "human_checkpoint_prompt_enabled=True\n"
        "scheduler_enabled=True\n"
        "background_worker_enabled=True\n"
        "autonomous_actions_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "command_execution_enabled=True\n"
        "subprocess_execution_enabled=True\n"
        "filesystem_mutation_enabled=True\n"
        "network_access_enabled=True\n"
        "browser_automation_enabled=True\n"
        "browser_form_enabled=True\n"
        "authenticated_browser_enabled=True\n"
        "download_enabled=True\n"
        "upload_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "account_auth_enabled=True\n"
        "mobile_sensor_enabled=True\n"
        "remote_execution_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "control_center_control_enabled=True\n"
        "dependency_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "mode5_runtime_authorized=True\n"
        "cross_tool_dependency_runtime_authorized=True\n"
        "dependency_execution_authorized=True\n"
        "dependency_execution_performed=True\n"
        "dependency_resolver_runtime_started=True\n"
        "cross_tool_runtime_started=True\n"
        "parallel_tool_execution_performed=True\n"
        "tool_state_handoff_performed=True\n"
        "tool_output_routing_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/cross-tool-dependency-execution/start\n"
        "/dependency-execution/execute\n"
        "/dependency-resolver/start\n"
        "/cross-tool/runtime\n"
        "/tool-state/handoff\n"
        "/tool-output/route\n"
        "/connectors/write\n"
        "/browser/click\n"
        "/browser/form\n"
        "/plugins/execute\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m136_cross_tool_dependency_execution_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m136_cross_tool_dependency_execution_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "mode5_runtime_enabled=True",
        "cross_tool_dependency_runtime_enabled=True",
        "dependency_execution_enabled=True",
        "dependency_resolver_runtime_enabled=True",
        "cross_tool_runtime_enabled=True",
        "parallel_tool_execution_enabled=True",
        "tool_state_handoff_enabled=True",
        "tool_output_routing_enabled=True",
        "recovery_execution_enabled=True",
        "supervisor_runtime_enabled=True",
        "checkpoint_scheduler_enabled=True",
        "human_checkpoint_prompt_enabled=True",
        "scheduler_enabled=True",
        "background_worker_enabled=True",
        "autonomous_actions_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "command_execution_enabled=True",
        "subprocess_execution_enabled=True",
        "filesystem_mutation_enabled=True",
        "network_access_enabled=True",
        "browser_automation_enabled=True",
        "browser_form_enabled=True",
        "authenticated_browser_enabled=True",
        "download_enabled=True",
        "upload_enabled=True",
        "plugin_execution_enabled=True",
        "connector_runtime_enabled=True",
        "account_auth_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "backend_route_enabled=True",
        "control_center_control_enabled=True",
        "dependency_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "mode5_runtime_authorized=True",
        "cross_tool_dependency_runtime_authorized=True",
        "dependency_execution_authorized=True",
        "dependency_execution_performed=True",
        "dependency_resolver_runtime_started=True",
        "cross_tool_runtime_started=True",
        "parallel_tool_execution_performed=True",
        "tool_state_handoff_performed=True",
        "tool_output_routing_performed=True",
        "tool_execution_performed=True",
        "/autonomy/cross-tool-dependency-execution/start",
        "/dependency-execution/execute",
        "/dependency-resolver/start",
        "/cross-tool/runtime",
        "/tool-state/handoff",
        "/tool-output/route",
        "/connectors/write",
        "/browser/click",
        "/browser/form",
        "/plugins/execute",
    ]:
        assert any(fragment in failure for failure in result.failures)
