from typing import Any
import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.local_model_management import (
    DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY,
    DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
    FakeM164GatewayTransport,
    M164ChatCompletionRequest,
    M164LocalGatewayModel,
    UAA_LLAMA_CPP_API_KEY_ENV,
    UAA_LLAMA_CPP_GATEWAY_ENV,
    UAA_LLAMA_CPP_GATEWAY_KEY_ENV,
    build_m164_chat_completion_response,
    build_m164_local_models_response,
    llama_cpp_backend_api_key,
    llama_cpp_gateway_authorized,
    llama_cpp_gateway_enabled,
)


client = TestClient(api_app.app)
M164_TEST_GATEWAY_KEY = "test-llama-cpp-local"


def _headers() -> dict[str, Any]:
    return {
        "Authorization": f"Bearer {M164_TEST_GATEWAY_KEY}",
        "X-UAA-Idempotency-Key": "idempotency:m164-llama-cpp",
    }


def _enable_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, M164_TEST_GATEWAY_KEY)


def test_m164_gateway_enablement_and_auth_are_explicit() -> None:
    assert llama_cpp_gateway_enabled({}) is False
    assert llama_cpp_gateway_enabled({UAA_LLAMA_CPP_GATEWAY_ENV: "1"}) is True
    assert llama_cpp_backend_api_key({}) is None
    assert llama_cpp_backend_api_key({UAA_LLAMA_CPP_API_KEY_ENV: "backend-secret"}) == "backend-secret"
    assert llama_cpp_gateway_authorized(None, {}) is False
    assert llama_cpp_gateway_authorized(f"Bearer {DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY}", {}) is False
    assert (
        llama_cpp_gateway_authorized(
            f"Bearer {M164_TEST_GATEWAY_KEY}",
            {UAA_LLAMA_CPP_GATEWAY_KEY_ENV: M164_TEST_GATEWAY_KEY},
        )
        is True
    )
    assert llama_cpp_gateway_authorized("Bearer wrong", {UAA_LLAMA_CPP_GATEWAY_KEY_ENV: M164_TEST_GATEWAY_KEY}) is False


def test_m164_models_response_exposes_approved_llama_cpp_model_only() -> None:
    response = build_m164_local_models_response(M164LocalGatewayModel())

    assert response["object"] == "list"
    assert response["data"][0]["id"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID
    assert response["uaa_safety"]["loopback_only"] is True
    assert response["uaa_safety"]["tools_enabled"] is False
    assert response["uaa_safety"]["streaming_enabled"] is False


def test_m164_fake_gateway_forwards_to_loopback_transport_without_tools_or_streaming() -> None:
    transport = FakeM164GatewayTransport(content="local llama.cpp says hello")
    request = M164ChatCompletionRequest(
        model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        messages=[{"role": "user", "content": "hello"}],
    )

    response = build_m164_chat_completion_response(
        request,
        gateway_model=M164LocalGatewayModel(),
        transport=transport,
    )

    assert len(transport.calls) == 1
    assert response["model"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID
    assert response["choices"][0]["message"]["content"] == "local llama.cpp says hello"
    assert response["uaa_safety"]["loopback_forward_performed"] is True
    assert response["uaa_safety"]["tools_enabled"] is False
    assert response["uaa_safety"]["raw_prompt_logged"] is False
    assert response["uaa_safety"]["raw_provider_payload_exposed"] is False
    assert response["uaa_safety"]["backend_fields_allowlisted"] is True


def test_m164_gateway_omits_unknown_backend_fields() -> None:
    class LeakyTransport:
        def chat_completions(self, gateway_model: Any, chat_request: Any, *, api_key: Any | None = None) -> dict[str, Any]:
            del gateway_model, chat_request, api_key
            return {
                "id": "backend-id-should-not-cross-boundary",
                "raw_provider_payload": {"prompt": "secret prompt should be omitted"},
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "safe local response"},
                        "finish_reason": "stop",
                        "backend_extra": "omit me",
                    }
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7, "backend_tokens": 99},
            }

    request = M164ChatCompletionRequest(
        model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        messages=[{"role": "user", "content": "hello"}],
    )

    response = build_m164_chat_completion_response(
        request,
        gateway_model=M164LocalGatewayModel(),
        transport=LeakyTransport(),
    )

    assert response["id"] == "chatcmpl-uaa-m164-local"
    assert response["choices"][0] == {
        "index": 0,
        "message": {"role": "assistant", "content": "safe local response"},
        "finish_reason": "stop",
    }
    assert response["usage"] == {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}
    serialized = str(response)
    assert "raw_provider_payload" not in response
    assert response["uaa_safety"]["raw_provider_payload_exposed"] is False
    assert "backend-id-should-not-cross-boundary" not in serialized
    assert "secret prompt" not in serialized


def test_m164_gateway_rejects_exact_prompt_echo() -> None:
    request = M164ChatCompletionRequest(
        model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        messages=[{"role": "user", "content": "hello"}],
    )

    with pytest.raises(ValueError, match="M164_GATEWAY_PROMPT_ECHO_DENIED"):
        build_m164_chat_completion_response(
            request,
            gateway_model=M164LocalGatewayModel(),
            transport=FakeM164GatewayTransport(content="hello"),
        )


@pytest.mark.parametrize(
    "payload,reason",
    [
        (
            {"model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID, "stream": True, "messages": [{"role": "user", "content": "hi"}]},
            "M164_STREAMING_DENIED",
        ),
        (
            {
                "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
                "messages": [{"role": "user", "content": "hi"}],
                "tools": [{"type": "function", "function": {"name": "x"}}],
            },
            "M164_TOOLS_DENIED",
        ),
        (
            {"model": "unsafe/model", "messages": [{"role": "user", "content": "hi"}]},
            "M164_MODEL_ID_UNSAFE",
        ),
    ],
)
def test_m164_request_denies_streaming_tools_and_unsafe_models(payload: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        M164ChatCompletionRequest(**payload)


def test_m164_api_models_endpoint_uses_llama_cpp_mode_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    response = client.get("/v1/models", headers=_headers())

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID


def test_m164_api_requires_gateway_bearer_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_m164_api_requires_configured_gateway_bearer_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")
    monkeypatch.delenv(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, raising=False)

    response = client.get("/v1/models", headers={"Authorization": f"Bearer {DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY}"})

    assert response.status_code == 401


def test_m164_api_chat_success_uses_typed_request_without_live_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    def fake_response(request: Any, *, gateway_model: Any, api_key: Any | None = None) -> dict[str, Any]:
        del gateway_model, api_key
        assert isinstance(request, M164ChatCompletionRequest)
        return {
            "id": "chatcmpl-uaa-m164-local",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "uaa_safety": {"raw_provider_payload_exposed": False},
        }

    monkeypatch.setattr(api_app, "build_m164_chat_completion_response", fake_response)

    response = client.post(
        "/v1/chat/completions",
        headers=_headers(),
        json={
            "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "ok"


def test_m164_api_redacts_validation_errors_in_llama_cpp_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    response = client.post(
        "/v1/chat/completions",
        headers=_headers(),
        json={
            "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
            "stream": True,
            "messages": [{"role": "user", "content": "secret prompt should not echo"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "M164 llama.cpp gateway request failed safe validation."
    assert "secret prompt" not in response.text
