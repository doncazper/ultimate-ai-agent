#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    ExactApprovedProviderFallbackAttempt,
    ExactApprovedProviderFallbackRequest,
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    build_tiny_provider_invocation_approval_request,
    evaluate_exact_approved_provider_fallback,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    AnthropicCompatibleTinyLiveProviderAdapter,
    OpenAICompatibleTinyLiveProviderAdapter,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect exact-approved two-provider fallback posture using safe refs only."
        )
    )
    parser.add_argument(
        "--fallback-run-ref",
        default="provider-fallback-run-ref:exact-approved:local-cli",
        help="Safe fallback run ref for inspection output.",
    )
    parser.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:provider-fallback:exact-approved:local-cli",
        help="Safe fallback idempotency ref for inspection output.",
    )
    parser.add_argument(
        "--receipts-path",
        default=None,
        help=(
            "Optional provider invocation receipt JSONL path. If omitted, the "
            "inspection proves fallback blocks before any attempt."
        ),
    )
    return parser.parse_args()


def _request_for_provider(
    prefix: str, *, second: bool = False
) -> TinyProviderInvocationRequest:
    provider_ref = (
        SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF
        if second
        else TINY_PROVIDER_INVOCATION_PROVIDER_REF
    )
    model_ref = (
        SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF
        if second
        else TINY_PROVIDER_INVOCATION_MODEL_REF
    )
    policy_ref = (
        SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF
        if second
        else TINY_PROVIDER_INVOCATION_POLICY_REF
    )
    slug = "anthropic-compatible" if second else "openai-compatible"
    return TinyProviderInvocationRequest(
        invocation_ref=f"provider-invocation-ref:{prefix}:{slug}",
        run_id=f"run-ref:{prefix}:{slug}",
        provider_ref=provider_ref,
        model_ref=model_ref,
        credential_ref=f"credential-ref:{slug}:inspection-only",
        policy_ref=policy_ref,
        approval_ref=f"approval-ref:{prefix}:{slug}",
        approval_scope_ref=f"approval-scope-ref:{prefix}:{slug}",
        cost_estimate_ref=f"cost-estimate-ref:{prefix}:{slug}",
        budget_decision_ref=f"budget-decision-ref:{prefix}:{slug}",
        max_approved_usd_ref=f"max-approved-usd-ref:{prefix}:{slug}",
        max_approved_usd=0.01,
        idempotency_ref=f"idempotency-ref:{prefix}:{slug}",
        expected_receipt_ref=f"receipt-ref:{prefix}:{slug}",
        usage_receipt_ref=f"usage-receipt-ref:{prefix}:{slug}",
        cost_receipt_ref=f"cost-receipt-ref:{prefix}:{slug}",
        redacted_input_summary_ref=f"redacted-input-summary-ref:{prefix}:{slug}",
        redacted_output_summary_ref=f"redacted-output-summary-ref:{prefix}:{slug}",
        safe_disable_ref=f"safe-disable-ref:{prefix}:{slug}",
        estimated_input_tokens=10,
        estimated_output_tokens=5,
        estimated_cost_usd=0.001,
    )


def _approval_authority_for(
    requests: list[TinyProviderInvocationRequest],
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    for request in requests:
        approval_request = build_tiny_provider_invocation_approval_request(request)
        authority.create_request(approval_request)
        authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id="operator:local",
            approval_ref=request.approval_ref,
        )
    return authority


def main() -> int:
    args = parse_args()
    first_request = _request_for_provider("provider-fallback-inspection")
    second_request = _request_for_provider("provider-fallback-inspection", second=True)
    fallback_request = ExactApprovedProviderFallbackRequest(
        fallback_run_ref=args.fallback_run_ref,
        idempotency_ref=args.idempotency_ref,
        attempts=[
            ExactApprovedProviderFallbackAttempt(
                attempt_ref="provider-fallback-attempt-ref:inspection:first",
                sequence_index=1,
                request=first_request,
            ),
            ExactApprovedProviderFallbackAttempt(
                attempt_ref="provider-fallback-attempt-ref:inspection:second",
                sequence_index=2,
                request=second_request,
            ),
        ],
    )
    receipt_store = (
        TinyProviderInvocationReceiptStore(Path(args.receipts_path))
        if args.receipts_path
        else None
    )
    decision = evaluate_exact_approved_provider_fallback(
        fallback_request,
        adapters_by_provider_ref={
            TINY_PROVIDER_INVOCATION_PROVIDER_REF: OpenAICompatibleTinyLiveProviderAdapter(),
            SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF: (
                AnthropicCompatibleTinyLiveProviderAdapter()
            ),
        },
        approval_authority=_approval_authority_for([first_request, second_request]),
        receipt_store=receipt_store,
    )
    payload = decision.model_dump(mode="json")
    payload["receipt_storage"] = {
        "inspected": bool(args.receipts_path),
        "safe_schema_only": True,
        "raw_prompt_response_provider_payload_stored": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
