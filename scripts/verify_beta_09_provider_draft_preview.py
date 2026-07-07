#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import SecretStr

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.providers import (
    PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
    PROVIDER_DRAFT_SUMMARIZE_PROOF_REF,
    PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF,
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
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parent.parent
LANE_DOC = ROOT / "docs/control_center/PROVIDER_DRAFT_SUMMARIZE_MICRO_LANE.md"
AUTHORITY_BOARD = ROOT / "docs/control_center/AUTHORITY_GRADUATION_BOARD.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
SOURCE_PATHS = (
    ROOT / "src/ultimate_ai_agent/core/providers/draft_summarize.py",
    ROOT / "scripts/inspect_provider_draft_summarize_lane.py",
)
FORBIDDEN_PROVIDER_SDK_FRAGMENTS = (
    "openai.OpenAI(",
    "anthropic.Anthropic(",
    "chat.completions.create(",
    "google.generativeai",
)
REQUIRED_DOC_FRAGMENTS = (
    "Full-strength version",
    "Repo-safe beta-09 version",
    "Blocked / needs authority",
    "Exact promotion path",
    "default Control Center provider invocation remains blocked",
    "Durable records omit the draft preview",
)


def _provider_request(**overrides: object) -> TinyProviderInvocationRequest:
    values: dict[str, object] = {
        "invocation_ref": "provider-invocation-ref:beta-09",
        "run_id": "run-ref:provider-draft-preview:beta-09",
        "provider_ref": TINY_PROVIDER_INVOCATION_PROVIDER_REF,
        "model_ref": TINY_PROVIDER_INVOCATION_MODEL_REF,
        "credential_ref": "credential-ref:provider-draft-preview:beta-09",
        "policy_ref": TINY_PROVIDER_INVOCATION_POLICY_REF,
        "approval_ref": "approval-ref:provider-draft-preview:beta-09",
        "approval_scope_ref": "approval-scope-ref:provider-draft-preview:beta-09",
        "cost_estimate_ref": "cost-estimate-ref:provider-draft-preview:beta-09",
        "budget_decision_ref": "budget-decision-ref:provider-draft-preview:beta-09",
        "max_approved_usd_ref": "max-approved-usd-ref:provider-draft-preview:beta-09",
        "max_approved_usd": 0.01,
        "idempotency_ref": "idempotency:provider-draft-preview:beta-09",
        "expected_receipt_ref": "receipt:provider-draft-preview:beta-09",
        "usage_receipt_ref": "usage-receipt-ref:provider-draft-preview:beta-09",
        "cost_receipt_ref": "cost-receipt-ref:provider-draft-preview:beta-09",
        "redacted_input_summary_ref": (
            "redacted-input-summary-ref:provider-draft-preview:beta-09"
        ),
        "redacted_output_summary_ref": (
            "redacted-output-summary-ref:provider-draft-preview:beta-09"
        ),
        "safe_disable_ref": "safe-disable-ref:provider-draft-preview:beta-09",
        "estimated_input_tokens": 24,
        "estimated_output_tokens": 32,
        "estimated_cost_usd": 0.001,
    }
    values.update(overrides)
    return TinyProviderInvocationRequest(**values)


def _draft_request(**overrides: object) -> ProviderDraftSummarizeRequest:
    values: dict[str, object] = {
        "draft_ref": "provider-draft-ref:beta-09",
        "source_context_ref": "source-context-ref:operator-selected-beta-09",
        "safe_prompt_envelope_ref": "safe-prompt-envelope-ref:beta-09",
        "operator_intent_ref": "operator-intent-ref:summarize-beta-09",
        "purpose": "summarize",
        "tiny_provider_request": _provider_request(),
    }
    values.update(overrides)
    return ProviderDraftSummarizeRequest(**values)


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
            lease_ref="authority-lease-ref:provider-draft-preview-execute-verify",
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
                "Verifier lease grants exact provider model call execution for "
                "provider draft preview checks."
            ),
        )
    )
    return authority


