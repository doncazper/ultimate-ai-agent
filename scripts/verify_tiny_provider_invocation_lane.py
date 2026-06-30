#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pydantic import SecretStr

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import route_rate_limit_group
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.providers import (
    DeterministicTinyProviderInvocationAdapter,
    OpenAICompatibleTinyLiveProviderAdapter,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TinyProviderInvocationAdapter,
    TinyLiveCredentialResolution,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    TinyLiveProviderTransportResult,
    TinyProviderInvocationTransportReceipt,
    build_tiny_provider_invocation_approval_request,
    build_tiny_provider_invocation_readiness,
    evaluate_tiny_provider_invocation,
)
from ultimate_ai_agent.core.secrets.vault_contracts import ProviderCredentialVaultPosture
from ultimate_ai_agent.core.providers.invocation import (
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_PROVIDER_INVOCATION_ROUTE,
)


FORBIDDEN_SOURCE_FRAGMENTS = (
    "import requests",
    "from requests import",
    "import httpx",
    "from httpx import",
    "openai.OpenAI(",
    "anthropic.Anthropic(",
    "google.generativeai",
    "chat.completions.create(",
)
PROVIDER_SDK_FORBIDDEN_FRAGMENTS = (
    "openai.OpenAI(",
    "anthropic.Anthropic(",
    "google.generativeai",
    "chat.completions.create(",
)


def _request(**overrides: object) -> TinyProviderInvocationRequest:
    values: dict[str, object] = {
        "invocation_ref": "provider-invocation-ref:tiny:verify",
        "run_id": "run-ref:tiny-provider-verify",
        "provider_ref": TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "credential_ref": "credential-ref:openai-compatible:scoped-test",
        "policy_ref": TINY_PROVIDER_INVOCATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-runtime:tiny-test",
        "approval_scope_ref": "approval-scope-ref:provider-runtime:tiny-test",
        "cost_estimate_ref": "cost-estimate-ref:provider-runtime:tiny-test",
        "budget_decision_ref": "budget-decision-ref:provider-runtime:tiny-test",
        "max_approved_usd_ref": "max-approved-usd-ref:provider-runtime:tiny-test",
        "max_approved_usd": 0.01,
        "idempotency_ref": "idempotency:provider-runtime:tiny-test",
        "expected_receipt_ref": "receipt:provider-runtime:tiny-test",
        "usage_receipt_ref": "usage-receipt-ref:provider-runtime:tiny-test",
        "cost_receipt_ref": "cost-receipt-ref:provider-runtime:tiny-test",
        "redacted_input_summary_ref": "redacted-input-summary-ref:provider-runtime:tiny-test",
        "redacted_output_summary_ref": "redacted-output-summary-ref:provider-runtime:tiny-test",
        "safe_disable_ref": "safe-disable-ref:provider-runtime:tiny-test",
        "estimated_input_tokens": 10,
        "estimated_output_tokens": 5,
        "estimated_cost_usd": 0.001,
    }
    values.update(overrides)
    return TinyProviderInvocationRequest(**values)


def _exact_authority_for(request: TinyProviderInvocationRequest) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_tiny_provider_invocation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def _evaluate_with_exact_approval(
    request: TinyProviderInvocationRequest,
    **kwargs: object,
):
    return evaluate_tiny_provider_invocation(
        request,
        approval_authority=_exact_authority_for(request),
        **kwargs,
    )


class _OverBudgetTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    enabled = True

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref="provider-transport-ref:tiny-provider:over-budget",
            adapter_ref=self.adapter_ref,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=(request.max_approved_usd or 0) + 0.01,
        )


class _SpoofedNetworkTinyProviderInvocationAdapter(TinyProviderInvocationAdapter):
    adapter_ref = "provider-adapter-ref:tiny-exact-approved:spoofed"
    enabled = True

    def execute(
        self,
        request: TinyProviderInvocationRequest,
    ) -> TinyProviderInvocationTransportReceipt:
        return TinyProviderInvocationTransportReceipt(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
            redacted_output_summary_ref=request.redacted_output_summary_ref,
            usage_receipt_ref=request.usage_receipt_ref,
            cost_receipt_ref=request.cost_receipt_ref,
            input_tokens_used=request.estimated_input_tokens,
            output_tokens_used=request.estimated_output_tokens,
            billed_cost_usd=request.estimated_cost_usd,
            network_call_performed=True,
        )


def _mocked_live_transport(
    request: TinyProviderInvocationRequest,
    credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    if credential.get_secret_value() != "transient-material":
        raise AssertionError("unexpected transient credential material")
    return TinyLiveProviderTransportResult(
        transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
        input_tokens_used=request.estimated_input_tokens,
        output_tokens_used=request.estimated_output_tokens,
        billed_cost_usd=request.estimated_cost_usd or 0.0,
        network_call_performed=True,
    )


def _credential_resolution(request: TinyProviderInvocationRequest) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:openai-compatible:verify",
        vault_record_ref="credential-vault-record-ref:openai-compatible:verify",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr("transient-material"),
    )


