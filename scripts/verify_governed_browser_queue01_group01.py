#!/usr/bin/env python3
"""Verify Queue 01 items 01–03 without activating external targets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 01 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    authority = _read("src/ultimate_ai_agent/core/authority/contracts.py", failures)
    contracts = _read(
        "src/ultimate_ai_agent/core/governed_browser/contracts.py", failures
    )
    broker = _read("src/ultimate_ai_agent/core/governed_browser/broker.py", failures)
    transaction = _read(
        "src/ultimate_ai_agent/core/governed_browser/transaction.py", failures
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    tests = _read("tests/test_governed_browser_queue01_group01.py", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "authority": (
            "AuthorityCapability.admin: {AuthorityCapability.admin}",
            "AuthorityCapability.destructive: {AuthorityCapability.destructive}",
        ),
        "contracts": (
            "ExternalActionAuthorityBinding",
            "origin_ref",
            "recipient_ref",
            "field_schema_ref",
            "transaction_ref",
            "artifact_refs",
            "resource_refs",
            "action_count",
            "page_snapshot_ref",
            "start_deadline",
            "human_presence_ref",
            '"status": "implemented_inactive"',
            '"real_external_targets_enabled": False',
            '"automatic_retry_allowed": False',
        ),
        "broker": (
            "WebAccessGateway",
            "TemporaryDirectory",
            "BoundedSemaphore",
            "GOVERNED_BROWSER_ORDINARY_PROFILE_DENIED",
            "GOVERNED_BROWSER_EXTERNAL_MUTATION_INACTIVE",
            "self.external_mutation_enabled = False",
        ),
        "transaction": (
            "ExternalActionTransactionStore",
            "PolicyEngine",
            "LocalApprovalAuthority",
            "AuthorityBudgetStoreGate",
            "outcome_ambiguous",
            "GOVERNED_EXTERNAL_ACTION_REAL_TARGETS_MUST_REMAIN_INACTIVE",
            "claim_start",
            "_revalidation_reasons",
        ),
        "doc": (
            "prepare → authorize → reserve → revalidate → dispatch → verify → settle",
            "real external targets",
            "Queue 02",
            "implemented_inactive",
        ),
        "tests": (
            "test_admin_and_destructive_authority_do_not_imply_unrelated_capabilities",
            "test_isolated_broker_stays_behind_gateway_and_removes_ephemeral_profile",
            "test_exact_local_validation_transaction_is_at_most_once_and_content_free",
            "test_dispatch_exception_is_ambiguous_and_never_retried",
        ),
    }
    values = {
        "authority": authority,
        "contracts": contracts,
        "broker": broker,
        "transaction": transaction,
        "doc": doc,
        "tests": tests,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 01 {label} marker missing: {marker}")

    for marker, text, label in (
        ("GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", docs_index, "documentation index"),
        ("Queue 01 items 01–03", board, "current board"),
        ("Queue 01 items 01–03", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 01 {label} marker missing: {marker}")

    forbidden_runtime_imports = (
        "import requests",
        "import httpx",
        "import playwright",
        "import selenium",
        "import browserbase",
        "import firecrawl",
    )
    runtime_text = "\n".join((contracts, broker, transaction)).lower()
    for fragment in forbidden_runtime_imports:
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 01 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 01 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 01 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 01 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [1, 2, 3],
                "classification": "implemented_inactive",
                "real_external_targets_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