def _credential_resolution(
    request: TinyProviderInvocationRequest,
) -> TinyLiveCredentialResolution:
    return TinyLiveCredentialResolution(
        credential_ref=request.credential_ref,
        secret_ref="secret-ref:provider-draft-preview:fixture",
        vault_record_ref="credential-vault-record-ref:provider-draft-preview:fixture",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        transient_secret=SecretStr("transient-material"),
    )


def _fixture_transport(
    request: TinyProviderInvocationRequest,
    credential: SecretStr,
) -> TinyLiveProviderTransportResult:
    if credential.get_secret_value() != "transient-material":
        raise AssertionError("unexpected transient credential material")
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


def _append_core_failures(failures: list[str]) -> None:
    blocked = evaluate_provider_draft_summarize(_draft_request())
    if blocked.status != "blocked":
        failures.append("default provider draft preview lane is not blocked")
    if blocked.provider_invocation_allowed:
        failures.append("default provider draft preview allows provider invocation")
    if blocked.redacted_draft_preview is not None:
        failures.append("default blocked result includes a draft preview")
    durable = blocked.durable_record()
    if "redacted_draft_preview" in durable:
        failures.append("durable blocked result includes draft preview")
    for field in (
        "durable_draft_preview_persisted",
        "default_control_center_provider_invocation_enabled",
        "default_live_provider_network_enabled",
        "provider_exchange_persistence_allowed",
        "model_output_authoritative",
        "provider_sdk_call_enabled",
        "autonomous_provider_call_enabled",
        "background_execution_enabled",
        "memory_write_performed",
        "context_injection_performed",
        "connector_write_performed",
        "action_execution_performed",
        "production_authority_granted",
    ):
        if getattr(blocked, field):
            failures.append(f"default blocked result enables {field}")

    request = _draft_request()
    provider_request = request.tiny_provider_request
    with TemporaryDirectory() as directory:
        store = TinyProviderInvocationReceiptStore(
            Path(directory) / "provider-draft-preview.jsonl"
        )
        ready = evaluate_provider_draft_summarize(
            request,
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
        if ready.status != "draft_ready":
            failures.append("fixture exact provider draft preview did not become ready")
        if ready.model_output_authoritative:
            failures.append("fixture result claims model output authority")
        if ready.default_control_center_provider_invocation_enabled:
            failures.append("fixture result enables default Control Center invocation")
        if ready.default_live_provider_network_enabled:
            failures.append("fixture result enables default live provider network")
        if ready.durable_draft_preview_persisted:
            failures.append("fixture result persists durable draft preview")
        if ready.provider_exchange_persistence_allowed:
            failures.append("fixture result allows provider exchange persistence")
        if "redacted_draft_preview" in ready.durable_record():
            failures.append("fixture durable record includes transient preview")
        if len(store.list_receipts()) != 1:
            failures.append("fixture exact provider draft preview did not record one receipt")


def _append_cli_failures(failures: list[str]) -> None:
    blocked = subprocess.run(
        [sys.executable, "scripts/inspect_provider_draft_summarize_lane.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    blocked_payload = json.loads(blocked.stdout)
    if blocked_payload.get("status") != "blocked":
        failures.append("CLI default inspection is not blocked")
    if blocked_payload.get("real_provider_network_performed") is not False:
        failures.append("CLI default inspection claims real provider network")

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
    fixture_text = fixture.stdout.lower()
    if fixture_payload.get("status") != "draft_ready":
        failures.append("CLI fixture inspection is not draft_ready")
    if fixture_payload.get("demo_fixture_used") is not True:
        failures.append("CLI fixture inspection does not label demo fixture")
    if fixture_payload.get("real_provider_network_performed") is not False:
        failures.append("CLI fixture inspection claims real provider network")
    durable = fixture_payload.get("durable_record", {})
    if durable.get("durable_draft_preview_persisted") is not False:
        failures.append("CLI fixture durable record persists preview")
    if durable.get("default_control_center_provider_invocation_enabled") is not False:
        failures.append("CLI fixture enables default Control Center invocation")
    if durable.get("default_live_provider_network_enabled") is not False:
        failures.append("CLI fixture enables default live provider network")
    for forbidden in (
        "transient-material",
        "raw prompt content",
        "raw response content",
        "provider payload content",
    ):
        if forbidden in fixture_text:
            failures.append(f"CLI fixture leaked forbidden text: {forbidden}")


def _append_trust_failures(failures: list[str]) -> None:
    matrix = build_trust_authority_matrix_read_model(today_summary={})
    lane = next(
        (
            candidate
            for candidate in matrix["lanes"]
            if candidate["lane_ref"] == "trust-lane:provider-draft-summarize"
        ),
        None,
    )
    if lane is None:
        failures.append("Trust matrix missing provider draft/summarize lane")
        return
    if lane["lane_kind"] != "draft_proposal":
        failures.append("Trust provider draft/summarize lane is not draft_proposal")
    if PROVIDER_DRAFT_SUMMARIZE_PROOF_REF not in lane["proof_refs"]:
        failures.append("Trust lane missing provider draft proof ref")
    if PROVIDER_DRAFT_SUMMARIZE_CLI_REF not in lane["cli_inspection_refs"]:
        failures.append("Trust lane missing provider draft CLI ref")
    if PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF not in lane["safe_disable_refs"]:
        failures.append("Trust lane missing provider draft safe-disable ref")
    if not any("no-provider-model-call" in ref for ref in lane["blocked_authority_refs"]):
        failures.append("Trust lane missing blocked provider/model call ref")


def _append_proof_failures(failures: list[str]) -> None:
    with TemporaryDirectory() as directory:
        service = FounderLoopControlCenterService(
            FounderLoopRepository(Path(directory) / "founder-loop")
        )
        index = service.proof_index()
        if PROVIDER_DRAFT_SUMMARIZE_PROOF_REF not in index["proof_refs"]:
            failures.append("Proof index missing provider draft preview proof ref")
        detail = service.proof_detail(PROVIDER_DRAFT_SUMMARIZE_PROOF_REF)
    record = detail["record"]
    if record["proof_kind"] != "provider_draft_preview":
        failures.append("Provider draft proof has wrong proof kind")
    if "Default Control Center invocation" not in record["authority_posture"]:
        failures.append("Provider draft proof missing default UI invocation block")
    for ref in (
        "blocked-state:provider-draft-summarize:no-default-control-center-invocation",
        "blocked-state:provider-draft-summarize:no-default-live-provider-network",
        "blocked-state:provider-draft-summarize:no-durable-preview-persistence",
    ):
        if ref not in record["blocked_authority_refs"]:
            failures.append(f"Provider draft proof missing blocked ref: {ref}")
    if record["safe_refs_only"] is not True or record["raw_content_included"] is not False:
        failures.append("Provider draft proof is not safe-ref only")


def _append_api_failures(failures: list[str]) -> None:
    paths = {route.path for route in build_api_manifest(app).routes}
    for forbidden_path in (
        "/control-center/providers/draft-summarize",
        "/control-center/providers/draft-preview",
    ):
        if forbidden_path in paths:
            failures.append(f"Unexpected provider draft API route: {forbidden_path}")


def _append_static_failures(failures: list[str]) -> None:
    for path in SOURCE_PATHS:
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_PROVIDER_SDK_FRAGMENTS:
            if fragment in text:
                failures.append(f"{path.relative_to(ROOT)} contains {fragment}")

    doc_text = LANE_DOC.read_text(encoding="utf-8")
    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in doc_text:
            failures.append(f"provider draft lane doc missing fragment: {fragment}")

    for path, fragment in (
        (AUTHORITY_BOARD, "fixture-proven provider draft/summarize core/CLI wrapper"),
        (TRUTH_PACKET, "Provider draft/summarize now has an exact core/CLI wrapper"),
        (CURRENT_BOARD, "Provider Draft/Summarize"),
    ):
        text = path.read_text(encoding="utf-8")
        if fragment not in text:
            failures.append(f"{path.relative_to(ROOT)} missing provider beta-09 fragment")


def main() -> int:
    failures: list[str] = []
    _append_core_failures(failures)
    _append_cli_failures(failures)
    _append_trust_failures(failures)
    _append_proof_failures(failures)
    _append_api_failures(failures)
    _append_static_failures(failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("Beta 09 provider draft preview verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
