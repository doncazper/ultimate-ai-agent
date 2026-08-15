from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import timedelta

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AUTHORITY_DOMAIN_READINESS_CONTRACT_REF,
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_LEASE_LOCAL_OPERATOR_REF,
    AUTHORITY_LANE_CATALOG_CONTRACT_REF,
    AUTHORITY_STATE_DIR_ENV,
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseConflictError,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    AuthorityMissionPlanRequest,
    TrustMode,
    build_authority_lease_approval_requirement_for_request,
    build_authority_lane_catalog_read_model,
    build_authority_mission_plan,
    build_authority_state_read_model,
    build_default_authority_leases,
    authority_lease_kill_switch_engaged,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalCapacityError,
    AuthorityLeaseApprovalStore,
    authority_lease_approval_validator,
    build_authority_lease_test_grant,
    capture_authority_lease_backend_approval,
    issue_authority_lease_from_backend_state,
    validate_authority_lease_approval,
)
from ultimate_ai_agent.core.communications.matrix_crypto import MATRIX_CRYPTO_LANES
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeAuthority,
    RuntimeInvocationRequest,
    RuntimeProfile,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import build_policy_decision


client = TestClient(app)


def _approved_issue_request(
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approval_ref: str,
    store: AuthorityLeaseStore | None = None,
) -> AuthorityLeaseIssueRequest:
    _requirement, grant = capture_authority_lease_backend_approval(
        store or AuthorityLeaseStore(),
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-approver",
        approval_ref=approval_ref,
    )
    if grant is None:
        return request
    return request.model_copy(update={"approval_ref": grant.approval_ref})


def _approved_issue_payload(
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approval_ref: str,
) -> dict:
    return _approved_issue_request(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    ).model_dump(mode="json")


def _workspace_execute_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-execute",
        mode=TrustMode.approved_safe_local_work_session,
        domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        constraints={"workspace_ref": "workspace-ref:test"},
        safe_summary="Test lease grants workspace read and execute for this session.",
    )


def _authority_lane_by_id(catalog: dict, lane_id: str) -> dict:
    for entry in catalog["entries"]:
        if entry["lane_id"] == lane_id:
            return entry
    raise AssertionError(f"missing authority lane {lane_id}")


