from typing import Any
import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.decision_router import build_turn_harness_binding
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
    turn_harness_binding = build_turn_harness_binding(
        "How do I build a DIY table?",
        binding_ref="turn-harness-binding:m164-test",
        decision_ref="turn-decision:m164-test",
    )

    response = build_m164_chat_completion_response(
        request,
        gateway_model=M164LocalGatewayModel(),
        transport=transport,
        turn_harness_binding=turn_harness_binding,
    )

    assert len(transport.calls) == 1
    assert response["model"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID
    assert response["choices"][0]["message"]["content"] == "local llama.cpp says hello"
    assert response["uaa_safety"]["loopback_forward_performed"] is True
    assert response["uaa_safety"]["tools_enabled"] is False
    assert response["uaa_safety"]["raw_prompt_logged"] is False
    assert response["uaa_safety"]["raw_provider_payload_exposed"] is False
    assert response["uaa_safety"]["backend_fields_allowlisted"] is True
    assert response["uaa_safety"]["turn_harness_binding"]["turn_contract"] == "answer_directly"
    assert response["uaa_safety"]["turn_harness_binding"]["tools_exposed_count"] == 0
    assert (
        response["uaa_safety"]["turn_harness_binding"]["no_effect_scope"]
        == "turn_harness_binding_compilation_only"
    )


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


@pytest.mark.parametrize("reply_mode", [None, False, True, 1, "true"])
def test_m164_prior_assistant_reply_requires_explicit_internal_mode(reply_mode) -> None:
    prior_reply = "a" * 12
    request = M164ChatCompletionRequest(
        model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        messages=[
            {"role": "user", "content": "u" * 8},
            {"role": "assistant", "content": prior_reply},
            {"role": "user", "content": "v" * 8},
        ],
    )
    arguments = {} if reply_mode is None else {"allow_repeated_assistant_reply": reply_mode}
    if reply_mode is True:
        response = build_m164_chat_completion_response(
            request, gateway_model=M164LocalGatewayModel(),
            transport=FakeM164GatewayTransport(content=prior_reply), **arguments,
        )
        assert response["choices"][0]["message"]["content"] == prior_reply
    else:
        with pytest.raises(ValueError, match="M164_GATEWAY_PROMPT_ECHO_DENIED"):
            build_m164_chat_completion_response(
                request, gateway_model=M164LocalGatewayModel(),
                transport=FakeM164GatewayTransport(content=prior_reply), **arguments,
            )


@pytest.mark.parametrize("role", ["system", "user"])
def test_m164_repeat_mode_never_exempts_user_or_system_echo(role) -> None:
    content = "u" * 8
    request = M164ChatCompletionRequest(
        model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        messages=[{"role": role, "content": content}],
    )
    with pytest.raises(ValueError, match="M164_GATEWAY_PROMPT_ECHO_DENIED"):
        build_m164_chat_completion_response(
            request, gateway_model=M164LocalGatewayModel(),
            transport=FakeM164GatewayTransport(content=content),
            allow_repeated_assistant_reply=True,
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


def test_m164_namespaced_model_works_through_existing_api_without_alias_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ultimate_ai_agent.core.local_model_management.gateway as gateway_module

    _enable_gateway(monkeypatch)
    model_id = "qwen/qwen3.8-27b"
    monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", model_id)
    transport = FakeM164GatewayTransport(content="y" * 12)
    monkeypatch.setattr(gateway_module, "StdlibM164LlamaCppGatewayTransport", lambda: transport)
    assert client.get("/v1/models", headers=_headers()).json()["data"][0]["id"] == model_id
    response = client.post(
        "/v1/chat/completions", headers=_headers(),
        json={"model": model_id, "messages": [{"role": "user", "content": "x" * 8}]},
    )
    assert response.status_code == 200
    assert response.json()["model"] == model_id
    assert response.json()["uaa_safety"]["tools_enabled"] is False
    assert len(transport.calls) == 1
    assert transport.calls[0].model == model_id
    denied = client.post(
        "/v1/chat/completions", headers=_headers(),
        json={"model": "different/model", "messages": [{"role": "user", "content": "x" * 8}]},
    )
    assert denied.status_code == 422
    assert len(transport.calls) == 1


@pytest.mark.parametrize("model_id", [
    "/absolute-model", "../model", "namespace/../model", "namespace//model",
    "namespace/model/extra", "namespace/", "namespace\\model", "https://example.invalid/model",
    "namespace/model?extra", "namespace/%2fmodel", "namespace/ model", "model\nheader",
    "C:/model.gguf", "c:/model.gguf", "C:model.gguf", "C:\\model.gguf",
])
def test_m164_namespaced_ids_still_reject_paths_and_ambiguous_identifiers(model_id: str) -> None:
    with pytest.raises(ValueError):
        M164LocalGatewayModel(model_id=model_id)
    with pytest.raises(ValueError):
        M164ChatCompletionRequest(model=model_id, messages=[{"role": "user", "content": "x"}])


def test_m164_api_requires_gateway_bearer_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_m164_api_requires_configured_gateway_bearer_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "1")
    monkeypatch.delenv(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, raising=False)

    response = client.get("/v1/models", headers={"Authorization": f"Bearer {DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY}"})

    assert response.status_code == 401


def _control_center_session_headers(monkeypatch, tmp_path, *, expired=False):
    from datetime import timedelta
    from ultimate_ai_agent.core.build_identity import build_identity
    from ultimate_ai_agent.core.control_center.backend_truth import (
        backend_instance_ref,
        build_control_center_backend_truth,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository
    from ultimate_ai_agent.core.time import utc_now

    _enable_gateway(monkeypatch)
    monkeypatch.setenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "0")
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", "fixture-control-center-session")
    monkeypatch.setenv("UAA_BUILD_COMMIT", "7" * 40)
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "session-state"),
        identity=build_identity(),
        now=utc_now() - timedelta(minutes=10) if expired else None,
    )
    return {
        "Authorization": "Bearer fixture-control-center-session",
        "X-UAA-Idempotency-Key": "idempotency-ref:m164-session-test",
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{'7' * 40}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }


