import pytest

from ultimate_ai_agent.core.model_runtime import (
    M23_FIXED_LOCAL_MODEL_PROMPT_ID,
    LocalModelCallDecision,
    LocalModelCallReceipt,
    LocalModelCallRequest,
    LocalModelCallTransportResult,
    LocalModelRuntimeKind,
    build_m23_fixed_prompt,
    validate_fixed_prompt,
    validate_local_model_call_decision,
    validate_local_model_call_receipt,
    validate_local_model_call_request,
    validate_local_model_transport_result,
)


def valid_request(**overrides):
    prompt = build_m23_fixed_prompt()
    payload = {
        "request_id": "m23_req_1",
        "run_id": "run_m23",
        "runtime_kind": LocalModelRuntimeKind.ollama_planned,
        "endpoint_url": "http://127.0.0.1:11434/api/generate",
        "safe_endpoint_label": "loopback ollama local endpoint",
        "model_ref": "local-model-ref",
        "fixed_prompt_id": prompt.prompt_id,
        "prompt_text": prompt.prompt_text,
        "approval_ref": None,
    }
    payload.update(overrides)
    return LocalModelCallRequest(**payload)


def test_m23_fixed_prompt_is_allowlisted_and_secret_clean():
    prompt = build_m23_fixed_prompt()

    assert prompt.prompt_id == M23_FIXED_LOCAL_MODEL_PROMPT_ID
    assert prompt.allowed_for_m23 is True
    assert prompt.contains_user_content is False
    assert prompt.contains_secret_like_content is False

    assert validate_fixed_prompt(prompt) is prompt


def test_m23_unknown_prompt_id_or_changed_prompt_text_is_rejected():
    prompt = build_m23_fixed_prompt()

    with pytest.raises(ValueError, match="fixed prompt"):
        validate_fixed_prompt(prompt.model_copy(update={"prompt_id": "other_prompt"}))

    with pytest.raises(ValueError, match="fixed prompt"):
        validate_local_model_call_request(valid_request(prompt_text="summarize this user prompt"))


@pytest.mark.parametrize(
    "field",
    [
        "contains_user_content",
        "contains_secret_like_content",
        "tool_call_requested",
        "memory_write_requested",
        "file_write_requested",
        "openwebui_context_requested",
    ],
)
def test_m23_request_rejects_user_content_secrets_tools_memory_files_and_openwebui(field):
    with pytest.raises(ValueError):
        validate_local_model_call_request(valid_request(**{field: True}))


def test_m23_request_rejects_unsafe_limits_and_arbitrary_approval_ref_execution():
    with pytest.raises(ValueError, match="timeout"):
        validate_local_model_call_request(valid_request(timeout_seconds=11))

    with pytest.raises(ValueError, match="response"):
        validate_local_model_call_request(valid_request(max_response_chars=1001))

    with pytest.raises(ValueError, match="approval"):
        validate_local_model_call_request(
            valid_request(
                dry_run=False,
                execute_local_call=True,
                approval_ref="approval_arbitrary_string",
            )
        )


def test_m23_transport_result_receipt_and_decision_remain_non_authoritative():
    decision = LocalModelCallDecision(
        decision_id="m23_decision_1",
        request_id="m23_req_1",
        allowed=True,
        status="allowed",
        reason_codes=["M23_LOCAL_CALL_ALLOWED"],
        safe_message="M23 local call allowed by policy.",
    )
    transport_result = LocalModelCallTransportResult(
        transport_result_id="m23_transport_1",
        request_id="m23_req_1",
        transport_kind="fake",
        call_performed=True,
        endpoint_contacted=True,
        network_scope="loopback",
        response_received=True,
        safe_response_text="UAA_M23_LOCAL_MODEL_CALL_OK",
        safe_response_summary="Fixed local smoke response.",
    )
    receipt = LocalModelCallReceipt(
        receipt_id="m23_receipt_1",
        request_id="m23_req_1",
        runtime_kind=LocalModelRuntimeKind.ollama_planned,
        endpoint_label="loopback ollama local endpoint",
        fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
        call_performed=True,
        response_summary="Fixed local smoke response.",
    )

    assert validate_local_model_call_decision(decision) is decision
    assert validate_local_model_transport_result(transport_result) is transport_result
    assert validate_local_model_call_receipt(receipt) is receipt
    assert receipt.model_output_non_authoritative is True
    assert receipt.tools_executed == []
    assert receipt.memory_written is False
    assert receipt.files_written is False


def test_m23_transport_result_rejects_secret_like_summary_and_raw_storage():
    with pytest.raises(ValueError, match="raw responses"):
        validate_local_model_transport_result(
            LocalModelCallTransportResult(
                transport_result_id="m23_transport_raw",
                request_id="m23_req_1",
                transport_kind="fake",
                raw_response_stored=True,
            )
        )

    with pytest.raises(ValueError, match="secret-like"):
        validate_local_model_transport_result(
            LocalModelCallTransportResult(
                transport_result_id="m23_transport_secret_summary",
                request_id="m23_req_1",
                transport_kind="fake",
                safe_response_summary="api_key='abcdefghijklmnop'",
            )
        )


def test_m23_receipt_rejects_authoritative_or_mutating_claims():
    with pytest.raises(ValueError, match="non-authoritative"):
        validate_local_model_call_receipt(
            LocalModelCallReceipt(
                receipt_id="m23_receipt_bad",
                request_id="m23_req_1",
                runtime_kind=LocalModelRuntimeKind.ollama_planned,
                endpoint_label="loopback",
                fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
                call_performed=True,
                model_output_non_authoritative=False,
                response_summary="unsafe",
            )
        )

    with pytest.raises(ValueError, match="tool"):
        validate_local_model_call_receipt(
            LocalModelCallReceipt(
                receipt_id="m23_receipt_tool",
                request_id="m23_req_1",
                runtime_kind=LocalModelRuntimeKind.ollama_planned,
                endpoint_label="loopback",
                fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
                call_performed=True,
                tools_executed=["tool_ref"],
                response_summary="unsafe",
            )
        )
