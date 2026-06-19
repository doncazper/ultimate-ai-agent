from __future__ import annotations

from copy import deepcopy

from ultimate_ai_agent.core.capabilities.models import CapabilitySpec


def capability_to_mcp_tool(spec: CapabilitySpec) -> dict:
    tool = {
        "name": spec.name,
        "title": spec.title,
        "description": spec.description,
        "inputSchema": deepcopy(spec.input_schema),
    }
    if spec.output_schema is not None:
        tool["outputSchema"] = deepcopy(spec.output_schema)
    if spec.instructions:
        tool["annotations"] = {"instructions": spec.instructions}
    return tool


def capabilities_to_mcp_tools(specs: list[CapabilitySpec]) -> list[dict]:
    return [capability_to_mcp_tool(spec) for spec in specs]
