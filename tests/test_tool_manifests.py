import pytest
from ultimate_ai_agent.core.tools import (
    ToolManifest,
    ToolPermissionManifest,
    ToolCategory,
    ToolExecutionMode,
    ToolRiskLevel,
    ToolPermissionKind,
    validate_tool_manifest,
)

def test_valid_tool_manifest():
    perm = ToolPermissionManifest(
        required_permissions=[ToolPermissionKind.filesystem_read],
        filesystem_roots=["/Users/sambehdjou/Documents"]
    )
    manifest = ToolManifest(
        tool_id="read_file_tool",
        display_name="Read File Tool",
        category=ToolCategory.file,
        description="Reads local files",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.safe,
        permissions_required=[ToolPermissionKind.filesystem_read],
        permission_manifest=perm,
        capability_flag="filesystem_read_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )
    assert validate_tool_manifest(manifest) is True

def test_invalid_tool_manifest_missing_perm_details():
    manifest = ToolManifest(
        tool_id="read_file_tool",
        display_name="Read File Tool",
        category=ToolCategory.file,
        description="Reads local files",
        execution_mode=ToolExecutionMode.dry_run,
        risk_level=ToolRiskLevel.safe,
        permissions_required=[ToolPermissionKind.filesystem_read],
        permission_manifest=None,  # Missing detail manifest
        capability_flag="filesystem_read_active",
        owner="orchestrator",
        source="system",
        version="1.0.0"
    )
    with pytest.raises(ValueError, match="must include permission_manifest details"):
        validate_tool_manifest(manifest)
