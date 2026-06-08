from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m115_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m115_production_audit_retention_contracts" in ids
    assert "m115_production_audit_retention_static_safety" in ids
    assert "m115_production_audit_retention_route_boundary" in ids
    assert "m115_roadmap_currentness" in ids


def test_m115_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m115_production_audit_retention_contracts",
        "m115_production_audit_retention_static_safety",
        "m115_production_audit_retention_route_boundary",
        "m115_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m115_route_boundary_rejects_audit_runtime_and_export_routes() -> None:
    failures = gate_evaluators.m115_openapi_route_failures(
        {
            "/api/manifest": {},
            "/audit/retention": {},
            "/audit/export": {},
            "/audit/logs/raw": {},
            "/logs/export": {},
            "/observability/export": {},
            "/siem/export": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/audit/retention",
        "/audit/export",
        "/audit/logs/raw",
        "/logs/export",
        "/observability/export",
        "/siem/export",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m115_openapi_route_failures(app.openapi().get("paths", {}))


def test_m115_static_safety_detects_audit_runtime_and_export_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "audit_runtime_enabled=True\n"
        "audit_store_enabled=True\n"
        "audit_export_enabled=True\n"
        "raw_log_storage_enabled=True\n"
        "raw_prompt_storage_enabled=True\n"
        "raw_provider_payload_storage_enabled=True\n"
        "external_saas_export_enabled=True\n"
        "network_delivery_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m115_production_audit_retention_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m115_production_audit_retention_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("audit_runtime_enabled=True" in failure for failure in result.failures)
    assert any("audit_store_enabled=True" in failure for failure in result.failures)
    assert any("audit_export_enabled=True" in failure for failure in result.failures)
    assert any("raw_log_storage_enabled=True" in failure for failure in result.failures)
    assert any("raw_prompt_storage_enabled=True" in failure for failure in result.failures)
    assert any(
        "raw_provider_payload_storage_enabled=True" in failure
        for failure in result.failures
    )
    assert any(
        "external_saas_export_enabled=True" in failure for failure in result.failures
    )
    assert any("network_delivery_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
