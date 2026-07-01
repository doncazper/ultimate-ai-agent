#!/usr/bin/env python3
"""Verify UAA-P1-090 Task Decomposition Proposal Engine.

This verifier is inspection-only. It proves the task-decomposition proposal
lane remains deterministic and review-only; it does not call models, execute
tools, fetch networks, open browsers, run shell/subprocesses, write connectors,
mutate memory, inject context, execute actions, or run workflows.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ultimate_ai_agent.core.task_decomposition.proposals import (  # noqa: E402
    TASK_DECOMPOSITION_ACTION_KIND,
    TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF,
    TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS,
    TaskDecompositionBlockedState,
    TaskDecompositionProposal,
    TaskDecompositionRequest,
    TaskDecompositionReviewEnvelope,
    TaskDecompositionRisk,
    TaskDecompositionStep,
    build_task_decomposition_review_envelope,
    task_decomposition_action_items,
    task_decomposition_read_model_for_plan,
)

PROPOSAL_PATH = Path("src/ultimate_ai_agent/core/task_decomposition/proposals.py")
DOC_PATH = Path("docs/control_center/UAA_P1_090_TASK_DECOMPOSITION_PROPOSAL_ENGINE.md")
TEST_PATH = Path("tests/test_uaa_p1_090_task_decomposition_proposal_engine.py")
REQUIRED_MODEL_NAMES = {
    "TaskDecompositionRequest",
    "TaskDecompositionProposal",
    "TaskDecompositionStep",
    "TaskDecompositionRisk",
    "TaskDecompositionReviewEnvelope",
    "TaskDecompositionBlockedState",
}
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "anthropic",
    "boto3",
    "cohere",
    "google",
    "http",
    "httpx",
    "importlib",
    "litellm",
    "mistralai",
    "ollama",
    "openai",
    "pexpect",
    "playwright",
    "pty",
    "requests",
    "selenium",
    "socket",
    "subprocess",
    "urllib",
    "urllib3",
    "webbrowser",
}
FORBIDDEN_MODULE_FRAGMENTS = {
    "ultimate_ai_agent.core.task_decomposition.executor",
    "ultimate_ai_agent.core.task_decomposition.runtime",
    "ultimate_ai_agent.core.web_access",
}
FORBIDDEN_CALL_NAMES = {
    "DAGExecutor",
    "TaskDecompositionService",
    "TaskDecompositionRunRequest",
    "TaskPlanExecutionRequest",
    "create_request",
    "eval",
    "exec",
    "execute",
    "execute_plan",
    "execute_plan_sync",
    "grant",
    "import_module",
    "open_url",
    "request",
    "run",
    "run_sync",
    "schedule",
    "spawn",
    "start",
    "write",
}
FORBIDDEN_DOC_CLAIMS = (
    "production ready",
    "production-ready",
    "public beta enabled",
    "grants execution authority",
    "grants planning authority",
    "executes tasks",
    "executes workflows",
    "dispatches tools",
    "writes memory",
    "injects context",
)


def _code_ref_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _code_ref_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _validate_files_exist() -> list[str]:
    failures: list[str] = []
    for rel_path in (PROPOSAL_PATH, DOC_PATH, TEST_PATH):
        if not (ROOT / rel_path).exists():
            failures.append(f"missing required UAA-P1-090 file: {rel_path.as_posix()}")
    return failures


def _validate_contract_shape() -> list[str]:
    failures: list[str] = []
    model_names = {
        TaskDecompositionRequest.__name__,
        TaskDecompositionProposal.__name__,
        TaskDecompositionStep.__name__,
        TaskDecompositionRisk.__name__,
        TaskDecompositionReviewEnvelope.__name__,
        TaskDecompositionBlockedState.__name__,
    }
    if model_names != REQUIRED_MODEL_NAMES:
        failures.append("task decomposition proposal models do not match required names")
    if TASK_DECOMPOSITION_ACTION_KIND != "task_decomposition_proposal":
        failures.append("task decomposition Action Inbox kind changed")
    if len(TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS) < 10:
        failures.append("task decomposition proposal must enumerate blocked authority refs")

    envelope = build_task_decomposition_review_envelope(
        TaskDecompositionRequest(
            request_ref="task-decomposition-request:verify",
            original_request_ref="operator-request:verify",
            original_request_safe_summary=(
                "Implement a review-only proposal from bounded safe refs."
            ),
            source_refs=["source-ref:verify"],
            evidence_refs=["evidence-ref:verify"],
            missing_evidence_refs=["missing-evidence-ref:verify"],
        )
    )
    proposal = envelope.proposals[0]
    if proposal.contract_ref != TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF:
        failures.append("proposal contract ref mismatch")
    if not proposal.proposed_steps:
        failures.append("proposal must include proposed steps")
    if not proposal.dependencies:
        failures.append("proposal must include dependency refs")
    if not proposal.suggested_action_inbox_proposal_refs:
        failures.append("proposal must include suggested Action Inbox proposal refs")
    if not proposal.required_approvals:
        failures.append("proposal must include required approvals")
    if not proposal.blocked_states:
        failures.append("proposal must include blocked states")
    if envelope.decision_receipt_only is not True:
        failures.append("review envelope decisions must be receipt-only")
    if envelope.separate_approval_required is not True:
        failures.append("review envelope must require separate approval")
    for model, owner in ((proposal, "proposal"), (envelope, "review envelope")):
        for field_name in (
            "runtime_authority_granted",
            "autonomous_planning_authority",
            "execution_authorized",
            "execution_performed",
            "task_execution_enabled",
            "workflow_execution_enabled",
            "action_execution_enabled",
            "tool_execution_enabled",
            "memory_write_authorized",
            "context_injection_authorized",
            "connector_write_enabled",
            "shell_subprocess_execution_enabled",
            "browser_network_enabled",
            "model_provider_authority_allowed",
            "production_authority_enabled",
        ):
            if getattr(model, field_name) is not False:
                failures.append(f"{owner} enabled denied authority: {field_name}")
        for field_name in (
            "review_only",
            "proposal_only",
            "safe_refs_only",
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
        ):
            if getattr(model, field_name) is not True:
                failures.append(f"{owner} failed no-effect proof flag: {field_name}")

    action_items = task_decomposition_action_items(envelope)
    if not action_items:
        failures.append("task decomposition proposal must project Action Inbox items")
    for item in action_items:
        if item.get("approval_required") is not False:
            failures.append("Action Inbox projection must not require approval authority")
        if item.get("state_change_contract_ref") is not None:
            failures.append("Action Inbox projection must not expose state change contract")
        if item.get("task_decomposition_execution_authorized") is not False:
            failures.append("Action Inbox projection authorized execution")
        if item.get("task_decomposition_memory_write_authorized") is not False:
            failures.append("Action Inbox projection authorized memory writes")

    read_model = task_decomposition_read_model_for_plan(
        "plan-summary:verify",
        title="Verify plan",
        safe_summary="Build review-only task proposal refs.",
        evidence_refs=["evidence-ref:verify-plan"],
    )
    if read_model.get("task_decomposition_execution_authorized") is not False:
        failures.append("plan read model authorized execution")
    if not read_model.get("task_decomposition_steps"):
        failures.append("plan read model must include bounded step display")
    return failures


def _validate_static_authority() -> list[str]:
    failures: list[str] = []
    path = ROOT / PROPOSAL_PATH
    if not path.exists():
        return [f"missing proposal module: {PROPOSAL_PATH.as_posix()}"]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{PROPOSAL_PATH.as_posix()}: cannot parse Python source: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif node.module:
                modules = [node.module]
            for module in modules:
                root = module.split(".")[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(
                        f"{PROPOSAL_PATH.as_posix()}: forbidden runtime import: {module}"
                    )
                if module in FORBIDDEN_MODULE_FRAGMENTS:
                    failures.append(
                        f"{PROPOSAL_PATH.as_posix()}: forbidden execution module import: {module}"
                    )
        if isinstance(node, ast.Call):
            call_name = _code_ref_name(node.func)
            call_attr = call_name.rsplit(".", 1)[-1]
            if call_attr in FORBIDDEN_CALL_NAMES:
                failures.append(
                    f"{PROPOSAL_PATH.as_posix()}: forbidden authority/runtime call: {call_name}"
                )

    app_path = ROOT / "src/ultimate_ai_agent/api/app.py"
    if app_path.exists() and "task-decomposition/proposal" in app_path.read_text(
        encoding="utf-8"
    ).lower():
        failures.append("UAA-P1-090 must not add a FastAPI proposal execution route")
    return failures


def _validate_doc() -> list[str]:
    failures: list[str] = []
    path = ROOT / DOC_PATH
    if not path.exists():
        return [f"missing UAA-P1-090 doc: {DOC_PATH.as_posix()}"]
    text = path.read_text(encoding="utf-8")
    required_fragments = (
        "UAA-P1-090 Task Decomposition Proposal Engine",
        "TaskDecompositionRequest",
        "TaskDecompositionProposal",
        "TaskDecompositionStep",
        "TaskDecompositionRisk",
        "TaskDecompositionReviewEnvelope",
        "TaskDecompositionBlockedState",
        "proposal-only",
        "review-only",
        "no runtime model calls",
        "no provider calls",
        "no tool execution",
        "no action execution",
        "no workflow execution",
        "no memory writes",
        "no context injection",
        "no shell/subprocess execution",
        "no browser/network access",
        "no connector writes",
        "no production authority",
    )
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(f"UAA-P1-090 doc missing required fragment: {fragment}")
    lowered = text.lower()
    for claim in FORBIDDEN_DOC_CLAIMS:
        if claim in lowered:
            failures.append(f"UAA-P1-090 doc contains forbidden claim: {claim}")
    return failures


def verify() -> list[str]:
    failures: list[str] = []
    failures.extend(_validate_files_exist())
    failures.extend(_validate_contract_shape())
    failures.extend(_validate_static_authority())
    failures.extend(_validate_doc())
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify UAA-P1-090 Task Decomposition Proposal Engine."
    )
    parser.parse_args()
    failures = verify()
    if failures:
        print("UAA-P1-090 verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("UAA-P1-090 verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
