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
    WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER,
    WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER_STATUSES,
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
ROADMAP_PATH = Path("docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md")
BOARD_PATH = Path("docs/kanban/current_board.md")
PROVIDER_SEQUENCE_PATH = Path("docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md")
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
FORBIDDEN_PUBLIC_WEB_IMPORTS = {
    "apify",
    "apify_client",
    "browserbase",
    "bs4",
    "ddgs",
    "duckduckgo_search",
    "exa",
    "exa_py",
    "firecrawl",
    "http.client",
    "httpx",
    "newspaper",
    "newspaper3k",
    "playwright",
    "requests",
    "scrapy",
    "selenium",
    "serpapi",
    "tavily",
    "tavily_client",
    "trafilatura",
    "urllib.request",
    "urllib3",
}
APPROVED_PUBLIC_WEB_IMPORT_FILES = {
    "src/ultimate_ai_agent/core/web_access/adapters.py",
    "src/ultimate_ai_agent/core/local_model_management/gateway.py",
    "src/ultimate_ai_agent/core/local_model_management/hf_search.py",
    "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py",
    "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
    "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
    "src/ultimate_ai_agent/core/network/governed_web_evidence.py",
    "src/ultimate_ai_agent/core/providers/live_invocation_adapter.py",
    "scripts/dev/uaa_launcher.py",
    "scripts/dev/uaa_setup.py",
    "scripts/run_local_runtime_packaging_proof.py",
}
SCAN_ROOTS = (Path("src"), Path("scripts"))
IGNORED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
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
    "Web Runtime Authority Promotion Ladder",
    "Roadmap/currentness stitching",
    "Governed read-only fetch",
    "Provider shells and diagnostics",
    "Read-only provider adapter",
    "Browser observe",
    "Browser action dry-run",
    "Low-risk click execution",
    "Connector-specific writes",
    "Callable runtime authority",
    "CostGovernor",
    "frontier paid usage without cost receipts",
)
REQUIRED_ROADMAP_FRAGMENTS = (
    "Web Runtime Authority Promotion Ladder",
    "WEB-HYBRID-001",
    "WEB-HYBRID-008",
    "WebAccessGateway",
    "request-scoped",
    "Unrestricted web fetching",
    "paid use",
)
REQUIRED_BOARD_FRAGMENTS = (
    "Web Runtime Authority Promotion Ladder",
    "P1 implementation lane",
    "runtime authority WIP limit at one lane",
    "WEB-HYBRID-001",
    "WEB-HYBRID-008",
    "Unrestricted web fetching",
    "browser automation",
    "paid use",
)


def verify() -> list[str]:
    failures: list[str] = []
    _append_file_failures(failures)
    _append_contract_failures(failures)
    _append_static_source_failures(failures)
    _append_public_web_bypass_failures(failures)
    _append_doc_failures(failures)
    return failures


def _append_file_failures(failures: list[str]) -> None:
    for path in [CONTRACT_PATH, DOC_PATH, TEST_PATH, ROADMAP_PATH, BOARD_PATH]:
        if not (ROOT / path).exists():
            failures.append(f"missing Web Runtime Authority file: {path.as_posix()}")


