from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from ultimate_ai_agent.core.control_center.action_inbox_work_queue import (
    ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS,
    ACTION_INBOX_WORK_QUEUE_CONTRACT_REF,
    ACTION_INBOX_WORK_QUEUE_SOURCE,
    ACTION_INBOX_WORK_QUEUE_UNSAFE_REF_OMITTED_REF,
    build_action_inbox_work_queue_read_model,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import workspace_write_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def _assert_work_queue(read_model: dict[str, Any]) -> None:
    assert read_model["schema_version"] == "action-inbox-work-queue.v1"
    assert read_model["contract_ref"] == ACTION_INBOX_WORK_QUEUE_CONTRACT_REF
    assert read_model["source"] == ACTION_INBOX_WORK_QUEUE_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_read_model_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["route_ref"] == "GET /control-center/actions/inbox"
    assert read_model["proof_route_ref"] == "GET /control-center/proof/{proof_ref}"
    assert set(ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS) <= set(
        read_model["blocked_authority_refs"]
    )
    assert read_model["lane_count"] == len(read_model["lanes"])
    assert read_model["work_item_count"] == len(read_model["work_items"])
    assert read_model["work_item_refs"] == [
        item["item_ref"] for item in read_model["work_items"]
    ]
    assert read_model["item_count"] >= read_model["operator_actionable_count"]
    assert read_model["next_safe_action"]
    assert read_model["fake_mutation_controls_exposed"] is False
    assert isinstance(read_model["unsafe_ref_omitted_count"], int)
    assert isinstance(read_model["unsafe_ref_blocked_state_refs"], list)
    assert read_model["work_items"]
    for item in read_model["work_items"]:
        assert item["item_ref"]
        assert item["proof_ref"].startswith("proof-ref:action-decision:")
        assert "exact_scope_ref" in item
        assert "idempotency_ref" in item
        assert item["expiry_or_staleness"]
        assert item["approval_posture"]
        assert item["receipt_posture"]
        assert item["mutation_control_posture"] in {
            "decision_receipt_only_no_execution",
            "exact_local_task_commit_route_only",
            "no_mutation_control_exposed",
        }
        assert item["fake_mutation_control_exposed"] is False
        assert item["expected_receipt_refs"] or item["receipt_refs"]
        assert item["blocked_authority_refs"]
    for field_name in [
        "action_execution_enabled",
        "connector_write_enabled",
        "connector_send_enabled",
        "provider_model_call_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "memory_write_enabled",
        "context_injection_authorized",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[field_name] is False
    serialized = json.dumps(read_model, sort_keys=True).lower()
    for forbidden in [
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "credential",
        "api_key",
        "/users/",
    ]:
        assert forbidden not in serialized


def test_action_inbox_work_queue_summarizes_backend_queue(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    inbox = repo.actions_inbox()
    read_model = inbox["action_inbox_work_queue_read_model"]

    assert inbox["action_inbox_work_queue_contract_ref"] == (
        ACTION_INBOX_WORK_QUEUE_CONTRACT_REF
    )
    _assert_work_queue(read_model)
    assert read_model["ready_for_decision_count"] >= 1
    assert read_model["proposal_only_count"] >= 1
    assert read_model["blocked_count"] >= 1
    assert read_model["tier_3_exact_local_task_commit_available"] is False
    assert read_model["next_item"]["proof_ref"].startswith("proof-ref:action-decision:")
    assert read_model["next_item"]["exact_scope_ref"]
    assert read_model["next_item"]["idempotency_ref"]
    assert read_model["next_item"]["expiry_or_staleness"]
    assert read_model["next_item"]["local_task_commit_eligible"] is False
    assert read_model["unsafe_ref_omitted_count"] == 0
    ready_item = next(
        item
        for item in read_model["work_items"]
        if item["item_ref"] == read_model["next_item_ref"]
    )
    assert ready_item["operator_actionable"] is True
    assert ready_item["mutation_control_posture"] == "decision_receipt_only_no_execution"
    assert ready_item["receipt_posture"] in {
        "expected_receipt_refs_visible",
        "receipt_refs_recorded",
    }


def test_action_inbox_work_queue_promotes_exact_local_task_lane_after_approval(
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
            decision_reason_ref="decision-reason-ref:test-work-queue-approval",
        ),
        idempotency_key_ref="idempotency-ref:test-work-queue-approval",
    )

    read_model = repo.actions_inbox()["action_inbox_work_queue_read_model"]

    _assert_work_queue(read_model)
    assert read_model["approved_local_task_count"] == 1
    assert read_model["tier_3_exact_local_task_commit_available"] is True
    assert read_model["next_item"]["lane_id"] == "approved_local_task_lane"
    assert read_model["next_item"]["local_task_commit_eligible"] is True
    assert read_model["next_item"]["local_task_commit_route_ref"] == (
        "POST /control-center/actions/{action_id}/local-task/commit"
    )
    assert read_model["next_safe_action"].startswith("Commit the exact approved")
    local_task_item = next(
        item
        for item in read_model["work_items"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert local_task_item["operator_actionable"] is True
    assert local_task_item["local_task_commit_eligible"] is True
    assert local_task_item["local_task_commit_route_ref"] == (
        "POST /control-center/actions/{action_id}/local-task/commit"
    )
    assert (
        local_task_item["mutation_control_posture"]
        == "exact_local_task_commit_route_only"
    )
    assert local_task_item["approval_posture"] == "backend_owned_approval_ready"
    assert local_task_item["exact_scope_ref"]
    assert local_task_item["idempotency_ref"]
    assert local_task_item["expiry_or_staleness"]
    assert local_task_item["proof_ref"].startswith("proof-ref:action-decision:")


def test_action_inbox_work_queue_marks_unsafe_ref_omissions() -> None:
    read_model = build_action_inbox_work_queue_read_model(
        actions=[
            {
                "item_ref": "founder-action:test-unsafe-ref",
                "title": "Unsafe ref test",
                "safe_summary": "Backend-owned test item with an omitted unsafe ref.",
                "action_group_id": "ready_for_decision",
                "action_group_label": "Ready for decision",
                "status": "review_ready",
                "priority": "high",
                "risk_class": "medium",
                "action_kind": "review_only",
                "side_effect_class": "validation_only",
                "approval_required": True,
                "approval_envelope_ref": "approval-envelope:test-unsafe-ref",
                "action_envelope_ref": "action-envelope:test-unsafe-ref",
                "action_scope_ref": "scope-ref:test-unsafe-ref",
                "approval_envelope_status": "review_ready_exact_scope_required",
                "action_expected_receipt_refs": [
                    "receipt-plan:test-unsafe-ref",
                    "/Users/private/raw-path",
                ],
                "receipt_refs": [],
                "evidence_refs": ["evidence-ref:test-unsafe-ref"],
                "action_blocked_state_refs": [],
                "next_safe_action": "Inspect safe refs only.",
            }
        ],
        action_groups=[
            {
                "group_id": "ready_for_decision",
                "label": "Ready for decision",
                "safe_summary": "Ready items.",
                "available_action": "Record a decision receipt only.",
                "count": 1,
            }
        ],
    )

    _assert_work_queue(read_model)
    assert read_model["unsafe_ref_omitted_count"] == 1
    assert read_model["unsafe_ref_blocked_state_refs"] == [
        ACTION_INBOX_WORK_QUEUE_UNSAFE_REF_OMITTED_REF
    ]
    assert ACTION_INBOX_WORK_QUEUE_UNSAFE_REF_OMITTED_REF in read_model[
        "blocked_authority_refs"
    ]
    serialized = json.dumps(read_model, sort_keys=True)
    assert "/Users/private/raw-path" not in serialized


def test_action_inbox_work_queue_cli_is_read_only_and_redacted(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_founder_loop.py"),
            "--state-dir",
            str(tmp_path / "founder_loop"),
            "inspect-action-work-queue",
            "--limit",
            "12",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "founder-loop-cli:v1"
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-action-work-queue"
    )
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    _assert_work_queue(payload["action_inbox_work_queue_read_model"])
