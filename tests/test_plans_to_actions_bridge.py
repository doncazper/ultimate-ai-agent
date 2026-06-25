from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.plans_to_actions import (
    PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF,
    PLANS_TO_ACTIONS_BRIDGE_READ_MODEL_SOURCE,
    PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS,
    PlansToActionsBridgeItem,
    PlansToActionsBridgeReadModel,
    build_plans_to_actions_bridge_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_bridge_read_model(read_model: dict[str, Any]) -> None:
    assert read_model["contract_ref"] == PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
    assert read_model["source"] == PLANS_TO_ACTIONS_BRIDGE_READ_MODEL_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_read_model_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["item_count"] == len(read_model["items"])
    assert set(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_state_refs"]
    )
    for flag in [
        "approval_ref_authority",
        "approval_grant_capture_enabled",
        "approval_alone_executes",
        "execution_authorized",
        "execution_performed",
        "action_execution_enabled",
        "tool_execution_enabled",
        "workflow_execution_enabled",
        "model_provider_call_enabled",
        "provider_model_call_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "connector_runtime_enabled",
        "connector_write_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False
    for item in read_model["items"]:
        assert item["backend_owned"] is True
        assert item["review_only"] is True
        assert item["proposal_only"] is True
        assert item["expected_receipt_refs"]
        assert item["rollback_ref"].startswith("rollback-")
        assert item["safe_disable_ref"].startswith("safe-disable:")
        assert item["risk_class"]
        assert item["why_proposed"]
        assert item["action_envelope_ref"]
        assert item["action_scope_ref"]
        assert item["approval_requirement_ref"]
        assert set(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS) <= set(
            item["blocked_authority_refs"]
        )
        for flag in [
            "approval_ref_authority",
            "approval_grant_capture_enabled",
            "approval_alone_executes",
            "execution_authorized",
            "execution_performed",
            "action_execution_enabled",
            "tool_execution_enabled",
            "workflow_execution_enabled",
            "model_provider_call_enabled",
            "provider_model_call_enabled",
            "shell_subprocess_execution_enabled",
            "browser_execution_enabled",
            "connector_runtime_enabled",
            "connector_write_enabled",
            "memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            assert item[flag] is False


def test_plans_to_actions_bridge_surfaces_from_today_and_actions(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["plans_to_actions_bridge_contract_ref"] == (
        PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
    )
    assert inbox["plans_to_actions_bridge_contract_ref"] == (
        PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
    )
    _assert_bridge_read_model(today["plans_to_actions_bridge_read_model"])
    _assert_bridge_read_model(inbox["plans_to_actions_bridge_read_model"])
    assert today["plans_to_actions_bridge_read_model"]["plan_refs"]
    assert inbox["plans_to_actions_bridge_read_model"]["action_inbox_item_refs"]


def test_today_bridge_uses_full_action_projection_when_display_limit_is_small(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today = repo.today_summary(limit=1)
    read_model = today["plans_to_actions_bridge_read_model"]

    _assert_bridge_read_model(read_model)
    assert read_model["action_inbox_item_refs"]
    for item in read_model["items"]:
        assert item["linked_action_item_ref"]
        assert "blocked-state:plans-to-actions-action-item-missing" not in set(
            item["blocked_authority_refs"]
        )


def test_plans_to_actions_bridge_maps_existing_plan_and_action_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    plans = repo.list_plan_summaries(limit=3)
    actions = repo.list_action_inbox(limit=50)

    read_model = build_plans_to_actions_bridge_read_model(
        plans=plans,
        action_items=actions,
    )

    _assert_bridge_read_model(read_model)
    plan = plans[0]
    item = read_model["items"][0]
    assert item["source_plan_ref"] == plan["plan_ref"]
    assert item["expected_receipt_refs"]
    assert item["rollback_ref"] == plan["rollback_ref"]
    assert item["safe_disable_ref"] == plan["safe_disable_ref"]
    assert item["task_decomposition_proposal_ref"] == (
        plan["task_decomposition_proposal_ref"]
    )
    assert item["linked_action_item_ref"]


def test_plans_to_actions_bridge_marks_synthetic_fallback_refs_as_blocked(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    plan = dict(repo.list_plan_summaries(limit=1)[0])
    for field_name in [
        "expected_receipt_refs",
        "plan_action_expected_receipt_refs",
        "rollback_ref",
        "safe_disable_ref",
        "task_decomposition_action_envelope_ref",
        "action_envelope_ref",
        "scope_ref",
        "plan_action_scope_ref",
        "approval_requirement_ref",
        "plan_action_approval_requirement_ref",
    ]:
        plan.pop(field_name, None)

    read_model = build_plans_to_actions_bridge_read_model(
        plans=[plan],
        action_items=[],
    )

    _assert_bridge_read_model(read_model)
    blocked_refs = set(read_model["items"][0]["blocked_authority_refs"])
    assert "blocked-state:plans-to-actions-expected-receipt-refs-missing" in blocked_refs
    assert "blocked-state:plans-to-actions-rollback-ref-missing" in blocked_refs
    assert "blocked-state:plans-to-actions-safe-disable-ref-missing" in blocked_refs
    assert "blocked-state:plans-to-actions-action-envelope-ref-missing" in blocked_refs
    assert "blocked-state:plans-to-actions-action-scope-ref-missing" in blocked_refs
    assert (
        "blocked-state:plans-to-actions-approval-requirement-ref-missing"
        in blocked_refs
    )


def test_plans_to_actions_bridge_rejects_authority_and_raw_content(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.today_summary()["plans_to_actions_bridge_read_model"]
    item_payload = dict(read_model["items"][0])

    item_payload["action_execution_enabled"] = True
    with pytest.raises(ValidationError, match="action_execution_enabled"):
        PlansToActionsBridgeItem(**item_payload)

    item_payload = dict(read_model["items"][0])
    item_payload["safe_summary"] = "Contains raw prompt material."
    with pytest.raises(ValidationError, match="unsafe/private content"):
        PlansToActionsBridgeItem(**item_payload)

    read_model["provider_model_call_enabled"] = True
    with pytest.raises(ValidationError, match="provider_model_call_enabled"):
        PlansToActionsBridgeReadModel(**read_model)


def test_plans_to_actions_bridge_cli_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.today_summary()
    state_dir = tmp_path / "founder_loop"
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_plans_to_actions_bridge.py"),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    payload = json.loads(result.stdout)

    assert after_files == before_files
    assert payload["contract_ref"] == PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
    assert payload["command_ref"] == "repo-local-command:inspect-plans-to-actions-bridge"
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["action_execution_enabled"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["workflow_execution_enabled"] is False
    assert payload["browser_execution_enabled"] is False
    assert payload["connector_runtime_enabled"] is False
    assert payload["provider_model_call_authorized"] is False
    _assert_bridge_read_model(payload["plans_to_actions_bridge_read_model"])

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_plans_to_actions_bridge.py"),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing_result.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert not missing_state_dir.exists()
