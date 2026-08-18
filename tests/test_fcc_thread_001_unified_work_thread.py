from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from scripts import verify_fcc_thread_001_unified_work_thread
from scripts.dev import uaa_founder_loop
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.unified_work_thread import (
    UNIFIED_WORK_THREAD_CONTRACT_REF,
    UNIFIED_WORK_THREAD_READ_MODEL_SOURCE,
    UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS,
    UNIFIED_WORK_THREAD_STEP_ORDER,
    UnifiedWorkThreadReadModel,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _chat_turn_request() -> ChatTurnReceiptRequest:
    return ChatTurnReceiptRequest(
        turn_ref="chat-turn:fcc-thread-001",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref="safe-summary-ref:fcc-thread-001",
        evidence_refs=["evidence-ref:fcc-thread-001:chat"],
        metadata_refs=["metadata-ref:fcc-thread-001:chat"],
    )


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _assert_thread(read_model: dict[str, Any]) -> UnifiedWorkThreadReadModel:
    parsed = UnifiedWorkThreadReadModel(**read_model)
    assert parsed.contract_ref == UNIFIED_WORK_THREAD_CONTRACT_REF
    assert parsed.source == UNIFIED_WORK_THREAD_READ_MODEL_SOURCE
    assert parsed.backend_owned is True
    assert parsed.local_read_model_only is True
    assert parsed.seeded_demo_safe is True
    assert parsed.safe_refs_only is True
    assert parsed.safe_summary_only is True
    assert parsed.raw_content_included is False
    assert parsed.step_order == list(UNIFIED_WORK_THREAD_STEP_ORDER)
    assert [step.step_id for step in parsed.steps] == list(
        UNIFIED_WORK_THREAD_STEP_ORDER
    )
    assert set(UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS) <= set(
        parsed.blocked_authority_refs
    )
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "a2a_runtime_dispatch_enabled",
        "mcp_runtime_dispatch_enabled",
        "browser_execution_enabled",
        "live_web_enabled",
        "connector_read_enabled",
        "connector_write_enabled",
        "email_calendar_send_enabled",
        "crm_write_enabled",
        "account_sync_enabled",
        "shell_subprocess_execution_enabled",
        "background_autonomy_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "action_execution_enabled",
        "public_beta_claim_enabled",
        "public_release_claim_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False
    return parsed


def test_unified_work_thread_links_existing_founder_loop_refs(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    turn_receipt = repo.record_chat_turn_receipt(
        request=_chat_turn_request(),
        idempotency_key_ref="idempotency-ref:fcc-thread-001-chat-turn",
    )
    plan_handoff = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=ChatHandoffRequest(
            handoff_target="plans",
            decision_reason_ref="decision-reason-ref:fcc-thread-001-plan",
            metadata_refs=["metadata-ref:fcc-thread-001-plan"],
        ),
        idempotency_key_ref="idempotency-ref:fcc-thread-001-plan",
    )
    action_handoff = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=ChatHandoffRequest(
            handoff_target="actions",
            decision_reason_ref="decision-reason-ref:fcc-thread-001-action",
            metadata_refs=["metadata-ref:fcc-thread-001-action"],
        ),
        idempotency_key_ref="idempotency-ref:fcc-thread-001-action",
    )
    action_decision = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="defer",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:setup-assistant-hardening"
            ),
            decision_reason_ref="decision-reason-ref:fcc-thread-001-action-defer"
        ),
        idempotency_key_ref="idempotency-ref:fcc-thread-001-action-defer",
    )
    memory_decision = repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision="defer",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:fcc-thread-001",
            source_refs=["source-ref:fcc-thread-001-memory"],
            evidence_refs=["evidence-ref:fcc-thread-001-memory"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-thread-001-memory-defer",
    )

    today = repo.today_summary()
    read_model = today["unified_work_thread_read_model"]
    parsed = _assert_thread(read_model)

    assert today["unified_work_thread_contract_ref"] == UNIFIED_WORK_THREAD_CONTRACT_REF
    assert turn_receipt["receipt_ref"] in parsed.chat_turn_receipt_refs
    assert plan_handoff["receipt_ref"] in parsed.chat_handoff_receipt_refs
    assert action_handoff["receipt_ref"] in parsed.chat_handoff_receipt_refs
    assert action_decision["receipt_ref"] in parsed.action_decision_receipt_refs
    assert memory_decision["receipt_ref"] in parsed.memory_review_receipt_refs
    assert action_decision["receipt_ref"] in parsed.receipt_refs
    assert memory_decision["receipt_ref"] in parsed.receipt_refs
    assert parsed.plan_refs
    assert parsed.plan_proposal_refs
    assert parsed.action_refs
    assert parsed.evidence_timeline_refs
    assert parsed.evidence_event_refs
    assert parsed.memory_review_candidate_refs
    assert parsed.weekly_review_refs
    assert parsed.steps[0].step_id == "chat_handoff"
    assert parsed.steps[-1].step_id == "weekly_review"


def test_unified_work_thread_rejects_authority_and_raw_content(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.today_summary()["unified_work_thread_read_model"]

    payload = dict(read_model)
    payload["provider_model_call_enabled"] = True
    with pytest.raises(ValidationError, match="provider_model_call_enabled"):
        UnifiedWorkThreadReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw prompt material."
    with pytest.raises(ValidationError, match="unsafe text"):
        UnifiedWorkThreadReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw-prompt material."
    with pytest.raises(ValidationError, match="unsafe text"):
        UnifiedWorkThreadReadModel(**payload)

    payload = dict(read_model)
    payload["step_order"] = list(reversed(payload["step_order"]))
    with pytest.raises(ValidationError, match="step order"):
        UnifiedWorkThreadReadModel(**payload)


def test_unified_work_thread_cli_is_read_only_and_redacted(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "founder_loop"
    FounderLoopRepository(state_dir).today_summary()
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_founder_loop.py"),
            "--state-dir",
            str(state_dir),
            "inspect-work-thread",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-work-thread"
    )
    assert payload["contract_ref"] == UNIFIED_WORK_THREAD_CONTRACT_REF
    assert payload["source"] == UNIFIED_WORK_THREAD_READ_MODEL_SOURCE
    assert payload["safe_summary"]
    assert payload["authority_boundary"]
    assert payload["next_safe_action"]
    assert payload["step_order"] == list(UNIFIED_WORK_THREAD_STEP_ORDER)
    assert [step["step_id"] for step in payload["steps"]] == list(
        UNIFIED_WORK_THREAD_STEP_ORDER
    )
    assert all(step["safe_summary"] for step in payload["steps"])
    assert all(step["next_safe_action"] for step in payload["steps"])
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["provider_model_call_enabled"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["production_authority_enabled"] is False
    assert str(state_dir) not in result.stdout
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    assert after_files == before_files

    missing_state_dir = tmp_path / "missing_founder_loop"
    assert uaa_founder_loop.main(
        [
            "--state-dir",
            str(missing_state_dir),
            "inspect-work-thread",
        ]
    ) == 0
    missing_output = capsys.readouterr().out
    missing_payload = json.loads(missing_output)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["steps"] == []
    assert missing_payload["step_order"] == list(UNIFIED_WORK_THREAD_STEP_ORDER)
    assert missing_payload["raw_paths_omitted"] is True
    assert str(missing_state_dir) not in missing_output
    assert not missing_state_dir.exists()


def test_fcc_thread_001_static_verifier_passes() -> None:
    assert verify_fcc_thread_001_unified_work_thread.verify() == []
