from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m119_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m119_production_red_team_harness_contracts" in ids
    assert "m119_production_red_team_harness_static_safety" in ids
    assert "m119_production_red_team_harness_route_boundary" in ids
    assert "m119_roadmap_currentness" in ids


def test_m119_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m119_production_red_team_harness_contracts",
        "m119_production_red_team_harness_static_safety",
        "m119_production_red_team_harness_route_boundary",
        "m119_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m119_route_boundary_rejects_red_team_runtime_routes() -> None:
    failures = gate_evaluators.m119_openapi_route_failures(
        {
            "/api/manifest": {},
            "/red-team/run": {},
            "/red-team/execute": {},
            "/red-team/attack": {},
            "/red-team/probe": {},
            "/red-team/exploit": {},
            "/red-team/report/export": {},
            "/production/red-team/run": {},
            "/security/scan/run": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/network/post": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/red-team/run",
        "/red-team/execute",
        "/red-team/attack",
        "/red-team/probe",
        "/red-team/exploit",
        "/red-team/report/export",
        "/production/red-team/run",
        "/security/scan/run",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/network/post",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m119_openapi_route_failures(app.openapi().get("paths", {}))


def test_m119_static_safety_detects_red_team_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "red_team_execution_enabled=True\n"
        "attack_automation_enabled=True\n"
        "external_probe_enabled=True\n"
        "exploit_generation_enabled=True\n"
        "security_scan_runtime_enabled=True\n"
        "production_authority_enabled=True\n"
        "credential_handling_enabled=True\n"
        "network_access_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m119_production_red_team_harness_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m119_production_red_team_harness_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("red_team_execution_enabled=True" in failure for failure in result.failures)
    assert any("attack_automation_enabled=True" in failure for failure in result.failures)
    assert any("external_probe_enabled=True" in failure for failure in result.failures)
    assert any("exploit_generation_enabled=True" in failure for failure in result.failures)
    assert any(
        "security_scan_runtime_enabled=True" in failure for failure in result.failures
    )
    assert any(
        "production_authority_enabled=True" in failure for failure in result.failures
    )
    assert any(
        "credential_handling_enabled=True" in failure for failure in result.failures
    )
    assert any("network_access_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
