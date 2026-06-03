import pytest
from datetime import UTC, datetime
from ultimate_ai_agent.core.tools import (
    ToolRegistry,
    ToolBroker,
    ToolManifest,
    ToolCategory,
    ToolExecutionMode,
    ToolRiskLevel,
    ToolRequest,
    ToolDecisionStatus,
    CapabilityFirewallPolicy,
)
from ultimate_ai_agent.core.consent import (
    ConsentLedger,
    ConsentGrant,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.consent.enums import DataBoundary

@pytest.fixture
def actor_context():
    return ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_actor",
        authority_source=AuthoritySource.explicit_user_request,
        created_at=datetime.now(UTC)
    )

def test_tool_broker_high_risk_requires_human_approval(actor_context):
    registry = ToolRegistry()
    high_risk_tool = ToolManifest(
        tool_id="dangerous_tool",
        display_name="Dangerous Tool",
        category=ToolCategory.system,
        description="Executes destructive tasks",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.high,  # High risk
        capability_flag="dangerous_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )
    registry.register_tool(high_risk_tool)
    
    # Configure ledger to allow it
    ledger = ConsentLedger()
    grant = ConsentGrant(
        consent_id="g_dangerous",
        subject_type=ConsentSubjectType.tool,
        subject_id="dangerous_tool",
        granted_to_actor="test_actor",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.execute],
        source="test"
    )
    ledger.add_grant(grant)
    
    firewall = CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high)
    broker = ToolBroker(registry=registry, firewall_policy=firewall)
    
    request = ToolRequest(
        request_id="req_high",
        run_id="run_1",
        tool_id="dangerous_tool",
        actor_context=actor_context,
        requested_action="execute",
        purpose="emergency restore",
        data_classification=DataBoundary.public
    )
    
    # Evaluate request without approval reference -> should return approval_required
    decision = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision.status == ToolDecisionStatus.approval_required
    assert decision.approval_required is True

    # Unvalidated approval references must not authorize high-risk tools.
    request.approval_ref = "human_approved_ref_123"
    decision2 = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision2.status == ToolDecisionStatus.approval_required
    assert "APPROVAL_REF_UNVALIDATED" in decision2.reason_codes

    # Test-only approval references are identifiers only and must not authorize
    # runtime-facing tool decisions without a LocalApprovalAuthority.
    high_risk_tool.execution_mode = ToolExecutionMode.mock
    request.approval_ref = "approval_test_123"
    decision3 = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision3.status == ToolDecisionStatus.approval_required
    assert "APPROVAL_REF_UNVALIDATED" in decision3.reason_codes
