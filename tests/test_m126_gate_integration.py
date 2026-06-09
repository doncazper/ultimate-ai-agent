from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m126_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m126_connector_approval_capture_contracts" in ids
    assert "m126_connector_approval_capture_static_safety" in ids
    assert "m126_connector_approval_capture_route_boundary" in ids
    assert "m126_roadmap_currentness" in ids


def test_m126_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m126_connector_approval_capture_contracts",
        "m126_connector_approval_capture_static_safety",
        "m126_connector_approval_capture_route_boundary",
        "m126_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m126_route_boundary_rejects_connector_approval_routes() -> None:
    failures = gate_evaluators.m126_openapi_route_failures(
        {
            "/api/manifest": {},
            "/connectors/approvals/capture": {},
            "/connectors/approve": {},
            "/connectors/read": {},
            "/connectors/runtime/read": {},
            "/connectors/email/read": {},
            "/connectors/calendar/read": {},
            "/connectors/contacts/read": {},
            "/connectors/messages/read": {},
            "/connectors/messages/send": {},
            "/connectors/export": {},
            "/connectors/attachments/download": {},
            "/network/post": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=16,
    )

    for forbidden in [
        "/connectors/approvals/capture",
        "/connectors/approve",
        "/connectors/read",
        "/connectors/runtime/read",
        "/connectors/email/read",
        "/connectors/calendar/read",
        "/connectors/contacts/read",
        "/connectors/messages/read",
        "/connectors/messages/send",
        "/connectors/export",
        "/connectors/attachments/download",
        "/network/post",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m126_openapi_route_failures(app.openapi().get("paths", {}))


def test_m126_static_safety_detects_approval_capture_authority_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/connectors"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "live_connector_runtime_enabled=True\n"
        "account_auth_enabled=True\n"
        "network_access_enabled=True\n"
        "credential_handling_enabled=True\n"
        "raw_connector_content_enabled=True\n"
        "full_content_read_enabled=True\n"
        "connector_write_enabled=True\n"
        "connector_send_enabled=True\n"
        "connector_delete_enabled=True\n"
        "connector_export_enabled=True\n"
        "connector_bulk_export_enabled=True\n"
        "attachment_download_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "execution_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m126_connector_approval_capture_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m126_connector_approval_capture_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "live_connector_runtime_enabled=True",
        "account_auth_enabled=True",
        "network_access_enabled=True",
        "credential_handling_enabled=True",
        "raw_connector_content_enabled=True",
        "full_content_read_enabled=True",
        "connector_write_enabled=True",
        "connector_send_enabled=True",
        "connector_delete_enabled=True",
        "connector_export_enabled=True",
        "connector_bulk_export_enabled=True",
        "attachment_download_enabled=True",
        "backend_route_added=True",
        "control_center_control_added=True",
    ]:
        assert any(fragment in failure for failure in result.failures)
