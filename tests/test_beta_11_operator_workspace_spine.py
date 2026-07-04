from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.operator_workspace_spine import (
    OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS,
    OPERATOR_WORKSPACE_SPINE_CLI_REF,
    OPERATOR_WORKSPACE_SPINE_CONTRACT_REF,
    OPERATOR_WORKSPACE_SPINE_PROOF_REF,
    OPERATOR_WORKSPACE_SPINE_ROUTE_REF,
    OperatorWorkspaceSpineReadModel,
    build_operator_workspace_spine_read_model,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_no_operator_workspace_authority(payload: dict) -> None:
    text = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "file_write_enabled\": true",
        "git_mutation_enabled\": true",
        "shell_subprocess_execution_enabled\": true",
        "browser_automation_enabled\": true",
        "dev_server_start_enabled\": true",
        "provider_model_call_enabled\": true",
        "connector_write_enabled\": true",
        "background_autonomy_enabled\": true",
        "production_authority_enabled\": true",
        "raw_path_persistence_enabled\": true",
        "raw_log_persistence_enabled\": true",
        "/Users/",
        "/home/",
        "-----BEGIN",
    ):
        assert forbidden not in text


def test_operator_workspace_spine_builder_is_backend_owned_safe_refs_only() -> None:
    read_model = build_operator_workspace_spine_read_model()
    payload = read_model.model_dump(mode="json")

    assert read_model.schema_version == "operator_workspace_spine_read_model.v1"
    assert read_model.contract_ref == OPERATOR_WORKSPACE_SPINE_CONTRACT_REF
    assert read_model.source == "python_core_operator_workspace_spine_read_model"
    assert read_model.backend_owned is True
    assert read_model.safe_refs_only is True
    assert read_model.read_only is True
    assert read_model.control_center_presentation_only is True
    assert read_model.route_ref == OPERATOR_WORKSPACE_SPINE_ROUTE_REF
    assert read_model.cli_ref == OPERATOR_WORKSPACE_SPINE_CLI_REF
    assert read_model.proof_refs == [OPERATOR_WORKSPACE_SPINE_PROOF_REF]
    assert [lane.lane_kind for lane in read_model.lanes] == [
        "workspace_status",
        "git_posture",
        "preview_status",
        "run_logs",
        "coworker_handoff",
    ]
    assert set(OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    for lane in read_model.lanes:
        assert lane.safe_refs_only is True
        assert lane.read_only is True
        assert lane.raw_content_included is False
        assert lane.runtime_execution_enabled is False
        assert lane.mutation_enabled is False
        assert OPERATOR_WORKSPACE_SPINE_PROOF_REF in lane.proof_refs
        assert lane.blocked_authority_refs
    _assert_no_operator_workspace_authority(payload)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    [
        ("file_write_enabled", True),
        ("git_mutation_enabled", True),
        ("shell_subprocess_execution_enabled", True),
        ("browser_automation_enabled", True),
        ("dev_server_start_enabled", True),
        ("provider_model_call_enabled", True),
        ("connector_write_enabled", True),
        ("background_autonomy_enabled", True),
        ("production_authority_enabled", True),
        ("raw_path_persistence_enabled", True),
        ("raw_log_persistence_enabled", True),
    ],
)
def test_operator_workspace_spine_rejects_authority_flags(
    field_name: str,
    unsafe_value: bool,
) -> None:
    payload = build_operator_workspace_spine_read_model().model_dump(mode="json")
    payload[field_name] = unsafe_value

    with pytest.raises(ValueError):
        OperatorWorkspaceSpineReadModel.model_validate(payload)


def test_operator_workspace_spine_rejects_raw_path_or_secret_text() -> None:
    payload = build_operator_workspace_spine_read_model().model_dump(mode="json")
    payload["workspace_ref"] = "/Users/someone/private/repo"

    with pytest.raises(ValueError):
        OperatorWorkspaceSpineReadModel.model_validate(payload)

    payload = build_operator_workspace_spine_read_model().model_dump(mode="json")
    payload["lanes"][0]["safe_summary"] = "Contains api_key material."

    with pytest.raises(ValueError):
        OperatorWorkspaceSpineReadModel.model_validate(payload)


