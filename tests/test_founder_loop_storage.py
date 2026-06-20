import json

import pytest

from ultimate_ai_agent.core.storage import (
    FOUNDER_LOOP_SCHEMA_VERSION,
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    JsonlLogKind,
)
from ultimate_ai_agent.core.storage.founder_loop import FounderLoopActionRecord


def test_founder_loop_repository_seeds_safe_storage_backed_loop(tmp_path):
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    status = repo.storage_status()
    today = repo.today_summary()
    inbox = repo.actions_inbox()
    briefing = repo.morning_briefing()

    assert status["schema_version"] == FOUNDER_LOOP_SCHEMA_VERSION
    assert status["storage_ref"] == "founder-loop-storage:local-sqlite-jsonl"
    assert status["safe_refs_only"] is True
    assert status["raw_content_stored"] is False
    assert status["postgres_sync_required"] is False
    assert status["postgres_sync_status"] == "adapter_boundary_only"
    assert status["counts"]["action_inbox"] >= 1
    assert today["status"] == "storage_backed_partial_loop"
    assert today["actions"]
    assert inbox["mutating_controls_enabled"] is False
    assert briefing["items"]

    serialized = json.dumps(
        {"status": status, "today": today, "inbox": inbox, "briefing": briefing},
        sort_keys=True,
    ).lower()
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
    ]:
        assert forbidden not in serialized


def test_founder_loop_repository_crud_and_idempotency_denial(tmp_path):
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_action(
        FounderLoopActionRecord(
            item_ref="founder-action:test-review",
            title="Review storage-backed action",
            safe_summary="Bounded summary for a review-only action inbox item.",
            surface="Actions",
            evidence_refs=["evidence-ref:founder-loop:test-review"],
        )
    )
    repo.record_idempotency_key(
        key_ref="idempotency-ref:founder-loop:test",
        scope_ref="approval-scope:founder-loop:test",
        receipt_ref="receipt-ref:founder-loop:test",
    )

    inbox = repo.actions_inbox()
    assert inbox["items"][0]["item_ref"] == "founder-action:test-review"
    assert repo.storage_status()["counts"]["idempotency_keys"] == 1

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_idempotency_key(
            key_ref="idempotency-ref:founder-loop:test",
            scope_ref="approval-scope:founder-loop:test",
            receipt_ref="receipt-ref:founder-loop:test",
        )


def test_founder_loop_jsonl_logs_are_append_only_and_redacted(tmp_path):
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    result = repo.append_log(
        JsonlLogKind.audit,
        {
            "event_ref": "founder-loop-event:audit-test",
            "safe_summary": "Redacted audit event for storage verifier.",
            "evidence_refs": ["evidence-ref:founder-loop:audit-test"],
        },
    )

    assert result == {
        "log_ref": "founder-loop-log:audit",
        "event_ref": "founder-loop-event:audit-test",
    }
    log_path = tmp_path / "founder_loop" / "logs" / "audit.jsonl"
    first = log_path.read_text(encoding="utf-8")
    repo.append_log(
        JsonlLogKind.audit,
        {
            "event_ref": "founder-loop-event:audit-test-two",
            "safe_summary": "Second redacted audit event for storage verifier.",
            "evidence_refs": ["evidence-ref:founder-loop:audit-test-two"],
        },
    )
    second = log_path.read_text(encoding="utf-8")

    assert second.startswith(first)
    assert len(second.splitlines()) == 2
    assert str(tmp_path) not in second
    assert "raw_prompt" not in second
    assert "provider_payload" not in second


def test_founder_loop_storage_rejects_unsafe_payload_language(tmp_path):
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    with pytest.raises(ValueError):
        repo.upsert_action(
            FounderLoopActionRecord(
                item_ref="founder-action:unsafe",
                title="Unsafe action",
                safe_summary="This includes raw_prompt material and must be denied.",
                surface="Actions",
                evidence_refs=["evidence-ref:founder-loop:unsafe"],
            )
        )
