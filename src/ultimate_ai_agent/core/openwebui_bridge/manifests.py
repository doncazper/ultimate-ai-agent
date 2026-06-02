from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUIBridgeManifest,
    OpenWebUIBridgePlan,
)
from ultimate_ai_agent.core.openwebui_bridge.enums import (
    OpenWebUIAuthorityBoundary,
    OpenWebUIBridgeStatus,
    OpenWebUIContentMode,
    OpenWebUISurfaceRole,
)
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_bridge_manifest,
    validate_openwebui_bridge_plan,
)


M21_OPENWEBUI_DOCS = [
    "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
    "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
    "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
    "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_NON_GOALS.md",
    "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
    "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
]


def build_default_openwebui_bridge_manifest(
    baseline_version: str = "0.25.1",
) -> OpenWebUIBridgeManifest:
    manifest = OpenWebUIBridgeManifest(
        baseline_version=baseline_version,
        supported_surfaces=[
            OpenWebUISurfaceRole.conversational_shell,
            OpenWebUISurfaceRole.chat_session_host,
            OpenWebUISurfaceRole.transcript_view,
            OpenWebUISurfaceRole.context_link_source,
        ],
        blocked_surfaces=[OpenWebUISurfaceRole.not_authority],
        allowed_content_modes=[
            OpenWebUIContentMode.summary_only,
            OpenWebUIContentMode.ref_only,
            OpenWebUIContentMode.redacted_preview,
        ],
        blocked_content_modes=[
            OpenWebUIContentMode.raw_content_blocked,
            OpenWebUIContentMode.future_requires_contract,
        ],
        authority_boundaries=[
            OpenWebUIAuthorityBoundary.agent_core_authority,
            OpenWebUIAuthorityBoundary.approval_authority_required,
            OpenWebUIAuthorityBoundary.no_direct_tool_execution,
            OpenWebUIAuthorityBoundary.no_direct_memory_write,
            OpenWebUIAuthorityBoundary.no_direct_runtime_execution,
            OpenWebUIAuthorityBoundary.no_direct_provider_call,
        ],
        docs_refs=M21_OPENWEBUI_DOCS,
        warnings=[
            "M21 is contract-only.",
            "OpenWebUI is the preferred conversational web shell, not the agent brain.",
            "Python Agent Core remains authority.",
            "No OpenWebUI integration, deployment config, plugin, runtime call, memory write, or tool execution is added.",
        ],
        safe_summary=(
            "M21 OpenWebUI bridge contract-only manifest; future chat shell "
            "integration remains planned and disabled."
        ),
    )
    validate_openwebui_bridge_manifest(manifest)
    return manifest


def build_default_openwebui_bridge_plan() -> OpenWebUIBridgePlan:
    plan = OpenWebUIBridgePlan(
        status=OpenWebUIBridgeStatus.planned_disabled,
        stage="m21_contract_only",
        purpose=(
            "Define future OpenWebUI chat shell bridge contracts while keeping "
            "Python Agent Core as authority."
        ),
        allowed_scope=[
            "contract-only Python models",
            "chat ingress and egress envelope validation",
            "session, transcript, and message refs",
            "redacted safe summaries",
            "documentation and Foundation Gate coverage",
        ],
        blocked_scope=[
            "OpenWebUI integration",
            "OpenWebUI deployment config",
            "OpenWebUI plugin function pipeline or tool enablement",
            "direct tool execution",
            "direct memory write",
            "direct runtime execution",
            "direct provider call",
            "direct model runtime calls",
            "approval grants",
            "credential access",
            "raw transcript storage",
        ],
        required_future_milestones=["M22", "M23"],
        docs_refs=M21_OPENWEBUI_DOCS,
        warnings=[
            "M22 remains Local Model Runtime Activation Contract.",
            "M23 remains First Real Local LLM Call, Non-Tool, Non-Authoritative.",
        ],
    )
    validate_openwebui_bridge_plan(plan)
    return plan
