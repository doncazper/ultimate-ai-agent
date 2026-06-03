import ipaddress
from typing import Any
from urllib.parse import parse_qsl, urlparse

from ultimate_ai_agent.core.approvals import (
    ApprovalDecisionStatus,
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    ApprovalValidationDecision,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.model_runtime.local_call_contracts import (
    M23_FIXED_LOCAL_MODEL_PROMPT_ID,
    M23_FIXED_LOCAL_MODEL_PROMPT_TEXT,
    M23_LOCAL_MODEL_CALL_ACTION,
    M23_MAX_PROMPT_CHARS,
    M23_MAX_RESPONSE_CHARS,
    M23_MAX_TIMEOUT_SECONDS,
    LocalModelCallDecision,
    LocalModelCallReceipt,
    LocalModelCallRequest,
    LocalModelCallTransportResult,
    LocalModelFixedPrompt,
)
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean, contains_secret_like


M23_SECRET_QUERY_KEYS = {
    "key",
    "secret",
    "password",
    "credential",
    "authorization",
    "auth",
    "token",
    "access_" + "token",
    "refresh_" + "token",
    "admin_" + "token",
    "session_" + "token",
    "api_" + "key",
    "client_" + "secret",
}


def build_m23_fixed_prompt() -> LocalModelFixedPrompt:
    return LocalModelFixedPrompt()


def validate_fixed_prompt(prompt: LocalModelFixedPrompt) -> LocalModelFixedPrompt:
    if prompt.prompt_id != M23_FIXED_LOCAL_MODEL_PROMPT_ID:
        raise ValueError("M23 fixed prompt id is not allowlisted.")
    if prompt.prompt_text != M23_FIXED_LOCAL_MODEL_PROMPT_TEXT:
        raise ValueError("M23 fixed prompt text must match the allowlisted fixed prompt.")
    if not prompt.allowed_for_m23:
        raise ValueError("M23 fixed prompt must be explicitly allowed.")
    if prompt.contains_user_content:
        raise ValueError("M23 fixed prompt must not contain user content.")
    if prompt.contains_secret_like_content:
        raise ValueError("M23 fixed prompt must not contain secret-like content.")
    if len(prompt.prompt_text) > min(prompt.max_prompt_chars, M23_MAX_PROMPT_CHARS):
        raise ValueError("M23 fixed prompt exceeds max_prompt_chars.")
    _assert_safe_metadata_refs(prompt.metadata_refs, "M23 fixed prompt metadata_refs")
    _assert_safe_metadata(prompt.metadata, "M23 fixed prompt metadata")
    assert_secret_clean(prompt.prompt_text, "M23 fixed prompt")
    return prompt


def validate_local_model_endpoint(endpoint_url: str) -> str:
    assert_secret_clean(endpoint_url, "M23 local model endpoint")
    parsed = urlparse(endpoint_url)
    if parsed.scheme != "http":
        raise ValueError("M23 local model endpoint must use loopback HTTP only.")
    if parsed.username or parsed.password:
        raise ValueError("M23 local model endpoint credentials are denied.")
    if not parsed.hostname:
        raise ValueError("M23 local model endpoint host is required.")
    if not _is_loopback_host(parsed.hostname):
        raise ValueError("M23 local model endpoint must be loopback-only.")
    query_keys = {key.lower().replace("-", "_") for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if any(_is_secret_query_key(key) for key in query_keys):
        raise ValueError("M23 local model endpoint secret-like query is denied.")
    return endpoint_url


def validate_local_model_call_request(request: LocalModelCallRequest) -> LocalModelCallRequest:
    validate_local_model_endpoint(request.endpoint_url)
    _assert_safe_endpoint_label(request.safe_endpoint_label)
    validate_fixed_prompt(
        LocalModelFixedPrompt(
            prompt_id=request.fixed_prompt_id,
            prompt_text=request.prompt_text,
            contains_user_content=request.contains_user_content,
            contains_secret_like_content=request.contains_secret_like_content,
        )
    )
    if request.tool_call_requested:
        raise ValueError("M23 local model call must not request tool calls.")
    if request.memory_write_requested:
        raise ValueError("M23 local model call must not request memory writes.")
    if request.file_write_requested:
        raise ValueError("M23 local model call must not request file writes.")
    if request.openwebui_context_requested:
        raise ValueError("M23 local model call must not request OpenWebUI context.")
    if request.timeout_seconds > M23_MAX_TIMEOUT_SECONDS:
        raise ValueError("M23 local model call timeout is too high.")
    if request.max_response_chars > M23_MAX_RESPONSE_CHARS:
        raise ValueError("M23 local model response cap is too high.")
    if request.execute_local_call and request.dry_run:
        raise ValueError("M23 execute_local_call requires dry_run=False.")
    if request.execute_local_call and not request.approval_ref:
        raise ValueError("M23 execute_local_call requires validated approval.")
    if request.execute_local_call and request.approval_ref and request.approval_ref.startswith("approval_arbitrary"):
        raise ValueError("M23 arbitrary approval_ref is not authority.")
    _assert_safe_metadata_refs(request.metadata_refs, "M23 local model call metadata_refs")
    _assert_safe_metadata(request.metadata, "M23 local model call metadata")
    for value in [
        request.request_id,
        request.run_id,
        request.safe_endpoint_label,
        request.model_ref,
        request.fixed_prompt_id,
    ]:
        assert_secret_clean(value, "M23 local model call request")
    return request


def validate_local_model_call_decision(decision: LocalModelCallDecision) -> LocalModelCallDecision:
    _assert_safe_metadata_refs(decision.metadata_refs, "M23 local model decision metadata_refs")
    _assert_safe_metadata(decision.metadata, "M23 local model decision metadata")
    for value in [decision.decision_id, decision.request_id, decision.status, decision.safe_message, *decision.reason_codes]:
        assert_secret_clean(value, "M23 local model decision")
    return decision


def validate_local_model_transport_result(result: LocalModelCallTransportResult) -> LocalModelCallTransportResult:
    if result.raw_response_stored:
        raise ValueError("M23 raw responses must not be stored.")
    if result.endpoint_contacted and result.network_scope != "loopback":
        raise ValueError("M23 local model transport must stay loopback scoped.")
    if result.safe_response_text is not None and contains_secret_like(result.safe_response_text):
        raise ValueError("M23 local model response contains secret-like content.")
    _assert_safe_metadata_refs(result.metadata_refs, "M23 local model transport metadata_refs")
    _assert_safe_metadata(result.metadata, "M23 local model transport metadata")
    for value in [
        result.transport_result_id,
        result.request_id,
        result.transport_kind,
        result.network_scope,
        result.safe_response_text,
        result.safe_response_summary,
    ]:
        assert_secret_clean(value, "M23 local model transport")
    return result


def validate_local_model_call_receipt(receipt: LocalModelCallReceipt) -> LocalModelCallReceipt:
    if not receipt.model_output_non_authoritative:
        raise ValueError("M23 local model output must remain non-authoritative.")
    if receipt.tools_executed:
        raise ValueError("M23 local model call must not execute tools.")
    if receipt.memory_written:
        raise ValueError("M23 local model call must not write memory.")
    if receipt.files_written:
        raise ValueError("M23 local model call must not write files.")
    if receipt.provider_called:
        raise ValueError("M23 local model call must not call providers.")
    if receipt.remote_called:
        raise ValueError("M23 local model call must not call remote endpoints.")
    if receipt.fixed_prompt_id != M23_FIXED_LOCAL_MODEL_PROMPT_ID:
        raise ValueError("M23 receipt must reference the fixed prompt id.")
    _assert_safe_metadata_refs(receipt.metadata_refs, "M23 local model receipt metadata_refs")
    _assert_safe_metadata(receipt.metadata, "M23 local model receipt metadata")
    for value in [
        receipt.receipt_id,
        receipt.request_id,
        receipt.endpoint_label,
        receipt.fixed_prompt_id,
        receipt.response_summary,
        receipt.redaction_status,
        *receipt.event_refs,
    ]:
        assert_secret_clean(value, "M23 local model receipt")
    return receipt


def redact_local_model_response(text: str, max_chars: int) -> tuple[str | None, str | None, bool, bool, str]:
    if contains_secret_like(text):
        return None, None, True, False, "blocked"
    truncated = len(text) > max_chars
    safe_text = text[:max_chars]
    return safe_text, safe_text, False, truncated, "none"


def local_model_call_approval_request(request: LocalModelCallRequest) -> ApprovalRequest:
    actor_context = ActorContext(
        actor_type=ActorType.human_user,
        actor_id="manual_operator",
        authority_source=AuthoritySource.manual_operator_action,
        approval_ref=request.approval_ref,
    )
    return ApprovalRequest(
        approval_request_id=f"areq_{request.request_id}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.model_runtime_request,
        subject_id=request.request_id,
        actor_context=actor_context,
        requested_action=M23_LOCAL_MODEL_CALL_ACTION,
        purpose="Approve M23 fixed-prompt local-only model call.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(classification=ClassificationValue.public, source="m23_local_model_call"),
        resource_refs=[request.endpoint_url, request.model_ref],
        model_profile_id=request.model_ref,
        runtime_request_id=request.request_id,
        trace_id=request.request_id,
        metadata={
            "manual_cli_only": True,
            "fixed_prompt_only": True,
            "model_output_non_authoritative": True,
        },
    )


def approval_reasons(
    request: LocalModelCallRequest,
    approval_decision: ApprovalValidationDecision | None,
) -> list[str]:
    if not request.approval_ref:
        return ["APPROVAL_REQUIRED"]
    if approval_decision is None:
        return ["APPROVAL_DECISION_REQUIRED"]
    if approval_decision.approval_ref != request.approval_ref:
        return ["APPROVAL_REF_MISMATCH"]
    if not approval_decision.allowed:
        return approval_decision.reason_codes or ["APPROVAL_NOT_ALLOWED"]
    if approval_decision.status != ApprovalDecisionStatus.approved:
        return approval_decision.reason_codes or ["APPROVAL_NOT_APPROVED"]
    if approval_decision.matched_grant_ref != request.approval_ref:
        return ["APPROVAL_MATCHED_GRANT_REQUIRED"]
    if approval_decision.safe_message != "Approval grant validated for the requested scope.":
        return ["APPROVAL_EVIDENCE_REQUIRED"]
    if "APPROVAL_VALIDATED" not in approval_decision.reason_codes:
        return ["APPROVAL_VALIDATION_EVIDENCE_REQUIRED"]
    return []


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower().strip("[]")
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_secret_query_key(key: str) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in M23_SECRET_QUERY_KEYS)


def _assert_safe_endpoint_label(label: str) -> None:
    lowered = label.lower()
    forbidden_fragments = [
        "://",
        "?",
        "&",
        "=",
        "@",
        "/api/",
        "localhost:",
        "127.0.0.1:",
        "[::1]:",
    ]
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise ValueError("M23 safe endpoint label must not echo raw endpoint URL details.")


def _assert_safe_metadata_refs(values: list[str], field_name: str) -> None:
    for value in values:
        assert_secret_clean(value, field_name)


def _assert_safe_metadata(metadata: dict[str, Any], field_name: str) -> None:
    for key, value in metadata.items():
        key_text = str(key)
        if _is_secret_query_key(key_text):
            raise ValueError(f"{field_name} contains secret-like content.")
        assert_secret_clean(key_text, field_name)
        if isinstance(value, dict):
            _assert_safe_metadata(value, field_name)
        elif isinstance(value, list):
            for item in value:
                assert_secret_clean(str(item), field_name)
        else:
            assert_secret_clean(str(value), field_name)
