from ultimate_ai_agent.core.tools.v2.contracts import ToolCatalogEntry
from ultimate_ai_agent.core.tools.v2.enums import (
    ToolApprovalRequirement,
    ToolExecutionMode,
    ToolRiskClass,
    ToolSideEffectKind,
    ToolTargetKind,
)


def build_default_tool_catalog() -> dict[str, ToolCatalogEntry]:
    return {
        "file.metadata_preview": ToolCatalogEntry(
            tool_id="file.metadata_preview",
            display_name="File Metadata Preview",
            target_kind=ToolTargetKind.file_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.low,
            side_effects=[ToolSideEffectKind.none],
            approval_requirement=ToolApprovalRequirement.not_required,
            safe_description="Validation-only preview of safe file metadata refs.",
        ),
        "memory.metadata_preview": ToolCatalogEntry(
            tool_id="memory.metadata_preview",
            display_name="Memory Metadata Preview",
            target_kind=ToolTargetKind.memory_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.low,
            side_effects=[ToolSideEffectKind.none],
            approval_requirement=ToolApprovalRequirement.not_required,
            safe_description="Validation-only preview of recall memory refs.",
        ),
        "message.draft_preview": ToolCatalogEntry(
            tool_id="message.draft_preview",
            display_name="Message Draft Preview",
            target_kind=ToolTargetKind.message_draft_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.low,
            side_effects=[ToolSideEffectKind.none],
            approval_requirement=ToolApprovalRequirement.not_required,
            safe_description="Validation-only preview of a message draft ref.",
        ),
        "api.route_preview": ToolCatalogEntry(
            tool_id="api.route_preview",
            display_name="API Route Preview",
            target_kind=ToolTargetKind.api_route_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.low,
            side_effects=[ToolSideEffectKind.none],
            approval_requirement=ToolApprovalRequirement.not_required,
            safe_description="Validation-only preview of API route metadata.",
        ),
    }
