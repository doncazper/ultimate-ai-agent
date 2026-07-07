from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_STATE_DIR_ENV,
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    AuthorityMissionPlanRequest,
    TrustMode,
    build_authority_lease_approval_requirement_for_request,
    build_authority_mission_plan,
    build_authority_state_read_model,
    build_default_authority_leases,
    authority_lease_kill_switch_engaged,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_test_grant,
    validate_authority_lease_approval,
)
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
) -> AuthorityLeaseIssueRequest:
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if not requirement.approval_required:
        return request
    grant = build_authority_lease_test_grant(
        requirement,
        approval_ref=approval_ref,
    )
    return request.model_copy(
        update={
            "approval_ref": grant.approval_ref,
            "approval_grants": [grant.model_dump(mode="json")],
        }
    )


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
    assert mode_catalog["full_local_workspace_session"].issue_ready is True
    assert mode_catalog["full_local_workspace_session"].approval_required is True
    assert mode_catalog["full_machine_access_session"].issue_ready is False
    assert (
        mode_catalog["full_machine_access_session"].status
        == "blocked_default_scope_unsupported"
    )
    assert mode_catalog["full_machine_access_session"].unsupported_adapter_refs
    assert mode_catalog["delegated_mission_autonomous_window"].issue_ready is False
    assert (
        mode_catalog["delegated_mission_autonomous_window"].requires_mission_ref is True
    )
    assert "reason-ref:authority:adapter-unsupported" in (
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
    assert (
        messaging_gateway_posture.status == "implemented_authority_bound_read_model"
    )
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
    assert (
        remote_execution_posture.status == "implemented_authority_bound_read_model"
    )
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
    assert (
        plugin_metadata_posture.status == "implemented_authority_bound_read_model"
    )
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
    assert (
        skill_marketplace_posture.status == "implemented_authority_bound_read_model"
    )
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
    assert "GET /api/runtime/capability-discovery" in (
        capability_discovery.route_refs
    )
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
        catalog_by_lane[
            "lane-ref:runtime-approval-bridge-read-model"
        ].decision.outcome
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


def test_authority_mode_defaults_are_mode_specific_and_fail_closed(
    tmp_path,
) -> None:
    store = AuthorityLeaseStore(tmp_path / "authority")

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
        ),
        idempotency_ref="idempotency-ref:test-safe-local-default",
        approval_validator=validate_authority_lease_approval,
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

    full_machine_lease, full_machine_receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.full_machine_access_session,
            decision_reason_ref="reason-ref:test-full-machine-default",
            safe_summary="Select default full machine authority.",
        ),
        idempotency_ref="idempotency-ref:test-full-machine-default",
    )
    assert full_machine_lease is None
    assert full_machine_receipt.status == "denied"
    assert full_machine_receipt.granted_domains == {}
    assert "authority-domain-ref:browser" in full_machine_receipt.denied_domain_refs
    assert "authority-domain-ref:shell" in full_machine_receipt.denied_domain_refs
    assert any(
        ref.startswith("adapter-ref:browser:")
        for ref in full_machine_receipt.unsupported_adapter_refs
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
        ),
        idempotency_ref="idempotency-ref:test-full-machine-provider-explicit",
        approval_validator=validate_authority_lease_approval,
    )
    assert provider_lease is not None
    assert provider_receipt.status == "issued"
    assert provider_receipt.approval_validated is True
    assert provider_receipt.granted_domains == {
        "provider_model_calls": ["read", "execute"]
    }
    assert provider_receipt.denied_domain_refs == []

    delegated_lease, delegated_receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope="mission",
            mission_ref="mission-ref:test-delegated-default",
            decision_reason_ref="reason-ref:test-delegated-default",
            safe_summary="Select default delegated mission authority.",
        ),
        idempotency_ref="idempotency-ref:test-delegated-default",
    )
    assert delegated_lease is None
    assert delegated_receipt.status == "denied"
    assert delegated_receipt.granted_domains == {}
    assert "authority-domain-ref:browser" in delegated_receipt.denied_domain_refs
    assert "authority-domain-ref:shopping_payments" in (
        delegated_receipt.denied_domain_refs
    )
    assert any(
        ref.startswith("adapter-ref:shopping_payments:")
        for ref in delegated_receipt.unsupported_adapter_refs
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
        ),
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
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
            "approved_by_actor_ref": "operator-ref:test-control-center",
            "approval_safe_summary": (
                "Operator approved the exact local workspace authority lease."
            ),
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
    assert runtime_modes["full_machine_access_session"]["issue_ready"] is False
    assert runtime_modes["full_machine_access_session"]["unsupported_adapter_refs"]
    assert len(runtime_body["data"]["decision_catalog"]) == len(
        runtime_body["data"]["capability_mappings"]
    )
    assert runtime_body["data"]["decision_summary"]["total_capabilities"] == len(
        runtime_body["data"]["decision_catalog"]
    )
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

    assert exit_code == 0
    cli_payload = capsys.readouterr().out
    assert "authority_state_read_model" in cli_payload
    assert "mode_catalog" in cli_payload
    assert "decision_summary" in cli_payload
    assert "decision_catalog" in cli_payload
    assert "raw_paths_omitted" in cli_payload

    text_exit_code = uaa_runtime.main(["inspect-authority-state"])
    assert text_exit_code == 0
    cli_text = capsys.readouterr().out
    assert "issued=" in cli_text
    assert "expires=" in cli_text
    assert "Mode readiness:" in cli_text
    assert "full_machine_access_session" in cli_text
    assert "blocked_default_scope_unsupported" in cli_text
    assert "Decision catalog:" in cli_text
    assert "Decision summary:" in cli_text
    assert "Outcome counts:" in cli_text
    assert "Blocked reasons:" in cli_text
    assert "authority-capability-ref:runtime-command-focused-pytest" in cli_text
    assert "source: lane-ref:runtime-command-focused-pytest" in cli_text

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
    lease, receipt = AuthorityLeaseStore(tmp_path / "authority").issue_lease(
        _approved_issue_request(
            issue_ready_plan.lease_issue_request,
            idempotency_ref=mission_issue_idempotency_ref,
            approval_ref="approval-ref:test-authority:core-workspace-mission",
        ),
        idempotency_ref=mission_issue_idempotency_ref,
        approval_validator=validate_authority_lease_approval,
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
            "approved_by_actor_ref": "operator-ref:test-control-center",
            "approval_safe_summary": (
                "Operator approved the exact local workspace authority lease."
            ),
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
            "approved_by_actor_ref": "operator-ref:test-control-center",
        },
    )
    assert inline_grant.status_code == 422
