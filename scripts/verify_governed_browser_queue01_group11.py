#!/usr/bin/env python3
"""Verify Queue 01 item 13 remains exact, plan-only, and inactive."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 11 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    composer = _read(
        "src/ultimate_ai_agent/core/governed_browser/task_composer.py",
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
        "tests/test_governed_browser_queue01_group11.py",
        failures,
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_readme = _read("docs/README.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "composer": (
            "ExactGovernedTaskComposer",
            "GovernedTaskOperationRegistry",
            "GovernedTaskCompositionRecipeRegistry",
            "registered_operations_only: Literal[True]",
            "exact_step_authority_required: Literal[True]",
            "composer_authority_applies_to_steps: Literal[False]",
            "complete_any_task_granted: Literal[False]",
            "model_call_allowed: Literal[False]",
            "automatic_execution_allowed: Literal[False]",
            "browser_action_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "GOVERNED_TASK_COMPOSER_OPERATION_UNREGISTERED",
            "_opaque_registered_source_ref",
            "_HASH_PINNED_REF_RE.fullmatch(source_ref)",
            '"completeanytask"',
            "broad_scope_grant",
            "governed_task_composition_plan_payload_ref",
            '"created_at": created_at.isoformat()',
            'prefix="intent-ref:governed-external-action:"',
            "GOVERNED_TASK_COMPOSER_ENVELOPE_REF_MISMATCH",
            "GOVERNED_TASK_COMPOSER_PLAN_PAYLOAD_REF_MISMATCH",
            "GOVERNED_TASK_COMPOSER_RECEIPT_STATE_MISMATCH",
            "GOVERNED_TASK_COMPOSER_AUTHORITY_DECISION_REF_REQUIRED",
            "GOVERNED_TASK_COMPOSER_RECEIPT_REASON_REQUIRED",
            "GOVERNED_TASK_COMPOSER_DEPENDENCY_NOT_PRIOR",
            "GOVERNED_TASK_COMPOSER_OPERATION_REUSE_DENIED",
            "GOVERNED_TASK_COMPOSER_PREPARE_CAPABILITY_REQUIRED",
            "GOVERNED_TASK_COMPOSER_BROAD_",
            "replay_if_terminal",
            "recover_if_prior_start",
            "idempotency-conflict",
            "recipe-expired",
            "trusted-clock-invalid",
        ),
        "transaction": (
            "Durable prepare-to-settle kernel for exact external actions.",
            "readiness.safe_disable_active",
            "readiness.kill_switch_engaged",
        ),
        "package": (
            "ExactGovernedTaskComposer",
            "GovernedTaskOperationRegistry",
            "build_governed_task_composition_recipe",
            "governed_task_broad_intent_ref",
        ),
        "tests": (
            "test_registered_operations_compose_into_exact_plan_only_projection",
            "test_bounded_operation_families_accept_only_their_exact_capability",
            "test_raw_or_broad_intent_cannot_enter_the_composer",
            "test_operation_registration_is_hash_bound_and_authority_unique",
            "test_recipe_rejects_unknown_operations_cycles_reuse_and_reordering",
            "test_exact_binding_rejects_capability_scope_and_target_drift",
            "test_unknown_recipe_and_exact_request_drift_are_preflight_blocked",
            "test_composition_request_rejects_contentful_refs_and_transaction_ids",
            "test_approval_identifier_alone_grants_no_composition_plan",
            "test_safe_disable_and_kill_switch_deny_composition",
            "test_success_replay_is_content_free_and_idempotency_drift_is_denied",
            "test_expired_recipe_and_invalid_clock_fail_before_composition",
            "test_real_target_absent_human_and_more_than_eight_steps_are_denied",
            "test_receipt_and_plan_are_safe_ref_only_and_record_no_intent_content",
            "test_serialized_plan_cannot_rebind_a_registered_operation_or_plan_ref",
            "test_recipe_registry_returns_defensive_copies_and_receipt_states_are_exact",
        ),
        "doc": (
            "13. Exact registered-operation task composer",
            "`implemented_inactive`",
            "hash-pinned broad-intent ref",
            "registered operations",
            "`prepare`",
            "`complete_any_task`",
            "does not execute",
            "Queue 02",
        ),
    }
    values = {
        "composer": composer,
        "transaction": transaction,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 11 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–13", docs_readme, "documentation README"),
        ("Queue 01 items 01–13", docs_index, "documentation index"),
        ("Queue 01 items 01–13", board, "current board"),
        ("Queue 01 items 01–13", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 11 {label} marker missing: {marker}")

    runtime_text = "\n".join((composer, transaction, package)).lower()
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
        "import subprocess",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 11 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 11 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 11 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 11 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [13],
                "classification": "implemented_inactive",
                "plan_only": True,
                "registered_operations_only": True,
                "complete_any_task_granted": False,
                "model_call_enabled": False,
                "automatic_execution_enabled": False,
                "browser_action_enabled": False,
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