def test_authority_state_read_model_exposes_modes_domains_and_mappings() -> None:
    read_model = build_authority_state_read_model()
    payload = read_model.model_dump(mode="json")

    assert read_model.backend_owned is True
    assert read_model.active_mode == "read_only"
    assert read_model.unknown_authority_default == "deny"
    assert read_model.kill_switch_visible is True
    assert read_model.kill_switch_engaged is False
    assert read_model.receipts_required is True
    assert read_model.audit_required is True
    assert read_model.redaction_required is True
    assert read_model.unsupported_adapters_claimed_execution is False
    assert {"allow", "ask", "deny", "degrade_to_draft"}.issubset(
        set(read_model.policy_outcomes)
    )
    assert "workspace" in payload["target_domains"]
    assert "browser" in payload["target_domains"]
    assert "shopping_payments" in payload["target_domains"]
    assert any(
        mapping.domain == "workspace" and mapping.capability == "execute"
        for mapping in read_model.capability_mappings
    )
    authority_control_plane = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/authority-leases" in mapping.route_refs
    )
    assert authority_control_plane.domain == "system_settings"
    assert authority_control_plane.capability == "write"
    assert authority_control_plane.required_mode == "ask_before_changes"
    assert (
        authority_control_plane.status
        == "implemented_operator_selected_root_control_receipt_required"
    )
    assert "POST /api/runtime/authority-leases/approve-and-issue" in (
        authority_control_plane.route_refs
    )
    assert "POST /api/runtime/authority-leases/revoke" in (
        authority_control_plane.route_refs
    )
    assert "scripts/dev/uaa_runtime.py select-authority-mode --approve" in (
        authority_control_plane.cli_refs
    )
    mappings_by_lane = {
        mapping.lane_ref: mapping for mapping in read_model.capability_mappings
    }
    decision_by_lane = {entry.lane_ref: entry for entry in read_model.decision_catalog}
    trust_read_model_refs = (
        "lane-ref:start-here-read",
        "lane-ref:today-loop-read",
        "lane-ref:proof-detail-read",
        "lane-ref:operator-workspace-spine",
        "lane-ref:action-inbox-work-queue",
        "lane-ref:memory-review-read",
        "lane-ref:evidence-timeline-read",
        "lane-ref:model-slot-posture",
    )
    for lane_ref in trust_read_model_refs:
        assert mappings_by_lane[lane_ref].status.startswith(
            "implemented_control_center"
        )
        assert decision_by_lane[lane_ref].decision.outcome == "allow"
    assert mappings_by_lane["lane-ref:local-draft-proposal"].capability == "draft"
    assert decision_by_lane["lane-ref:local-draft-proposal"].decision.outcome == "allow"
    assert mappings_by_lane["lane-ref:connector-draft-only"].domain == "email"
    assert mappings_by_lane["lane-ref:connector-draft-only"].capability == "draft"
    assert decision_by_lane["lane-ref:connector-draft-only"].decision.outcome == "allow"
    mapped_domains = {
        str(getattr(mapping.domain, "value", mapping.domain))
        for mapping in read_model.capability_mappings
    }
    target_domains = {
        str(getattr(domain, "value", domain)) for domain in read_model.target_domains
    }
    assert target_domains <= mapped_domains
    assert len(read_model.decision_catalog) == len(read_model.capability_mappings)
    assert read_model.decision_summary.total_capabilities == len(
        read_model.decision_catalog
    )
    assert read_model.decision_summary.active_lease_count == len(
        read_model.active_leases
    )
    assert read_model.decision_summary.outcome_counts["allow"] > 0
    assert read_model.decision_summary.outcome_counts["deny"] > 0
    assert read_model.decision_summary.outcome_counts["degrade_to_draft"] > 0
    assert "reason-ref:authority:adapter-unsupported" in (
        read_model.decision_summary.blocked_reason_refs
    )
    assert read_model.decision_summary.unsupported_adapter_refs
    assert read_model.decision_summary.safe_refs_only is True
    assert read_model.decision_summary.execution_performed is False
    assert read_model.decision_summary.control_center_grants_authority is False
    assert len(read_model.mode_catalog) == len(read_model.target_modes)
    mode_catalog = {entry.mode: entry for entry in read_model.mode_catalog}
    assert mode_catalog["read_only"].status == "issue_ready_no_approval_required"
    assert mode_catalog["read_only"].issue_ready is True
    assert mode_catalog["read_only"].approval_required is False
    assert mode_catalog["read_only"].default_requested_domains["files"] == [
        "prepare",
        "read",
    ]
    assert mode_catalog["read_only"].default_requested_domains["browser"] == ["read"]
    assert mode_catalog["read_only"].default_requested_domains[
        "provider_model_calls"
    ] == ["observe", "read"]
    assert mode_catalog["read_only"].granted_default_domains["files"] == [
        "prepare",
        "read",
    ]
    assert mode_catalog["read_only"].denied_default_domain_refs == []
    assert mode_catalog["read_only"].unsupported_adapter_refs == []
    assert mode_catalog["ask_before_changes"].status == "issue_ready_approval_required"
    assert mode_catalog["ask_before_changes"].issue_ready is True
    assert mode_catalog["ask_before_changes"].approval_required is True
    assert mode_catalog["ask_before_changes"].default_requested_domains["contacts"] == [
        "read",
        "write",
    ]
    assert mode_catalog["ask_before_changes"].default_requested_domains["browser"] == [
        "read"
    ]
    assert mode_catalog["ask_before_changes"].default_requested_domains[
        "provider_model_calls"
    ] == ["observe", "read"]
    assert mode_catalog["ask_before_changes"].denied_default_domain_refs == []
    assert mode_catalog["ask_before_changes"].unsupported_adapter_refs == []
    assert mode_catalog["full_local_workspace_session"].issue_ready is True
    assert mode_catalog["full_local_workspace_session"].approval_required is True
    assert mode_catalog["full_local_workspace_session"].default_requested_domains[
        "contacts"
    ] == ["mutate", "read", "write"]
    assert mode_catalog["full_local_workspace_session"].default_requested_domains[
        "browser"
    ] == ["read"]
    assert mode_catalog["full_local_workspace_session"].default_requested_domains[
        "provider_model_calls"
    ] == ["observe", "read"]
    assert mode_catalog["full_local_workspace_session"].granted_default_domains[
        "contacts"
    ] == ["mutate", "read", "write"]
    assert mode_catalog["full_local_workspace_session"].denied_default_domain_refs == []
    assert mode_catalog["full_local_workspace_session"].unsupported_adapter_refs == []
    assert mode_catalog["full_machine_access_session"].status == (
        "issue_ready_approval_required"
    )
    assert mode_catalog["full_machine_access_session"].issue_ready is True
    assert mode_catalog["full_machine_access_session"].approval_required is True
    assert mode_catalog["full_machine_access_session"].default_requested_domains[
        "provider_model_calls"
    ] == ["execute", "read"]
    assert mode_catalog["full_machine_access_session"].default_requested_domains[
        "browser"
    ] == ["read"]
    assert mode_catalog["full_machine_access_session"].granted_default_domains[
        "provider_model_calls"
    ] == ["execute", "read"]
    assert mode_catalog["full_machine_access_session"].denied_default_domain_refs == []
    assert mode_catalog["full_machine_access_session"].unsupported_adapter_refs == []
    assert mode_catalog["delegated_mission_autonomous_window"].status == (
        "issue_ready_approval_required"
    )
    assert mode_catalog["delegated_mission_autonomous_window"].issue_ready is True
    assert mode_catalog["delegated_mission_autonomous_window"].approval_required is True
    assert (
        mode_catalog["delegated_mission_autonomous_window"].requires_mission_ref is True
    )
    assert mode_catalog[
        "delegated_mission_autonomous_window"
    ].default_requested_domains["provider_model_calls"] == ["execute", "read"]
    assert mode_catalog[
        "delegated_mission_autonomous_window"
    ].default_requested_domains["browser"] == ["read"]
    assert mode_catalog["delegated_mission_autonomous_window"].granted_default_domains[
        "provider_model_calls"
    ] == ["execute", "read"]
    assert (
        mode_catalog["delegated_mission_autonomous_window"].denied_default_domain_refs
        == []
    )
    assert (
        mode_catalog["delegated_mission_autonomous_window"].unsupported_adapter_refs
        == []
    )
    assert "reason-ref:authority:mission-scope-required" in (
        mode_catalog["delegated_mission_autonomous_window"].blocked_reason_refs
    )
    assert all(entry.safe_refs_only for entry in read_model.mode_catalog)
    assert all(
        not entry.execution_performed and not entry.mutation_performed
        for entry in read_model.mode_catalog
    )
    assert {
        str(getattr(entry.decision.outcome, "value", entry.decision.outcome))
        for entry in read_model.decision_catalog
    } >= {"allow", "deny", "degrade_to_draft"}
    assert all(entry.safe_refs_only for entry in read_model.decision_catalog)
    assert all(
        entry.authority_capability_ref.startswith("authority-capability-ref:")
        for entry in read_model.decision_catalog
    )
    assert all(
        not entry.execution_performed and not entry.mutation_performed
        for entry in read_model.decision_catalog
    )
    assert all(
        not entry.control_center_grants_authority
        for entry in read_model.decision_catalog
    )
    catalog_by_lane = {entry.lane_ref: entry for entry in read_model.decision_catalog}
    assert (
        catalog_by_lane["lane-ref:runtime-command-focused-pytest"].decision.outcome
        == "degrade_to_draft"
    )
    assert (
        catalog_by_lane["lane-ref:shell-arbitrary-command-adapter"].decision.outcome
        == "deny"
    )
    assert (
        catalog_by_lane[
            "lane-ref:shell-arbitrary-command-adapter"
        ].decision.unsupported_adapter
        is True
    )
    shell_adapter = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:shell-arbitrary-command-adapter"
    )
    assert shell_adapter.domain == "shell"
    assert shell_adapter.capability == "execute"
    assert shell_adapter.required_mode == "full_machine_access_session"
    assert shell_adapter.status == "planned_unsupported_adapter"
    assert shell_adapter.unsupported_adapter_blocks_capability is True
    assert "adapter-ref:shell-arbitrary-command:not-implemented" in (
        shell_adapter.unsupported_adapter_refs
    )
    apps_adapter = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:apps-local-automation-adapter"
    )
    assert apps_adapter.domain == "apps"
    assert apps_adapter.capability == "execute"
    assert apps_adapter.status == "planned_unsupported_adapter"
    issue_tracker_sync = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:issue-tracker-sync"
    )
    assert issue_tracker_sync.domain == "apps"
    assert issue_tracker_sync.capability == "write"
    assert issue_tracker_sync.required_mode == "full_machine_access_session"
    assert issue_tracker_sync.status == "planned_unsupported_adapter"
    assert catalog_by_lane["lane-ref:issue-tracker-sync"].decision.outcome == "deny"
    assert (
        catalog_by_lane["lane-ref:issue-tracker-sync"].decision.unsupported_adapter
        is True
    )
    task_decomposition_execute = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /task-decomposition/plans/execute" in mapping.route_refs
    )
    assert task_decomposition_execute.domain == "workspace"
    assert task_decomposition_execute.capability == "execute"
    assert (
        task_decomposition_execute.required_mode == "approved_safe_local_work_session"
    )
    assert (
        task_decomposition_execute.status
        == "implemented_exact_lease_required_local_orchestration"
    )
    hermes_chat = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/hermes/chat" in mapping.route_refs
    )
    assert hermes_chat.domain == "workspace"
    assert hermes_chat.capability == "execute"
    assert hermes_chat.required_mode == "approved_safe_local_work_session"
    assert hermes_chat.status == "implemented_exact_lease_required_external_runtime"
    runtime_invocation_record = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/invocations" in mapping.route_refs
    )
    assert runtime_invocation_record.domain == "workspace"
    assert runtime_invocation_record.capability == "draft"
    assert runtime_invocation_record.required_mode == "read_only"
    runtime_approval_binding = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/invocations/{id}/approve" in mapping.route_refs
    )
    assert runtime_approval_binding.domain == "workspace"
    assert runtime_approval_binding.capability == "execute"
    assert runtime_approval_binding.required_mode == "approved_safe_local_work_session"
    runtime_approved_execute = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/invocations/{id}/execute" in mapping.route_refs
    )
    assert runtime_approved_execute.domain == "workspace"
    assert runtime_approved_execute.capability == "execute"
    assert (
        runtime_approved_execute.status == "implemented_exact_lease_rechecked_execution"
    )
    worktree_implementer = mappings_by_lane[
        "lane-ref:runtime-worktree-implementer-proposal"
    ]
    assert worktree_implementer.domain == "workspace"
    assert worktree_implementer.capability == "draft"
    assert worktree_implementer.required_mode == "read_only"
    assert (
        decision_by_lane[
            "lane-ref:runtime-worktree-implementer-proposal"
        ].decision.outcome
        == "allow"
    )
    worktree_reviewer = mappings_by_lane["lane-ref:runtime-worktree-reviewer-compare"]
    assert worktree_reviewer.domain == "workspace"
    assert worktree_reviewer.capability == "read"
    assert (
        decision_by_lane["lane-ref:runtime-worktree-reviewer-compare"].decision.outcome
        == "allow"
    )
    worktree_verifier = mappings_by_lane["lane-ref:runtime-worktree-verifier-proof"]
    assert worktree_verifier.domain == "workspace"
    assert worktree_verifier.capability == "prepare"
    assert (
        decision_by_lane["lane-ref:runtime-worktree-verifier-proof"].decision.outcome
        == "allow"
    )
    staged_read_model = mappings_by_lane["lane-ref:staged-orchestration-read-model"]
    assert staged_read_model.domain == "workspace"
    assert staged_read_model.capability == "prepare"
    assert staged_read_model.required_mode == "read_only"
    assert (
        decision_by_lane["lane-ref:staged-orchestration-read-model"].decision.outcome
        == "allow"
    )
    preview_rail = mappings_by_lane["lane-ref:runtime-preview-rail-safe-ref-read-model"]
    assert preview_rail.domain == "workspace"
    assert preview_rail.capability == "read"
    assert preview_rail.required_mode == "read_only"
    assert preview_rail.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/preview-rail" in preview_rail.route_refs
    assert (
        decision_by_lane[
            "lane-ref:runtime-preview-rail-safe-ref-read-model"
        ].decision.outcome
        == "allow"
    )
    slash_command_registry = mappings_by_lane[
        "lane-ref:runtime-slash-command-registry-metadata"
    ]
    assert slash_command_registry.domain == "workspace"
    assert slash_command_registry.capability == "read"
    assert slash_command_registry.required_mode == "read_only"
    assert slash_command_registry.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/slash-command-registry" in (
        slash_command_registry.route_refs
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-slash-command-registry-metadata"
        ].decision.outcome
        == "allow"
    )
    result_classification = mappings_by_lane[
        "lane-ref:runtime-result-classification-taxonomy"
    ]
    assert result_classification.domain == "workspace"
    assert result_classification.capability == "read"
    assert result_classification.required_mode == "read_only"
    assert result_classification.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/result-classification" in (
        result_classification.route_refs
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-result-classification-taxonomy"
        ].decision.outcome
        == "allow"
    )
    logging_profile = mappings_by_lane["lane-ref:runtime-logging-profile-posture"]
    assert logging_profile.domain == "workspace"
    assert logging_profile.capability == "read"
    assert logging_profile.required_mode == "read_only"
    assert logging_profile.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/logging-profile" in logging_profile.route_refs
    assert (
        decision_by_lane["lane-ref:runtime-logging-profile-posture"].decision.outcome
        == "allow"
    )
    interrupt_redirect = mappings_by_lane[
        "lane-ref:runtime-interrupt-redirect-proposals"
    ]
    assert interrupt_redirect.domain == "workspace"
    assert interrupt_redirect.capability == "read"
    assert interrupt_redirect.required_mode == "read_only"
    assert interrupt_redirect.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/interrupt-redirect" in interrupt_redirect.route_refs
    assert (
        decision_by_lane[
            "lane-ref:runtime-interrupt-redirect-proposals"
        ].decision.outcome
        == "allow"
    )
    voice_media_posture = mappings_by_lane[
        "lane-ref:runtime-voice-media-posture-read-model"
    ]
    assert voice_media_posture.domain == "workspace"
    assert voice_media_posture.capability == "read"
    assert voice_media_posture.required_mode == "read_only"
    assert voice_media_posture.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/voice-media-posture" in (voice_media_posture.route_refs)
    assert voice_media_posture.unsupported_adapter_blocks_capability is False
    assert (
        decision_by_lane[
            "lane-ref:runtime-voice-media-posture-read-model"
        ].decision.outcome
        == "allow"
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-voice-media-posture-read-model"
        ].decision.unsupported_adapter
        is False
    )
    messaging_gateway_posture = mappings_by_lane[
        "lane-ref:runtime-messaging-gateway-posture-read-model"
    ]
    assert messaging_gateway_posture.domain == "workspace"
    assert messaging_gateway_posture.capability == "read"
    assert messaging_gateway_posture.required_mode == "read_only"
    assert messaging_gateway_posture.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/messaging-gateway-posture" in (
        messaging_gateway_posture.route_refs
    )
    assert messaging_gateway_posture.unsupported_adapter_blocks_capability is False
    assert (
        decision_by_lane[
            "lane-ref:runtime-messaging-gateway-posture-read-model"
        ].decision.outcome
        == "allow"
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-messaging-gateway-posture-read-model"
        ].decision.unsupported_adapter
        is False
    )
    remote_execution_posture = mappings_by_lane[
        "lane-ref:runtime-remote-execution-posture-read-model"
    ]
    assert remote_execution_posture.domain == "workspace"
    assert remote_execution_posture.capability == "read"
    assert remote_execution_posture.required_mode == "read_only"
    assert remote_execution_posture.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/remote-execution-posture" in (
        remote_execution_posture.route_refs
    )
    assert remote_execution_posture.unsupported_adapter_blocks_capability is False
    assert (
        decision_by_lane[
            "lane-ref:runtime-remote-execution-posture-read-model"
        ].decision.outcome
        == "allow"
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-remote-execution-posture-read-model"
        ].decision.unsupported_adapter
        is False
    )
    plugin_metadata_posture = mappings_by_lane[
        "lane-ref:runtime-plugin-metadata-posture-read-model"
    ]
    assert plugin_metadata_posture.domain == "workspace"
    assert plugin_metadata_posture.capability == "read"
    assert plugin_metadata_posture.required_mode == "read_only"
    assert plugin_metadata_posture.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/plugin-metadata-posture" in (
        plugin_metadata_posture.route_refs
    )
    assert plugin_metadata_posture.unsupported_adapter_blocks_capability is False
    assert (
        decision_by_lane[
            "lane-ref:runtime-plugin-metadata-posture-read-model"
        ].decision.outcome
        == "allow"
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-plugin-metadata-posture-read-model"
        ].decision.unsupported_adapter
        is False
    )
    skill_marketplace_posture = mappings_by_lane[
        "lane-ref:runtime-skill-marketplace-posture-read-model"
    ]
    assert skill_marketplace_posture.domain == "workspace"
    assert skill_marketplace_posture.capability == "read"
    assert skill_marketplace_posture.required_mode == "read_only"
    assert skill_marketplace_posture.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/skill-marketplace-posture" in (
        skill_marketplace_posture.route_refs
    )
    assert skill_marketplace_posture.unsupported_adapter_blocks_capability is False
    assert (
        decision_by_lane[
            "lane-ref:runtime-skill-marketplace-posture-read-model"
        ].decision.outcome
        == "allow"
    )
    assert (
        decision_by_lane[
            "lane-ref:runtime-skill-marketplace-posture-read-model"
        ].decision.unsupported_adapter
        is False
    )
    staged_runtime_command = mappings_by_lane[
        "lane-ref:staged-orchestration-approved-runtime-command"
    ]
    assert staged_runtime_command.domain == "workspace"
    assert staged_runtime_command.capability == "execute"
    assert staged_runtime_command.required_mode == "approved_safe_local_work_session"
    assert (
        staged_runtime_command.status
        == "implemented_exact_lease_required_runtime_command_step"
    )
    assert (
        decision_by_lane[
            "lane-ref:staged-orchestration-approved-runtime-command"
        ].decision.outcome
        == "degrade_to_draft"
    )
    runtime_safe_disable = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/safe-disable" in mapping.route_refs
    )
    assert runtime_safe_disable.domain == "workspace"
    assert runtime_safe_disable.capability == "write"
    assert runtime_safe_disable.status == "implemented_safety_control_no_execution"
    work_board_card_create = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/work-board/cards" in mapping.route_refs
    )
    assert work_board_card_create.domain == "workspace"
    assert work_board_card_create.capability == "write"
    assert work_board_card_create.required_mode == "ask_before_changes"
    crm_local_mutation = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/crm/local-mutations" in mapping.route_refs
    )
    assert crm_local_mutation.domain == "contacts"
    assert crm_local_mutation.capability == "write"
    assert crm_local_mutation.required_mode == "ask_before_changes"
    file_review_capture = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /files/review/approvals/capture" in mapping.route_refs
    )
    assert file_review_capture.domain == "files"
    assert file_review_capture.capability == "write"
    assert file_review_capture.required_mode == "ask_before_changes"
    assert file_review_capture.status == "implemented_exact_lease_required_review_only"
    file_safe_preview = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /files/read/preview" in mapping.route_refs
    )
    assert file_safe_preview.domain == "files"
    assert file_safe_preview.capability == "read"
    assert file_safe_preview.required_mode == "read_only"
    assert file_safe_preview.unsupported_adapter_blocks_capability is False
    assert (
        catalog_by_lane["lane-ref:file-safe-preview"].decision.outcome
        == "degrade_to_draft"
    )
    assert (
        catalog_by_lane["lane-ref:file-safe-preview"].decision.unsupported_adapter
        is False
    )
    file_write_proposal = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /files/write/propose" in mapping.route_refs
    )
    assert file_write_proposal.domain == "files"
    assert file_write_proposal.capability == "prepare"
    assert (
        file_write_proposal.status == "implemented_exact_lease_required_proposal_only"
    )
    assert file_write_proposal.unsupported_adapter_blocks_capability is False
    assert (
        catalog_by_lane["lane-ref:file-write-proposal-diff-preview"].decision.outcome
        == "degrade_to_draft"
    )
    email_metadata = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:source-readiness-email-calendar"
    )
    assert email_metadata.unsupported_adapter_blocks_capability is False
    assert (
        catalog_by_lane["lane-ref:source-readiness-email-calendar"].decision.outcome
        == "allow"
    )
    connector_write = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:connector-write-low-risk"
    )
    assert connector_write.domain == "email"
    assert connector_write.capability == "send"
    assert connector_write.required_mode == "full_machine_access_session"
    assert connector_write.status == "planned_unsupported_adapter"
    assert (
        catalog_by_lane["lane-ref:connector-write-low-risk"].decision.outcome == "deny"
    )
    provider_invocation = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/providers/exact-approved-lanes/tiny"
        in mapping.route_refs
    )
    assert provider_invocation.domain == "provider_model_calls"
    assert provider_invocation.capability == "execute"
    assert provider_invocation.required_mode == "full_machine_access_session"
    assert (
        provider_invocation.status
        == "implemented_exact_lease_required_provider_cost_governed"
    )
    provider_credential_validation = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/providers/credentials/validate" in mapping.route_refs
    )
    assert provider_credential_validation.domain == "provider_model_calls"
    assert provider_credential_validation.capability == "execute"
    assert provider_credential_validation.required_mode == "full_machine_access_session"
    assert (
        provider_credential_validation.status
        == "implemented_exact_lease_required_non_invoking_validation"
    )
    local_model_runtime = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /api/runtime/local-model/call" in mapping.route_refs
    )
    assert local_model_runtime.domain == "provider_model_calls"
    assert local_model_runtime.capability == "execute"
    assert local_model_runtime.required_mode == "full_machine_access_session"
    assert (
        local_model_runtime.status == "implemented_exact_lease_required_local_loopback"
    )
    web_evidence = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/web-evidence/attach" in mapping.route_refs
    )
    assert web_evidence.domain == "browser"
    assert web_evidence.capability == "read"
    assert web_evidence.required_mode == "read_only"
    assert (
        web_evidence.status == "implemented_authority_lease_required_gateway_https_get"
    )
    calendar_metadata = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:source-readiness-calendar-metadata"
    )
    assert calendar_metadata.domain == "calendar"
    assert calendar_metadata.capability == "observe"
    assert calendar_metadata.status == "partial_metadata_contract_only"
    messages_send = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:messages-live-send-adapter"
    )
    assert messages_send.domain == "messages"
    assert messages_send.capability == "send"
    assert messages_send.status == "planned_unsupported_adapter"
    capability_discovery = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-capability-discovery-read-model"
    )
    assert capability_discovery.domain == "workspace"
    assert capability_discovery.capability == "read"
    assert capability_discovery.required_mode == "read_only"
    assert capability_discovery.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/capability-discovery" in (capability_discovery.route_refs)
    assert "adapter-ref:runtime-tool-invocation:not-implemented" in (
        capability_discovery.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-capability-discovery-read-model"
        ].decision.outcome
        == "allow"
    )
    tool_registry = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-tool-registry-read-model"
    )
    assert tool_registry.domain == "workspace"
    assert tool_registry.capability == "read"
    assert tool_registry.required_mode == "read_only"
    assert tool_registry.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/tool-registry" in tool_registry.route_refs
    assert "adapter-ref:runtime-tool-invocation:not-implemented" in (
        tool_registry.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-tool-registry-read-model"].decision.outcome
        == "allow"
    )
    run_events = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-run-events-read-model"
    )
    assert run_events.domain == "workspace"
    assert run_events.capability == "read"
    assert run_events.required_mode == "read_only"
    assert run_events.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/run-events" in run_events.route_refs
    assert "adapter-ref:runtime-run-create:not-implemented" in (
        run_events.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-run-events-read-model"].decision.outcome
        == "allow"
    )
    approval_bridge = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-approval-bridge-read-model"
    )
    assert approval_bridge.domain == "workspace"
    assert approval_bridge.capability == "read"
    assert approval_bridge.required_mode == "read_only"
    assert approval_bridge.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/approval-bridge" in approval_bridge.route_refs
    assert "adapter-ref:runtime-approval-resolution-send:not-implemented" in (
        approval_bridge.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-approval-bridge-read-model"].decision.outcome
        == "allow"
    )
    streaming_progress = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-streaming-progress-read-model"
    )
    assert streaming_progress.domain == "workspace"
    assert streaming_progress.capability == "read"
    assert streaming_progress.required_mode == "read_only"
    assert streaming_progress.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/streaming-progress" in streaming_progress.route_refs
    assert "adapter-ref:runtime-streaming-progress-live-sse:not-implemented" in (
        streaming_progress.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-streaming-progress-read-model"
        ].decision.outcome
        == "allow"
    )
    profile_isolation = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-profile-isolation-read-model"
    )
    assert profile_isolation.domain == "workspace"
    assert profile_isolation.capability == "read"
    assert profile_isolation.required_mode == "read_only"
    assert profile_isolation.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/profiles" in profile_isolation.route_refs
    assert "adapter-ref:runtime-profile-provider-call:not-implemented" in (
        profile_isolation.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-profile-isolation-read-model"
        ].decision.outcome
        == "allow"
    )
    managed_scope = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-managed-scope-policy-read-model"
    )
    assert managed_scope.domain == "workspace"
    assert managed_scope.capability == "read"
    assert managed_scope.required_mode == "read_only"
    assert managed_scope.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/managed-scope-policy" in managed_scope.route_refs
    assert "adapter-ref:managed-scope-system-config-write:not-implemented" in (
        managed_scope.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-managed-scope-policy-read-model"
        ].decision.outcome
        == "allow"
    )
    doctor_diagnostics = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-doctor-diagnostics-read-model"
    )
    assert doctor_diagnostics.domain == "workspace"
    assert doctor_diagnostics.capability == "read"
    assert doctor_diagnostics.required_mode == "read_only"
    assert doctor_diagnostics.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/doctor-diagnostics" in doctor_diagnostics.route_refs
    assert "adapter-ref:runtime-doctor-install:not-implemented" in (
        doctor_diagnostics.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-doctor-diagnostics-read-model"
        ].decision.outcome
        == "allow"
    )
    session_continuity = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-session-continuity-read-model"
    )
    assert session_continuity.domain == "workspace"
    assert session_continuity.capability == "read"
    assert session_continuity.required_mode == "read_only"
    assert session_continuity.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/session-continuity" in session_continuity.route_refs
    assert "adapter-ref:session-continuity-remote-session:not-implemented" in (
        session_continuity.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-session-continuity-read-model"
        ].decision.outcome
        == "allow"
    )
    mcp_catalog = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-mcp-catalog-filtering-read-model"
    )
    assert mcp_catalog.domain == "workspace"
    assert mcp_catalog.capability == "read"
    assert mcp_catalog.required_mode == "read_only"
    assert mcp_catalog.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/mcp-catalog-filtering" in mcp_catalog.route_refs
    assert "adapter-ref:mcp-catalog-tool-invocation:not-implemented" in (
        mcp_catalog.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-mcp-catalog-filtering-read-model"
        ].decision.outcome
        == "allow"
    )
    usage_cost = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-usage-cost-analytics-read-model"
    )
    assert usage_cost.domain == "workspace"
    assert usage_cost.capability == "read"
    assert usage_cost.required_mode == "read_only"
    assert usage_cost.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/usage-cost-analytics" in usage_cost.route_refs
    assert "adapter-ref:usage-cost-provider-call:not-implemented" in (
        usage_cost.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-usage-cost-analytics-read-model"
        ].decision.outcome
        == "allow"
    )
    prompt_stability = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-prompt-stability-tiers-read-model"
    )
    assert prompt_stability.domain == "workspace"
    assert prompt_stability.capability == "read"
    assert prompt_stability.required_mode == "read_only"
    assert prompt_stability.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/prompt-stability-tiers" in prompt_stability.route_refs
    assert "adapter-ref:prompt-stability-model-call:not-implemented" in (
        prompt_stability.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-prompt-stability-tiers-read-model"
        ].decision.outcome
        == "allow"
    )
    context_budget = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-context-budget-pressure-read-model"
    )
    assert context_budget.domain == "workspace"
    assert context_budget.capability == "read"
    assert context_budget.required_mode == "read_only"
    assert context_budget.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/context-budget-pressure" in context_budget.route_refs
    assert "adapter-ref:context-budget-model-summarization:not-implemented" in (
        context_budget.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-context-budget-pressure-read-model"
        ].decision.outcome
        == "allow"
    )
    hardline_floor = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-hardline-command-blocklist-read-model"
    )
    assert hardline_floor.domain == "workspace"
    assert hardline_floor.capability == "read"
    assert hardline_floor.required_mode == "read_only"
    assert hardline_floor.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/hardline-command-blocklist" in hardline_floor.route_refs
    assert "adapter-ref:runtime-hardline-floor-override:not-implemented" in (
        hardline_floor.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-hardline-command-blocklist-read-model"
        ].decision.outcome
        == "allow"
    )
    virtual_provider_moa = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-virtual-provider-moa-read-model"
    )
    assert virtual_provider_moa.domain == "provider_model_calls"
    assert virtual_provider_moa.capability == "read"
    assert virtual_provider_moa.required_mode == "read_only"
    assert virtual_provider_moa.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/virtual-provider-moa" in virtual_provider_moa.route_refs
    assert "adapter-ref:virtual-provider-moa-live-fanout:not-implemented" in (
        virtual_provider_moa.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-virtual-provider-moa-read-model"
        ].decision.outcome
        == "allow"
    )
    checkpoint_rollback = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-checkpoint-rollback-read-model"
    )
    assert checkpoint_rollback.domain == "workspace"
    assert checkpoint_rollback.capability == "read"
    assert checkpoint_rollback.required_mode == "read_only"
    assert checkpoint_rollback.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/checkpoint-rollback" in checkpoint_rollback.route_refs
    assert "adapter-ref:checkpoint-rollback-execution-route:not-implemented" in (
        checkpoint_rollback.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-checkpoint-rollback-read-model"
        ].decision.outcome
        == "allow"
    )
    context_references = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-context-references-read-model"
    )
    assert context_references.domain == "workspace"
    assert context_references.capability == "read"
    assert context_references.required_mode == "read_only"
    assert context_references.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/context-references" in context_references.route_refs
    assert "adapter-ref:context-references-live-url-fetch:not-implemented" in (
        context_references.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-context-references-read-model"
        ].decision.outcome
        == "allow"
    )
    session_lineage = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-session-lineage-read-model"
    )
    assert session_lineage.domain == "workspace"
    assert session_lineage.capability == "read"
    assert session_lineage.required_mode == "read_only"
    assert session_lineage.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/session-lineage" in session_lineage.route_refs
    assert "adapter-ref:session-lineage-runtime-dispatch:not-implemented" in (
        session_lineage.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-session-lineage-read-model"].decision.outcome
        == "allow"
    )
    session_search = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-session-search-read-model"
    )
    assert session_search.domain == "workspace"
    assert session_search.capability == "read"
    assert session_search.required_mode == "read_only"
    assert session_search.status == "implemented_authority_bound_read_model"
    assert "GET /api/runtime/session-search" in session_search.route_refs
    assert "adapter-ref:session-search-memory-write:not-implemented" in (
        session_search.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-session-search-read-model"].decision.outcome
        == "allow"
    )
    browser_action = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:browser-action-adapter"
    )
    assert browser_action.domain == "browser"
    assert browser_action.capability == "click"
    assert browser_action.status == "planned_unsupported_adapter"
    browser_low_risk_action = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:browser-low-risk-action"
    )
    assert browser_low_risk_action.domain == "browser"
    assert browser_low_risk_action.capability == "click"
    assert browser_low_risk_action.required_mode == "full_machine_access_session"
    assert browser_low_risk_action.status == "planned_unsupported_adapter"
    assert (
        catalog_by_lane["lane-ref:browser-low-risk-action"].decision.outcome == "deny"
    )
    context_pack_action = next(
        mapping
        for mapping in read_model.capability_mappings
        if (
            "POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal"
            in mapping.route_refs
        )
    )
    assert context_pack_action.domain == "memory"
    assert context_pack_action.capability == "draft"
    assert context_pack_action.required_mode == "read_only"
    assert (
        context_pack_action.status == "implemented_exact_lease_required_proposal_only"
    )
    memory_write = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/memory/review/{candidate_ref}/accept"
        in mapping.route_refs
    )
    assert "POST /control-center/memory/review/{candidate_ref}/correct" in (
        memory_write.route_refs
    )
    assert memory_write.domain == "memory"
    assert memory_write.capability == "write"
    assert memory_write.required_mode == "ask_before_changes"
    today_action_envelope = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /control-center/today/action-envelope" in mapping.route_refs
    )
    assert today_action_envelope.domain == "workspace"
    assert today_action_envelope.capability == "draft"
    assert today_action_envelope.required_mode == "read_only"
    assert (
        today_action_envelope.status == "implemented_exact_lease_required_proposal_only"
    )
    home_assistant_control = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:home-assistant-control-adapter"
    )
    assert home_assistant_control.domain == "home_assistant"
    assert home_assistant_control.capability == "write"
    assert home_assistant_control.status == "planned_unsupported_adapter"
    background_autonomy = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:background-autonomy-scoped"
    )
    assert background_autonomy.domain == "apps"
    assert background_autonomy.capability == "execute"
    assert background_autonomy.required_mode == "delegated_mission_autonomous_window"
    assert background_autonomy.status == "planned_unsupported_adapter"
    assert "GET /api/runtime/background-jobs" in background_autonomy.route_refs
    assert "repo-local-command:uaa-runtime-inspect-background-jobs" in (
        background_autonomy.cli_refs
    )
    assert "adapter-ref:background-worker-runtime:not-implemented" in (
        background_autonomy.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:background-autonomy-scoped"].decision.outcome
        == "deny"
    )
    subagent_live_dispatch = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-subagent-isolation-live-dispatch"
    )
    assert subagent_live_dispatch.domain == "apps"
    assert subagent_live_dispatch.capability == "execute"
    assert subagent_live_dispatch.required_mode == "delegated_mission_autonomous_window"
    assert subagent_live_dispatch.status == "planned_unsupported_adapter"
    assert "GET /api/runtime/subagent-isolation" in subagent_live_dispatch.route_refs
    assert "adapter-ref:subagent-live-dispatch:not-implemented" in (
        subagent_live_dispatch.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane[
            "lane-ref:runtime-subagent-isolation-live-dispatch"
        ].decision.outcome
        == "deny"
    )
    lsp_diagnostics = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:runtime-lsp-diagnostics-evidence"
    )
    assert lsp_diagnostics.domain == "workspace"
    assert lsp_diagnostics.capability == "read"
    assert lsp_diagnostics.required_mode == "full_local_workspace_session"
    assert lsp_diagnostics.status == "planned_unsupported_adapter"
    assert "GET /api/runtime/lsp-diagnostics" in lsp_diagnostics.route_refs
    assert "adapter-ref:lsp-server-launch:not-implemented" in (
        lsp_diagnostics.unsupported_adapter_refs
    )
    assert (
        catalog_by_lane["lane-ref:runtime-lsp-diagnostics-evidence"].decision.outcome
        == "deny"
    )
    cloud_production_deploy = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:cloud-production-deploy-adapter"
    )
    assert cloud_production_deploy.domain == "cloud_production"
    assert cloud_production_deploy.capability == "deploy"
    assert cloud_production_deploy.status == "planned_unsupported_adapter"
    production_authority = next(
        mapping
        for mapping in read_model.capability_mappings
        if mapping.lane_ref == "lane-ref:production-authority-gate"
    )
    assert production_authority.domain == "cloud_production"
    assert production_authority.capability == "deploy"
    assert production_authority.required_mode == "delegated_mission_autonomous_window"
    assert production_authority.status == "planned_unsupported_adapter"
    assert (
        catalog_by_lane["lane-ref:production-authority-gate"].decision.outcome == "deny"
    )
    assert {decision.outcome for decision in read_model.sample_decisions} >= {
        "allow",
        "deny",
        "degrade_to_draft",
    }


