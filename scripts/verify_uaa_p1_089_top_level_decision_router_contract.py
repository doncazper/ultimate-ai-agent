#!/usr/bin/env python3
"""Verify UAA-P1-089 Top-Level Decision Router Contract.

This verifier is inspection-only. It validates contract files and static
authority boundaries; it does not call models, execute tools, fetch networks,
open browsers, run shell/subprocesses, write connectors, mutate memory, inject
context, execute actions, or run workflows.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ultimate_ai_agent.core.decision_router import (  # noqa: E402
    DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
    DECISION_ROUTER_REQUIRED_OUTCOME_KINDS,
    DecisionRouterCandidate,
    DecisionRouterInput,
    DecisionRouterOutcomeKind,
    route_decision,
)

CONTRACT_DIR = Path("src/ultimate_ai_agent/core/decision_router")
DOC_PATH = Path("docs/control_center/UAA_P1_089_TOP_LEVEL_DECISION_ROUTER_CONTRACT.md")
TEST_PATH = Path("tests/test_uaa_p1_089_top_level_decision_router_contract.py")
EXPECTED_OUTCOMES = {
    "answer_directly",
    "use_reviewed_memory",
    "propose_action_inbox_item",
    "ask_human",
    "escalate_to_review",
    "defer",
    "blocked_unsafe",
    "insufficient_evidence",
}
FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "boto3",
    "httpx",
    "openai",
    "playwright",
    "requests",
    "selenium",
    "socket",
    "subprocess",
    "urllib",
    "webbrowser",
}
FORBIDDEN_CALL_ROOTS = {
    "eval",
    "exec",
    "openai",
    "os.system",
    "requests",
    "subprocess",
}
FORBIDDEN_AUTHORITY_CALL_NAMES = {
    "evaluate_request",
    "execute",
    "grant",
    "create_request",
    "validate_for_request",
    "request_for_model_route",
    "request_for_tool_request",
    "write",
}
FORBIDDEN_DOC_CLAIMS = (
    "production ready",
    "production-ready",
    "public beta enabled",
    "grants autonomous routing authority",
    "adds autonomous routing authority",
    "authorizes routes",
    "executes routes",
    "dispatches tools",
)


def _code_ref_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _code_ref_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _python_files() -> list[Path]:
    return sorted((ROOT / CONTRACT_DIR).glob("*.py"))


def _validate_files_exist() -> list[str]:
    failures: list[str] = []
    required = [
        CONTRACT_DIR / "__init__.py",
        CONTRACT_DIR / "contracts.py",
        DOC_PATH,
        TEST_PATH,
    ]
    for rel_path in required:
        if not (ROOT / rel_path).exists():
            failures.append(f"missing required UAA-P1-089 file: {rel_path.as_posix()}")
    return failures


def _validate_outcomes_and_blockers() -> list[str]:
    failures: list[str] = []
    if set(DECISION_ROUTER_REQUIRED_OUTCOME_KINDS) != EXPECTED_OUTCOMES:
        failures.append("decision router outcome kinds do not match required outcomes")
    if len(DECISION_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS) < 10:
        failures.append("decision router must carry blocked authority refs for every denied authority class")
    candidate = DecisionRouterCandidate(
        candidate_ref="decision-router-candidate:verify",
        outcome_kind=DecisionRouterOutcomeKind.answer_directly,
        safe_summary="Safe route outcome proposal.",
        safe_reason_refs=["reason-ref:decision-router:verify"],
        evidence_refs=["evidence:decision-router:verify"],
        source_refs=["source:decision-router:verify"],
        confidence=0.9,
        next_safe_operator_action="Review the proposed route outcome.",
    )
    outcome = route_decision(
        DecisionRouterInput(
            router_input_ref="decision-router-input:verify",
            safe_request_summary="Reviewed safe request summary.",
            source_refs=["source:decision-router:verify"],
            evidence_refs=["evidence:decision-router:verify"],
            candidates=[candidate],
        )
    )
    if outcome.route_authority_granted is not False:
        failures.append("decision router outcome granted route authority")
    if outcome.execution_performed is not False:
        failures.append("decision router outcome performed execution")
    no_effect_flags = (
        "no_model_call_performed",
        "no_provider_call_performed",
        "no_tool_execution_performed",
        "no_action_execution_performed",
        "no_workflow_execution_performed",
        "no_memory_write_performed",
        "no_context_injection_performed",
        "no_shell_subprocess_performed",
        "no_browser_network_performed",
        "no_connector_write_performed",
    )
    for field_name in no_effect_flags:
        if getattr(outcome, field_name) is not True:
            failures.append(f"decision router outcome failed no-effect flag: {field_name}")
    blocked = route_decision(
        DecisionRouterInput(
            router_input_ref="decision-router-input:blocked",
            safe_request_summary="Reviewed safe request summary.",
            source_refs=["source:decision-router:blocked"],
            evidence_refs=["evidence:decision-router:blocked"],
            candidates=[
                DecisionRouterCandidate(
                    candidate_ref="decision-router-candidate:blocked",
                    outcome_kind=DecisionRouterOutcomeKind.blocked_unsafe,
                    safe_summary="Unsafe route outcome proposal.",
                    safe_reason_refs=["reason-ref:decision-router:blocked"],
                    evidence_refs=["evidence:decision-router:blocked"],
                    source_refs=["source:decision-router:blocked"],
                    confidence=0.1,
                    next_safe_operator_action="Keep the route blocked.",
                )
            ],
        )
    )
    if not blocked.blocked_states:
        failures.append("blocked_unsafe outcome must include blocked states")
    empty = route_decision(
        DecisionRouterInput(
            router_input_ref="decision-router-input:empty",
            safe_request_summary="Reviewed safe request summary.",
            source_refs=["source:decision-router:empty"],
            evidence_refs=["evidence:decision-router:empty"],
        )
    )
    if empty.outcome_kind != "insufficient_evidence" or not empty.blocked_states:
        failures.append("empty candidate set must produce insufficient_evidence with blocked states")
    return failures


def _validate_static_authority() -> list[str]:
    failures: list[str] = []
    for path in _python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT).as_posix()}: cannot parse Python source: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name in FORBIDDEN_IMPORT_ROOTS:
                        failures.append(f"{path.relative_to(ROOT).as_posix()}: forbidden runtime import: {name}")
            if isinstance(node, ast.Call):
                call_name = _code_ref_name(node.func)
                call_root = call_name.split(".")[0]
                call_attr = call_name.rsplit(".", 1)[-1]
                if call_name in FORBIDDEN_CALL_ROOTS or call_root in FORBIDDEN_CALL_ROOTS:
                    failures.append(f"{path.relative_to(ROOT).as_posix()}: forbidden runtime call: {call_name}")
                if call_attr in FORBIDDEN_AUTHORITY_CALL_NAMES:
                    failures.append(f"{path.relative_to(ROOT).as_posix()}: forbidden authority call: {call_name}")
    app_path = ROOT / "src/ultimate_ai_agent/api/app.py"
    if app_path.exists() and "decision-router" in app_path.read_text(encoding="utf-8").lower():
        failures.append("UAA-P1-089 must not add a FastAPI decision-router route")
    return failures


def _validate_doc() -> list[str]:
    failures: list[str] = []
    if not (ROOT / DOC_PATH).exists():
        return [f"missing UAA-P1-089 doc: {DOC_PATH.as_posix()}"]
    text = (ROOT / DOC_PATH).read_text(encoding="utf-8")
    required_fragments = (
        "UAA-P1-089 Top-Level Decision Router Contract",
        "DecisionRouterInput",
        "DecisionRouterCandidate",
        "DecisionRouterOutcome",
        "DecisionRouterTrace",
        "DecisionRouterBlockedState",
        "answer_directly",
        "use_reviewed_memory",
        "propose_action_inbox_item",
        "ask_human",
        "escalate_to_review",
        "defer",
        "blocked_unsafe",
        "insufficient_evidence",
        "route_authority_granted=false",
        "execution_performed=false",
        "no_memory_write_performed=true",
        "no_context_injection_performed=true",
        "does not add",
    )
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(f"UAA-P1-089 doc missing required fragment: {fragment}")
    lowered = text.lower()
    for claim in FORBIDDEN_DOC_CLAIMS:
        if claim in lowered:
            failures.append(f"UAA-P1-089 doc contains forbidden product/authority claim: {claim}")
    return failures


def verify() -> list[str]:
    failures: list[str] = []
    failures.extend(_validate_files_exist())
    failures.extend(_validate_outcomes_and_blockers())
    failures.extend(_validate_static_authority())
    failures.extend(_validate_doc())
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify UAA-P1-089 Top-Level Decision Router Contract.")
    parser.parse_args(argv)
    failures = verify()
    if failures:
        print("FAIL: UAA-P1-089 Top-Level Decision Router Contract verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: UAA-P1-089 Top-Level Decision Router Contract is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
