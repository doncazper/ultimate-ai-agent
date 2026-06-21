"""Regression test for tool->capability risk-level mapping.

capability_from_tool_manifest maps a ToolManifest's risk level onto the
capability layer's RiskLevel. ToolRiskLevel.forbidden was mapped down to
RiskLevel.DESTRUCTIVE, which ranks below forbidden in the approval risk
ordering, so a forbidden tool was silently under-classified once it crossed
into the capability layer. This pins the correct, non-downgrading mapping.
"""

from ultimate_ai_agent.core.capabilities.adapters.tool_manifest import (
    capability_from_tool_manifest,
)
from ultimate_ai_agent.core.capabilities.models import RiskLevel
from ultimate_ai_agent.core.tools import (
    ToolCategory,
    ToolExecutionMode,
    ToolManifest,
    ToolPermissionKind,
    ToolPermissionManifest,
    ToolRiskLevel,
)


def _manifest(risk_level: ToolRiskLevel) -> ToolManifest:
    return ToolManifest(
        tool_id="example_tool",
        display_name="Example Tool",
        category=ToolCategory.file,
        description="Example tool used for risk-mapping coverage.",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=risk_level,
        permissions_required=[ToolPermissionKind.filesystem_read],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.filesystem_read],
            filesystem_roots=["/workspace"],
        ),
        capability_flag="filesystem_read_active",
        owner="orchestrator",
        source="system",
        version="1.0.0",
    )


def test_forbidden_tool_maps_to_forbidden_capability_risk() -> None:
    spec = capability_from_tool_manifest(_manifest(ToolRiskLevel.forbidden))
    assert spec.policy.risk == RiskLevel.forbidden


def test_critical_tool_still_maps_to_secret_access() -> None:
    spec = capability_from_tool_manifest(_manifest(ToolRiskLevel.critical))
    assert spec.policy.risk == RiskLevel.SECRET_ACCESS
