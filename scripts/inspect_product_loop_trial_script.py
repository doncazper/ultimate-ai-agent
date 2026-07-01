#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from ultimate_ai_agent.core.readiness import build_private_product_loop_trial_script


DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "action_execution_enabled",
    "code_apply_execution_enabled",
    "runtime_authority_added",
    "backend_route_added",
    "telemetry_export_enabled",
    "connector_runtime_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "provider_sdk_call_enabled",
    "live_web_enabled",
    "shell_browser_execution_enabled",
]


def inspect_product_loop_trial_script() -> dict[str, Any]:
    script = build_private_product_loop_trial_script()
    payload = script.model_dump(mode="json")
    denied_flags = {flag: payload[flag] for flag in DENIED_FLAGS}
    return {
        "ok": True,
        "contract_ref": payload["contract_ref"],
        "script_ref": payload["script_ref"],
        "milestone_ref": payload["milestone_ref"],
        "status": payload["status"],
        "surfaces": [step["surface"] for step in payload["manual_steps"]],
        "manual_steps": [
            {
                "step_ref": step["step_ref"],
                "surface": step["surface"],
                "step_state": step["step_state"],
                "evidence_refs": step["evidence_refs"],
                "acceptance_ledger_refs": step["acceptance_ledger_refs"],
            }
            for step in payload["manual_steps"]
        ],
        "acceptance_ledger": [
            {
                "ledger_item_ref": item["ledger_item_ref"],
                "surface": item["surface"],
                "review_state": item["review_state"],
                "acceptance_question_ref": item["acceptance_question_ref"],
                "expected_gap_report_ref": item["expected_gap_report_ref"],
            }
            for item in payload["acceptance_ledger"]
        ],
        "source_trial_refs": payload["source_trial_refs"],
        "final_report_template_refs": payload["final_report_template_refs"],
        "evidence_refs": payload["evidence_refs"],
        "blocked_state_refs": payload["blocked_state_refs"],
        "denied_flags": denied_flags,
        "local_private_only": payload["local_private_only"],
        "safe_refs_only": payload["safe_refs_only"],
        "manual_operator_review_required": payload[
            "manual_operator_review_required"
        ],
        "next_safe_action": payload["next_safe_action"],
    }


def _format_human(payload: dict[str, Any]) -> str:
    lines = [
        "Product Loop 012 Private product loop trial script",
        f"Contract: {payload['contract_ref']}",
        f"Status: {payload['status']}",
        "Scope: local/private, safe-ref-only, manual operator review.",
        "",
        "Manual checklist:",
    ]
    for step in payload["manual_steps"]:
        evidence = ", ".join(step["evidence_refs"])
        ledger = ", ".join(step["acceptance_ledger_refs"])
        lines.append(
            f"- {step['surface']}: {step['step_state']} "
            f"({step['step_ref']}; evidence {evidence}; ledger {ledger})"
        )
    lines.extend(["", "Acceptance ledger:"])
    for item in payload["acceptance_ledger"]:
        lines.append(
            f"- {item['surface']}: {item['review_state']} "
            f"({item['acceptance_question_ref']}; {item['expected_gap_report_ref']})"
        )
    lines.extend(["", "Denied authority:"])
    for flag, enabled in sorted(payload["denied_flags"].items()):
        lines.append(f"- {flag}: {str(enabled).lower()}")
    lines.extend(["", f"Next safe action: {payload['next_safe_action']}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the local/private Product Loop 012 trial script."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()
    payload = inspect_product_loop_trial_script()
    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    else:
        print(_format_human(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
