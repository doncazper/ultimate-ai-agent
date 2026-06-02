import re
from collections.abc import Mapping
from typing import Any

from ultimate_ai_agent.core.openwebui_bridge.contracts import (
    OpenWebUIBridgeManifest,
    OpenWebUIBridgePlan,
    OpenWebUIBridgeReceiptPlan,
    OpenWebUIBridgeValidationDecision,
    OpenWebUIChatEgressEnvelope,
    OpenWebUIChatIngressEnvelope,
    OpenWebUIChatSessionRef,
    OpenWebUIMessageRef,
    OpenWebUITranscriptRef,
)
from ultimate_ai_agent.core.openwebui_bridge.enums import (
    OpenWebUIAuthorityBoundary,
    OpenWebUIBridgeDecisionStatus,
    OpenWebUIBridgeStatus,
    OpenWebUIContentMode,
)


SECRET_KEY = re.compile(
    r"(?i)(api[_-]?key|admin[_-]?token|auth[_-]?token|authorization|browser[_-]?profile|cookie|credential|password|secret|session[_-]?token|token)"
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|admin[_-]?token|auth[_-]?token|authorization|cookie|credential|password|secret|session[_-]?token|token)\s*[:=]"
)
NEGATED_OPENWEBUI_AUTHORITY_TEXT = re.compile(
    r"(?i)\bopenwebui\b.{0,80}\b(?:is\s+not|isn't|must\s+not|cannot|can't|does\s+not|doesn't|never)\b.{0,80}\b(?:agent\s+brain|authority|approve|approves|execute|executes|bypass|bypasses|call|calls|write|writes)\b"
)
POSITIVE_OPENWEBUI_AUTHORITY_CLAIMS = (
    re.compile(
        r"(?i)\bopenwebui\b.{0,80}\b(?:is|remains|becomes)\b.{0,30}\b(?:the\s+)?(?:agent\s+brain|authority)\b"
    ),
    re.compile(
        r"(?i)\bopenwebui\b.{0,20}\bas\b.{0,20}\b(?:the\s+)?(?:agent\s+brain|authority)\b"
    ),
    re.compile(
        r"(?i)\b(?:agent\s+brain|authority)\b.{0,80}\bopenwebui\b"
    ),
    re.compile(
        r"(?i)\bopenwebui\b.{0,80}\b(?:can|may|will|does|is\s+allowed\s+to|is\s+authorized\s+to)\b.{0,40}\b(?:approve|execute|bypass|call|write)\b"
    ),
    re.compile(
        r"(?i)\bopenwebui\b.{0,80}\b(?:approves|executes|bypasses|calls|writes)\b"
    ),
)
ALLOWED_OPENWEBUI_CONTENT_MODES = {
    OpenWebUIContentMode.summary_only,
    OpenWebUIContentMode.ref_only,
    OpenWebUIContentMode.redacted_preview,
}


def validate_openwebui_bridge_manifest(
    manifest: OpenWebUIBridgeManifest,
) -> OpenWebUIBridgeManifest:
    assert_openwebui_contract_only(manifest)
    assert_agent_core_authority_boundary(manifest)
    assert_no_raw_content(manifest)
    assert_no_secret_metadata(manifest)
    assert_no_tool_execution(manifest)
    assert_no_memory_write(manifest)
    assert_no_runtime_execution(manifest)
    assert_no_provider_call(manifest)
    assert_no_approval_grant(manifest)
    return manifest


def validate_openwebui_bridge_plan(plan: OpenWebUIBridgePlan) -> OpenWebUIBridgePlan:
    _assert_safe_text(plan.purpose)
    _assert_policy_text(plan.allowed_scope)
    _assert_policy_text(plan.blocked_scope)
    _assert_metadata_refs_only(plan.required_future_milestones)
    _assert_metadata_refs_only(plan.docs_refs)
    _assert_policy_text(plan.warnings)
    _assert_metadata_refs_only(plan.metadata_refs)
    _assert_safe_metadata(plan.metadata)
    if plan.status not in {
        OpenWebUIBridgeStatus.contract_only,
        OpenWebUIBridgeStatus.planned_disabled,
    }:
        raise ValueError("OpenWebUI bridge plan must remain contract-only/planned-disabled")
    return plan


def validate_openwebui_chat_session_ref(
    session: OpenWebUIChatSessionRef,
) -> OpenWebUIChatSessionRef:
    _assert_safe_text(session.session_ref)
    _assert_safe_text(session.shell_ref)
    _assert_safe_text(session.user_ref)
    _assert_safe_text(session.safe_label)
    _assert_metadata_refs_only(session.metadata_refs)
    _assert_safe_metadata(session.metadata)
    if session.authority_granted:
        raise ValueError("OpenWebUI session refs are not authority")
    return session


