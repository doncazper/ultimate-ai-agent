from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import scripts.verify_fcc_action_001_approval_bound_local_micro_lanes as verifier
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FounderLoopLocalTaskCommitReceipt,
)


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_action_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_action_001_approval_bound_local_micro_lanes() == []


def test_local_task_create_is_only_rank5_graduated_lane() -> None:
    manifest = json.loads(
        (ROOT / "docs/control_center/operational_maturity_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    action_module = next(
        module
        for module in manifest["modules"]
        if module["module_id"] == "action_inbox"
    )
    rank5_lanes = [
        lane
        for lane in action_module["graduated_lanes"]
        if lane["rank"] == 5
    ]

    assert [lane["lane_id"] for lane in rank5_lanes] == [
        FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    ]
    lane = rank5_lanes[0]
    assert lane["real_local_mutation"] is True
    assert lane["durable_receipt"] is True
    assert lane["evidence_timeline_event"] is True
    assert lane["repeatability_gate_ref"] == "FCC-ACTION-002"
    assert lane["cli_parity_ref"] == "scripts/dev/uaa_founder_loop.py commit-local-task"
    assert "rollback_execution" in lane["blocked_authorities"]
    assert FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF in lane[
        "rollback_or_safe_disable_refs"
    ]
    assert FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF in lane[
        "rollback_or_safe_disable_refs"
    ]


def test_local_task_commit_receipt_denies_broader_authority() -> None:
    receipt = FounderLoopLocalTaskCommitReceipt(
        item_ref="action-item:test-local-task",
        local_task_ref="local-task:founder-loop:test-local-task",
        receipt_ref="receipt:founder-loop-local-task:test-local-task:test-idem",
        audit_ref="audit:founder-loop-local-task:test-local-task:test-idem",
        idempotency_key_ref="idempotency:test-local-task",
        payload_fingerprint_ref="payload-fingerprint:founder-loop-local-task:test",
        evidence_timeline_event_ref="evidence-timeline:local-task/test-local-task",
        approval_ref="approval-ref:test-local-task",
        approval_status="approved",
        approval_reason_refs=["approval-reason-ref:test-local-task"],
        safe_summary="Local task commit receipt uses safe refs only.",
        evidence_refs=["evidence-ref:test-local-task"],
        blocked_state_refs=list(FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS),
    )

    assert receipt.contract_ref == FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
    assert receipt.action_kind == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    assert receipt.status == "local_task_created"
    assert receipt.safe_disable_ref == FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
    assert receipt.rollback_ref == FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
    assert receipt.safe_disable_posture_ref == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF
    )
    assert receipt.rollback_execution_enabled is False
    assert receipt.rollback_blocker_refs == [FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF]
    assert receipt.connector_write_performed is False
    assert receipt.shell_subprocess_execution_performed is False
    assert receipt.model_provider_authority_used is False
    assert receipt.memory_write_performed is False
    assert receipt.context_injection_performed is False
    assert receipt.external_side_effect_performed is False

    for denied_flag in [
        "connector_write_performed",
        "shell_subprocess_execution_performed",
        "model_provider_authority_used",
        "memory_write_performed",
        "context_injection_performed",
        "external_side_effect_performed",
    ]:
        payload = receipt.model_dump(mode="json")
        payload[denied_flag] = True
        with pytest.raises(ValidationError):
            FounderLoopLocalTaskCommitReceipt(**payload)

    payload = receipt.model_dump(mode="json")
    payload["rollback_execution_enabled"] = True
    with pytest.raises(ValidationError):
        FounderLoopLocalTaskCommitReceipt(**payload)
