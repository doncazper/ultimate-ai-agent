from ultimate_ai_agent.core.local_model_management import (
    UAA_LLAMA_CPP_GATEWAY_ENV,
    UAA_LLAMA_CPP_GATEWAY_KEY_ENV,
    LocalModelGatewayReadiness,
    inspect_local_model_gateway,
)
from ultimate_ai_agent.core.openwebui_bridge.local_test_shell import (
    UAA_OPENWEBUI_TEST_GATEWAY_ENV,
    UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV,
)


def test_local_model_gateway_readiness_is_disabled_by_default() -> None:
    readiness = inspect_local_model_gateway({})

    assert isinstance(readiness, LocalModelGatewayReadiness)
    assert readiness.model_status == "disabled_by_default"
    assert readiness.chat_status == "disabled_by_default"
    assert readiness.gateway_mode == "disabled"
    assert readiness.local_gateway_enabled is False
    assert readiness.blocked_prerequisite == "Local /v1 gateway is disabled by default."
    assert readiness.gateway_env_ref == UAA_OPENWEBUI_TEST_GATEWAY_ENV


def test_local_model_gateway_readiness_reports_m164_missing_bearer() -> None:
    readiness = inspect_local_model_gateway({UAA_LLAMA_CPP_GATEWAY_ENV: "1"})

    assert readiness.gateway_mode == "m164_llama_cpp"
    assert readiness.model_status == "gateway_misconfigured_missing_bearer"
    assert readiness.chat_status == "gateway_misconfigured_missing_bearer"
    assert readiness.local_gateway_enabled is True
    assert readiness.llama_cpp_gateway_enabled is True
    assert readiness.llama_cpp_bearer_configured is False
    assert readiness.bearer_env_configured is False
    assert readiness.blocked_prerequisite == "M164 local gateway bearer is not configured."
    assert readiness.gateway_env_ref == UAA_LLAMA_CPP_GATEWAY_ENV


def test_local_model_gateway_readiness_reports_m164_ready_for_bearer_auth() -> None:
    readiness = inspect_local_model_gateway(
        {
            UAA_LLAMA_CPP_GATEWAY_ENV: "1",
            UAA_LLAMA_CPP_GATEWAY_KEY_ENV: "local-test-bearer",
        }
    )

    assert readiness.gateway_mode == "m164_llama_cpp"
    assert readiness.model_status == "gateway_enabled_requires_bearer"
    assert readiness.chat_status == "gateway_enabled_requires_bearer"
    assert readiness.llama_cpp_bearer_configured is True
    assert readiness.bearer_env_configured is True
    assert readiness.blocked_prerequisite == ""
    assert readiness.next_safe_action == "call_v1_routes_with_configured_local_bearer"


def test_local_model_gateway_readiness_reports_m151_local_test_mode() -> None:
    readiness = inspect_local_model_gateway({UAA_OPENWEBUI_TEST_GATEWAY_ENV: "1"})

    assert readiness.gateway_mode == "m151_openwebui_local_test"
    assert readiness.model_status == "gateway_enabled_requires_bearer"
    assert readiness.chat_status == "gateway_enabled_requires_bearer"
    assert readiness.local_gateway_enabled is True
    assert readiness.openwebui_test_gateway_enabled is True
    assert readiness.openwebui_test_bearer_configured is False
    assert readiness.bearer_env_configured is False
    assert readiness.blocked_prerequisite == ""
    assert readiness.gateway_env_ref == UAA_OPENWEBUI_TEST_GATEWAY_ENV
    assert readiness.next_safe_action == "call_v1_routes_with_local_test_bearer"


def test_local_model_gateway_readiness_reports_explicit_m151_bearer_env() -> None:
    readiness = inspect_local_model_gateway(
        {
            UAA_OPENWEBUI_TEST_GATEWAY_ENV: "1",
            UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV: "local-openwebui-bearer",
        }
    )

    assert readiness.gateway_mode == "m151_openwebui_local_test"
    assert readiness.openwebui_test_bearer_configured is True
    assert readiness.bearer_env_configured is True
