from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.openwebui_bridge import (
    DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY,
    UAA_OPENWEBUI_TEST_GATEWAY_ENV,
    UAA_OPENWEBUI_TEST_MODEL_ID,
)


client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY}"}


def test_m151_models_endpoint_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, raising=False)

    response = client.get("/v1/models", headers=_auth_headers())

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_m151_models_endpoint_requires_local_bearer_value(monkeypatch):
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_m151_models_endpoint_returns_safe_openai_compatible_model_list(monkeypatch):
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "list"
    assert body["data"][0]["id"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert body["uaa_safety"]["provider_call_enabled"] is False
    assert body["uaa_safety"]["tool_execution_enabled"] is False


def test_m151_chat_completion_returns_deterministic_safe_response(monkeypatch):
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")
    secret_like_prompt = "token=should-not-appear"

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": secret_like_prompt}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert "should-not-appear" not in response.text
    assert body["uaa_safety"]["raw_prompt_logged"] is False
    assert body["uaa_safety"]["provider_called"] is False
    assert body["uaa_safety"]["tool_executed"] is False
    assert body["uaa_safety"]["memory_written"] is False
    assert body["uaa_safety"]["context_injected"] is False
    assert body["uaa_safety"]["external_network_called"] is False


def test_m151_chat_completion_rejects_streaming_and_tools(monkeypatch):
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")
    secret_like_prompt = "token=should-not-appear"

    streaming_response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "stream": True,
            "messages": [{"role": "user", "content": secret_like_prompt}],
        },
    )
    tool_response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": "hello"}],
            "tools": [{"type": "function", "function": {"name": "unsafe"}}],
        },
    )

    assert streaming_response.status_code == 422
    assert tool_response.status_code == 422
    assert "should-not-appear" not in streaming_response.text
    assert secret_like_prompt not in streaming_response.text
