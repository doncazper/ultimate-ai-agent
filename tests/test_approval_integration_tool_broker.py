from typing import Any
from tests.test_stage_a_policy_hardening import make_consent_ledger, make_request, make_tool
from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
from ultimate_ai_agent.core.consent.enums import PermissionAction
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.tools import CapabilityFirewallPolicy, ToolBroker, ToolDecisionStatus, ToolRegistry
from ultimate_ai_agent.core.tools.enums import ToolRiskLevel


def actor_context() -> Any:
    return ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_actor",
        authority_source=AuthoritySource.explicit_user_request,
    )


def evaluate_with_authority(request: Any, tool: Any, authority: Any) -> Any:
    registry = ToolRegistry()
    registry.register_tool(tool)
    broker = ToolBroker(
        registry=registry,
        firewall_policy=CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high),
        approval_authority=authority,
    )
    return broker.evaluate_request(request, make_consent_ledger(PermissionAction.execute))


def test_high_risk_tool_with_arbitrary_approval_ref_stays_approval_required() -> None:
    request = make_request(actor_context(), approval_ref="human_approved_ref_123")
    decision = evaluate_with_authority(request, make_tool(risk_level=ToolRiskLevel.high), LocalApprovalAuthority())

    assert decision.status == ToolDecisionStatus.approval_required
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes


def test_high_risk_tool_with_local_authority_grant_is_policy_authorized() -> None:
    request = make_request(actor_context())
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_tool_request(
            request,
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=request.request_id,
            resource_refs=[request.tool_id],
            risk_level=ApprovalRiskLevel.high,
        )
    )
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")

    decision = evaluate_with_authority(
        request.model_copy(update={"approval_ref": grant.approval_ref}),
        make_tool(risk_level=ToolRiskLevel.high),
        authority,
    )

    assert decision.status == ToolDecisionStatus.allowed
    assert decision.reason_codes == ["AUTHORIZED"]
