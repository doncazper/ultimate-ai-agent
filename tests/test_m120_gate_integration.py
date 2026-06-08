from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m120_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m120_production_authority_readiness_review_contracts" in ids
    assert "m120_production_authority_readiness_review_static_safety" in ids
    assert "m120_production_authority_readiness_review_route_boundary" in ids
    assert "m120_roadmap_currentness" in ids


def test_m120_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m120_production_authority_readiness_review_contracts",
        "m120_production_authority_readiness_review_static_safety",
        "m120_production_authority_readiness_review_route_boundary",
        "m120_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m120_route_boundary_rejects_production_authority_routes() -> None:
    failures = gate_evaluators.m120_openapi_route_failures(
        {
            "/api/manifest": {},
            "/production/authority/enable": {},
            "/production/go-live": {},
            "/production/deploy": {},
            "/production/traffic/route": {},
            "/production/rollback/execute": {},
            "/production/readiness/approve": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/network/post": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/production/authority/enable",
        "/production/go-live",
        "/production/deploy",
        "/production/traffic/route",
        "/production/rollback/execute",
        "/production/readiness/approve",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/network/post",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m120_openapi_route_failures(app.openapi().get("paths", {}))


def test_m120_static_safety_detects_production_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "production_authority_enabled=True\n"
        "production_runtime_enabled=True\n"
        "go_live_enabled=True\n"
        "production_deployment_enabled=True\n"
        "traffic_routing_enabled=True\n"
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
        if item.criterion_id
        == "m120_production_authority_readiness_review_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m120_production_authority_readiness_review_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any(
        "production_authority_enabled=True" in failure for failure in result.failures
    )
    assert any("production_runtime_enabled=True" in failure for failure in result.failures)
    assert any("go_live_enabled=True" in failure for failure in result.failures)
    assert any(
        "production_deployment_enabled=True" in failure for failure in result.failures
    )
    assert any("traffic_routing_enabled=True" in failure for failure in result.failures)
    assert any(
        "credential_handling_enabled=True" in failure for failure in result.failures
    )
    assert any("network_access_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
