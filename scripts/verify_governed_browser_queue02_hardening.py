#!/usr/bin/env python3
"""Verify Queue 02 hardening coverage and all-inactive activation truth."""

from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.core.governed_browser import (
    GovernedBrowserQueue02Lane,
    governed_browser_queue02_inactive_activation_matrix,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 02 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    contracts = _read(
        "src/ultimate_ai_agent/core/governed_browser/contracts.py", failures
    )
    transaction = _read(
        "src/ultimate_ai_agent/core/governed_browser/transaction.py", failures
    )
    hardening = _read(
        "src/ultimate_ai_agent/core/governed_browser/adversarial_hardening.py",
        failures,
    )
    external_operations = _read(
        "src/ultimate_ai_agent/core/governed_browser/external_operation_contracts.py",
        failures,
    )
    tests = _read("tests/test_governed_browser_queue02_hardening.py", failures)
    external_operation_tests = _read(
        "tests/test_governed_browser_queue01_group09.py", failures
    )
    projection_sources = {
        relative: _read(relative, failures)
        for relative in (
            "src/ultimate_ai_agent/core/governed_browser/artifact_transfers.py",
            "src/ultimate_ai_agent/core/governed_browser/browser_actions.py",
            "src/ultimate_ai_agent/core/governed_browser/evidence_recipes.py",
            "src/ultimate_ai_agent/core/governed_browser/financial_operation_contracts.py",
            "src/ultimate_ai_agent/core/governed_browser/human_challenges.py",
            "src/ultimate_ai_agent/core/governed_browser/post_forms.py",
            "src/ultimate_ai_agent/core/governed_browser/task_composer.py",
        )
    }
    browser_actions = projection_sources[
        "src/ultimate_ai_agent/core/governed_browser/browser_actions.py"
    ]
    origin_sessions = _read(
        "src/ultimate_ai_agent/core/governed_browser/origin_sessions.py", failures
    )
    doc = _read(
        "docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_02_HARDENING.md", failures
    )
    queue01_doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_readme = _read("docs/README.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required = {
        "contracts": (
            "ExternalActionAdversarialSignals",
            "observed_origin_ref",
            "observed_recipient_ref",
            "observed_field_schema_ref",
            "observed_transaction_ref",
            "observed_artifact_refs",
            "observed_resource_refs",
            "cross_origin_redirect_detected",
            "prompt_injection_detected",
            "automatic-retry-denied",
            "GOVERNED_BROWSER_READINESS_REF_MISMATCH",
            "GOVERNED_EXTERNAL_ACTION_RECEIPT_REF_MISMATCH",
        ),
        "transaction": (
            "BEGIN IMMEDIATE",
            "GOVERNED_EXTERNAL_ACTION_TERMINAL_RECEIPT_CONFLICT",
            "GOVERNED_EXTERNAL_ACTION_FINISH_STATE_CONFLICT",
            "start-already-claimed",
            "recovery_not_before",
            "post-start-revalidation-denied",
            "post-dispatch-revalidation-denied",
            "dispatch-timeout",
            "dispatch-capacity-bounded",
            "claim_dispatch_slot",
            "governed_external_action_dispatch_slot",
            "_try_acquire_dispatch_process_lock",
            "_DISPATCH_PROCESS_LOCK_PROTOCOL",
            "fcntl.flock",
            "MAX_EXTERNAL_ACTION_DISPATCH_SECONDS",
            "hold_validation_lock",
            "monotonic()",
            "budget_release_ref",
            "budget_reservation_ref_if_exact",
            "started_budget_reservation_ref_if_exact",
            "_lost_start_claim_receipt",
            "finish-ownership-lost",
            "prior-start-recovery",
            "post-start-dispatch-not-invoked",
            "_TERMINAL_ACCOUNTING_REASON_MARKERS",
            "reason-overflow",
            "budget-settlement-ambiguous",
        ),
        "hardening": (
            "GovernedBrowserLaneActivationEvidence",
            "GovernedBrowserLaneActivationDecision",
            "adapter_required",
            "configuration_required",
            "external_facility_required",
            "blocked_pending_live_evidence",
            "eligible_for_separate_activation_review",
            "activation_performed: Literal[False]",
            "standing_authority_granted: Literal[False]",
            "governed_browser_queue02_inactive_activation_matrix",
        ),
        "external_operations": (
            "budget_release_ref",
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "_external_operation_receipt_identity_payload",
        ),
        "browser_actions": (
            "GOVERNED_BROWSER_ACTION_RECEIPT_REF_MISMATCH",
            '"receipt-ref:governed-browser-action"',
            '"receipt-ref:governed-post-form"',
        ),
        "tests": (
            "test_every_hostile_signal_blocks_before_dispatch",
            "test_every_observed_scope_dimension_is_revalidated",
            "test_stop_posture_race_after_start_becomes_ambiguous",
            "test_authority_revocation_race_after_reservation_blocks_start",
            "test_authority_revocation_waits_for_final_validation_and_dispatch",
            "test_dispatch_timeout_is_ambiguous_non_retryable_and_capacity_bounded",
            "test_ambiguous_dispatch_evidence_is_bound_to_each_exact_request",
            "test_concurrent_execute_never_clobbers_the_dispatch_owner",
            "test_restart_recovery_cannot_terminalize_a_fresh_live_start",
            "test_restart_recovery_uses_the_maximum_owner_dispatch_window",
            "test_restart_recovery_reaps_stale_process_slot_and_settles_budget",
            "test_stale_dispatch_slot_is_reaped_before_capacity_denial",
            "test_dispatch_capacity_is_shared_durably_across_kernel_instances",
            "test_lost_start_claim_releases_only_a_distinct_unused_reservation",
            "test_lost_start_claim_preserves_the_winners_shared_reservation",
            "test_preclaim_denial_never_releases_a_live_owners_shared_reservation",
            "test_lost_start_claim_surfaces_distinct_local_release_proof_after_terminal",
            "test_lost_start_claim_rejects_release_without_receipt_proof",
            "test_prestart_finish_cas_loss_returns_current_ambiguous_state",
            "test_browser_action_receipt_identity_binds_budget_release_proof",
            "test_terminal_compare_and_swap_rejects_overwrite",
            "test_reason_bounding_preserves_terminal_accounting_failures",
            "test_every_operator_receipt_contract_retains_budget_release_proof",
            "test_honest_matrix_covers_every_lane_and_keeps_every_lane_inactive",
        ),
        "external_operation_tests": (
            "test_operation_receipt_rejects_rebound_kernel_receipt_fields",
            "test_operation_receipt_preserves_prestart_budget_release_proof",
            "test_failed_kernel_receipt_keeps_original_reason_identity",
        ),
        "doc": (
            "Queue 02",
            "implemented_inactive",
            "Activation Matrix",
            "external_facility_required",
            "adapter_required",
            "configuration_required",
            "blocked_pending_live_evidence",
            "No lane was activated",
        ),
    }
    texts = {
        "contracts": contracts,
        "transaction": transaction,
        "hardening": hardening,
        "external_operations": external_operations,
        "browser_actions": browser_actions,
        "tests": tests,
        "external_operation_tests": external_operation_tests,
        "doc": doc,
    }
    for label, markers in required.items():
        for marker in markers:
            if marker not in texts[label]:
                failures.append(f"Queue 02 {label} marker missing: {marker}")

    release_projection_marker = (
        '"budget_release_ref": external_receipt.budget_release_ref'
    )
    for relative, source in projection_sources.items():
        if release_projection_marker not in source:
            failures.append(
                f"Queue 02 budget release projection missing: {relative}"
            )
    if (
        '"budget_release_ref": (' not in origin_sessions
        or "external_receipt.budget_release_ref" not in origin_sessions
    ):
        failures.append("Queue 02 budget release projection missing: origin_sessions.py")

    campaign_markers = (
        "authority and capability confusion",
        "changed, expired, revoked, missing, and mismatched approvals or leases",
        "cross-origin redirects",
        "DOM swaps",
        "hidden fields",
        "changed form actions",
        "misleading controls",
        "unexpected pop-ups and downloads",
        "page mutation between approval and dispatch",
        "duplicate submission",
        "timeout after dispatch",
        "crash, replay, interruption, restart, and settlement recovery",
        "concurrent execution",
        "kill-switch races",
        "safe-disable races",
        "secret and credential canaries",
        "prompt-injection-shaped page content",
        "raw-content and path leakage",
        "session fixation and origin confusion",
        "upload artifact substitution",
        "download filename/type/signature attacks",
        "recipient/content/amount/total substitution",
        "payment, publishing, account, consent, deletion, and transfer retry denial",
        "resource exhaustion and bounded cleanup",
        "cross-lane non-interference",
        "full macOS packaged golden journeys",
    )
    for marker in campaign_markers:
        if marker not in doc:
            failures.append(f"Queue 02 campaign evidence missing: {marker}")

    for marker, text, label in (
        ("Queue 02 adversarial hardening", queue01_doc, "Queue 01 document"),
        ("Queue 02 adversarial hardening", docs_readme, "documentation README"),
        ("Queue 02 adversarial hardening", docs_index, "documentation index"),
        ("Queue 02 adversarial hardening", board, "current board"),
        ("Queue 02 adversarial hardening", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 02 cross-link missing from {label}")

    try:
        matrix = governed_browser_queue02_inactive_activation_matrix(
            macos_packaged_golden_verified=True
        )
    except Exception as exc:
        failures.append(f"Queue 02 activation matrix invalid: {type(exc).__name__}")
    else:
        if len(matrix) != len(GovernedBrowserQueue02Lane) or len(matrix) != 13:
            failures.append("Queue 02 activation matrix does not cover 13 lanes")
        if any(item.activation_performed for item in matrix):
            failures.append("Queue 02 activation matrix activated a lane")
        if any(item.real_external_targets_enabled for item in matrix):
            failures.append("Queue 02 activation matrix enabled a real target")

    runtime_text = "\n".join((contracts, transaction, hardening)).lower()
    for fragment in (
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "import playwright",
        "import selenium",
        "import subprocess",
        "external_mutation_enabled: literal[true]",
        "activation_performed: literal[true]",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 02 forbidden runtime marker: {fragment}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 02 hardening verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    matrix = governed_browser_queue02_inactive_activation_matrix(
        macos_packaged_golden_verified=True
    )
    print("Governed Browser Queue 02 hardening verification PASSED")
    print(
        json.dumps(
            {
                "lanes": len(matrix),
                "classifications": sorted({item.posture for item in matrix}),
                "activation_performed": False,
                "real_external_targets_enabled": False,
                "browser_action_enabled": False,
                "live_network_enabled": False,
                "external_mutation_enabled": False,
                "standing_authority_granted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
