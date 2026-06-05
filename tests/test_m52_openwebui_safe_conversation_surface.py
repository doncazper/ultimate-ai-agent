import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIContentMode,
    OpenWebUIMessageDirection,
    OpenWebUISafeConversationSurfacePolicy,
    OpenWebUISafeConversationSurfaceStatus,
    OpenWebUISafeConversationTurn,
    build_openwebui_safe_conversation_surface,
    validate_openwebui_safe_conversation_surface_policy,
    validate_openwebui_safe_conversation_turn,
)


def _turn(**overrides):
    data = {
        "turn_ref": "openwebui-conversation-turn:m52-safe",
        "session_ref": "openwebui-session:m52-safe",
        "message_ref": "openwebui-message:m52-safe",
        "direction": OpenWebUIMessageDirection.user_to_agent_core_planned,
        "content_mode": OpenWebUIContentMode.summary_only,
        "safe_summary": "User asked for a safe, redacted conversation summary.",
        "approval_ref": None,
    }
    data.update(overrides)
    return OpenWebUISafeConversationTurn(**data)


def test_safe_conversation_surface_returns_summary_only_non_authoritative_turns() -> None:
    surface = build_openwebui_safe_conversation_surface(
        conversation_ref="openwebui-safe-conversation:m52",
        session_ref="openwebui-session:m52-safe",
        safe_title="Governed OpenWebUI conversation preview",
        turns=[_turn()],
    )

    assert surface.status == OpenWebUISafeConversationSurfaceStatus.safe_review_ready
    assert surface.content_mode == OpenWebUIContentMode.summary_only
    assert surface.safe_title == "Governed OpenWebUI conversation preview"
    assert len(surface.turns) == 1
    assert surface.turns[0].raw_prompt_present is False
    assert surface.turns[0].raw_provider_payload_present is False
    assert surface.turns[0].model_output_authoritative is False
    assert surface.openwebui_called is False
    assert surface.provider_called is False
    assert surface.tool_executed is False
    assert surface.memory_written is False
    assert surface.context_injected is False
    assert surface.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("raw_prompt_present", "RAW_PROMPT_DENIED"),
        ("raw_provider_payload_present", "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_content_present", "RAW_CONTENT_DENIED"),
        ("secret_like_content_present", "SECRET_LIKE_CONTENT_DENIED"),
        ("provider_call_requested", "PROVIDER_CALL_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("model_authority_requested", "MODEL_AUTHORITY_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("openwebui_runtime_call_requested", "OPENWEBUI_RUNTIME_CALL_DENIED"),
    ],
)
def test_safe_conversation_turn_rejects_raw_or_authority_requests(field: str, reason: str) -> None:
    turn = _turn(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_openwebui_safe_conversation_turn(turn)


def test_safe_conversation_surface_revalidates_model_copy_mutated_turns() -> None:
    unsafe_turn = _turn().model_copy(
        update={
            "raw_prompt_present": True,
            "raw_provider_payload_present": True,
            "model_authority_requested": True,
        }
    )

    with pytest.raises(ValueError, match="RAW_PROMPT_DENIED"):
        build_openwebui_safe_conversation_surface(
            conversation_ref="openwebui-safe-conversation:m52-mutated",
            session_ref="openwebui-session:m52-safe",
            safe_title="Mutated unsafe turn",
            turns=[unsafe_turn],
        )


def test_safe_conversation_surface_does_not_treat_approval_ref_as_authority() -> None:
    turn = _turn(
        approval_ref="approval:m52-shell-preview",
        tool_execution_requested=True,
    )

    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        build_openwebui_safe_conversation_surface(
            conversation_ref="openwebui-safe-conversation:m52-approval",
            session_ref="openwebui-session:m52-safe",
            safe_title="Approval refs are not authority",
            turns=[turn],
        )


def test_safe_conversation_policy_rejects_runtime_and_authority_flags() -> None:
    policy = OpenWebUISafeConversationSurfacePolicy(
        live_openwebui_connection_enabled=True,
        model_call_enabled=True,
        model_authority_enabled=True,
        tool_execution_enabled=True,
        memory_write_enabled=True,
        context_injection_enabled=True,
        raw_prompt_exposure_enabled=True,
        raw_provider_payload_exposure_enabled=True,
    )

    with pytest.raises(ValueError, match="LIVE_OPENWEBUI_CONNECTION_DENIED"):
        validate_openwebui_safe_conversation_surface_policy(policy)
