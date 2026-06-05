from ultimate_ai_agent.core.openwebui_bridge.adapter import M51_OPENWEBUI_DOCS
from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUISafeConversationSurface,
    OpenWebUISafeConversationSurfacePolicy,
    OpenWebUISafeConversationTurn,
)
from ultimate_ai_agent.core.openwebui_bridge.enums import OpenWebUIContentMode
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_safe_conversation_surface,
    validate_openwebui_safe_conversation_surface_policy,
)


M52_OPENWEBUI_DOCS = [
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md",
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md",
    "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/M52_TO_M53_BOUNDARY.md",
    *M51_OPENWEBUI_DOCS,
]


def build_default_openwebui_safe_conversation_policy() -> OpenWebUISafeConversationSurfacePolicy:
    policy = OpenWebUISafeConversationSurfacePolicy(
        docs_refs=M52_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M52", "version:v0.56.0"],
        metadata={
            "scope": "safe_conversation_surface",
            "authority": "agent_core_remains_authority",
        },
    )
    return validate_openwebui_safe_conversation_surface_policy(policy)


def build_openwebui_safe_conversation_surface(
    *,
    conversation_ref: str,
    session_ref: str,
    safe_title: str,
    turns: list[OpenWebUISafeConversationTurn],
    policy: OpenWebUISafeConversationSurfacePolicy | None = None,
) -> OpenWebUISafeConversationSurface:
    active_policy = policy or build_default_openwebui_safe_conversation_policy()
    validate_openwebui_safe_conversation_surface_policy(active_policy)
    surface = OpenWebUISafeConversationSurface(
        conversation_ref=conversation_ref,
        session_ref=session_ref,
        safe_title=safe_title,
        content_mode=OpenWebUIContentMode.summary_only,
        turns=list(turns),
        reason_codes=["M52_SAFE_CONVERSATION_SURFACE_READY"],
        docs_refs=M52_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M52", "version:v0.56.0"],
    )
    return validate_openwebui_safe_conversation_surface(surface)
