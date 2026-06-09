from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m124_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m124_messages_connector_contract_review_contracts" in ids
    assert "m124_messages_connector_contract_review_static_safety" in ids
    assert "m124_messages_connector_contract_review_route_boundary" in ids
    assert "m124_roadmap_currentness" in ids


def test_m124_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m124_messages_connector_contract_review_contracts",
        "m124_messages_connector_contract_review_static_safety",
        "m124_messages_connector_contract_review_route_boundary",
        "m124_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m124_route_boundary_rejects_messages_connector_runtime_routes() -> None:
    failures = gate_evaluators.m124_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/messages/auth": {},
            "/connectors/messages/read": {},
            "/connectors/messages/search": {},
            "/connectors/messages/lookup": {},
            "/connectors/messages/send": {},
            "/connectors/messages/thread": {},
            "/connectors/messages/attachments/download": {},
            "/connectors/messages/create": {},
            "/connectors/messages/update": {},
            "/connectors/messages/delete": {},
            "/connectors/messages/export": {},
            "/connectors/messages/bulk-export": {},
            "/messages/export": {},
            "/network/post": {},
            "/memory/write": {},
            "/context/inject": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
            "/connectors/messages/auth",
            "/connectors/messages/read",
            "/connectors/messages/search",
            "/connectors/messages/lookup",
            "/connectors/messages/send",
            "/connectors/messages/thread",
            "/connectors/messages/attachments/download",
            "/connectors/messages/create",
            "/connectors/messages/update",
            "/connectors/messages/delete",
            "/connectors/messages/export",
            "/connectors/messages/bulk-export",
            "/messages/export",
        "/network/post",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m124_openapi_route_failures(app.openapi().get("paths", {}))


def test_m124_static_safety_detects_messages_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "messages_connector_runtime_enabled=True\n"
        "messages_account_auth_enabled=True\n"
        "messages_read_enabled=True\n"
        "messages_lookup_enabled=True\n"
        "messages_send_enabled=True\n"
        "message_thread_access_enabled=True\n"
        "messages_create_enabled=True\n"
        "messages_export_enabled=True\n"
        "messages_bulk_export_enabled=True\n"
        "attachment_download_enabled=True\n"
        "raw_messages_content_enabled=True\n"
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
        if item.criterion_id == "m124_messages_connector_contract_review_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m124_messages_connector_contract_review_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "messages_connector_runtime_enabled=True",
        "messages_account_auth_enabled=True",
        "messages_read_enabled=True",
        "messages_lookup_enabled=True",
        "messages_send_enabled=True",
        "message_thread_access_enabled=True",
        "messages_create_enabled=True",
        "messages_export_enabled=True",
        "messages_bulk_export_enabled=True",
        "attachment_download_enabled=True",
        "raw_messages_content_enabled=True",
        "credential_handling_enabled=True",
        "network_access_enabled=True",
        "backend_route_added=True",
        "control_center_control_added=True",
    ]:
        assert any(fragment in failure for failure in result.failures)