def test_authority_lane_catalog_v1_normalizes_required_lanes_without_execution() -> (
    None
):
    catalog = build_authority_lane_catalog_read_model().model_dump(mode="json")

    assert catalog["schema_version"] == "uaa-authority-lane-catalog.v1"
    assert catalog["contract_ref"] == AUTHORITY_LANE_CATALOG_CONTRACT_REF
    assert (
        catalog["api_ref"] == "GET /api/runtime/authority-state#authority_lane_catalog"
    )
    assert (
        catalog["cli_ref"]
        == "repo-local-command:uaa-runtime-inspect-authority-lane-catalog"
    )
    assert catalog["entry_count"] == 44
    assert catalog["missing_required_lane_ids"] == []
    assert set(catalog["required_lane_ids"]) == {
        "local.verify.focused_pytest",
        "local.verify.repo_verifier",
        "local.verify.frontend_check",
        "code.patch_proposal",
        "calculation.sealed_arithmetic",
        "code.apply_exact_patch",
        "web.evidence.fetch_readonly",
        "memory.review.decision",
        "model.provider.readiness",
        "extension.catalog.review",
        "matrix.harness.inspect",
        "matrix.harness.smoke",
        "matrix.harness.start",
        "matrix.harness.fixture_seed",
        "matrix.harness.stop",
        "matrix.harness.reset",
        "matrix.session.discovery_read",
        "matrix.session.auth_methods_read",
        "matrix.session.credential_auth_create",
        "matrix.session.sso_launch",
        "matrix.session.sso_callback_consume",
        "matrix.session.refresh",
        "matrix.session.logout",
        "matrix.session.revoke_all",
        "matrix.session.credential_store_rotate",
        "matrix.session.credential_delete",
    } | {
        f"matrix.crypto.{operation.value}" for operation in MATRIX_CRYPTO_LANES
    }
    assert catalog["status_counts"] == {
        "approval_required": 10,
        "blocked": 26,
        "implemented": 7,
        "proposal_only": 1,
    }
    assert catalog["safe_refs_only"] is True
    assert catalog["execution_performed"] is False
    assert catalog["mutation_performed"] is False
    assert catalog["control_center_grants_authority"] is False
    assert catalog["unknown_authority_default"] == "deny"
    assert catalog["receipts_required"] is True
    assert catalog["audit_required"] is True
    assert catalog["redaction_required"] is True
    assert catalog["rollback_or_safe_disable_required"] is True

    focused_pytest = _authority_lane_by_id(catalog, "local.verify.focused_pytest")
    assert focused_pytest["status"] == "approval_required"
    assert focused_pytest["authority_domain"] == "shell"
    assert focused_pytest["authority_capability"] == "execute"
    assert focused_pytest["required_mode"] == "approved_safe_local_work_session"
    assert focused_pytest["idempotency_required"] is True
    for lane_id in (
        "matrix.harness.inspect",
        "matrix.harness.smoke",
        "matrix.harness.start",
        "matrix.harness.fixture_seed",
        "matrix.harness.stop",
        "matrix.harness.reset",
    ):
        harness_lane = _authority_lane_by_id(catalog, lane_id)
        assert harness_lane["authority_domain"] == "messages"
        assert harness_lane["idempotency_required"] is True
    assert focused_pytest["allowed_inputs_schema"]["shell_expansion"] is False
    assert "shell expansion" in focused_pytest["denied_capabilities"]
    assert focused_pytest["receipt_kind"] == "runtime_command_receipt"
    assert (
        focused_pytest["api_operation_ref"]
        == "POST /api/runtime/invocations/{id}/execute"
    )

    patch_proposal = _authority_lane_by_id(catalog, "code.patch_proposal")
    assert patch_proposal["status"] == "proposal_only"
    assert patch_proposal["authority_domain"] == "workspace"
    assert patch_proposal["authority_capability"] == "draft"
    assert patch_proposal["idempotency_required"] is False
    assert patch_proposal["allowed_inputs_schema"]["file_mutation"] is False
    assert "patch apply" in patch_proposal["denied_capabilities"]

    patch_apply = _authority_lane_by_id(catalog, "code.apply_exact_patch")
    assert patch_apply["status"] == "blocked"
    assert patch_apply["authority_domain"] == "files"
    assert patch_apply["authority_capability"] == "write"
    assert patch_apply["required_mode"] == "full_local_workspace_session"
    assert patch_apply["idempotency_required"] is True
    assert patch_apply["blocked_reason_refs"]
    assert "unhashed patch payloads" in patch_apply["denied_capabilities"]
    assert (
        patch_apply["api_operation_ref"]
        == "GET /control-center/coding/patch-apply-readiness"
    )

    web_evidence = _authority_lane_by_id(catalog, "web.evidence.fetch_readonly")
    assert web_evidence["status"] == "approval_required"
    assert web_evidence["authority_domain"] == "browser"
    assert web_evidence["authority_capability"] == "read"
    assert web_evidence["side_effect_class"] == "governed_network_read_only"
    assert web_evidence["allowed_inputs_schema"]["browser_action"] is False
    assert "browser actions" in web_evidence["denied_capabilities"]

    memory_decision = _authority_lane_by_id(catalog, "memory.review.decision")
    assert memory_decision["status"] == "approval_required"
    assert memory_decision["authority_domain"] == "memory"
    assert memory_decision["receipt_kind"] == "memory_review_decision_receipt"
    assert "memory as truth" in memory_decision["denied_capabilities"]

    provider_readiness = _authority_lane_by_id(catalog, "model.provider.readiness")
    assert provider_readiness["status"] == "implemented"
    assert provider_readiness["authority_domain"] == "provider_model_calls"
    assert provider_readiness["allowed_inputs_schema"]["model_call"] is False
    assert "provider SDK calls" in provider_readiness["denied_capabilities"]

    extension_review = _authority_lane_by_id(catalog, "extension.catalog.review")
    assert extension_review["status"] == "implemented"
    assert extension_review["api_operation_ref"] == "GET /extensions/catalog"
    assert extension_review["allowed_inputs_schema"]["callable_import"] is False
    assert "runtime import" in extension_review["denied_capabilities"]

    extension_install_disabled = _authority_lane_by_id(
        catalog, "extension.install_disabled"
    )
    assert extension_install_disabled["status"] == "approval_required"
    assert extension_install_disabled["authority_domain"] == "workspace"
    assert extension_install_disabled["authority_capability"] == "write"
    assert (
        extension_install_disabled["required_mode"]
        == "approved_safe_local_work_session"
    )
    assert extension_install_disabled["idempotency_required"] is True
    assert (
        extension_install_disabled["approval_scope"]
        == "approval-scope:extension-install-disabled-exact-package-version"
    )
    assert (
        extension_install_disabled["api_operation_ref"]
        == "GET /extensions/catalog#install_disabled_posture"
    )
    assert (
        extension_install_disabled["cli_inspection_ref"]
        == "scripts/dev/uaa_extensions.py inspect-install-disabled-posture"
    )
    assert "runtime import" in extension_install_disabled["denied_capabilities"]
    assert "plugin execution" in extension_install_disabled["denied_capabilities"]
    assert (
        "reason-ref:extension-install-disabled:local-approval-required"
        in (extension_install_disabled["blocked_reason_refs"])
    )

    serialized = json.dumps(catalog, sort_keys=True).lower()
    for forbidden in (
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential material",
    ):
        assert forbidden not in serialized


def test_authority_state_embeds_authority_lane_catalog_v1() -> None:
    read_model = build_authority_state_read_model()
    catalog = read_model.model_dump(mode="json")["authority_lane_catalog"]

    assert catalog["contract_ref"] == AUTHORITY_LANE_CATALOG_CONTRACT_REF
    assert catalog["entry_count"] == 44
    assert _authority_lane_by_id(catalog, "code.apply_exact_patch")["status"] == (
        "blocked"
    )
    assert (
        _authority_lane_by_id(catalog, "model.provider.readiness")["status"]
        == "implemented"
    )
    assert (
        _authority_lane_by_id(catalog, "extension.install_disabled")["status"]
        == "approval_required"
    )


def test_authority_evaluator_denies_unknown_and_degrades_when_draft_available() -> None:
    leases = build_default_authority_leases()

    read_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-read",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.read,
            safe_summary="Read workspace state.",
        ),
        leases,
    )
    execute_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-execute",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute workspace command.",
            draft_fallback_available=True,
            requested_mode=TrustMode.approved_safe_local_work_session,
        ),
        leases,
    )

    assert read_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert read_decision.receipt_ref is not None
    assert execute_decision.outcome == AuthorityDecisionOutcome.degrade_to_draft.value
    assert execute_decision.receipt_ref is None
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        execute_decision.reason_refs
    )


def test_authority_evaluator_treats_stronger_local_grants_as_draft_capable() -> None:
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Workspace write implies lower-risk draft proposal authority.",
    )

    decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-today-envelope",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.draft,
            safe_summary="Create a reviewable Today-to-Action envelope.",
            route_ref="POST /control-center/today/action-envelope",
            requested_mode=TrustMode.read_only,
        ),
        [lease],
    )

    assert decision.outcome == AuthorityDecisionOutcome.allow.value
    assert decision.lease_ref == lease.lease_ref


def test_authority_evaluator_keeps_browser_action_grants_bounded() -> None:
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-browser-click",
        mode=TrustMode.full_machine_access_session,
        domains={AuthorityDomain.browser: [AuthorityCapability.click]},
        safe_summary="Browser click authority implies only lower-risk browser read posture.",
    )

    read_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-browser-click-read",
            domain=AuthorityDomain.browser,
            capability=AuthorityCapability.read,
            safe_summary="Inspect browser posture under a future click lease.",
            requested_mode=TrustMode.read_only,
        ),
        [lease],
    )
    form_fill_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-browser-click-form-fill",
            domain=AuthorityDomain.browser,
            capability=AuthorityCapability.form_fill,
            safe_summary="Try to fill a browser form under click-only authority.",
            requested_mode=TrustMode.full_machine_access_session,
            draft_fallback_available=True,
        ),
        [lease],
    )

    assert read_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert read_decision.lease_ref == lease.lease_ref
    assert form_fill_decision.outcome == AuthorityDecisionOutcome.degrade_to_draft.value
    assert form_fill_decision.lease_ref is None
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        form_fill_decision.reason_refs
    )


