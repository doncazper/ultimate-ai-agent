#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import SecretStr

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.providers import (
    PROVIDER_DRAFT_SUMMARIZE_BLOCKED_AUTHORITY_REFS,
    PROVIDER_DRAFT_SUMMARIZE_LANE_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    ProviderDraftSummarizeRequest,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    build_tiny_provider_invocation_approval_request,
    evaluate_provider_draft_summarize,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveCredentialResolution,
    TinyLiveProviderTransportResult,
)
from ultimate_ai_agent.core.secrets.vault_contracts import ProviderCredentialVaultPosture


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the exact provider draft/summarize micro-lane."
    )
    parser.add_argument(
        "--demo-fixture",
        action="store_true",
        help=(
            "Use an injected fake transport and transient test credential to prove "
            "the exact draft path without real provider network."
        ),
    )
    args = parser.parse_args()

    provider_request = _provider_request()
    draft_request = ProviderDraftSummarizeRequest(
        draft_ref="provider-draft-ref:local-operator-summary",
        source_context_ref="source-context-ref:local-operator-selected",
        safe_prompt_envelope_ref="safe-prompt-envelope-ref:provider-draft-summary",
        operator_intent_ref="operator-intent-ref:summarize-selected-local-context",
        purpose="summarize",
        tiny_provider_request=provider_request,
    )

    if not args.demo_fixture:
        result = evaluate_provider_draft_summarize(draft_request)
        payload = {
            "lane_ref": PROVIDER_DRAFT_SUMMARIZE_LANE_REF,
            "status": result.status,
            "result": result.durable_record(),
            "demo_fixture_used": False,
            "real_provider_network_performed": False,
            "blocked_authority_refs": list(PROVIDER_DRAFT_SUMMARIZE_BLOCKED_AUTHORITY_REFS),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    with TemporaryDirectory() as directory:
        store = TinyProviderInvocationReceiptStore(
            Path(directory) / "provider-draft-summarize-receipts.jsonl"
        )
        result = evaluate_provider_draft_summarize(
            draft_request,
            adapter=OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _credential_ref: _credential_resolution(
                    provider_request
                ),
                transport=_fixture_transport,
            ),
            approval_authority=_exact_authority_for(provider_request),
            receipt_store=store,
        )
        payload = {
            "lane_ref": PROVIDER_DRAFT_SUMMARIZE_LANE_REF,
            "status": result.status,
            "result": result.model_dump(mode="json"),
            "durable_record": result.durable_record(),
            "receipt_count": len(store.list_receipts()),
            "demo_fixture_used": True,
            "real_provider_network_performed": False,
            "blocked_authority_refs": list(PROVIDER_DRAFT_SUMMARIZE_BLOCKED_AUTHORITY_REFS),
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _provider_request() -> TinyProviderInvocationRequest:
    return TinyProviderInvocationRequest(
        invocation_ref="provider-invocation-ref:draft-summarize:local-cli",
        run_id="run-ref:provider-draft-summarize:local-cli",
        provider_ref=TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        model_ref=TINY_PROVIDER_INVOCATION_MODEL_REF,
        credential_ref="credential-ref:openai-compatible:draft-summarize-local",
        policy_ref=TINY_PROVIDER_INVOCATION_POLICY_REF,
        approval_ref="approval-ref:provider-draft-summarize:local-cli",
        approval_scope_ref="approval-scope-ref:provider-draft-summarize:local-cli",
        cost_estimate_ref="cost-estimate-ref:provider-draft-summarize:local-cli",
        budget_decision_ref="budget-decision-ref:provider-draft-summarize:local-cli",
        max_approved_usd_ref="max-approved-usd-ref:provider-draft-summarize:local-cli",
        max_approved_usd=0.01,
        idempotency_ref="idempotency:provider-draft-summarize:local-cli",
        expected_receipt_ref="receipt:provider-draft-summarize:local-cli",
        usage_receipt_ref="usage-receipt-ref:provider-draft-summarize:local-cli",
        cost_receipt_ref="cost-receipt-ref:provider-draft-summarize:local-cli",
        redacted_input_summary_ref=(
            "redacted-input-summary-ref:provider-draft-summarize:local-cli"
        ),
        redacted_output_summary_ref=(
            "redacted-output-summary-ref:provider-draft-summarize:local-cli"
        ),
        safe_disable_ref="safe-disable-ref:provider-draft-summarize:local-cli",
        estimated_input_tokens=24,
        estimated_output_tokens=32,
        estimated_cost_usd=0.001,
    )


def _exact_authority_for(
    request: TinyProviderInvocationRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_tiny_provider_invocation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    authority.issue_authority_lease(
        AuthorityLease(
            lease_ref="authority-lease-ref:provider-draft-summarize-execute-cli",
            mode=TrustMode.full_machine_access_session,
            domains={
                AuthorityDomain.provider_model_calls: [
                    AuthorityCapability.read,
                    AuthorityCapability.execute,
                ]
            },
            constraints={
                "provider_lane_ref": "provider-invocation-lane:tiny-exact-approved:v1"
            },
            safe_summary=(
                "CLI fixture lease grants exact provider model call execution "
                "for provider draft summarize inspection."
            ),
        )
    )
    return authority


def _credential_resolution(
    request: TinyProviderInvocationRequest,
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:provider-draft-summarize:fixture",
        vault_record_ref="credential-vault-record-ref:provider-draft-summarize:fixture",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr("transient-material"),
    )


def _fixture_transport(
    request: TinyProviderInvocationRequest,
    _credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    return TinyLiveProviderTransportResult(
        transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
        input_tokens_used=request.estimated_input_tokens,
        output_tokens_used=request.estimated_output_tokens,
        billed_cost_usd=0.001,
        redacted_output_preview=(
            "Draft summary: selected local context is ready for operator review."
        ),
        network_call_performed=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
