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
    TrustMode,
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
