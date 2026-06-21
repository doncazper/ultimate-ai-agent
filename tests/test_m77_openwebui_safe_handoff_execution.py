from typing import Any
import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIRuntimeBridgeRequest,
    OpenWebUISafeHandoffRequest,
    OpenWebUISafeHandoffStatus,
    build_openwebui_runtime_bridge_envelope,
    build_openwebui_safe_handoff_result,
    validate_openwebui_safe_handoff_policy,
    validate_openwebui_safe_handoff_request,
)


def _bridge_envelope() -> Any:
    return build_openwebui_runtime_bridge_envelope(
        OpenWebUIRuntimeBridgeRequest(
            bridge_request_ref="openwebui-runtime-bridge-request:m77-safe",
            session_ref="openwebui-session:m77-safe",
            safe_conversation_ref="openwebui-safe-conversation:m77-safe",
            actor_ref="actor:m77-reviewer",
            safe_intent_summary="Prepare a safe OpenWebUI handoff for Agent Core review.",
        )
    )


def _handoff_request(**overrides: Any) -> Any:
    envelope = _bridge_envelope()
    data = {
        "handoff_request_ref": "openwebui-safe-handoff-request:m77-safe",
        "bridge_envelope_ref": envelope.bridge_envelope_ref,
        "session_ref": envelope.session_ref,
        "safe_conversation_ref": envelope.safe_conversation_ref,
        "actor_ref": envelope.actor_ref,
        "approval_ref": "approval:m77-exact-bound",
        "approved_bridge_envelope_ref": envelope.bridge_envelope_ref,
        "approved_session_ref": envelope.session_ref,
        "approved_safe_conversation_ref": envelope.safe_conversation_ref,
        "approved_actor_ref": envelope.actor_ref,
        "safe_handoff_summary": "Record an exact-bound safe handoff inside Agent Core.",
    }
    data.update(overrides)
    return OpenWebUISafeHandoffRequest(**data)


def test_openwebui_safe_handoff_execution_records_exact_bound_review_only_result() -> None:
    result = build_openwebui_safe_handoff_result(_handoff_request())

    assert result.status == OpenWebUISafeHandoffStatus.safe_handoff_executed
    assert result.safe_handoff_executed is True
    assert result.bridge_envelope_ref == result.receipt_plan.bridge_envelope_ref
    assert result.approval_ref == result.receipt_plan.approval_ref
    assert result.reason_codes == [
        "M77_OPENWEBUI_SAFE_HANDOFF_EXECUTION",
        "AGENT_CORE_REMAINS_AUTHORITY",
        "M78_REMAINS_FUTURE",
    ]
    assert result.openwebui_called is False
    assert result.provider_called is False
    assert result.model_called is False
    assert result.model_output_authoritative is False
    assert result.tool_executed is False
    assert result.memory_written is False
    assert result.context_injected is False
    assert result.network_called is False
    assert result.credential_cookie_accessed is False
    assert result.raw_prompt_returned is False
    assert result.raw_provider_payload_returned is False
    assert result.raw_content_returned is False
    assert result.production_authority_granted is False
    assert result.side_effects_performed == []
    assert result.receipt_plan.safe_handoff_recorded is True
    assert result.receipt_plan.openwebui_runtime_call_performed is False
    assert result.receipt_plan.raw_provider_payload_stored is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("approval_ref", None, "APPROVAL_REF_REQUIRED"),
        ("approval_ref", "approval_test_m77", "APPROVAL_TEST_REF_DENIED"),
        ("approved_bridge_envelope_ref", "openwebui-runtime-bridge-envelope:other", "APPROVAL_BINDING_MISMATCH"),
        ("approved_session_ref", "openwebui-session:other", "APPROVAL_BINDING_MISMATCH"),
        ("approved_safe_conversation_ref", "openwebui-safe-conversation:other", "APPROVAL_BINDING_MISMATCH"),
        ("approved_actor_ref", "actor:other", "APPROVAL_BINDING_MISMATCH"),
        ("approval_expired", True, "APPROVAL_EXPIRED_DENIED"),
        ("approval_revoked", True, "APPROVAL_REVOKED_DENIED"),
        ("approval_replayed", True, "APPROVAL_REPLAY_DENIED"),
        ("raw_prompt_present", True, "RAW_PROMPT_DENIED"),
        ("raw_provider_payload_present", True, "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_content_present", True, "RAW_CONTENT_DENIED"),
        ("secret_like_content_present", True, "SECRET_LIKE_CONTENT_DENIED"),
        ("openwebui_runtime_call_requested", True, "OPENWEBUI_RUNTIME_CALL_DENIED"),
        ("provider_call_requested", True, "PROVIDER_CALL_DENIED"),
        ("model_call_requested", True, "MODEL_CALL_DENIED"),
        ("model_authority_requested", True, "MODEL_AUTHORITY_DENIED"),
        ("tool_execution_requested", True, "TOOL_EXECUTION_DENIED"),
        ("memory_write_requested", True, "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", True, "CONTEXT_INJECTION_DENIED"),
        ("network_call_requested", True, "OPENWEBUI_NETWORK_CALL_DENIED"),
        ("credential_cookie_access_requested", True, "CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("production_authority_requested", True, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_openwebui_safe_handoff_execution_denies_unbound_or_unsafe_requests(
    field: str, value: object, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_openwebui_safe_handoff_request(_handoff_request(**{field: value}))


def test_openwebui_safe_handoff_execution_revalidates_model_copy_mutated_requests() -> None:
    request = _handoff_request().model_copy(
        update={
            "approved_bridge_envelope_ref": "openwebui-runtime-bridge-envelope:mutated",
            "raw_provider_payload_present": True,
            "context_injection_requested": True,
        }
    )

    with pytest.raises(ValueError, match="APPROVAL_BINDING_MISMATCH"):
        build_openwebui_safe_handoff_result(request)


def test_openwebui_safe_handoff_policy_blocks_every_non_handoff_authority() -> None:
    policy = validate_openwebui_safe_handoff_policy()
    assert policy.safe_handoff_execution_enabled is True
    assert policy.agent_core_remains_authority is True
    assert policy.openwebui_is_agent_brain is False

    with pytest.raises(ValueError, match="OPENWEBUI_RUNTIME_CALL_DENIED"):
        validate_openwebui_safe_handoff_policy(
            policy.model_copy(update={"openwebui_runtime_call_enabled": True})
        )

    with pytest.raises(ValueError, match="CONTEXT_INJECTION_DENIED"):
        validate_openwebui_safe_handoff_policy(
            policy.model_copy(update={"context_injection_enabled": True})
        )
