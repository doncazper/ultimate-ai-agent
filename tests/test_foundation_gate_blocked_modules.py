from ultimate_ai_agent.core.gate import FoundationGateStatus
from ultimate_ai_agent.core.tools import (
    CapabilityFirewallPolicy,
    ToolBroker,
    ToolCategory,
    ToolExecutionMode,
    ToolManifest,
    ToolRegistry,
    ToolRequest,
    ToolRiskLevel,
)
from ultimate_ai_agent.core.tools.enums import ToolDecisionStatus
from ultimate_ai_agent.core.consent import ConsentLedger
from tests.test_kernel_minimum_lovable_happy_path import actor
from ultimate_ai_agent.core.consent.enums import DataBoundary


def test_foundation_gate_evaluator_confirms_blocked_modules_are_absent(foundation_gate_results):
    assert foundation_gate_results["blocked_modules_absent"].status == FoundationGateStatus.passed
    assert foundation_gate_results["forbidden_runtime_integrations_absent"].status == FoundationGateStatus.passed


def test_tool_broker_blocks_advanced_adapter_categories():
    for category in (ToolCategory.mcp, ToolCategory.a2a, ToolCategory.sdk_adapter, ToolCategory.skill):
        registry = ToolRegistry()
        registry.register_tool(
            ToolManifest(
                tool_id=f"{category.value}.example",
                display_name="Blocked Adapter",
                category=category,
                description="Advanced adapter category blocked until after the Foundation Gate.",
                execution_mode=ToolExecutionMode.mock,
                risk_level=ToolRiskLevel.low,
                capability_flag=f"{category.value}_blocked",
                owner="test",
                source="test",
                version="0.0.0",
            )
        )
        decision = ToolBroker(registry, CapabilityFirewallPolicy()).evaluate_request(
            ToolRequest(
                request_id=f"req_{category.value}",
                run_id="run_gate",
                tool_id=f"{category.value}.example",
                actor_context=actor(),
                requested_action="execute",
                purpose="test_blocked_adapter",
                data_classification=DataBoundary.project_private,
            ),
            ConsentLedger(),
        )

        assert decision.status == ToolDecisionStatus.blocked_by_foundation_gate
        assert "FOUNDATION_GATE_BLOCKED" in decision.reason_codes
