from ultimate_ai_agent.core.openwebui_bridge.conversation import M52_OPENWEBUI_DOCS
from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUIRuntimeBridgeEnvelope,
    OpenWebUIRuntimeBridgePolicy,
    OpenWebUIRuntimeBridgeReceiptPlan,
    OpenWebUIRuntimeBridgeRequest,
    OpenWebUISafeHandoffPolicy,
    OpenWebUISafeHandoffReceiptPlan,
    OpenWebUISafeHandoffRequest,
    OpenWebUISafeHandoffResult,
)
from ultimate_ai_agent.core.openwebui_bridge.enums import OpenWebUIContentMode
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    validate_openwebui_runtime_bridge_envelope,
    validate_openwebui_runtime_bridge_policy,
    validate_openwebui_runtime_bridge_request,
    validate_openwebui_safe_handoff_policy,
    validate_openwebui_safe_handoff_request,
    validate_openwebui_safe_handoff_result,
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

M77_OPENWEBUI_DOCS = [
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_EXECUTION.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RESULT_CONTRACT.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RECEIPT_PLAN.md",
    "docs/openwebui/M77_TO_M78_BOUNDARY.md",
    *M76_OPENWEBUI_DOCS,
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


def build_default_openwebui_safe_handoff_policy() -> OpenWebUISafeHandoffPolicy:
    policy = OpenWebUISafeHandoffPolicy(
        docs_refs=M77_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M77", "version:v0.81.0"],
        metadata={
            "scope": "safe_handoff_execution_agent_core_only",
            "authority": "agent_core_remains_authority",
        },
    )
    return validate_openwebui_safe_handoff_policy(policy)


def build_openwebui_safe_handoff_result(
    request: OpenWebUISafeHandoffRequest,
    policy: OpenWebUISafeHandoffPolicy | None = None,
) -> OpenWebUISafeHandoffResult:
    active_policy = policy or build_default_openwebui_safe_handoff_policy()
    validate_openwebui_safe_handoff_policy(active_policy)
    validate_openwebui_safe_handoff_request(request)
    safe_suffix = request.handoff_request_ref.rsplit(":", 1)[-1].replace("/", "_")
    result_ref = f"openwebui-safe-handoff-result:{safe_suffix}"
    receipt_plan = OpenWebUISafeHandoffReceiptPlan(
        receipt_plan_ref=f"openwebui-safe-handoff-receipt-plan:{safe_suffix}",
        handoff_request_ref=request.handoff_request_ref,
        safe_handoff_result_ref=result_ref,
        bridge_envelope_ref=request.bridge_envelope_ref,
        approval_ref=request.approval_ref,
        session_ref=request.session_ref,
        safe_conversation_ref=request.safe_conversation_ref,
        actor_ref=request.actor_ref,
        safe_summary="M77 OpenWebUI safe handoff receipt stores exact-bound refs only.",
        metadata_refs=["milestone:M77", "version:v0.81.0"],
    )
    result = OpenWebUISafeHandoffResult(
        safe_handoff_result_ref=result_ref,
        handoff_request_ref=request.handoff_request_ref,
        bridge_envelope_ref=request.bridge_envelope_ref,
        approval_ref=request.approval_ref,
        session_ref=request.session_ref,
        safe_conversation_ref=request.safe_conversation_ref,
        actor_ref=request.actor_ref,
        safe_handoff_summary=request.safe_handoff_summary,
        reason_codes=[
            "M77_OPENWEBUI_SAFE_HANDOFF_EXECUTION",
            "AGENT_CORE_REMAINS_AUTHORITY",
            "M78_REMAINS_FUTURE",
        ],
        receipt_plan=receipt_plan,
        docs_refs=M77_OPENWEBUI_DOCS,
        metadata_refs=["milestone:M77", "version:v0.81.0"],
    )
    return validate_openwebui_safe_handoff_result(result)
