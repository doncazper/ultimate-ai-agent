from ultimate_ai_agent.core.openwebui_bridge.conversation import M52_OPENWEBUI_DOCS
from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUIRuntimeBridgeEnvelope,
    OpenWebUIRuntimeBridgePolicy,
    OpenWebUIRuntimeBridgeReceiptPlan,
    OpenWebUIRuntimeBridgeRequest,
)
from ultimate_ai_agent.core.openwebui_bridge.enums import OpenWebUIContentMode
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_runtime_bridge_envelope,
    validate_openwebui_runtime_bridge_policy,
    validate_openwebui_runtime_bridge_request,
)


M76_OPENWEBUI_DOCS = [
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_V1.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_POLICY.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RESULT_CONTRACT.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RECEIPT_PLAN.md",
    "docs/openwebui/M76_TO_M77_BOUNDARY.md",
    *M52_OPENWEBUI_DOCS,
]


def build_default_openwebui_runtime_bridge_policy() -> OpenWebUIRuntimeBridgePolicy:
    policy = OpenWebUIRuntimeBridgePolicy(
        docs_refs=M76_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M76", "version:v0.80.0"],
        metadata={
            "scope": "review_only_runtime_bridge_v1",
            "authority": "agent_core_remains_authority",
        },
    )
    return validate_openwebui_runtime_bridge_policy(policy)


def build_openwebui_runtime_bridge_envelope(
    request: OpenWebUIRuntimeBridgeRequest,
    policy: OpenWebUIRuntimeBridgePolicy | None = None,
) -> OpenWebUIRuntimeBridgeEnvelope:
    active_policy = policy or build_default_openwebui_runtime_bridge_policy()
    validate_openwebui_runtime_bridge_policy(active_policy)
    validate_openwebui_runtime_bridge_request(request)
    safe_suffix = request.bridge_request_ref.rsplit(":", 1)[-1].replace("/", "_")
    envelope_ref = f"openwebui-runtime-bridge-envelope:{safe_suffix}"
    receipt_plan = OpenWebUIRuntimeBridgeReceiptPlan(
        receipt_plan_ref=f"openwebui-runtime-bridge-receipt-plan:{safe_suffix}",
        bridge_request_ref=request.bridge_request_ref,
        bridge_envelope_ref=envelope_ref,
        session_ref=request.session_ref,
        safe_conversation_ref=request.safe_conversation_ref,
        safe_summary="M76 OpenWebUI runtime bridge receipt plan stores only redacted refs.",
        metadata_refs=["milestone:M76", "version:v0.80.0"],
    )
    envelope = OpenWebUIRuntimeBridgeEnvelope(
        bridge_envelope_ref=envelope_ref,
        bridge_request_ref=request.bridge_request_ref,
        session_ref=request.session_ref,
        safe_conversation_ref=request.safe_conversation_ref,
        actor_ref=request.actor_ref,
        content_mode=OpenWebUIContentMode.summary_only,
        safe_bridge_summary=request.safe_intent_summary,
        reason_codes=["M76_OPENWEBUI_RUNTIME_BRIDGE_V1", "M77_REMAINS_FUTURE"],
        receipt_plan=receipt_plan,
        docs_refs=M76_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M76", "version:v0.80.0"],
    )
    return validate_openwebui_runtime_bridge_envelope(envelope)
