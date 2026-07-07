from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)


def test_local_approval_authority_grant_validates() -> None:
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is True
    assert decision.status == ApprovalDecisionStatus.approved
    assert decision.matched_grant_ref == grant.approval_ref


def test_unknown_approval_ref_is_invalid() -> None:
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())

    decision = authority.validate_for_request(request, "human_approved_ref_123")

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.invalid
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes


def test_test_approval_ref_requires_local_authority_fixture() -> None:
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.create_test_grant(request.approval_request_id, approval_ref="approval_test_fixture")

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is True
    assert decision.matched_grant_ref == "approval_test_fixture"


def test_local_approval_authority_evaluates_loaded_authority_lease_scope() -> None:
    authority = LocalApprovalAuthority()
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:approval-authority-workspace-execute",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        safe_summary="Approval authority test lease grants workspace execute.",
    )
    authority.load_authority_lease_for_validation(lease)

    decision = authority.evaluate_authority_scope(
        AuthorityActionRequest(
            action_ref="authority-action-ref:approval-authority-workspace-execute",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            requested_mode=TrustMode.approved_safe_local_work_session,
            safe_summary="Evaluate workspace execute through LocalApprovalAuthority.",
        )
    )

    assert decision.outcome == AuthorityDecisionOutcome.allow.value
    assert decision.lease_ref == lease.lease_ref
    assert decision.known_authority is True


def test_local_approval_authority_does_not_invent_default_lease() -> None:
    authority = LocalApprovalAuthority()
    request = AuthorityActionRequest(
        action_ref="authority-action-ref:approval-authority-read-without-lease",
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.read,
        safe_summary="Evaluate workspace read without a loaded lease.",
    )

    denied = authority.evaluate_authority_scope(request)
    allowed_default = authority.evaluate_authority_scope(
        request,
        include_default_read_only=True,
    )

    assert denied.outcome == AuthorityDecisionOutcome.deny.value
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        denied.reason_refs
    )
    assert allowed_default.outcome == AuthorityDecisionOutcome.allow.value
    assert allowed_default.lease_ref == "authority-lease-ref:default-read-only-session"


def test_local_approval_authority_enforces_mission_scoped_lease() -> None:
    authority = LocalApprovalAuthority()
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:approval-authority-mission-workspace",
        mode=TrustMode.approved_safe_local_work_session,
        scope="mission",
        mission_ref="mission-ref:approval-authority-workspace",
        domains={AuthorityDomain.workspace: [AuthorityCapability.execute]},
        safe_summary="Approval authority test mission lease grants workspace execute.",
    )
    authority.issue_authority_lease(lease)

    missing_mission = authority.evaluate_authority_scope(
        AuthorityActionRequest(
            action_ref="authority-action-ref:approval-authority-missing-mission",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            requested_mode=TrustMode.approved_safe_local_work_session,
            draft_fallback_available=True,
            safe_summary="Evaluate workspace execute without the mission ref.",
        )
    )
    matching_mission = authority.evaluate_authority_scope(
        AuthorityActionRequest(
            action_ref="authority-action-ref:approval-authority-matching-mission",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            resource_refs=["mission-ref:approval-authority-workspace"],
            requested_mode=TrustMode.approved_safe_local_work_session,
            safe_summary="Evaluate workspace execute inside the mission ref.",
        )
    )

    assert missing_mission.outcome == AuthorityDecisionOutcome.degrade_to_draft.value
    assert "reason-ref:authority:mission-scope-mismatch" in (
        missing_mission.reason_refs
    )
    assert matching_mission.outcome == AuthorityDecisionOutcome.allow.value
    assert matching_mission.lease_ref == lease.lease_ref
