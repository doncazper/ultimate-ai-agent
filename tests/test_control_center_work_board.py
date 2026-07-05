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
from ultimate_ai_agent.core.control_center import (
    WORK_BOARD_BACKEND_ROUTE_REF,
    WORK_BOARD_BOARD_REF,
    WORK_BOARD_CLI_REF,
    WORK_BOARD_CONTRACT_REF,
    WORK_BOARD_FRONTEND_ROUTE_REF,
    WORK_BOARD_REQUIRED_BLOCKED_REFS,
    WorkBoardReadModel,
    build_work_board_read_model,
)


ROOT = Path(__file__).resolve().parents[1]


def test_work_board_read_model_is_backend_owned_safe_refs_only() -> None:
    board = build_work_board_read_model()
    payload = board.model_dump(mode="json")

    assert board.schema_version == "uaa-work-board-read-model.v1"
    assert board.contract_ref == WORK_BOARD_CONTRACT_REF
    assert board.board_ref == WORK_BOARD_BOARD_REF
    assert board.backend_route_refs == [WORK_BOARD_BACKEND_ROUTE_REF]
    assert board.frontend_route_refs == [WORK_BOARD_FRONTEND_ROUTE_REF]
    assert board.cli_inspection_refs == [WORK_BOARD_CLI_REF]
    assert board.backend_owned is True
    assert board.read_only is True
    assert board.safe_refs_only is True
    assert board.non_authoritative_mock_fallback is False
    assert board.raw_paths_included is False
    assert board.raw_content_included is False
    assert board.board_mutation_enabled is False
    assert board.durable_drag_drop_enabled is False
    assert board.issue_tracker_write_enabled is False
    assert board.connector_write_enabled is False
    assert board.shell_subprocess_execution_enabled is False
    assert board.browser_automation_enabled is False
    assert board.background_autonomy_enabled is False
    assert board.production_authority_enabled is False
    assert board.drag_drop_posture.local_preview_enabled is True
    assert board.drag_drop_posture.keyboard_reorder_preview_enabled is True
    assert board.drag_drop_posture.durable_reorder_enabled is False
    assert board.columns
    assert board.cards
    assert set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
        board.blocked_authority_refs
    )
    assert {column.column_ref for column in board.columns} >= {
        "work-board-column:triage",
        "work-board-column:doing",
        "work-board-column:blocked",
        "work-board-column:done",
    }
    assert "work-board-card:work-board-kanban-shell" in {
        card.card_ref for card in board.cards
    }
    assert "/Users/" not in json.dumps(payload)
    assert "credential" not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    "flag_name",
    [
        "board_mutation_enabled",
        "durable_drag_drop_enabled",
        "issue_tracker_write_enabled",
        "connector_write_enabled",
        "shell_subprocess_execution_enabled",
        "browser_automation_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ],
)
def test_work_board_rejects_runtime_and_mutation_authority(flag_name: str) -> None:
    payload = build_work_board_read_model().model_dump(mode="json")
    payload[flag_name] = True

    with pytest.raises(ValidationError, match=flag_name):
        WorkBoardReadModel(**payload)


def test_work_board_rejects_raw_paths_and_card_mutation() -> None:
    payload = build_work_board_read_model().model_dump(mode="json")
    payload["raw_paths_included"] = True
    with pytest.raises(ValidationError, match="raw_paths_included"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["cards"][0]["mutation_enabled"] = True
    with pytest.raises(ValidationError, match="mutation"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["drag_drop_posture"]["durable_reorder_enabled"] = True
    with pytest.raises(ValidationError, match="durable_reorder_enabled"):
        WorkBoardReadModel(**payload)


def test_control_center_work_board_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/work-board")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_work_board"
    assert body["service"] == "ControlCenterWorkBoardAPI"
    assert body["trace_id"] == WORK_BOARD_BOARD_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:raw-paths-omitted",
        "redaction-ref:raw-content-omitted",
    ]
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["read_only"] is True
    assert data["safe_refs_only"] is True
    assert data["board_mutation_enabled"] is False
    assert data["durable_drag_drop_enabled"] is False
    assert data["drag_drop_posture"]["local_preview_enabled"] is True
    assert data["drag_drop_posture"]["durable_reorder_enabled"] is False
    assert set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
        data["blocked_authority_refs"]
    )


def test_work_board_route_is_local_sensitive_and_side_effect_bounded() -> None:
    manifest = build_api_manifest(app)
    route = next(
        item
        for item in manifest.routes
        if item.path == "/control-center/work-board" and item.method == "GET"
    )

    assert route.tags == ["control-center"]
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.protected_route is True
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_posture == "not_required_for_route_classification"
    assert route.rate_limit_posture == "not_targeted_for_route"


def test_work_board_cli_inspection_prints_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_work_board.py"),
            "inspect-board",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["board_ref"] == WORK_BOARD_BOARD_REF
    assert payload["backend_owned"] is True
    assert payload["board_mutation_enabled"] is False
    assert payload["durable_drag_drop_enabled"] is False
    assert "/Users/" not in result.stdout
