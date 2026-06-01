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

@pytest.fixture
def mock_tool_manifest():
    return ToolManifest(
        tool_id="mock_validator",
        display_name="Mock Validator",
        category=ToolCategory.mock,
        description="Dry-run validator tool",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.safe,
        capability_flag="mock_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )

def test_tool_broker_authorized_request(actor_context, mock_tool_manifest):
    registry = ToolRegistry()
    registry.register_tool(mock_tool_manifest)
    
    firewall = CapabilityFirewallPolicy()
    broker = ToolBroker(registry=registry, firewall_policy=firewall)
    
    # Add matching consent grant
    ledger = ConsentLedger()
    grant = ConsentGrant(
        consent_id="grant_mock",
        subject_type=ConsentSubjectType.tool,
        subject_id="mock_validator",
        granted_to_actor="test_actor",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.execute],
        source="test"
    )
    ledger.add_grant(grant)
    
    request = ToolRequest(
        request_id="req_1",
        run_id="run_1",
        tool_id="mock_validator",
        actor_context=actor_context,
        requested_action="execute",
        purpose="testing",
        data_classification=DataBoundary.public
    )
    
    decision = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision.status == ToolDecisionStatus.allowed
    assert "grant_mock" in decision.matched_consent_refs

def test_tool_broker_missing_consent(actor_context, mock_tool_manifest):
    registry = ToolRegistry()
    registry.register_tool(mock_tool_manifest)
    
    firewall = CapabilityFirewallPolicy()
    broker = ToolBroker(registry=registry, firewall_policy=firewall)
    
    ledger = ConsentLedger()  # Empty ledger (no consent)
    
    request = ToolRequest(
        request_id="req_2",
        run_id="run_1",
        tool_id="mock_validator",
        actor_context=actor_context,
        requested_action="execute",
        purpose="testing",
        data_classification=DataBoundary.public
    )
    
    decision = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision.status == ToolDecisionStatus.denied
    assert decision.consent_required is True
