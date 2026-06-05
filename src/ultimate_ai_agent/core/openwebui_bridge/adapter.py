from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUIBridgeAdapterPolicy,
    OpenWebUIBridgeAdapterRequest,
    OpenWebUIBridgeAdapterResult,
)
from ultimate_ai_agent.core.openwebui_bridge.manifests import M21_OPENWEBUI_DOCS
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_bridge_adapter_policy,
    validate_openwebui_bridge_adapter_request,
    validate_openwebui_bridge_adapter_result,
)


M51_OPENWEBUI_DOCS = [
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md",
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md",
    "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/M51_TO_M52_BOUNDARY.md",
    *M21_OPENWEBUI_DOCS,
]


def build_default_openwebui_bridge_adapter_policy() -> OpenWebUIBridgeAdapterPolicy:
    policy = OpenWebUIBridgeAdapterPolicy(
        docs_refs=M51_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M51", "version:v0.55.0"],
        metadata={
            "scope": "safe_summary_adapter_pilot",
            "authority": "agent_core_remains_authority",
        },
    )
    return validate_openwebui_bridge_adapter_policy(policy)


def adapt_openwebui_bridge_request(
    request: OpenWebUIBridgeAdapterRequest,
    policy: OpenWebUIBridgeAdapterPolicy | None = None,
) -> OpenWebUIBridgeAdapterResult:
    active_policy = policy or build_default_openwebui_bridge_adapter_policy()
    validate_openwebui_bridge_adapter_policy(active_policy)
    validate_openwebui_bridge_adapter_request(request)
    safe_suffix = request.adapter_request_ref.rsplit(":", 1)[-1].replace("/", "_")
    result = OpenWebUIBridgeAdapterResult(
        adapter_result_ref=f"openwebui-bridge-adapter-result:{safe_suffix}",
        adapter_request_ref=request.adapter_request_ref,
        session_ref=request.session_ref,
        message_ref=request.message_ref,
        content_mode=request.content_mode,
        safe_shell_summary=request.safe_user_summary,
        reason_codes=["M51_SAFE_SUMMARY_ADAPTER_READY"],
        metadata_refs=["milestone:M51", "version:v0.55.0"],
    )
    return validate_openwebui_bridge_adapter_result(result)
