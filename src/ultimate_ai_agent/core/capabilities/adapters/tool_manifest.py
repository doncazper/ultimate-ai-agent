from __future__ import annotations

from typing import Iterable

from ultimate_ai_agent.core.capabilities.models import CapabilityPolicy, CapabilitySpec, RiskLevel
from ultimate_ai_agent.core.tools import (
    ToolCategory,
    ToolExecutionMode,
    ToolManifest,
    ToolPermissionKind,
    ToolPermissionManifest,
    ToolRegistry,
    ToolRiskLevel,
)


def capability_to_tool_manifest(spec: CapabilitySpec) -> ToolManifest:
    permissions = _permissions_for_risk(spec.policy.risk)
    permission_manifest = ToolPermissionManifest(required_permissions=permissions) if permissions else None
    return ToolManifest(
        tool_id=spec.name,
        display_name=spec.title,
        category=_category_for_source(spec.source),
        description=spec.description,
        execution_mode=ToolExecutionMode.local_dev if spec.source in {"python", "internal"} else ToolExecutionMode.validate_only,
        risk_level=_tool_risk(spec.policy.risk),
        input_schema_ref=f"capability-schema:{spec.name}:input:{spec.version}",
        output_schema_ref=f"capability-schema:{spec.name}:output:{spec.version}" if spec.output_schema is not None else None,
        permissions_required=permissions,
        permission_manifest=permission_manifest,
        requires_consent=bool(spec.policy.required_scopes),
        requires_approval=spec.policy.requires_approval,
        supports_dry_run=False,
        supports_rollback=False,
        idempotency_required=not spec.policy.idempotent,
        foundation_gate_required=spec.source in {"mcp", "langchain", "pydantic_ai"},
        capability_flag=f"capability_registry.{spec.name}",
        owner=str(spec.metadata.get("owner", "capability_registry")),
        source=spec.source,
        version=spec.version,
        event_refs=None,
    )


def capability_from_tool_manifest(manifest: ToolManifest) -> CapabilitySpec:
    return CapabilitySpec(
        id=f"capability:{manifest.tool_id}:{manifest.version}",
        name=manifest.tool_id,
        version=manifest.version,
        title=manifest.display_name,
        description=manifest.description,
        tags={manifest.category.value},
        input_schema={"type": "object", "additionalProperties": True},
        output_schema=None,
        policy=CapabilityPolicy(
            risk=_capability_risk(manifest.risk_level),
            requires_approval=manifest.requires_approval,
            idempotent=not manifest.idempotency_required,
        ),
        source=manifest.source or "internal",
        metadata={
            "tool_category": manifest.category.value,
            "tool_execution_mode": manifest.execution_mode.value,
            "input_schema_ref": manifest.input_schema_ref,
            "output_schema_ref": manifest.output_schema_ref,
        },
    )


def register_capabilities_as_tools(tool_registry: ToolRegistry, capabilities: Iterable[CapabilitySpec]) -> None:
    for spec in capabilities:
        tool_registry.register_tool(capability_to_tool_manifest(spec))


def tool_registry_from_capabilities(capabilities: Iterable[CapabilitySpec]) -> ToolRegistry:
    registry = ToolRegistry()
    register_capabilities_as_tools(registry, capabilities)
    return registry


def _tool_risk(risk: RiskLevel) -> ToolRiskLevel:
    mapping = {
        RiskLevel.READ_ONLY: ToolRiskLevel.safe,
        RiskLevel.WRITE: ToolRiskLevel.medium,
        RiskLevel.DESTRUCTIVE: ToolRiskLevel.high,
        RiskLevel.EXTERNAL_NETWORK: ToolRiskLevel.high,
        RiskLevel.SHELL: ToolRiskLevel.critical,
        RiskLevel.SECRET_ACCESS: ToolRiskLevel.critical,
        RiskLevel.safe: ToolRiskLevel.safe,
        RiskLevel.low: ToolRiskLevel.low,
        RiskLevel.medium: ToolRiskLevel.medium,
        RiskLevel.high: ToolRiskLevel.high,
        RiskLevel.critical: ToolRiskLevel.critical,
        RiskLevel.forbidden: ToolRiskLevel.forbidden,
    }
    return mapping[risk]


def _capability_risk(risk: ToolRiskLevel) -> RiskLevel:
    mapping = {
        ToolRiskLevel.safe: RiskLevel.READ_ONLY,
        ToolRiskLevel.low: RiskLevel.READ_ONLY,
        ToolRiskLevel.medium: RiskLevel.WRITE,
        ToolRiskLevel.high: RiskLevel.DESTRUCTIVE,
        ToolRiskLevel.critical: RiskLevel.SECRET_ACCESS,
        ToolRiskLevel.forbidden: RiskLevel.forbidden,
    }
    return mapping[risk]


def _category_for_source(source: str) -> ToolCategory:
    if source == "mcp":
        return ToolCategory.mcp
    if source in {"langchain", "pydantic_ai", "openapi"}:
        return ToolCategory.sdk_adapter
    if source == "internal":
        return ToolCategory.system
    return ToolCategory.mock if source == "python" else ToolCategory.external


def _permissions_for_risk(risk: RiskLevel) -> list[ToolPermissionKind]:
    if risk == RiskLevel.WRITE:
        return [ToolPermissionKind.filesystem_write]
    if risk == RiskLevel.DESTRUCTIVE:
        return [ToolPermissionKind.filesystem_write]
    if risk == RiskLevel.EXTERNAL_NETWORK:
        return [ToolPermissionKind.network]
    if risk == RiskLevel.SHELL:
        return [ToolPermissionKind.shell, ToolPermissionKind.code_execution]
    if risk == RiskLevel.SECRET_ACCESS:
        return [ToolPermissionKind.credential]
    if risk in {RiskLevel.medium, RiskLevel.high, RiskLevel.critical, RiskLevel.forbidden}:
        return [ToolPermissionKind.filesystem_write]
    return []