def test_authority_mode_defaults_are_mode_specific_and_fail_closed(
    tmp_path,
) -> None:
    store = AuthorityLeaseStore(tmp_path / "authority")

    read_only_lease, read_only_receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            decision_reason_ref="reason-ref:test-read-only-default",
            safe_summary="Select default read-only authority.",
        ),
        idempotency_ref="idempotency-ref:test-read-only-default",
        approval_validator=validate_authority_lease_approval,
    )
    assert read_only_lease is not None
    assert read_only_receipt.status == "issued"
    assert read_only_receipt.approval_required is False
    assert read_only_receipt.approval_validated is False
    assert read_only_receipt.approval_status == "not_required"
    assert read_only_receipt.approval_ref is None
    assert read_only_receipt.requested_domains["files"] == ["read", "prepare"]
    assert read_only_receipt.requested_domains["browser"] == ["read"]
    assert read_only_receipt.requested_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert read_only_receipt.granted_domains["files"] == ["read", "prepare"]
    assert read_only_receipt.granted_domains["browser"] == ["read"]
    assert read_only_receipt.granted_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert read_only_receipt.denied_domain_refs == []
    assert read_only_receipt.unsupported_adapter_refs == []

    safe_local_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        decision_reason_ref="reason-ref:test-safe-local-default",
        safe_summary="Select default safe local authority.",
    )
    missing_approval_lease, missing_approval_receipt = store.issue_lease(
        safe_local_request,
        idempotency_ref="idempotency-ref:test-safe-local-missing-approval",
        approval_validator=validate_authority_lease_approval,
    )
    assert missing_approval_lease is None
    assert missing_approval_receipt.status == "denied"
    assert missing_approval_receipt.approval_required is True
    assert missing_approval_receipt.approval_validated is False
    assert missing_approval_receipt.approval_scope_ref is not None
    assert "APPROVAL_REF_MISSING" in missing_approval_receipt.approval_reason_codes

    safe_local_lease, safe_local_receipt = store.issue_lease(
        _approved_issue_request(
            safe_local_request,
            idempotency_ref="idempotency-ref:test-safe-local-default",
            approval_ref="approval-ref:test-authority:safe-local-default",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-safe-local-default",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert safe_local_lease is not None
    assert safe_local_receipt.status == "issued"
    assert safe_local_receipt.approval_required is True
    assert safe_local_receipt.approval_validated is True
    assert (
        safe_local_receipt.approval_ref
        == "approval-ref:test-authority:safe-local-default"
    )
    assert safe_local_receipt.granted_domains == {
        "workspace": ["read", "write", "execute"]
    }
    assert safe_local_receipt.denied_domain_refs == []

    ask_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.ask_before_changes,
        decision_reason_ref="reason-ref:test-ask-before-changes-default",
        safe_summary="Select default ask-before-changes authority.",
    )
    ask_lease, ask_receipt = store.issue_lease(
        _approved_issue_request(
            ask_request,
            idempotency_ref="idempotency-ref:test-ask-before-changes-default",
            approval_ref="approval-ref:test-authority:ask-before-changes-default",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-ask-before-changes-default",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert ask_lease is not None
    assert ask_receipt.status == "issued"
    assert ask_receipt.approval_required is True
    assert ask_receipt.approval_validated is True
    assert ask_receipt.requested_domains["contacts"] == ["read", "write"]
    assert ask_receipt.requested_domains["browser"] == ["read"]
    assert ask_receipt.requested_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert ask_receipt.granted_domains["contacts"] == ["read", "write"]
    assert ask_receipt.granted_domains["browser"] == ["read"]
    assert ask_receipt.granted_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert ask_receipt.denied_domain_refs == []
    assert ask_receipt.unsupported_adapter_refs == []
    contacts_write_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-ask-default-contacts-write",
            domain=AuthorityDomain.contacts,
            capability=AuthorityCapability.write,
            safe_summary="Write a local CRM contact under ask-before-changes mode.",
            requested_mode=TrustMode.ask_before_changes,
        ),
        [ask_lease],
    )
    browser_read_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-ask-default-browser-read",
            domain=AuthorityDomain.browser,
            capability=AuthorityCapability.read,
            safe_summary="Read browser evidence posture under ask-before-changes mode.",
            requested_mode=TrustMode.read_only,
        ),
        [ask_lease],
    )
    email_send_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-ask-default-email-send",
            domain=AuthorityDomain.email,
            capability=AuthorityCapability.send,
            safe_summary="Try to send email under ask-before-changes default scope.",
            requested_mode=TrustMode.full_machine_access_session,
            draft_fallback_available=True,
        ),
        [ask_lease],
    )
    assert contacts_write_decision.outcome == AuthorityDecisionOutcome.ask.value
    assert contacts_write_decision.lease_ref == ask_lease.lease_ref
    assert browser_read_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert browser_read_decision.lease_ref == ask_lease.lease_ref
    assert (
        email_send_decision.outcome == AuthorityDecisionOutcome.degrade_to_draft.value
    )
    assert email_send_decision.lease_ref is None

    full_local_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.full_local_workspace_session,
        decision_reason_ref="reason-ref:test-full-local-default",
        safe_summary="Select default full local workspace authority.",
    )
    full_local_lease, full_local_receipt = store.issue_lease(
        _approved_issue_request(
            full_local_request,
            idempotency_ref="idempotency-ref:test-full-local-default",
            approval_ref="approval-ref:test-authority:full-local-default",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-full-local-default",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert full_local_lease is not None
    assert full_local_receipt.status == "issued"
    assert full_local_receipt.approval_required is True
    assert full_local_receipt.approval_validated is True
    assert full_local_receipt.requested_domains["contacts"] == [
        "read",
        "write",
        "mutate",
    ]
    assert full_local_receipt.requested_domains["browser"] == ["read"]
    assert full_local_receipt.requested_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert full_local_receipt.granted_domains["contacts"] == [
        "read",
        "write",
        "mutate",
    ]
    assert full_local_receipt.granted_domains["browser"] == ["read"]
    assert full_local_receipt.granted_domains["provider_model_calls"] == [
        "observe",
        "read",
    ]
    assert full_local_receipt.denied_domain_refs == []
    assert full_local_receipt.unsupported_adapter_refs == []
    full_local_contacts_write = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-full-local-contacts-write",
            domain=AuthorityDomain.contacts,
            capability=AuthorityCapability.write,
            safe_summary="Write local CRM state under full local workspace mode.",
            requested_mode=TrustMode.full_local_workspace_session,
        ),
        [full_local_lease],
    )
    full_local_email_draft = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-full-local-email-draft",
            domain=AuthorityDomain.email,
            capability=AuthorityCapability.draft,
            safe_summary="Prepare a local email draft under full local workspace mode.",
            requested_mode=TrustMode.read_only,
        ),
        [full_local_lease],
    )
    full_local_provider_execute = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-full-local-provider-execute",
            domain=AuthorityDomain.provider_model_calls,
            capability=AuthorityCapability.execute,
            safe_summary="Try provider execution under full local workspace mode.",
            requested_mode=TrustMode.full_machine_access_session,
            draft_fallback_available=True,
        ),
        [full_local_lease],
    )
    assert full_local_contacts_write.outcome == AuthorityDecisionOutcome.allow.value
    assert full_local_contacts_write.lease_ref == full_local_lease.lease_ref
    assert full_local_email_draft.outcome == AuthorityDecisionOutcome.allow.value
    assert full_local_email_draft.lease_ref == full_local_lease.lease_ref
    assert (
        full_local_provider_execute.outcome
        == AuthorityDecisionOutcome.degrade_to_draft.value
    )
    assert full_local_provider_execute.lease_ref is None

    full_machine_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.full_machine_access_session,
        decision_reason_ref="reason-ref:test-full-machine-default",
        safe_summary="Select default full machine authority.",
    )
    missing_full_machine_lease, missing_full_machine_receipt = store.issue_lease(
        full_machine_request,
        idempotency_ref="idempotency-ref:test-full-machine-missing-approval",
        approval_validator=validate_authority_lease_approval,
    )
    assert missing_full_machine_lease is None
    assert missing_full_machine_receipt.status == "denied"
    assert missing_full_machine_receipt.approval_required is True
    assert missing_full_machine_receipt.approval_validated is False
    assert "APPROVAL_REF_MISSING" in (
        missing_full_machine_receipt.approval_reason_codes
    )

    full_machine_lease, full_machine_receipt = store.issue_lease(
        _approved_issue_request(
            full_machine_request,
            idempotency_ref="idempotency-ref:test-full-machine-default",
            approval_ref="approval-ref:test-authority:full-machine-default",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-full-machine-default",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert full_machine_lease is not None
    assert full_machine_receipt.status == "issued"
    assert full_machine_receipt.approval_required is True
    assert full_machine_receipt.approval_validated is True
    assert full_machine_receipt.requested_domains["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert full_machine_receipt.requested_domains["browser"] == ["read"]
    assert full_machine_receipt.granted_domains["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert full_machine_receipt.granted_domains["browser"] == ["read"]
    assert full_machine_receipt.denied_domain_refs == []
    assert full_machine_receipt.unsupported_adapter_refs == []
    full_machine_provider_execute = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-full-machine-provider-execute",
            domain=AuthorityDomain.provider_model_calls,
            capability=AuthorityCapability.execute,
            safe_summary=(
                "Evaluate provider execute authority under full machine mode."
            ),
            requested_mode=TrustMode.full_machine_access_session,
        ),
        [full_machine_lease],
    )
    full_machine_shell_execute = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-full-machine-shell-execute",
            domain=AuthorityDomain.shell,
            capability=AuthorityCapability.execute,
            safe_summary=(
                "Try arbitrary shell execution under full machine default scope."
            ),
            requested_mode=TrustMode.full_machine_access_session,
            draft_fallback_available=True,
        ),
        [full_machine_lease],
    )
    assert full_machine_provider_execute.outcome == AuthorityDecisionOutcome.allow.value
    assert full_machine_provider_execute.lease_ref == full_machine_lease.lease_ref
    assert (
        full_machine_shell_execute.outcome
        == AuthorityDecisionOutcome.degrade_to_draft.value
    )
    assert full_machine_shell_execute.lease_ref is None
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        full_machine_shell_execute.reason_refs
    )

    explicit_shell_lease, explicit_shell_receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_machine_access_session,
            requested_domains={
                AuthorityDomain.shell: [AuthorityCapability.execute],
                AuthorityDomain.browser: [AuthorityCapability.click],
                AuthorityDomain.system_settings: [AuthorityCapability.mutate],
            },
            decision_reason_ref="reason-ref:test-full-machine-default",
            safe_summary="Try explicit unsupported full machine adapters.",
        ),
        idempotency_ref="idempotency-ref:test-full-machine-unsupported-explicit",
    )
    assert explicit_shell_lease is None
    assert explicit_shell_receipt.status == "denied"
    assert explicit_shell_receipt.granted_domains == {}
    assert "authority-domain-ref:browser" in explicit_shell_receipt.denied_domain_refs
    assert "authority-domain-ref:shell" in explicit_shell_receipt.denied_domain_refs
    assert "authority-domain-ref:system_settings" in (
        explicit_shell_receipt.denied_domain_refs
    )
    assert any(
        ref.startswith("adapter-ref:browser:")
        for ref in explicit_shell_receipt.unsupported_adapter_refs
    )

    provider_lease, provider_receipt = store.issue_lease(
        _approved_issue_request(
            AuthorityLeaseIssueRequest(
                mode=TrustMode.full_machine_access_session,
                requested_domains={
                    AuthorityDomain.provider_model_calls: [
                        AuthorityCapability.read,
                        AuthorityCapability.execute,
                    ]
                },
                decision_reason_ref="reason-ref:test-full-machine-provider-explicit",
                safe_summary="Select explicit provider model call authority.",
            ),
            idempotency_ref="idempotency-ref:test-full-machine-provider-explicit",
            approval_ref="approval-ref:test-authority:provider-explicit",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-full-machine-provider-explicit",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert provider_lease is not None
    assert provider_receipt.status == "issued"
    assert provider_receipt.approval_validated is True
    assert provider_receipt.granted_domains == {
        "provider_model_calls": ["read", "execute"]
    }
    assert provider_receipt.denied_domain_refs == []

    delegated_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.delegated_mission_autonomous_window,
        scope="mission",
        mission_ref="mission-ref:test-delegated-default",
        decision_reason_ref="reason-ref:test-delegated-default",
        safe_summary="Select default delegated mission authority.",
    )
    missing_delegated_lease, missing_delegated_receipt = store.issue_lease(
        delegated_request,
        idempotency_ref="idempotency-ref:test-delegated-missing-approval",
        approval_validator=validate_authority_lease_approval,
    )
    assert missing_delegated_lease is None
    assert missing_delegated_receipt.status == "denied"
    assert missing_delegated_receipt.approval_required is True
    assert missing_delegated_receipt.approval_validated is False
    assert "APPROVAL_REF_MISSING" in missing_delegated_receipt.approval_reason_codes

    delegated_lease, delegated_receipt = store.issue_lease(
        _approved_issue_request(
            delegated_request,
            idempotency_ref="idempotency-ref:test-delegated-default",
            approval_ref="approval-ref:test-authority:delegated-default",
            store=store,
        ),
        idempotency_ref="idempotency-ref:test-delegated-default",
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert delegated_lease is not None
    assert delegated_receipt.status == "issued"
    assert delegated_receipt.scope == "mission"
    assert delegated_receipt.approval_required is True
    assert delegated_receipt.approval_validated is True
    assert delegated_receipt.requested_domains["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert delegated_receipt.requested_domains["browser"] == ["read"]
    assert delegated_receipt.granted_domains["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert delegated_receipt.granted_domains["browser"] == ["read"]
    assert delegated_receipt.denied_domain_refs == []
    assert delegated_receipt.unsupported_adapter_refs == []
    delegated_mission_provider_execute = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-delegated-provider-execute",
            domain=AuthorityDomain.provider_model_calls,
            capability=AuthorityCapability.execute,
            safe_summary="Execute provider call inside the delegated mission scope.",
            resource_refs=["mission-ref:test-delegated-default"],
            requested_mode=TrustMode.delegated_mission_autonomous_window,
        ),
        [delegated_lease],
    )
    delegated_unrelated_provider_execute = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-delegated-provider-unrelated",
            domain=AuthorityDomain.provider_model_calls,
            capability=AuthorityCapability.execute,
            safe_summary="Try provider call outside the delegated mission scope.",
            requested_mode=TrustMode.delegated_mission_autonomous_window,
            draft_fallback_available=True,
        ),
        [delegated_lease],
    )
    assert (
        delegated_mission_provider_execute.outcome
        == AuthorityDecisionOutcome.allow.value
    )
    assert delegated_mission_provider_execute.lease_ref == delegated_lease.lease_ref
    assert (
        delegated_unrelated_provider_execute.outcome
        == AuthorityDecisionOutcome.degrade_to_draft.value
    )
    assert "reason-ref:authority:mission-scope-mismatch" in (
        delegated_unrelated_provider_execute.reason_refs
    )

    unsupported_delegated_lease, unsupported_delegated_receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope="mission",
            mission_ref="mission-ref:test-delegated-ticket",
            requested_domains={
                AuthorityDomain.browser: [
                    AuthorityCapability.click,
                    AuthorityCapability.form_fill,
                ],
                AuthorityDomain.shopping_payments: [
                    AuthorityCapability.purchase_under_budget
                ],
            },
            decision_reason_ref="reason-ref:test-delegated-ticket",
            safe_summary="Try unsupported delegated ticket authority.",
        ),
        idempotency_ref="idempotency-ref:test-delegated-ticket",
    )
    assert unsupported_delegated_lease is None
    assert unsupported_delegated_receipt.status == "denied"
    assert unsupported_delegated_receipt.granted_domains == {}
    assert "authority-domain-ref:browser" in (
        unsupported_delegated_receipt.denied_domain_refs
    )
    assert "authority-domain-ref:shopping_payments" in (
        unsupported_delegated_receipt.denied_domain_refs
    )
    assert any(
        ref.startswith("adapter-ref:shopping_payments:")
        for ref in unsupported_delegated_receipt.unsupported_adapter_refs
    )


def test_authority_lease_kill_switch_blocks_new_lease_issue_api_cli_and_state(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "1")
    assert authority_lease_kill_switch_engaged() is True

    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ]
        },
        decision_reason_ref="reason-ref:test-authority-kill-switch",
        safe_summary="Attempt local workspace authority while kill switch is engaged.",
    )
    idempotency_ref = "idempotency-ref:test-authority-kill-switch"
    lease, receipt = store.issue_lease(
        _approved_issue_request(
            issue_request,
            idempotency_ref=idempotency_ref,
            approval_ref="approval-ref:test-authority:kill-switch",
            store=store,
        ),
        idempotency_ref=idempotency_ref,
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )

    assert lease is None
    assert receipt.status == "denied"
    assert receipt.approval_required is True
    assert receipt.approval_validated is True
    assert "AUTHORITY_LEASE_KILL_SWITCH_ENGAGED" in receipt.approval_reason_codes
    assert "reason-ref:authority:lease-kill-switch-engaged" in (
        receipt.blocked_reason_refs
    )
    assert receipt.granted_domains == {}
    assert receipt.execution_performed is False
    assert store.list_leases(active_only=True) == []

    state_model = store.build_state_read_model()
    assert state_model.kill_switch_visible is True
    assert state_model.kill_switch_engaged is True
    assert "kill switch is engaged" in state_model.operator_summary
    assert {decision.outcome for decision in state_model.sample_decisions} == {"deny"}
    assert all(
        "reason-ref:authority:kill-switch-engaged" in entry.decision.reason_refs
        for entry in state_model.decision_catalog
    )
    assert state_model.decision_summary.total_capabilities == len(
        state_model.decision_catalog
    )
    assert state_model.decision_summary.outcome_counts == {
        "allow": 0,
        "ask": 0,
        "deny": len(state_model.decision_catalog),
        "degrade_to_draft": 0,
    }
    assert state_model.decision_summary.denied_capability_refs
    assert state_model.decision_summary.allowed_capability_refs == []
    assert state_model.decision_summary.ask_capability_refs == []
    assert state_model.decision_summary.degraded_capability_refs == []
    assert "reason-ref:authority:kill-switch-engaged" in (
        state_model.decision_summary.blocked_reason_refs
    )
    assert all(not entry.issue_ready for entry in state_model.mode_catalog)
    assert all(
        entry.status == "blocked_kill_switch_engaged"
        for entry in state_model.mode_catalog
    )
    assert all(
        "reason-ref:authority:kill-switch-engaged" in entry.blocked_reason_refs
        for entry in state_model.mode_catalog
    )

    preview = store.preview_decision(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-kill-switch-preview",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.read,
            safe_summary="Preview workspace read while kill switch is engaged.",
        )
    )
    assert preview.decision.outcome == "deny"
    assert "reason-ref:authority:kill-switch-engaged" in (preview.decision.reason_refs)

    direct_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-direct-kill-switch-evaluation",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.read,
            safe_summary=(
                "Evaluate direct workspace read while kill switch is engaged."
            ),
        ),
        build_default_authority_leases(),
    )
    assert direct_decision.outcome == "deny"
    assert direct_decision.lease_ref is None
    assert "reason-ref:authority:kill-switch-engaged" in direct_decision.reason_refs

    api_issue = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-kill-switch"},
        json={
            "lease_issue_request": issue_request.model_dump(mode="json"),
        },
    )
    assert api_issue.status_code == 200
    api_body = api_issue.json()
    assert api_body["success"] is False
    api_receipt = api_body["data"]["receipt"]
    assert api_receipt["status"] == "denied"
    assert api_receipt["blocked_reason_refs"] == [
        "reason-ref:authority:lease-kill-switch-engaged"
    ]
    assert (
        "AUTHORITY_LEASE_KILL_SWITCH_ENGAGED" in (api_receipt["approval_reason_codes"])
    )
    assert api_body["data"]["lease"] is None

    api_state = client.get("/api/runtime/authority-state")
    assert api_state.status_code == 200
    api_state_data = api_state.json()["data"]
    assert api_state_data["kill_switch_engaged"] is True
    assert api_state_data["decision_summary"]["outcome_counts"]["deny"] == len(
        api_state_data["decision_catalog"]
    )
    assert (
        "reason-ref:authority:kill-switch-engaged"
        in (api_state_data["decision_summary"]["blocked_reason_refs"])
    )

    cli_state = uaa_runtime.main(["inspect-authority-state"])
    assert cli_state == 0
    cli_text = capsys.readouterr().out
    assert "Kill switch engaged: True" in cli_text
    assert "allow=0" in cli_text
    assert f"deny={len(state_model.decision_catalog)}" in cli_text
    assert "reason-ref:authority:kill-switch-engaged" in cli_text

    cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "approved_safe_local_work_session",
            "--domain",
            "workspace:read,write,execute",
            "--reason-ref",
            "reason-ref:test-cli-kill-switch",
            "--idempotency-ref",
            "idempotency-ref:test-cli-kill-switch",
            "--summary",
            "Attempt local workspace authority while kill switch is engaged.",
            "--approve",
            "--json",
        ]
    )
    assert cli_issue == 1
    cli_payload = capsys.readouterr().out
    assert '"status": "denied"' in cli_payload
    assert "AUTHORITY_LEASE_KILL_SWITCH_ENGAGED" in cli_payload


