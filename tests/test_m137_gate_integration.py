from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m137_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m137_browser_connector_combined_workflow_contracts" in ids
    assert "m137_browser_connector_combined_workflow_static_safety" in ids
    assert "m137_browser_connector_combined_workflow_route_boundary" in ids
    assert "m137_roadmap_currentness" in ids


def test_m137_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m137_browser_connector_combined_workflow_contracts",
        "m137_browser_connector_combined_workflow_static_safety",
        "m137_browser_connector_combined_workflow_route_boundary",
        "m137_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m137_route_boundary_rejects_browser_connector_combined_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/autonomy/browser-connector-combined-workflow": {},
        "/autonomy/browser-connector-combined-workflow/start": {},
        "/autonomy/browser-connector-combined-workflow/run": {},
        "/combined-workflows/run": {},
        "/combined-workflows/execute": {},
        "/browser/actions/run": {},
        "/browser/actions/execute": {},
        "/browser/navigate": {},
        "/browser/click": {},
        "/browser/form": {},
        "/browser/download": {},
        "/browser/upload": {},
        "/browser/authenticated": {},
        "/connectors/runtime": {},
        "/connectors/read": {},
        "/connectors/write": {},
        "/connectors/send": {},
        "/connectors/delete": {},
        "/connectors/auth": {},
        "/accounts/auth": {},
        "/dependency-execution/execute": {},
        "/dependency-resolver/start": {},
        "/tools/execute": {},
        "/network/post": {},
        "/plugins/execute": {},
    }
    failures = gate_evaluators.m137_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/autonomy/browser-connector-combined-workflow",
        "/combined-workflows/run",
        "/browser/actions/run",
        "/browser/navigate",
        "/browser/click",
        "/browser/form",
        "/connectors/runtime",
        "/connectors/write",
        "/connectors/auth",
        "/accounts/auth",
        "/dependency-execution/execute",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m137_openapi_route_failures(app.openapi().get("paths", {}))


def test_m137_static_safety_detects_browser_connector_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "combined_workflow_runtime_enabled=True\n"
        "browser_action_enabled=True\n"
        "browser_navigation_enabled=True\n"
        "browser_click_enabled=True\n"
        "browser_form_enabled=True\n"
        "browser_download_enabled=True\n"
        "browser_upload_enabled=True\n"
        "authenticated_browser_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "connector_read_runtime_enabled=True\n"
        "connector_write_enabled=True\n"
        "connector_send_enabled=True\n"
        "connector_delete_enabled=True\n"
        "account_auth_enabled=True\n"
        "dependency_execution_enabled=True\n"
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
        "combined_workflow_runtime_authorized=True\n"
        "browser_action_authorized=True\n"
        "browser_action_performed=True\n"
        "browser_click_performed=True\n"
        "browser_form_performed=True\n"
        "connector_runtime_authorized=True\n"
        "connector_action_authorized=True\n"
        "connector_write_performed=True\n"
        "account_auth_performed=True\n"
        "dependency_execution_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/browser-connector-combined-workflow/start\n"
        "/combined-workflows/run\n"
        "/browser/actions/run\n"
        "/browser/navigate\n"
        "/browser/click\n"
        "/browser/form\n"
        "/connectors/runtime\n"
        "/connectors/write\n"
        "/connectors/auth\n"
        "/accounts/auth\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m137_browser_connector_combined_workflow_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m137_browser_connector_combined_workflow_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "combined_workflow_runtime_enabled=True",
        "browser_action_enabled=True",
        "browser_click_enabled=True",
        "browser_form_enabled=True",
        "connector_runtime_enabled=True",
        "connector_write_enabled=True",
        "account_auth_enabled=True",
        "dependency_execution_enabled=True",
        "tool_execution_enabled=True",
        "backend_route_enabled=True",
        "production_authority_granted=True",
        "combined_workflow_runtime_authorized=True",
        "browser_action_authorized=True",
        "browser_action_performed=True",
        "connector_action_authorized=True",
        "connector_write_performed=True",
        "/autonomy/browser-connector-combined-workflow/start",
        "/combined-workflows/run",
        "/browser/actions/run",
        "/browser/navigate",
        "/browser/click",
        "/connectors/runtime",
        "/connectors/write",
        "/accounts/auth",
    ]:
        assert any(fragment in failure for failure in result.failures)
