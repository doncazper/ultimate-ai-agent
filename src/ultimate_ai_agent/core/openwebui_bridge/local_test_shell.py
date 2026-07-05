from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.decision_router import TurnHarnessBindingReadModel


UAA_OPENWEBUI_TEST_MODEL_ID = "uaa-safe-local"
UAA_OPENWEBUI_TEST_GATEWAY_ENV = "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"
UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV = "UAA_OPENWEBUI_TEST_GATEWAY_KEY"
DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY = "uaa-local-test"
M151_LOCAL_TEST_SHELL_DOCS = (
    "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md",
    "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_RUNBOOK.md",
)


class _OpenWebUILocalTestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class OpenWebUILocalTestShellPolicy(_OpenWebUILocalTestModel):
    policy_ref: str = "openwebui-local-test-shell-policy:m151"
    milestone_ref: str = "M151"
    local_dev_only: bool = True
    disabled_by_default: bool = True
    localhost_only: bool = True
    openai_compatible_gateway: bool = True
    deterministic_response_only: bool = True
    safe_summary_only: bool = True
    openwebui_is_agent_brain: bool = False
    provider_call_enabled: bool = False
    model_authority_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    external_network_enabled: bool = False
    raw_prompt_logging_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    dependency_added: bool = False
    production_authority_enabled: bool = False
    docs_refs: tuple[str, ...] = M151_LOCAL_TEST_SHELL_DOCS
    reason_codes: tuple[str, ...] = (
        "M151_LOCAL_DEV_ONLY",
        "M151_DISABLED_BY_DEFAULT",
        "M151_LOCALHOST_ONLY",
        "M151_OPENWEBUI_IS_SHELL_NOT_BRAIN",
        "M151_NO_PROVIDER_CALL",
        "M151_NO_TOOL_EXECUTION",
        "M151_NO_MEMORY_WRITE",
        "M151_NO_CONTEXT_INJECTION",
        "M151_NO_EXTERNAL_NETWORK",
        "M151_NO_RAW_PROMPT_LOGGING",
    )


class OpenWebUILocalChatMessage(BaseModel):
    role: str = Field(..., min_length=1)
    content: str | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"system", "user", "assistant"}:
            raise ValueError("Only system, user, and assistant messages are allowed in M151 local test mode.")
        return normalized


class OpenWebUILocalChatCompletionRequest(BaseModel):
    model: str = Field(..., min_length=1)
    messages: list[OpenWebUILocalChatMessage] = Field(..., min_length=1)
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any = None
    functions: list[dict[str, Any]] | None = None
    function_call: Any = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("model")
    @classmethod
    def _validate_model(cls, value: str) -> str:
        if value != UAA_OPENWEBUI_TEST_MODEL_ID:
            raise ValueError(f"Only {UAA_OPENWEBUI_TEST_MODEL_ID} is available in M151 local test mode.")
        return value

    @model_validator(mode="after")
    def _deny_authority_features(self) -> "OpenWebUILocalChatCompletionRequest":
        if self.stream:
            raise ValueError("Streaming is disabled in M151 local test mode.")
        if self.tools:
            raise ValueError("Tool calls are disabled in M151 local test mode.")
        if self.tool_choice is not None:
            raise ValueError("Tool choice is disabled in M151 local test mode.")
        if self.functions:
            raise ValueError("Function calls are disabled in M151 local test mode.")
        if self.function_call is not None:
            raise ValueError("Function calls are disabled in M151 local test mode.")
        return self


class OpenWebUILocalGatewayReceipt(_OpenWebUILocalTestModel):
    receipt_ref: str = "openwebui-local-test-gateway-receipt:m151"
    model: str = UAA_OPENWEBUI_TEST_MODEL_ID
    message_count: int = Field(..., ge=0)
    local_dev_only: bool = True
    disabled_by_default: bool = True
    localhost_only: bool = True
    deterministic_response_only: bool = True
    openwebui_is_agent_brain: bool = False
    provider_called: bool = False
    model_authority_granted: bool = False
    tool_executed: bool = False
    tools_enabled: bool = False
    functions_enabled: bool = False
    streaming_enabled: bool = False
    memory_written: bool = False
    context_injected: bool = False
    external_network_called: bool = False
    raw_prompt_logged: bool = False
    raw_provider_payload_exposed: bool = False
    production_authority_granted: bool = False
    reason_codes: tuple[str, ...] = OpenWebUILocalTestShellPolicy().reason_codes


def build_default_openwebui_local_test_shell_policy() -> OpenWebUILocalTestShellPolicy:
    return OpenWebUILocalTestShellPolicy()


def openwebui_test_gateway_enabled(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return values.get(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def openwebui_test_gateway_key(env: Mapping[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    configured = values.get(UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV, "").strip()
    return configured or DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY


def openwebui_test_gateway_authorized(
    authorization_header: str | None,
    env: Mapping[str, str] | None = None,
) -> bool:
    expected = openwebui_test_gateway_key(env)
    if not authorization_header:
        return False
    scheme, _, value = authorization_header.strip().partition(" ")
    return scheme.lower() == "bearer" and value == expected


def build_openwebui_local_models_response() -> dict[str, Any]:
    policy = build_default_openwebui_local_test_shell_policy()
    return {
        "object": "list",
        "data": [
            {
                "id": UAA_OPENWEBUI_TEST_MODEL_ID,
                "object": "model",
                "created": 0,
                "owned_by": "ultimate-ai-agent-local",
            }
        ],
        "uaa_safety": policy.model_dump(mode="json"),
    }


def build_openwebui_local_chat_completion_response(
    request: OpenWebUILocalChatCompletionRequest,
    *,
    turn_harness_binding: TurnHarnessBindingReadModel | None = None,
) -> dict[str, Any]:
    receipt = OpenWebUILocalGatewayReceipt(message_count=len(request.messages))
    safety = receipt.model_dump(mode="json")
    if turn_harness_binding is not None:
        safety["turn_harness_binding"] = turn_harness_binding.model_dump(mode="json")
    content = (
        "UAA safe local test gateway is online. "
        f"Received {receipt.message_count} message(s). "
        "No tools, provider calls, memory writes, context injection, or external network calls were performed."
    )
    return {
        "id": "chatcmpl-uaa-safe-local-m151",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": UAA_OPENWEBUI_TEST_MODEL_ID,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "uaa_safety": safety,
    }
