import pytest

from ultimate_ai_agent.core.agent_runtime import (
    AgentRuntimeAuthorityPosture,
    AgentRuntimeKind,
    AgentRuntimeRequest,
    DeterministicNoopAgentRuntimeAdapter,
)


def _request() -> AgentRuntimeRequest:
    return AgentRuntimeRequest(
        request_ref="agent-runtime-request:test",
        adapter_ref="agent-runtime-adapter:deterministic-noop",
        runtime_kind=AgentRuntimeKind.deterministic_local,
        capability_ref="cap:agent-runtime:test",
        safe_objective_summary="Inspect safe refs only.",
        safe_input_refs=["input-ref:agent-runtime:test"],
        evidence_refs=["evidence-ref:agent-runtime:test"],
        idempotency_ref="idempotency-ref:agent-runtime:test",
    )


def test_agent_runtime_authority_posture_denies_runtime_authority() -> None:
    with pytest.raises(ValueError, match="AGENT_RUNTIME_AUTHORITY_DENIED"):
        AgentRuntimeAuthorityPosture(provider_runtime_authorized=True)

    with pytest.raises(ValueError, match="AGENT_RUNTIME_CORE_AUTHORITY_REQUIRED"):
        AgentRuntimeAuthorityPosture(policy_engine_required=False)


def test_deterministic_noop_adapter_returns_safe_refs_only() -> None:
    adapter = DeterministicNoopAgentRuntimeAdapter()
    result = adapter.invoke(_request())

    assert result.safe_output_ref == "agent-runtime-output:test"
    assert result.execution_performed is False
    assert result.provider_runtime_performed is False
    assert result.memory_write_performed is False
    assert result.context_injection_performed is False
    assert result.connector_write_performed is False
    assert result.output_is_authority is False
    assert result.receipt_refs == ["agent-runtime-receipt:test"]


def test_agent_runtime_request_rejects_unsafe_refs() -> None:
    with pytest.raises(ValueError, match="structured safe ref"):
        AgentRuntimeRequest(
            request_ref="/tmp/raw-path",
            adapter_ref="agent-runtime-adapter:deterministic-noop",
            runtime_kind=AgentRuntimeKind.deterministic_local,
            capability_ref="cap:agent-runtime:test",
            safe_objective_summary="Inspect safe refs only.",
        )


def test_agent_runtime_request_rejects_raw_content_markers_in_safe_summary() -> None:
    with pytest.raises(ValueError, match="forbidden raw-content marker"):
        AgentRuntimeRequest(
            request_ref="agent-runtime-request:test",
            adapter_ref="agent-runtime-adapter:deterministic-noop",
            runtime_kind=AgentRuntimeKind.deterministic_local,
            capability_ref="cap:agent-runtime:test",
            safe_objective_summary="raw_provider_payload should not appear here",
        )
