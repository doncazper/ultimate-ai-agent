#!/usr/bin/env python3
"""Verify the UAA GoatCitadel runtime turn/run/approval chain slice."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "runtime" / "UAA_GOATCITADEL_RUNTIME_TURN_RUN_APPROVAL_CHAIN.md"
CORE_PATH = ROOT / "src" / "ultimate_ai_agent" / "core" / "execution" / "turn_run_approval_chain.py"
CLI_PATH = ROOT / "scripts" / "dev" / "uaa_runtime.py"
TEST_PATH = ROOT / "tests" / "test_turn_run_approval_chain.py"

REQUIRED_STATES = (
    "created",
    "routed",
    "planning",
    "waiting_for_approval",
    "approved",
    "running",
    "retry_scheduled",
    "paused",
    "resumed",
    "cancelled",
    "failed",
    "blocked",
    "completed",
)

REQUIRED_CORE_STRINGS = (
    "class TurnRef",
    "class DurableRunRef",
    "class ApprovalRef",
    "class CheckpointRef",
    "class ReceiptRef",
    "class RouteDecisionBindingRef",
    "class TurnRunApprovalChainReadModel",
    "class TurnRunApprovalTransitionRequest",
    "apply_turn_run_approval_transition",
    "reason-ref:turn-run-chain:approval-run-scope-mismatch",
    "reason-ref:turn-run-chain:idempotency-conflict",
)

REQUIRED_DOC_STRINGS = (
    "# UAA GoatCitadel Runtime Turn Run Approval Chain",
    "does not copy GoatCitadel code",
    "does not add runtime authority",
    "Approval refs remain identifiers only",
    "Control Center cannot mint authority",
    "runtime model calls",
    "provider SDK calls",
    "browser automation",
    "connector writes",
    "unrestricted shell/subprocess execution",
    "production authority",
    "broad autonomy",
)

REQUIRED_TEST_STRINGS = (
    "test_turn_run_approval_chain_requires_turn_or_operator_task_ref",
    "test_sample_turn_run_approval_chain_is_waiting_for_approval",
    "test_approval_scope_mismatch_cannot_approve_changed_run",
    "test_retry_resume_and_cancel_states_are_inspectable",
    "test_transition_replay_is_idempotent_and_conflict_is_denied",
    "test_transition_execution_and_raw_payload_flags_are_denied",
    "test_runtime_cli_inspects_turn_run_approval_chain_safe_json",
)

FORBIDDEN_STRINGS = (
    "runtime model calls are enabled",
    "provider SDK calls are enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "unrestricted shell/subprocess execution is enabled",
    "production authority is enabled",
    "broad autonomy is enabled",
)

ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s`)]+"),
    re.compile(r"/home/[^\s`)]+"),
    re.compile(r"/var/[^\s`)]+"),
    re.compile(r"/etc/[^\s`)]+"),
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _missing(text: str, required: tuple[str, ...], label: str) -> list[str]:
    return [f"missing {label}: {item}" for item in required if item not in text]


def verify() -> list[str]:
    doc_text = _read(DOC_PATH)
    core_text = _read(CORE_PATH)
    cli_text = _read(CLI_PATH)
    test_text = _read(TEST_PATH)
    combined = "\n".join((doc_text, core_text, cli_text, test_text))
    lowered = combined.lower()
    failures: list[str] = []

    failures.extend(_missing(doc_text, REQUIRED_DOC_STRINGS, "doc string"))
    failures.extend(_missing(core_text, REQUIRED_CORE_STRINGS, "core string"))
    failures.extend(_missing(test_text, REQUIRED_TEST_STRINGS, "test coverage"))
    failures.extend(_missing(combined, REQUIRED_STATES, "canonical state"))
    if "inspect-turn-run-approval-chain" not in cli_text:
        failures.append("CLI inspection command is missing")
    for forbidden in FORBIDDEN_STRINGS:
        if forbidden.lower() in lowered:
            failures.append(f"forbidden overclaim present: {forbidden}")
    for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS:
        if pattern.search(combined):
            failures.append("turn/run/approval chain artifacts contain an absolute local path")
            break
    return failures


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    failures = verify()
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("UAA GoatCitadel runtime turn/run/approval chain verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
