from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIAuthorityBoundary,
    OpenWebUIBridgeStatus,
    OpenWebUIContentMode,
    OpenWebUISurfaceRole,
    build_default_openwebui_bridge_manifest,
    build_default_openwebui_bridge_plan,
)
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    assert_agent_core_authority_boundary,
    assert_openwebui_contract_only,
)


def test_default_openwebui_bridge_manifest_is_contract_only():
    manifest = build_default_openwebui_bridge_manifest()

    assert manifest.baseline_version == "0.25.1"
    assert manifest.status == OpenWebUIBridgeStatus.contract_only
    assert manifest.openwebui_integration_implemented is False
    assert manifest.deployment_config_added is False
    assert manifest.backend_routes_added is False
    assert OpenWebUISurfaceRole.conversational_shell in manifest.supported_surfaces
    assert OpenWebUIAuthorityBoundary.agent_core_authority in manifest.authority_boundaries
    assert OpenWebUIAuthorityBoundary.no_direct_tool_execution in manifest.authority_boundaries
    assert OpenWebUIAuthorityBoundary.no_direct_memory_write in manifest.authority_boundaries

    assert_openwebui_contract_only(manifest)
    assert_agent_core_authority_boundary(manifest)


def test_default_openwebui_bridge_plan_preserves_future_stage_boundary():
    plan = build_default_openwebui_bridge_plan()

    assert plan.status == OpenWebUIBridgeStatus.planned_disabled
    assert plan.stage == "m21_contract_only"
    assert "M22" in plan.required_future_milestones
    assert "M23" in plan.required_future_milestones
    assert "direct tool execution" in plan.blocked_scope
    assert "direct model runtime calls" in plan.blocked_scope


def test_transcript_and_message_refs_are_summary_only_and_not_authority():
    manifest = build_default_openwebui_bridge_manifest()

    assert OpenWebUIContentMode.summary_only in manifest.allowed_content_modes
    assert OpenWebUIContentMode.ref_only in manifest.allowed_content_modes
    assert OpenWebUIContentMode.raw_content_blocked in manifest.blocked_content_modes
    assert OpenWebUISurfaceRole.not_authority in manifest.blocked_surfaces
