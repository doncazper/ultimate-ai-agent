from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m140_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m140_higher_autonomy_red_team_freeze_contracts" in ids
    assert "m140_higher_autonomy_red_team_freeze_static_safety" in ids
    assert "m140_higher_autonomy_red_team_freeze_route_boundary" in ids
    assert "m140_roadmap_currentness" in ids


def test_m140_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m140_higher_autonomy_red_team_freeze_contracts",
        "m140_higher_autonomy_red_team_freeze_static_safety",
        "m140_higher_autonomy_red_team_freeze_route_boundary",
        "m140_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m140_route_boundary_rejects_red_team_and_authority_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/autonomy/higher-autonomy-red-team-freeze": {},
        "/autonomy/higher-autonomy-red-team-freeze/start": {},
        "/autonomy/higher-autonomy-red-team-freeze/run": {},
        "/red-team/run": {},
        "/red-team/execute": {},
        "/red-team/harness/run": {},
        "/red-team/harness/execute": {},
        "/adversarial-tests/run": {},
        "/adversarial-tests/execute": {},
        "/autonomy/execute": {},
        "/autonomy/broad/enable": {},
        "/multi-user/enable": {},
        "/tenants/create": {},
        "/workspaces/share": {},
        "/production/authority/enable": {},
        "/tools/execute": {},
        "/browser/click": {},
        "/connectors/write": {},
    }
    failures = gate_evaluators.m140_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/autonomy/higher-autonomy-red-team-freeze",
        "/autonomy/higher-autonomy-red-team-freeze/start",
        "/red-team/run",
        "/red-team/harness/run",
        "/adversarial-tests/run",
        "/autonomy/execute",
        "/multi-user/enable",
        "/tenants/create",
        "/workspaces/share",
        "/production/authority/enable",
        "/tools/execute",
        "/browser/click",
        "/connectors/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m140_openapi_route_failures(app.openapi().get("paths", {}))


def test_m140_static_safety_detects_red_team_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "red_team_runtime_enabled=True\n"
        "red_team_harness_execution_enabled=True\n"
        "adversarial_test_execution_enabled=True\n"
        "autonomous_execution_enabled=True\n"
        "broad_autonomy_enabled=True\n"
        "global_autonomy_switch_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "browser_action_enabled=True\n"
        "connector_action_enabled=True\n"
        "network_access_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "red_team_runtime_started=True\n"
        "red_team_harness_execution_performed=True\n"
        "adversarial_test_execution_performed=True\n"
        "autonomous_execution_performed=True\n"
        "tool_execution_performed=True\n"
        "browser_action_performed=True\n"
        "connector_action_performed=True\n"
        "/autonomy/higher-autonomy-red-team-freeze/start\n"
        "/red-team/run\n"
        "/red-team/harness/run\n"
        "/adversarial-tests/run\n"
        "/autonomy/execute\n"
        "/multi-user/enable\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m140_higher_autonomy_red_team_freeze_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m140_higher_autonomy_red_team_freeze_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "red_team_runtime_enabled=True",
        "red_team_harness_execution_enabled=True",
        "adversarial_test_execution_enabled=True",
        "autonomous_execution_enabled=True",
        "broad_autonomy_enabled=True",
        "global_autonomy_switch_enabled=True",
        "tool_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "backend_route_enabled=True",
        "production_authority_granted=True",
        "red_team_runtime_started=True",
        "red_team_harness_execution_performed=True",
        "adversarial_test_execution_performed=True",
        "autonomous_execution_performed=True",
        "tool_execution_performed=True",
        "/autonomy/higher-autonomy-red-team-freeze/start",
        "/red-team/run",
        "/red-team/harness/run",
        "/adversarial-tests/run",
        "/autonomy/execute",
        "/multi-user/enable",
    ]:
        assert any(fragment in failure for failure in result.failures)
