#!/usr/bin/env python3
"""Verify Queue 01 item 11 remains exact, plan-only, and inactive."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 09 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    contracts = _read(
        ("src/ultimate_ai_agent/core/governed_browser/external_operation_contracts.py"),
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
        "tests/test_governed_browser_queue01_group09.py",
        failures,
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_readme = _read("docs/README.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "contracts": (
            "GovernedExternalOperation.send_communication",
            "GovernedExternalOperation.publish_artifact",
            "GovernedExternalOperation.create_account",
            "GovernedExternalOperation.record_legal_consent",
            "GovernedExternalOperation.delete_resource",
            "AuthorityCapability.send",
            "AuthorityCapability.write",
            "AuthorityCapability.mutate",
            "AuthorityCapability.destructive",
            "GovernedExternalOperationRecipeRegistry",
            "ExactGovernedExternalOperationService",
            "GovernedExternalActionKernel",
            "idempotency-ref:governed-external-operation",
            "external-operation-authority-ref:governed-browser",
            "GOVERNED_EXTERNAL_OPERATION_RESOURCE_NOT_EXACTLY_BOUND",
            "GOVERNED_EXTERNAL_OPERATION_LEGAL_SCOPE_MISMATCH",
            "GOVERNED_EXTERNAL_OPERATION_DELETE_TARGET_MISMATCH",
            "GOVERNED_EXTERNAL_OPERATION_REVERSIBILITY_UNPROVEN",
            "GOVERNED_EXTERNAL_OPERATION_SUCCESS_KERNEL_PROOF_REQUIRED",
            "GOVERNED_EXTERNAL_OPERATION_SUCCESS_EVIDENCE_MISMATCH",
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_EXTERNAL_OPERATION_RECEIPT_STATE_MISMATCH",
            "_external_operation_replay_validation_context",
            "require_external_action_replay_provenance",
            "contract_plan_only: Literal[True]",
            "payload_materialization_allowed: Literal[False]",
            "browser_open_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "communication_send_allowed: Literal[False]",
            "publishing_allowed: Literal[False]",
            "account_creation_allowed: Literal[False]",
            "legal_consent_recording_allowed: Literal[False]",
            "delete_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "separate_exact_execution_required: Literal[True]",
            "communication_sent: Literal[False]",
            "artifact_published: Literal[False]",
            "account_created: Literal[False]",
            "legal_consent_recorded: Literal[False]",
            "resource_deleted: Literal[False]",
            "replay_if_terminal",
            "recover_if_prior_start",
            "idempotency-conflict",
            "recipe-expired",
            "trusted-clock-invalid",
        ),
        "transaction": (
            "Durable prepare-to-settle kernel for exact external actions.",
            "len(lease.domains) == 1",
            "len(browser_capabilities) == 1",
            "readiness.safe_disable_active",
            "readiness.kill_switch_engaged",
        ),
        "package": (
            "ExactGovernedExternalOperationService",
            "GovernedExternalOperationRecipeRegistry",
            "build_governed_external_operation_recipe",
            "governed_external_operation_authority_ref",
        ),
        "tests": (
            "test_registered_operations_prepare_exact_inactive_contracts",
            "test_legal_consent_is_explicit_and_account_creation_cannot_imply_it",
            "test_legal_and_delete_operation_specific_scope_is_fail_closed",
            "test_unknown_recipe_and_request_scope_drift_are_preflight_blocked",
            "test_exact_target_schema_artifact_and_operation_authority_are_required",
            "test_wrong_capability_and_real_targets_cannot_build_recipes",
            "test_approval_identifier_alone_grants_nothing",
            "test_exact_approval_without_matching_authority_lease_grants_nothing",
            "test_safe_disable_and_kill_switch_deny_contract_preparation_and_replay",
            "test_success_replay_is_content_free_and_at_most_once",
            "test_external_operation_replay_requires_exact_durable_provenance",
            "test_external_operation_terminal_replay_reconstructs_exact_operation_evidence",
            "test_external_operation_terminal_replay_rejects_arbitrary_non_success_evidence",
            "_rehash_external_operation_replay",
            "test_external_operation_replay_rejects_every_rehashed_evidence_field_tamper",
            "test_external_operation_replay_rejects_rehashed_evidence_order_and_arity_tamper",
            "test_external_operation_replay_rejects_cross_operation_and_transaction_substitution",
            "test_idempotency_drift_returns_content_free_blocked_receipt",
            "test_exported_contract_cannot_be_rebound_to_another_recipe",
            "test_success_and_replay_receipts_require_complete_kernel_proof",
            "test_success_receipt_rejects_tampered_operation_evidence",
            "test_operation_non_preflight_receipt_requires_kernel_context",
            "test_operation_receipt_rejects_kernel_state_status_mismatch",
            "test_operation_receipt_rejects_conflicting_rehashed_kernel_proofs",
            "test_expired_recipe_is_non_mutating_preflight_denial",
            "test_prior_started_transaction_remains_outcome_ambiguous_after_recipe_expiry",
            "test_invalid_service_clock_is_content_free_preflight_denial",
            "test_receipts_and_durable_ledger_never_record_descriptor_material",
        ),
        "doc": (
            "11. Exact communications, publishing, account creation, legal consent, and delete contracts",
            "`implemented_inactive`",
            "plan-only",
            "explicit accept or decline",
            "cannot imply legal consent",
            "exact deletion target",
            "separate exact execution",
            "does not send",
            "does not publish",
            "does not create an account",
            "does not record legal consent",
            "does not delete",
            "Queue 02",
        ),
    }
    values = {
        "contracts": contracts,
        "transaction": transaction,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 09 {label} marker missing: {marker}")

    completed_item11_or_later = tuple(
        f"Queue 01 items 01–{item:02d}" for item in range(11, 14)
    )
    for text, label in (
        (docs_readme, "documentation README"),
        (docs_index, "documentation index"),
        (board, "current board"),
        (truth, "release truth"),
    ):
        if not any(marker in text for marker in completed_item11_or_later):
            failures.append(
                "Queue 01 group 09 "
                f"{label} marker missing: Queue 01 items 01–11 or later"
            )

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
        "import browserbase",
        "from browserbase import",
        "import firecrawl",
        "from firecrawl import",
        "import subprocess",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 09 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 09 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 09 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 09 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [11],
                "classification": "implemented_inactive",
                "contract_plan_only": True,
                "communication_send_enabled": False,
                "publishing_enabled": False,
                "account_creation_enabled": False,
                "legal_consent_recording_enabled": False,
                "delete_enabled": False,
                "browser_session_enabled": False,
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
