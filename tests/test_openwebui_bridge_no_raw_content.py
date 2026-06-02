import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIContentMode,
    OpenWebUIMessageDirection,
    OpenWebUIMessageRef,
    OpenWebUITranscriptRef,
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
