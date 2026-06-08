from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m122_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m122_calendar_connector_contract_refresh_contracts" in ids
    assert "m122_calendar_connector_contract_refresh_static_safety" in ids
    assert "m122_calendar_connector_contract_refresh_route_boundary" in ids
    assert "m122_roadmap_currentness" in ids


def test_m122_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m122_calendar_connector_contract_refresh_contracts",
        "m122_calendar_connector_contract_refresh_static_safety",
        "m122_calendar_connector_contract_refresh_route_boundary",
        "m122_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m122_route_boundary_rejects_calendar_connector_runtime_routes() -> None:
    failures = gate_evaluators.m122_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/calendar/auth": {},
            "/connectors/calendar/read": {},
            "/connectors/calendar/search": {},
            "/connectors/calendar/events/create": {},
            "/connectors/calendar/events/update": {},
            "/connectors/calendar/events/delete": {},
            "/connectors/calendar/invites/send": {},
            "/connectors/calendar/attachments/download": {},
            "/calendar/events/create": {},
            "/network/post": {},
            "/memory/write": {},
            "/context/inject": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/connectors/calendar/auth",
        "/connectors/calendar/read",
        "/connectors/calendar/search",
        "/connectors/calendar/events/create",
        "/connectors/calendar/events/update",
        "/connectors/calendar/events/delete",
        "/connectors/calendar/invites/send",
        "/connectors/calendar/attachments/download",
        "/calendar/events/create",
        "/network/post",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m122_openapi_route_failures(app.openapi().get("paths", {}))


def test_m122_static_safety_detects_calendar_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "calendar_connector_runtime_enabled=True\n"
        "calendar_account_auth_enabled=True\n"
        "calendar_read_enabled=True\n"
        "calendar_event_create_enabled=True\n"
        "raw_calendar_content_enabled=True\n"
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
        if item.criterion_id == "m122_calendar_connector_contract_refresh_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m122_calendar_connector_contract_refresh_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "calendar_connector_runtime_enabled=True",
        "calendar_account_auth_enabled=True",
        "calendar_read_enabled=True",
        "calendar_event_create_enabled=True",
        "raw_calendar_content_enabled=True",
        "credential_handling_enabled=True",
        "network_access_enabled=True",
        "backend_route_added=True",
        "control_center_control_added=True",
    ]:
        assert any(fragment in failure for failure in result.failures)
