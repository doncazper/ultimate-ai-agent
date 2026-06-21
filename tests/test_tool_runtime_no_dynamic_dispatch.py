from typing import Any
import pytest

from ultimate_ai_agent.core.tools.runtime import NOOP_TOOL_NAME, NOOP_TOOL_REF, ToolInvocationRequest, ToolInvocationStatus, evaluate_tool_invocation


def _request(**overrides: Any) -> Any:
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
def test_model_copy_mutated_raw_or_secret_fields_are_revalidated(update: Any, reason: str) -> None:
    request = _request().model_copy(update=update)

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    "update",
    [
        {"module_path": "tool_plugins.file_writer"},
        {"callable_name": "run_file_writer"},
        {"function_name": "execute_tool"},
        {"metadata": {"module_path": "tool_plugins.noop"}},
        {"metadata": {"callable_name": "run_noop"}},
        {"metadata": {"tool_ref": "tool:file_write.v1"}},
    ],
)
def test_model_copy_mutated_dynamic_dispatch_fields_are_revalidated(update: Any) -> None:
    request = _request().model_copy(update=update)

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert "DYNAMIC_DISPATCH_DENIED" in decision.reason_codes


@pytest.mark.parametrize(
    "update",
    [
        {"side_effects_performed": ["file:write"]},
        {"file_write_requested": True},
        {"memory_write_requested": True},
        {"network_call_requested": True},
        {"model_call_requested": True},
        {"shell_command_requested": True},
        {"environment_read_requested": True},
        {"secret_lookup_requested": True},
        {"metadata": {"side_effects_performed": ["file:write"]}},
        {"metadata": {"file_write_requested": True}},
    ],
)
def test_model_copy_mutated_side_effect_fields_are_revalidated(update: Any) -> None:
    request = _request().model_copy(update=update)

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert "SIDE_EFFECT_ATTEMPT_DENIED" in decision.reason_codes


def test_model_copy_mutated_tool_ref_to_effectful_tool_is_denied() -> None:
    request = _request().model_copy(update={"tool_ref": "tool:file_write.v1"})

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert "TOOL_NOT_ALLOWLISTED_DENIED" in decision.reason_codes
    assert "EFFECTFUL_TOOL_BLOCKED" in decision.reason_codes


def test_model_copy_mutated_tool_name_mismatch_is_revalidated() -> None:
    request = _request().model_copy(update={"tool_name": "not_noop"})

    decision = evaluate_tool_invocation(request)

    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert "TOOL_NAME_MISMATCH_DENIED" in decision.reason_codes
