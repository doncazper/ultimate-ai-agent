from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m118_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m118_deployment_mode_matrix_contracts" in ids
    assert "m118_deployment_mode_matrix_static_safety" in ids
    assert "m118_deployment_mode_matrix_route_boundary" in ids
    assert "m118_roadmap_currentness" in ids


def test_m118_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m118_deployment_mode_matrix_contracts",
        "m118_deployment_mode_matrix_static_safety",
        "m118_deployment_mode_matrix_route_boundary",
        "m118_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m118_route_boundary_rejects_deployment_runtime_routes() -> None:
    failures = gate_evaluators.m118_openapi_route_failures(
        {
            "/api/manifest": {},
            "/deployment/modes/apply": {},
            "/deployment/run": {},
            "/deployment/release": {},
            "/deployment/promote": {},
            "/deployment/rollback": {},
            "/production/deploy": {},
            "/ci-cd/run": {},
            "/infra/provision": {},
            "/remote-agents/dispatch": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/network/post": {},
        },
        expected_path_count=14,
    )

    for forbidden in [
        "/deployment/modes/apply",
        "/deployment/run",
        "/deployment/release",
        "/deployment/promote",
        "/deployment/rollback",
        "/production/deploy",
        "/ci-cd/run",
        "/infra/provision",
        "/remote-agents/dispatch",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/network/post",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m118_openapi_route_failures(app.openapi().get("paths", {}))


def test_m118_static_safety_detects_deployment_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "deployment_runtime_enabled=True\n"
        "deployment_execution_enabled=True\n"
        "release_automation_enabled=True\n"
        "external_distribution_enabled=True\n"
        "infrastructure_provisioning_enabled=True\n"
        "ci_cd_execution_enabled=True\n"
        "signing_or_notarization_enabled=True\n"
        "production_authority_enabled=True\n"
        "credential_handling_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m118_deployment_mode_matrix_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m118_deployment_mode_matrix_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("deployment_runtime_enabled=True" in failure for failure in result.failures)
    assert any(
        "deployment_execution_enabled=True" in failure for failure in result.failures
    )
    assert any("release_automation_enabled=True" in failure for failure in result.failures)
    assert any(
        "external_distribution_enabled=True" in failure for failure in result.failures
    )
    assert any(
        "infrastructure_provisioning_enabled=True" in failure
        for failure in result.failures
    )
    assert any("ci_cd_execution_enabled=True" in failure for failure in result.failures)
    assert any(
        "signing_or_notarization_enabled=True" in failure
        for failure in result.failures
    )
    assert any(
        "production_authority_enabled=True" in failure for failure in result.failures
    )
    assert any(
        "credential_handling_enabled=True" in failure for failure in result.failures
    )
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
