from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.code import (
    CODING_COCKPIT_BACKEND_ROUTE_REF,
    CODING_COCKPIT_FRONTEND_ROUTE_REF,
    CODING_COCKPIT_REQUIRED_BLOCKED_REFS,
    CODING_COCKPIT_SESSION_REF,
    CodingCockpitSessionReadModel,
    build_coding_cockpit_session_seed,
)


ROOT = Path(__file__).resolve().parents[1]


def test_coding_cockpit_session_seed_is_backend_owned_safe_refs_only() -> None:
    session = build_coding_cockpit_session_seed()
    payload = session.model_dump(mode="json")

    assert session.schema_version == "uaa-coding-cockpit-session.v1"
    assert session.session_ref == CODING_COCKPIT_SESSION_REF
    assert session.backend_route_refs == [CODING_COCKPIT_BACKEND_ROUTE_REF]
    assert session.frontend_route_refs == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert session.backend_owned is True
    assert session.mock_fallback is False
    assert session.local_read_model_only is True
    assert session.safe_refs_only is True
    assert session.raw_content_included is False
    assert session.control_center_grants_authority is False
    assert set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS).issubset(
        session.blocked_authority_refs
    )
    assert session.same_ref_spine == [
        "coding-session:local-readonly-cockpit",
        "coding-task:cockpit-shell-seed",
        "context-pack:coding-cockpit-seed",
        "patch-proposal:coding-blocked-seed",
        "command-proposal:coding-blocked-seed",
        "git-status:coding-readonly-seed",
        "proof-ref:coding-cockpit-seed",
        "preview-ref:coding-blocked-seed",
    ]
    assert "Local coding cockpit" in session.full_strength_goal
    assert "Prompt 01 seed" in session.repo_safe_scope
    assert "scripts/dev/uaa_coding.py inspect-session" in session.cli_inspection_refs
    assert all(not panel.mutation_enabled for panel in _coding_panels(session))
    assert all(not panel.runtime_authority_enabled for panel in _coding_panels(session))
    assert all(item.proof_refs for panel in _coding_panels(session) for item in panel.items)
    assert "/Users/" not in json.dumps(payload)


@pytest.mark.parametrize(
    "flag_name",
    [
        "file_write_enabled",
        "shell_subprocess_execution_enabled",
        "git_mutation_enabled",
        "provider_model_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ],
)
def test_coding_cockpit_session_rejects_runtime_authority_flags(
    flag_name: str,
) -> None:
    payload = build_coding_cockpit_session_seed().model_dump(mode="json")
    payload[flag_name] = True

    with pytest.raises(ValidationError, match=flag_name):
        CodingCockpitSessionReadModel(**payload)


def test_coding_cockpit_session_rejects_panel_mutation_authority() -> None:
    payload = build_coding_cockpit_session_seed().model_dump(mode="json")
    payload["terminal_preview"]["runtime_authority_enabled"] = True

    with pytest.raises(ValidationError, match="runtime authority"):
        CodingCockpitSessionReadModel(**payload)


def test_control_center_coding_session_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/coding/session")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_coding_session"
    assert body["service"] == "ControlCenterCodingAPI"
    assert body["trace_id"] == CODING_COCKPIT_SESSION_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:bounded-summaries-only",
        "redaction-ref:raw-content-omitted",
        "redaction-ref:raw-paths-omitted",
    ]

    data = body["data"]
    assert data["backend_owned"] is True
    assert data["mock_fallback"] is False
    assert data["file_write_enabled"] is False
    assert data["shell_subprocess_execution_enabled"] is False
    assert data["git_mutation_enabled"] is False
    assert data["provider_model_call_enabled"] is False
    assert data["browser_automation_enabled"] is False
    assert data["connector_write_enabled"] is False
    assert data["background_autonomy_enabled"] is False
    assert data["production_authority_enabled"] is False
    assert set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS).issubset(
        data["blocked_authority_refs"]
    )


def test_coding_cockpit_route_and_capabilities_are_manifested_as_local_read_model() -> None:
    manifest = build_api_manifest(app)
    routes = {(route.method, route.path): route for route in manifest.routes}
    route = routes[("GET", "/control-center/coding/session")]

    assert route.operation_id == "get_control_center_coding_session"
    assert route.tags == ["control-center"]
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.route_classification == "local_sensitive"
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_required is False
    assert "control_center_coding_cockpit_session_read_model" in (
        manifest.capabilities_declared
    )
    for capability in [
        "control_center_coding_cockpit_file_writes",
        "control_center_coding_cockpit_shell_subprocess_execution",
        "control_center_coding_cockpit_git_mutation",
        "control_center_coding_cockpit_provider_model_calls",
        "control_center_coding_cockpit_browser_automation",
        "control_center_coding_cockpit_connector_writes",
        "control_center_coding_cockpit_background_autonomy",
        "control_center_coding_cockpit_production_authority",
    ]:
        assert capability in manifest.capabilities_blocked


def test_coding_cockpit_cli_inspection_prints_same_safe_session() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/dev/uaa_coding.py"), "inspect-session"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["session_ref"] == CODING_COCKPIT_SESSION_REF
    assert data["backend_owned"] is True
    assert data["mock_fallback"] is False
    assert data["frontend_route_refs"] == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert "/Users/" not in result.stdout
    assert "credential" not in result.stdout.lower()


def _coding_panels(session: CodingCockpitSessionReadModel):
    return [
        session.workspace_context,
        session.task_thread,
        session.task_timeline,
        session.diff_preview,
        session.proof_preview,
        session.terminal_preview,
        session.git_preview,
        session.test_output_preview,
        session.live_preview,
        session.chat_thread,
    ]