def validate_openwebui_transcript_ref(
    transcript: OpenWebUITranscriptRef,
) -> OpenWebUITranscriptRef:
    _assert_safe_text(transcript.transcript_ref)
    _assert_safe_text(transcript.session_ref)
    _assert_safe_text(transcript.redaction_status)
    _assert_safe_text(transcript.safe_summary)
    _assert_metadata_refs_only(transcript.event_refs)
    _assert_metadata_refs_only(transcript.receipt_refs)
    _assert_metadata_refs_only(transcript.metadata_refs)
    _assert_safe_metadata(transcript.metadata)
    _assert_allowed_content_mode(transcript.content_mode)
    if transcript.raw_content_stored:
        raise ValueError("raw content is not stored by M21 OpenWebUI transcript refs")
    return transcript


def validate_openwebui_message_ref(message: OpenWebUIMessageRef) -> OpenWebUIMessageRef:
    _assert_safe_text(message.message_ref)
    _assert_safe_text(message.session_ref)
    _assert_safe_text(message.safe_summary)
    _assert_metadata_refs_only(message.event_refs)
    _assert_metadata_refs_only(message.receipt_refs)
    _assert_metadata_refs_only(message.metadata_refs)
    _assert_safe_metadata(message.metadata)
    _assert_allowed_content_mode(message.content_mode)
    return message


def validate_openwebui_chat_ingress_envelope(
    envelope: OpenWebUIChatIngressEnvelope,
) -> OpenWebUIChatIngressEnvelope:
    _assert_safe_text(envelope.envelope_id)
    _assert_safe_text(envelope.session_ref)
    _assert_safe_text(envelope.message_ref)
    _assert_safe_text(envelope.user_visible_summary)
    _assert_metadata_refs_only(envelope.event_refs)
    _assert_metadata_refs_only(envelope.metadata_refs)
    _assert_safe_metadata(envelope.metadata)
    _assert_allowed_content_mode(envelope.content_mode)
    if envelope.raw_content_allowed or envelope.raw_content_present:
        raise ValueError("raw content is not allowed in M21 OpenWebUI ingress")
    if envelope.contains_secret_like_content:
        raise ValueError("secret-like OpenWebUI content is denied in M21")
    if envelope.tool_execution_requested:
        if envelope.approval_ref:
            raise ValueError("approval_ref is not authority for OpenWebUI tool execution")
        raise ValueError("direct tool execution is denied in M21")
    if envelope.memory_write_requested:
        if envelope.approval_ref:
            raise ValueError("approval_ref is not authority for OpenWebUI memory write")
        raise ValueError("direct memory write is denied in M21")
    if envelope.runtime_execution_requested:
        raise ValueError("runtime execution is denied in M21")
    if envelope.provider_call_requested:
        raise ValueError("provider call is denied in M21")
    return envelope


def validate_openwebui_chat_egress_envelope(
    envelope: OpenWebUIChatEgressEnvelope,
) -> OpenWebUIChatEgressEnvelope:
    _assert_safe_text(envelope.envelope_id)
    _assert_safe_text(envelope.session_ref)
    _assert_safe_text(envelope.message_ref)
    _assert_safe_text(envelope.safe_response_summary)
    _assert_metadata_refs_only(envelope.event_refs)
    _assert_metadata_refs_only(envelope.receipt_refs)
    _assert_metadata_refs_only(envelope.metadata_refs)
    _assert_safe_metadata(envelope.metadata)
    _assert_allowed_content_mode(envelope.content_mode)
    if not envelope.model_output_non_authoritative:
        raise ValueError("OpenWebUI bridge output must remain non-authoritative")
    if envelope.action_executed:
        raise ValueError("action execution is denied in M21")
    if envelope.tool_executed:
        raise ValueError("tool execution is denied in M21")
    if envelope.memory_written:
        raise ValueError("memory write is denied in M21")
    if envelope.provider_called:
        raise ValueError("provider call is denied in M21")
    if envelope.runtime_called:
        raise ValueError("runtime execution is denied in M21")
    if envelope.approval_granted:
        raise ValueError("approval grant is denied in M21")
    return envelope


def validate_openwebui_bridge_decision(
    decision: OpenWebUIBridgeValidationDecision,
) -> OpenWebUIBridgeValidationDecision:
    _assert_safe_text(decision.subject_ref)
    _assert_safe_text(decision.safe_message)
    _assert_safe_text(decision.required_next_action)
    _assert_metadata_refs_only(decision.reason_codes)
    _assert_metadata_refs_only(decision.metadata_refs)
    _assert_safe_metadata(decision.metadata)
    if decision.allowed:
        raise ValueError("OpenWebUI bridge validation decisions cannot authorize runtime behavior in M21")
    if decision.status == OpenWebUIBridgeDecisionStatus.contract_valid:
        return decision
    return decision


