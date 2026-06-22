from pathlib import Path
import json

import pytest

from ultimate_ai_agent.core.storage import (
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
    FOUNDER_LOOP_SCHEMA_VERSION,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    TODAY_PRODUCT_SPINE_CONTRACT_REF,
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


HISTORY_KEYS = {
    "proposed",
    "approved",
    "happened",
    "changed",
    "undoable",
    "stale",
    "blocked",
}


def _history_answers() -> dict[str, dict[str, object]]:
    return {
        key: {
            "question": f"What is {key}?",
            "answer": f"Safe redacted answer for {key}.",
            "refs": [f"status-ref:test-{key}"],
            "status": "present",
        }
        for key in HISTORY_KEYS
    }


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
    assert today["product_spine_contract_ref"] == TODAY_PRODUCT_SPINE_CONTRACT_REF
    assert (
        today["evidence_history_contract_ref"] == EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF
    )
    assert (
        today["memory_source_provenance_contract_ref"]
        == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    assert (
        today["memory_review_decision_contract_ref"]
        == MEMORY_REVIEW_DECISION_CONTRACT_REF
    )
    assert (
        today["business_memory_quality_contract_ref"]
        == BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    )
    assert (
        today["plans_action_envelope_contract_ref"]
        == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert [
        row["review_action"]
        for row in today["plans_action_envelope_review_postures"]
    ] == ["approve", "edit", "reject", "defer"]
    assert "scope_ref" in today["plans_action_envelope_required_ref_fields"]
    assert (
        "blocked-state:no-action-execution"
        in today["plans_action_envelope_required_blocked_refs"]
    )
    assert (
        today["plans_action_envelope_authority_posture"][
            "approval_grant_capture_enabled"
        ]
        is False
    )
    assert (
        today["plans_action_envelope_authority_posture"]["action_execution_enabled"]
        is False
    )
    assert (
        today["plans_action_envelope_status"]
        == "implemented_reviewable_action_envelopes_execution_blocked"
    )
    assert today["memory_source_required_kinds"] == [
        "manual_note",
        "external_assistant_review_summary",
        "local_chat_summary",
        "local_coding_summary",
        "task_plan",
        "action_proposal",
        "evidence_timeline_ref",
        "read_only_calendar_metadata_ref",
        "read_only_email_metadata_ref",
        "crm_lite_business_record",
    ]
    assert len(today["memory_source_policy"]) == len(
        today["memory_source_required_kinds"]
    )
    for source_policy in today["memory_source_policy"]:
        assert source_policy["review_required"] is True
        assert source_policy["trusted_without_review"] is False
        assert source_policy["source_payload_storage_allowed"] is False
        assert source_policy["automatic_memory_write_allowed"] is False
        assert source_policy["context_injection_allowed"] is False
        assert source_policy["connector_runtime_allowed"] is False
        assert source_policy["provider_or_model_authority_allowed"] is False
        assert source_policy["account_auth_allowed"] is False
    assert (
        today["memory_source_review_posture"]["review_required_before_recall"] is True
    )
    assert today["memory_source_review_posture"]["connector_runtime_enabled"] is False
    assert today["memory_source_review_posture"]["account_auth_enabled"] is False
    assert (
        today["memory_source_review_posture"]["production_authority_enabled"] is False
    )
    assert [
        row["decision_state"] for row in today["memory_review_decision_states"]
    ] == [
        "accept",
        "correct",
        "reject",
        "defer",
        "merge",
        "supersede",
        "forget_request",
    ]
    assert today["memory_review_decision_required_ref_fields"] == [
        "actor_ref",
        "source_refs",
        "provenance_refs",
        "evidence_refs",
        "stale_state",
        "retention_posture",
        "audit_refs",
        "receipt_refs",
        "blocked_state_refs",
    ]
    assert today["memory_review_decision_authority_posture"]["review_only"] is True
    assert (
        today["memory_review_decision_authority_posture"]["memory_write_authorized"]
        is False
    )
    assert (
        today["memory_review_decision_authority_posture"]["accepted_as_recall"] is False
    )
    assert set(today["evidence_history_required_states"]) == HISTORY_KEYS
    assert {
        item["key"]
        for item in today["evidence_history_required_questions"]
        if item["required"] is True
    } == HISTORY_KEYS
    surface_bindings = {
        item["surface"]: item for item in today["evidence_history_surface_bindings"]
    }
    assert {"Actions", "Plans", "Memory", "Chat", "Code"} <= set(surface_bindings)
    assert (
        surface_bindings["Chat"]["current_status"] == "planned_blocked_until_uaa_p1_074"
    )
    assert (
        surface_bindings["Code"]["current_status"] == "planned_blocked_until_uaa_p1_075"
    )
    assert today["required_loop_surfaces"] == [
        "Today",
        "Actions",
        "Evidence",
        "Memory",
    ]
    assert {
        item["signal"]
        for item in today["required_today_signals"]
        if item["required"] is True
    } == {
        "priorities",
        "blockers",
        "follow_ups",
        "plan_action_state",
        "memory_review_count",
        "stale_source_posture",
        "next_safe_actions",
    }
    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    assert {
        "Today",
        "Actions",
        "Plans",
        "Memory",
        "Evidence",
        "Morning Briefing",
        "Chat",
        "Code",
    } <= set(module_feeds)
    for feed in module_feeds.values():
        assert feed["standalone_complete_allowed"] is False
        assert len(feed["required_loop_outputs"]) == 4
        assert feed["current_feed_refs"]
    assert (
        module_feeds["Memory"]["status"]
        == "implemented_review_queue_decision_and_quality_metadata_contract"
    )
    assert (
        MEMORY_REVIEW_DECISION_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert (
        BUSINESS_MEMORY_QUALITY_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert today["module_completion_contract"] == {
        "visibility_requirement": (
            "Module state must be visible in Today, Actions, Evidence, and "
            "Memory before completion can be claimed."
        ),
        "visibility_is_sufficient_for_completion": False,
        "standalone_module_complete_allowed": False,
        "required_done_gates": [
            "definition_of_done",
            "schema_or_typed_contract",
            "focused_tests",
            "redaction_checks",
            "policy_approval_boundary",
            "openapi_api_manifest_when_routes_change",
            "cli_or_repo_local_inspection_path",
        ],
    }
    assert today["plan_action_state"] == {
        "action_count": len(today["actions"]),
        "plan_count": len(today["plans"]),
        "approval_required_before_mutation": True,
        "mutating_controls_enabled": False,
        "execution_authorized": False,
        "action_envelope_contract_status": (
            "implemented_reviewable_action_envelopes_execution_blocked"
        ),
        "action_envelope_contract_ref": PLANS_ACTION_ENVELOPE_CONTRACT_REF,
        "review_actions": ["approve", "edit", "reject", "defer"],
        "approval_grant_capture_enabled": False,
        "state_change_enabled": False,
    }
    assert today["stale_source_posture"]["source_refresh_enabled"] is False
    assert today["stale_source_posture"]["connector_runtime_enabled"] is False
    assert today["stale_source_posture"]["stale_state_refs"]
    assert today["priority_refs"]
    assert today["blocker_refs"]
    assert today["follow_up_refs"]
    assert today["next_safe_actions"]
    assert today["actions"]
    assert inbox["mutating_controls_enabled"] is False
    assert inbox["action_envelope_contract_ref"] == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    assert [
        row["review_action"] for row in inbox["action_envelope_review_postures"]
    ] == ["approve", "edit", "reject", "defer"]
    assert "scope_ref" in inbox["action_envelope_required_ref_fields"]
    assert inbox["action_envelope_authority_posture"]["action_execution_enabled"] is False
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
        today["memory_review_backend_route_ref"] == "GET /control-center/today/summary"
    )
    assert today["memory_review_status"] == (
        "storage_backed_review_queue_with_business_quality_metadata"
    )
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
    assert (
        "contract-ref:business-memory-quality-controls-missing"
        not in (today["memory_review_missing_contract_refs"])
    )
    assert "no_memory_write" in today["memory_review_blocked_states"]
    assert "no_context_injection" in today["memory_review_blocked_states"]
    assert "no_external_crm_write" in today["memory_review_blocked_states"]
    assert "no_account_sync" in today["memory_review_blocked_states"]
    assert "no_automatic_recall" in today["memory_review_blocked_states"]
    assert "no_model_provider_authority" in today["memory_review_blocked_states"]
    assert today["evidence_timeline_route_ref"] == "/evidence"
    assert (
        today["evidence_timeline_backend_route_ref"]
        == "GET /control-center/today/summary"
    )
    assert (
        today["evidence_timeline_status"]
        == "storage_backed_redacted_history_grammar_refs"
    )
    assert (
        "safe-ref and redacted-summary only"
        in (today["evidence_timeline_authority_boundary"])
    )
    assert "no_raw_evidence_display" in today["evidence_timeline_blocked_states"]
    assert "no_rollback_execution" in today["evidence_timeline_blocked_states"]
    assert (
        "approval_refs_are_identifiers_only"
        in (today["evidence_timeline_blocked_states"])
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
    assert (
        approval_item["rollback_ref"]
        == "rollback-plan:founder-loop:setup-assistant-hardening"
    )
    assert (
        approval_item["safe_disable_ref"]
        == "safe-disable:founder-loop:setup-assistant-hardening"
    )
    assert "scoped state-change milestone" in approval_item["next_safe_action"]
    assert (
        approval_item["action_envelope_contract_ref"]
        == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert approval_item["action_envelope_ref"].startswith("action-envelope:plans:")
    assert approval_item["action_scope_ref"].startswith(
        "scope-ref:plans-action-envelope:"
    )
    assert approval_item["action_review_actions"] == [
        "approve",
        "edit",
        "reject",
        "defer",
    ]
    assert approval_item["action_expected_receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert (
        "blocked-state:no-action-execution"
        in approval_item["action_blocked_state_refs"]
    )
    assert approval_item["action_envelope_execution_enabled"] is False
    assert approval_item["action_envelope_grant_capture_enabled"] is False
    assert approval_item["action_envelope_raw_content_included"] is False

    plan_item = next(
        item
        for item in today["plans"]
        if item["plan_ref"] == "plan-summary:founder-loop-v1"
    )
    assert plan_item["action_envelope_contract_ref"] == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    assert (
        plan_item["action_envelope_ref"]
        == "action-envelope:plans:plan-summary-founder-loop-v1"
    )
    assert plan_item["scope_ref"] == (
        "scope-ref:plans-action-envelope:plan-summary-founder-loop-v1"
    )
    assert plan_item["approval_requirement_ref"] == (
        "approval-requirement:plans-action-envelope:plan-summary-founder-loop-v1"
    )
    assert plan_item["review_actions"] == ["approve", "edit", "reject", "defer"]
    assert plan_item["expected_receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert (
        plan_item["idempotency_key_ref"]
        == "idempotency-ref:plans-action-envelope:plan-summary-founder-loop-v1"
    )
    assert (
        "blocked-state:no-approval-grant-capture"
        in plan_item["blocked_state_refs"]
    )
    assert plan_item["action_execution_enabled"] is False
    assert plan_item["approval_grant_capture_enabled"] is False
    assert plan_item["raw_content_included"] is False

    briefing_item = next(
        item
        for item in briefing["items"]
        if item["briefing_ref"] == "briefing:api-boundary-modularization"
    )
    assert briefing_item["priority"] == "high"
    assert briefing_item["source_readiness"] == "local_status_refs_only"
    assert briefing_item["source_refs"] == ["source-ref:control-center-route-status"]
    assert (
        "contract-ref:calendar-read-only-missing"
        in briefing_item["missing_contract_refs"]
    )
    assert "no_background_refresh" in briefing_item["blocked_states"]
    assert briefing_item["stale_state"] == "recheck_route_status_before_briefing_use"
    assert "source evidence is bound" in briefing_item["evidence_gap"]
    assert "define source contracts" in briefing_item["next_safe_action"]

    memory_item = next(
        item
        for item in today["memory_review_queue"]
        if item["review_ref"] == "memory-review:founder-loop-preferences"
    )
    assert memory_item["candidate_kind"] == "preference"
    assert memory_item["priority"] == "high"
    assert memory_item["review_state"] == "review_needed"
    assert memory_item["side_effect_class"] == "local_dev_workspace_only"
    assert (
        "writes, deletes, and context injection remain unscoped"
        in memory_item["authority_boundary"]
    )
    assert memory_item["provenance_refs"] == [
        "provenance-ref:manual-note:founder-loop-preferences"
    ]
    assert memory_item["source_refs"] == ["source-ref:manual-note:founder-loop-storage"]
    assert memory_item["source_policy_ref"] == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    assert memory_item["source_kind"] == "manual_note"
    assert memory_item["source_kind_ref"] == "memory-source-kind:manual-note"
    assert memory_item["source_review_required"] is True
    assert memory_item["source_trust_posture"] == "untrusted_until_reviewed"
    assert memory_item["safe_summary_only"] is True
    assert memory_item["source_truth_authority"] is False
    assert memory_item["memory_write_authorized"] is False
    assert memory_item["automatic_memory_write_authorized"] is False
    assert memory_item["context_injection_authorized"] is False
    assert memory_item["connector_runtime_allowed"] is False
    assert memory_item["account_auth_enabled"] is False
    assert memory_item["provider_or_model_authority_allowed"] is False
    assert memory_item["public_beta_claim_enabled"] is False
    assert memory_item["public_distribution_claim_enabled"] is False
    assert memory_item["production_authority_enabled"] is False
    assert memory_item["accepted_as_truth"] is False
    assert memory_item["decision_contract_ref"] == MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert memory_item["available_decision_states"] == [
        "accept",
        "correct",
        "reject",
        "defer",
        "merge",
        "supersede",
        "forget_request",
    ]
    assert (
        memory_item["decision_capture_status"] == "review_needed_no_decision_captured"
    )
    assert memory_item["decision_actor_ref"] == (
        "actor-ref:local-operator-review-required"
    )
    assert memory_item["decision_source_provenance_contract_ref"] == (
        MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    assert memory_item["decision_source_kind"] == "manual_note"
    assert memory_item["decision_source_trust_posture"] == "untrusted_until_reviewed"
    assert memory_item["decision_redaction_status"] == "redacted_summary_only"
    assert memory_item["decision_review_only"] is True
    assert memory_item["memory_delete_authorized"] is False
    assert memory_item["memory_export_authorized"] is False
    assert memory_item["retention_execution_authorized"] is False
    assert (
        memory_item["business_memory_quality_contract_ref"]
        == BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    )
    assert memory_item["business_memory_candidate_kind"] == "preference"
    assert memory_item["business_memory_source_provenance_contract_ref"] == (
        MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    assert memory_item["business_memory_source_kind"] == "manual_note"
    assert memory_item["business_memory_source_trust_posture"] == (
        "untrusted_until_reviewed"
    )
    assert memory_item["business_memory_redaction_status"] == "redacted_summary_only"
    assert memory_item["business_memory_quality_state_refs"] == [
        "business-memory-quality:blocked",
        "business-memory-quality:low-confidence",
    ]
    assert memory_item["business_memory_safe_refs_only"] is True
    assert memory_item["business_memory_review_required_before_recall"] is True
    assert memory_item["business_memory_accepted_as_recall"] is False
    assert memory_item["business_memory_crm_write_authorized"] is False
    assert memory_item["business_memory_account_sync_authorized"] is False
    assert memory_item["business_memory_context_injection_authorized"] is False
    assert "blocked-state:no-connector-runtime" in (
        memory_item["business_memory_blocker_refs"]
    )
    assert "blocked-state:no-model-provider-authority" in (
        memory_item["business_memory_blocker_refs"]
    )
    assert memory_item["decision_audit_refs"]
    assert memory_item["decision_receipt_refs"]
    assert "blocked-state:no-memory-write" in memory_item["decision_blocked_state_refs"]
    assert (
        "blocked-state:no-memory-delete" in memory_item["decision_blocked_state_refs"]
    )
    assert (
        "blocked-state:no-memory-export" in memory_item["decision_blocked_state_refs"]
    )
    assert (
        "contract-ref:business-memory-quality-controls-missing"
        not in (memory_item["missing_contract_refs"])
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
    assert "plan_action_envelope_ref" in timeline_kinds
    assert "memory_review_evidence_ref" in timeline_kinds
    assert "source_readiness_evidence_ref" in timeline_kinds
    assert "foundation_gate_latency_ref" in timeline_kinds
    for item in timeline:
        assert item["history_contract_ref"] == EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF
        assert set(item["history_answers"]) == HISTORY_KEYS
        assert item["approval_ref_authority"] is False
        assert item["rollback_execution_enabled"] is False
        assert item["memory_truth_authority"] is False
        assert item["context_injection_authorized"] is False
        assert item["raw_evidence_included"] is False
        assert item["redaction_status"] in {"redacted_summary_only", "safe_refs_only"}
        for answer in item["history_answers"].values():
            assert answer["answer"]
            assert isinstance(answer["refs"], list)

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
    assert (
        "GET /control-center/actions/inbox"
        in (action_timeline_item["related_route_refs"])
    )
    assert "mutation stays blocked" in action_timeline_item["safe_summary"]
    assert (
        action_timeline_item["history_answers"]["approved"]["status"] == "posture_only"
    )
    assert (
        "identifiers, not authority"
        in (action_timeline_item["history_answers"]["approved"]["answer"])
    )
    assert (
        action_timeline_item["history_answers"]["undoable"]["status"] == "posture_only"
    )
    assert (
        "do not execute rollback"
        in (action_timeline_item["history_answers"]["undoable"]["answer"])
    )

    plan_timeline_item = next(
        item for item in timeline if item["item_kind"] == "plan_action_envelope_ref"
    )
    assert PLANS_ACTION_ENVELOPE_CONTRACT_REF in plan_timeline_item["status_refs"]
    assert (
        "action-envelope:plans:plan-summary-founder-loop-v1"
        in plan_timeline_item["status_refs"]
    )
    assert (
        "reviewable Action envelope"
        in plan_timeline_item["history_answers"]["proposed"]["answer"]
    )
    assert (
        "approval refs remain identifiers only"
        in plan_timeline_item["history_answers"]["approved"]["answer"]
    )
    assert plan_timeline_item["receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert plan_timeline_item["rollback_refs"] == [
        "rollback-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert "rollback_execution_not_scoped" in plan_timeline_item["rollback_blockers"]
    assert (
        "blocked-state:no-action-execution"
        in plan_timeline_item["blocked_states"]
    )

    memory_timeline_item = next(
        item for item in timeline if item["item_kind"] == "memory_review_evidence_ref"
    )
    assert memory_timeline_item["approval_posture"] == (
        "memory_review_refs_do_not_authorize_writes"
    )
    assert "Memory is not truth" in memory_timeline_item["safe_summary"]
    assert memory_timeline_item["history_answers"]["approved"]["status"] == "blocked"
    assert (
        "No memory write"
        in memory_timeline_item["history_answers"]["approved"]["answer"]
    )
    assert memory_timeline_item["memory_truth_authority"] is False
    assert memory_timeline_item["context_injection_authorized"] is False
    assert (
        "memory_write_or_delete_rollback_not_scoped"
        in (memory_timeline_item["rollback_blockers"])
    )

    foundation_timeline_item = next(
        item for item in timeline if item["item_kind"] == "foundation_gate_latency_ref"
    )
    assert foundation_timeline_item["foundation_gate_refs"] == [
        "foundation-gate-ref:latest-report"
    ]
    assert (
        "latency-ref:foundation-gate:latest-report"
        in (foundation_timeline_item["latency_refs"])
    )
    assert (
        "foundation_gate_refs_not_production_authority"
        in (foundation_timeline_item["blocked_states"])
    )
    assert foundation_timeline_item["rollback_blockers"] == [
        "rollback_execution_not_scoped"
    ]
    assert (
        foundation_timeline_item["history_answers"]["approved"]["status"] == "blocked"
    )
    assert (
        "No production"
        in (foundation_timeline_item["history_answers"]["approved"]["answer"])
    )

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
    assert (
        inbox["items"][0]["approval_envelope_status"] == "missing_until_scoped_contract"
    )
    assert (
        inbox["items"][0]["state_change_readiness"]
        == "blocked_missing_backend_contract"
    )
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


def test_founder_loop_briefing_defaults_are_blocked_and_read_only(
    tmp_path: Path,
) -> None:
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
    assert (
        "contract-ref:context-injection-missing"
        in (today["memory_review_missing_contract_refs"])
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
    assert item["source_policy_ref"] == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    assert item["source_kind"] == "manual_note"
    assert item["source_refs_status"] == "missing_safe_source_refs"
    assert item["provenance_refs_status"] == "missing_provenance_refs"
    assert item["source_review_required"] is True
    assert item["source_trust_posture"] == "untrusted_until_reviewed"
    assert item["accepted_as_truth"] is False
    assert item["memory_write_authorized"] is False
    assert item["context_injection_authorized"] is False
    assert item["decision_contract_ref"] == MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert item["decision_capture_status"] == "review_needed_no_decision_captured"
    assert item["decision_review_only"] is True
    assert item["memory_delete_authorized"] is False
    assert item["memory_export_authorized"] is False
    assert item["missing_contract_refs"] == []
    assert (
        item["correction_posture"] == "correction_requires_scoped_memory_write_contract"
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
            history_answers=_history_answers(),
            source_refs=["evidence-ref:founder-loop:unsafe"],
            status_refs=["status-ref:founder-loop:unsafe"],
            authority_posture="Review-only evidence posture.",
            next_safe_action="Keep unsafe evidence blocked.",
        )


@pytest.mark.parametrize(
    "unsafe_update",
    [
        {"approval_ref_authority": True},
        {"rollback_execution_enabled": True},
        {"memory_truth_authority": True},
        {"context_injection_authorized": True},
        {"raw_evidence_included": True},
    ],
)
def test_founder_loop_evidence_timeline_rejects_authority_creep(
    unsafe_update: dict[str, bool],
) -> None:
    with pytest.raises(ValueError):
        FounderLoopEvidenceTimelineItem(
            timeline_item_ref="evidence-timeline:unsafe/authority",
            item_kind="unsafe_authority_ref",
            title="Unsafe authority",
            safe_summary="Safe summary for rejected authority posture.",
            history_answers=_history_answers(),
            source_refs=["evidence-ref:founder-loop:unsafe-authority"],
            status_refs=["status-ref:founder-loop:unsafe-authority"],
            authority_posture="Review-only evidence posture.",
            next_safe_action="Keep unsafe authority blocked.",
            **unsafe_update,
        )
