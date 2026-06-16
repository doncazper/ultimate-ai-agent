from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m131_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m131_autonomy_mode4_scoped_work_session_contracts" in ids
    assert "m131_autonomy_mode4_scoped_work_session_static_safety" in ids
    assert "m131_autonomy_mode4_scoped_work_session_route_boundary" in ids
    assert "m131_roadmap_currentness" in ids


def test_m131_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m131_autonomy_mode4_scoped_work_session_contracts",
        "m131_autonomy_mode4_scoped_work_session_static_safety",
        "m131_autonomy_mode4_scoped_work_session_route_boundary",
        "m131_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m131_route_boundary_rejects_mode4_and_execution_routes() -> None:
    failures = gate_evaluators.m131_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/mode4": {},
            "/autonomy/mode4/start": {},
            "/autonomy/scoped-work-session": {},
            "/autonomy/scoped-work-session/start": {},
            "/autonomy/session/start": {},
            "/autonomy/actions/execute": {},
            "/autonomy/tools/execute": {},
            "/automation/session/start": {},
            "/automation/mode4/start": {},
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
            "/workers/start": {},
            "/scheduler/start": {},
            "/memory/write": {},
            "/context/inject": {},
            "/models/call": {},
        },
        expected_path_count=27,
    )

    for forbidden in [
        "/autonomy/mode4",
        "/autonomy/mode4/start",
        "/autonomy/scoped-work-session",
        "/autonomy/scoped-work-session/start",
        "/autonomy/session/start",
        "/autonomy/actions/execute",
        "/autonomy/tools/execute",
        "/automation/session/start",
        "/automation/mode4/start",
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
        "/workers/start",
        "/scheduler/start",
        "/memory/write",
        "/context/inject",
        "/models/call",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m131_openapi_route_failures(app.openapi().get("paths", {}))


def test_m131_static_safety_detects_mode4_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "mode4_runtime_enabled=True\n"
        "scoped_work_session_start_enabled=True\n"
        "session_active=True\n"
        "autonomous_actions_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "network_access_enabled=True\n"
        "browser_automation_enabled=True\n"
        "browser_form_enabled=True\n"
        "authenticated_browser_enabled=True\n"
        "download_enabled=True\n"
        "upload_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "background_worker_enabled=True\n"
        "scheduler_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "trusted_recurring_workflow_enabled=True\n"
        "mode4_runtime_requested=True\n"
        "scoped_work_session_start_requested=True\n"
        "autonomous_actions_performed=True\n"
        "tool_execution_performed=True\n"
        "background_worker_started=True\n"
        "/autonomy/mode4/start\n"
        "/autonomy/scoped-work-session/start\n"
        "/browser/form\n"
        "/plugins/execute\n"
        "/models/call\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m131_autonomy_mode4_scoped_work_session_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m131_autonomy_mode4_scoped_work_session_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "mode4_runtime_enabled=True",
        "scoped_work_session_start_enabled=True",
        "session_active=True",
        "autonomous_actions_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_access_enabled=True",
        "browser_automation_enabled=True",
        "browser_form_enabled=True",
        "authenticated_browser_enabled=True",
        "download_enabled=True",
        "upload_enabled=True",
        "plugin_execution_enabled=True",
        "connector_runtime_enabled=True",
        "background_worker_enabled=True",
        "scheduler_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "production_authority_granted=True",
        "trusted_recurring_workflow_enabled=True",
        "mode4_runtime_requested=True",
        "scoped_work_session_start_requested=True",
        "autonomous_actions_performed=True",
        "tool_execution_performed=True",
        "background_worker_started=True",
        "/autonomy/mode4/start",
        "/autonomy/scoped-work-session/start",
        "/browser/form",
        "/plugins/execute",
        "/models/call",
    ]:
        assert any(fragment in failure for failure in result.failures)
