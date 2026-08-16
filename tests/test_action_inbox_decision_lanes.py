from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from ultimate_ai_agent.core.control_center.action_inbox_decision_lanes import (
    ACTION_INBOX_DECISION_LANE_CONTRACT_REF,
    ACTION_INBOX_DECISION_LANE_ORDER,
    ACTION_INBOX_DECISION_LANE_READ_MODEL_SOURCE,
    ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS,
    ActionInboxDecisionLaneItem,
    build_action_inbox_decision_lane_read_model,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import workspace_write_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def _base_action(ref: str, **overrides: Any) -> dict[str, Any]:
    suffix = ref.replace(":", "-")
    action = {
        "item_ref": ref,
        "title": f"Action {suffix}",
        "safe_summary": f"Review safe refs for {suffix}.",
        "surface": "Actions",
        "priority": "normal",
        "risk_class": "medium",
        "action_kind": "local_task_create",
        "status": "review_ready",
        "side_effect_class": "local_dev_workspace_only",
        "authority_boundary": (
            "Action Inbox decision lanes are review posture only."
        ),
        "approval_required": True,
        "approval_envelope_ref": f"approval-envelope:test:{suffix}",
        "approval_envelope_status": "review_ready_exact_scope_required",
        "state_change_contract_ref": "contract-ref:test-action-state-change:v1",
        "state_change_readiness": "review_ready",
        "blocked_state": "none",
        "evidence_refs": [f"evidence-ref:test:{suffix}"],
        "receipt_refs": [f"receipt-plan:test:{suffix}"],
        "idempotency_key_ref": f"idempotency-ref:test:{suffix}",
        "expires_at": "review-required",
        "stale_state": "fresh",
        "rollback_ref": f"rollback-ref:test:{suffix}",
        "safe_disable_ref": f"safe-disable:test:{suffix}",
        "action_envelope_ref": f"action-envelope:test:{suffix}",
        "action_scope_ref": f"scope-ref:test:{suffix}",
        "action_approval_requirement_ref": f"approval-requirement:test:{suffix}",
        "action_expected_receipt_refs": [f"receipt-plan:test:{suffix}"],
        "action_blocked_state_refs": [
            "blocked-state:no-action-execution",
        ],
        "action_group_id": "ready_for_decision",
        "action_group_reason": "Exact scope and receipts are visible.",
        "action_group_available_action": "Record a decision receipt only.",
        "action_envelope_estimated_cost_usd": 0.0,
        "action_envelope_max_approved_cost_usd": 1.0,
        "action_envelope_provider_ref": "provider-ref:test",
        "action_envelope_model_profile_ref": "model-profile-ref:test",
        "action_envelope_input_metered_units": 0,
        "action_envelope_output_metered_units": 0,
        "action_envelope_total_metered_units": 0,
        "action_envelope_cost_estimate_ref": f"cost-estimate-ref:test:{suffix}",
        "action_envelope_captured_usage_ref": f"usage-capture-ref:test:{suffix}",
        "action_envelope_budget_decision_ref": f"budget-decision-ref:test:{suffix}",
        "action_envelope_cost_receipt_refs": [
            f"cost-estimate-ref:test:{suffix}",
            f"usage-capture-ref:test:{suffix}",
            f"budget-decision-ref:test:{suffix}",
            "provider-ref:test",
            "model-profile-ref:test",
        ],
        "action_envelope_cost_blocked_state_refs": [],
        "action_envelope_cost_state_label": "Cost approved",
        "action_envelope_provider_authority_state_label": (
            "Provider/model refs present"
        ),
        "action_envelope_unknown_paid_cost_requires_explicit_approval": False,
        "action_envelope_frontier_usage_claimed": False,
        "approval_envelope": {
            "expected_receipt_refs": [f"receipt-plan:test:{suffix}"],
            "blocked_authority_refs": ["blocked-state:no-action-execution"],
            "evidence_refs": [f"evidence-ref:test:{suffix}"],
            "cost_receipt_refs": [
                f"cost-estimate-ref:test:{suffix}",
                f"usage-capture-ref:test:{suffix}",
                f"budget-decision-ref:test:{suffix}",
            ],
            "cost_blocked_state_refs": [],
            "cost_state_label": "Cost approved",
            "provider_authority_state_label": "Provider/model refs present",
        },
        "next_safe_action": "Record a review receipt only.",
    }
    action.update(overrides)
    return action


def _assert_read_model(read_model: dict[str, Any]) -> None:
    assert read_model["contract_ref"] == ACTION_INBOX_DECISION_LANE_CONTRACT_REF
    assert read_model["source"] == ACTION_INBOX_DECISION_LANE_READ_MODEL_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_read_model_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["lane_order"] == list(ACTION_INBOX_DECISION_LANE_ORDER)
    assert [lane["lane_id"] for lane in read_model["lanes"]] == list(
        ACTION_INBOX_DECISION_LANE_ORDER
    )
    assert set(ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_state_refs"]
    )
    for field_name in [
        "action_execution_enabled",
        "connector_write_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "provider_model_call_enabled",
        "memory_write_enabled",
        "context_injection_authorized",
        "hidden_memory_write_authorized",
        "production_authority_enabled",
        "approval_alone_executes",
    ]:
        assert read_model[field_name] is False
    for item in read_model["items"]:
        assert item["backend_owned"] is True
        assert item["safe_refs_only"] is True
        assert item["raw_content_included"] is False
        assert set(ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS) <= set(
            item["blocked_authority_refs"]
        )
        for field_name in [
            "approval_alone_executes",
            "approval_ref_authority",
            "approval_grants_runtime_authority",
            "action_execution_enabled",
            "connector_write_enabled",
            "shell_subprocess_execution_enabled",
            "browser_execution_enabled",
            "provider_model_call_enabled",
            "memory_write_enabled",
            "context_injection_authorized",
            "hidden_memory_write_authorized",
            "production_authority_enabled",
        ]:
            assert item[field_name] is False


def test_action_inbox_decision_lanes_surface_from_storage(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    inbox = repo.actions_inbox()
    read_model = inbox["action_inbox_decision_lane_read_model"]

    assert (
        inbox["action_inbox_decision_lane_contract_ref"]
        == ACTION_INBOX_DECISION_LANE_CONTRACT_REF
    )
    _assert_read_model(read_model)
    lane_counts = {lane["lane_id"]: lane["count"] for lane in read_model["lanes"]}
    assert lane_counts["blocked"] >= 1
    assert lane_counts["cost_blocked"] >= 1
    assert lane_counts["draft_only"] >= 1
    item_by_ref = {item["item_ref"]: item for item in read_model["items"]}
    assert (
        item_by_ref["founder-action:setup-assistant-hardening"]["lane_id"]
        == "blocked"
    )
    assert (
        item_by_ref["founder-action:local-task-create-scorecard"]["lane_id"]
        == "cost_blocked"
    )
    assert (
        item_by_ref["founder-action:local-task-create-scorecard"][
            "cost_state_label"
        ]
        == "Cost blocked"
    )
    assert (
        item_by_ref["founder-action:local-task-create-scorecard"][
            "provider_authority_state_label"
        ]
        == "No provider authority"
    )


def test_action_inbox_decision_lanes_cover_canonical_operator_states() -> None:
    actions = [
        _base_action("founder-action:test-needs-approval"),
        _base_action(
            "founder-action:test-blocked",
            status="blocked",
            action_group_id="blocked_by_authority",
        ),
        _base_action(
            "founder-action:test-draft",
            approval_required=False,
            action_kind="task_decomposition_proposal",
            action_group_id="proposal_only_no_execution_path",
        ),
        _base_action(
            "founder-action:test-cost-blocked",
            action_envelope_cost_state_label="Cost blocked",
            action_envelope_cost_blocked_state_refs=[
                "blocked-state:frontier-ai-cost-blocked"
            ],
        ),
        _base_action(
            "founder-action:test-no-authority",
            action_envelope_provider_authority_state_label="No provider authority",
        ),
        _base_action("founder-action:test-approved", status="approved"),
        _base_action("founder-action:test-rejected", status="rejected"),
        _base_action("founder-action:test-deferred", status="deferred"),
        _base_action("founder-action:test-receipt", status="receipt_recorded"),
    ]

    read_model = build_action_inbox_decision_lane_read_model(actions=actions)

    _assert_read_model(read_model)
    lane_by_ref = {item["item_ref"]: item["lane_id"] for item in read_model["items"]}
    assert lane_by_ref == {
        "founder-action:test-needs-approval": "needs_approval",
        "founder-action:test-blocked": "blocked",
        "founder-action:test-draft": "draft_only",
        "founder-action:test-cost-blocked": "cost_blocked",
        "founder-action:test-no-authority": "no_authority",
        "founder-action:test-approved": "approved_no_execution",
        "founder-action:test-rejected": "rejected",
        "founder-action:test-deferred": "deferred",
        "founder-action:test-receipt": "receipt_recorded",
    }


def test_action_inbox_decision_lanes_fail_safe_when_envelope_fields_are_missing() -> None:
    action = _base_action(
        "founder-action:test-missing-envelope",
        approval_envelope=None,
    )
    for field_name in [
        "approval_envelope_ref",
        "action_scope_ref",
        "action_approval_requirement_ref",
        "idempotency_key_ref",
        "rollback_ref",
        "safe_disable_ref",
        "action_expected_receipt_refs",
        "receipt_refs",
        "evidence_refs",
    ]:
        action.pop(field_name, None)

    read_model = build_action_inbox_decision_lane_read_model(actions=[action])
    item = read_model["items"][0]

    assert item["lane_id"] == "blocked"
    assert "approval_envelope:missing" in item["missing_envelope_field_states"]
    assert "expected_receipt_refs:missing" in item["missing_envelope_field_states"]
    assert item["expected_receipt_state"] == "missing_fail_closed"


def test_action_inbox_decision_lanes_approval_receipts_do_not_execute(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[workspace_write_authority_lease()],
    )
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:local-task-create-scorecard"
            ),
            decision_reason_ref="decision-reason-ref:test-decision-lane-approve"
        ),
        idempotency_key_ref="idempotency-ref:test-decision-lane-approve",
    )

    read_model = repo.actions_inbox()["action_inbox_decision_lane_read_model"]
    item = next(
        item
        for item in read_model["items"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )

    assert item["lane_id"] == "approved_no_execution"
    assert item["action_execution_enabled"] is False
    assert item["approval_alone_executes"] is False
    assert item["approval_ref_authority"] is False


def test_action_inbox_decision_lane_contract_rejects_raw_content_and_runtime_authority() -> None:
    safe_item = _base_action("founder-action:test-contract")
    read_model = build_action_inbox_decision_lane_read_model(actions=[safe_item])
    item_payload = dict(read_model["items"][0])

    with pytest.raises(ValueError, match="unsafe/private content"):
        ActionInboxDecisionLaneItem(
            **{
                **item_payload,
                "title": "raw_prompt /Users/example secret",
            }
        )
    with pytest.raises(ValueError, match="action_execution_enabled must remain false"):
        ActionInboxDecisionLaneItem(
            **{
                **item_payload,
                "action_execution_enabled": True,
            }
        )
    with pytest.raises(ValueError, match="frontier usage claims require cost telemetry"):
        ActionInboxDecisionLaneItem(
            **{
                **item_payload,
                "frontier_usage_claimed": True,
                "cost_receipt_refs": [],
            }
        )


def test_action_inbox_decision_lane_cli_inspection_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    FounderLoopRepository(state_dir)
    before = {
        path.relative_to(state_dir): path.read_bytes()
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_action_inbox_decision_lanes.py"),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    after = {
        path.relative_to(state_dir): path.read_bytes()
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    assert before == after
    assert payload["contract_ref"] == ACTION_INBOX_DECISION_LANE_CONTRACT_REF
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["action_execution_enabled"] is False
    _assert_read_model(payload["action_inbox_decision_lane_read_model"])

    serialized = json.dumps(payload, sort_keys=True).lower()
    for forbidden in [
        str(tmp_path).lower(),
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "api_key",
        "authorization",
        "cookie",
        "password",
        "private_key",
        "username",
        "hostname",
    ]:
        assert forbidden not in serialized

    missing_state_dir = tmp_path / "missing_state"
    missing = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_action_inbox_decision_lanes.py"),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["action_inbox_decision_lane_read_model"]["items"] == []
    assert not missing_state_dir.exists()
