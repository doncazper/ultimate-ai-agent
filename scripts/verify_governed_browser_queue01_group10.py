#!/usr/bin/env python3
"""Verify Queue 01 item 12 remains exact, financial-plan-only, and inactive."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 10 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    contracts = _read(
        "src/ultimate_ai_agent/core/governed_browser/financial_operation_contracts.py",
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
        "tests/test_governed_browser_queue01_group10.py",
        failures,
    )
    hardening_tests = _read(
        "tests/test_governed_browser_queue01_group10_hardening.py",
        failures,
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_readme = _read("docs/README.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "contracts": (
            "GovernedFinancialOperation.purchase",
            "GovernedFinancialOperation.booking",
            "GovernedFinancialOperation.checkout_payment",
            "GovernedFinancialOperation.financial_transaction",
            "AuthorityCapability.purchase",
            "AuthorityCapability.purchase_under_budget",
            "ExactGovernedFinancialService",
            "GovernedFinancialRecipeRegistry",
            "GOVERNED_FINANCIAL_AMOUNT_OUTSIDE_EXACT_BUDGET",
            "GOVERNED_FINANCIAL_OPERATION_SCOPE_MISMATCH",
            "GOVERNED_FINANCIAL_RESOURCE_NOT_EXACTLY_BOUND",
            "GOVERNED_FINANCIAL_RECEIPT_STATE_MISMATCH",
            "GOVERNED_FINANCIAL_SUCCESS_EVIDENCE_MISMATCH",
            "GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_FINANCIAL_EXTERNAL_RECEIPT_REF_MISMATCH",
            "payment_handle_resolution_allowed: Literal[False]",
            "checkout_open_allowed: Literal[False]",
            "purchase_allowed: Literal[False]",
            "booking_allowed: Literal[False]",
            "payment_allowed: Literal[False]",
            "financial_transaction_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "separate_financial_execution_required: Literal[True]",
            "payment_handle_resolved: Literal[False]",
            "checkout_opened: Literal[False]",
            "purchase_performed: Literal[False]",
            "booking_performed: Literal[False]",
            "payment_performed: Literal[False]",
            "financial_transaction_performed: Literal[False]",
            "replay_if_terminal",
            "recover_if_prior_start",
            "idempotency-conflict",
            "recipe-expired",
            "trusted-clock-invalid",
        ),
        "transaction": (
            "Durable prepare-to-settle kernel for exact external actions.",
            "recover_if_prior_start",
            "readiness.safe_disable_active",
            "readiness.kill_switch_engaged",
        ),
        "package": (
            "ExactGovernedFinancialService",
            "GovernedFinancialRecipeRegistry",
            "build_exact_governed_financial_scope",
            "build_governed_financial_recipe",
        ),
        "tests": (
            "test_registered_financial_operations_prepare_exact_inactive_contracts",
            "test_exported_financial_contract_cannot_be_rebound_to_another_binding",
            "test_operation_specific_financial_scope_is_fail_closed",
            "test_amount_must_fit_exact_positive_spend_ceiling",
            "test_wrong_capability_real_target_and_absent_human_are_denied",
            "test_exact_target_schema_and_resource_binding_cannot_drift",
            "test_unknown_recipe_and_exact_request_drift_are_preflight_blocked",
            "test_approval_identifier_alone_grants_no_financial_contract",
            "test_exact_approval_without_matching_lease_grants_no_financial_contract",
            "test_safe_disable_and_kill_switch_deny_financial_preparation_and_replay",
            "test_success_replay_and_idempotency_drift_are_content_free",
            "test_success_receipt_requires_complete_exact_evidence",
            "test_financial_non_preflight_receipt_requires_kernel_context",
            "test_financial_receipt_rejects_conflicting_rehashed_kernel_proofs",
            "test_expired_recipe_is_preflight_denial_but_prior_start_is_ambiguous",
            "test_invalid_clock_is_content_free_preflight_denial",
            "test_receipt_and_ledger_never_record_target_or_payment_material",
        ),
        "doc": (
            "12. Exact purchases/bookings, checkout/payment, and financial-transaction contracts",
            "`implemented_inactive`",
            "opaque payment-handle",
            "exact spend ceiling",
            "plan-only",
            "does not purchase",
            "does not book",
            "does not open checkout",
            "does not pay",
            "does not transfer funds",
            "Queue 02",
        ),
    }
    values = {
        "contracts": contracts,
        "transaction": transaction,
        "package": package,
        "tests": "\n".join((tests, hardening_tests)),
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 10 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–12", docs_readme, "documentation README"),
        ("Queue 01 items 01–12", docs_index, "documentation index"),
        ("Queue 01 items 01–12", board, "current board"),
        ("Queue 01 items 01–12", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 10 {label} marker missing: {marker}")

    runtime_text = "\n".join((contracts, transaction, package)).lower()
    for fragment in (
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "from urllib import request",
        "import urllib3",
        "from urllib3 import",
        "import http.client",
        "from http import client",
        "import playwright",
        "from playwright import",
        "import selenium",
        "from selenium import",
        "import stripe",
        "from stripe import",
        "import subprocess",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 10 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 10 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 10 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 10 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [12],
                "classification": "implemented_inactive",
                "contract_plan_only": True,
                "payment_handle_resolution_enabled": False,
                "checkout_enabled": False,
                "purchase_enabled": False,
                "booking_enabled": False,
                "payment_enabled": False,
                "financial_transaction_enabled": False,
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
