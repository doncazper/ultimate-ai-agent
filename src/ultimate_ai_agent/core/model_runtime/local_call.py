from ultimate_ai_agent.core.approvals import ApprovalValidationDecision
from ultimate_ai_agent.core.model_runtime.local_call_contracts import (
    M23_FIXED_LOCAL_MODEL_PROMPT_ID,
    LocalModelCallDecision,
    LocalModelCallReceipt,
    LocalModelCallRequest,
    LocalModelCallResult,
    LocalModelCallTransportResult,
)
from ultimate_ai_agent.core.model_runtime.local_call_policy import (
    approval_reasons,
    validate_local_model_call_decision,
    validate_local_model_call_receipt,
    validate_local_model_call_request,
    validate_local_model_transport_result,
)
from ultimate_ai_agent.core.model_runtime.local_call_transport import LocalModelCallTransport


def build_dry_run_local_model_call_result(
    request: LocalModelCallRequest,
    *,
    transport: LocalModelCallTransport | None = None,
) -> LocalModelCallResult:
    del transport
    validate_local_model_call_request(request)
    decision = validate_local_model_call_decision(
        LocalModelCallDecision(
            decision_id=f"m23_decision_{request.request_id}",
            request_id=request.request_id,
            allowed=False,
            status="dry_run",
            reason_codes=["M23_DRY_RUN_ONLY"],
            safe_message="M23 local model call validated in dry-run mode; no endpoint was contacted.",
            required_next_action="rerun_with_execute_flag_and_valid_local_approval",
        )
    )
    transport_result = validate_local_model_transport_result(
        LocalModelCallTransportResult(
            transport_result_id=f"m23_transport_{request.request_id}",
            request_id=request.request_id,
            transport_kind="none",
            call_performed=False,
            endpoint_contacted=False,
            network_scope="none",
            response_received=False,
            raw_response_stored=False,
        )
    )
    receipt = validate_local_model_call_receipt(
        LocalModelCallReceipt(
            receipt_id=f"m23_receipt_{request.request_id}",
            request_id=request.request_id,
            runtime_kind=request.runtime_kind,
            endpoint_label=request.safe_endpoint_label,
            fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
            call_performed=False,
            response_summary="Dry-run validation only; no model output.",
            redaction_status="none",
        )
    )
    return LocalModelCallResult(
        result_id=f"m23_result_{request.request_id}",
        request_id=request.request_id,
        decision=decision,
        transport_result=transport_result,
        receipt=receipt,
        safe_message="M23 dry-run validation completed; model output is non-authoritative and no call was performed.",
        warnings=["No endpoint was contacted."],
    )


def run_local_model_call(
    request: LocalModelCallRequest,
    *,
    transport: LocalModelCallTransport,
    approval_decision: ApprovalValidationDecision | None = None,
) -> LocalModelCallResult:
    validate_local_model_call_request(request)
    if not request.execute_local_call or request.dry_run:
        return build_dry_run_local_model_call_result(request, transport=transport)

    reasons = approval_reasons(request, approval_decision)
    if reasons:
        return _blocked_result(request, reasons, "M23 local model call is blocked by approval policy.")

    transport_result = validate_local_model_transport_result(transport.send(request))
    if transport_result.metadata.get("reason_codes") == ["M23_RESPONSE_SECRET_BLOCKED"]:
        return _blocked_result(
            request,
            ["M23_RESPONSE_SECRET_BLOCKED"],
            "M23 local model response was blocked by secret hygiene.",
            transport_result=transport_result,
            redaction_status="blocked",
        )

    decision = validate_local_model_call_decision(
        LocalModelCallDecision(
            decision_id=f"m23_decision_{request.request_id}",
            request_id=request.request_id,
            allowed=True,
            status="allowed",
            reason_codes=["M23_LOCAL_CALL_ALLOWED", "APPROVAL_VALIDATED"],
            safe_message="M23 fixed-prompt local-only model call completed; model output is non-authoritative.",
        )
    )
    receipt = validate_local_model_call_receipt(
        LocalModelCallReceipt(
            receipt_id=f"m23_receipt_{request.request_id}",
            request_id=request.request_id,
            runtime_kind=request.runtime_kind,
            endpoint_label=request.safe_endpoint_label,
            fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
            call_performed=transport_result.call_performed,
            response_summary=transport_result.safe_response_summary,
            redaction_status="applied" if transport_result.redaction_applied else "none",
            metadata={
                "manual_cli_only": True,
                "fixed_prompt_only": True,
            },
        )
    )
    return LocalModelCallResult(
        result_id=f"m23_result_{request.request_id}",
        request_id=request.request_id,
        decision=decision,
        transport_result=transport_result,
        receipt=receipt,
        safe_message="M23 local model call completed; model output is non-authoritative and not trusted control input.",
    )


def _blocked_result(
    request: LocalModelCallRequest,
    reason_codes: list[str],
    safe_message: str,
    *,
    transport_result: LocalModelCallTransportResult | None = None,
    redaction_status: str = "none",
) -> LocalModelCallResult:
    decision = validate_local_model_call_decision(
        LocalModelCallDecision(
            decision_id=f"m23_decision_{request.request_id}",
            request_id=request.request_id,
            allowed=False,
            status="blocked",
            reason_codes=reason_codes,
            safe_message=safe_message,
            required_next_action="provide_valid_local_manual_approval",
        )
    )
    safe_transport_result = transport_result or validate_local_model_transport_result(
        LocalModelCallTransportResult(
            transport_result_id=f"m23_transport_{request.request_id}",
            request_id=request.request_id,
            transport_kind="none",
            call_performed=False,
            endpoint_contacted=False,
            network_scope="none",
            response_received=False,
            raw_response_stored=False,
        )
    )
    receipt = validate_local_model_call_receipt(
        LocalModelCallReceipt(
            receipt_id=f"m23_receipt_{request.request_id}",
            request_id=request.request_id,
            runtime_kind=request.runtime_kind,
            endpoint_label=request.safe_endpoint_label,
            fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
            call_performed=safe_transport_result.call_performed,
            response_summary="M23 local model call blocked by policy.",
            redaction_status=redaction_status,
        )
    )
    return LocalModelCallResult(
        result_id=f"m23_result_{request.request_id}",
        request_id=request.request_id,
        decision=decision,
        transport_result=safe_transport_result,
        receipt=receipt,
        safe_message=safe_message,
    )
