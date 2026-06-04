import pytest

from ultimate_ai_agent.core.tools.runtime import NOOP_TOOL_NAME, NOOP_TOOL_REF, ToolInvocationRequest, ToolInvocationStatus, evaluate_tool_invocation


def _request(**overrides):
    data = {
        "invocation_id": "tool-runtime-invocation:m31-revalidation",
        "tool_ref": NOOP_TOOL_REF,
        "tool_name": NOOP_TOOL_NAME,
        "replay_key": "tool-runtime-replay:m31-revalidation",
        "safe_summary": "Run deterministic no-op tool.",
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"contains_raw_prompt": True}, "RAW_PROMPT_DENIED"),
        ({"contains_raw_model_output": True}, "RAW_MODEL_OUTPUT_DENIED"),
        ({"contains_raw_file_content": True}, "RAW_FILE_CONTENT_DENIED"),
        ({"contains_raw_transcript": True}, "RAW_TRANSCRIPT_DENIED"),
        ({"contains_secret_like_content": True}, "SECRET_CONTENT_DENIED"),
        ({"metadata": {"token": "abc123"}}, "SECRET_CONTENT_DENIED"),
        ({"safe_summary": "contains token=abc123"}, "SECRET_CONTENT_DENIED"),
    ],
)
def test_model_copy_mutated_raw_or_secret_fields_are_revalidated(update, reason):
    request = _request().model_copy(update=update)

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


def test_model_copy_mutated_tool_ref_to_effectful_tool_is_denied():
    request = _request().model_copy(update={"tool_ref": "tool:file_write.v1"})

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert "TOOL_NOT_ALLOWLISTED_DENIED" in decision.reason_codes
    assert "EFFECTFUL_TOOL_BLOCKED" in decision.reason_codes
