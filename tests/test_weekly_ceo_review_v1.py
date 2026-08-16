from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.weekly_ceo_review import (
    WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
    WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE,
    WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS,
    WeeklyCeoReviewV1ReadModel,
    build_weekly_ceo_review_v1_read_model,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _assert_weekly_ceo_review_v1(read_model: dict[str, Any]) -> None:
    assert read_model["schema_version"] == "product-loop-008-weekly-ceo-review.v1"
    assert read_model["contract_ref"] == WEEKLY_CEO_REVIEW_V1_CONTRACT_REF
    assert read_model["source"] == WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_review_artifact_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["safe_summary_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["evidence_backed"] is True
    assert read_model["blocked_authority_refs"]
    assert set(WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_authority_refs"]
    )
    for field in [
        "completed_refs",
        "deferred_refs",
        "rejected_refs",
        "blocked_refs",
        "stale_refs",
        "unresolved_refs",
        "carry_forward_refs",
        "next_week_priority_refs",
        "action_decision_refs",
        "memory_decision_refs",
        "follow_up_refs",
        "evidence_event_refs",
        "evidence_refs",
        "receipt_refs",
        "missing_source_refs",
    ]:
        assert isinstance(read_model[field], list)
    assert read_model["completed_count"] == len(read_model["completed_refs"])
    assert read_model["deferred_count"] == len(read_model["deferred_refs"])
    assert read_model["rejected_count"] == len(read_model["rejected_refs"])
    assert read_model["blocked_count"] == len(read_model["blocked_refs"])
    assert read_model["stale_count"] == len(read_model["stale_refs"])
    assert read_model["unresolved_count"] == len(read_model["unresolved_refs"])
    assert read_model["action_decision_count"] == len(
        read_model["action_decision_refs"]
    )
    assert read_model["memory_decision_count"] == len(
        read_model["memory_decision_refs"]
    )
    assert read_model["follow_up_count"] == len(read_model["follow_up_refs"])
    assert read_model["evidence_event_count"] == len(read_model["evidence_event_refs"])
    assert all(
        ref.startswith("evidence-event:")
        for ref in read_model["evidence_event_refs"]
    )
    for flag in [
        "raw_logs_included",
        "prompt_content_included",
        "response_content_included",
        "provider_exchange_content_included",
        "connector_read_enabled",
        "connector_runtime_enabled",
        "connector_write_enabled",
        "email_calendar_fetch_enabled",
        "live_web_enabled",
        "model_summary_enabled",
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "automatic_memory_write_authorized",
        "context_injection_authorized",
        "action_execution_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "public_beta_claim_enabled",
        "production_claim_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False


def test_weekly_ceo_review_v1_surfaces_receipt_backed_safe_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    action_receipt = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="defer",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:setup-assistant-hardening"
            ),
            decision_reason_ref="decision-reason-ref:weekly-review-action-defer"
        ),
        idempotency_key_ref="idempotency-ref:weekly-review-action-defer",
    )
    memory_receipt = repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision="defer",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:weekly-review-test",
            source_refs=["source-ref:manual-note:weekly-review-test"],
            evidence_refs=["evidence-ref:memory-review:weekly-review-test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:weekly-review-memory-defer",
    )

    today = repo.today_summary()
    briefing = repo.morning_briefing()
    weekly = repo.weekly_ceo_review(limit=6)
    read_model = weekly["weekly_ceo_review_v1_read_model"]

    assert today["weekly_ceo_review_v1_contract_ref"] == (
        WEEKLY_CEO_REVIEW_V1_CONTRACT_REF
    )
    assert briefing["weekly_ceo_review_v1_contract_ref"] == (
        WEEKLY_CEO_REVIEW_V1_CONTRACT_REF
    )
    assert today["weekly_ceo_review_v1_read_model"] == read_model
    _assert_weekly_ceo_review_v1(read_model)
    assert action_receipt["receipt_ref"] in read_model["action_decision_refs"]
    assert memory_receipt["receipt_ref"] in read_model["memory_decision_refs"]
    assert memory_receipt["receipt_ref"] in read_model["receipt_refs"]
    assert read_model["evidence_event_refs"]
    assert read_model["unresolved_refs"]
    assert weekly["read_only"] is True
    assert weekly["raw_content_included"] is False
    assert weekly["model_summary_enabled"] is False
    assert weekly["production_authority_enabled"] is False