def validate_openwebui_bridge_receipt_plan(
    plan: OpenWebUIBridgeReceiptPlan,
) -> OpenWebUIBridgeReceiptPlan:
    _assert_safe_text(plan.receipt_plan_id)
    _assert_safe_text(plan.session_ref)
    _assert_safe_text(plan.safe_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    _assert_safe_metadata(plan.metadata)
    if not plan.redaction_required:
        raise ValueError("OpenWebUI bridge receipts require redaction")
    if plan.raw_transcript_storage_allowed:
        raise ValueError("raw transcript storage is not allowed in M21")
    return plan


def assert_openwebui_contract_only(
    manifest: OpenWebUIBridgeManifest,
) -> OpenWebUIBridgeManifest:
    _assert_safe_text(manifest.safe_summary)
    if manifest.status not in {
        OpenWebUIBridgeStatus.contract_only,
        OpenWebUIBridgeStatus.planned_disabled,
    }:
        raise ValueError("OpenWebUI bridge manifest must remain contract-only")
    if manifest.openwebui_integration_implemented:
        raise ValueError("OpenWebUI integration is not implemented in M21")
    if manifest.deployment_config_added:
        raise ValueError("OpenWebUI deployment config is not added in M21")
    if manifest.backend_routes_added:
        raise ValueError("OpenWebUI backend routes are not added in M21")
    if manifest.openwebui_package_imported:
        raise ValueError("OpenWebUI packages are not imported in M21")
    if manifest.dependencies_added:
        raise ValueError("OpenWebUI dependencies are not added in M21")
    return manifest


def assert_agent_core_authority_boundary(
    manifest: OpenWebUIBridgeManifest,
) -> OpenWebUIBridgeManifest:
    if manifest.openwebui_is_agent_brain:
        raise ValueError("OpenWebUI is not the agent brain")
    if not manifest.agent_core_remains_authority:
        raise ValueError("Agent Core remains authority for OpenWebUI bridge contracts")
    if OpenWebUIAuthorityBoundary.agent_core_authority not in manifest.authority_boundaries:
        raise ValueError("OpenWebUI bridge manifest must include Agent Core authority boundary")
    return manifest


def assert_no_raw_content(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.raw_content_allowed:
        raise ValueError("raw content is blocked in M21")
    return manifest


def assert_no_secret_metadata(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    _assert_metadata_refs_only(manifest.metadata_refs)
    _assert_safe_metadata(manifest.metadata)
    return manifest


def assert_no_tool_execution(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.tool_execution_enabled:
        raise ValueError("direct tool execution is denied in M21")
    return manifest


def assert_no_memory_write(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.memory_write_enabled:
        raise ValueError("direct memory write is denied in M21")
    return manifest


def assert_no_runtime_execution(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.runtime_execution_enabled:
        raise ValueError("runtime execution is denied in M21")
    return manifest


def assert_no_provider_call(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.provider_call_enabled:
        raise ValueError("provider call is denied in M21")
    return manifest


def assert_no_approval_grant(manifest: OpenWebUIBridgeManifest) -> OpenWebUIBridgeManifest:
    if manifest.approval_grant_enabled:
        raise ValueError("approval grants are denied in M21")
    return manifest


def _assert_metadata_refs_only(values: list[str]) -> None:
    for value in values:
        _assert_safe_text(value)


def _assert_policy_text(values: list[str]) -> None:
    for value in values:
        if SECRET_ASSIGNMENT.search(value):
            raise ValueError("secret-like OpenWebUI bridge metadata is not allowed")
        if _contains_positive_openwebui_authority_claim(value):
            raise ValueError("OpenWebUI bridge text must not claim authority or agent-brain status")


def _assert_safe_metadata(metadata: Mapping[str, Any]) -> None:
    for key, value in metadata.items():
        _assert_safe_text(str(key))
        if isinstance(value, Mapping):
            _assert_safe_metadata(value)
        elif isinstance(value, list):
            for item in value:
                _assert_safe_text(str(item))
        else:
            _assert_safe_text(str(value))


def _assert_safe_text(value: str) -> None:
    if SECRET_KEY.search(value) or SECRET_ASSIGNMENT.search(value):
        raise ValueError("secret-like OpenWebUI bridge metadata is not allowed")
    if _contains_positive_openwebui_authority_claim(value):
        raise ValueError("OpenWebUI bridge text must not claim authority or agent-brain status")


def _assert_allowed_content_mode(content_mode: OpenWebUIContentMode) -> None:
    if content_mode not in ALLOWED_OPENWEBUI_CONTENT_MODES:
        raise ValueError("raw content mode is not allowed for M21 OpenWebUI refs or envelopes")


def _contains_positive_openwebui_authority_claim(value: str) -> bool:
    if NEGATED_OPENWEBUI_AUTHORITY_TEXT.search(value):
        return False
    return any(pattern.search(value) for pattern in POSITIVE_OPENWEBUI_AUTHORITY_CLAIMS)