def test_delegated_mission_mode_requires_mission_scope() -> None:
    with pytest.raises(
        ValueError,
        match="AUTHORITY_DELEGATED_MISSION_REQUIRES_MISSION_SCOPE",
    ):
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            decision_reason_ref="reason-ref:test-delegated-session-denied",
            safe_summary="Invalid delegated mission session lease.",
        )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_DELEGATED_MISSION_REQUIRES_MISSION_SCOPE",
    ):
        AuthorityLease(
            lease_ref="authority-lease-ref:test-delegated-session-denied",
            mode=TrustMode.delegated_mission_autonomous_window,
            domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
            safe_summary="Invalid delegated mission session lease.",
        )


def test_authority_evaluator_ask_and_allow_modes() -> None:
    ask_lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-ask-workspace",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        safe_summary="Test ask-before-changes lease for workspace execute.",
    )
    ask_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-ask",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute under ask-before-changes mode.",
            requested_mode=TrustMode.ask_before_changes,
        ),
        [ask_lease],
    )
    allow_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-allow",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute under approved safe local work mode.",
            requested_mode=TrustMode.approved_safe_local_work_session,
        ),
        [_workspace_execute_lease()],
    )

    assert ask_decision.outcome == AuthorityDecisionOutcome.ask.value
    assert ask_decision.lease_ref == ask_lease.lease_ref
    assert ask_decision.receipt_ref is not None
    assert allow_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert allow_decision.known_authority is True
    assert allow_decision.receipt_ref is not None


def test_authority_evaluator_bounds_mission_scoped_leases_to_mission_ref() -> None:
    mission_lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-workspace-mission",
        mode=TrustMode.approved_safe_local_work_session,
        scope="mission",
        mission_ref="mission-ref:test-workspace-maintenance",
        domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        safe_summary="Test mission lease grants workspace execute for one mission.",
    )

    unrelated_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-mission-unrelated",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute workspace command outside the mission.",
            requested_mode=TrustMode.approved_safe_local_work_session,
            draft_fallback_available=True,
        ),
        [mission_lease],
    )
    matched_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-mission-matched",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute workspace command inside the mission.",
            resource_refs=["mission-ref:test-workspace-maintenance"],
            requested_mode=TrustMode.approved_safe_local_work_session,
        ),
        [mission_lease],
    )
    constrained_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-mission-constrained",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            safe_summary="Execute workspace command inside the constrained mission.",
            constraints={"mission_ref": "mission-ref:test-workspace-maintenance"},
            requested_mode=TrustMode.approved_safe_local_work_session,
        ),
        [mission_lease],
    )

    assert unrelated_decision.outcome == AuthorityDecisionOutcome.degrade_to_draft.value
    assert unrelated_decision.lease_ref is None
    assert "reason-ref:authority:mission-scope-mismatch" in (
        unrelated_decision.reason_refs
    )
    assert matched_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert matched_decision.lease_ref == mission_lease.lease_ref
    assert constrained_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert constrained_decision.lease_ref == mission_lease.lease_ref


def test_authority_api_preview_enforces_mission_lease_scope(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    issue_idempotency_ref = "idempotency-ref:authority-api-mission"
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        scope="mission",
        mission_ref="mission-ref:test-api-workspace-maintenance",
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute],
        },
        decision_reason_ref="reason-ref:authority-api-mission",
        safe_summary="Select mission workspace authority.",
    )
    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": issue_idempotency_ref},
        json=_approved_issue_payload(
            issue_request,
            idempotency_ref=issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:api-mission",
        ),
    )
    assert issue.status_code == 200
    assert issue.json()["data"]["receipt"]["status"] == "issued"

    unrelated = client.post(
        "/api/runtime/authority-decisions/preview",
        json={
            "action_ref": "authority-action-ref:test-api-mission-unrelated",
            "domain": "workspace",
            "capability": "execute",
            "safe_summary": "Preview unrelated workspace execution.",
            "requested_mode": "approved_safe_local_work_session",
            "draft_fallback_available": True,
        },
    )
    matched = client.post(
        "/api/runtime/authority-decisions/preview",
        json={
            "action_ref": "authority-action-ref:test-api-mission-matched",
            "domain": "workspace",
            "capability": "execute",
            "safe_summary": "Preview mission-scoped workspace execution.",
            "resource_refs": ["mission-ref:test-api-workspace-maintenance"],
            "requested_mode": "approved_safe_local_work_session",
        },
    )

    assert unrelated.status_code == 200
    assert unrelated.json()["data"]["decision"]["outcome"] == "degrade_to_draft"
    assert (
        "reason-ref:authority:mission-scope-mismatch"
        in (unrelated.json()["data"]["decision"]["reason_refs"])
    )
    assert matched.status_code == 200
    assert matched.json()["data"]["decision"]["outcome"] == "allow"
    assert (
        matched.json()["data"]["decision"]["lease_ref"]
        == (issue.json()["data"]["lease"]["lease_ref"])
    )


def test_unsupported_adapter_denies_without_execution_claim() -> None:
    decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-browser-click",
            domain=AuthorityDomain.browser,
            capability=AuthorityCapability.click,
            safe_summary="Click a browser control through an unsupported adapter.",
            unsupported_adapter=True,
            requested_mode=TrustMode.full_machine_access_session,
        ),
        [_workspace_execute_lease()],
    )

    assert decision.outcome == AuthorityDecisionOutcome.deny.value
    assert decision.unsupported_adapter is True
    assert decision.receipt_ref is None
    assert "reason-ref:authority:adapter-unsupported" in decision.reason_refs


def test_local_approval_authority_issues_and_revokes_authority_leases() -> None:
    authority = LocalApprovalAuthority()
    lease = authority.issue_authority_lease(_workspace_execute_lease())

    assert authority.list_authority_leases(active_only=True) == [lease]

    revoked = authority.revoke_authority_lease(
        lease.lease_ref,
        "reason-ref:test-authority-lease-revoked",
    )
    assert revoked.status == "revoked"
    assert authority.list_authority_leases(active_only=True) == []
    with pytest.raises(ValueError):
        authority.revoke_authority_lease(lease.lease_ref, "unsafe raw reason")


def test_runtime_policy_can_be_gated_by_active_authority_lease() -> None:
    request = RuntimeInvocationRequest(
        requested_authority=RuntimeAuthority.allowlisted_command,
        requested_profile=RuntimeProfile.operator_approved,
        input_ref="runtime-input-ref:test-authority-lease",
        action_ref="authority-action-ref:test-runtime-command",
        safe_summary="Run an allowlisted workspace command.",
    )
    denied = build_policy_decision(
        request,
        invocation_ref="runtime-invocation-ref:test-authority-denied",
        command_gateway_validated=True,
        active_authority_leases=build_default_authority_leases(),
    )
    allowed = build_policy_decision(
        request,
        invocation_ref="runtime-invocation-ref:test-authority-allowed",
        command_gateway_validated=True,
        active_authority_leases=[_workspace_execute_lease()],
    )

    assert denied.allowed_to_execute is False
    assert denied.authority_decision_outcome == "degrade_to_draft"
    assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in denied.reason_codes
    assert allowed.allowed_to_execute is True
    assert allowed.authority_decision_outcome == "allow"
    assert allowed.authority_lease_ref == "authority-lease-ref:test-workspace-execute"


def test_authority_state_api_cli_and_settings_surface(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))

    runtime_response = client.get("/api/runtime/authority-state")
    domain_readiness_response = client.get("/api/runtime/authority-domain-readiness")
    settings_response = client.get("/control-center/settings/status")
    exit_code = uaa_runtime.main(["inspect-authority-state", "--json"])

    assert runtime_response.status_code == 200
    runtime_body = runtime_response.json()
    assert runtime_body["success"] is True
    assert runtime_body["data"]["active_mode"] == "read_only"
    assert runtime_body["data"]["unknown_authority_default"] == "deny"
    assert "issued_at" in runtime_body["data"]["active_leases"][0]
    assert "expires_at" in runtime_body["data"]["active_leases"][0]
    assert len(runtime_body["data"]["mode_catalog"]) == len(
        runtime_body["data"]["target_modes"]
    )
    runtime_modes = {
        entry["mode"]: entry for entry in runtime_body["data"]["mode_catalog"]
    }
    assert runtime_modes["read_only"]["issue_ready"] is True
    assert runtime_modes["read_only"]["approval_required"] is False
    assert runtime_modes["full_machine_access_session"]["issue_ready"] is True
    assert runtime_modes["full_machine_access_session"]["approval_required"] is True
    assert runtime_modes["full_machine_access_session"]["default_requested_domains"][
        "provider_model_calls"
    ] == ["execute", "read"]
    assert (
        runtime_modes["full_machine_access_session"]["unsupported_adapter_refs"] == []
    )
    assert len(runtime_body["data"]["decision_catalog"]) == len(
        runtime_body["data"]["capability_mappings"]
    )
    authority_lane_catalog = runtime_body["data"]["authority_lane_catalog"]
    assert authority_lane_catalog["contract_ref"] == AUTHORITY_LANE_CATALOG_CONTRACT_REF
    assert authority_lane_catalog["entry_count"] == 44
    assert (
        _authority_lane_by_id(authority_lane_catalog, "code.apply_exact_patch")[
            "status"
        ]
        == "blocked"
    )
    assert (
        _authority_lane_by_id(authority_lane_catalog, "extension.install_disabled")[
            "status"
        ]
        == "approval_required"
    )
    assert runtime_body["data"]["decision_summary"]["total_capabilities"] == len(
        runtime_body["data"]["decision_catalog"]
    )
    domain_readiness = {
        entry["domain"]: entry for entry in runtime_body["data"]["domain_readiness"]
    }
    assert set(domain_readiness) == set(runtime_body["data"]["target_domains"])
    assert domain_readiness["workspace"]["status"] == "active_allow"
    assert (
        "authority-lease-ref:default-read-only-session"
        in domain_readiness["workspace"]["active_lease_refs"]
    )
    assert domain_readiness["shell"]["status"] == "blocked_unsupported"
    assert (
        "adapter-ref:shell-arbitrary-command:not-implemented"
        in (domain_readiness["shell"]["unsupported_adapter_refs"])
    )
    assert domain_readiness["cloud_production"]["status"] in {
        "known_denied",
        "blocked_unsupported",
    }
    assert all(
        entry["execution_performed"] is False
        and entry["mutation_performed"] is False
        and entry["control_center_grants_authority"] is False
        for entry in domain_readiness.values()
    )

    assert domain_readiness_response.status_code == 200
    domain_readiness_body = domain_readiness_response.json()
    assert domain_readiness_body["success"] is True
    domain_readiness_data = domain_readiness_body["data"]
    assert (
        domain_readiness_data["contract_ref"] == AUTHORITY_DOMAIN_READINESS_CONTRACT_REF
    )
    assert (
        domain_readiness_data["api_ref"]
        == "GET /api/runtime/authority-domain-readiness"
    )
    assert domain_readiness_data["source_authority_state_api_ref"] == (
        "GET /api/runtime/authority-state"
    )
    assert domain_readiness_data["cli_ref"] == (
        "repo-local-command:uaa-runtime-inspect-authority-domain-readiness"
    )
    assert domain_readiness_data["domain_count"] == len(
        runtime_body["data"]["target_domains"]
    )
    assert domain_readiness_data["entries"] == runtime_body["data"]["domain_readiness"]
    assert domain_readiness_data["safe_refs_only"] is True
    assert domain_readiness_data["execution_performed"] is False
    assert domain_readiness_data["mutation_performed"] is False
    assert domain_readiness_data["control_center_grants_authority"] is False
    assert domain_readiness_data["unknown_authority_default"] == "deny"
    assert (
        runtime_body["data"]["decision_summary"]["outcome_counts"]["degrade_to_draft"]
        > 0
    )
    assert (
        "reason-ref:authority:no-active-lease-for-domain-capability"
        in (runtime_body["data"]["decision_summary"]["blocked_reason_refs"])
    )
    assert any(
        entry["decision"]["outcome"] == "degrade_to_draft"
        for entry in runtime_body["data"]["decision_catalog"]
    )

    assert settings_response.status_code == 200
    settings_body = settings_response.json()
    authority_state = settings_body["data"]["authority_lease_state"]
    assert authority_state["api_ref"] == "GET /api/runtime/authority-state"
    assert authority_state["kill_switch_visible"] is True
    assert authority_state["kill_switch_engaged"] is False
    assert authority_state["unsupported_adapters_claimed_execution"] is False
    assert "issued_at" in authority_state["active_leases"][0]
    assert "expires_at" in authority_state["active_leases"][0]
    assert len(authority_state["mode_catalog"]) == len(authority_state["target_modes"])
    assert any(
        entry["mode"] == "delegated_mission_autonomous_window"
        and entry["requires_mission_ref"] is True
        for entry in authority_state["mode_catalog"]
    )
    assert authority_state["decision_catalog"]
    assert len(authority_state["decision_catalog"]) == len(
        authority_state["capability_mappings"]
    )
    assert authority_state["decision_summary"]["total_capabilities"] == len(
        authority_state["decision_catalog"]
    )
    assert authority_state["authority_lane_catalog"]["entry_count"] == 44
    assert len(authority_state["domain_readiness"]) == len(
        authority_state["target_domains"]
    )

    assert exit_code == 0
    cli_payload = capsys.readouterr().out
    assert "authority_state_read_model" in cli_payload
    assert "authority_lane_catalog" in cli_payload
    assert "mode_catalog" in cli_payload
    assert "domain_readiness" in cli_payload
    assert "decision_summary" in cli_payload
    assert "decision_catalog" in cli_payload
    assert "raw_paths_omitted" in cli_payload

    text_exit_code = uaa_runtime.main(["inspect-authority-state"])
    assert text_exit_code == 0
    cli_text = capsys.readouterr().out
    assert "issued=" in cli_text
    assert "expires=" in cli_text
    assert "Mode readiness:" in cli_text
    assert "Domain readiness:" in cli_text
    assert "- workspace status=active_allow" in cli_text
    assert "- shell status=blocked_unsupported" in cli_text
    assert "full_machine_access_session" in cli_text
    assert "issue_ready_approval_required" in cli_text
    assert "provider_model_calls: execute, read" in cli_text
    assert "delegated_mission_autonomous_window" in cli_text
    assert "planned_unsupported_adapter" in cli_text
    assert "adapter-ref:shell-arbitrary-command:not-implemented" in cli_text
    assert "Decision catalog:" in cli_text
    assert "Decision summary:" in cli_text
    assert "Outcome counts:" in cli_text
    assert "Blocked reasons:" in cli_text
    assert "authority-capability-ref:runtime-command-focused-pytest" in cli_text
    assert "source: lane-ref:runtime-command-focused-pytest" in cli_text

    lane_catalog_exit_code = uaa_runtime.main(
        ["inspect-authority-lane-catalog", "--json"]
    )
    assert lane_catalog_exit_code == 0
    lane_catalog_payload = json.loads(capsys.readouterr().out)
    assert lane_catalog_payload["command_ref"] == (
        "repo-local-command:uaa-runtime-inspect-authority-lane-catalog"
    )
    lane_catalog = lane_catalog_payload["authority_lane_catalog_read_model"]
    assert lane_catalog["contract_ref"] == AUTHORITY_LANE_CATALOG_CONTRACT_REF
    assert lane_catalog["entry_count"] == 44
    assert lane_catalog_payload["safe_refs_only"] is True
    assert lane_catalog_payload["execution_performed"] is False

    lane_catalog_text_exit_code = uaa_runtime.main(["inspect-authority-lane-catalog"])
    assert lane_catalog_text_exit_code == 0
    lane_catalog_text = capsys.readouterr().out
    assert "Authority Lane Catalog V1" in lane_catalog_text
    assert "local.verify.focused_pytest" in lane_catalog_text
    assert "code.apply_exact_patch status=blocked" in lane_catalog_text

    domain_readiness_exit_code = uaa_runtime.main(
        ["inspect-authority-domain-readiness", "--json"]
    )
    assert domain_readiness_exit_code == 0
    domain_readiness_payload = json.loads(capsys.readouterr().out)
    assert domain_readiness_payload["command_ref"] == (
        "repo-local-command:uaa-runtime-inspect-authority-domain-readiness"
    )
    domain_readiness_read_model = domain_readiness_payload[
        "authority_domain_readiness_read_model"
    ]
    assert (
        domain_readiness_read_model["contract_ref"]
        == AUTHORITY_DOMAIN_READINESS_CONTRACT_REF
    )
    assert domain_readiness_read_model["domain_count"] == len(
        runtime_body["data"]["target_domains"]
    )
    assert domain_readiness_payload["safe_refs_only"] is True
    assert domain_readiness_payload["execution_performed"] is False

    domain_readiness_text_exit_code = uaa_runtime.main(
        ["inspect-authority-domain-readiness"]
    )
    assert domain_readiness_text_exit_code == 0
    domain_readiness_text = capsys.readouterr().out
    assert "Authority domain readiness" in domain_readiness_text
    assert "GET /api/runtime/authority-domain-readiness" in domain_readiness_text
    assert "- workspace status=active_allow" in domain_readiness_text
    assert "- shell status=blocked_unsupported" in domain_readiness_text

    summary_exit_code = uaa_runtime.main(["inspect-authority-state", "--summary"])
    assert summary_exit_code == 0
    summary_text = capsys.readouterr().out
    assert "Decision summary:" in summary_text
    assert "Outcome counts:" in summary_text
    assert "Decision catalog:" not in summary_text
    assert "authority-capability-ref:runtime-command-focused-pytest" not in summary_text


