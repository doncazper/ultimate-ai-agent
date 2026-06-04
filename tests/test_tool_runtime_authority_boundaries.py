import pytest

from ultimate_ai_agent.core.tools.runtime import NOOP_TOOL_NAME, NOOP_TOOL_REF, ToolInvocationRequest, ToolInvocationStatus, evaluate_tool_invocation


def _request(**overrides):
    data = {
        "invocation_id": "tool-runtime-invocation:m31-authority",
        "tool_ref": NOOP_TOOL_REF,
        "tool_name": NOOP_TOOL_NAME,
        "replay_key": "tool-runtime-replay:m31-authority",
        "safe_summary": "Run deterministic no-op tool.",
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


def _assert_denied(decision, reason):
    assert decision.status == ToolInvocationStatus.denied
    assert decision.execution_performed is False
    assert reason in decision.reason_codes


def test_approval_ref_alone_cannot_authorize_noop_runtime():
    decision = evaluate_tool_invocation(_request(approval_ref="approval:m31"))

    _assert_denied(decision, "APPROVAL_REF_NOT_AUTHORITY")


def test_approval_test_ref_is_denied():
    decision = evaluate_tool_invocation(_request(approval_ref="approval_test_m31"))

    _assert_denied(decision, "APPROVAL_TEST_REF_DENIED")


def test_model_copy_mutated_secret_invocation_id_is_denied_safely():
    request = _request().model_copy(update={"invocation_id": "secret:m31-token"})

    decision = evaluate_tool_invocation(request)

    _assert_denied(decision, "SECRET_CONTENT_DENIED")
    assert decision.invocation_id == "tool-runtime-invocation:denied"
    assert "secret" not in decision.safe_message.lower()


@pytest.mark.parametrize(
    "authority_ref",
    [
        "task-plan:m31",
        "context-pack:m31",
        "memory:m31",
        "tool-intent:m31",
        "approval:m31",
        "model:m31",
        "runtime:m31",
        "openwebui:m31",
    ],
)
def test_refs_cannot_authorize_arbitrary_tool_runtime(authority_ref):
    decision = evaluate_tool_invocation(_request(authority_refs=[authority_ref]))

    _assert_denied(decision, "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY")