def main() -> int:
    failures: list[str] = []

    readiness = build_tiny_provider_invocation_readiness()
    if readiness.invocation_enabled or readiness.status != TinyProviderInvocationStatus.disabled:
        failures.append("default tiny provider readiness is not disabled")
    if "Approved no execution" in readiness.ui_states:
        failures.append("default tiny provider readiness exposes approved state label")
    for label in ("Live adapter blocked", "Live receipt required"):
        if label not in readiness.ui_states:
            failures.append(f"default tiny provider readiness missing UI label: {label}")

    missing_provider = evaluate_tiny_provider_invocation(
        _request(provider_ref="provider-ref:provider-runtime:not-bound")
    )
    if missing_provider.status != TinyProviderInvocationStatus.blocked_missing_provider_ref:
        failures.append("missing provider ref did not block")

    unknown_cost = _evaluate_with_exact_approval(_request(estimated_cost_usd=None))
    if unknown_cost.status != TinyProviderInvocationStatus.unknown_paid_cost_blocked:
        failures.append("unknown paid cost did not block")

    above_budget = _evaluate_with_exact_approval(
        _request(estimated_cost_usd=0.02, max_approved_usd=0.01)
    )
    if above_budget.status != TinyProviderInvocationStatus.cost_blocked:
        failures.append("above budget provider estimate did not block")

    bad_policy = _evaluate_with_exact_approval(
        _request(policy_ref="policy-ref:provider-runtime:wrong-scope")
    )
    if bad_policy.status != TinyProviderInvocationStatus.blocked_missing_policy_validation:
        failures.append("wrong provider policy ref did not block")

    try:
        _request(credential_ref="credential-ref:/Users/example/.env")
        failures.append("path-shaped credential ref was accepted")
    except ValueError:
        pass

    original_scope = _request()
    replayed_cost_scope = evaluate_tiny_provider_invocation(
        original_scope.model_copy(
            update={
                "estimated_cost_usd": 0.5,
                "max_approved_usd": 1.0,
            }
        ),
        adapter=DeterministicTinyProviderInvocationAdapter(),
        approval_authority=_exact_authority_for(original_scope),
    )
    if replayed_cost_scope.status != TinyProviderInvocationStatus.approval_invalid:
        failures.append("approval grant replay with elevated cost scope did not fail")
    elif "APPROVAL_RESOURCE_NOT_GRANTED" not in replayed_cost_scope.reason_codes:
        failures.append("approval grant replay did not report resource scope failure")

    actual_over_budget = _evaluate_with_exact_approval(
        _request(),
        adapter=_OverBudgetTinyProviderInvocationAdapter(),
    )
    if actual_over_budget.status != TinyProviderInvocationStatus.cost_blocked:
        failures.append("actual usage/cost over approved budget did not block")
    elif actual_over_budget.receipt is not None:
        failures.append("actual over-budget adapter recorded a receipt")

    no_approval = evaluate_tiny_provider_invocation(_request())
    if no_approval.status != TinyProviderInvocationStatus.approval_required:
        failures.append("missing exact approval did not block")

    approved_disabled = _evaluate_with_exact_approval(_request())
    if approved_disabled.status != TinyProviderInvocationStatus.approved_no_execution:
        failures.append("default adapter did not remain approved/no-execution")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = TinyProviderInvocationReceiptStore(Path(tmpdir) / "spoofed-receipts.jsonl")
        spoofed_network = _evaluate_with_exact_approval(
            _request(invocation_ref="provider-invocation-ref:tiny:verify-spoofed-net"),
            adapter=_SpoofedNetworkTinyProviderInvocationAdapter(),
            receipt_store=store,
        )
        if spoofed_network.status != TinyProviderInvocationStatus.live_adapter_blocked:
            failures.append("spoofed network adapter did not block")
        elif "TINY_PROVIDER_TRANSPORT_ADAPTER_REF_MISMATCH" not in spoofed_network.reason_codes:
            failures.append("spoofed network adapter did not report adapter-ref mismatch")
        if store.list_receipts():
            failures.append("spoofed network adapter recorded a receipt")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = TinyProviderInvocationReceiptStore(Path(tmpdir) / "receipts.jsonl")
        success = _evaluate_with_exact_approval(
            _request(invocation_ref="provider-invocation-ref:tiny:success"),
            adapter=DeterministicTinyProviderInvocationAdapter(),
            receipt_store=store,
        )
        if not success.allowed or success.receipt is None:
            failures.append("deterministic exact-approved adapter did not record receipt")
        else:
            receipt_json = json.dumps(success.receipt.model_dump(mode="json"), sort_keys=True)
            if any(fragment in receipt_json.lower() for fragment in ("api_key", "token=", "provider_payload")):
                failures.append("receipt contains unsafe raw/provider/secret content")
            if len(store.list_receipts()) != 1:
                failures.append("receipt store did not persist exactly one redacted receipt")
            if "ACTUAL_USAGE_COST_RECONCILED" not in success.receipt.reason_codes:
                failures.append("receipt does not record actual usage/cost reconciliation")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = TinyProviderInvocationReceiptStore(Path(tmpdir) / "live-receipts.jsonl")
        missing_secret = _evaluate_with_exact_approval(
            _request(invocation_ref="provider-invocation-ref:tiny:verify-missing-secret"),
            adapter=OpenAICompatibleTinyLiveProviderAdapter(enabled=True),
            receipt_store=store,
        )
        if missing_secret.status != TinyProviderInvocationStatus.live_adapter_blocked:
            failures.append("live adapter did not block without transient secret resolver")
        elif "TINY_LIVE_PROVIDER_SECRET_RESOLVER_REQUIRED" not in missing_secret.reason_codes:
            failures.append("live adapter missing-secret block did not expose safe reason code")

        live_request = _request(invocation_ref="provider-invocation-ref:tiny:verify-live-mocked")
        live_mocked = _evaluate_with_exact_approval(
            live_request,
            adapter=OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _credential_ref: _credential_resolution(live_request),
                transport=_mocked_live_transport,
            ),
            receipt_store=store,
        )
        if not live_mocked.allowed or live_mocked.receipt is None:
            failures.append("mocked live adapter did not record redacted receipt")
        elif live_mocked.receipt.adapter_ref != TINY_LIVE_PROVIDER_ADAPTER_REF:
            failures.append("mocked live adapter receipt did not record scoped adapter ref")
        elif not live_mocked.receipt.network_call_performed:
            failures.append("mocked live adapter receipt did not record network posture")
        elif live_mocked.receipt.provider_sdk_used:
            failures.append("mocked live adapter claimed provider SDK use")

        replayed = _evaluate_with_exact_approval(
            live_request,
            adapter=OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                credential_resolver=lambda _credential_ref: _credential_resolution(live_request),
                transport=_mocked_live_transport,
            ),
            receipt_store=store,
        )
        if "IDEMPOTENCY_REPLAYED_RECEIPT" not in replayed.reason_codes:
            failures.append("mocked live adapter did not replay existing idempotent receipt")

        wrong_model_request = _request(
            invocation_ref="provider-invocation-ref:tiny:verify-wrong-model",
            idempotency_ref="idempotency:provider-runtime:tiny-wrong-model",
            expected_receipt_ref="receipt:provider-runtime:tiny-wrong-model",
            usage_receipt_ref="usage-receipt-ref:provider-runtime:tiny-wrong-model",
            cost_receipt_ref="cost-receipt-ref:provider-runtime:tiny-wrong-model",
        )
        wrong_model = _evaluate_with_exact_approval(
            wrong_model_request,
            adapter=OpenAICompatibleTinyLiveProviderAdapter(
                enabled=True,
                provider_model_name="not-the-single-allowed-model",
                credential_resolver=lambda _credential_ref: _credential_resolution(
                    wrong_model_request
                ),
                transport=_mocked_live_transport,
            ),
            receipt_store=store,
        )
        if wrong_model.status != TinyProviderInvocationStatus.live_adapter_blocked:
            failures.append("live adapter did not block unapproved provider model name")
        elif "TINY_LIVE_PROVIDER_MODEL_NAME_NOT_ALLOWLISTED" not in wrong_model.reason_codes:
            failures.append("live adapter wrong-model block did not expose safe reason code")

    manifest = build_api_manifest(app).model_dump(mode="json")
    routes = {
        (route["method"], route["path"]): route
        for route in manifest["routes"]
    }
    route = routes.get(("POST", TINY_PROVIDER_INVOCATION_ROUTE))
    if route is None:
        failures.append("tiny provider route missing from API manifest")
    else:
        if route["route_classification"] != "mutating_requires_authority":
            failures.append("tiny provider route is not mutating_requires_authority")
        if route["side_effect_class"] != "local_dev_workspace_only":
            failures.append("tiny provider route is not local_dev_workspace_only")
        if route["idempotency_required"] is not True:
            failures.append("tiny provider route does not require idempotency")
        if route["rate_limit_group"] != "provider_exact_approved_lane":
            failures.append("tiny provider route is not rate limited as provider lane")
        if "disabled-by-default" not in route["classification_reason"]:
            failures.append("tiny provider route description does not state disabled-by-default")
    if route_rate_limit_group("POST", TINY_PROVIDER_INVOCATION_ROUTE) != "provider_exact_approved_lane":
        failures.append("tiny provider route rate-limit group lookup failed")

    source = Path("src/ultimate_ai_agent/core/providers/invocation.py").read_text(
        encoding="utf-8"
    )
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in source:
            failures.append(f"forbidden provider/network source fragment present: {fragment}")
    live_adapter_source = Path(
        "src/ultimate_ai_agent/core/providers/live_invocation_adapter.py"
    ).read_text(encoding="utf-8")
    if "urllib_request.urlopen" not in live_adapter_source:
        failures.append("live provider network call is not contained in the scoped adapter")
    for fragment in PROVIDER_SDK_FORBIDDEN_FRAGMENTS:
        if fragment in live_adapter_source:
            failures.append(
                f"provider SDK source fragment present in live adapter: {fragment}"
            )

    if failures:
        print("FAIL: tiny provider invocation lane verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: tiny provider invocation lane remains exact-approved, cost-governed, and redacted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