def test_authority_decision_preview_api_and_cli_are_read_only(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))

    denied = client.post(
        "/api/runtime/authority-decisions/preview",
        json={
            "action_ref": "authority-action-ref:test-preview-workspace-execute-denied",
            "domain": "workspace",
            "capability": "execute",
            "capability_ref": "authority-capability-ref:test-preview-workspace-execute",
            "safe_summary": "Preview workspace execution authority without running anything.",
            "route_ref": "POST /api/runtime/command/run",
            "requested_mode": "approved_safe_local_work_session",
            "draft_fallback_available": True,
        },
    )
    assert denied.status_code == 200
    denied_preview = denied.json()["data"]
    assert denied_preview["execution_performed"] is False
    assert denied_preview["mutation_performed"] is False
    assert denied_preview["safe_refs_only"] is True
    assert denied_preview["preview_receipt_ref"].startswith(
        "receipt-ref:authority-decision-preview:"
    )
    assert denied_preview["decision"]["outcome"] == "degrade_to_draft"
    assert denied_preview["decision"]["lease_ref"] is None
    assert denied_preview["decision"]["required_domain_refs"] == [
        "authority-domain-ref:workspace"
    ]
    assert denied_preview["decision"]["required_capability_refs"] == [
        "authority-capability-ref:execute"
    ]
    assert (
        denied_preview["decision"]["capability_ref"]
        == "authority-capability-ref:test-preview-workspace-execute"
    )

    preview_issue_idempotency_ref = "idempotency-ref:authority-preview-issue"
    preview_issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
            ]
        },
        decision_reason_ref="reason-ref:authority-preview-issue",
        safe_summary="Select workspace execute authority for preview testing.",
    )
    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": preview_issue_idempotency_ref},
        json=_approved_issue_payload(
            preview_issue_request,
            idempotency_ref=preview_issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:preview-issue",
        ),
    )
    assert issue.status_code == 200
    lease_ref = issue.json()["data"]["lease"]["lease_ref"]

    allowed = client.post(
        "/api/runtime/authority-decisions/preview",
        json={
            "action_ref": "authority-action-ref:test-preview-workspace-execute-allowed",
            "domain": "workspace",
            "capability": "execute",
            "safe_summary": "Preview workspace execution authority without running anything.",
            "route_ref": "POST /api/runtime/command/run",
            "requested_mode": "approved_safe_local_work_session",
        },
    )
    assert allowed.status_code == 200
    allowed_preview = allowed.json()["data"]
    assert allowed_preview["execution_performed"] is False
    assert allowed_preview["decision"]["outcome"] == "allow"
    assert allowed_preview["decision"]["lease_ref"] == lease_ref
    assert allowed_preview["decision"]["receipt_ref"].startswith(
        "receipt-ref:authority-policy:"
    )
    assert lease_ref in allowed_preview["active_lease_refs"]

    cli_exit = uaa_runtime.main(
        [
            "preview-authority-decision",
            "--action-ref",
            "authority-action-ref:test-preview-cli",
            "--domain",
            "browser",
            "--capability",
            "click",
            "--capability-ref",
            "authority-capability-ref:test-preview-cli-browser-click",
            "--summary",
            "Preview browser click authority without running browser automation.",
            "--requested-mode",
            "delegated_mission_autonomous_window",
            "--unsupported-adapter",
            "--draft-fallback-available",
            "--json",
        ]
    )
    assert cli_exit == 0
    cli_payload = capsys.readouterr().out
    assert "uaa-runtime-preview-authority-decision" in cli_payload
    assert "authority-capability-ref:test-preview-cli-browser-click" in cli_payload
    assert "adapter-unsupported" in cli_payload
    assert "execution_performed" in cli_payload

    cli_text_exit = uaa_runtime.main(
        [
            "preview-authority-decision",
            "--action-ref",
            "authority-action-ref:test-preview-cli-text",
            "--domain",
            "browser",
            "--capability",
            "click",
            "--capability-ref",
            "authority-capability-ref:test-preview-cli-text-browser-click",
            "--summary",
            "Preview browser click authority without running browser automation.",
            "--requested-mode",
            "full_machine_access_session",
            "--unsupported-adapter",
            "--draft-fallback-available",
        ]
    )
    assert cli_text_exit == 0
    cli_text = capsys.readouterr().out
    assert "Authority decision preview" in cli_text
    assert (
        "Capability ref: authority-capability-ref:test-preview-cli-text-browser-click"
        in cli_text
    )
    assert (
        "Requirement: Requires full machine access session + browser domain + "
        "click capability."
    ) in cli_text


def test_authority_mission_plan_api_cli_and_core_are_read_only(
    capsys,
    tmp_path,
) -> None:
    draft_plan = build_authority_mission_plan(
        AuthorityMissionPlanRequest(
            mission_ref="mission-ref:test-ticket-purchase",
            safe_goal_summary=(
                "Preview a delegated ticket purchase mission without opening a browser."
            ),
            requested_mode=TrustMode.delegated_mission_autonomous_window,
            requested_domains={
                AuthorityDomain.browser: [
                    AuthorityCapability.observe,
                    AuthorityCapability.click,
                    AuthorityCapability.form_fill,
                ],
                AuthorityDomain.shopping_payments: [
                    AuthorityCapability.purchase_under_budget
                ],
            },
            constraints={
                "merchant_ref": "merchant-ref:test-ticket-site",
                "budget_ref": "budget-ref:test-max-total",
            },
            decision_reason_ref="reason-ref:test-ticket-mission-plan",
        ),
        build_default_authority_leases(),
    )
    assert draft_plan.execution_performed is False
    assert draft_plan.mutation_performed is False
    assert draft_plan.lease_issue_ready is False
    assert "authority-domain-ref:browser" in draft_plan.denied_domain_refs
    assert "authority-domain-ref:shopping_payments" in draft_plan.denied_domain_refs
    assert any(
        ref.startswith("adapter-ref:browser:")
        for ref in draft_plan.unsupported_adapter_refs
    )
    assert any(
        ref.startswith("adapter-ref:shopping_payments:")
        for ref in draft_plan.unsupported_adapter_refs
    )
    assert {preview.decision.outcome for preview in draft_plan.action_previews} == {
        "degrade_to_draft"
    }
    assert "reason-ref:authority:adapter-unsupported" in draft_plan.blocked_reason_refs

    delegated_default_plan = build_authority_mission_plan(
        AuthorityMissionPlanRequest(
            mission_ref="mission-ref:test-delegated-default-plan",
            safe_goal_summary=(
                "Preview a delegated mission using implemented default authority."
            ),
            requested_mode=TrustMode.delegated_mission_autonomous_window,
            decision_reason_ref="reason-ref:test-delegated-default-plan",
        ),
        build_default_authority_leases(),
    )
    assert delegated_default_plan.execution_performed is False
    assert delegated_default_plan.mutation_performed is False
    assert delegated_default_plan.lease_issue_ready is True
    assert delegated_default_plan.lease_issue_request.scope == "mission"
    assert delegated_default_plan.lease_issue_request.mission_ref == (
        "mission-ref:test-delegated-default-plan"
    )
    assert delegated_default_plan.granted_domains["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert delegated_default_plan.granted_domains["browser"] == ["read"]
    assert delegated_default_plan.denied_domain_refs == []
    assert delegated_default_plan.unsupported_adapter_refs == []
    assert "authority-domain-ref:provider_model_calls" in (
        delegated_default_plan.required_domain_refs
    )
    assert "authority-capability-ref:execute" in (
        delegated_default_plan.required_capability_refs
    )
    delegated_issue_idempotency_ref = "idempotency-ref:test-delegated-default-plan"
    delegated_store = AuthorityLeaseStore(tmp_path / "authority-delegated")
    delegated_lease, delegated_receipt = delegated_store.issue_lease(
        _approved_issue_request(
            delegated_default_plan.lease_issue_request,
            idempotency_ref=delegated_issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:delegated-default-plan",
            store=delegated_store,
        ),
        idempotency_ref=delegated_issue_idempotency_ref,
        approval_validator=authority_lease_approval_validator(
            delegated_store.state_dir
        ),
    )
    assert delegated_lease is not None
    assert delegated_lease.scope == "mission"
    assert delegated_lease.mission_ref == "mission-ref:test-delegated-default-plan"
    assert delegated_lease.domains["provider_model_calls"] == ["read", "execute"]
    assert delegated_receipt.status == "issued"
    assert delegated_receipt.unsupported_adapter_refs == []

    response = client.post(
        "/api/runtime/authority-missions/plan",
        json={
            "mission_ref": "mission-ref:test-workspace-maintenance",
            "safe_goal_summary": "Preview a local workspace maintenance mission.",
            "requested_mode": "approved_safe_local_work_session",
            "requested_domains": {
                "workspace": ["read", "execute"],
            },
            "decision_reason_ref": "reason-ref:test-workspace-mission-plan",
            "duration_minutes": 120,
        },
    )
    assert response.status_code == 200
    plan = response.json()["data"]
    assert plan["lease_issue_ready"] is True
    assert plan["execution_performed"] is False
    assert plan["mutation_performed"] is False
    assert plan["lease_issue_request"]["scope"] == "mission"
    assert plan["lease_issue_request"]["mission_ref"] == (
        "mission-ref:test-workspace-maintenance"
    )
    assert plan["granted_domains"]["workspace"] == ["read", "execute"]
    assert plan["unsupported_adapter_refs"] == []
    assert plan["route_ref"] == "POST /api/runtime/authority-missions/plan"
    assert plan["cli_ref"] == "repo-local-command:uaa-runtime-plan-authority-mission"

    delegated_default_response = client.post(
        "/api/runtime/authority-missions/plan",
        json={
            "mission_ref": "mission-ref:test-api-delegated-default",
            "safe_goal_summary": (
                "Preview delegated mission defaults through the API."
            ),
            "requested_mode": "delegated_mission_autonomous_window",
            "decision_reason_ref": "reason-ref:test-api-delegated-default",
            "duration_minutes": 120,
        },
    )
    assert delegated_default_response.status_code == 200
    delegated_default_body = delegated_default_response.json()["data"]
    assert delegated_default_body["lease_issue_ready"] is True
    assert delegated_default_body["lease_issue_request"]["scope"] == "mission"
    assert delegated_default_body["lease_issue_request"]["mission_ref"] == (
        "mission-ref:test-api-delegated-default"
    )
    assert delegated_default_body["granted_domains"]["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert delegated_default_body["unsupported_adapter_refs"] == []

    issue_ready_plan = build_authority_mission_plan(
        AuthorityMissionPlanRequest(
            mission_ref="mission-ref:test-core-workspace-maintenance",
            safe_goal_summary="Preview a local workspace maintenance mission.",
            requested_mode=TrustMode.approved_safe_local_work_session,
            requested_domains={
                AuthorityDomain.workspace: [
                    AuthorityCapability.read,
                    AuthorityCapability.execute,
                ],
            },
            decision_reason_ref="reason-ref:test-core-workspace-mission-plan",
        ),
        build_default_authority_leases(),
    )
    mission_issue_idempotency_ref = "idempotency-ref:test-core-workspace-mission-issue"
    mission_store = AuthorityLeaseStore(tmp_path / "authority")
    lease, receipt = mission_store.issue_lease(
        _approved_issue_request(
            issue_ready_plan.lease_issue_request,
            idempotency_ref=mission_issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:core-workspace-mission",
            store=mission_store,
        ),
        idempotency_ref=mission_issue_idempotency_ref,
        approval_validator=authority_lease_approval_validator(
            mission_store.state_dir
        ),
    )
    assert issue_ready_plan.lease_issue_ready is True
    assert lease is not None
    assert lease.scope == "mission"
    assert lease.mission_ref == "mission-ref:test-core-workspace-maintenance"
    assert lease.domains["workspace"] == ["read", "execute"]
    assert receipt.status == "issued"
    assert receipt.scope == "mission"
    assert receipt.execution_performed is False
    assert receipt.unsupported_adapter_refs == []

    default_cli_exit = uaa_runtime.main(
        [
            "plan-authority-mission",
            "--mission-ref",
            "mission-ref:test-cli-delegated-default",
            "--summary",
            "Preview delegated mission defaults from the CLI.",
            "--json",
        ]
    )
    assert default_cli_exit == 0
    default_cli_payload = json.loads(capsys.readouterr().out)
    default_cli_plan = default_cli_payload["authority_mission_plan"]
    assert default_cli_plan["lease_issue_ready"] is True
    assert default_cli_plan["granted_domains"]["provider_model_calls"] == [
        "read",
        "execute",
    ]
    assert default_cli_plan["unsupported_adapter_refs"] == []

    cli_exit = uaa_runtime.main(
        [
            "plan-authority-mission",
            "--mission-ref",
            "mission-ref:test-cli-ticket-mission",
            "--domain",
            "browser:observe,click,form_fill",
            "--domain",
            "shopping_payments:purchase_under_budget",
            "--summary",
            "Preview a delegated ticket purchase mission from the CLI.",
            "--json",
        ]
    )
    assert cli_exit == 0
    cli_payload = capsys.readouterr().out
    assert "uaa-runtime-plan-authority-mission" in cli_payload
    assert "authority_mission_plan" in cli_payload
    assert "adapter-ref:shopping_payments" in cli_payload
    assert "execution_performed" in cli_payload

    cli_text_exit = uaa_runtime.main(
        [
            "plan-authority-mission",
            "--mission-ref",
            "mission-ref:test-cli-ticket-mission-text",
            "--domain",
            "browser:observe,click,form_fill",
            "--domain",
            "shopping_payments:purchase_under_budget",
            "--summary",
            "Preview a delegated ticket purchase mission from the CLI.",
        ]
    )
    assert cli_text_exit == 0
    cli_text = capsys.readouterr().out
    assert "Authority mission plan" in cli_text
    assert (
        "Requirement: Requires delegated mission autonomous window + "
        "browser, shopping payments domain scope + click, form fill, observe, "
        "purchase under budget capability scope."
    ) in cli_text


def test_authority_lease_issue_revoke_api_and_cli_are_durable(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))

    missing_idempotency = client.post(
        "/api/runtime/authority-leases",
        json={
            "mode": "approved_safe_local_work_session",
            "decision_reason_ref": "reason-ref:authority-api-missing-idempotency",
            "safe_summary": "Select local workspace authority for this session.",
        },
    )
    assert missing_idempotency.status_code == 428
    assert missing_idempotency.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    issue_idempotency_ref = "idempotency-ref:authority-api-issue"
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ],
            AuthorityDomain.contacts: [AuthorityCapability.write],
            AuthorityDomain.browser: [AuthorityCapability.click],
            AuthorityDomain.provider_model_calls: [AuthorityCapability.execute],
        },
        decision_reason_ref="reason-ref:authority-api-issue",
        safe_summary="Select local workspace authority for this session.",
    )
    missing_approval = client.post(
        "/api/runtime/authority-leases",
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:authority-api-missing-approval"
        },
        json=issue_request.model_dump(mode="json"),
    )
    assert missing_approval.status_code == 200
    missing_receipt = missing_approval.json()["data"]["receipt"]
    assert missing_approval.json()["success"] is False
    assert missing_receipt["status"] == "denied"
    assert missing_receipt["approval_required"] is True
    assert missing_receipt["approval_validated"] is False
    assert "APPROVAL_REF_MISSING" in missing_receipt["approval_reason_codes"]

    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": issue_idempotency_ref},
        json=_approved_issue_payload(
            issue_request,
            idempotency_ref=issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:api-issue",
        ),
    )
    assert issue.status_code == 200
    body = issue.json()
    assert body["success"] is True
    receipt = body["data"]["receipt"]
    lease = body["data"]["lease"]
    assert receipt["status"] == "issued"
    assert receipt["approval_required"] is True
    assert receipt["approval_validated"] is True
    assert receipt["approval_ref"] == "approval-ref:test-authority:api-issue"
    assert receipt["execution_performed"] is False
    assert receipt["lease_issued_at"] == lease["issued_at"]
    assert receipt["lease_expires_at"] == lease["expires_at"]
    assert receipt["granted_domains"]["workspace"] == ["read", "write", "execute"]
    assert "contacts" not in receipt["granted_domains"]
    assert "authority-domain-ref:contacts" in receipt["denied_domain_refs"]
    assert "authority-domain-ref:browser" in receipt["denied_domain_refs"]
    assert (
        "authority-domain-ref:provider_model_calls" in (receipt["denied_domain_refs"])
    )
    assert (
        "adapter-ref:contacts:write-not-available-for-authority-mode-v1"
        in receipt["unsupported_adapter_refs"]
    )
    assert (
        "adapter-ref:browser:click-not-implemented-for-authority-lease-v1"
        in (receipt["unsupported_adapter_refs"])
    )
    assert (
        "adapter-ref:provider_model_calls:execute-not-available-for-authority-mode-v1"
    ) in receipt["unsupported_adapter_refs"]

    state = client.get("/api/runtime/authority-state")
    assert state.status_code == 200
    state_data = state.json()["data"]
    assert state_data["active_mode"] == "approved_safe_local_work_session"
    assert state_data["active_leases"][0]["lease_ref"] == lease["lease_ref"]
    assert receipt["receipt_ref"] in {
        item["receipt_ref"] for item in state_data["recent_receipts"]
    }

    cli_state = uaa_runtime.main(["inspect-authority-state"])
    assert cli_state == 0
    cli_state_text = capsys.readouterr().out
    assert "Authority modes and mission leases" in cli_state_text
    assert "Active leases: 1" in cli_state_text
    assert lease["lease_ref"] in cli_state_text
    assert "domains: workspace: read, write, execute" in cli_state_text
    assert "constraints:" in cli_state_text
    assert "Recent receipts:" in cli_state_text
    assert receipt["receipt_ref"] in cli_state_text
    assert "lease-issued=" in cli_state_text
    assert "lease-expires=" in cli_state_text
    assert "denied: authority-domain-ref:contacts" in cli_state_text
    assert "unsupported adapters: adapter-ref:contacts" in cli_state_text
    assert "Sample decisions:" in cli_state_text
    assert "Unknown authority default: deny" in cli_state_text
    assert "Kill switch visible: True" in cli_state_text
    assert "Kill switch engaged: False" in cli_state_text

    cli_issue_idempotency_ref = "idempotency-ref:authority-cli-issue"
    cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "ask_before_changes",
            "--domain",
            "workspace:read,write",
            "--reason-ref",
            "reason-ref:authority-cli-issue",
            "--idempotency-ref",
            cli_issue_idempotency_ref,
            "--summary",
            "Select ask-before-changes workspace authority.",
            "--approve",
            "--approved-by-actor-ref",
            "operator-ref:test-cli-approver",
            "--json",
        ]
    )
    assert cli_issue == 0
    cli_payload = capsys.readouterr().out
    assert "uaa-runtime-select-authority-mode" in cli_payload
    assert "receipt-ref:authority-lease" in cli_payload
    assert '"approval_captured": true' in cli_payload
    assert '"approval_validated": true' in cli_payload

    default_cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "approved_safe_local_work_session",
            "--reason-ref",
            "reason-ref:authority-cli-default-mode-scope",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-default-mode-scope",
            "--summary",
            "Select approved safe local work with backend default domains.",
            "--approve",
            "--approved-by-actor-ref",
            "operator-ref:test-cli-default-approver",
            "--json",
        ]
    )
    assert default_cli_issue == 0
    default_cli_payload = json.loads(capsys.readouterr().out)
    assert default_cli_payload["receipt"]["requested_domains"] == {
        "workspace": ["read", "write", "execute"]
    }
    assert default_cli_payload["receipt"]["granted_domains"] == {
        "workspace": ["read", "write", "execute"]
    }
    assert default_cli_payload["approval_captured"] is True

    full_local_cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "full_local_workspace_session",
            "--reason-ref",
            "reason-ref:authority-cli-full-local-default",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-full-local-default",
            "--summary",
            "Select full local workspace with backend default domains.",
            "--approve",
            "--approved-by-actor-ref",
            "operator-ref:test-cli-full-local-approver",
            "--json",
        ]
    )
    assert full_local_cli_issue == 0
    full_local_cli_payload = json.loads(capsys.readouterr().out)
    assert full_local_cli_payload["receipt"]["requested_domains"]["contacts"] == [
        "read",
        "write",
        "mutate",
    ]
    assert full_local_cli_payload["receipt"]["requested_domains"]["browser"] == ["read"]
    assert full_local_cli_payload["receipt"]["requested_domains"][
        "provider_model_calls"
    ] == ["observe", "read"]
    assert full_local_cli_payload["receipt"]["granted_domains"]["contacts"] == [
        "read",
        "write",
        "mutate",
    ]
    assert full_local_cli_payload["receipt"]["denied_domain_refs"] == []
    assert full_local_cli_payload["receipt"]["unsupported_adapter_refs"] == []
    assert full_local_cli_payload["approval_captured"] is True

    full_machine_cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "full_machine_access_session",
            "--reason-ref",
            "reason-ref:authority-cli-full-machine-default",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-full-machine-default",
            "--summary",
            "Select full machine access with implemented exact-gated defaults.",
            "--approve",
            "--approved-by-actor-ref",
            "operator-ref:test-cli-full-machine-approver",
            "--json",
        ]
    )
    assert full_machine_cli_issue == 0
    full_machine_cli_payload = json.loads(capsys.readouterr().out)
    assert full_machine_cli_payload["receipt"]["requested_domains"][
        "provider_model_calls"
    ] == ["read", "execute"]
    assert full_machine_cli_payload["receipt"]["requested_domains"]["browser"] == [
        "read"
    ]
    assert full_machine_cli_payload["receipt"]["granted_domains"][
        "provider_model_calls"
    ] == ["read", "execute"]
    assert full_machine_cli_payload["receipt"]["denied_domain_refs"] == []
    assert full_machine_cli_payload["receipt"]["unsupported_adapter_refs"] == []
    assert full_machine_cli_payload["approval_captured"] is True

    conflicting_cli_issue = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "ask_before_changes",
            "--domain",
            "workspace:read,write",
            "--reason-ref",
            "reason-ref:authority-cli-conflict",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-conflict",
            "--summary",
            "Reject conflicting local authority approval inputs.",
            "--approve",
            "--approval-ref",
            "approval-ref:test-authority:conflict",
            "--json",
        ]
    )
    assert conflicting_cli_issue == 2

    revoke = client.post(
        "/api/runtime/authority-leases/revoke",
        headers={"x-uaa-idempotency-key": "idempotency-ref:authority-api-revoke"},
        json={
            "lease_ref": lease["lease_ref"],
            "decision_reason_ref": "reason-ref:authority-api-revoke",
            "safe_summary": "Revoke local workspace authority for this session.",
        },
    )
    assert revoke.status_code == 200
    assert revoke.json()["success"] is True
    revoke_receipt = revoke.json()["data"]["receipt"]
    assert revoke_receipt["status"] == "revoked"
    assert revoke_receipt["lease_issued_at"] == lease["issued_at"]
    assert revoke_receipt["lease_expires_at"] == lease["expires_at"]

    cli_revoke = uaa_runtime.main(
        [
            "revoke-authority-lease",
            "--lease-ref",
            lease["lease_ref"],
            "--reason-ref",
            "reason-ref:authority-cli-revoke",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-revoke",
            "--summary",
            "Revoke already-revoked authority lease for safe replay proof.",
            "--json",
        ]
    )
    assert cli_revoke == 0
    assert "uaa-runtime-revoke-authority-lease" in capsys.readouterr().out


