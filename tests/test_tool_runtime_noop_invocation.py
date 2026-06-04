from ultimate_ai_agent.core.tools.runtime import (
    NOOP_TOOL_NAME,
    NOOP_TOOL_REF,
    ToolInvocationRequest,
    ToolInvocationStatus,
    ToolRuntimeAdapter,
    evaluate_tool_invocation,
)


def _request(**overrides):
    data = {
        "invocation_id": "tool-runtime-invocation:m31-noop",
        "tool_ref": NOOP_TOOL_REF,
        "tool_name": NOOP_TOOL_NAME,
        "replay_key": "tool-runtime-replay:m31-noop",
        "safe_summary": "Run deterministic no-op tool.",
        "input_refs": ["canonical:m31"],
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


def test_noop_invocation_succeeds_deterministically():
    decision = evaluate_tool_invocation(_request())

    assert decision.status == ToolInvocationStatus.noop_completed
    assert decision.invocation_allowed is True
    assert decision.execution_performed is True
    assert decision.side_effects_performed == []
    assert decision.result is not None
    assert decision.result.output.safe_message == "NOOP_TOOL_COMPLETED"
    assert decision.result.output.raw_input_echoed is False
    assert decision.result.output.raw_content_stored is False
    assert decision.result.side_effects_performed == []
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is True
    assert decision.receipt_plan.side_effects_performed == []


def test_noop_adapter_invocation_uses_same_safe_path():
    decision = ToolRuntimeAdapter().invoke(_request(invocation_id="tool-runtime-invocation:m31-adapter"))

    assert decision.status == ToolInvocationStatus.noop_completed
    assert decision.execution_performed is True
    assert decision.result is not None
    assert decision.result.output.safe_message == "NOOP_TOOL_COMPLETED"
