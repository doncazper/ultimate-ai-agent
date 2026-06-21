from typing import Any
import json

from scripts import manual_local_model_call
from tests.test_m23_local_model_call_contracts import valid_request
from ultimate_ai_agent.core.model_runtime import (
    LocalModelRuntimeKind,
    ManualStdlibOpenAICompletionsLocalModelCallTransport,
)


class _FakeHTTPResponse:
    status = 200

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        return False

    def read(self, size: int) -> bytes:
        return self._body[:size]


class _RecordingOpenAICompletionsOpener:
    def __init__(self, completion_text: str = "UAA_M23_LOCAL_MODEL_CALL_OK") -> None:
        self.completion_text = completion_text
        self.calls = []

    def __call__(self, request: Any, timeout: float) -> Any:
        self.calls.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "headers": dict(request.header_items()),
                "payload": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return _FakeHTTPResponse({"choices": [{"text": self.completion_text}]})


def test_llama_cpp_openai_completions_transport_extracts_safe_completion_text() -> None:
    opener = _RecordingOpenAICompletionsOpener()
    request = valid_request(
        runtime_kind=LocalModelRuntimeKind.llama_cpp_planned,
        endpoint_url="http://127.0.0.1:8080/v1/completions",
        safe_endpoint_label="loopback llama cpp openai completions endpoint",
        model_ref="local-gguf-model",
    )
    transport = ManualStdlibOpenAICompletionsLocalModelCallTransport(opener=opener)

    result = transport.send(request)

    assert result.transport_kind == "manual_stdlib_openai_completions"
    assert result.call_performed is True
    assert result.endpoint_contacted is True
    assert result.network_scope == "loopback"
    assert result.raw_response_stored is False
    assert result.safe_response_text == "UAA_M23_LOCAL_MODEL_CALL_OK"
    assert result.metadata["response_shape"] == "openai_completions"
    assert opener.calls == [
        {
            "url": "http://127.0.0.1:8080/v1/completions",
            "method": "POST",
            "headers": {"Content-type": "application/json"},
            "payload": {
                "model": "local-gguf-model",
                "prompt": request.prompt_text,
                "stream": False,
                "temperature": 0,
                "max_tokens": 32,
            },
            "timeout": 5.0,
        }
    ]


def test_llama_cpp_transport_blocks_secret_like_completion_text() -> None:
    opener = _RecordingOpenAICompletionsOpener(completion_text="api_key='abcdefghijklmnop'")
    request = valid_request(
        runtime_kind=LocalModelRuntimeKind.llama_cpp_planned,
        endpoint_url="http://127.0.0.1:8080/v1/completions",
        safe_endpoint_label="loopback llama cpp openai completions endpoint",
        model_ref="local-gguf-model",
    )
    transport = ManualStdlibOpenAICompletionsLocalModelCallTransport(opener=opener)

    result = transport.send(request)

    assert result.safe_response_text is None
    assert result.redaction_applied is True
    assert result.metadata["reason_codes"] == ["M23_RESPONSE_SECRET_BLOCKED"]
    assert "api_key" not in result.model_dump_json()


def test_m23_cli_defaults_llama_cpp_runtime_to_openai_completions_transport() -> None:
    assert manual_local_model_call._default_transport_shape(LocalModelRuntimeKind.llama_cpp_planned) == "openai-completions"
    assert manual_local_model_call._default_transport_shape(LocalModelRuntimeKind.ollama_planned) == "ollama-generate"
