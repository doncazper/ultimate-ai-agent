import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIBridgeDecisionStatus,
    OpenWebUIChatEgressEnvelope,
    OpenWebUIChatIngressEnvelope,
    OpenWebUIContentMode,
    OpenWebUIMessageDirection,
    validate_openwebui_chat_egress_envelope,
    validate_openwebui_chat_ingress_envelope,
)


def _ingress(**overrides):
    values = {
        "envelope_id": "owui_ingress_001",
        "session_ref": "owui_session_demo",
        "message_ref": "owui_msg_001",
        "direction": OpenWebUIMessageDirection.user_to_agent_core_planned,
        "content_mode": OpenWebUIContentMode.summary_only,
        "user_visible_summary": "user asks for a safe planning summary",
    }
    values.update(overrides)
    return OpenWebUIChatIngressEnvelope(**values)


def _egress(**overrides):
    values = {
        "envelope_id": "owui_egress_001",
        "session_ref": "owui_session_demo",
        "message_ref": "owui_msg_002",
        "content_mode": OpenWebUIContentMode.summary_only,
        "safe_response_summary": "agent core returns a redacted planning summary",
    }
    values.update(overrides)
    return OpenWebUIChatEgressEnvelope(**values)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("raw_content_allowed", "raw content"),
        ("raw_content_present", "raw content"),
        ("contains_secret_like_content", "secret-like"),
        ("tool_execution_requested", "tool execution"),
        ("memory_write_requested", "memory write"),
        ("runtime_execution_requested", "runtime execution"),
        ("provider_call_requested", "provider call"),
    ],
)
def test_ingress_envelope_rejects_m21_forbidden_runtime_flags(field, message):
    envelope = _ingress(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_openwebui_chat_ingress_envelope(envelope)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("action_executed", "action execution"),
        ("tool_executed", "tool execution"),
        ("memory_written", "memory write"),
        ("provider_called", "provider call"),
        ("runtime_called", "runtime execution"),
        ("approval_granted", "approval grant"),
    ],
)
def test_egress_envelope_rejects_m21_authority_or_execution_claims(field, message):
    envelope = _egress(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_openwebui_chat_egress_envelope(envelope)


def test_arbitrary_approval_ref_does_not_authorize_ingress():
    envelope = _ingress(
        approval_ref="approval_made_up",
        tool_execution_requested=True,
    )

    with pytest.raises(ValueError, match="approval_ref"):
        validate_openwebui_chat_ingress_envelope(envelope)


def test_secret_like_summary_and_metadata_are_rejected():
    envelope = _ingress(
        user_visible_summary="user pasted api_key=abc123456789",
        metadata_refs=["openwebui_session_token_abc123"],
        metadata={"cookie": "session=abc123456789"},
    )

    with pytest.raises(ValueError, match="secret-like"):
        validate_openwebui_chat_ingress_envelope(envelope)


def test_raw_prompt_or_transcript_fields_are_forbidden_by_model_contract():
    with pytest.raises(ValidationError):
        OpenWebUIChatIngressEnvelope(
            envelope_id="owui_raw_001",
            session_ref="owui_session_demo",
            message_ref="owui_msg_raw",
            direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
            user_visible_summary="summary only",
            raw_prompt_body="raw prompt must not exist",
        )


def test_validation_decision_cannot_be_runtime_allow_authority():
    envelope = _ingress(validation_status=OpenWebUIBridgeDecisionStatus.contract_valid)

    assert validate_openwebui_chat_ingress_envelope(envelope).validation_status == (
        OpenWebUIBridgeDecisionStatus.contract_valid
    )
