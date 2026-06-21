from pathlib import Path
import json

import pytest

from ultimate_ai_agent.core.storage import (
    FOUNDER_LOOP_SCHEMA_VERSION,
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    JsonlLogKind,
)
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopActionRecord,
    FounderLoopBriefingRecord,
    FounderLoopEvidenceTimelineItem,
    FounderLoopMemoryReviewRecord,
)


def test_founder_loop_repository_seeds_safe_storage_backed_loop(tmp_path: Path) -> None:
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
    assert inbox["route_ref"] == "/control-center/actions/inbox"
    assert "GET /control-center/storage/status" in inbox["read_only_route_refs"]
    assert "capability-ref:local-approval-authority" in inbox["local_prerequisite_refs"]
    assert "no_approval_grant_capture_route" in inbox["blocked_states"]
    assert briefing["items"]
    assert briefing["route_ref"] == "/control-center/morning-briefing/summary"
    assert "GET /control-center/storage/status" in briefing["read_only_route_refs"]
    assert "contract-ref:email-read-only-missing" in briefing["missing_contract_refs"]
    assert briefing["source_readiness"] == (
        "blocked_missing_email_calendar_notification_contracts"
    )
    assert briefing["bounded_preview_only"] is True
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert "no_background_refresh" in briefing["blocked_states"]
    assert "no_notification_delivery" in briefing["blocked_states"]
    assert today["memory_review_route_ref"] == "/memory"
    assert (
        today["memory_review_backend_route_ref"]
        == "GET /control-center/today/summary"
    )
    assert today["memory_review_status"] == "storage_backed_review_queue"
    assert today["memory_write_enabled"] is False
    assert today["memory_delete_enabled"] is False
    assert today["context_injection_enabled"] is False
    assert (
        "contract-ref:memory-write-policy-binding-missing"
        in today["memory_review_missing_contract_refs"]
    )
    assert (
        "contract-ref:memory-retention-delete-missing"
        in today["memory_review_missing_contract_refs"]
    )
    assert "no_memory_write" in today["memory_review_blocked_states"]
    assert "no_context_injection" in today["memory_review_blocked_states"]
    assert "no_model_provider_authority" in today["memory_review_blocked_states"]
    assert today["evidence_timeline_route_ref"] == "/evidence"
    assert (
        today["evidence_timeline_backend_route_ref"]
        == "GET /control-center/today/summary"
    )
    assert today["evidence_timeline_status"] == "storage_backed_redacted_refs"
    assert "safe-ref and redacted-summary only" in (
        today["evidence_timeline_authority_boundary"]
    )
    assert "no_raw_evidence_display" in today["evidence_timeline_blocked_states"]
    assert "no_rollback_execution" in today["evidence_timeline_blocked_states"]
    assert "approval_refs_are_identifiers_only" in (
        today["evidence_timeline_blocked_states"]
    )
    assert today["sections"]["evidence_timeline_count"] == len(
        today["evidence_timeline"]
    )

    approval_item = next(
        item
        for item in inbox["items"]
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    assert approval_item["risk_class"] == "high"
    assert approval_item["approval_required"] is True
    assert (
        approval_item["approval_envelope_ref"]
        == "approval-envelope:founder-loop:setup-assistant-hardening"
    )
    assert approval_item["approval_envelope_status"] == "dry_run_ref_available"
    assert (
        approval_item["state_change_readiness"]
        == "blocked_pending_scoped_mutation_contract"
    )
    assert approval_item["receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert approval_item["audit_refs"] == [
        "audit-plan:founder-loop:setup-assistant-hardening"
    ]
    assert (
        approval_item["idempotency_key_ref"]
        == "idempotency-ref:founder-loop:setup-assistant-hardening"
    )
    assert approval_item["rollback_ref"] == "rollback-plan:founder-loop:setup-assistant-hardening"
    assert approval_item["safe_disable_ref"] == "safe-disable:founder-loop:setup-assistant-hardening"
    assert "scoped state-change milestone" in approval_item["next_safe_action"]

    briefing_item = next(
        item
        for item in briefing["items"]
        if item["briefing_ref"] == "briefing:api-boundary-modularization"
    )
    assert briefing_item["priority"] == "high"
    assert briefing_item["source_readiness"] == "local_status_refs_only"
    assert briefing_item["source_refs"] == ["source-ref:control-center-route-status"]
    assert "contract-ref:calendar-read-only-missing" in briefing_item["missing_contract_refs"]
    assert "no_background_refresh" in briefing_item["blocked_states"]
    assert briefing_item["stale_state"] == "recheck_route_status_before_briefing_use"
    assert "source evidence is bound" in briefing_item["evidence_gap"]
    assert "define source contracts" in briefing_item["next_safe_action"]

    memory_item = next(
        item
        for item in today["memory_review_queue"]
        if item["review_ref"] == "memory-review:founder-loop-preferences"
    )
    assert memory_item["candidate_kind"] == "operator_preference"
    assert memory_item["priority"] == "high"
    assert memory_item["review_state"] == "review_needed"
    assert memory_item["side_effect_class"] == "local_dev_workspace_only"
    assert (
        "writes, deletes, and context injection remain unscoped"
        in memory_item["authority_boundary"]
    )
    assert memory_item["provenance_refs"] == [
        "provenance-ref:founder-loop-memory:preferences"
    ]
    assert memory_item["source_refs"] == ["source-ref:founder-loop-storage"]
    assert (
        "contract-ref:memory-review-decision-capture-missing"
        in memory_item["missing_contract_refs"]
    )
    assert (
        memory_item["correction_posture"]
        == "correction_requires_scoped_memory_write_contract"
    )
    assert (
        memory_item["rejection_posture"]
        == "rejection_is_review_state_only_until_capture_contract"
    )
    assert memory_item["retention_posture"] == "retention_policy_not_bound"
    assert memory_item["delete_posture"] == "delete_execution_not_scoped"
    assert memory_item["confidence_posture"] == "safe_summary_unverified"
    assert memory_item["stale_state"] == "recheck_source_refs_before_memory_use"
    assert "no_raw_source_display" in memory_item["blocked_states"]
    assert "scoped memory policy milestone" in memory_item["next_safe_action"]

    timeline = today["evidence_timeline"]
    timeline_kinds = {item["item_kind"] for item in timeline}
    assert "receipt_audit_rollback_ref" in timeline_kinds
    assert "plan_evidence_ref" in timeline_kinds
    assert "memory_review_evidence_ref" in timeline_kinds
    assert "source_readiness_evidence_ref" in timeline_kinds
    assert "foundation_gate_latency_ref" in timeline_kinds

    action_timeline_item = next(
        item
        for item in timeline
        if item["timeline_item_ref"]
        == "evidence-timeline:action/founder-action/setup-assistant-hardening"
    )
    assert action_timeline_item["receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert action_timeline_item["audit_refs"] == [
        "audit-plan:founder-loop:setup-assistant-hardening"
    ]
    assert action_timeline_item["rollback_refs"] == [
        "rollback-plan:founder-loop:setup-assistant-hardening"
    ]
    assert action_timeline_item["redaction_status"] == "redacted_summary_only"
    assert "GET /control-center/actions/inbox" in (
        action_timeline_item["related_route_refs"]
    )
    assert "mutation stays blocked" in action_timeline_item["safe_summary"]

    memory_timeline_item = next(
        item
        for item in timeline
        if item["item_kind"] == "memory_review_evidence_ref"
    )
    assert memory_timeline_item["approval_posture"] == (
        "memory_review_refs_do_not_authorize_writes"
    )
    assert "Memory is not truth" in memory_timeline_item["safe_summary"]
    assert "memory_write_or_delete_rollback_not_scoped" in (
        memory_timeline_item["rollback_blockers"]
    )

    foundation_timeline_item = next(
        item
        for item in timeline
        if item["item_kind"] == "foundation_gate_latency_ref"
    )
    assert foundation_timeline_item["foundation_gate_refs"] == [
        "foundation-gate-ref:latest-report"
    ]
    assert "latency-ref:foundation-gate:latest-report" in (
        foundation_timeline_item["latency_refs"]
    )
    assert "foundation_gate_refs_not_production_authority" in (
        foundation_timeline_item["blocked_states"]
    )
    assert foundation_timeline_item["rollback_blockers"] == [
        "rollback_execution_not_scoped"
    ]

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


def test_founder_loop_repository_crud_and_idempotency_denial(tmp_path: Path) -> None:
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
    assert inbox["items"][0]["approval_envelope_status"] == "missing_until_scoped_contract"
    assert inbox["items"][0]["state_change_readiness"] == "blocked_missing_backend_contract"
    assert inbox["items"][0]["receipt_refs"] == []
    assert inbox["items"][0]["audit_refs"] == []
    assert inbox["items"][0]["idempotency_key_ref"] is None
    assert inbox["items"][0]["rollback_ref"] is None
    assert inbox["items"][0]["safe_disable_ref"] is None
    assert repo.storage_status()["counts"]["idempotency_keys"] == 1

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_idempotency_key(
            key_ref="idempotency-ref:founder-loop:test",
            scope_ref="approval-scope:founder-loop:test",
            receipt_ref="receipt-ref:founder-loop:test",
        )


def test_founder_loop_briefing_defaults_are_blocked_and_read_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_briefing_item(
        FounderLoopBriefingRecord(
            briefing_ref="briefing:test-review",
            title="Briefing review",
            safe_summary="Bounded briefing summary for a local review-only item.",
            evidence_refs=["evidence-ref:founder-loop:test-briefing"],
        )
    )

    briefing = repo.morning_briefing()
    item = briefing["items"][0]
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert item["briefing_ref"] == "briefing:test-review"
    assert item["priority"] == "medium"
    assert item["source_readiness"] == "blocked_missing_source_contract"
    assert item["source_refs"] == []
    assert item["missing_contract_refs"] == []
    assert item["blocked_states"] == []
    assert item["stale_state"] == "recheck_required_before_source_contract"
    assert "source connector evidence" in item["evidence_gap"]
    assert "read-only source contracts" in item["next_safe_action"]


def test_founder_loop_memory_review_defaults_are_review_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_memory_review(
        FounderLoopMemoryReviewRecord(
            review_ref="memory-review:test-review",
            title="Memory review",
            safe_summary="Bounded memory review summary for a local review-only item.",
            evidence_refs=["evidence-ref:founder-loop:test-memory"],
        )
    )

    today = repo.today_summary()
    item = today["memory_review_queue"][0]
    assert today["memory_review_route_ref"] == "/memory"
    assert today["memory_write_enabled"] is False
    assert today["memory_delete_enabled"] is False
    assert today["context_injection_enabled"] is False
    assert "contract-ref:context-injection-missing" in (
        today["memory_review_missing_contract_refs"]
    )
    assert "no_background_sync" in today["memory_review_blocked_states"]
    assert item["review_ref"] == "memory-review:test-review"
    assert item["candidate_kind"] == "preference"
    assert item["priority"] == "medium"
    assert item["review_state"] == "review_needed"
    assert item["side_effect_class"] == "local_dev_workspace_only"
    assert "remain unscoped" in item["authority_boundary"]
    assert item["provenance_refs"] == []
    assert item["source_refs"] == []
    assert item["missing_contract_refs"] == []
    assert (
        item["correction_posture"]
        == "correction_requires_scoped_memory_write_contract"
    )
    assert item["rejection_posture"] == "rejection_is_review_state_only"
    assert item["retention_posture"] == "retention_policy_not_bound"
    assert item["delete_posture"] == "delete_execution_not_scoped"
    assert item["confidence_posture"] == "safe_summary_unverified"
    assert item["stale_state"] == "recheck_source_refs_before_memory_use"
    assert item["blocked_states"] == []
    assert "scoped memory policy milestone" in item["next_safe_action"]


def test_founder_loop_jsonl_logs_are_append_only_and_redacted(tmp_path: Path) -> None:
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


def test_founder_loop_storage_rejects_unsafe_payload_language(tmp_path: Path) -> None:
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


def test_founder_loop_evidence_timeline_rejects_unsafe_content() -> None:
    with pytest.raises(ValueError):
        FounderLoopEvidenceTimelineItem(
            timeline_item_ref="evidence-timeline:unsafe/test",
            item_kind="unsafe_evidence_ref",
            title="Unsafe evidence",
            safe_summary="This includes raw_prompt material and must be denied.",
            source_refs=["evidence-ref:founder-loop:unsafe"],
            status_refs=["status-ref:founder-loop:unsafe"],
            authority_posture="Review-only evidence posture.",
            next_safe_action="Keep unsafe evidence blocked.",
        )
