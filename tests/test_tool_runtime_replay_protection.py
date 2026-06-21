from ultimate_ai_agent.core.tools.runtime import NOOP_TOOL_NAME, NOOP_TOOL_REF, ToolInvocationRequest, ToolInvocationStatus, evaluate_tool_invocation


def test_replay_key_reuse_is_denied() -> None:
    request = ToolInvocationRequest(
        invocation_id="tool-runtime-invocation:m31-replay",
        tool_ref=NOOP_TOOL_REF,
        tool_name=NOOP_TOOL_NAME,
        replay_key="tool-runtime-replay:m31-replay",
        safe_summary="Run deterministic no-op tool.",
    )

    decision = evaluate_tool_invocation(request, replay_keys_seen=["tool-runtime-replay:m31-replay"])

    assert decision.status == ToolInvocationStatus.replay_detected
    assert decision.invocation_allowed is False
    assert decision.execution_performed is False
    assert "TOOL_RUNTIME_REPLAY_DETECTED" in decision.reason_codes
