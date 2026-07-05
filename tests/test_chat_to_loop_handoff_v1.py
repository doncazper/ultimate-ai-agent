from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.control_center.chat_to_loop_handoff import (
    CHAT_TO_LOOP_HANDOFF_CONTRACT_REF,
    CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS,
    CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE,
    CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS,
    ChatToLoopHandoffReadModel,
    build_chat_to_loop_handoff_read_model,
)
from ultimate_ai_agent.core.decision_router import build_turn_harness_binding
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)


ROOT = Path(__file__).resolve().parents[1]


def _chat_turn_request(
    turn_ref: str = "chat-turn:product-loop-009",
    safe_summary_ref: str = "safe-summary-ref:chat-to-loop-test",
) -> ChatTurnReceiptRequest:
    return ChatTurnReceiptRequest(
        turn_ref=turn_ref,
        route_ref="/v1/chat/completions",
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref=safe_summary_ref,
        evidence_refs=["evidence-ref:chat-to-loop:test"],
        metadata_refs=["metadata-ref:chat-to-loop:test"],
    )


def _chat_turn_request_with_binding() -> ChatTurnReceiptRequest:
    return ChatTurnReceiptRequest(
        turn_ref="chat-turn:product-loop-router-binding",
        route_ref="/v1/chat/completions",
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="local-chat-route-answered",
        auth_truth="local-bearer-accepted",
        tool_denial_truth="tools-functions-streaming-denied",
        safe_summary_ref="safe-summary-ref:chat-to-loop-router-test",
        turn_harness_binding=build_turn_harness_binding(
            "Use my card and book pickup at Home Depot.",
            binding_ref="turn-harness-binding:chat-to-loop-test",
            decision_ref="turn-decision:chat-to-loop-test",
        ),
        evidence_refs=["evidence-ref:chat-to-loop:router-test"],
        metadata_refs=["metadata-ref:chat-to-loop:router-test"],
    )


