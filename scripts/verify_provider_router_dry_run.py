#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "src/ultimate_ai_agent/core/providers/router_dry_run.py"
API_PATH = ROOT / "src/ultimate_ai_agent/api/provider_setup.py"
CLI_PATH = ROOT / "scripts/inspect_provider_router_dry_run.py"
PANEL_PATH = ROOT / "apps/control-center/src/components/OperatorFlowPanels.tsx"
TYPES_PATH = ROOT / "apps/control-center/src/api/types.ts"
CLIENT_PATH = ROOT / "apps/control-center/src/api/client.ts"


def main() -> int:
    failures: list[str] = []
    for path in [CORE_PATH, API_PATH, CLI_PATH, PANEL_PATH, TYPES_PATH, CLIENT_PATH]:
        if not path.exists():
            failures.append(f"missing provider router dry-run artifact: {path}")

    if not failures:
        failures.extend(_core_failures(CORE_PATH.read_text(encoding="utf-8")))
        failures.extend(_api_failures(API_PATH.read_text(encoding="utf-8")))
        failures.extend(_frontend_failures())
        failures.extend(_cli_failures())

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Provider router dry-run verifier passed.")
    return 0


def _core_failures(text: str) -> list[str]:
    failures: list[str] = []
    required_fragments = [
        "ProviderRouterDryRunRequest",
        "ProviderRouterDryRunProposal",
        "ProviderRouterDryRunProviderProposal",
        "evaluate_provider_router_dry_run",
        "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY",
        "NO_PROVIDER_INVOCATION",
        "NO_FALLBACK_EXECUTION",
        "NO_NETWORK_CALLS",
        "NO_PROVIDER_SDK_CALL",
        "NO_CREDENTIAL_VALIDATION",
        "NO_MODEL_CALL",
        "NO_BILLING_AUTHORITY",
        "NO_AUTONOMOUS_BACKGROUND_CALLS",
        "COSTGOVERNOR_REQUIRED_BEFORE_INVOCATION",
        "UNKNOWN_PAID_COST_BLOCKS",
        "EXACT_APPROVAL_SCOPE_REQUIRED_FOR_ANY_FUTURE_USE",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(f"core provider router dry-run missing fragment: {fragment}")
    forbidden_imports = [
        "import requests",
        "import httpx",
        "import urllib",
        "from urllib",
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "google.generativeai",
        "subprocess",
    ]
    lowered = text.lower()
    for forbidden in forbidden_imports:
        if forbidden in lowered:
            failures.append(f"core provider router dry-run has forbidden import: {forbidden}")
    forbidden_authority_snippets = [
        "invocation_authorized: bool = true",
        "fallback_execution_authorized: bool = true",
        "network_call_performed: bool = true",
        "provider_sdk_call_performed: bool = true",
        "credential_validation_performed: bool = true",
        "model_invocation_performed: bool = true",
        "billing_authority_granted: bool = true",
        "autonomous_background_execution_enabled: bool = true",
    ]
    for snippet in forbidden_authority_snippets:
        if snippet in lowered:
            failures.append(f"core provider router dry-run enables authority: {snippet}")
    return failures


def _api_failures(text: str) -> list[str]:
    failures: list[str] = []
    for fragment in [
        '"/router/dry-run"',
        "control_center_providers_router_dry_run",
        "evaluate_provider_router_dry_run",
        "provider_router_safe_refs_only",
        "raw_prompt_response_provider_payload_omitted",
        '"billing_authority_granted": False',
        '"unknown_paid_cost_blocks": True',
    ]:
        if fragment not in text:
            failures.append(f"provider router dry-run API missing fragment: {fragment}")
    return failures


def _frontend_failures() -> list[str]:
    failures: list[str] = []
    panel_text = PANEL_PATH.read_text(encoding="utf-8")
    types_text = TYPES_PATH.read_text(encoding="utf-8")
    client_text = CLIENT_PATH.read_text(encoding="utf-8")
    for fragment in [
        "Provider router dry-run",
        "Router no-authority refs",
        "Exact-approval candidate refs",
        "Blocked provider refs",
        "Degraded provider refs",
        "No fallback execution",
        "Billing authority",
    ]:
        if fragment not in panel_text:
            failures.append(f"provider router dry-run UI missing fragment: {fragment}")
    for fragment in [
        "ProviderRouterDryRunReadiness",
        "ProviderRouterDryRunProviderProposal",
        "recommended_exact_approval_scope",
        "degraded_provider_refs",
        "fallback_execution_authorized",
        "provider_sdk_call_performed",
        "billing_authority_granted",
    ]:
        if fragment not in types_text:
            failures.append(f"provider router dry-run types missing fragment: {fragment}")
    for fragment in [
        "isSafeProviderRouterDryRunReadiness",
        "isSafeProviderRouterDryRunProviderProposal",
        "isSafeProviderRouterDryRunRecommendedScope",
        "NO_PROVIDER_INVOCATION",
        "NO_FALLBACK_EXECUTION",
        "NO_PROVIDER_SDK_CALL",
        "NO_CREDENTIAL_VALIDATION",
        "NO_MODEL_CALL",
        "NO_BILLING_AUTHORITY",
    ]:
        if fragment not in client_text:
            failures.append(f"provider router dry-run client check missing fragment: {fragment}")
    for unsafe in [
        "connect provider",
        "provider call button",
        "credential input",
        "api key input",
        "router ready",
        "callable router",
        "fallback candidate",
        "provider enabled",
        "validation available",
    ]:
        if unsafe in panel_text.lower():
            failures.append(f"provider router dry-run UI contains unsafe wording: {unsafe}")
    return failures


def _cli_failures() -> list[str]:
    failures: list[str] = []
    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "--router-run-ref",
            "provider-router-run-ref:dry-run:verifier",
            "--idempotency-ref",
            "idempotency-ref:provider-router:dry-run:verifier",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"provider router dry-run CLI failed: {result.stderr.strip()}"]
    data = json.loads(result.stdout)
    for field in [
        "invocation_authorized",
        "fallback_execution_authorized",
        "provider_sdk_call_performed",
        "credential_validation_performed",
        "model_invocation_performed",
        "billing_authority_granted",
        "autonomous_background_execution_enabled",
    ]:
        if data.get(field) is not False:
            failures.append(f"provider router dry-run CLI field must be false: {field}")
    if data.get("proposal_only") is not True:
        failures.append("provider router dry-run CLI must remain proposal_only")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
