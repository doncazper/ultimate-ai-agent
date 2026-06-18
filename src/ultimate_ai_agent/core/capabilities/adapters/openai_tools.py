from __future__ import annotations

from copy import deepcopy

from ultimate_ai_agent.core.capabilities.models import CapabilitySpec


def capability_to_openai_tool(spec: CapabilitySpec, *, strict: bool = True) -> dict:
    description = spec.description
    if spec.instructions:
        description = f"{description}\n\n{spec.instructions}"
    function = {
        "name": spec.name,
        "description": description,
        "parameters": deepcopy(spec.input_schema),
    }
    if strict:
        function["strict"] = True
    return {"type": "function", "function": function}


def capabilities_to_openai_tools(specs: list[CapabilitySpec], *, strict: bool = True) -> list[dict]:
    return [capability_to_openai_tool(spec, strict=strict) for spec in specs]
