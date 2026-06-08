from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m117_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m117_remote_agent_coordination_contracts" in ids
    assert "m117_remote_agent_coordination_static_safety" in ids
    assert "m117_remote_agent_coordination_route_boundary" in ids
    assert "m117_roadmap_currentness" in ids


def test_m117_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m117_remote_agent_coordination_contracts",
        "m117_remote_agent_coordination_static_safety",
        "m117_remote_agent_coordination_route_boundary",
        "m117_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m117_route_boundary_rejects_remote_agent_runtime_routes() -> None:
    failures = gate_evaluators.m117_openapi_route_failures(
        {
            "/api/manifest": {},
            "/remote-agents/coordinate": {},
            "/remote-agents/dispatch": {},
            "/remote-agents/connect": {},
            "/remote-agents/spawn": {},
            "/remote/execute": {},
            "/agent-mesh/dispatch": {},
            "/agents/remote/handoff": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/network/post": {},
        },
        expected_path_count=12,
    )

    for forbidden in [
        "/remote-agents/coordinate",
        "/remote-agents/dispatch",
        "/remote-agents/connect",
        "/remote-agents/spawn",
        "/remote/execute",
        "/agent-mesh/dispatch",
        "/agents/remote/handoff",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/network/post",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m117_openapi_route_failures(app.openapi().get("paths", {}))


def test_m117_static_safety_detects_remote_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "remote_agent_runtime_enabled=True\n"
        "remote_dispatch_enabled=True\n"
        "remote_execution_enabled=True\n"
        "live_connection_enabled=True\n"
        "network_access_enabled=True\n"
        "agent_spawn_enabled=True\n"
        "background_worker_enabled=True\n"
        "credential_handling_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m117_remote_agent_coordination_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m117_remote_agent_coordination_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any(
        "remote_agent_runtime_enabled=True" in failure for failure in result.failures
    )
    assert any("remote_dispatch_enabled=True" in failure for failure in result.failures)
    assert any("remote_execution_enabled=True" in failure for failure in result.failures)
    assert any("live_connection_enabled=True" in failure for failure in result.failures)
    assert any("network_access_enabled=True" in failure for failure in result.failures)
    assert any("agent_spawn_enabled=True" in failure for failure in result.failures)
    assert any("background_worker_enabled=True" in failure for failure in result.failures)
    assert any(
        "credential_handling_enabled=True" in failure for failure in result.failures
    )
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
