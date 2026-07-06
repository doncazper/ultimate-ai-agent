from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseStore,
    AuthorityMissionPlanRequest,
    TrustMode,
    build_authority_mission_plan,
    build_authority_state_read_model,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeAuthority,
    RuntimeInvocationRequest,
    RuntimeProfile,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import build_policy_decision


client = TestClient(app)


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
    task_decomposition_execute = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /task-decomposition/plans/execute" in mapping.route_refs
    )
    assert task_decomposition_execute.domain == "workspace"
    assert task_decomposition_execute.capability == "execute"
    assert task_decomposition_execute.required_mode == "approved_safe_local_work_session"
    assert (
        task_decomposition_execute.status
        == "implemented_exact_lease_required_local_orchestration"
    )
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
    file_write_proposal = next(
        mapping
        for mapping in read_model.capability_mappings
        if "POST /files/write/propose" in mapping.route_refs
    )
    assert file_write_proposal.domain == "files"
    assert file_write_proposal.capability == "prepare"
    assert file_write_proposal.status == "implemented_exact_lease_required_proposal_only"
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
    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": "idempotency-ref:authority-api-mission"},
        json={
            "mode": "approved_safe_local_work_session",
            "scope": "mission",
            "mission_ref": "mission-ref:test-api-workspace-maintenance",
            "requested_domains": {
                "workspace": ["execute"],
            },
            "decision_reason_ref": "reason-ref:authority-api-mission",
            "safe_summary": "Select mission workspace authority.",
        },
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
    assert "reason-ref:authority:mission-scope-mismatch" in (
        unrelated.json()["data"]["decision"]["reason_refs"]
    )
    assert matched.status_code == 200
    assert matched.json()["data"]["decision"]["outcome"] == "allow"
    assert matched.json()["data"]["decision"]["lease_ref"] == (
        issue.json()["data"]["lease"]["lease_ref"]
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


def test_authority_state_api_cli_and_settings_surface(capsys) -> None:
    runtime_response = client.get("/api/runtime/authority-state")
    settings_response = client.get("/control-center/settings/status")
    exit_code = uaa_runtime.main(["inspect-authority-state", "--json"])

    assert runtime_response.status_code == 200
    runtime_body = runtime_response.json()
    assert runtime_body["success"] is True
    assert runtime_body["data"]["active_mode"] == "read_only"
    assert runtime_body["data"]["unknown_authority_default"] == "deny"

    assert settings_response.status_code == 200
    settings_body = settings_response.json()
    authority_state = settings_body["data"]["authority_lease_state"]
    assert authority_state["api_ref"] == "GET /api/runtime/authority-state"
    assert authority_state["kill_switch_visible"] is True
    assert authority_state["unsupported_adapters_claimed_execution"] is False

    assert exit_code == 0
    cli_payload = capsys.readouterr().out
    assert "authority_state_read_model" in cli_payload
    assert "raw_paths_omitted" in cli_payload


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

    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": "idempotency-ref:authority-preview-issue"},
        json={
            "mode": "approved_safe_local_work_session",
            "requested_domains": {"workspace": ["read", "execute"]},
            "decision_reason_ref": "reason-ref:authority-preview-issue",
            "safe_summary": "Select workspace execute authority for preview testing.",
        },
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
    assert "adapter-unsupported" in cli_payload
    assert "execution_performed" in cli_payload


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
    assert {
        preview.decision.outcome for preview in draft_plan.action_previews
    } == {"degrade_to_draft"}
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
    lease, receipt = AuthorityLeaseStore(tmp_path / "authority").issue_lease(
        issue_ready_plan.lease_issue_request,
        idempotency_ref="idempotency-ref:test-core-workspace-mission-issue",
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

    issue = client.post(
        "/api/runtime/authority-leases",
        headers={"x-uaa-idempotency-key": "idempotency-ref:authority-api-issue"},
        json={
            "mode": "approved_safe_local_work_session",
            "requested_domains": {
                "workspace": ["read", "write", "execute"],
                "contacts": ["write"],
                "browser": ["click"],
                "provider_model_calls": ["execute"],
            },
            "decision_reason_ref": "reason-ref:authority-api-issue",
            "safe_summary": "Select local workspace authority for this session.",
        },
    )
    assert issue.status_code == 200
    body = issue.json()
    assert body["success"] is True
    receipt = body["data"]["receipt"]
    lease = body["data"]["lease"]
    assert receipt["status"] == "issued"
    assert receipt["execution_performed"] is False
    assert receipt["granted_domains"]["workspace"] == ["read", "write", "execute"]
    assert receipt["granted_domains"]["contacts"] == ["write"]
    assert "authority-domain-ref:browser" in receipt["denied_domain_refs"]
    assert "authority-domain-ref:provider_model_calls" in (
        receipt["denied_domain_refs"]
    )
    assert "adapter-ref:browser:not-implemented-for-authority-lease-v1" in (
        receipt["unsupported_adapter_refs"]
    )
    assert (
        "adapter-ref:provider_model_calls:execute"
        "-not-implemented-for-authority-lease-v1"
    ) in receipt["unsupported_adapter_refs"]

    state = client.get("/api/runtime/authority-state")
    assert state.status_code == 200
    state_data = state.json()["data"]
    assert state_data["active_mode"] == "approved_safe_local_work_session"
    assert state_data["active_leases"][0]["lease_ref"] == lease["lease_ref"]
    assert state_data["recent_receipts"][0]["receipt_ref"] == receipt["receipt_ref"]

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
            "idempotency-ref:authority-cli-issue",
            "--summary",
            "Select ask-before-changes workspace authority.",
            "--json",
        ]
    )
    assert cli_issue == 0
    cli_payload = capsys.readouterr().out
    assert "uaa-runtime-select-authority-mode" in cli_payload
    assert "receipt-ref:authority-lease" in cli_payload

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
    assert revoke.json()["data"]["receipt"]["status"] == "revoked"

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
