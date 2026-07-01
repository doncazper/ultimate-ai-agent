from __future__ import annotations

from copy import deepcopy

from ultimate_ai_agent.core.capabilities.models import CapabilityManifest, CapabilitySpec


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


def capability_manifest_to_openai_tool(manifest: CapabilityManifest, *, strict: bool = True) -> dict:
    function = {
        "name": _safe_openai_name(manifest.id),
        "description": manifest.description,
        "parameters": deepcopy(manifest.input_schema),
        "x-uaa-authority": _authority_metadata(manifest),
    }
    if strict:
        function["strict"] = True
    return {"type": "function", "function": function}


def capability_manifests_to_openai_tools(
    manifests: list[CapabilityManifest],
    *,
    strict: bool = True,
) -> list[dict]:
    return [capability_manifest_to_openai_tool(manifest, strict=strict) for manifest in manifests]


def _safe_openai_name(value: str) -> str:
    return value.replace(":", "_").replace("/", "_")


def _authority_metadata(manifest: CapabilityManifest) -> dict:
    return {
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
