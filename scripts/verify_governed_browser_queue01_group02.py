#!/usr/bin/env python3
"""Verify Queue 01 item 04 without activating browser or external targets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 02 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    envelope = _read(
        "src/ultimate_ai_agent/core/governed_browser/action_inbox.py", failures
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py", failures
    )
    tests = _read("tests/test_governed_browser_queue01_group02.py", failures)
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "envelope": (
            "ExternalActionInboxExecutionEnvelope",
            "readable_scope",
            "side_effect_posture",
            "data_classification",
            "expiry_posture",
            "reversibility_posture",
            "retry_posture",
            "approval_fingerprint_ref",
            "expected_receipt_refs",
            "receipt_refs",
            "reconciliation_status",
            "Open in browser",
            "Human takeover",
            "approval_ref_is_identifier_only",
            "uaa_execution_enabled: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "GOVERNED_BROWSER_INBOX_RECEIPT_BINDING_MISMATCH",
            "_ACCOUNTING_RECONCILIATION_REASON_MARKERS",
            "budget-release-unconfirmed",
        ),
        "package": (
            "ExternalActionInboxExecutionEnvelope",
            "build_external_action_inbox_envelope",
        ),
        "tests": (
            "test_action_inbox_envelope_is_readable_content_free_and_inactive",
            "test_approval_identifier_alone_never_enables_execution_and_missing_scope_denies",
            "test_current_safety_posture_is_visible_and_fail_closed",
            "test_ambiguous_receipt_requires_manual_reconciliation_and_never_retries",
            "test_blocked_receipt_with_unconfirmed_budget_release_requires_reconciliation",
            "test_receipt_from_a_different_transaction_is_rejected",
        ),
        "doc": (
            "04. Action Inbox execution envelope",
            "`implemented_inactive`",
            "Open in browser",
            "Human takeover",
            "Queue 02",
        ),
    }
    values = {
        "envelope": envelope,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 02 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–04", docs_index, "documentation index"),
        ("Queue 01 items 01–04", board, "current board"),
        ("Queue 01 items 01–04", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 02 {label} marker missing: {marker}")

    runtime_text = "\n".join((envelope, package)).lower()
    for fragment in (
        "import requests",
        "import httpx",
        "import playwright",
        "import selenium",
        "import browserbase",
        "import firecrawl",
        "subprocess.",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 02 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 02 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 02 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 02 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [4],
                "classification": "implemented_inactive",
                "real_external_targets_enabled": False,
                "browser_execution_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
