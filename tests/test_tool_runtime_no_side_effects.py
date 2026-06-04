from ultimate_ai_agent.core.tools.runtime import NOOP_TOOL_NAME, NOOP_TOOL_REF, ToolInvocationRequest, ToolInvocationStatus, evaluate_tool_invocation


def _request(**overrides):
    data = {
        "invocation_id": "tool-runtime-invocation:m31-side-effect",
        "tool_ref": NOOP_TOOL_REF,
        "tool_name": NOOP_TOOL_NAME,
        "replay_key": "tool-runtime-replay:m31-side-effect",
        "safe_summary": "Run deterministic no-op tool.",
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


def _assert_denied(decision, reason):
    assert decision.status == ToolInvocationStatus.denied
    assert decision.invocation_allowed is False
    assert decision.execution_performed is False
    assert decision.side_effects_performed == []
    assert reason in decision.reason_codes


def test_unknown_tool_is_denied():
    decision = evaluate_tool_invocation(_request(tool_ref="tool:unknown.v1"))

    _assert_denied(decision, "TOOL_NOT_ALLOWLISTED_DENIED")


def test_mismatched_tool_name_is_denied():
    decision = evaluate_tool_invocation(_request(tool_name="not_noop"))

    _assert_denied(decision, "TOOL_NAME_MISMATCH_DENIED")


def test_effectful_tool_refs_are_denied():
    for label, tool_ref in [
        ("file", "tool:file_write.v1"),
        ("memory", "tool:memory_write.v1"),
        ("network", "tool:network_call.v1"),
        ("model", "tool:model_call.v1"),
        ("browser", "tool:browser_action.v1"),
        ("mobile", "tool:mobile_action.v1"),
        ("remote", "tool:remote_action.v1"),
        ("plugin", "tool:plugin_enable.v1"),
        ("shell", "tool:shell_action.v1"),
    ]:
        decision = evaluate_tool_invocation(
            _request(
                invocation_id=f"tool-runtime-invocation:m31-{label}",
                replay_key=f"tool-runtime-replay:m31-{label}",
                tool_ref=tool_ref,
            )
        )

        _assert_denied(decision, "TOOL_NOT_ALLOWLISTED_DENIED")
        assert "EFFECTFUL_TOOL_BLOCKED" in decision.reason_codes


def test_dynamic_dispatch_names_are_denied():
    decision = evaluate_tool_invocation(_request(tool_name="module.callable"))

    _assert_denied(decision, "TOOL_NAME_MISMATCH_DENIED")
    assert "DYNAMIC_DISPATCH_DENIED" in decision.reason_codes
