#!/usr/bin/env python3
"""Verify Queue 01 item 05 without activating live browser or network access."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 03 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    recipes = _read(
        "src/ultimate_ai_agent/core/governed_browser/evidence_recipes.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = _read("tests/test_governed_browser_queue01_group03.py", failures)
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "recipes": (
            "GovernedBrowserEvidenceRecipe",
            "GovernedBrowserEvidenceRecipeRegistry",
            "ExactBrowserObservationService",
            "registered_recipe_required: Literal[True]",
            "exact_authority_lease_required: Literal[True]",
            "approval_revalidation_required: Literal[True]",
            "budget_reservation_required: Literal[True]",
            "readiness_revalidation_required: Literal[True]",
            "ephemeral_private_profile_required: Literal[True]",
            "web_content_instruction_use_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "raw_gateway_result_returned: Literal[False]",
            "raw_transport_result_returned: Literal[False]",
            "WebAccessGateway",
            "GovernedExternalActionKernel",
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_RECEIPT_STATE_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_REPLAY_STATUS_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_PREFLIGHT_EXTERNAL_PROOF_DENIED",
            "GOVERNED_BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE",
            "_browser_observation_kernel_execution",
            "_browser_observation_replay_expectation",
            "require_external_action_replay_provenance",
        ),
        "package": (
            "GovernedBrowserEvidenceRecipe",
            "ExactBrowserObservationService",
            "build_governed_browser_evidence_recipe",
        ),
        "tests": (
            "test_registered_recipe_observes_exact_local_fixture_through_all_governance",
            "test_unknown_recipe_is_content_free_and_blocked_before_gateway",
            "test_approval_identifier_alone_grants_no_observation_authority",
            "test_revalidation_denies_before_observation",
            "test_observation_is_at_most_once_and_replay_is_content_free",
            "test_observation_blocked_and_failed_terminals_replay_content_free",
            "test_observation_kernel_ambiguous_terminal_replays_content_free",
            "test_observation_receipt_rejects_rehashed_conflicting_kernel_proofs",
            "test_observation_non_preflight_receipt_requires_kernel_context",
            "test_observation_non_preflight_rejects_orphan_kernel_proof",
            "test_observation_preflight_rejects_orphan_kernel_proof",
            "test_observation_receipt_rejects_kernel_state_status_mismatch",
            "test_observation_non_replay_status_rejects_replay_flag",
            "test_observation_replayed_success_requires_complete_kernel_proof",
            "test_observation_replay_requires_exact_durable_provenance",
            "test_observation_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity",
            "test_observation_recipe_identity_conflicts_on_same_transaction",
            "test_settlement_failure_returns_ambiguous_receipt_without_evidence_or_retry",
            "test_unregistered_raw_or_drifted_transport_output_fails_content_free",
            "test_real_external_target_cannot_create_an_evidence_recipe",
        ),
        "doc": (
            "05. Evidence Recipes and exact browser observation",
            "`implemented_inactive`",
            "registered Evidence Recipe",
            "injected local validation",
            "Queue 02",
        ),
    }
    values = {
        "recipes": recipes,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 03 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–05", docs_index, "documentation index"),
        ("Queue 01 items 01–05", board, "current board"),
        ("Queue 01 items 01–05", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 03 {label} marker missing: {marker}")

    runtime_text = "\n".join((recipes, package)).lower()
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
            failures.append(f"Queue 01 group 03 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 03 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 03 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 03 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [5],
                "classification": "implemented_inactive",
                "browser_observation_mode": "injected_local_validation",
                "live_browser_enabled": False,
                "real_external_targets_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
