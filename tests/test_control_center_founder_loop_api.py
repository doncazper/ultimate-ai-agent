# ruff: noqa: F401
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.chat import CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
from ultimate_ai_agent.core.code import (
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
    GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS,
)
from ultimate_ai_agent.core.memory import (
    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES,
    MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
    MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_REQUIRED_SURFACES,
)
from ultimate_ai_agent.core.intent import (
    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
    USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS,
    USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES,
    USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS,
)
from ultimate_ai_agent.core.readiness import (
    PRIVATE_BETA_READINESS_ACCEPTANCE_STATES,
    PRIVATE_BETA_READINESS_CONTRACT_REF,
    PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
    PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS,
    PRIVATE_BETA_READINESS_REQUIRED_SURFACES,
)
from ultimate_ai_agent.core.storage import (
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    TODAY_PRODUCT_SPINE_CONTRACT_REF,
)


client = TestClient(app)


def test_control_center_founder_loop_routes_are_storage_backed_and_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))

    for path, operation in [
        ("/control-center/today/summary", "control_center_today_summary"),
        ("/control-center/actions/inbox", "control_center_actions_inbox"),
        (
            "/control-center/morning-briefing/summary",
            "control_center_morning_briefing_summary",
        ),
        ("/control-center/storage/status", "control_center_storage_status"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert "safe_refs_only" in body["redactions_applied"]
        serialized = response.text.lower()
        assert str(tmp_path).lower() not in serialized
        assert "raw_prompt" not in serialized
        assert "raw_response" not in serialized
        assert "provider_payload" not in serialized
        assert "api_key" not in serialized

    inbox = client.get("/control-center/actions/inbox").json()["data"]
    assert inbox["route_ref"] == "/control-center/actions/inbox"
    assert inbox["mutating_controls_enabled"] is True
    assert inbox["action_execution_enabled"] is False
    assert inbox["decision_state_contract_ref"] == (
        "contract-ref:founder-loop-action-state-machine:v1"
    )
    assert inbox["decision_actions"] == ["approve", "edit", "reject", "defer"]
    assert inbox["decision_receipts_required"] is True
    assert inbox["idempotency_replay_enabled"] is True
    assert inbox["idempotency_conflict_rejected"] is True
    assert inbox["action_group_order"] == [
        "ready_for_decision",
        "approved_local_task_lane",
        "blocked_by_authority",
        "expired_stale",
        "receipt_recorded",
        "proposal_only_no_execution_path",
    ]
    action_groups = {group["group_id"]: group for group in inbox["action_groups"]}
    assert action_groups["ready_for_decision"]["count"] == 1
    assert action_groups["blocked_by_authority"]["count"] == 1
    assert action_groups["proposal_only_no_execution_path"]["count"] == 1
    assert "GET /control-center/actions/{action_id}/receipt" in inbox[
        "read_only_route_refs"
    ]
    assert "GET /control-center/storage/status" in inbox["read_only_route_refs"]
    assert "capability-ref:local-approval-authority" in inbox["local_prerequisite_refs"]
    assert "approval_ref_must_validate_exact_scope" in inbox["blocked_states"]
    assert inbox["private_beta_readiness_contract_ref"] == (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    )
    assert inbox["private_beta_readiness_authority_posture"][
        "action_execution_enabled"
    ] is False
    assert inbox["user_intent_understanding_contract_ref"] == (
        USER_INTENT_UNDERSTANDING_CONTRACT_REF
    )
    assert inbox["user_intent_proposals"]
    assert inbox["user_intent_authority_posture"]["low_confidence_asks_user"] is True
    assert inbox["user_intent_authority_posture"]["action_execution_enabled"] is False

    action_items = {item["item_ref"]: item for item in inbox["items"]}
    assert (
        action_items["founder-action:local-task-create-scorecard"]["action_group_id"]
        == "ready_for_decision"
    )
    assert (
        action_items["founder-action:setup-assistant-hardening"]["action_group_id"]
        == "blocked_by_authority"
    )
    assert (
        action_items["founder-action:morning-briefing-skeleton"]["action_group_id"]
        == "proposal_only_no_execution_path"
    )

    setup_item = next(
        item
        for item in inbox["items"]
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    assert setup_item["approval_required"] is True
    assert (
        setup_item["approval_envelope_ref"]
        == "approval-envelope:founder-loop:setup-assistant-hardening"
    )
    assert setup_item["approval_envelope_status"] == "dry_run_ref_available"
    assert (
        setup_item["state_change_readiness"]
        == "blocked_pending_scoped_mutation_contract"
    )
    assert setup_item["receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert setup_item["audit_refs"] == [
        "audit-plan:founder-loop:setup-assistant-hardening"
    ]
    assert (
        setup_item["idempotency_key_ref"]
        == "idempotency-ref:founder-loop:setup-assistant-hardening"
    )
    assert (
        setup_item["rollback_ref"]
        == "rollback-plan:founder-loop:setup-assistant-hardening"
    )
    assert (
        setup_item["safe_disable_ref"]
        == "safe-disable:founder-loop:setup-assistant-hardening"
    )
    setup_envelope = setup_item["approval_envelope"]
    assert setup_envelope["backend_owned"] is True
    assert setup_envelope["action_kind"] == "review_only"
    assert setup_envelope["risk_class"] == "high"
    assert setup_envelope["side_effect_class"] == "validation_only"
    assert setup_envelope["approval_requirement"].startswith(
        "approval-requirement:"
    )
    assert setup_envelope["expected_receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert "blocked-state:no-action-execution" in setup_envelope[
        "blocked_authority_refs"
    ]
    assert "evidence-ref:founder-loop:setup-assistant" in setup_envelope[
        "evidence_refs"
    ]
    setup_visibility = setup_item["receipt_visibility"]
    assert setup_visibility["backend_owned"] is True
    assert setup_visibility["decision_receipt_ref"] == "pending"
    assert setup_visibility["local_task_ref"] == "not_applicable"
    assert setup_visibility["local_task_commit_receipt_ref"] == "not_applicable"
    assert setup_visibility["evidence_timeline_event_ref"] == "pending"
    assert setup_visibility["replay_posture"] == "pending"
    assert setup_visibility["conflict_posture"] == "pending"
    assert "decision_receipt_ref:pending" in setup_visibility[
        "missing_field_states"
    ]
    assert setup_item["action_envelope_contract_ref"] == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    assert setup_item["action_envelope_ref"].startswith("action-envelope:plans:")
    assert setup_item["action_review_actions"] == [
        "approve",
        "edit",
        "reject",
        "defer",
    ]
    assert setup_item["action_envelope_execution_enabled"] is False
    assert setup_item["action_envelope_grant_capture_enabled"] is False

    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]
    assert briefing["route_ref"] == "/control-center/morning-briefing/summary"
    assert briefing["bounded_preview_only"] is True
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert briefing["source_readiness"] == (
        "blocked_missing_email_calendar_notification_contracts"
    )
    assert "contract-ref:email-read-only-missing" in briefing["missing_contract_refs"]
    assert "no_background_refresh" in briefing["blocked_states"]
    assert "no_notification_delivery" in briefing["blocked_states"]

    briefing_item = next(
        item
        for item in briefing["items"]
        if item["briefing_ref"] == "briefing:api-boundary-modularization"
    )
    assert briefing_item["priority"] == "high"
    assert briefing_item["source_readiness"] == "local_status_refs_only"
    assert briefing_item["source_refs"] == ["source-ref:control-center-route-status"]
    assert (
        "contract-ref:notification-delivery-missing"
        in briefing_item["missing_contract_refs"]
    )
    assert "no_background_refresh" in briefing_item["blocked_states"]
    assert briefing_item["stale_state"] == "recheck_route_status_before_briefing_use"
    assert "source evidence is bound" in briefing_item["evidence_gap"]
    assert "define source contracts" in briefing_item["next_safe_action"]

    today = client.get("/control-center/today/summary").json()["data"]
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
        "blocked-state:no-approval-grant-capture"
        in today["plans_action_envelope_required_blocked_refs"]
    )
    assert (
        today["plans_action_envelope_authority_posture"]["action_execution_enabled"]
        is False
    )
    assert {
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
    } == set(today["memory_source_required_kinds"])
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
    assert today["memory_review_decision_authority_posture"]["review_only"] is True
    assert (
        today["memory_review_decision_authority_posture"]["memory_write_authorized"]
        is False
    )
    assert (
        today["memory_review_decision_authority_posture"]["accepted_as_recall"] is False
    )
    assert set(today["evidence_history_required_states"]) == {
        "proposed",
        "approved",
        "happened",
        "changed",
        "undoable",
        "stale",
        "blocked",
    }
    assert {
        item["key"] for item in today["evidence_history_required_questions"]
    } == set(today["evidence_history_required_states"])
    evidence_bindings = {
        item["surface"]: item for item in today["evidence_history_surface_bindings"]
    }
    assert {"Actions", "Plans", "Memory", "Chat", "Code"} <= set(evidence_bindings)
    assert (
        evidence_bindings["Chat"]["current_status"]
        == "implemented_local_operator_turn_truth_refs"
    )
    assert (
        evidence_bindings["Code"]["current_status"]
        == "implemented_governed_diff_validation_refs"
    )
    assert today["required_loop_surfaces"] == [
        "Today",
        "Actions",
        "Evidence",
        "Memory",
    ]
    assert {item["signal"] for item in today["required_today_signals"]} == {
        "priorities",
        "blockers",
        "follow_ups",
        "plan_action_state",
        "memory_review_count",
        "stale_source_posture",
        "next_safe_actions",
    }
    assert (
        today["module_completion_contract"]["visibility_is_sufficient_for_completion"]
        is False
    )
    assert (
        today["module_completion_contract"]["standalone_module_complete_allowed"]
        is False
    )
    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    assert {
        "Today",
        "Actions",
        "Plans",
        "Memory",
        "Evidence",
        "Chat",
        "Code",
        "User Intent Understanding",
    } <= set(module_feeds)
    assert (
        module_feeds["Memory"]["status"]
        == "implemented_review_queue_quality_intake_and_loop_binding_contract"
    )
    assert (
        MEMORY_REVIEW_DECISION_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert (
        BUSINESS_MEMORY_QUALITY_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert (
        CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert (
        USER_INTENT_UNDERSTANDING_CONTRACT_REF
        in module_feeds["User Intent Understanding"]["current_feed_refs"]
    )
    assert (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
        in module_feeds["Memory"]["current_feed_refs"]
    )
    assert module_feeds["Plans"]["status"] == (
        "implemented_reviewable_action_envelope_contract"
    )
    assert PLANS_ACTION_ENVELOPE_CONTRACT_REF in module_feeds["Plans"][
        "current_feed_refs"
    ]
    assert (
        module_feeds["Chat"]["status"] == "implemented_local_operator_surface_contract"
    )
    assert CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF in module_feeds["Chat"][
        "current_feed_refs"
    ]
    assert module_feeds["Code"]["status"] == (
        "implemented_governed_code_workbench_contract_apply_blocked"
    )
    assert GOVERNED_CODE_WORKBENCH_CONTRACT_REF in module_feeds["Code"][
        "current_feed_refs"
    ]
    assert (
        today["governed_code_workbench_contract_ref"]
        == GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    )
    assert today["governed_code_workbench_status"] == (
        "implemented_reviewable_repo_local_diff_contract_apply_blocked"
    )
    assert today["governed_code_workbench_required_ref_fields"] == (
        GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS
    )
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        today["governed_code_workbench_blocked_state_refs"]
    )
    assert (
        today["governed_code_workbench_authority_posture"][
            "apply_execution_enabled"
        ]
        is False
    )
    assert (
        today["governed_code_workbench_authority_posture"][
            "approval_grant_capture_enabled"
        ]
        is False
    )
    assert (
        today["governed_code_workbench_authority_posture"][
            "shell_subprocess_execution_enabled"
        ]
        is False
    )
    assert (
        today["governed_code_workbench_authority_posture"][
            "production_authority_enabled"
        ]
        is False
    )
    assert (
        today["cross_surface_memory_intake_contract_ref"]
        == CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
    )
    assert today["cross_surface_memory_intake_required_surfaces"] == (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    )
    assert today["cross_surface_memory_intake_required_ref_fields"] == (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS
    )
    assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
        today["cross_surface_memory_intake_blocked_state_refs"]
    )
    assert today["cross_surface_memory_intake_proposal_count"] == len(
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    )
    assert (
        today["cross_surface_memory_intake_authority_posture"][
            "automatic_memory_write_authorized"
        ]
        is False
    )
    assert (
        today["cross_surface_memory_intake_authority_posture"][
            "context_injection_authorized"
        ]
        is False
    )
    assert today["memory_to_loop_binding_contract_ref"] == (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    )
    assert today["memory_to_loop_required_surfaces"] == MEMORY_TO_LOOP_REQUIRED_SURFACES
    assert today["memory_to_loop_required_ref_fields"] == (
        MEMORY_TO_LOOP_REQUIRED_REF_FIELDS
    )
    assert today["memory_derived_action_required_ref_fields"] == (
        MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS
    )
    assert set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        today["memory_to_loop_blocked_state_refs"]
    )
    assert today["memory_to_loop_items"]
    assert today["memory_derived_action_proposals"]
    assert today["weekly_ceo_review_summary"]["weekly_review_ref"] == (
        "weekly-review-ref:memory-to-loop-binding"
    )
    assert today["memory_to_loop_authority_posture"]["automatic_recall_enabled"] is False
    assert today["memory_to_loop_authority_posture"]["action_execution_enabled"] is False
    assert today["private_beta_readiness_contract_ref"] == (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    )
    assert today["private_beta_readiness_required_surfaces"] == (
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    )
    assert today["private_beta_readiness_acceptance_states"] == (
        PRIVATE_BETA_READINESS_ACCEPTANCE_STATES
    )
    assert today["private_beta_readiness_required_ref_fields"] == (
        PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS
    )
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        today["private_beta_readiness_blocked_state_refs"]
    )
    assert today["private_beta_readiness_criteria"]
    assert (
        today["private_beta_readiness_authority_posture"][
            "public_beta_claim_enabled"
        ]
        is False
    )
    assert (
        today["private_beta_readiness_authority_posture"]["remote_execution_enabled"]
        is False
    )
    assert today["private_beta_readiness_execution_authorized"] is False
    assert today["user_intent_understanding_contract_ref"] == (
        USER_INTENT_UNDERSTANDING_CONTRACT_REF
    )
    assert today["user_intent_required_surfaces"] == (
        USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES
    )
    assert today["user_intent_routing_decisions"] == (
        USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS
    )
    assert today["user_intent_required_dependency_refs"] == (
        USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS
    )
    assert today["user_intent_required_ref_fields"] == (
        USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS
    )
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        today["user_intent_blocked_state_refs"]
    )
    assert today["user_intent_proposals"]
    assert any(
        proposal["confidence_band"] == "low"
        and proposal["routing_decision"] == "ask"
        and proposal["ask_user_question_ref"]
        for proposal in today["user_intent_proposals"]
    )
    assert any(
        proposal["confidence_band"] == "conflicting"
        and proposal["routing_decision"] == "ask"
        and proposal["conflict_refs"]
        for proposal in today["user_intent_proposals"]
    )
    assert today["user_intent_authority_posture"]["action_execution_enabled"] is False
    assert today["user_intent_hidden_authority_enabled"] is False
    assert today["plan_action_state"]["execution_authorized"] is False
    assert today["plan_action_state"]["mutating_controls_enabled"] is True
    assert (
        today["plan_action_state"]["action_envelope_contract_status"]
        == "implemented_today_promotion_and_action_decision_receipts_execution_blocked"
    )
    assert (
        today["plan_action_state"]["action_envelope_contract_ref"]
        == PLANS_ACTION_ENVELOPE_CONTRACT_REF
    )
    assert today["plan_action_state"]["approval_grant_capture_enabled"] is False
    assert today["plan_action_state"]["state_change_enabled"] is True
    assert today["stale_source_posture"]["connector_runtime_enabled"] is False
    assert today["next_safe_actions"]
    assert today["memory_review_route_ref"] == "/memory"
    assert (
        today["memory_review_backend_route_ref"] == "GET /control-center/memory/review"
    )
    assert today["memory_review_status"] == "storage_backed_review_queue_with_backend_decision_receipts"
    assert today["memory_write_enabled"] is False
    assert today["memory_delete_enabled"] is False
    assert today["context_injection_enabled"] is False
    assert (
        "contract-ref:memory-write-policy-binding-missing"
        in today["memory_review_missing_contract_refs"]
    )
    assert (
        "contract-ref:business-memory-quality-controls-missing"
        not in (today["memory_review_missing_contract_refs"])
    )
    assert "no_memory_write" in today["memory_review_blocked_states"]
    assert "no_context_injection" in today["memory_review_blocked_states"]
    assert "no_raw_source_display" in today["memory_review_blocked_states"]
    assert "no_external_crm_write" in today["memory_review_blocked_states"]
    assert "no_account_sync" in today["memory_review_blocked_states"]
    assert "no_automatic_recall" in today["memory_review_blocked_states"]
    memory_item = next(
        item
        for item in today["memory_review_queue"]
        if item["review_ref"] == "memory-review:founder-loop-preferences"
    )
    assert memory_item["candidate_kind"] == "preference"
    assert memory_item["priority"] == "high"
    assert memory_item["review_state"] == "review_needed"
    assert memory_item["provenance_refs"] == [
        "provenance-ref:manual-note:founder-loop-preferences"
    ]
    assert memory_item["source_refs"] == ["source-ref:manual-note:founder-loop-storage"]
    assert memory_item["source_policy_ref"] == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    assert memory_item["source_kind"] == "manual_note"
    assert memory_item["source_trust_posture"] == "untrusted_until_reviewed"
    assert memory_item["source_review_required"] is True
    assert memory_item["safe_summary_only"] is True
    assert memory_item["accepted_as_truth"] is False
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
    assert (
        "contract-ref:memory-retention-delete-missing"
        in memory_item["missing_contract_refs"]
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
    assert "no_model_provider_authority" in memory_item["blocked_states"]
    assert "scoped memory policy milestone" in memory_item["next_safe_action"]

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
    assert plan_item["review_actions"] == ["approve", "edit", "reject", "defer"]
    assert plan_item["expected_receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert "blocked-state:no-action-execution" in plan_item["blocked_state_refs"]
    assert plan_item["action_execution_enabled"] is False
    assert plan_item["approval_grant_capture_enabled"] is False

    timeline = today["evidence_timeline"]
    assert today["evidence_timeline_status"] == "implemented_productized_evidence_timeline_safe_refs_only"
    assert timeline
    for item in timeline:
        assert item["history_contract_ref"] == EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF
        assert set(item["history_answers"]) == set(
            today["evidence_history_required_states"]
        )
        assert item["approval_ref_authority"] is False
        assert item["rollback_execution_enabled"] is False
        assert item["memory_truth_authority"] is False
        assert item["context_injection_authorized"] is False
        assert item["raw_evidence_included"] is False

    action_history = next(
        item for item in timeline if item["item_kind"] == "receipt_audit_rollback_ref"
    )["history_answers"]
    assert "identifiers, not authority" in action_history["approved"]["answer"]
    assert "do not execute rollback" in action_history["undoable"]["answer"]

    plan_history_item = next(
        item for item in timeline if item["item_kind"] == "plan_action_envelope_ref"
    )
    assert PLANS_ACTION_ENVELOPE_CONTRACT_REF in plan_history_item["status_refs"]
    assert (
        "reviewable Action envelope"
        in plan_history_item["history_answers"]["proposed"]["answer"]
    )
    assert plan_history_item["receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert (
        "blocked-state:no-approval-grant-capture"
        in plan_history_item["blocked_states"]
    )

    code_history_item = next(
        item
        for item in timeline
        if item["item_kind"] == "governed_code_workbench_proposal_ref"
    )
    assert GOVERNED_CODE_WORKBENCH_CONTRACT_REF in code_history_item["status_refs"]
    assert (
        today["governed_code_workbench_safe_diff_summary_ref"]
        in code_history_item["status_refs"]
    )
    assert (
        today["governed_code_workbench_expected_apply_receipt_ref"]
        in code_history_item["receipt_refs"]
    )
    assert (
        "no files were changed"
        in code_history_item["history_answers"]["happened"]["answer"]
    )
    assert code_history_item["history_answers"]["approved"]["status"] == "blocked"
    assert code_history_item["approval_ref_authority"] is False
    assert code_history_item["rollback_execution_enabled"] is False
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        code_history_item["blocked_states"]
    )

    memory_intake_item = next(
        item
        for item in timeline
        if item["item_kind"] == "cross_surface_memory_intake_proposal_ref"
    )
    assert CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF in memory_intake_item[
        "status_refs"
    ]
    assert memory_intake_item["history_answers"]["approved"]["status"] == "blocked"
    assert "Only safe memory intake proposal metadata" in (
        memory_intake_item["history_answers"]["happened"]["answer"]
    )
    assert memory_intake_item["memory_truth_authority"] is False
    assert memory_intake_item["context_injection_authorized"] is False
    assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
        memory_intake_item["blocked_states"]
    )
    memory_loop_item = next(
        item
        for item in timeline
        if item["item_kind"] == "memory_to_loop_binding_ref"
    )
    assert MEMORY_TO_LOOP_BINDING_CONTRACT_REF in memory_loop_item["status_refs"]
    assert memory_loop_item["history_answers"]["approved"]["status"] == "blocked"
    assert memory_loop_item["memory_truth_authority"] is False
    assert memory_loop_item["context_injection_authorized"] is False
    assert memory_loop_item["approval_ref_authority"] is False
    assert memory_loop_item["rollback_execution_enabled"] is False
    assert set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        memory_loop_item["blocked_states"]
    )
    private_beta_item = next(
        item
        for item in timeline
        if item["item_kind"] == "private_beta_readiness_gate_ref"
    )
    assert PRIVATE_BETA_READINESS_CONTRACT_REF in private_beta_item["status_refs"]
    assert private_beta_item["history_answers"]["approved"]["status"] == "blocked"
    assert private_beta_item["approval_ref_authority"] is False
    assert private_beta_item["rollback_execution_enabled"] is False
    assert private_beta_item["memory_truth_authority"] is False
    assert private_beta_item["context_injection_authorized"] is False
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        private_beta_item["blocked_states"]
    )
    user_intent_item = next(
        item
        for item in timeline
        if item["item_kind"] == "user_intent_understanding_proposal_ref"
    )
    assert USER_INTENT_UNDERSTANDING_CONTRACT_REF in user_intent_item["status_refs"]
    assert user_intent_item["history_answers"]["approved"]["status"] == "blocked"
    assert user_intent_item["approval_ref_authority"] is False
    assert user_intent_item["rollback_execution_enabled"] is False
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        user_intent_item["blocked_states"]
    )
