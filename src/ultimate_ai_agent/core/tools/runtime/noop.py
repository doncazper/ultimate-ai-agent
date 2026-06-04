from ultimate_ai_agent.core.tools.runtime.contracts import NoOpToolInput, NoOpToolOutput, ToolInvocationRequest


def build_noop_tool_input(request: ToolInvocationRequest) -> NoOpToolInput:
    return NoOpToolInput(
        input_ref=f"noop-input:{request.invocation_id.split(':', 1)[-1]}",
        safe_summary="Validated no-op tool input boundary.",
        metadata_refs=request.metadata_refs,
    )


def invoke_noop_tool(request: ToolInvocationRequest) -> NoOpToolOutput:
    build_noop_tool_input(request)
    return NoOpToolOutput(output_ref=f"noop-output:{request.invocation_id.split(':', 1)[-1]}")
