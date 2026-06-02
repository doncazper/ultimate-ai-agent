import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.model_runtime import (
    LocalModelRuntimeActivationDecision,
    LocalModelRuntimeActivationPolicy,
    LocalModelRuntimeActivationRequest,
    LocalModelRuntimeActivationStatus,
    LocalModelRuntimeKind,
    validate_local_runtime_activation_decision,
    validate_local_runtime_activation_policy,
    validate_local_runtime_activation_request,
)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("activation_allowed_now", "activation"),
        ("endpoint_probe_allowed", "endpoint probe"),
        ("provider_call_allowed", "provider call"),
        ("user_content_allowed", "user content"),
        ("tool_call_allowed", "tool call"),
        ("memory_write_allowed", "memory write"),
        ("remote_host_allowed", "remote host"),
        ("secret_material_allowed", "secret"),
        ("approval_ref_can_authorize_activation", "approval_ref"),
    ],
)
def test_activation_policy_rejects_m22_authority_flags(field, message):
    policy = LocalModelRuntimeActivationPolicy(**{field: True})

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_activation_policy(policy)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("runtime_execution_requested", "runtime execution"),
        ("provider_call_requested", "provider call"),
        ("endpoint_probe_requested", "endpoint probe"),
        ("prompt_present", "prompt"),
        ("user_content_present", "user content"),
        ("secret_present", "secret"),
        ("tool_call_requested", "tool call"),
        ("memory_write_requested", "memory write"),
    ],
)
def test_activation_request_rejects_runtime_call_or_content_flags(field, message):
    request = LocalModelRuntimeActivationRequest(
        request_ref="local_runtime_activation_request_demo",
        runtime_kind=LocalModelRuntimeKind.ollama_planned,
        safe_summary="metadata only activation request",
        **{field: True},
    )

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_activation_request(request)


def test_approval_ref_does_not_authorize_activation_request():
    request = LocalModelRuntimeActivationRequest(
        request_ref="local_runtime_activation_request_demo",
        runtime_kind=LocalModelRuntimeKind.llama_cpp_planned,
        approval_ref="approval_made_up",
        runtime_execution_requested=True,
        safe_summary="metadata only activation request",
    )

    with pytest.raises(ValueError, match="approval_ref"):
        validate_local_runtime_activation_request(request)


def test_activation_decision_cannot_allow_runtime_activation():
    decision = LocalModelRuntimeActivationDecision(
        decision_ref="local_runtime_activation_decision_demo",
        runtime_kind=LocalModelRuntimeKind.mlx_planned,
        allowed=True,
        status=LocalModelRuntimeActivationStatus.contract_valid,
        safe_message="metadata only activation decision",
    )

    with pytest.raises(ValueError, match="cannot authorize"):
        validate_local_runtime_activation_decision(decision)


def test_activation_request_forbids_raw_prompt_field():
    with pytest.raises(ValidationError):
        LocalModelRuntimeActivationRequest(
            request_ref="local_runtime_activation_request_raw",
            runtime_kind=LocalModelRuntimeKind.ollama_planned,
            safe_summary="metadata only activation request",
            raw_prompt="not allowed",
        )
