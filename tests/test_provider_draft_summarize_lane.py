from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pydantic import SecretStr

from ultimate_ai_agent.core.providers import (
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    ProviderDraftSummarizeRequest,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    evaluate_provider_draft_summarize,
)
from ultimate_ai_agent.core.providers.live_invocation_adapter import (
    OpenAICompatibleTinyLiveProviderAdapter,
    TinyLiveCredentialResolution,
    TinyLiveProviderTransportResult,
)
from ultimate_ai_agent.core.secrets.vault_contracts import ProviderCredentialVaultPosture
from tests.tiny_provider_invocation_helpers import (
    exact_authority_for,
    invocation_request,
)


ROOT = Path(__file__).resolve().parents[1]


def _draft_request(**overrides: object) -> ProviderDraftSummarizeRequest:
    values: dict[str, object] = {
        "draft_ref": "provider-draft-ref:test-summary",
        "source_context_ref": "source-context-ref:operator-selected-local",
        "safe_prompt_envelope_ref": "safe-prompt-envelope-ref:test-summary",
        "operator_intent_ref": "operator-intent-ref:summarize-local-context",
        "purpose": "summarize",
        "tiny_provider_request": invocation_request(
            invocation_ref="provider-invocation-ref:draft-summarize:test",
            idempotency_ref="idempotency:provider-draft-summarize:test",
            expected_receipt_ref="receipt:provider-draft-summarize:test",
            usage_receipt_ref="usage-receipt-ref:provider-draft-summarize:test",
            cost_receipt_ref="cost-receipt-ref:provider-draft-summarize:test",
            redacted_input_summary_ref=(
                "redacted-input-summary-ref:provider-draft-summarize:test"
            ),
            redacted_output_summary_ref=(
                "redacted-output-summary-ref:provider-draft-summarize:test"
            ),
            safe_disable_ref="safe-disable-ref:provider-draft-summarize:test",
        ),
    }
    values.update(overrides)
    return ProviderDraftSummarizeRequest(**values)


def test_provider_draft_summarize_defaults_to_blocked_no_execution() -> None:
    result = evaluate_provider_draft_summarize(_draft_request())

    assert result.status == "blocked"
    assert result.provider_invocation_allowed is False
    assert result.redacted_draft_preview is None
    assert result.model_output_authoritative is False
    assert result.memory_write_performed is False
    assert result.context_injection_performed is False
    assert result.connector_write_performed is False
    assert result.action_execution_performed is False
    assert result.raw_prompt_persisted is False
    assert result.raw_response_persisted is False
    assert "redacted_draft_preview" not in result.durable_record()


def test_provider_draft_summarize_returns_draft_for_exact_injected_lane(
    tmp_path: Path,
) -> None:
    request = _draft_request()
    provider_request = request.tiny_provider_request
    store = TinyProviderInvocationReceiptStore(tmp_path / "provider-draft.jsonl")

    result = evaluate_provider_draft_summarize(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: _credential_resolution(
                provider_request
            ),
            transport=_fixture_transport,
        ),
        approval_authority=exact_authority_for(provider_request),
        receipt_store=store,
    )

    assert result.status == "draft_ready"
    assert result.provider_invocation_allowed is True
    assert result.provider_invocation_receipt_ref == provider_request.expected_receipt_ref
    assert result.redacted_draft_preview == (
        "Draft summary: selected local context is ready for operator review."
    )
    assert result.output_is_draft_only is True
    assert result.model_output_authoritative is False
    assert result.provider_sdk_call_enabled is False
    assert result.autonomous_provider_call_enabled is False
    assert result.background_execution_enabled is False
    assert len(store.list_receipts()) == 1

    durable = result.durable_record()
    durable_text = json.dumps(durable, sort_keys=True).lower()
    assert "redacted_draft_preview" not in durable
    assert "selected local context is ready" not in durable_text
    assert durable["draft_preview_storage"] == "omitted_returned_to_requester_only"


def test_provider_draft_summarize_blocks_secret_like_preview(tmp_path: Path) -> None:
    request = _draft_request()
    provider_request = request.tiny_provider_request
    store = TinyProviderInvocationReceiptStore(tmp_path / "provider-draft.jsonl")

    def unsafe_transport(
        transport_request: TinyProviderInvocationRequest,
        _credential: SecretStr,
    ) -> TinyLiveProviderTransportResult:
        return TinyLiveProviderTransportResult(
            transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            input_tokens_used=transport_request.estimated_input_tokens,
            output_tokens_used=transport_request.estimated_output_tokens,
            billed_cost_usd=transport_request.estimated_cost_usd or 0.001,
            redacted_output_preview="token=super-sensitive-value",
            network_call_performed=True,
        )

    result = evaluate_provider_draft_summarize(
        request,
        adapter=OpenAICompatibleTinyLiveProviderAdapter(
            enabled=True,
            credential_resolver=lambda _credential_ref: _credential_resolution(
                provider_request
            ),
            transport=unsafe_transport,
        ),
        approval_authority=exact_authority_for(provider_request),
        receipt_store=store,
    )

    assert result.status == "blocked"
    assert result.redacted_draft_preview is None
    assert result.provider_invocation_status == "live_adapter_blocked"
    receipts = store.list_receipts()
    assert len(receipts) == 1
    assert receipts[0].raw_response_persisted is False
    assert receipts[0].model_output_authoritative is False


def test_provider_draft_summarize_cli_inspects_blocked_and_fixture_modes() -> None:
    blocked = subprocess.run(
        [sys.executable, "scripts/inspect_provider_draft_summarize_lane.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    blocked_payload = json.loads(blocked.stdout)
    assert blocked_payload["status"] == "blocked"
    assert blocked_payload["demo_fixture_used"] is False
    assert blocked_payload["real_provider_network_performed"] is False

    fixture = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_provider_draft_summarize_lane.py",
            "--demo-fixture",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    fixture_payload = json.loads(fixture.stdout)
    output_text = fixture.stdout.lower()
    assert fixture_payload["status"] == "draft_ready"
    assert fixture_payload["demo_fixture_used"] is True
    assert fixture_payload["real_provider_network_performed"] is False
    assert fixture_payload["receipt_count"] == 1
    assert "transient-material" not in output_text
    assert "secret" not in output_text


def _fixture_transport(
    request: TinyProviderInvocationRequest,
    _credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    return TinyLiveProviderTransportResult(
        transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
        input_tokens_used=request.estimated_input_tokens,
        output_tokens_used=request.estimated_output_tokens,
        billed_cost_usd=request.estimated_cost_usd or 0.001,
        redacted_output_preview=(
            "Draft summary: selected local context is ready for operator review."
        ),
        network_call_performed=True,
    )


def _credential_resolution(
    request: TinyProviderInvocationRequest,
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:provider-draft-summarize:test",
        vault_record_ref="credential-vault-record-ref:provider-draft-summarize:test",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr("transient-material"),
    )