def _append_contract_failures(failures: list[str]) -> None:
    contract = build_web_runtime_authority_contract()
    dumped_contract = contract.model_dump(mode="python")
    if contract.scope_posture != "broad_unrestricted_ladder_only":
        failures.append("web runtime ladder is not scoped to broad authority")
    if contract.exact_lanes_do_not_promote_broad_authority is not True:
        failures.append("exact web lanes promote broad runtime authority")
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
    ladder_steps = tuple(
        step.model_dump(mode="python")["step"] for step in contract.promotion_ladder
    )
    if ladder_steps != WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER:
        failures.append("web runtime authority promotion ladder is incomplete or unordered")
    ladder_statuses = tuple(
        step.model_dump(mode="python")["status"] for step in contract.promotion_ladder
    )
    if ladder_statuses != WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER_STATUSES:
        failures.append("web runtime authority promotion ladder statuses drifted")
    for index, ladder_step in enumerate(contract.promotion_ladder, start=1):
        if ladder_step.sequence != index:
            failures.append(f"{ladder_step.step} ladder sequence drifted")
        if ladder_step.runtime_authority_granted is not False:
            failures.append(f"{ladder_step.step} grants runtime authority")
        if ladder_step.live_web_fetching_allowed is not False:
            failures.append(f"{ladder_step.step} allows live web fetching")
        if ladder_step.browser_automation_allowed is not False:
            failures.append(f"{ladder_step.step} allows browser automation")
        if ladder_step.provider_sdk_call_allowed is not False:
            failures.append(f"{ladder_step.step} allows provider SDK calls")
        if ladder_step.generic_public_web_mutation_allowed is not False:
            failures.append(f"{ladder_step.step} allows generic public-web mutation")
        if ladder_step.callable_runtime_authority is not False:
            failures.append(f"{ladder_step.step} grants callable runtime authority")
    cost_posture = contract.cost_governor_posture
    if cost_posture.cost_governor_required_before_paid_provider_use is not True:
        failures.append("paid/frontier provider use is not CostGovernor-bound")
    if cost_posture.unknown_paid_cost_requires_explicit_approval is not True:
        failures.append("unknown paid/frontier cost is not approval-bound")
    if cost_posture.cost_receipt_refs_required_for_frontier_usage_claims is not True:
        failures.append("frontier usage claims do not require cost receipt refs")
    if cost_posture.provider_model_refs_required_before_frontier_usage is not True:
        failures.append("frontier usage does not require provider/model refs")
    if cost_posture.provider_sdk_calls_allowed is not False:
        failures.append("cost posture allows provider SDK calls")
    if cost_posture.callable_runtime_authority is not False:
        failures.append("cost posture grants callable runtime authority")
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


def _append_public_web_bypass_failures(failures: list[str]) -> None:
    for root in SCAN_ROOTS:
        scan_root = ROOT / root
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*.py"):
            if any(part in IGNORED_DIR_NAMES for part in path.parts):
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in APPROVED_PUBLIC_WEB_IMPORT_FILES:
                continue
            for imported in sorted(_direct_imports(path)):
                if _is_public_web_import(imported):
                    failures.append(
                        "public web/provider import bypasses WebAccessGateway: "
                        f"{rel}: {imported}"
                    )


def _append_doc_failures(failures: list[str]) -> None:
    path = ROOT / DOC_PATH
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for fragment in REQUIRED_DOC_FRAGMENTS:
        if not _contains_fragment(text, fragment):
            failures.append(f"Web Runtime Authority doc missing required fragment: {fragment}")
    for path, fragments, label in [
        (ROOT / ROADMAP_PATH, REQUIRED_ROADMAP_FRAGMENTS, "roadmap"),
        (ROOT / BOARD_PATH, REQUIRED_BOARD_FRAGMENTS, "board"),
        (
            ROOT / PROVIDER_SEQUENCE_PATH,
            ("Add providers earlier. Add dangerous authority much later.",),
            "provider sequence",
        ),
    ]:
        if not path.exists():
            failures.append(f"missing {label} document for Web Runtime Authority")
            continue
        doc_text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if not _contains_fragment(doc_text, fragment):
                failures.append(f"Web Runtime Authority {label} missing required fragment: {fragment}")


def _direct_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            imports.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imports


def _is_public_web_import(module: str) -> bool:
    return any(
        module == banned or module.startswith(f"{banned}.")
        for banned in FORBIDDEN_PUBLIC_WEB_IMPORTS
    )


def _contains_fragment(text: str, fragment: str) -> bool:
    return fragment in text or " ".join(fragment.split()) in " ".join(text.split())


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
