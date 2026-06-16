from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m129_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m129_connector_audit_revocation_hardening_contracts" in ids
    assert "m129_connector_audit_revocation_hardening_static_safety" in ids
    assert "m129_connector_audit_revocation_hardening_route_boundary" in ids
    assert "m129_roadmap_currentness" in ids


def test_m129_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m129_connector_audit_revocation_hardening_contracts",
        "m129_connector_audit_revocation_hardening_static_safety",
        "m129_connector_audit_revocation_hardening_route_boundary",
        "m129_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m129_route_boundary_rejects_connector_audit_revocation_routes() -> None:
    failures = gate_evaluators.m129_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/audit": {},
            "/connectors/audit/export": {},
            "/connectors/revocation": {},
            "/connectors/revocation/execute": {},
            "/connectors/kill-switch": {},
            "/connectors/kill-switch/execute": {},
            "/connectors/safety/freeze": {},
            "/connectors/freeze": {},
            "/connectors/export": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/connectors/audit",
        "/connectors/audit/export",
        "/connectors/revocation",
        "/connectors/revocation/execute",
        "/connectors/kill-switch",
        "/connectors/kill-switch/execute",
        "/connectors/safety/freeze",
        "/connectors/freeze",
        "/connectors/export",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m129_openapi_route_failures(app.openapi().get("paths", {}))


def test_m129_static_safety_detects_audit_revocation_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "revocation_execution_enabled=True\n"
        "kill_switch_execution_enabled=True\n"
        "audit_export_enabled=True\n"
        "raw_audit_payload_stored=True\n"
        "audit_exported=True\n"
        "revocation_executed=True\n"
        "kill_switch_executed=True\n"
        "connector_approval_revoked=True\n"
        "connector_session_stopped=True\n"
        "backend_route_added=True\n"
        "production_authority_granted=True\n"
        "/connectors/revocation/execute\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m129_connector_audit_revocation_hardening_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m129_connector_audit_revocation_hardening_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "revocation_execution_enabled=True",
        "kill_switch_execution_enabled=True",
        "audit_export_enabled=True",
        "raw_audit_payload_stored=True",
        "audit_exported=True",
        "revocation_executed=True",
        "kill_switch_executed=True",
        "connector_approval_revoked=True",
        "connector_session_stopped=True",
        "backend_route_added=True",
        "production_authority_granted=True",
        "/connectors/revocation/execute",
    ]:
        assert any(fragment in failure for failure in result.failures)