def test_authority_lease_approve_and_issue_api_captures_exact_backend_approval(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ],
            AuthorityDomain.browser: [AuthorityCapability.click],
        },
        decision_reason_ref="reason-ref:authority-approve-issue-api",
        safe_summary="Select approved safe local authority for this session.",
    )
    response = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:authority-approve-issue-api"
        },
        json={
            "lease_issue_request": issue_request.model_dump(mode="json"),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    receipt = data["receipt"]
    requirement = data["approval_requirement"]
    assert data["approval_captured"] is True
    assert data["approval_grant_payload_persisted"] is False
    assert data["approval_ref"].startswith("approval-ref:authority-lease:")
    assert receipt["status"] == "issued"
    assert receipt["approval_required"] is True
    assert receipt["approval_validated"] is True
    assert receipt["approval_ref"] == data["approval_ref"]
    assert receipt["approval_scope_ref"] == requirement["approval_scope_ref"]
    assert requirement["approval_required"] is True
    assert requirement["operator_ref"] == AUTHORITY_LEASE_LOCAL_OPERATOR_REF
    assert data["lease"]["operator_ref"] == AUTHORITY_LEASE_LOCAL_OPERATOR_REF
    assert "authority-domain-ref:workspace" in requirement["resource_refs"]
    assert "authority-domain-ref:browser" not in requirement["resource_refs"]
    assert "authority-domain-ref:browser" in receipt["denied_domain_refs"]
    assert (
        "adapter-ref:browser:click-not-implemented-for-authority-lease-v1"
        in (receipt["unsupported_adapter_refs"])
    )

    state = client.get("/api/runtime/authority-state")
    assert state.status_code == 200
    assert state.json()["data"]["active_mode"] == "approved_safe_local_work_session"

    inline_grant = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:authority-approve-issue-inline-denied"
            )
        },
        json={
            "lease_issue_request": {
                **issue_request.model_dump(mode="json"),
                "approval_ref": "approval-ref:caller-supplied-denied",
            },
        },
    )
    assert inline_grant.status_code == 422


def test_authority_lease_public_issue_rejects_caller_supplied_unsigned_grant(
    tmp_path,
    monkeypatch,
) -> None:
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    idempotency_ref = "idempotency-ref:authority-forged-inline-grant"
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ]
        },
        decision_reason_ref="reason-ref:authority-forged-inline-grant",
        safe_summary="Attempt authority issuance with caller-authored approval data.",
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        issue_request,
        idempotency_ref=idempotency_ref,
    )
    forged_grant = build_authority_lease_test_grant(
        requirement,
        approval_ref="approval-ref:authority-forged-inline-grant",
        approved_by_actor_id="operator-ref:forged-caller",
    )
    payload = issue_request.model_dump(mode="json")
    payload.update(
        {
            "approval_ref": forged_grant.approval_ref,
            "approval_grants": [forged_grant.model_dump(mode="json")],
        }
    )

    response = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json=payload,
    )

    assert response.status_code == 422
    assert "extra_forbidden" in response.text
    assert AuthorityLeaseStore(authority_state_dir).list_leases() == []

    reference_only = client.post(
        "/api/runtime/authority-leases",
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:authority-forged-reference-only"
            )
        },
        json={
            **issue_request.model_dump(mode="json"),
            "approval_ref": forged_grant.approval_ref,
        },
    )
    assert reference_only.status_code == 200
    assert reference_only.json()["success"] is False
    assert reference_only.json()["data"]["lease"] is None
    assert reference_only.json()["data"]["receipt"]["approval_reason_codes"] == [
        "APPROVAL_REF_UNKNOWN"
    ]
    assert reference_only.json()["data"]["receipt"]["audit_ref"]
    assert AuthorityLeaseStore(authority_state_dir).list_leases() == []


def test_authority_lease_public_issue_resolves_exact_backend_owned_state(
    tmp_path,
    monkeypatch,
) -> None:
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    idempotency_ref = "idempotency-ref:authority-backend-approval-resolution"
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ]
        },
        decision_reason_ref="reason-ref:authority-backend-approval-resolution",
        safe_summary="Resolve one exact backend-owned authority approval.",
    )
    store = AuthorityLeaseStore(authority_state_dir)
    requirement, grant = capture_authority_lease_backend_approval(
        store,
        issue_request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-resolution",
    )
    assert grant is not None

    response = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json={
            **issue_request.model_dump(mode="json"),
            "approval_ref": grant.approval_ref,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["receipt"]["approval_scope_ref"] == (
        requirement.approval_scope_ref
    )
    records = AuthorityLeaseApprovalStore(authority_state_dir).list_records()
    assert len(records) == 1
    assert records[0].backend_owned is True
    assert records[0].caller_payload_accepted is False
    assert records[0].requirement == requirement


def test_authority_lease_backend_approval_scope_substitution_is_audited_and_terminal(
    tmp_path,
    monkeypatch,
) -> None:
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    idempotency_ref = "idempotency-ref:authority-backend-scope-substitution"
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.read]
        },
        decision_reason_ref="reason-ref:authority-backend-scope-original",
        safe_summary="Approve one exact backend-owned read scope.",
    )
    store = AuthorityLeaseStore(authority_state_dir)
    _requirement, grant = capture_authority_lease_backend_approval(
        store,
        issue_request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-scope-substitution",
    )
    assert grant is not None
    substituted_request = issue_request.model_copy(
        update={
            "requested_domains": {
                AuthorityDomain.workspace: [
                    AuthorityCapability.read,
                    AuthorityCapability.write,
                    AuthorityCapability.execute,
                ]
            }
        }
    )

    substituted = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json={
            **substituted_request.model_dump(mode="json"),
            "approval_ref": grant.approval_ref,
        },
    )
    assert substituted.status_code == 200
    substituted_body = substituted.json()
    assert substituted_body["success"] is False
    assert substituted_body["data"]["lease"] is None
    assert "APPROVAL_BACKEND_SCOPE_MISMATCH" in (
        substituted_body["data"]["receipt"]["approval_reason_codes"]
    )
    assert substituted_body["data"]["receipt"]["approval_status"] == "out_of_scope"
    assert len(store.list_receipts(limit=10)) == 1

    exact_retry = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json={
            **issue_request.model_dump(mode="json"),
            "approval_ref": grant.approval_ref,
        },
    )
    assert exact_retry.status_code == 200
    assert exact_retry.json()["success"] is False
    assert exact_retry.json()["error"]["code"] == (
        "AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT"
    )
    assert store.list_leases() == []


def test_authority_lease_backend_approval_expiry_and_tampering_fail_closed(
    tmp_path,
    monkeypatch,
) -> None:
    import ultimate_ai_agent.core.approvals.authority as approval_authority_module

    authority_state_dir = tmp_path / "authority"
    idempotency_ref = "idempotency-ref:authority-backend-expired"
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref="reason-ref:authority-backend-expired",
        safe_summary="Reject stale backend-owned approval state.",
    )
    store = AuthorityLeaseStore(authority_state_dir)
    _requirement, grant = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-expired",
    )
    assert grant is not None
    monkeypatch.setattr(
        approval_authority_module,
        "utc_now",
        lambda: grant.expires_at + timedelta(seconds=1),
    )
    lease, expired_receipt = issue_authority_lease_from_backend_state(
        store,
        request.model_copy(update={"approval_ref": grant.approval_ref}),
        idempotency_ref=idempotency_ref,
    )
    assert lease is None
    assert expired_receipt.status == "denied"
    assert expired_receipt.approval_status == "expired"
    assert expired_receipt.approval_reason_codes == ["APPROVAL_EXPIRED"]

    tamper_dir = tmp_path / "authority-tampered"
    tamper_store = AuthorityLeaseStore(tamper_dir)
    tamper_idempotency_ref = "idempotency-ref:authority-backend-tampered"
    _requirement, tamper_grant = capture_authority_lease_backend_approval(
        tamper_store,
        request,
        idempotency_ref=tamper_idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-tampered",
    )
    assert tamper_grant is not None
    approval_store = AuthorityLeaseApprovalStore(tamper_dir)
    state_payload = json.loads(approval_store.records_path.read_text(encoding="utf-8"))
    forged_signing_key = b"f" * 32
    forged_record = state_payload["records"][0]
    forged_record["grant"]["approved_by_actor_id"] = "operator-ref:forged-writer"
    forged_record_payload = {
        key: value
        for key, value in forged_record.items()
        if key != "record_authenticator_ref"
    }
    forged_record["record_authenticator_ref"] = (
        "authority-lease-approval-record-authenticator-ref:hmac-sha256:"
        + hmac.new(
            forged_signing_key,
            json.dumps(
                forged_record_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )
    forged_store_payload = {
        key: value
        for key, value in state_payload.items()
        if key != "store_authenticator_ref"
    }
    state_payload["store_authenticator_ref"] = (
        "authority-lease-approval-store-authenticator-ref:hmac-sha256:"
        + hmac.new(
            forged_signing_key,
            json.dumps(
                forged_store_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )
    approval_store.records_path.write_text(
        json.dumps(state_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    caller_writable_key = tamper_dir / "authority_lease_approvals.key"
    caller_writable_key.write_bytes(forged_signing_key)
    caller_writable_key.chmod(0o600)
    tampered_lease, tampered_receipt = issue_authority_lease_from_backend_state(
        tamper_store,
        request.model_copy(update={"approval_ref": tamper_grant.approval_ref}),
        idempotency_ref=tamper_idempotency_ref,
    )
    assert tampered_lease is None
    assert tampered_receipt.status == "denied"
    assert tampered_receipt.approval_reason_codes == [
        "APPROVAL_BACKEND_STATE_INVALID"
    ]
    assert tampered_receipt.raw_paths_included is False
    assert tampered_receipt.raw_prompt_included is False
    assert tampered_receipt.raw_response_included is False
    assert tampered_receipt.raw_provider_payload_included is False
    assert tampered_receipt.redactions_applied
    assert tamper_store.list_leases() == []
    assert not approval_store.signing_key_path.is_relative_to(tamper_dir)
    assert approval_store.signing_key_dir.stat().st_mode & 0o077 == 0
    assert approval_store.signing_key_path.stat().st_mode & 0o077 == 0
    assert approval_store.signing_key_path.stat().st_size == 32
    assert caller_writable_key.read_bytes() == forged_signing_key
    assert "signing_key" not in approval_store.records_path.read_text(encoding="utf-8")


def test_authority_lease_expired_backend_approval_is_recaptured_after_confirmation(
    tmp_path,
    monkeypatch,
) -> None:
    import ultimate_ai_agent.core.approvals.authority as approval_authority_module
    import ultimate_ai_agent.core.authority.approval_validation as validation_module

    state_dir = tmp_path / "authority-recapture"
    idempotency_ref = "idempotency-ref:authority-backend-recapture"
    approval_ref = "approval-ref:authority-backend-recapture"
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref="reason-ref:authority-backend-recapture",
        safe_summary="Recapture one expired exact backend approval after confirmation.",
    )
    store = AuthorityLeaseStore(state_dir)
    requirement, first_grant = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref=approval_ref,
    )
    assert first_grant is not None
    assert first_grant.expires_at is not None
    recapture_time = first_grant.expires_at + timedelta(seconds=1)
    monkeypatch.setattr(validation_module, "utc_now", lambda: recapture_time)
    monkeypatch.setattr(approval_authority_module, "utc_now", lambda: recapture_time)

    recaptured_requirement, recaptured_grant = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref=approval_ref,
    )

    assert recaptured_requirement == requirement
    assert recaptured_grant is not None
    assert recaptured_grant.approval_ref == first_grant.approval_ref
    assert recaptured_grant.created_at == recapture_time
    assert recaptured_grant.expires_at > first_grant.expires_at
    approval_state = json.loads(
        AuthorityLeaseApprovalStore(state_dir).records_path.read_text(encoding="utf-8")
    )
    assert approval_state["generation"] == 2
    assert len(approval_state["records"]) == 1

    lease, receipt = issue_authority_lease_from_backend_state(
        store,
        request.model_copy(update={"approval_ref": approval_ref}),
        idempotency_ref=idempotency_ref,
    )
    assert lease is not None
    assert receipt.status == "issued"
    assert receipt.approval_validated is True


def test_authority_lease_signing_key_recovers_interrupted_publish_link(
    tmp_path,
) -> None:
    state_dir = tmp_path / "authority-key-recovery"
    store = AuthorityLeaseStore(state_dir)
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref="reason-ref:authority-key-recovery",
        safe_summary="Recover an interrupted backend signing key publication.",
    )
    capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref="idempotency-ref:authority-key-recovery",
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-key-recovery",
    )
    approval_store = AuthorityLeaseApprovalStore(state_dir)
    interrupted_temp = approval_store.signing_key_path.with_name(
        f".{approval_store.signing_key_path.name}.interrupted.tmp"
    )
    os.link(approval_store.signing_key_path, interrupted_temp)
    assert approval_store.signing_key_path.stat().st_nlink == 2

    records = approval_store.list_records()

    assert len(records) == 1
    assert interrupted_temp.exists() is False
    assert approval_store.signing_key_path.stat().st_nlink == 1


@pytest.mark.parametrize(
    "request_update",
    (
        {"duration_minutes": 480},
        {"constraints": {"workspace_ref": "workspace-ref:substituted"}},
    ),
)
def test_authority_lease_backend_approval_binds_complete_lease_scope(
    tmp_path,
    monkeypatch,
    request_update,
) -> None:
    suffix = next(iter(request_update))
    state_dir = tmp_path / f"authority-scope-{suffix}"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))
    idempotency_ref = f"idempotency-ref:authority-scope-{suffix}"
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref=f"reason-ref:authority-scope-{suffix}",
        duration_minutes=5,
        constraints={"workspace_ref": "workspace-ref:approved"},
        safe_summary="Bind every authority-bearing lease field to approval scope.",
    )
    store = AuthorityLeaseStore(state_dir)
    _requirement, grant = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref=f"approval-ref:authority-scope-{suffix}",
    )
    assert grant is not None

    response = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json={
            **request.model_copy(update=request_update).model_dump(mode="json"),
            "approval_ref": grant.approval_ref,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["data"]["lease"] is None
    assert response.json()["data"]["receipt"]["approval_reason_codes"] == [
        "APPROVAL_BACKEND_SCOPE_MISMATCH"
    ]
    assert store.list_leases() == []


def test_authority_lease_backend_approval_store_is_bounded_and_idempotent(
    tmp_path,
    monkeypatch,
) -> None:
    import ultimate_ai_agent.core.authority.approval_validation as validation_module

    monkeypatch.setattr(validation_module, "AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT", 1)
    store = AuthorityLeaseStore(tmp_path / "authority")
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref="reason-ref:authority-backend-capacity",
        safe_summary="Bound durable backend-owned approval state.",
    )
    requirement, first = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref="idempotency-ref:authority-backend-capacity-first",
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-capacity-first",
    )
    replay_requirement, replayed = capture_authority_lease_backend_approval(
        store,
        request,
        idempotency_ref="idempotency-ref:authority-backend-capacity-first",
        approved_by_actor_id="operator-ref:test-backend-approver",
        approval_ref="approval-ref:authority-backend-capacity-first",
    )
    assert first == replayed
    assert requirement == replay_requirement
    state_payload = json.loads(
        AuthorityLeaseApprovalStore(store.state_dir).records_path.read_text(
            encoding="utf-8"
        )
    )
    assert state_payload["generation"] == 1
    assert len(state_payload["records"]) == 1
    with pytest.raises(
        AuthorityLeaseApprovalCapacityError,
        match="AUTHORITY_LEASE_APPROVAL_CAPACITY_EXHAUSTED",
    ):
        capture_authority_lease_backend_approval(
            store,
            request,
            idempotency_ref="idempotency-ref:authority-backend-capacity-second",
            approved_by_actor_id="operator-ref:test-backend-approver",
            approval_ref="approval-ref:authority-backend-capacity-second",
        )

    api_state_dir = tmp_path / "authority-api-capacity"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(api_state_dir))
    monkeypatch.setattr(validation_module, "AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT", 0)
    response = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:authority-backend-capacity-api"
            )
        },
        json={"lease_issue_request": request.model_dump(mode="json")},
    )
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["data"]["lease"] is None
    assert response.json()["data"]["approval_captured"] is False
    assert response.json()["data"]["receipt"]["approval_reason_codes"] == [
        "APPROVAL_BACKEND_CAPACITY_EXHAUSTED"
    ]
    assert AuthorityLeaseStore(api_state_dir).list_receipts(limit=10)

    monkeypatch.setattr(validation_module, "AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT", 1)
    retry = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:authority-backend-capacity-api"
            )
        },
        json={"lease_issue_request": request.model_dump(mode="json")},
    )
    assert retry.status_code == 200
    assert retry.json()["success"] is False
    assert retry.json()["data"]["lease"] is None
    assert retry.json()["data"]["receipt"]["status"] == "denied"
    assert retry.json()["data"]["receipt"]["approval_reason_codes"] == [
        "APPROVAL_BACKEND_CAPACITY_EXHAUSTED"
    ]
    assert AuthorityLeaseStore(api_state_dir).list_leases() == []


