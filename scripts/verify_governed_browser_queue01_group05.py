#!/usr/bin/env python3
"""Verify Queue 01 item 07 without enabling POST or browser execution."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 05 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    post_forms = _read(
        "src/ultimate_ai_agent/core/governed_browser/post_forms.py",
        failures,
    )
    receipt_contract = _read(
        "src/ultimate_ai_agent/core/governed_browser/browser_actions.py",
        failures,
    )
    broker = _read(
        "src/ultimate_ai_agent/core/governed_browser/broker.py",
        failures,
    )
    policy = _read(
        "src/ultimate_ai_agent/core/web_access/policy.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = "\n".join(
        (
            _read("tests/test_governed_browser_queue01_group05.py", failures),
            _read("tests/test_governed_browser_queue02_hardening.py", failures),
        )
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "post_forms": (
            "GovernedPostFormSchema",
            "GovernedPostFormSchemaRegistry",
            "GovernedPostFormRecipe",
            "GovernedPostFormRecipeRegistry",
            "ExactPostFormService",
            "MAX_REGISTERED_POST_FORM_FIELDS = 5",
            'method: Literal["POST"]',
            'encoding: Literal["application/x-www-form-urlencoded"]',
            "registered_schema_required: Literal[True]",
            "exact_authority_lease_required: Literal[True]",
            "approval_revalidation_required: Literal[True]",
            "budget_reservation_required: Literal[True]",
            "readiness_revalidation_required: Literal[True]",
            "request_body_materialization_allowed: Literal[False]",
            "form_submission_allowed: Literal[False]",
            "authenticated_session_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "WebAccessGateway",
            "GovernedExternalActionKernel",
            "GOVERNED_POST_FORM_PLAN_RECEIPT_MISMATCH",
            "GOVERNED_POST_FORM_PLAN_PROJECTION_REF_MISMATCH",
            "_post_form_kernel_execution",
            "_post_form_replay_expectation",
        ),
        "receipt_contract": (
            "GOVERNED_BROWSER_ACTION_SUCCESS_KERNEL_PROOF_REQUIRED",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_BROWSER_ACTION_RECEIPT_STATE_MISMATCH",
            "GOVERNED_BROWSER_ACTION_REPLAY_STATUS_MISMATCH",
            "require_external_action_replay_provenance",
        ),
        "broker": (
            "IsolatedBrowserActionDryRunBrokerAdapter",
            '"form_submission_execution"',
            '"field_value_resolution"',
            '"request_body_materialization"',
            '"form_submission_performed"',
            '"field_values_resolved"',
            '"request_body_materialized"',
            "GOVERNED_BROWSER_ACTION_EXECUTION_INACTIVE",
        ),
        "policy": (
            '"form_submission_execution"',
            "browser_action_dry_run_form_submission_execution_denied",
            '"field_value_resolution"',
            "browser_action_dry_run_field_value_resolution_denied",
            '"request_body_materialization"',
            "browser_action_dry_run_request_body_materialization_denied",
            '"form_submission_performed"',
            "browser_action_dry_run_form_submission_performed_denied",
            '"field_values_resolved"',
            "browser_action_dry_run_field_values_resolved_denied",
            '"request_body_materialized"',
            "browser_action_dry_run_request_body_materialized_denied",
        ),
        "package": (
            "GovernedPostFormSchema",
            "GovernedPostFormRecipe",
            "ExactPostFormService",
            "build_governed_post_form_schema",
            "build_governed_post_form_recipe",
        ),
        "tests": (
            "test_registered_exact_post_schema_is_governed_and_inactive",
            "test_unknown_recipe_is_blocked_before_authority_or_gateway",
            "test_approval_identifier_alone_grants_nothing",
            "test_post_form_revalidation_denies_before_plan",
            "test_schema_and_recipe_require_exact_registered_field_set",
            "test_post_schema_fields_and_values_must_be_authority_bound",
            "test_post_schema_field_limit_matches_authority_resource_capacity",
            "test_post_transport_requires_explicit_proof_flags",
            "test_post_form_plan_is_at_most_once_and_replay_is_content_free",
            "test_post_form_blocked_and_failed_terminals_replay_content_free",
            "test_post_form_settlement_failure_suppresses_plan_and_retry",
            "test_post_transport_drift_or_execution_fails_content_free",
            "test_real_external_target_cannot_create_post_recipe",
            "test_browser_action_success_receipt_requires_complete_kernel_proof",
            "test_browser_action_receipt_identity_binds_budget_release_proof",
            "test_post_form_result_binds_exact_plan_projection",
            "test_browser_action_receipt_rejects_rehashed_kernel_proof_conflicts",
            "test_browser_action_receipt_rejects_rehashed_kernel_field_rebinding",
            "test_browser_action_non_preflight_receipt_requires_kernel_context",
            "test_browser_action_non_preflight_rejects_orphan_kernel_proof",
            "test_browser_action_receipt_rejects_kernel_state_status_mismatch",
            "test_browser_action_non_replay_status_rejects_replay_flag",
            "test_post_form_replay_requires_exact_durable_provenance",
            "test_post_form_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity",
        ),
        "doc": (
            "07. Registered exact POST-form schemas",
            "`implemented_inactive`",
            "exact POST-form schemas",
            "no request body",
            "Queue 02",
        ),
    }
    values = {
        "post_forms": post_forms,
        "receipt_contract": receipt_contract,
        "broker": broker,
        "policy": policy,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 05 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–07", docs_index, "documentation index"),
        ("Queue 01 items 01–07", board, "current board"),
        ("Queue 01 items 01–07", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 05 {label} marker missing: {marker}")

    runtime_text = "\n".join((post_forms, broker, policy, package)).lower()
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
            failures.append(f"Queue 01 group 05 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 05 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 05 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 05 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [7],
                "classification": "implemented_inactive",
                "post_form_mode": "registered_schema_plan_only",
                "request_body_materialized": False,
                "form_submission_enabled": False,
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
