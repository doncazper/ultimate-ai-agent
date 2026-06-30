#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center import build_provider_credential_readiness_summary  # noqa: E402


REQUIRED_POSTURES = {
    "configured",
    "not_configured",
    "revoked",
    "blocked",
    "validation_blocked",
    "invocation_blocked",
    "vault_blocked",
    "cost_blocked",
    "unknown_paid_cost_requires_approval",
}
REQUIRED_BINDING_BLOCKERS = {
    "UNKNOWN_PAID_COST_REQUIRES_APPROVAL",
    "PROVIDER_MODEL_REFS_REQUIRED",
    "COST_ESTIMATE_REF_REQUIRED",
    "BUDGET_DECISION_REF_REQUIRED",
    "MAX_APPROVED_USD_REF_REQUIRED",
    "FUTURE_RECEIPT_REFS_REQUIRED",
    "PROVIDER_USAGE_CLAIM_REQUIRES_RECEIPT_REFS",
}
FORBIDDEN_TEXT = (
    "paste key",
    "save key",
    "connect provider",
    "test provider",
    "invoke provider",
    "api_key=",
    "raw prompt",
    "raw response",
    "raw provider payload",
)
REQUIRED_DECLARED_CAPABILITIES = {
    "control_center_provider_credential_readiness_cost_binding_read_only",
    "control_center_provider_credential_readiness_cli_inspection",
}
REQUIRED_BLOCKED_CAPABILITIES = {
    "control_center_provider_credential_readiness_secret_entry",
    "control_center_provider_credential_readiness_provider_validation",
    "control_center_provider_credential_readiness_provider_invocation",
    "control_center_provider_credential_readiness_as_runtime_authority",
    "control_center_provider_cost_binding_as_billing_authority",
    "control_center_provider_cost_binding_without_budget_decision",
    "control_center_provider_cost_binding_without_receipts",
    "control_center_provider_unknown_paid_cost_without_explicit_approval",
}
REQUIRED_DOC_FRAGMENTS = {
    "Provider Credential Readiness + Cost Governor Binding",
    "ProviderCostGovernorBinding",
    "unknown_paid_cost_requires_approval",
    "claim provider usage without future usage and cost receipt refs",
    "no provider SDK calls",
    "no model invocation",
    "no billing authority",
    "no callable runtime authority",
}


def main() -> int:
    failures: list[str] = []
    summary = build_provider_credential_readiness_summary()
    payload = summary.model_dump(mode="json")
    text = str(payload).lower()

    supported_postures = {str(posture) for posture in payload["supported_readiness_postures"]}
    if supported_postures != REQUIRED_POSTURES:
        failures.append("supported provider readiness postures drifted")
    for posture in REQUIRED_POSTURES:
        if posture not in payload["posture_counts"]:
            failures.append(f"posture count missing: {posture}")

    if summary.invocation_enabled or summary.raw_key_collection_enabled:
        failures.append("summary enables invocation or raw key collection")
    if summary.credential_material_stored or summary.vault_adapter_configured:
        failures.append("summary enables credential storage")
    if not summary.provider_runtime_authority_denied or not summary.provider_spend_authority_denied:
        failures.append("summary does not deny provider runtime or spend authority")
    for flag_name in [
        "cost_governor_binding_required",
        "provider_model_refs_required",
        "cost_estimate_ref_required",
        "budget_decision_ref_required",
        "max_approved_usd_ref_required",
        "future_receipt_refs_required",
        "unknown_paid_cost_requires_approval",
        "estimated_cost_above_budget_blocks_use",
        "provider_usage_claim_requires_receipt_refs",
    ]:
        if getattr(summary, flag_name) is not True:
            failures.append(f"summary missing required gate: {flag_name}")

    if not summary.providers:
        failures.append("provider credential readiness has no provider rows")
    for provider in summary.providers:
        binding = provider.cost_governor_binding
        if provider.invocation_enabled or provider.credential_material_stored or provider.raw_key_visible:
            failures.append(f"{provider.provider_id} grants credential or invocation authority")
        if provider.readiness_posture != "not_configured":
            failures.append(f"{provider.provider_id} should remain not_configured in default snapshot")
        if binding.provider_use_authority_granted or binding.model_invocation_enabled:
            failures.append(f"{provider.provider_id} cost binding grants provider use")
        if binding.provider_ref != provider.provider_id:
            failures.append(f"{provider.provider_id} cost binding provider ref does not match provider row")
        if binding.credential_ref != provider.credential_ref:
            failures.append(f"{provider.provider_id} cost binding credential ref does not match provider row")
        if binding.provider_ref_status != "present" or binding.model_ref_status != "missing":
            failures.append(f"{provider.provider_id} provider/model ref posture drifted")
        if not REQUIRED_BINDING_BLOCKERS.issubset(set(binding.blocker_codes)):
            failures.append(f"{provider.provider_id} cost binding missing blocker codes")
        for required_ref in [
            binding.cost_estimate_ref,
            binding.budget_decision_ref,
            binding.max_approved_usd_ref,
            binding.future_receipt_ref,
            binding.usage_receipt_ref,
            binding.cost_receipt_ref,
            binding.cost_governor_posture_ref,
            binding.cost_governor_decision_ref,
        ]:
            if not required_ref or ":" not in required_ref:
                failures.append(f"{provider.provider_id} contains malformed cost binding ref")

    for phrase in FORBIDDEN_TEXT:
        if phrase in text:
            failures.append(f"unsafe credential readiness text found: {phrase}")

    inspect_result = subprocess.run(
        [sys.executable, "scripts/inspect_provider_credential_readiness.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if inspect_result.returncode != 0:
        failures.append("inspect_provider_credential_readiness.py failed")
    if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" not in inspect_result.stdout:
        failures.append("CLI inspection does not include CostGovernor unknown-cost posture")

    manifest = build_api_manifest(app)
    declared = set(manifest.capabilities_declared)
    blocked = set(manifest.capabilities_blocked)
    missing_declared = REQUIRED_DECLARED_CAPABILITIES - declared
    missing_blocked = REQUIRED_BLOCKED_CAPABILITIES - blocked
    if missing_declared:
        failures.append(f"manifest missing declared cost-binding capabilities: {sorted(missing_declared)}")
    if missing_blocked:
        failures.append(f"manifest missing blocked cost-binding capabilities: {sorted(missing_blocked)}")

    doc_path = ROOT / "docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md"
    if not doc_path.exists():
        failures.append("provider credential readiness cost-binding doc is missing")
    else:
        doc_text = doc_path.read_text(encoding="utf-8")
        for fragment in REQUIRED_DOC_FRAGMENTS:
            if fragment not in doc_text:
                failures.append(f"provider credential readiness doc missing fragment: {fragment}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("provider credential cost binding verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
