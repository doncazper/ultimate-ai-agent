#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pydantic import ValidationError  # noqa: E402

from ultimate_ai_agent.core.approvals import ApprovalGrant, LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.model_runtime import (  # noqa: E402
    M23_FIXED_LOCAL_MODEL_PROMPT_ID,
    LocalModelCallRequest,
    LocalModelRuntimeKind,
    ManualStdlibOpenAICompletionsLocalModelCallTransport,
    ManualStdlibLoopbackLocalModelCallTransport,
    build_dry_run_local_model_call_result,
    build_m23_fixed_prompt,
    local_model_call_approval_request,
    run_local_model_call,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="M23 manual fixed-prompt local model call. CLI-only, loopback-only, and non-authoritative."
    )
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--fixed-prompt-id", required=True, choices=[M23_FIXED_LOCAL_MODEL_PROMPT_ID])
    parser.add_argument("--execute-local-call", action="store_true")
    parser.add_argument("--approval-ref")
    parser.add_argument("--approval-grant-json")
    parser.add_argument("--runtime-kind", default=LocalModelRuntimeKind.ollama_planned.value)
    parser.add_argument("--transport-shape", choices=["ollama-generate", "openai-completions"])
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--max-response-chars", type=int, default=512)
    return parser


def build_transport(transport_shape: str):
    if transport_shape == "openai-completions":
        return ManualStdlibOpenAICompletionsLocalModelCallTransport()
    return ManualStdlibLoopbackLocalModelCallTransport()


def main(argv: list[str] | None = None, *, transport=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prompt = build_m23_fixed_prompt()
    try:
        grant = ApprovalGrant(**json.loads(args.approval_grant_json)) if args.approval_grant_json else None
        request = LocalModelCallRequest(
            request_id="m23_manual_local_model_call",
            run_id=grant.run_id if grant is not None else "run_m23_manual_local_model_call",
            runtime_kind=LocalModelRuntimeKind(args.runtime_kind),
            endpoint_url=args.endpoint,
            safe_endpoint_label="manual loopback local model endpoint",
            model_ref=args.model,
            fixed_prompt_id=args.fixed_prompt_id,
            prompt_text=prompt.prompt_text,
            approval_ref=args.approval_ref,
            timeout_seconds=args.timeout_seconds,
            max_response_chars=args.max_response_chars,
            dry_run=not args.execute_local_call,
            execute_local_call=args.execute_local_call,
        )
        transport_shape = args.transport_shape or _default_transport_shape(request.runtime_kind)
        approval_decision = _approval_decision_from_grant(request, grant)
        result = (
            run_local_model_call(
                request,
                transport=transport or build_transport(transport_shape),
                approval_decision=approval_decision,
            )
            if args.execute_local_call
            else build_dry_run_local_model_call_result(request, transport=transport)
        )
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        result = _validation_denial(str(type(exc).__name__))

    print(json.dumps(result.model_dump(mode="json", exclude={"prompt_text"})))
    return 0 if result.decision.allowed or result.decision.status == "dry_run" else 1


def _approval_decision_from_grant(request: LocalModelCallRequest, grant: ApprovalGrant | None):
    if grant is None:
        return None
    authority = LocalApprovalAuthority()
    authority.load_grant_for_validation(grant)
    return authority.validate(local_model_call_approval_request(request).to_validation_request(request.approval_ref or ""))


def _default_transport_shape(runtime_kind: LocalModelRuntimeKind) -> str:
    if runtime_kind == LocalModelRuntimeKind.llama_cpp_planned:
        return "openai-completions"
    return "ollama-generate"


def _validation_denial(caused_by: str):
    from ultimate_ai_agent.core.model_runtime import (
        LocalModelCallDecision,
        LocalModelCallReceipt,
        LocalModelCallResult,
        LocalModelCallTransportResult,
    )

    decision = LocalModelCallDecision(
        decision_id="m23_decision_validation_failed",
        request_id="m23_manual_local_model_call",
        allowed=False,
        status="blocked",
        reason_codes=["M23_VALIDATION_FAILED"],
        safe_message="M23 manual local model call validation failed.",
        metadata={"caused_by": [caused_by]},
    )
    transport_result = LocalModelCallTransportResult(
        transport_result_id="m23_transport_validation_failed",
        request_id="m23_manual_local_model_call",
        transport_kind="none",
    )
    receipt = LocalModelCallReceipt(
        receipt_id="m23_receipt_validation_failed",
        request_id="m23_manual_local_model_call",
        runtime_kind=LocalModelRuntimeKind.generic_loopback_http_planned,
        endpoint_label="validation failed",
        fixed_prompt_id=M23_FIXED_LOCAL_MODEL_PROMPT_ID,
        call_performed=False,
        response_summary="Validation failed before any model call.",
    )
    return LocalModelCallResult(
        result_id="m23_result_validation_failed",
        request_id="m23_manual_local_model_call",
        decision=decision,
        transport_result=transport_result,
        receipt=receipt,
        safe_message="M23 validation failed; no endpoint was contacted.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
