from __future__ import annotations

from copy import deepcopy

from ultimate_ai_agent.core.capabilities.models import CapabilityManifest, CapabilitySpec


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


def capability_manifest_to_mcp_tool(manifest: CapabilityManifest) -> dict:
    return {
        "name": manifest.id,
        "title": manifest.name,
        "description": manifest.description,
        "inputSchema": deepcopy(manifest.input_schema),
        "outputSchema": deepcopy(manifest.output_schema),
        "annotations": {
            "x-uaa-authority": {
                "capability_id": manifest.id,
                "authority_level": manifest.authority_level.value,
                "side_effects": manifest.side_effects.value,
                "risk_level": manifest.risk_level.value,
                "approval_required": bool(manifest.approval_required),
                "deterministic": manifest.deterministic,
                "rollback_supported": manifest.rollback_supported,
                "receipt_required": manifest.receipt_required,
                "evidence_required": manifest.evidence_required,
                "privacy_level": manifest.privacy_level.value,
                "estimated_latency_class": manifest.estimated_latency_class.value,
                "estimated_cost_class": manifest.estimated_cost_class.value,
                "memory_write_allowed": manifest.memory_write_allowed,
                "context_injection_allowed": manifest.context_injection_allowed,
                "provider_runtime_allowed": manifest.provider_runtime_allowed,
                "browser_runtime_allowed": manifest.browser_runtime_allowed,
                "connector_write_allowed": manifest.connector_write_allowed,
                "dispatch_authorized": False,
            }
        },
    }


def capability_manifests_to_mcp_tools(manifests: list[CapabilityManifest]) -> list[dict]:
    return [capability_manifest_to_mcp_tool(manifest) for manifest in manifests]