def _assert_chat_to_loop(read_model: dict[str, Any]) -> None:
    assert read_model["schema_version"] == "product-loop-009-chat-to-loop-handoff.v1"
    assert read_model["contract_ref"] == CHAT_TO_LOOP_HANDOFF_CONTRACT_REF
    assert read_model["source"] == CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE
    assert tuple(read_model["outcome_kinds"]) == CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS
    assert {item["outcome_kind"] for item in read_model["outcomes"]} == set(
        CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS
    )
    assert read_model["outcome_count"] == len(read_model["outcomes"])
    assert read_model["outcome_refs"] == [
        item["outcome_ref"] for item in read_model["outcomes"]
    ]
    assert read_model["turn_receipt_count"] == len(read_model["turn_receipt_refs"])
    assert read_model["handoff_receipt_count"] == len(
        read_model["handoff_receipt_refs"]
    )
    assert read_model["remember_this_count"] == len(read_model["memory_proposal_refs"])
    assert read_model["create_action_count"] == len(read_model["action_created_refs"])
    assert read_model["add_to_plan_count"] == len(read_model["plan_created_refs"])
    assert read_model["defer_count"] == len(read_model["defer_refs"])
    assert read_model["ask_human_count"] == len(read_model["ask_human_refs"])
    assert read_model["blocked_count"] == len(read_model["blocked_state_refs"])
    assert read_model["proposal_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["model_output_authority"] is False
    assert read_model["direct_memory_write_authorized"] is False
    assert read_model["context_injection_authorized"] is False
    assert read_model["tool_execution_enabled"] is False
    assert read_model["connector_write_enabled"] is False
    assert read_model["action_execution_enabled"] is False
    assert read_model["plan_execution_enabled"] is False
    assert read_model["provider_model_call_enabled"] is False
    assert read_model["production_authority_enabled"] is False
    assert set(CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_state_refs"]
    )


def test_chat_to_loop_handoff_read_model_classifies_reviewable_outcomes(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    turn_receipt = repo.record_chat_turn_receipt(
        request=_chat_turn_request(),
        idempotency_key_ref="idempotency-ref:chat-to-loop-turn",
    )
    actions_receipt = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=ChatHandoffRequest(
            handoff_target="actions",
            decision_reason_ref="decision-reason-ref:chat-to-loop-actions",
            metadata_refs=["metadata-ref:chat-to-loop-actions"],
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-actions",
    )
    plans_receipt = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=ChatHandoffRequest(
            handoff_target="plans",
            decision_reason_ref="decision-reason-ref:chat-to-loop-plans",
            metadata_refs=["metadata-ref:chat-to-loop-plans"],
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-plans",
    )

    today = repo.today_summary()
    inbox = repo.actions_inbox()
    briefing = repo.morning_briefing()
    read_model = today["chat_to_loop_handoff_read_model"]

    assert today["chat_to_loop_handoff_contract_ref"] == (
        CHAT_TO_LOOP_HANDOFF_CONTRACT_REF
    )
    assert inbox["chat_to_loop_handoff_read_model"] == read_model
    assert briefing["chat_to_loop_handoff_read_model"] == read_model
    _assert_chat_to_loop(read_model)
    assert turn_receipt["receipt_ref"] in read_model["turn_receipt_refs"]
    assert actions_receipt["receipt_ref"] in read_model["handoff_receipt_refs"]
    assert plans_receipt["receipt_ref"] in read_model["handoff_receipt_refs"]
    assert actions_receipt["created_ref"] in read_model["action_created_refs"]
    assert plans_receipt["created_ref"] in read_model["plan_created_refs"]
    assert "memory-intake-proposal:" in read_model["memory_proposal_refs"][0]


def test_chat_to_loop_handoff_rejects_authority_raw_content_and_unsafe_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.chat_to_loop_handoff()["chat_to_loop_handoff_read_model"]

    payload = dict(read_model)
    payload["direct_memory_write_authorized"] = True
    with pytest.raises(ValidationError, match="direct_memory_write_authorized"):
        ChatToLoopHandoffReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw prompt material."
    with pytest.raises(ValidationError, match="unsafe/private content"):
        ChatToLoopHandoffReadModel(**payload)

    payload = dict(read_model)
    payload["outcome_kinds"] = ["create_action"]
    with pytest.raises(ValidationError, match="outcome kinds"):
        ChatToLoopHandoffReadModel(**payload)

    for unsafe_ref in (
        "evidence-ref:alice@example.com",
        "evidence-ref:workstation.local",
        "evidence-ref:relative/path/project",
        "evidence-ref:relative\\path\\project",
    ):
        payload = dict(read_model)
        payload["evidence_refs"] = [unsafe_ref]
        with pytest.raises(ValidationError, match="unsafe ref"):
            ChatToLoopHandoffReadModel(**payload)


def test_chat_to_loop_handoff_idempotency_replay_and_conflict(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    turn_receipt = repo.record_chat_turn_receipt(
        request=_chat_turn_request(),
        idempotency_key_ref="idempotency-ref:chat-to-loop-turn",
    )
    request = ChatHandoffRequest(
        handoff_target="actions",
        decision_reason_ref="decision-reason-ref:chat-to-loop-actions",
    )
    receipt = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=request,
        idempotency_key_ref="idempotency-ref:chat-to-loop-actions",
    )
    replay = repo.record_chat_handoff(
        turn_ref=turn_receipt["turn_ref"],
        request=request,
        idempotency_key_ref="idempotency-ref:chat-to-loop-actions",
    )
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == receipt["receipt_ref"]

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_chat_handoff(
            turn_ref=turn_receipt["turn_ref"],
            request=ChatHandoffRequest(
                handoff_target="plans",
                decision_reason_ref="decision-reason-ref:chat-to-loop-plans",
            ),
            idempotency_key_ref="idempotency-ref:chat-to-loop-actions",
        )


def test_chat_to_loop_preserves_turn_harness_binding_refs_without_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    turn_receipt = repo.record_chat_turn_receipt(
        request=_chat_turn_request_with_binding(),
        idempotency_key_ref="idempotency-ref:chat-to-loop-router-turn",
    )
    stored = repo.latest_chat_turn_receipt(turn_receipt["turn_ref"])

    assert stored is not None
    assert stored["turn_harness_binding"]["turn_contract"] == "approval_required"
    assert stored["turn_harness_binding"]["approval_required"] is True
    assert stored["turn_harness_binding"]["no_action_execution_performed"] is True
    assert stored["turn_harness_binding"]["side_effects_allowed"] is False
    assert stored["action_execution_enabled"] is False
    assert stored["memory_write_authorized"] is False


def test_chat_to_loop_handoff_keeps_created_refs_on_their_source_turn(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    first_turn = repo.record_chat_turn_receipt(
        request=_chat_turn_request(
            turn_ref="chat-turn:product-loop-009-first",
            safe_summary_ref="safe-summary-ref:chat-to-loop-first",
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-first",
    )
    action_receipt = repo.record_chat_handoff(
        turn_ref=first_turn["turn_ref"],
        request=ChatHandoffRequest(
            handoff_target="actions",
            decision_reason_ref="decision-reason-ref:chat-to-loop-first-action",
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-first-action",
    )
    second_turn = repo.record_chat_turn_receipt(
        request=_chat_turn_request(
            turn_ref="chat-turn:product-loop-009-second",
            safe_summary_ref="safe-summary-ref:chat-to-loop-second",
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-second",
    )

    read_model = build_chat_to_loop_handoff_read_model(
        chat_turn_receipts=[second_turn, first_turn],
        chat_handoff_receipts=[action_receipt],
    )

    create_action = next(
        item for item in read_model["outcomes"] if item["outcome_kind"] == "create_action"
    )
    remember_this = next(
        item for item in read_model["outcomes"] if item["outcome_kind"] == "remember_this"
    )
    assert create_action["source_ref"] == first_turn["turn_ref"]
    assert create_action["proposal_ref"] == action_receipt["created_ref"]
    assert remember_this["source_ref"] == second_turn["turn_ref"]
    _assert_chat_to_loop(read_model)


def test_chat_to_loop_handoff_cli_is_read_only_and_redacted(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.record_chat_turn_receipt(
        request=_chat_turn_request(),
        idempotency_key_ref="idempotency-ref:chat-to-loop-turn",
    )
    repo.record_chat_turn_receipt(
        request=_chat_turn_request(
            turn_ref="chat-turn:product-loop-009-second",
            safe_summary_ref="safe-summary-ref:chat-to-loop-test-second",
        ),
        idempotency_key_ref="idempotency-ref:chat-to-loop-turn-second",
    )
    repo.chat_to_loop_handoff()
    state_dir = tmp_path / "founder_loop"
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_chat_to_loop_handoff.py"),
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
    assert payload["contract_ref"] == CHAT_TO_LOOP_HANDOFF_CONTRACT_REF
    assert payload["command_ref"] == "repo-local-command:inspect-chat-to-loop-handoff"
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["proposal_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["direct_memory_write_authorized"] is False
    assert payload["context_injection_authorized"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["production_authority_enabled"] is False
    _assert_chat_to_loop(payload["chat_to_loop_handoff_read_model"])
    assert payload["chat_to_loop_handoff_read_model"]["turn_receipt_count"] == 2

    limited_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_chat_to_loop_handoff.py"),
            "--state-dir",
            str(state_dir),
            "--limit",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    limited_payload = json.loads(limited_result.stdout)
    _assert_chat_to_loop(limited_payload["chat_to_loop_handoff_read_model"])
    assert limited_payload["chat_to_loop_handoff_read_model"][
        "turn_receipt_count"
    ] == 1

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_chat_to_loop_handoff.py"),
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
    _assert_chat_to_loop(missing_payload["chat_to_loop_handoff_read_model"])
