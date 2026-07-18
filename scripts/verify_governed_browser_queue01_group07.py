#!/usr/bin/env python3
"""Verify Queue 01 item 09 remains a human-only inactive handoff."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 07 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    handoffs = _read(
        "src/ultimate_ai_agent/core/governed_browser/human_challenges.py",
        failures,
    )
    transaction = _read(
        "src/ultimate_ai_agent/core/governed_browser/transaction.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = _read(
        "tests/test_governed_browser_queue01_group07.py",
        failures,
    )
    docs_readme = _read("docs/README.md", failures)
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "handoffs": (
            "GovernedHumanChallengeKind",
            "GovernedHumanChallengeHandoffRecipeRegistry",
            "ExactGovernedHumanChallengeHandoffService",
            "GovernedExternalActionKernel",
            "GOVERNED_HUMAN_CHALLENGE_RECEIPT_REF_MISMATCH",
            "GOVERNED_HUMAN_CHALLENGE_MATERIAL_REF_DENIED",
            "MAX_HUMAN_CHALLENGE_HANDOFF_LIFETIME",
            "idempotency-ref:governed-human-challenge-handoff",
            "exact_capability: Literal[AuthorityCapability.prepare]",
            "registered_recipe_required: Literal[True]",
            "exact_authority_lease_required: Literal[True]",
            "approval_revalidation_required: Literal[True]",
            "budget_reservation_required: Literal[True]",
            "readiness_revalidation_required: Literal[True]",
            "human_presence_required: Literal[True]",
            "credential_challenge_handling_allowed: Literal[False]",
            "passkey_operation_allowed: Literal[False]",
            "captcha_solving_allowed: Literal[False]",
            "captcha_bypass_allowed: Literal[False]",
            "browser_session_start_allowed: Literal[False]",
            "authentication_allowed: Literal[False]",
            "cookies_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "challenge_completed: Literal[False]",
            "passkey_operation_performed: Literal[False]",
            "captcha_solve_performed: Literal[False]",
            "captcha_bypass_performed: Literal[False]",
            "network_call_performed: Literal[False]",
        ),
        "transaction": (
            "def replay_if_terminal",
            "SELECT fingerprint_ref, receipt_json",
            "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT",
            "len(lease.domains) == 1",
            "AuthorityCapability(request.binding.authority_capability)",
        ),
        "package": (
            "ExactGovernedHumanChallengeHandoffService",
            "GovernedHumanChallengeHandoffRecipeRegistry",
            "build_governed_human_challenge_handoff_recipe",
            "governed_human_challenge_handoff_ref",
        ),
        "tests": (
            "test_registered_human_challenges_prepare_handoff_only",
            "test_handoff_replay_is_content_free_and_at_most_once",
            "test_unknown_recipe_and_approval_identifier_alone_do_not_prepare_handoff",
            "test_shared_revalidation_gates_block_before_handoff",
            "test_exact_scope_human_presence_and_real_targets_fail_closed",
            "test_expiry_and_dispatch_revalidation_never_return_handoff",
            "test_successful_handoff_replay_preserves_durable_receipt_after_expiry",
            "test_terminal_handoff_replays_before_recipe_window_without_new_claim",
            "test_registered_recipe_cannot_outlive_binding_deadline",
            "test_contracts_reject_raw_or_unbound_handoff_fields",
            "test_challenge_material_cannot_hide_inside_handoff_refs",
            "test_prepare_handoff_rejects_lease_with_implied_broader_capability",
            "test_replay_transaction_identity_is_bound_to_registered_recipe",
            "test_receipts_are_content_free_and_verifier_passes",
        ),
        "doc": (
            "09. Human-present MFA, passkey, and CAPTCHA handoff only",
            "`implemented_inactive`",
            "Material-like values hidden inside handoff refs",
            "recipe-bound transaction fingerprint",
            "does not handle",
            "Queue 02",
        ),
    }
    values = {
        "handoffs": handoffs,
        "transaction": transaction,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 07 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–09", docs_readme, "documentation README"),
        ("Queue 01 items 01–09", docs_index, "documentation index"),
        ("Queue 01 items 01–09", board, "current board"),
        ("Queue 01 items 01–09", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 07 {label} marker missing: {marker}")

    runtime_text = "\n".join((handoffs, transaction, package)).lower()
    for fragment in (
        "import requests",
        "import httpx",
        "import playwright",
        "import selenium",
        "import browserbase",
        "import firecrawl",
        "import subprocess",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 07 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 07 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 07 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 07 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [9],
                "classification": "implemented_inactive",
                "handoff_kinds": ["mfa", "passkey", "captcha"],
                "human_present_required": True,
                "challenge_handling_enabled": False,
                "passkey_operation_enabled": False,
                "captcha_solving_enabled": False,
                "captcha_bypass_enabled": False,
                "browser_session_enabled": False,
                "authentication_enabled": False,
                "live_network_enabled": False,
                "real_external_targets_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
