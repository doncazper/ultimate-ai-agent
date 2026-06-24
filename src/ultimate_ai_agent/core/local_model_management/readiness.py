from __future__ import annotations

import os
import json
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.constants import (
    _RAW_LOCAL_PATH_RE,
    _SECRET_LIKE_RE,
    _URL_RE,
)

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


_UNSAFE_ADAPTER_READINESS_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw log",
    "raw_log",
    "full shell command",
    "environment dump",
    "env_dump",
    "ollama generate",
    "ollama chat",
    "ollama run",
    "python -m mlx_lm",
    "mlx_lm.generate",
    "mlx_lm.chat",
    "mlx_lm.fuse",
    "mlx_lm.lora",
    "hostname=",
    "username=",
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


class OptionalLocalModelAdapterReadiness(BaseModel):
    adapter_id: Literal["ollama", "mlx_lm"]
    display_name: str
    readiness_state: Literal[
        "ready",
        "not_installed",
        "not_configured",
        "blocked",
        "unavailable",
        "unknown",
    ] = "blocked"
    install_detection_posture: str = "blocked_manual_verification_required"
    config_detection_posture: str = "blocked_manual_verification_required"
    allowed_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "inspection-ref:backend-status-no-binary-execution",
            "inspection-ref:manual-operator-verification-only",
        ]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-authority:model-call",
            "blocked-authority:model-pull-download",
            "blocked-authority:lifecycle-start-stop-switch",
            "blocked-authority:provider-model-authority",
            "blocked-authority:control-center-subprocess-execution",
        ]
    )
    next_safe_action: str = (
        "review local install/config manually; do not pull, start, or call models from UAA"
    )
    safe_evidence_refs: list[str]
    route_refs: list[str] = Field(
        default_factory=lambda: ["GET /control-center/local-models/status"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md"
        ]
    )
    runtime_calls_enabled: bool = False
    model_pulls_enabled: bool = False
    model_downloads_enabled: bool = False
    lifecycle_start_stop_switch_enabled: bool = False
    provider_model_authority_enabled: bool = False
    control_center_subprocess_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def readiness_remains_read_only(self) -> "OptionalLocalModelAdapterReadiness":
        if (
            self.runtime_calls_enabled
            or self.model_pulls_enabled
            or self.model_downloads_enabled
            or self.lifecycle_start_stop_switch_enabled
            or self.provider_model_authority_enabled
            or self.control_center_subprocess_execution_enabled
        ):
            raise ValueError("OPTIONAL_LOCAL_MODEL_ADAPTER_AUTHORITY_DENIED")
        serialized = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        serialized_lower = serialized.lower()
        if (
            _RAW_LOCAL_PATH_RE.search(serialized)
            or _SECRET_LIKE_RE.search(serialized)
            or _URL_RE.search(serialized)
            or any(
                fragment in serialized_lower
                for fragment in _UNSAFE_ADAPTER_READINESS_FRAGMENTS
            )
        ):
            raise ValueError("OPTIONAL_LOCAL_MODEL_ADAPTER_UNSAFE_PAYLOAD_DENIED")
        return self


def build_optional_local_model_adapter_readiness() -> tuple[
    OptionalLocalModelAdapterReadiness, ...
]:
    return (
        OptionalLocalModelAdapterReadiness(
            adapter_id="ollama",
            display_name="Ollama",
            safe_evidence_refs=[
                "evidence-ref:local-model-readiness:ollama:manual-verification-required",
                "evidence-ref:local-model-readiness:ollama:no-runtime-authority",
            ],
        ),
        OptionalLocalModelAdapterReadiness(
            adapter_id="mlx_lm",
            display_name="MLX-LM",
            safe_evidence_refs=[
                "evidence-ref:local-model-readiness:mlx-lm:manual-verification-required",
                "evidence-ref:local-model-readiness:mlx-lm:no-runtime-authority",
            ],
        ),
    )


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
