from typing import Any
import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIBridgeAdapterPolicy,
    OpenWebUIBridgeAdapterRequest,
    OpenWebUIBridgeAdapterStatus,
    OpenWebUIContentMode,
    adapt_openwebui_bridge_request,
    validate_openwebui_bridge_adapter_policy,
    validate_openwebui_bridge_adapter_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "adapter_request_ref": "openwebui-bridge-adapter-request:m51-safe",
        "session_ref": "openwebui-session:m51-safe",
        "message_ref": "openwebui-message:m51-safe",
        "safe_user_summary": "User asked to view a redacted governance summary.",
        "content_mode": OpenWebUIContentMode.summary_only,
        "approval_ref": None,
    }
    data.update(overrides)
    return OpenWebUIBridgeAdapterRequest(**data)


def test_openwebui_bridge_adapter_pilot_returns_safe_summary_only_result() -> None:
    result = adapt_openwebui_bridge_request(_request())

    assert result.status == OpenWebUIBridgeAdapterStatus.safe_summary_ready
    assert result.adapter_result_ref.startswith("openwebui-bridge-adapter-result:")
    assert result.content_mode == OpenWebUIContentMode.summary_only
    assert result.raw_prompt_returned is False
    assert result.raw_provider_payload_returned is False
    assert result.model_output_authoritative is False
    assert result.openwebui_called is False
    assert result.provider_called is False
    assert result.tool_executed is False
    assert result.memory_written is False
    assert result.context_injected is False
    assert result.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("raw_prompt_present", "RAW_PROMPT_DENIED"),
        ("raw_provider_payload_present", "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_content_present", "RAW_CONTENT_DENIED"),
        ("secret_like_content_present", "SECRET_LIKE_CONTENT_DENIED"),
        ("provider_call_requested", "PROVIDER_CALL_DENIED"),
        ("model_authority_requested", "MODEL_AUTHORITY_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("openwebui_runtime_call_requested", "OPENWEBUI_RUNTIME_CALL_DENIED"),
    ],
)
def test_openwebui_bridge_adapter_pilot_rejects_raw_or_authority_requests(field: str, reason: str) -> None:
    request = _request(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_openwebui_bridge_adapter_request(request)


def test_openwebui_bridge_adapter_pilot_revalidates_model_copy_mutated_fields() -> None:
    request = _request().model_copy(
        update={
            "raw_prompt_present": True,
            "provider_call_requested": True,
            "model_authority_requested": True,
        }
    )

    with pytest.raises(ValueError, match="RAW_PROMPT_DENIED"):
        adapt_openwebui_bridge_request(request)


def test_openwebui_bridge_adapter_pilot_does_not_treat_approval_ref_as_authority() -> None:
    request = _request(
        approval_ref="approval:m51-shell-preview",
        tool_execution_requested=True,
    )

    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        adapt_openwebui_bridge_request(request)


def test_openwebui_bridge_adapter_policy_rejects_runtime_flags() -> None:
    policy = OpenWebUIBridgeAdapterPolicy(
        adapter_runtime_enabled=True,
        live_openwebui_connection_enabled=True,
        provider_call_enabled=True,
        model_authority_enabled=True,
        tool_execution_enabled=True,
        memory_write_enabled=True,
        context_injection_enabled=True,
        raw_prompt_exposure_enabled=True,
        raw_provider_payload_exposure_enabled=True,
    )

    with pytest.raises(ValueError, match="ADAPTER_RUNTIME_DENIED"):
        validate_openwebui_bridge_adapter_policy(policy)

