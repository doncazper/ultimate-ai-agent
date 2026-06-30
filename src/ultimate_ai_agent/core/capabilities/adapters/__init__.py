from ultimate_ai_agent.core.capabilities.adapters.base import (
    AgentAdapter,
    CallableCapabilityAdapter,
    CapabilityAdapter,
    HandoffAdapter,
    HumanGateAdapter,
    ReviewerAdapter,
    ToolAdapter,
    WorkflowAdapter,
    wrap_agent,
    wrap_tool,
)
from ultimate_ai_agent.core.capabilities.adapters.mcp import (
    capabilities_to_mcp_tools,
    capability_manifest_to_mcp_tool,
    capability_manifests_to_mcp_tools,
    capability_to_mcp_tool,
)
from ultimate_ai_agent.core.capabilities.adapters.openai_tools import (
    capabilities_to_openai_tools,
    capability_manifest_to_openai_tool,
    capability_manifests_to_openai_tools,
    capability_to_openai_tool,
)
from ultimate_ai_agent.core.capabilities.adapters.openapi import capability_from_openapi_operation
from ultimate_ai_agent.core.capabilities.adapters.tool_manifest import (
    capability_from_tool_manifest,
    capability_to_tool_manifest,
    register_capabilities_as_tools,
    tool_registry_from_capabilities,
)

__all__ = [
    "AgentAdapter",
    "CallableCapabilityAdapter",
    "CapabilityAdapter",
    "HandoffAdapter",
    "HumanGateAdapter",
    "ReviewerAdapter",
    "ToolAdapter",
    "WorkflowAdapter",
    "capability_to_mcp_tool",
    "capabilities_to_mcp_tools",
    "capability_manifest_to_mcp_tool",
    "capability_manifests_to_mcp_tools",
    "capability_to_openai_tool",
    "capabilities_to_openai_tools",
    "capability_manifest_to_openai_tool",
    "capability_manifests_to_openai_tools",
    "capability_from_openapi_operation",
    "capability_from_tool_manifest",
    "capability_to_tool_manifest",
    "register_capabilities_as_tools",
    "tool_registry_from_capabilities",
    "wrap_agent",
    "wrap_tool",
]