def test_today_summary_binds_operator_workspace_spine(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    today = service.today_summary()
    read_model = today["operator_workspace_spine_read_model"]

    assert today["operator_workspace_spine_contract_ref"] == (
        OPERATOR_WORKSPACE_SPINE_CONTRACT_REF
    )
    assert today["operator_workspace_spine_status"] == (
        "implemented_read_only_operator_workspace_spine"
    )
    assert read_model["source"] == "python_core_operator_workspace_spine_read_model"
    assert read_model["route_ref"] == OPERATOR_WORKSPACE_SPINE_ROUTE_REF
    assert read_model["cli_ref"] == OPERATOR_WORKSPACE_SPINE_CLI_REF
    assert read_model["git_mutation_enabled"] is False
    assert read_model["shell_subprocess_execution_enabled"] is False
    assert read_model["browser_automation_enabled"] is False
    assert read_model["dev_server_start_enabled"] is False
    assert read_model["production_authority_enabled"] is False
    _assert_no_operator_workspace_authority(read_model)


def test_operator_workspace_cli_outputs_safe_refs_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_operator_workspace_spine.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "operator_workspace_spine_read_model.v1"
    assert payload["source"] == "python_core_operator_workspace_spine_read_model"
    assert payload["real_workspace_runtime_performed"] is False
    assert payload["git_mutation_performed"] is False
    assert payload["shell_subprocess_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["dev_server_started"] is False
    assert payload["coworker_dispatch_performed"] is False
    assert payload["provider_or_connector_runtime_performed"] is False
    _assert_no_operator_workspace_authority(payload)


def test_operator_workspace_proof_and_trust_refs_are_visible(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    detail = service.proof_detail(OPERATOR_WORKSPACE_SPINE_PROOF_REF)
    record = detail["record"]
    assert record["proof_kind"] == "operator_workspace_spine"
    assert record["status"] == "implemented_read_only_operator_workspace_spine"
    assert OPERATOR_WORKSPACE_SPINE_ROUTE_REF in record["backend_route_refs"]
    assert OPERATOR_WORKSPACE_SPINE_CLI_REF in record["next_safe_action"]
    assert "blocked-state:operator-workspace:no-git-mutation" in (
        record["blocked_authority_refs"]
    )
    assert "blocked-state:operator-workspace:no-shell-subprocess-execution" in (
        record["blocked_authority_refs"]
    )
    _assert_no_operator_workspace_authority(detail)

    trust = build_trust_authority_matrix_read_model(today_summary=service.today_summary())
    lane = next(
        item
        for item in trust["lanes"]
        if item["lane_ref"] == "trust-lane:operator-workspace-spine"
    )
    assert lane["authority_state"] == "available_now"
    assert lane["operator_posture"] == "enabled_read_only"
    assert OPERATOR_WORKSPACE_SPINE_PROOF_REF in lane["proof_refs"]
    assert OPERATOR_WORKSPACE_SPINE_CLI_REF in lane["cli_inspection_refs"]
    assert "blocked-state:operator-workspace:no-git-mutation" in (
        lane["blocked_authority_refs"]
    )


def test_operator_workspace_does_not_add_mutation_routes() -> None:
    route_paths = {route.path for route in build_api_manifest(app).routes}
    for forbidden_route in (
        "/control-center/git/commit",
        "/control-center/git/push",
        "/control-center/git/pull",
        "/control-center/git/checkout",
        "/control-center/workspace/apply",
        "/control-center/workspace/run",
        "/control-center/coworker/dispatch",
        "/control-center/operator-workspace/run",
        "/control-center/operator-workspace/git/commit",
    ):
        assert forbidden_route not in route_paths
