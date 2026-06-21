from __future__ import annotations

from ultimate_ai_agent.core.capabilities.models import CapabilitySpec


def capability_to_pydantic_ai_tool(spec: CapabilitySpec) -> None:
    raise RuntimeError(
        f"Executable Pydantic AI tool export is disabled for capability '{spec.name}'. "
        "Use the OpenAI, MCP, or tool-manifest schema adapters until a reviewed "
        "runtime adapter milestone grants this authority."
    )
