from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m111_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m111_production_threat_model_contracts" in ids
    assert "m111_production_threat_model_static_safety" in ids
    assert "m111_production_threat_model_route_boundary" in ids
    assert "m111_roadmap_currentness" in ids


def test_m111_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m111_production_threat_model_contracts",
        "m111_production_threat_model_static_safety",
        "m111_production_threat_model_route_boundary",
        "m111_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m111_route_boundary_rejects_production_runtime_routes() -> None:
    failures = gate_evaluators.m111_openapi_route_failures(
        {
            "/api/manifest": {},
            "/production/threat-model": {},
            "/production/threat-model/run": {},
            "/production/threat-model/approve": {},
            "/production/runtime": {},
            "/production/authority": {},
            "/production/deploy": {},
            "/credentials/read": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/production/threat-model",
        "/production/threat-model/run",
        "/production/threat-model/approve",
        "/production/runtime",
        "/production/authority",
        "/production/deploy",
        "/credentials/read",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m111_openapi_route_failures(app.openapi().get("paths", {}))


def test_m111_static_safety_detects_production_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "production_authority_enabled=True\n"
        "production_runtime_enabled=True\n"
        "deployment_enabled=True\n"
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
        if item.criterion_id == "m111_production_threat_model_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m111_production_threat_model_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("production_authority_enabled=True" in failure for failure in result.failures)
    assert any("production_runtime_enabled=True" in failure for failure in result.failures)
    assert any("deployment_enabled=True" in failure for failure in result.failures)
    assert any("credential_handling_enabled=True" in failure for failure in result.failures)
    assert any("network_access_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
