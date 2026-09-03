from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from typing import Any, Protocol
from urllib import error as urllib_error
from urllib import parse, request

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.decision_router import TurnHarnessBindingReadModel
from ultimate_ai_agent.core.local_model_management.contracts import (
    _SECRET_LIKE_RE,
    _validate_safe_payload,
)


UAA_LLAMA_CPP_GATEWAY_ENV = "UAA_LLAMA_CPP_GATEWAY_ENABLED"
UAA_LLAMA_CPP_GATEWAY_KEY_ENV = "UAA_LLAMA_CPP_GATEWAY_KEY"
UAA_LLAMA_CPP_MODEL_ID_ENV = "UAA_LLAMA_CPP_MODEL_ID"
UAA_LLAMA_CPP_BASE_URL_ENV = "UAA_LLAMA_CPP_BASE_URL"
UAA_LLAMA_CPP_API_KEY_ENV = "UAA_LLAMA_CPP_API_KEY"
DEFAULT_UAA_LLAMA_CPP_GATEWAY_KEY = "uaa-local-llama-cpp"
DEFAULT_UAA_LLAMA_CPP_MODEL_ID = "uaa-llama-cpp-local"
DEFAULT_UAA_LLAMA_CPP_BASE_URL = "http://127.0.0.1:8080"
M164_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
M164_MAX_NATIVE_MODEL_CATALOG_BYTES = 256 * 1024
_M164_ALLOWED_FINISH_REASONS = {"stop", "length", "content_filter"}


class _M164Model(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class M164LocalGatewayModel(_M164Model):
    model_id: str = DEFAULT_UAA_LLAMA_CPP_MODEL_ID
    base_url: str = DEFAULT_UAA_LLAMA_CPP_BASE_URL
    owned_by: str = "ultimate-ai-agent-llama-cpp"
    approved: bool = True
    loopback_only: bool = True
    tools_enabled: bool = False
    functions_enabled: bool = False
    streaming_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_model_id(self.model_id)
        _validate_loopback_base_url(self.base_url)
        _validate_safe_text(self.owned_by, "owned_by", max_length=80)
        return self


class M164ChatMessage(_M164Model):
    role: str = Field(..., min_length=1)
    content: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"system", "user", "assistant"}:
            raise ValueError("M164_ROLE_DENIED")
        return normalized


class M164ChatCompletionRequest(_M164Model):
    model: str
    messages: list[M164ChatMessage] = Field(..., min_length=1)
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any = None
    functions: list[dict[str, Any]] | None = None
    function_call: Any = None

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_model_id(self.model)
        if self.stream:
            raise ValueError("M164_STREAMING_DENIED")
        if self.tools or self.tool_choice is not None:
            raise ValueError("M164_TOOLS_DENIED")
        if self.functions or self.function_call is not None:
            raise ValueError("M164_FUNCTIONS_DENIED")
        return self


class M164GatewayReceipt(_M164Model):
    model: str
    message_count: int = Field(ge=0)
    loopback_forward_performed: bool = True
    openwebui_is_agent_brain: bool = False
    tools_enabled: bool = False
    functions_enabled: bool = False
    streaming_enabled: bool = False
    raw_prompt_logged: bool = False
    raw_provider_payload_exposed: bool = False
    backend_fields_allowlisted: bool = True
    unknown_backend_fields_omitted: bool = True
    memory_written: bool = False
    context_injected: bool = False
    production_authority_granted: bool = False


