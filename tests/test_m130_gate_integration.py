from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m130_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m130_connector_safety_freeze_contracts" in ids
    assert "m130_connector_safety_freeze_static_safety" in ids
    assert "m130_connector_safety_freeze_route_boundary" in ids
    assert "m130_roadmap_currentness" in ids


def test_m130_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m130_connector_safety_freeze_contracts",
        "m130_connector_safety_freeze_static_safety",
        "m130_connector_safety_freeze_route_boundary",
        "m130_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m130_route_boundary_rejects_connector_freeze_and_m131_routes() -> None:
    failures = gate_evaluators.m130_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/safety/freeze": {},
            "/connectors/freeze": {},
            "/connectors/freeze/accept": {},
            "/connectors/runtime": {},
            "/connectors/auth": {},
            "/connectors/export": {},
            "/connectors/audit/export": {},
            "/connectors/revocation/execute": {},
            "/connectors/kill-switch/execute": {},
            "/autonomy/mode4": {},
            "/autonomy/scoped-work-session": {},
            "/automation/session/start": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=16,
    )

    for forbidden in [
        "/connectors/safety/freeze",
        "/connectors/freeze",
        "/connectors/freeze/accept",
        "/connectors/runtime",
        "/connectors/auth",
        "/connectors/export",
        "/connectors/audit/export",
        "/connectors/revocation/execute",
        "/connectors/kill-switch/execute",
        "/autonomy/mode4",
        "/autonomy/scoped-work-session",
        "/automation/session/start",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m130_openapi_route_failures(app.openapi().get("paths", {}))


def test_m130_static_safety_detects_freeze_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "live_connector_runtime_enabled=True\n"
        "connector_export_performed=True\n"
        "audit_export_performed=True\n"
        "revocation_executed=True\n"
        "kill_switch_executed=True\n"
        "connector_approval_revoked=True\n"
        "connector_session_stopped=True\n"
        "background_worker_started=True\n"
        "external_service_called=True\n"
        "backend_route_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "/connectors/safety/freeze\n"
        "/autonomy/scoped-work-session\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m130_connector_safety_freeze_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m130_connector_safety_freeze_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "live_connector_runtime_enabled=True",
        "connector_export_performed=True",
        "audit_export_performed=True",
        "revocation_executed=True",
        "kill_switch_executed=True",
        "connector_approval_revoked=True",
        "connector_session_stopped=True",
        "background_worker_started=True",
        "external_service_called=True",
        "backend_route_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "/connectors/safety/freeze",
        "/autonomy/scoped-work-session",
    ]:
        assert any(fragment in failure for failure in result.failures)
