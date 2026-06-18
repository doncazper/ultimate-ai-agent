import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.local_model_management import (
    DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY,
    DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
    FakeM164GatewayTransport,
    M164ChatCompletionRequest,
    M164LocalGatewayModel,
    UAA_LLAMA_CPP_API_KEY_ENV,
    UAA_LLAMA_CPP_GATEWAY_ENV,
    build_m164_chat_completion_response,
    build_m164_local_models_response,
    llama_cpp_backend_api_key,
    llama_cpp_gateway_authorized,
    llama_cpp_gateway_enabled,
)


client = TestClient(app)


def _headers():
    return {"Authorization": f"Bearer {DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY}"}


def test_m164_gateway_enablement_and_auth_are_explicit():
    assert llama_cpp_gateway_enabled({}) is False
    assert llama_cpp_gateway_enabled({UAA_LLAMA_CPP_GATEWAY_ENV: "1"}) is True
    assert llama_cpp_backend_api_key({}) is None
    assert llama_cpp_backend_api_key({UAA_LLAMA_CPP_API_KEY_ENV: "backend-secret"}) == "backend-secret"
    assert llama_cpp_gateway_authorized(None, {}) is False
    assert llama_cpp_gateway_authorized(f"Bearer {DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY}", {}) is True
    assert llama_cpp_gateway_authorized("Bearer wrong", {}) is False


def test_m164_models_response_exposes_approved_llama_cpp_model_only():
    response = build_m164_local_models_response(M164LocalGatewayModel())

    assert response["object"] == "list"
    assert response["data"][0]["id"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID
    assert response["uaa_safety"]["loopback_only"] is True
    assert response["uaa_safety"]["tools_enabled"] is False
    assert response["uaa_safety"]["streaming_enabled"] is False


def test_m164_fake_gateway_forwards_to_loopback_transport_without_tools_or_streaming():
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
def test_m164_request_denies_streaming_tools_and_unsafe_models(payload, reason):
    with pytest.raises(ValueError, match=reason):
        M164ChatCompletionRequest(**payload)


def test_m164_api_models_endpoint_uses_llama_cpp_mode_when_enabled(monkeypatch):
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers=_headers())

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID


def test_m164_api_requires_gateway_bearer_when_enabled(monkeypatch):
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_m164_api_redacts_validation_errors_in_llama_cpp_mode(monkeypatch):
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")

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
