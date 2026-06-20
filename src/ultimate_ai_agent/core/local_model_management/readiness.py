from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent.core.local_model_management.gateway import (
    UAA_LLAMA_CPP_GATEWAY_ENV,
    llama_cpp_gateway_enabled,
    llama_cpp_gateway_key,
)
from ultimate_ai_agent.core.openwebui_bridge.local_test_shell import (
    UAA_OPENWEBUI_TEST_GATEWAY_ENV,
    UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV,
    openwebui_test_gateway_enabled,
)


class LocalModelGatewayReadiness(BaseModel):
    model_status: str
    chat_status: str
    model_summary: str
    chat_summary: str
    next_safe_action: str
    blocked_prerequisite: str
    local_gateway_enabled: bool
    llama_cpp_gateway_enabled: bool
    llama_cpp_bearer_configured: bool
    openwebui_test_gateway_enabled: bool
    openwebui_test_bearer_configured: bool
    gateway_mode: str
    gateway_env_ref: str
    bearer_env_configured: bool

    model_config = ConfigDict(extra="forbid")


def inspect_local_model_gateway(env: Mapping[str, str] | None = None) -> LocalModelGatewayReadiness:
    values = os.environ if env is None else env
    llama_enabled = llama_cpp_gateway_enabled(values)
    llama_bearer_configured = bool(llama_cpp_gateway_key(values))
    openwebui_enabled = openwebui_test_gateway_enabled(values)
    openwebui_bearer_configured = bool(values.get(UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV, "").strip())

    if llama_enabled:
        status = (
            "gateway_enabled_requires_bearer"
            if llama_bearer_configured
            else "gateway_misconfigured_missing_bearer"
        )
        summary = (
            "M164 loopback llama.cpp gateway is enabled; model and chat routes require the configured local bearer."
            if llama_bearer_configured
            else "M164 loopback llama.cpp gateway is enabled but no local bearer is configured."
        )
        next_action = (
            "call_v1_routes_with_configured_local_bearer"
            if llama_bearer_configured
            else "configure_m164_local_bearer"
        )
        blocked = "" if llama_bearer_configured else "M164 local gateway bearer is not configured."
        mode = "m164_llama_cpp"
    elif openwebui_enabled:
        status = "gateway_enabled_requires_bearer"
        summary = "M151 local OpenWebUI test gateway is enabled; model and chat routes require the local test bearer."
        next_action = "call_v1_routes_with_local_test_bearer"
        blocked = ""
        mode = "m151_openwebui_local_test"
    else:
        status = "disabled_by_default"
        summary = (
            "Local /v1 model and chat gateways are disabled by default; "
            "no model call or prompt probe is performed by the dashboard."
        )
        next_action = "enable_reviewed_local_gateway_before_chat_smoke"
        blocked = "Local /v1 gateway is disabled by default."
        mode = "disabled"

    return LocalModelGatewayReadiness(
        model_status=status,
        chat_status=status,
        model_summary=summary,
        chat_summary=summary,
        next_safe_action=next_action,
        blocked_prerequisite=blocked,
        local_gateway_enabled=llama_enabled or openwebui_enabled,
        llama_cpp_gateway_enabled=llama_enabled,
        llama_cpp_bearer_configured=llama_bearer_configured,
        openwebui_test_gateway_enabled=openwebui_enabled,
        openwebui_test_bearer_configured=openwebui_bearer_configured,
        gateway_mode=mode,
        gateway_env_ref=UAA_LLAMA_CPP_GATEWAY_ENV if llama_enabled else UAA_OPENWEBUI_TEST_GATEWAY_ENV,
        bearer_env_configured=llama_bearer_configured or openwebui_bearer_configured,
    )