def test_m164_control_center_session_uses_distinct_credentials_without_exposing_gateway_key(monkeypatch, tmp_path):
    import ultimate_ai_agent.core.local_model_management.gateway as gateway_module

    headers = _control_center_session_headers(monkeypatch, tmp_path)
    headers["X-UAA-Operator-Confirmed"] = "send-one-local-turn.v1"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "turn-state"))
    transport = FakeM164GatewayTransport(content="y" * 12)
    monkeypatch.setattr(gateway_module, "StdlibM164LlamaCppGatewayTransport", lambda: transport)
    models = client.get("/v1/models", headers=headers)
    assert models.status_code == 200
    reply = client.post("/v1/chat/completions", headers=headers, json={
        "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID, "messages": [{"role": "user", "content": "x" * 8}],
    })
    assert reply.status_code == 200
    assert len(transport.calls) == 1
    assert reply.json()["uaa_safety"]["backend_fields_allowlisted"] is True
    assert M164_TEST_GATEWAY_KEY not in models.text + reply.text
    assert headers["Authorization"] != _headers()["Authorization"]


@pytest.mark.parametrize("invalid", [
    "missing_binding", "wrong_version", "wrong_instance", "wrong_revision", "wrong_truth",
    "expired_truth", "wrong_bearer", "missing_gateway_key", "disabled_gateway",
])
def test_m164_control_center_session_fails_closed_before_transport(monkeypatch, tmp_path, invalid):
    import ultimate_ai_agent.core.local_model_management.gateway as gateway_module

    headers = _control_center_session_headers(monkeypatch, tmp_path, expired=invalid == "expired_truth")
    transport = FakeM164GatewayTransport(content="y" * 12)
    monkeypatch.setattr(gateway_module, "StdlibM164LlamaCppGatewayTransport", lambda: transport)
    if invalid == "missing_binding":
        headers.pop("X-UAA-Control-Center-Mutation-Binding")
    elif invalid == "wrong_version":
        headers["X-UAA-Control-Center-Mutation-Binding"] = "backend-truth.v0"
    elif invalid == "wrong_instance":
        headers["X-UAA-Expected-Backend-Instance-Ref"] = "backend-instance-ref:other"
    elif invalid == "wrong_revision":
        headers["X-UAA-Expected-Backend-Revision-Ref"] = f"commit-ref:git:{'8' * 40}"
    elif invalid == "wrong_truth":
        headers["X-UAA-Expected-Backend-Truth-Ref"] = "proof-ref:substituted"
    elif invalid == "wrong_bearer":
        headers["Authorization"] = "Bearer wrong-session"
    elif invalid == "missing_gateway_key":
        monkeypatch.delenv(UAA_LLAMA_CPP_GATEWAY_KEY_ENV)
    elif invalid == "disabled_gateway":
        monkeypatch.setenv(UAA_LLAMA_CPP_GATEWAY_ENV, "0")
        monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_ENABLED", "0")
    assert client.get("/v1/models", headers=headers).status_code in {401, 403, 409}
    response = client.post("/v1/chat/completions", headers=headers, json={
        "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID, "messages": [{"role": "user", "content": "x" * 8}],
    })
    assert response.status_code in {401, 403, 409}
    assert not transport.calls


def test_m164_api_chat_success_uses_typed_request_without_live_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)

    def fake_response(
        request: Any,
        *,
        gateway_model: Any,
        api_key: Any | None = None,
        turn_harness_binding: Any | None = None,
    ) -> dict[str, Any]:
        del gateway_model, api_key
        assert isinstance(request, M164ChatCompletionRequest)
        assert turn_harness_binding is not None
        assert turn_harness_binding.turn_contract == "answer_directly"
        assert turn_harness_binding.tools_exposed_count == 0
        return {
            "id": "chatcmpl-uaa-m164-local",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "uaa_safety": {
                "raw_provider_payload_exposed": False,
                "turn_harness_binding": turn_harness_binding.model_dump(mode="json"),
            },
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
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "ok"
    assert body["uaa_safety"]["turn_harness_binding"]["turn_contract"] == "answer_directly"
    assert body["uaa_safety"]["turn_harness_binding"]["raw_prompt_persisted"] is False
    assert (
        body["uaa_safety"]["turn_harness_binding"]["no_effect_scope"]
        == "turn_harness_binding_compilation_only"
    )


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
