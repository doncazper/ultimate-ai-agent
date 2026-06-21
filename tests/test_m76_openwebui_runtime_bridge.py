from typing import Any
import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIContentMode,
    OpenWebUIRuntimeBridgePolicy,
    OpenWebUIRuntimeBridgeRequest,
    OpenWebUIRuntimeBridgeStatus,
    build_openwebui_runtime_bridge_envelope,
    validate_openwebui_runtime_bridge_policy,
    validate_openwebui_runtime_bridge_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "bridge_request_ref": "openwebui-runtime-bridge-request:m76-safe",
        "session_ref": "openwebui-session:m76-safe",
        "safe_conversation_ref": "openwebui-safe-conversation:m76-safe",
        "actor_ref": "actor:m76-reviewer",
        "safe_intent_summary": "Prepare a redacted OpenWebUI bridge envelope for review.",
        "content_mode": OpenWebUIContentMode.summary_only,
        "approval_ref": None,
    }
    data.update(overrides)
    return OpenWebUIRuntimeBridgeRequest(**data)


def test_openwebui_runtime_bridge_v1_returns_review_only_envelope() -> None:
    envelope = build_openwebui_runtime_bridge_envelope(_request())

    assert envelope.status == OpenWebUIRuntimeBridgeStatus.review_envelope_ready
    assert envelope.bridge_envelope_ref.startswith("openwebui-runtime-bridge-envelope:")
    assert envelope.content_mode == OpenWebUIContentMode.summary_only
    assert envelope.safe_bridge_summary == "Prepare a redacted OpenWebUI bridge envelope for review."
    assert "M76_OPENWEBUI_RUNTIME_BRIDGE_V1" in envelope.reason_codes
    assert "M77_REMAINS_FUTURE" in envelope.reason_codes
    assert envelope.raw_prompt_returned is False
    assert envelope.raw_provider_payload_returned is False
    assert envelope.raw_content_returned is False
    assert envelope.model_output_authoritative is False
    assert envelope.openwebui_called is False
    assert envelope.provider_called is False
    assert envelope.model_called is False
    assert envelope.tool_executed is False
    assert envelope.memory_written is False
    assert envelope.context_injected is False
    assert envelope.network_called is False
    assert envelope.credential_cookie_accessed is False
    assert envelope.approval_granted is False
    assert envelope.handoff_executed is False
    assert envelope.production_authority_granted is False
    assert envelope.side_effects_performed == []
    assert envelope.receipt_plan.raw_prompt_stored is False
    assert envelope.receipt_plan.raw_provider_payload_stored is False
    assert envelope.receipt_plan.openwebui_runtime_call_performed is False


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
        ("openwebui_handoff_requested", "OPENWEBUI_HANDOFF_DENIED"),
        ("network_call_requested", "OPENWEBUI_NETWORK_CALL_DENIED"),
        ("credential_cookie_access_requested", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_openwebui_runtime_bridge_v1_rejects_raw_runtime_and_authority_requests(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_openwebui_runtime_bridge_request(_request(**{field: True}))


def test_openwebui_runtime_bridge_v1_revalidates_model_copy_mutated_requests() -> None:
    request = _request().model_copy(
        update={
            "raw_prompt_present": True,
            "openwebui_runtime_call_requested": True,
            "model_authority_requested": True,
        }
    )

    with pytest.raises(ValueError, match="RAW_PROMPT_DENIED"):
        build_openwebui_runtime_bridge_envelope(request)


def test_openwebui_runtime_bridge_v1_does_not_treat_approval_refs_as_authority() -> None:
    approval_request = _request(
        approval_ref="approval:m76-review",
        tool_execution_requested=True,
    )

    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        build_openwebui_runtime_bridge_envelope(approval_request)

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_openwebui_runtime_bridge_request(_request(approval_ref="approval_test_m76"))


def test_openwebui_runtime_bridge_policy_rejects_runtime_and_authority_flags() -> None:
    policy = OpenWebUIRuntimeBridgePolicy(
        live_openwebui_connection_enabled=True,
        openwebui_runtime_call_enabled=True,
        openwebui_network_call_enabled=True,
        provider_call_enabled=True,
        model_call_enabled=True,
        model_authority_enabled=True,
        tool_execution_enabled=True,
        memory_write_enabled=True,
        context_injection_enabled=True,
        approval_ref_authority_enabled=True,
        raw_prompt_exposure_enabled=True,
        raw_provider_payload_exposure_enabled=True,
        credential_cookie_access_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="LIVE_OPENWEBUI_CONNECTION_DENIED"):
        validate_openwebui_runtime_bridge_policy(policy)
