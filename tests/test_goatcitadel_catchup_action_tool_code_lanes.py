from __future__ import annotations

import json

from fastapi.testclient import TestClient

from scripts.dev import uaa_founder_loop
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.action_tool_code_catalog import (
    ACTION_TOOL_CODE_CATALOG_CONTRACT_REF,
    ACTION_TOOL_CODE_CATALOG_SOURCE,
    build_action_tool_code_lane_catalog_read_model,
)
from ultimate_ai_agent.core.storage import (
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopRepository,
)


BROAD_AUTHORITY_FLAGS = (
    "generic_tool_execution_enabled",
    "unrestricted_shell_execution_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "plugin_runtime_import_enabled",
    "remote_execution_enabled",
    "provider_model_call_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)


def _entry_by_id(catalog: dict[str, object], capability_id: str) -> dict[str, object]:
    entries = catalog["entries"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        if entry["capability_id"] == capability_id:
            return entry
    raise AssertionError(f"missing catalog entry {capability_id}")


def test_action_tool_code_catalog_preserves_exact_lanes_and_blocks_broad_authority() -> None:
    catalog = build_action_tool_code_lane_catalog_read_model().model_dump(mode="json")

    assert catalog["contract_ref"] == ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    assert catalog["source"] == ACTION_TOOL_CODE_CATALOG_SOURCE
    assert catalog["backend_owned"] is True
    assert catalog["control_center_presentation_only"] is True
    assert catalog["safe_refs_only"] is True
    assert catalog["raw_content_included"] is False
    assert catalog["entry_count"] == 14
    assert catalog["preview_only_count"] == 4
    assert catalog["exact_local_mutation_count"] == 1
    assert catalog["exact_local_authority_capability_count"] == 1
    assert catalog["exact_runtime_lane_count"] == 4
    assert catalog["exact_runtime_authority_capability_count"] == 4
    assert catalog["proposal_only_count"] == 5
    assert catalog["blocked_count"] == 4
    assert all(catalog[flag] is False for flag in BROAD_AUTHORITY_FLAGS)

    local_task = _entry_by_id(catalog, "local_task_create")
    assert local_task["status"] == "implemented_exact_local_mutation_lane"
    assert local_task["exact_local_mutation_available"] is True
    assert local_task["receipt_refs"]
    assert "POST /control-center/actions/{action_id}/local-task/commit" in (
        local_task["route_refs"]
    )

    for capability_id in [
        "runtime.focused_pytest_action_inbox",
        "runtime.repo_verifier_action_inbox",
        "runtime.frontend_check_action_inbox",
        "runtime.repo_doctor_action_inbox",
    ]:
        runtime = _entry_by_id(catalog, capability_id)
        assert runtime["status"] == "implemented_exact_approval_required"
        assert runtime["exact_runtime_lane_available"] is True
        assert runtime["receipt_refs"]
        assert "POST /api/runtime/invocations/{id}/execute" in runtime["route_refs"]

    patch_apply = _entry_by_id(catalog, "coding.approved_patch_apply")
    assert patch_apply["status"] == "blocked_missing_exact_authority"
    assert patch_apply["exact_local_mutation_available"] is False
    assert patch_apply["blocked_authority_refs"]

    for entry in catalog["entries"]:
        assert isinstance(entry, dict)
        assert entry["operator_visible"] is True
        assert entry["inspectable_now"] is True
        assert all(entry[flag] is False for flag in BROAD_AUTHORITY_FLAGS)

    prompt_refs = {prompt["prompt_ref"] for prompt in catalog["unblock_prompts"]}
    assert "prompt-ref:unblock-coding-approved-patch-apply" in prompt_refs
    assert "prompt-ref:unblock-coding-allowlisted-test-command" in prompt_refs
    assert "prompt-ref:unblock-callable-tool-catalog" in prompt_refs

    serialized = json.dumps(catalog, sort_keys=True).lower()
    for forbidden in (
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential material",
    ):
        assert forbidden not in serialized


def test_actions_inbox_persists_backend_owned_action_tool_code_catalog(
    tmp_path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop")
    inbox = repo.actions_inbox(limit=50)
    catalog = inbox["action_tool_code_lane_catalog_read_model"]

    assert inbox["action_tool_code_lane_catalog_contract_ref"] == (
        ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    )
    assert catalog["contract_ref"] == ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    assert catalog["backend_owned"] is True
    assert catalog["entry_count"] == len(catalog["entries"])
    assert catalog["exact_local_mutation_count"] == 1
    assert catalog["exact_local_authority_capability_count"] == 1
    assert catalog["exact_runtime_lane_count"] == 4
    assert catalog["exact_runtime_authority_capability_count"] == 4
    assert catalog["generic_tool_execution_enabled"] is False


def test_actions_inbox_api_exposes_catalog_without_minting_authority(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(FOUNDER_LOOP_STATE_DIR_ENV, str(tmp_path / "api-state"))
    response = TestClient(app).get("/control-center/actions/inbox")

    assert response.status_code == 200
    data = response.json()["data"]
    catalog = data["action_tool_code_lane_catalog_read_model"]
    assert data["action_tool_code_lane_catalog_contract_ref"] == (
        ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    )
    assert catalog["source"] == ACTION_TOOL_CODE_CATALOG_SOURCE
    assert catalog["control_center_presentation_only"] is True
    assert catalog["generic_tool_execution_enabled"] is False
    assert catalog["unrestricted_shell_execution_enabled"] is False
    assert catalog["provider_model_call_enabled"] is False
    assert catalog["production_authority_enabled"] is False


def test_founder_loop_cli_inspects_action_tool_code_catalog(capsys, tmp_path) -> None:
    state_dir = tmp_path / "cli-state"
    FounderLoopRepository(state_dir)

    exit_code = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-action-tool-code-catalog",
            "--limit",
            "50",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    catalog = output["action_tool_code_lane_catalog_read_model"]
    assert output["command_ref"] == "repo-local-command:founder-loop-action-tool-code-catalog"
    assert output["safe_refs_only"] is True
    assert output["raw_content_omitted"] is True
    assert output["raw_paths_omitted"] is True
    assert catalog["contract_ref"] == ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    assert catalog["entry_count"] == 14
    assert catalog["background_autonomy_enabled"] is False
