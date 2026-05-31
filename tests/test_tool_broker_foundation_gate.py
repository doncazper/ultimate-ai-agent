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
from ultimate_ai_agent.core.consent import ConsentLedger
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

def test_foundation_gate_blocks_skills_and_mcp(actor_context):
    registry = ToolRegistry()
    
    # Tool in MCP category
    mcp_tool = ToolManifest(
        tool_id="mcp_tool_abc",
        display_name="MCP Tool",
        category=ToolCategory.mcp,  # Blocked category
        description="MCP server tool integration",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.safe,
        capability_flag="mcp_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )
    registry.register_tool(mcp_tool)
    
    firewall = CapabilityFirewallPolicy()
    broker = ToolBroker(registry=registry, firewall_policy=firewall)
    
    ledger = ConsentLedger()
    request = ToolRequest(
        request_id="req_mcp",
        run_id="run_1",
        tool_id="mcp_tool_abc",
        actor_context=actor_context,
        requested_action="execute",
        purpose="execution integration",
        data_classification=DataBoundary.public
    )
    
    decision = broker.evaluate_request(request, consent_ledger=ledger)
    assert decision.status == ToolDecisionStatus.blocked_by_foundation_gate
    assert "FOUNDATION_GATE_BLOCKED" in decision.reason_codes
