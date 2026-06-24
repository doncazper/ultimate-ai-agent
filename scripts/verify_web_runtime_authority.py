#!/usr/bin/env python3
"""Verify the contract-first Web Runtime Authority hardening lane.

This verifier is inspection-only. It does not fetch the web, run browser
automation, call providers, execute POST/click/form/download/upload behavior,
or grant callable runtime authority.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.web_access import (  # noqa: E402
    WEB_RUNTIME_CANONICAL_NOUNS,
    WEB_RUNTIME_PROMOTION_STEPS,
    WEB_RUNTIME_REQUIRED_OPERATOR_LABELS,
    WEB_RUNTIME_REQUIRED_SIDE_EFFECTS,
    WebRuntimeAuditRecordContract,
    build_web_runtime_authority_contract,
)

SUCCESS_MESSAGE = "Web Runtime Authority hardening verification passed."
CONTRACT_PATH = Path("src/ultimate_ai_agent/core/web_access/runtime_authority.py")
DOC_PATH = Path("docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md")
TEST_PATH = Path("tests/test_web_runtime_authority_contract.py")
FORBIDDEN_IMPORT_ROOTS = {
    "browserbase",
    "firecrawl",
    "http.client",
    "httpx",
    "playwright",
    "requests",
    "selenium",
    "subprocess",
    "urllib",
    "webbrowser",
}
FORBIDDEN_CALL_ROOTS = {
    "browserbase",
    "firecrawl",
    "httpx",
    "open",
    "playwright",
    "requests",
    "subprocess",
    "urllib",
    "webbrowser",
}
REQUIRED_DOC_FRAGMENTS = (
    "web_request",
    "web_observation",
    "web_evidence",
    "web_approval",
    "web_action_plan",
    "web_audit_record",
    "Durable audit storage comes before provider or browser execution.",
    "Catalog and manifest visibility is metadata-only.",
    "Provider diagnostics are diagnostic-only.",
    "Blocked",
    "Degraded",
    "Partial",
)


def verify() -> list[str]:
    failures: list[str] = []
    _append_file_failures(failures)
    _append_contract_failures(failures)
    _append_static_source_failures(failures)
    _append_doc_failures(failures)
    return failures


def _append_file_failures(failures: list[str]) -> None:
    for path in [CONTRACT_PATH, DOC_PATH, TEST_PATH]:
        if not (ROOT / path).exists():
            failures.append(f"missing Web Runtime Authority file: {path.as_posix()}")


def _append_contract_failures(failures: list[str]) -> None:
    contract = build_web_runtime_authority_contract()
    dumped_contract = contract.model_dump(mode="python")
    if tuple(dumped_contract["canonical_nouns"]) != WEB_RUNTIME_CANONICAL_NOUNS:
        failures.append("canonical web runtime nouns are incomplete")
    if {entry.model_dump(mode="python")["side_effect"] for entry in contract.side_effect_ledger} != set(
        WEB_RUNTIME_REQUIRED_SIDE_EFFECTS
    ):
        failures.append("side-effect ledger is missing POST/click/form/download/upload")
    for entry in contract.side_effect_ledger:
        if entry.execution_allowed is not False or entry.blocked_before_execution is not True:
            failures.append(f"{entry.model_dump(mode='python')['side_effect']} side-effect ledger is not blocked")
    if {state.model_dump(mode="python")["label"] for state in contract.operator_states} != set(
        WEB_RUNTIME_REQUIRED_OPERATOR_LABELS
    ):
        failures.append("operator labels must include blocked/degraded/partial")
    if {step.model_dump(mode="python")["step"] for step in contract.promotion_steps} != set(
        WEB_RUNTIME_PROMOTION_STEPS
    ):
        failures.append("promotion steps are incomplete")
    for step in contract.promotion_steps:
        if not step.verification_lane_ref.startswith("verification-lane:web-runtime-authority:"):
            failures.append(f"{step.model_dump(mode='python')['step']} is missing named verification lane")
    if contract.approval_linkage.execution_authorized is not False:
        failures.append("approval linkage implies execution authority")
    if contract.approval_linkage.exact_scope_validation_required is not True:
        failures.append("approval linkage is missing exact scope validation")
    if contract.catalog_manifest_visibility.callable_runtime is not False:
        failures.append("catalog/manifest visibility implies callable runtime")
    for diagnostic in contract.provider_diagnostics:
        if diagnostic.diagnostic_only is not True:
            failures.append("provider diagnostic is not diagnostic-only")
        if diagnostic.provider_authority_granted is not False:
            failures.append("provider diagnostic grants provider authority")
    try:
        WebRuntimeAuditRecordContract(
            audit_record_ref="web-audit-record-ref:verify",
            web_request_ref="web-request-ref:verify",
            policy_decision_ref="policy-decision-ref:verify",
            scope_ref="scope-ref:web-runtime:verify",
            actor_ref="actor-ref:verify",
            redacted_summary="raw prompt content leaked",
        )
    except ValueError:
        pass
    else:
        failures.append("web audit record accepted raw prompt content")


def _append_static_source_failures(failures: list[str]) -> None:
    path = ROOT / CONTRACT_PATH
    if not path.exists():
        return
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        failures.append(f"{CONTRACT_PATH.as_posix()} cannot parse: {exc}")
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"forbidden runtime import in Web Runtime Authority: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                failures.append(f"forbidden runtime import in Web Runtime Authority: {node.module}")
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            root = call_name.split(".")[0]
            if root in FORBIDDEN_CALL_ROOTS or call_name in FORBIDDEN_CALL_ROOTS:
                failures.append(f"forbidden runtime call in Web Runtime Authority: {call_name}")


def _append_doc_failures(failures: list[str]) -> None:
    path = ROOT / DOC_PATH
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in text:
            failures.append(f"Web Runtime Authority doc missing required fragment: {fragment}")


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def main() -> int:
    failures = verify()
    if failures:
        print("Web Runtime Authority hardening verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
