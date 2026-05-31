import pytest
from datetime import datetime
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
        created_at=datetime.utcnow()
    )

def test_dry_run_returns_plan_with_no_side_effects(actor_context):
    registry = ToolRegistry()
    tool = ToolManifest(
        tool_id="mock_mutator",
        display_name="Mock Mutator",
        category=ToolCategory.mock,
        description="Dry-run mutator tool",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.medium,
        supports_dry_run=True,  # Supports dry run
        capability_flag="mock_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )
    registry.register_tool(tool)
    
    ledger = ConsentLedger()
    grant = ConsentGrant(
        consent_id="g_mutator",
        subject_type=ConsentSubjectType.tool,
        subject_id="mock_mutator",
        granted_to_actor="test_actor",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.execute],
        source="test"
    )
    ledger.add_grant(grant)
    
    firewall = CapabilityFirewallPolicy()
    broker = ToolBroker(registry=registry, firewall_policy=firewall)
    
    request = ToolRequest(
        request_id="req_mut",
        run_id="run_1",
        tool_id="mock_mutator",
        actor_context=actor_context,
        requested_action="execute",
        purpose="editing",
        data_classification=DataBoundary.public,
        dry_run_requested=True  # Dry run requested
    )
    
    decision = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision.status == ToolDecisionStatus.dry_run_only
    assert decision.dry_run_plan is not None
    assert "Mutable disk write" in decision.dry_run_plan.side_effects_prevented
