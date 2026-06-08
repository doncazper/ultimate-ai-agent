from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m121_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m121_email_connector_contract_refresh_contracts" in ids
    assert "m121_email_connector_contract_refresh_static_safety" in ids
    assert "m121_email_connector_contract_refresh_route_boundary" in ids
    assert "m121_roadmap_currentness" in ids


def test_m121_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m121_email_connector_contract_refresh_contracts",
        "m121_email_connector_contract_refresh_static_safety",
        "m121_email_connector_contract_refresh_route_boundary",
        "m121_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m121_route_boundary_rejects_email_connector_runtime_routes() -> None:
    failures = gate_evaluators.m121_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/email/auth": {},
            "/connectors/email/read": {},
            "/connectors/email/search": {},
            "/connectors/email/send": {},
            "/connectors/email/write": {},
            "/connectors/email/delete": {},
            "/connectors/email/attachments/download": {},
            "/email/send": {},
            "/network/post": {},
            "/memory/write": {},
            "/context/inject": {},
        },
        expected_path_count=12,
    )

    for forbidden in [
        "/connectors/email/auth",
        "/connectors/email/read",
        "/connectors/email/search",
        "/connectors/email/send",
        "/connectors/email/write",
        "/connectors/email/delete",
        "/connectors/email/attachments/download",
        "/email/send",
        "/network/post",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m121_openapi_route_failures(app.openapi().get("paths", {}))


def test_m121_static_safety_detects_email_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "email_connector_runtime_enabled=True\n"
        "email_account_auth_enabled=True\n"
        "email_read_enabled=True\n"
        "email_send_enabled=True\n"
        "raw_email_content_enabled=True\n"
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
        if item.criterion_id == "m121_email_connector_contract_refresh_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m121_email_connector_contract_refresh_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "email_connector_runtime_enabled=True",
        "email_account_auth_enabled=True",
        "email_read_enabled=True",
        "email_send_enabled=True",
        "raw_email_content_enabled=True",
        "credential_handling_enabled=True",
        "network_access_enabled=True",
        "backend_route_added=True",
        "control_center_control_added=True",
    ]:
        assert any(fragment in failure for failure in result.failures)