class M164GatewayTransport(Protocol):
    def chat_completions(
        self,
        gateway_model: M164LocalGatewayModel,
        chat_request: M164ChatCompletionRequest,
        *,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        ...


class FakeM164GatewayTransport:
    def __init__(self, content: str = "UAA_M164_LLAMA_CPP_GATEWAY_OK") -> None:
        self.content = content
        self.calls: list[M164ChatCompletionRequest] = []

    def chat_completions(
        self,
        gateway_model: M164LocalGatewayModel,
        chat_request: M164ChatCompletionRequest,
        *,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        del api_key
        self.calls.append(chat_request)
        return _openai_chat_response(gateway_model.model_id, self.content, len(chat_request.messages))


class _M164NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        raise urllib_error.HTTPError(req.full_url, code, "M164_REDIRECT_DENIED", headers, fp)


class StdlibM164LlamaCppGatewayTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 120.0,
        max_response_bytes: int = M164_MAX_RESPONSE_BYTES,
        opener: Any | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self._opener = opener or request.build_opener(
            request.ProxyHandler({}),
            _M164NoRedirectHandler,
        )

    def chat_completions(
        self,
        gateway_model: M164LocalGatewayModel,
        chat_request: M164ChatCompletionRequest,
        *,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        base_url = _validate_loopback_base_url(gateway_model.base_url)
        endpoint = f"{base_url}/v1/chat/completions"
        payload = {
            "model": chat_request.model,
            "messages": [message.model_dump(mode="json") for message in chat_request.messages],
            "stream": False,
        }
        if chat_request.temperature is not None:
            payload["temperature"] = chat_request.temperature
        if chat_request.max_tokens is not None:
            payload["max_tokens"] = chat_request.max_tokens
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        http_request = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener.open(http_request, timeout=self.timeout_seconds) as response:
                body = response.read(self.max_response_bytes + 1)
        except urllib_error.HTTPError as exc:
            if 300 <= exc.code < 400:
                raise ValueError("M164_GATEWAY_REDIRECT_DENIED") from exc
            raise ValueError("M164_LLAMA_CPP_GATEWAY_UNAVAILABLE") from exc
        except urllib_error.URLError as exc:
            raise ValueError("M164_LLAMA_CPP_GATEWAY_UNAVAILABLE") from exc
        if len(body) > self.max_response_bytes:
            raise ValueError("M164_GATEWAY_RESPONSE_TOO_LARGE")
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("M164_GATEWAY_JSON_REQUIRED") from exc
        if not isinstance(decoded, dict):
            raise ValueError("M164_GATEWAY_OBJECT_REQUIRED")
        return decoded


def fetch_loopback_native_model_catalog(
    base_url: str,
    *,
    timeout_seconds: float = 5.0,
    max_response_bytes: int = M164_MAX_NATIVE_MODEL_CATALOG_BYTES,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Read bounded local-server model metadata without granting web access."""

    normalized = _validate_loopback_base_url(base_url)
    if not 0 < timeout_seconds <= 30:
        raise ValueError("M164_NATIVE_MODEL_CATALOG_TIMEOUT_INVALID")
    if not 0 < max_response_bytes <= M164_MAX_NATIVE_MODEL_CATALOG_BYTES:
        raise ValueError("M164_NATIVE_MODEL_CATALOG_BOUND_INVALID")
    http_request = request.Request(
        f"{normalized}/api/v1/models",
        headers={"Accept": "application/json"},
        method="GET",
    )
    http_opener = opener or request.build_opener(
        request.ProxyHandler({}),
        _M164NoRedirectHandler,
    )
    try:
        with http_opener.open(http_request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            content_type = response.headers.get_content_type()
            if status != 200 or content_type != "application/json":
                raise ValueError("M164_NATIVE_MODEL_CATALOG_RESPONSE_INVALID")
            body = response.read(max_response_bytes + 1)
    except urllib_error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("M164_NATIVE_MODEL_CATALOG_REDIRECT_DENIED") from exc
        raise ValueError("M164_NATIVE_MODEL_CATALOG_UNAVAILABLE") from exc
    except (TimeoutError, urllib_error.URLError) as exc:
        raise ValueError("M164_NATIVE_MODEL_CATALOG_UNAVAILABLE") from exc
    if len(body) > max_response_bytes:
        raise ValueError("M164_NATIVE_MODEL_CATALOG_RESPONSE_TOO_LARGE")
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("M164_NATIVE_MODEL_CATALOG_JSON_REQUIRED") from exc
    if not isinstance(decoded, dict):
        raise ValueError("M164_NATIVE_MODEL_CATALOG_OBJECT_REQUIRED")
    return decoded


def llama_cpp_gateway_enabled(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return values.get(UAA_LLAMA_CPP_GATEWAY_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def llama_cpp_gateway_key(env: Mapping[str, str] | None = None) -> str | None:
    values = os.environ if env is None else env
    value = values.get(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "").strip()
    return value or None


def llama_cpp_backend_api_key(env: Mapping[str, str] | None = None) -> str | None:
    values = os.environ if env is None else env
    value = values.get(UAA_LLAMA_CPP_API_KEY_ENV, "").strip()
    return value or None


def llama_cpp_gateway_authorized(authorization_header: str | None, env: Mapping[str, str] | None = None) -> bool:
    if not authorization_header:
        return False
    expected = llama_cpp_gateway_key(env)
    if not expected:
        return False
    scheme, _, value = authorization_header.strip().partition(" ")
    return scheme.lower() == "bearer" and value == expected


def build_m164_gateway_model_from_env(env: Mapping[str, str] | None = None) -> M164LocalGatewayModel:
    values = os.environ if env is None else env
    return M164LocalGatewayModel(
        model_id=values.get(UAA_LLAMA_CPP_MODEL_ID_ENV, DEFAULT_UAA_LLAMA_CPP_MODEL_ID).strip()
        or DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
        base_url=values.get(UAA_LLAMA_CPP_BASE_URL_ENV, DEFAULT_UAA_LLAMA_CPP_BASE_URL).strip()
        or DEFAULT_UAA_LLAMA_CPP_BASE_URL,
    )


def build_m164_local_models_response(gateway_model: M164LocalGatewayModel) -> dict[str, Any]:
    validated = M164LocalGatewayModel.model_validate(gateway_model.model_dump())
    return {
        "object": "list",
        "data": [
            {
                "id": validated.model_id,
                "object": "model",
                "created": 0,
                "owned_by": validated.owned_by,
            }
        ],
        "uaa_safety": {
            "milestone": "M164",
            "loopback_only": True,
            "tools_enabled": False,
            "functions_enabled": False,
            "streaming_enabled": False,
            "openwebui_is_agent_brain": False,
        },
    }


def build_m164_chat_completion_response(
    chat_request: M164ChatCompletionRequest,
    *,
    gateway_model: M164LocalGatewayModel,
    transport: M164GatewayTransport | None = None,
    api_key: str | None = None,
    turn_harness_binding: TurnHarnessBindingReadModel | None = None,
) -> dict[str, Any]:
    validated_model = M164LocalGatewayModel.model_validate(gateway_model.model_dump())
    validated_request = M164ChatCompletionRequest.model_validate(chat_request.model_dump())
    if validated_request.model != validated_model.model_id:
        raise ValueError("M164_MODEL_NOT_APPROVED")
    active_transport = transport or StdlibM164LlamaCppGatewayTransport()
    response_payload = active_transport.chat_completions(validated_model, validated_request, api_key=api_key)
    choices = _sanitize_m164_choices(response_payload.get("choices"), validated_request)
    safety = M164GatewayReceipt(
        model=validated_model.model_id,
        message_count=len(validated_request.messages),
    ).model_dump(mode="json")
    if turn_harness_binding is not None:
        safety["turn_harness_binding"] = turn_harness_binding.model_dump(mode="json")
    return {
        "id": "chatcmpl-uaa-m164-local",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": validated_model.model_id,
        "choices": choices,
        "usage": _sanitize_m164_usage(response_payload.get("usage")),
        "uaa_safety": safety,
    }


def _sanitize_m164_choices(choices: Any, chat_request: M164ChatCompletionRequest) -> list[dict[str, Any]]:
    if not isinstance(choices, list) or not choices:
        raise ValueError("M164_GATEWAY_CHOICES_REQUIRED")
    request_contents = {
        message.content.strip()
        for message in chat_request.messages
        if isinstance(message.content, str) and message.content.strip()
    }
    safe_choices: list[dict[str, Any]] = []
    for fallback_index, choice in enumerate(choices[:4]):
        if not isinstance(choice, dict):
            raise ValueError("M164_GATEWAY_CHOICE_OBJECT_REQUIRED")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("M164_GATEWAY_MESSAGE_OBJECT_REQUIRED")
        role = str(message.get("role", "assistant")).strip().lower()
        if role != "assistant":
            raise ValueError("M164_GATEWAY_ASSISTANT_MESSAGE_REQUIRED")
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("M164_GATEWAY_TEXT_CONTENT_REQUIRED")
        stripped_content = content.strip()
        if stripped_content in request_contents:
            raise ValueError("M164_GATEWAY_PROMPT_ECHO_DENIED")
        _validate_safe_text(stripped_content, "assistant_content", max_length=4096)
        index = choice.get("index", fallback_index)
        if not isinstance(index, int) or index < 0:
            index = fallback_index
        finish_reason = choice.get("finish_reason", "stop")
        if finish_reason not in _M164_ALLOWED_FINISH_REASONS:
            finish_reason = "stop"
        safe_choices.append(
            {
                "index": index,
                "message": {"role": "assistant", "content": stripped_content},
                "finish_reason": finish_reason,
            }
        )
    return safe_choices


def _sanitize_m164_usage(usage: Any) -> dict[str, int]:
    safe_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    if not isinstance(usage, dict):
        return safe_usage
    for key in safe_usage:
        value = usage.get(key)
        if isinstance(value, int) and 0 <= value <= 10_000_000:
            safe_usage[key] = value
    return safe_usage


def _openai_chat_response(model_id: str, content: str, message_count: int) -> dict[str, Any]:
    _validate_safe_text(content, "content", max_length=4096)
    return {
        "id": "chatcmpl-uaa-m164-local",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "uaa_fake_message_count": message_count,
    }


def _validate_loopback_base_url(base_url: str) -> str:
    parsed = parse.urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("M164_LOOPBACK_ONLY_REQUIRED")
    if parsed.username or parsed.password:
        raise ValueError("M164_BASE_URL_SCOPE_DENIED")
    if parsed.path not in {"", "/"}:
        raise ValueError("M164_BASE_URL_SCOPE_DENIED")
    if parsed.query or parsed.params or parsed.fragment:
        raise ValueError("M164_BASE_URL_SCOPE_DENIED")
    return base_url.rstrip("/")


def _validate_model_id(model_id: str) -> None:
    _validate_safe_text(model_id, "model_id", max_length=120)
    if "/" in model_id or "\\" in model_id or ".." in model_id:
        raise ValueError("M164_MODEL_ID_UNSAFE")


def _validate_safe_text(value: str, field_name: str, *, max_length: int) -> None:
    if not value or not value.strip() or len(value) > max_length:
        raise ValueError(f"{field_name} invalid")
    if _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)