def test_weekly_ceo_review_v1_rejects_authority_and_raw_content(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.weekly_ceo_review()["weekly_ceo_review_v1_read_model"]

    payload = dict(read_model)
    payload["model_summary_enabled"] = True
    with pytest.raises(ValidationError, match="model_summary_enabled"):
        WeeklyCeoReviewV1ReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw response material."
    with pytest.raises(ValidationError, match="unsafe/private content"):
        WeeklyCeoReviewV1ReadModel(**payload)

    payload = dict(read_model)
    payload["contract_ref"] = "contract-ref:product-loop-008-other:v1"
    with pytest.raises(ValidationError, match="contract ref"):
        WeeklyCeoReviewV1ReadModel(**payload)

    payload = dict(read_model)
    payload["schema_version"] = "product-loop-008-other.v1"
    with pytest.raises(ValidationError, match="schema version"):
        WeeklyCeoReviewV1ReadModel(**payload)

    for unsafe_ref in (
        "evidence-ref:alice@example.com",
        "evidence-ref:workstation.local",
        "evidence-ref:relative/path/project",
    ):
        payload = dict(read_model)
        payload["evidence_refs"] = [unsafe_ref]
        with pytest.raises(ValidationError, match="unsafe ref"):
            WeeklyCeoReviewV1ReadModel(**payload)

    payload = dict(read_model)
    payload["completed_count"] = len(payload["completed_refs"]) + 1
    with pytest.raises(ValidationError, match="completed_count"):
        WeeklyCeoReviewV1ReadModel(**payload)


def test_weekly_ceo_review_v1_excludes_planned_receipts_from_completed_refs() -> None:
    read_model = build_weekly_ceo_review_v1_read_model(
        weekly_review_narrative={
            "deferred_refs": [],
            "rejected_refs": [],
            "blocked_refs": [],
            "stale_refs": [],
            "missing_source_refs": [],
            "carry_forward_refs": [],
            "next_week_priority_refs": [],
            "evidence_refs": ["evidence-ref:weekly-review:planned-receipt-test"],
        },
        actions=[
            {
                "item_ref": "approved-only",
                "status": "approved",
                "receipt_refs": ["receipt:action:approved-only"],
            },
            {
                "item_ref": "completed-plan-only",
                "status": "completed",
                "receipt_refs": ["receipt-plan:action:completed-plan-only"],
                "receipt_visibility": {
                    "decision_receipt_ref": "receipt-plan:action:completed-plan-only"
                },
            },
            {
                "item_ref": "completed-durable",
                "status": "completed",
                "receipt_refs": ["receipt:action:completed-durable"],
            },
        ],
        memory_review_decisions=[],
        follow_up_tracker={},
        evidence_timeline=[],
        source_readiness_items=[],
        evidence_event_refs=["evidence-event:weekly-review:planned-receipt-test"],
    )

    assert read_model["completed_refs"] == [
        "action-status-ref:completed-durable:completed"
    ]
    assert "receipt-plan:action:completed-plan-only" not in read_model["receipt_refs"]
    assert set(read_model["receipt_refs"]) == {
        "receipt:action:approved-only",
        "receipt:action:completed-durable",
    }


def test_weekly_ceo_review_cli_is_read_only_and_redacted(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.weekly_ceo_review()
    state_dir = tmp_path / "founder_loop"
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_weekly_ceo_review.py"),
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
    assert payload["contract_ref"] == WEEKLY_CEO_REVIEW_V1_CONTRACT_REF
    assert payload["command_ref"] == "repo-local-command:inspect-weekly-ceo-review"
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["safe_summary_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["provider_exchange_content_included"] is False
    assert payload["connector_runtime_enabled"] is False
    assert payload["model_summary_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["runtime_model_call_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["production_claim_enabled"] is False
    assert payload["production_authority_enabled"] is False
    _assert_weekly_ceo_review_v1(payload["weekly_ceo_review_v1_read_model"])

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_weekly_ceo_review.py"),
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
