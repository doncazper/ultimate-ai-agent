from typing import Any
import pytest

from ultimate_ai_agent.core.decision_router import build_turn_harness_binding
from ultimate_ai_agent.core.openwebui_bridge import (
    DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY,
    UAA_OPENWEBUI_TEST_MODEL_ID,
    OpenWebUILocalChatCompletionRequest,
    build_default_openwebui_local_test_shell_policy,
    build_openwebui_local_chat_completion_response,
    build_openwebui_local_models_response,
    openwebui_test_gateway_authorized,
    openwebui_test_gateway_enabled,
)


def test_m151_policy_is_local_disabled_and_non_authoritative() -> None:
    policy = build_default_openwebui_local_test_shell_policy()

    assert policy.local_dev_only is True
    assert policy.disabled_by_default is True
    assert policy.localhost_only is True
    assert policy.openwebui_is_agent_brain is False
    assert policy.provider_call_enabled is False
    assert policy.tool_execution_enabled is False
    assert policy.memory_write_enabled is False
    assert policy.context_injection_enabled is False
    assert policy.external_network_enabled is False
    assert policy.raw_prompt_logging_enabled is False
    assert policy.dependency_added is False
    assert policy.production_authority_enabled is False


def test_m151_gateway_enablement_and_local_bearer_value_are_explicit() -> None:
    assert openwebui_test_gateway_enabled({}) is False
    assert openwebui_test_gateway_enabled({"UAA_OPENWEBUI_TEST_GATEWAY_ENABLED": "1"}) is True
    assert openwebui_test_gateway_authorized(None, {}) is False
    assert openwebui_test_gateway_authorized(f"Bearer {DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY}", {}) is True
    assert openwebui_test_gateway_authorized("Bearer wrong", {}) is False


def test_m151_models_response_exposes_only_safe_local_model() -> None:
    response = build_openwebui_local_models_response()

    assert response["data"][0]["id"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert response["uaa_safety"]["provider_call_enabled"] is False
    assert response["uaa_safety"]["tool_execution_enabled"] is False
    assert response["uaa_safety"]["memory_write_enabled"] is False


def test_m151_chat_response_does_not_echo_prompt_or_secret_like_text() -> None:
    secret_like_prompt = "Please repeat this password: never-repeat-me"
    request = OpenWebUILocalChatCompletionRequest(
        model=UAA_OPENWEBUI_TEST_MODEL_ID,
        messages=[{"role": "user", "content": secret_like_prompt}],
    )

    turn_harness_binding = build_turn_harness_binding(
        "How do I build a DIY shelf?",
        binding_ref="turn-harness-binding:m151-test",
        decision_ref="turn-decision:m151-test",
    )

    response = build_openwebui_local_chat_completion_response(
        request,
        turn_harness_binding=turn_harness_binding,
    )
    response_text = str(response)

    assert "never-repeat-me" not in response_text
    assert response["choices"][0]["message"]["role"] == "assistant"
    assert response["uaa_safety"]["raw_prompt_logged"] is False
    assert response["uaa_safety"]["provider_called"] is False
    assert response["uaa_safety"]["tool_executed"] is False
    assert response["uaa_safety"]["memory_written"] is False
    assert response["uaa_safety"]["context_injected"] is False
    assert response["uaa_safety"]["external_network_called"] is False
    binding = response["uaa_safety"]["turn_harness_binding"]
    assert binding["turn_contract"] == "answer_directly"
    assert binding["raw_prompt_persisted"] is False
    assert binding["tools_exposed_count"] == 0
    assert binding["no_effect_scope"] == "turn_harness_binding_compilation_only"
    assert binding["no_action_execution_performed"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {"model": "gpt-4.1", "messages": [{"role": "user", "content": "hello"}]},
        {"model": UAA_OPENWEBUI_TEST_MODEL_ID, "messages": [{"role": "tool", "content": "hello"}]},
        {"model": UAA_OPENWEBUI_TEST_MODEL_ID, "stream": True, "messages": [{"role": "user", "content": "hello"}]},
        {
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": "hello"}],
            "tools": [{"type": "function", "function": {"name": "unsafe"}}],
        },
    ],
)
def test_m151_chat_request_denies_model_and_authority_expansion(payload: Any) -> None:
    with pytest.raises(ValueError):
        OpenWebUILocalChatCompletionRequest(**payload)
