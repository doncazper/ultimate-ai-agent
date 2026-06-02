import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIChatEgressEnvelope,
    OpenWebUIChatIngressEnvelope,
    OpenWebUIContentMode,
    OpenWebUIMessageDirection,
    OpenWebUIMessageRef,
    OpenWebUITranscriptRef,
    validate_openwebui_chat_egress_envelope,
    validate_openwebui_chat_ingress_envelope,
    validate_openwebui_message_ref,
    validate_openwebui_transcript_ref,
)


def test_transcript_ref_rejects_raw_content_mode_and_raw_storage():
    transcript = OpenWebUITranscriptRef(
        transcript_ref="owui_transcript_demo",
        session_ref="owui_session_demo",
        redaction_status="redacted_summary_only",
        content_mode=OpenWebUIContentMode.raw_content_blocked,
        safe_summary="raw transcript content is stored",
        raw_content_stored=True,
    )

    with pytest.raises(ValueError, match="raw content"):
        validate_openwebui_transcript_ref(transcript)


@pytest.mark.parametrize(
    "content_mode",
    [
        OpenWebUIContentMode.summary_only,
        OpenWebUIContentMode.ref_only,
        OpenWebUIContentMode.redacted_preview,
    ],
)
def test_safe_content_modes_are_allowed_for_transcript_and_message_refs(content_mode):
    transcript = OpenWebUITranscriptRef(
        transcript_ref=f"owui_transcript_{content_mode.value}",
        session_ref="owui_session_demo",
        redaction_status="redacted_summary_only",
        content_mode=content_mode,
        safe_summary="redacted summary only",
    )
    message = OpenWebUIMessageRef(
        message_ref=f"owui_msg_{content_mode.value}",
        session_ref="owui_session_demo",
        direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
        content_mode=content_mode,
        safe_summary="redacted message summary only",
    )

    assert validate_openwebui_transcript_ref(transcript).content_mode == content_mode
    assert validate_openwebui_message_ref(message).content_mode == content_mode


@pytest.mark.parametrize(
    "content_mode",
    [
        OpenWebUIContentMode.raw_content_blocked,
        OpenWebUIContentMode.future_requires_contract,
    ],
)
def test_blocked_content_modes_are_not_valid_ref_or_envelope_modes(content_mode):
    transcript = OpenWebUITranscriptRef(
        transcript_ref=f"owui_transcript_blocked_{content_mode.value}",
        session_ref="owui_session_demo",
        redaction_status="redacted_summary_only",
        content_mode=content_mode,
        safe_summary="redacted summary only",
    )
    message = OpenWebUIMessageRef(
        message_ref=f"owui_msg_blocked_{content_mode.value}",
        session_ref="owui_session_demo",
        direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
        content_mode=content_mode,
        safe_summary="redacted message summary only",
    )
    ingress = OpenWebUIChatIngressEnvelope(
        envelope_id=f"owui_ingress_blocked_{content_mode.value}",
        session_ref="owui_session_demo",
        message_ref="owui_msg_ingress",
        direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
        content_mode=content_mode,
        user_visible_summary="redacted ingress summary only",
    )
    egress = OpenWebUIChatEgressEnvelope(
        envelope_id=f"owui_egress_blocked_{content_mode.value}",
        session_ref="owui_session_demo",
        message_ref="owui_msg_egress",
        content_mode=content_mode,
        safe_response_summary="redacted egress summary only",
    )

    for validator, value in [
        (validate_openwebui_transcript_ref, transcript),
        (validate_openwebui_message_ref, message),
        (validate_openwebui_chat_ingress_envelope, ingress),
        (validate_openwebui_chat_egress_envelope, egress),
    ]:
        with pytest.raises(ValueError, match="content mode is not allowed"):
            validator(value)


def test_message_ref_rejects_secret_like_safe_summary():
    message = OpenWebUIMessageRef(
        message_ref="owui_msg_secret",
        session_ref="owui_session_demo",
        direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
        content_mode=OpenWebUIContentMode.summary_only,
        safe_summary="contains password=abc123456789",
    )

    with pytest.raises(ValueError, match="secret-like"):
        validate_openwebui_message_ref(message)