def test_authority_lease_lock_failures_are_redacted_across_api_and_cli(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    invalid_state_path = tmp_path / "authority-state-is-not-a-directory"
    invalid_state_path.write_text("not a directory\n", encoding="utf-8")
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(invalid_state_path))
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode.approved_safe_local_work_session,
        requested_domains={
            AuthorityDomain.workspace: [AuthorityCapability.execute]
        },
        decision_reason_ref="reason-ref:authority-lock-unavailable",
        safe_summary="Fail closed when backend approval locking is unavailable.",
    )

    for route, payload, suffix in (
        (
            "/api/runtime/authority-leases",
            issue_request.model_dump(mode="json"),
            "issue",
        ),
        (
            "/api/runtime/authority-leases/approve-and-issue",
            {"lease_issue_request": issue_request.model_dump(mode="json")},
            "approve",
        ),
    ):
        response = client.post(
            route,
            headers={
                "x-uaa-idempotency-key": f"idempotency-ref:authority-lock-{suffix}"
            },
            json=payload,
        )
        assert response.status_code == 200
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "APPROVAL_BACKEND_STATE_INVALID"
        assert response.json()["error"]["details_redacted"] is True
        assert str(tmp_path) not in response.text

    cli_result = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "approved_safe_local_work_session",
            "--domain",
            "workspace:execute",
            "--reason-ref",
            "reason-ref:authority-lock-cli",
            "--idempotency-ref",
            "idempotency-ref:authority-lock-cli",
            "--summary",
            "Fail closed without exposing the backend approval path.",
            "--approve",
        ]
    )
    cli_output = capsys.readouterr()
    assert cli_result == 1
    assert cli_output.out == ""
    assert "backend-owned authority approval state is unavailable" in cli_output.err
    assert str(tmp_path) not in cli_output.err


def test_authority_lease_openapi_and_cli_reject_grant_payload_inputs(
    capsys,
    tmp_path,
    monkeypatch,
) -> None:
    schema = app.openapi()["components"]["schemas"]["AuthorityLeaseIssueRequest"]
    assert "approval_ref" in schema["properties"]
    assert "approval_grants" not in schema["properties"]
    with pytest.raises(SystemExit) as exc_info:
        uaa_runtime.main(
            [
                "select-authority-mode",
                "--mode",
                "approved_safe_local_work_session",
                "--reason-ref",
                "reason-ref:authority-cli-caller-grant-denied",
                "--idempotency-ref",
                "idempotency-ref:authority-cli-caller-grant-denied",
                "--summary",
                "Reject caller-authored approval grant data from the CLI.",
                "--approval-ref",
                "approval-ref:authority-cli-caller-grant-denied",
                "--approval-grant-json",
                "{}",
            ]
        )
    assert exc_info.value.code == 2
    assert "unrecognized arguments: --approval-grant-json" in capsys.readouterr().err

    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    command = [
        "select-authority-mode",
        "--mode",
        "approved_safe_local_work_session",
        "--reason-ref",
        "reason-ref:authority-cli-approval-conflict",
        "--idempotency-ref",
        "idempotency-ref:authority-cli-approval-conflict",
        "--summary",
        "Reject conflicting backend-owned approval provenance from the CLI.",
        "--approve",
        "--approved-by-actor-ref",
    ]
    assert uaa_runtime.main([*command, "operator-ref:first-cli-approver"]) == 0
    capsys.readouterr()
    assert uaa_runtime.main([*command, "operator-ref:second-cli-approver"]) == 2
    conflict_output = capsys.readouterr()
    assert conflict_output.out == ""
    assert "backend-owned authority approval state conflicts" in conflict_output.err
    assert str(tmp_path) not in conflict_output.err
    assert len(AuthorityLeaseStore(authority_state_dir).list_leases()) == 1
    assert len(AuthorityLeaseStore(authority_state_dir).list_receipts(limit=10)) == 1

    invalid_state_dir = tmp_path / "authority-invalid-cli-state"
    invalid_state_dir.mkdir()
    invalid_records_path = invalid_state_dir / "authority_lease_approvals.json"
    invalid_records_path.write_text("{}\n", encoding="utf-8")
    invalid_records_path.chmod(0o600)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(invalid_state_dir))
    invalid_state_result = uaa_runtime.main(
        [
            "select-authority-mode",
            "--mode",
            "approved_safe_local_work_session",
            "--reason-ref",
            "reason-ref:authority-cli-invalid-backend-state",
            "--idempotency-ref",
            "idempotency-ref:authority-cli-invalid-backend-state",
            "--summary",
            "Report invalid backend approval state without exposing raw data.",
            "--approval-ref",
            "approval-ref:authority-cli-invalid-backend-state",
        ]
    )
    assert invalid_state_result == 1
    invalid_state_output = capsys.readouterr().out
    assert "Approval reasons: APPROVAL_BACKEND_STATE_INVALID" in (invalid_state_output)
    assert "Blocked reasons: none" in invalid_state_output
    assert str(tmp_path) not in invalid_state_output


def _exact_workspace_constraints(*, path_ref: str) -> list[AuthorityConstraint]:
    return [
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-workspace-resource",
            kind=AuthorityConstraintKind.resource_refs,
            allowed_refs=["resource-ref:test-run"],
            safe_summary="Limit the action to one exact run resource ref.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-workspace-path",
            kind=AuthorityConstraintKind.path_refs,
            allowed_refs=[path_ref],
            safe_summary="Limit the action to one approved workspace path ref.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-workspace-app",
            kind=AuthorityConstraintKind.app_refs,
            allowed_refs=["app-ref:test-control-center"],
            safe_summary="Limit the action to the local Control Center app ref.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-workspace-host",
            kind=AuthorityConstraintKind.host_refs,
            allowed_refs=["host-ref:test-loopback"],
            safe_summary="Limit the action to one loopback host ref.",
        ),
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-delegation-depth",
            kind=AuthorityConstraintKind.delegation_depth,
            maximum=1,
            safe_summary="Limit delegated execution to one child level.",
        ),
    ]


def _exact_workspace_constraint_claims(
    *,
    path_ref: str = "path-ref:test-workspace-src",
    include_host: bool = True,
    delegation_depth: int = 1,
) -> list[AuthorityConstraintClaim]:
    claims = [
        AuthorityConstraintClaim(
            kind=AuthorityConstraintKind.path_refs,
            refs=[path_ref],
        ),
        AuthorityConstraintClaim(
            kind=AuthorityConstraintKind.app_refs,
            refs=["app-ref:test-control-center"],
        ),
        AuthorityConstraintClaim(
            kind=AuthorityConstraintKind.delegation_depth,
            value=delegation_depth,
        ),
    ]
    if include_host:
        claims.append(
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.host_refs,
                refs=["host-ref:test-loopback"],
            )
        )
    return claims


def test_authority_lease_constraints_fail_closed_and_select_exact_matching_lease() -> (
    None
):
    constrained = AuthorityLease(
        lease_ref="authority-lease-ref:test-constrained-workspace",
        mode=TrustMode.full_local_workspace_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        authority_constraints=_exact_workspace_constraints(
            path_ref="path-ref:test-workspace-src"
        ),
        safe_summary="Grant exact constrained workspace execution for this session.",
    )
    other_path = constrained.model_copy(
        update={
            "lease_ref": "authority-lease-ref:test-constrained-other-path",
            "authority_constraints": _exact_workspace_constraints(
                path_ref="path-ref:test-workspace-docs"
            ),
        }
    )
    action = AuthorityActionRequest(
        action_ref="authority-action-ref:test-constrained-workspace",
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
        resource_refs=["resource-ref:test-run"],
        constraint_claims=_exact_workspace_constraint_claims(),
        safe_summary="Execute one exact constrained workspace action.",
    )

    allowed = evaluate_authority_request(action, [other_path, constrained])
    missing = evaluate_authority_request(
        action.model_copy(
            update={
                "action_ref": "authority-action-ref:test-constraint-missing-host",
                "constraint_claims": _exact_workspace_constraint_claims(
                    include_host=False
                ),
            }
        ),
        [constrained],
    )
    wrong_path = evaluate_authority_request(
        action.model_copy(
            update={
                "action_ref": "authority-action-ref:test-constraint-wrong-path",
                "constraint_claims": _exact_workspace_constraint_claims(
                    path_ref="path-ref:test-workspace-private"
                ),
            }
        ),
        [constrained],
    )
    excess_delegation = evaluate_authority_request(
        action.model_copy(
            update={
                "action_ref": "authority-action-ref:test-constraint-depth",
                "constraint_claims": _exact_workspace_constraint_claims(
                    delegation_depth=2
                ),
            }
        ),
        [constrained],
    )

    assert allowed.outcome == AuthorityDecisionOutcome.allow.value
    assert allowed.lease_ref == constrained.lease_ref
    assert allowed.applied_constraint_refs == [
        constraint.constraint_ref for constraint in constrained.authority_constraints
    ]
    assert missing.outcome == AuthorityDecisionOutcome.deny.value
    assert (
        "reason-ref:authority:constraint-claim-missing:host_refs" in missing.reason_refs
    )
    assert wrong_path.outcome == AuthorityDecisionOutcome.deny.value
    assert (
        "reason-ref:authority:constraint-ref-outside-scope:path_refs"
        in wrong_path.reason_refs
    )
    assert excess_delegation.outcome == AuthorityDecisionOutcome.deny.value
    assert (
        "reason-ref:authority:constraint-limit-exceeded:delegation_depth"
        in excess_delegation.reason_refs
    )


def test_authority_constraint_rejects_raw_path_and_duplicate_claim_kind() -> None:
    with pytest.raises(ValueError):
        AuthorityConstraint(
            constraint_ref="authority-constraint-ref:test-raw-path-denied",
            kind=AuthorityConstraintKind.path_refs,
            allowed_refs=["/private/workspace/path"],
            safe_summary="Raw paths are never valid authority constraints.",
        )
    with pytest.raises(ValueError, match="AUTHORITY_ACTION_DUPLICATE_CONSTRAINT"):
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-duplicate-constraint-claim",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            constraint_claims=[
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.path_refs,
                    refs=["path-ref:test-one"],
                ),
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.path_refs,
                    refs=["path-ref:test-two"],
                ),
            ],
            safe_summary="Duplicate constraint kinds are denied.",
        )


def test_constraint_scope_binds_approval_lease_identity_and_idempotency(
    tmp_path,
) -> None:
    idempotency_ref = "idempotency-ref:test-constrained-lease-issue"
    base = AuthorityLeaseIssueRequest(
        mode=TrustMode.full_local_workspace_session,
        requested_domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        authority_constraints=_exact_workspace_constraints(
            path_ref="path-ref:test-workspace-src"
        ),
        decision_reason_ref="reason-ref:test-constrained-lease-issue",
        safe_summary="Issue one exact constrained workspace lease.",
    )
    changed = base.model_copy(
        update={
            "authority_constraints": _exact_workspace_constraints(
                path_ref="path-ref:test-workspace-docs"
            )
        }
    )
    base_requirement = build_authority_lease_approval_requirement_for_request(
        base,
        idempotency_ref=idempotency_ref,
    )
    changed_requirement = build_authority_lease_approval_requirement_for_request(
        changed,
        idempotency_ref=idempotency_ref,
    )
    store = AuthorityLeaseStore(tmp_path / "authority")
    approved = _approved_issue_request(
        base,
        idempotency_ref=idempotency_ref,
        approval_ref="approval-ref:test-constrained-lease-issue",
        store=store,
    )
    approved_changed = approved.model_copy(
        update={"authority_constraints": changed.authority_constraints}
    )
    lease, receipt = store.issue_lease(
        approved,
        idempotency_ref=idempotency_ref,
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    replayed_lease, replayed_receipt = store.issue_lease(
        approved,
        idempotency_ref=idempotency_ref,
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )

    assert base_requirement.approval_scope_ref != changed_requirement.approval_scope_ref
    assert lease is not None
    assert lease.authority_constraints == base.authority_constraints
    assert receipt.request_fingerprint_ref is not None
    assert replayed_lease == lease
    assert replayed_receipt.status == "replayed"
    for index in range(205):
        store._append_receipt(
            receipt.model_copy(
                update={
                    "receipt_ref": f"receipt-ref:test-filler:{index}",
                    "idempotency_ref": f"idempotency-ref:test-filler:{index}",
                    "request_fingerprint_ref": (
                        f"request-fingerprint-ref:test-filler:{index}"
                    ),
                }
            )
        )
    old_replayed_lease, old_replayed_receipt = store.issue_lease(
        approved,
        idempotency_ref=idempotency_ref,
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )
    assert old_replayed_lease == lease
    assert old_replayed_receipt.status == "replayed"
    with pytest.raises(
        AuthorityLeaseConflictError,
        match="AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT",
    ):
        store.issue_lease(
            approved_changed,
            idempotency_ref=idempotency_ref,
            approval_validator=authority_lease_approval_validator(store.state_dir),
        )
    store._append_receipt(
        receipt.model_copy(
            update={
                "receipt_ref": "receipt-ref:test-conflicting-history",
                "request_fingerprint_ref": (
                    "request-fingerprint-ref:test-conflicting-history"
                ),
            }
        )
    )
    with pytest.raises(
        AuthorityLeaseConflictError,
        match="AUTHORITY_LEASE_IDEMPOTENCY_HISTORY_CONFLICT",
    ):
        store.issue_lease(
            approved,
            idempotency_ref=idempotency_ref,
            approval_validator=authority_lease_approval_validator(store.state_dir),
        )


def test_denied_issue_idempotency_cannot_be_reused_with_later_approval(
    tmp_path,
) -> None:
    idempotency_ref = "idempotency-ref:test-denied-then-approved-conflict"
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode.full_local_workspace_session,
        requested_domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        authority_constraints=_exact_workspace_constraints(
            path_ref="path-ref:test-workspace-src"
        ),
        decision_reason_ref="reason-ref:test-denied-then-approved-conflict",
        safe_summary="Issue one exact constrained workspace lease.",
    )
    store = AuthorityLeaseStore(tmp_path / "authority")
    lease, denied_receipt = store.issue_lease(
        request,
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    approved = _approved_issue_request(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref="approval-ref:test-denied-then-approved-conflict",
        store=store,
    )

    assert lease is None
    assert denied_receipt.status == "denied"
    with pytest.raises(
        AuthorityLeaseConflictError,
        match="AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT",
    ):
        store.issue_lease(
            approved,
            idempotency_ref=idempotency_ref,
            approval_validator=authority_lease_approval_validator(store.state_dir),
        )
