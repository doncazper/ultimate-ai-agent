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
    replay_provenance = _read(
        "src/ultimate_ai_agent/core/governed_browser/replay_provenance.py",
        failures,
    )
    operation_proofs = _read(
        "src/ultimate_ai_agent/core/governed_browser/operation_proofs.py",
        failures,
    )
    replay_provenance_tests = _read(
        "tests/test_governed_browser_replay_provenance.py",
        failures,
    )
    operation_proof_tests = _read(
        "tests/test_governed_browser_operation_proofs.py",
        failures,
    )
    operation_proof_service_binding_tests = _read(
        "tests/test_governed_browser_operation_proof_service_bindings.py",
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
    financial_operation_tests = _read(
        "tests/test_governed_browser_queue01_group10.py", failures
    )
    artifact_transfer_review_tests = _read(
        "tests/test_governed_browser_queue01_group08_review_repairs.py",
        failures,
    )
    observation_tests = _read(
        "tests/test_governed_browser_queue01_group03.py",
        failures,
    )
    browser_action_tests = _read(
        "tests/test_governed_browser_queue01_group04.py",
        failures,
    )
    post_form_tests = _read(
        "tests/test_governed_browser_queue01_group05.py",
        failures,
    )
    origin_session_tests = _read(
        "tests/test_governed_browser_queue01_group06.py",
        failures,
    )
    human_challenge_tests = _read(
        "tests/test_governed_browser_queue01_group07.py",
        failures,
    )
    task_composer_tests = _read(
        "tests/test_governed_browser_queue01_group11.py",
        failures,
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
    post_forms = projection_sources[
        "src/ultimate_ai_agent/core/governed_browser/post_forms.py"
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
            "started_dispatch_timeout_seconds_if_exact",
            "dispatch_timeout_seconds",
            "_lost_start_claim_receipt",
            "start-persistence-failed",
            "claim_start_or_terminal",
            "finish-ownership-lost",
            "prior-start-recovery",
            "post-start-dispatch-not-invoked",
            "_TERMINAL_ACCOUNTING_REASON_MARKERS",
            "_bounded_external_action_reason_refs",
            "_bound_external_action_replay_store",
            "_register_external_action_store_replay_source",
            "_register_external_action_kernel_replay_source",
            "_attest_terminal_commit",
            "_record_terminal_receipt_binding",
            "reason-overflow",
            "dispatch-outcome-ambiguous",
            "budget-settlement-ambiguous",
            "budget-reservation-proof-missing",
            "_semantic_budget_status",
            "_prior_settlement",
            "reconcile_release",
            "_finalize_timed_out_dispatch",
            "_settle_and_finish_dispatch",
            "dispatch_ownership_transferred",
            "recover_if_prior_start(request)",
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
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_EXTERNAL_OPERATION_RECEIPT_STATE_MISMATCH",
            "_external_operation_receipt_identity_payload",
            "_external_operation_replay_validation_context",
            "require_external_action_replay_provenance",
        ),
        "financial_operations": (
            "budget_release_ref",
            "GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_FINANCIAL_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_FINANCIAL_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_FINANCIAL_RECEIPT_STATE_MISMATCH",
            "_financial_replay_validation_context",
            "require_external_action_replay_provenance",
        ),
        "artifact_transfers": (
            "download-payload-rejected",
            "download_payload_exceeds_max",
            "GOVERNED_ARTIFACT_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_ARTIFACT_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_ARTIFACT_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_ARTIFACT_RECEIPT_STATE_MISMATCH",
            "GOVERNED_ARTIFACT_PREFLIGHT_EXTERNAL_PROOF_DENIED",
            "GOVERNED_ARTIFACT_SUCCESS_KERNEL_PROOF_REQUIRED",
            "_artifact_replay_evidence_expectation",
            "_artifact_replay_validation_context",
            "require_external_action_replay_provenance",
            "GOVERNED_ARTIFACT_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
        ),
        "replay_provenance": (
            "ExternalActionReplayEvidenceExpectation",
            "ExternalActionReplayEvidenceEnvelope",
            "ExternalActionReplayValidationContext",
            "operation_proof_ref",
            "terminal_binding_ref",
            "_build_external_action_replay_validation_context",
            "_KERNEL_AMBIGUITY_REASON_BY_EVIDENCE_SUFFIX",
            "_ambiguity_provenance_valid",
            "_ambiguity_accounting_shape_valid",
            "attest_terminal_replay",
            "GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH",
            "GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
        ),
        "operation_proofs": (
            "GovernedBrowserOperationProof",
            "GovernedBrowserTerminalReceiptBinding",
            "BrowserObservationOperationProofMaterial",
            "BrowserActionPlanOperationProofMaterial",
            "PostFormPlanOperationProofMaterial",
            "OriginSessionOperationProofMaterial",
            "GovernedBrowserOperationProofStore",
            "MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES",
            "MAX_GOVERNED_BROWSER_OPERATION_PROOFS",
            "MAX_GOVERNED_BROWSER_TERMINAL_BINDINGS",
            "_record_operation_proof",
            "_attest_operation_proof",
            "_record_terminal_receipt_binding",
            "_attest_terminal_receipt_binding",
            "terminal-bindings",
            "_register_operation_proof_service",
            "_require_operation_proof_service",
            "_OperationProofStoreBinding",
            "_OperationProofServiceBinding",
            "O_NOFOLLOW",
            "O_EXCL",
            "fcntl.flock",
            "raw_content_persisted: Literal[False]",
            "credential_material_persisted: Literal[False]",
            "browser_authority_granted: Literal[False]",
            "network_authority_granted: Literal[False]",
            "mutation_authority_granted: Literal[False]",
            "execution_authority_granted: Literal[False]",
            "GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
            "GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH",
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED",
            "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID",
            "GOVERNED_BROWSER_TERMINAL_BINDING_REQUIRED",
            "GOVERNED_BROWSER_TERMINAL_BINDING_PROVENANCE_MISMATCH",
        ),
        "operation_proof_tests": (
            "test_store_save_is_idempotent_and_ignores_instance_method_shadows",
            "test_terminal_binding_attestation_ignores_instance_method_shadows",
            "test_recreated_terminal_binding_directory_changes_store_identity",
            "test_store_rejects_preexisting_symlink_root",
            "test_terminal_binding_write_failure_never_backfills_or_redispatches",
            "test_full_store_keeps_existing_save_idempotent_and_rejects_new_proof",
            "test_store_rejects_tampered_proof_without_recomputed_ref",
            "test_attestation_rejects_missing_proof",
            "test_store_rejects_symlinked_proof_file",
            "test_store_rejects_hardlinked_proof_file",
            "test_store_rejects_fifo_in_place_of_proof_file",
            "test_store_rejects_oversize_proof_file",
            "test_attestation_rejects_cross_operation_scope_substitution",
            "test_attestation_rejects_cross_transaction_substitution",
            "test_attestation_rejects_evidence_order_arity_and_field_tampering",
            "test_recomputed_proof_hash_cannot_cross_operation_boundary",
            "test_recomputed_proof_hash_cannot_reclassify_dispatch_outcome",
            "test_replay_context_binds_exact_operation_proof",
            "test_terminal_binding_rejects_ambiguity_rewritten_as_success",
            "test_terminal_binding_rejects_success_rewritten_as_generic_ambiguity",
            "test_terminal_binding_rejects_recomputed_evidence_envelope_tampering",
            "test_terminal_binding_rejects_recomputed_reason_and_accounting_changes",
            "test_terminal_binding_rejects_cross_operation_proof_substitution",
            "test_terminal_binding_rejects_cross_transaction_proof_substitution",
            "test_recomputed_terminal_binding_hash_cannot_rebind_request",
            "test_recomputed_terminal_receipt_cannot_substitute_proven_evidence",
        ),
        "operation_proof_service_binding_tests": (
            "test_observation_whole_dependency_substitution_cannot_redirect_replay",
            "test_action_whole_dependency_substitution_cannot_redirect_replay",
            "test_post_form_whole_dependency_substitution_cannot_redirect_replay",
            "test_origin_whole_dependency_substitution_cannot_redirect_replay",
            "test_observation_instance_helper_shadows_cannot_redirect_execution_or_replay",
            "test_action_instance_helper_shadows_cannot_redirect_execution_or_replay",
            "test_post_form_instance_helper_shadows_cannot_redirect_execution_or_replay",
            "test_origin_captured_helper_shadows_cannot_redirect_execution_or_replay",
        ),
        "replay_provenance_tests": (
            "test_clean_proof_uses_atomic_row_and_builds_deterministic_envelope",
            "test_clean_generic_ambiguity_replay_requires_terminal_binding",
            "test_legacy_terminal_without_binding_fails_closed",
            "test_structurally_compatible_fake_source_cannot_mint_context",
            "test_legitimate_token_cannot_authenticate_a_copied_context",
            "test_in_place_context_snapshot_mutation_fails_closed",
            "test_concrete_attestation_ignores_instance_method_substitution",
            "test_concrete_store_attestation_ignores_connector_and_lock_shadows",
            "test_connector_shadow_cannot_redirect_attestation_to_another_ledger",
            "test_store_path_or_whole_store_substitution_fails_closed",
            "test_concrete_serializers_ignore_request_replay_and_expectation_shadows",
            "test_candidate_model_dump_shadow_cannot_bypass_whole_receipt_match",
            "test_context_model_dump_json_shadow_cannot_hide_snapshot_mutation",
            "test_complete_terminal_evidence_envelope_accepts_only_defined_shapes",
            "test_undefined_terminal_evidence_envelopes_fail_closed",
            "test_kernel_ambiguity_evidence_requires_its_exact_primary_reason",
            "test_post_start_guard_replay_recomputes_the_complete_reason_envelope",
            "test_post_start_guard_overflow_uses_the_exact_bounded_reason_envelope",
            "test_lane_evidence_cannot_change_to_ambiguous_without_transition_proof",
            "test_lane_ambiguity_requires_an_exact_transition_and_accounting_shape",
            "test_operation_specific_ambiguity_requires_explicit_classification",
            "test_atomic_attestation_rejects_request_scope_drift",
            "test_atomic_attestation_rejects_nonterminal_row_state",
        ),
        "browser_actions": (
            "GOVERNED_BROWSER_ACTION_RECEIPT_REF_MISMATCH",
            "GOVERNED_BROWSER_ACTION_RESULT_RECEIPT_KIND_MISMATCH",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_BROWSER_ACTION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_BROWSER_ACTION_RECEIPT_STATE_MISMATCH",
            "GOVERNED_BROWSER_ACTION_REPLAY_STATUS_MISMATCH",
            "GOVERNED_BROWSER_ACTION_PREFLIGHT_EXTERNAL_PROOF_DENIED",
            "GOVERNED_BROWSER_ACTION_SUCCESS_KERNEL_PROOF_REQUIRED",
            "GOVERNED_BROWSER_ACTION_PLAN_RECEIPT_MISMATCH",
            "GOVERNED_BROWSER_ACTION_PLAN_PROJECTION_REF_MISMATCH",
            '"receipt-ref:governed-browser-action"',
            '"receipt-ref:governed-post-form"',
            "_browser_action_kernel_execution",
            "_browser_action_replay_expectation",
            "_record_operation_proof",
            "_attest_operation_proof",
            "_register_operation_proof_service",
            "require_external_action_replay_provenance",
        ),
        "observations": (
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_RECEIPT_STATE_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_REPLAY_STATUS_MISMATCH",
            "GOVERNED_BROWSER_OBSERVATION_PREFLIGHT_EXTERNAL_PROOF_DENIED",
            "GOVERNED_BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE",
            "_browser_observation_kernel_execution",
            "_browser_observation_replay_expectation",
            "_record_operation_proof",
            "_attest_operation_proof",
            "_register_operation_proof_service",
            "require_external_action_replay_provenance",
        ),
        "human_challenges": (
            "GOVERNED_HUMAN_CHALLENGE_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_HUMAN_CHALLENGE_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_HUMAN_CHALLENGE_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_HUMAN_CHALLENGE_RECEIPT_STATE_MISMATCH",
            "GOVERNED_HUMAN_CHALLENGE_REPLAY_STATUS_MISMATCH",
            "GOVERNED_HUMAN_CHALLENGE_PREFLIGHT_EXTERNAL_PROOF_DENIED",
            "GOVERNED_HUMAN_CHALLENGE_SUCCESS_KERNEL_PROOF_REQUIRED",
            "GOVERNED_HUMAN_CHALLENGE_RECEIPT_MISMATCH",
            "_human_challenge_replay_context",
            "require_external_action_replay_provenance",
        ),
        "origin_sessions": (
            "recipe_snapshot",
            "external_receipt_snapshot",
            "_origin_session_receipt_identity_payload",
            "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_SNAPSHOT_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_SNAPSHOT_SCOPE_MISMATCH",
            "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_EVIDENCE_MISMATCH",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_RECEIPT_SNAPSHOT_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_RECEIPT_PROJECTION_MISMATCH",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_INVALID",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_STATE_MISMATCH",
            "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_STATE_INVALID",
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_SUCCESS_KERNEL_PROOF_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_SUCCESS_PROJECTION_REQUIRED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_NON_SUCCESS_PROJECTION_DENIED",
            "GOVERNED_BROWSER_ORIGIN_SESSION_KEYCHAIN_PROJECTION_MISMATCH",
            "GOVERNED_BROWSER_ORIGIN_SESSION_RECORD_PROJECTION_MISMATCH",
            "_origin_session_kernel_execution",
            "_origin_session_replay_context",
            "_validate_origin_session_operation_proof",
            "_record_operation_proof",
            "_attest_operation_proof",
            "_register_operation_proof_service",
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_REQUIRED",
            "require_external_action_replay_provenance",
        ),
        "task_composer": (
            "ExternalActionReceipt(",
            "GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_REF_MISMATCH",
            "GOVERNED_TASK_COMPOSER_PROOF_INCOMPLETE_STATE_MISMATCH",
            "_task_composer_replay_context",
            "require_external_action_replay_provenance",
        ),
        "post_forms": (
            "GOVERNED_POST_FORM_RESULT_RECEIPT_KIND_MISMATCH",
            "GOVERNED_POST_FORM_PLAN_RECEIPT_MISMATCH",
            "GOVERNED_POST_FORM_PLAN_PROJECTION_REF_MISMATCH",
            '"receipt-ref:governed-post-form"',
            "_post_form_kernel_execution",
            "_post_form_replay_expectation",
            "_record_operation_proof",
            "_attest_operation_proof",
            "_register_operation_proof_service",
        ),
        "tests": (
            "test_queue02_package_exports_are_declared",
            "test_every_hostile_signal_blocks_before_dispatch",
            "test_every_observed_scope_dimension_is_revalidated",
            "test_stop_posture_race_after_start_becomes_ambiguous",
            "test_authority_revocation_race_after_reservation_blocks_start",
            "test_authority_revocation_waits_for_final_validation_and_dispatch",
            "test_dispatch_timeout_is_ambiguous_non_retryable_and_capacity_bounded",
            "test_ambiguous_dispatch_evidence_is_bound_to_each_exact_request",
            "test_dispatch_cannot_start_when_worker_misses_the_deadline",
            "test_worker_rechecks_expired_readiness_before_dispatch",
            "test_concurrent_execute_never_clobbers_the_dispatch_owner",
            "test_restart_recovery_cannot_terminalize_a_fresh_live_start",
            "test_restart_recovery_uses_the_maximum_owner_dispatch_window",
            "test_restart_recovery_uses_the_persisted_short_owner_dispatch_window",
            "test_restart_recovery_reaps_stale_process_slot_and_settles_budget",
            "test_stale_dispatch_slot_is_reaped_before_capacity_denial",
            "test_dispatch_capacity_is_shared_durably_across_kernel_instances",
            "test_dispatch_capacity_check_failure_is_terminal_and_replayed",
            "test_allowed_reservation_without_receipt_proof_is_released",
            "test_start_persistence_failure_releases_unused_reservation_and_dispatch_slot",
            "test_start_persistence_failure_surfaces_unconfirmed_budget_release",
            "test_reservation_cancellation_releases_dispatch_slot",
            "test_replayed_closed_reservation_is_not_active",
            "test_failed_terminal_write_cannot_reactivate_released_reservation",
            "test_lost_start_claim_releases_only_a_distinct_unused_reservation",
            "test_lost_start_claim_preserves_the_winners_shared_reservation",
            "test_same_request_contender_never_releases_live_owner_reservation",
            "test_lost_start_claim_surfaces_distinct_local_release_proof_after_terminal",
            "test_lost_start_claim_rejects_release_without_receipt_proof",
            "test_prestart_finish_cas_loss_returns_current_ambiguous_state",
            "test_browser_action_success_receipt_requires_complete_kernel_proof",
            "test_browser_action_receipt_identity_binds_budget_release_proof",
            "test_browser_action_preflight_rejects_proof_without_kernel_receipt",
            "test_browser_action_and_post_form_results_reject_cross_lane_receipts",
            "test_browser_action_result_binds_exact_plan_projection",
            "test_post_form_result_binds_exact_plan_projection",
            "test_browser_action_receipt_rejects_rehashed_kernel_proof_conflicts",
            "test_browser_action_receipt_rejects_rehashed_kernel_field_rebinding",
            "test_browser_action_non_preflight_receipt_requires_kernel_context",
            "test_browser_action_non_preflight_rejects_orphan_kernel_proof",
            "test_browser_action_receipt_rejects_kernel_state_status_mismatch",
            "test_browser_action_non_replay_status_rejects_replay_flag",
            "test_execute_automatically_recovers_a_stale_started_transaction",
            "test_recovery_reuses_a_prior_durable_settlement_proof",
            "test_recovery_reuses_a_prior_durable_release_proof",
            "test_replayed_denied_budget_release_remains_denied",
            "test_dispatch_slot_remains_owned_through_settlement_and_terminal_close",
            "test_dispatch_slot_is_owned_before_post_claim_revalidation",
            "test_terminal_compare_and_swap_rejects_overwrite",
            "test_reason_bounding_preserves_terminal_accounting_failures",
            "test_every_operator_receipt_contract_retains_budget_release_proof",
            "test_honest_matrix_covers_every_lane_and_keeps_every_lane_inactive",
        ),
        "external_operation_tests": (
            "test_external_operation_terminal_replay_reconstructs_exact_operation_evidence",
            "test_external_operation_terminal_replay_rejects_arbitrary_non_success_evidence",
            "test_external_operation_replay_rejects_every_rehashed_evidence_field_tamper",
            "test_external_operation_replay_rejects_rehashed_evidence_order_and_arity_tamper",
            "test_external_operation_replay_rejects_cross_operation_and_transaction_substitution",
            "test_operation_receipt_rejects_rebound_kernel_receipt_fields",
            "test_operation_preflight_rejects_release_proof_without_kernel_receipt",
            "test_operation_ready_receipt_preserves_validation_precedence",
            "test_operation_non_preflight_receipt_requires_kernel_context",
            "test_operation_receipt_rejects_kernel_state_status_mismatch",
            "test_operation_receipt_rejects_conflicting_rehashed_kernel_proofs",
            "test_operation_receipt_preserves_prestart_budget_release_proof",
            "test_failed_kernel_receipt_keeps_original_reason_identity",
            "test_legacy_failed_operation_receipt_preserves_empty_kernel_reasons",
            "test_legacy_failed_operation_receipt_preserves_nonempty_kernel_reasons",
        ),
        "financial_operation_tests": (
            "test_financial_terminal_replay_reconstructs_exact_operation_evidence",
            "test_financial_terminal_replay_rejects_arbitrary_non_success_evidence",
            "test_financial_replay_rejects_every_rehashed_evidence_field_tamper",
            "test_financial_replay_rejects_rehashed_evidence_order_and_arity_tamper",
            "test_financial_replay_rejects_cross_operation_substitution",
            "test_financial_replay_rejects_cross_transaction_substitution",
            "test_financial_receipt_rejects_budget_proof_without_kernel_receipt",
            "test_financial_non_preflight_receipt_requires_kernel_context",
            "test_financial_receipt_rejects_rebound_kernel_receipt_fields",
            "test_financial_receipt_rejects_conflicting_rehashed_kernel_proofs",
        ),
        "artifact_transfer_review_tests": (
            "test_oversized_download_payload_is_rejected_before_owned_copy",
            "test_artifact_receipt_rejects_rehashed_conflicting_kernel_proofs",
            "test_artifact_non_preflight_receipt_requires_kernel_context",
            "test_artifact_non_preflight_rejects_orphan_kernel_proof",
            "test_artifact_preflight_rejects_orphan_kernel_proof",
            "test_artifact_receipt_rejects_kernel_state_status_mismatch",
            "test_artifact_replayed_content_free_requires_succeeded_kernel_state",
            "test_artifact_replayed_success_rejects_standalone_rehashed_scope_forgery",
            "test_artifact_replay_requires_exact_durable_provenance_context",
            "test_artifact_terminal_replay_reconstructs_exact_operation_evidence",
            "test_artifact_terminal_replay_rejects_arbitrary_non_success_evidence",
            "test_artifact_replay_rejects_every_rehashed_evidence_field_tamper",
            "test_artifact_replay_rejects_rehashed_evidence_order_and_arity_tamper",
            "test_artifact_replay_rejects_cross_operation_and_transaction_substitution",
            "test_artifact_replayed_success_requires_complete_kernel_proof",
            "evidence-ref:governed-artifact:download-payload-rejected",
        ),
        "observation_tests": (
            "test_observation_receipt_rejects_rehashed_conflicting_kernel_proofs",
            "test_observation_non_preflight_receipt_requires_kernel_context",
            "test_observation_non_preflight_rejects_orphan_kernel_proof",
            "test_observation_preflight_rejects_orphan_kernel_proof",
            "test_observation_receipt_rejects_kernel_state_status_mismatch",
            "test_observation_non_replay_status_rejects_replay_flag",
            "test_observation_replayed_success_requires_complete_kernel_proof",
            "test_observation_replay_requires_exact_durable_provenance",
            "test_observation_recipe_identity_conflicts_on_same_transaction",
        ),
        "browser_action_tests": (
            "test_action_replay_requires_exact_durable_provenance",
            "test_action_blocked_and_failed_terminals_replay_content_free",
            "test_action_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity",
        ),
        "post_form_tests": (
            "test_post_form_replay_requires_exact_durable_provenance",
            "test_post_form_blocked_and_failed_terminals_replay_content_free",
            "test_post_form_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity",
        ),
        "origin_session_tests": (
            "test_origin_receipt_snapshot_preserves_outer_identity_and_is_required",
            "test_origin_receipt_rejects_conflicting_or_rebound_kernel_snapshot",
            "test_origin_receipt_rejects_cross_operation_recipe_rebinding",
            "test_origin_receipt_binds_success_evidence_to_exact_recipe_snapshot",
            "test_origin_succeeded_snapshot_requires_complete_kernel_proof",
            "test_origin_non_preflight_receipt_requires_kernel_context",
            "test_origin_preflight_rejects_orphan_kernel_proof",
            "test_origin_receipt_rejects_external_state_status_or_operation_mismatch",
            "test_origin_result_requires_exact_success_projections",
            "test_fresh_store_revoke_allows_absent_session_projection",
            "test_non_success_origin_result_rejects_unrelated_projection",
            "test_idempotent_distinct_origin_transactions_accept_existing_record",
            "test_origin_replay_reconstruction_requires_exact_terminal_provenance",
            "test_origin_non_success_terminal_replays_use_complete_envelope",
            "test_origin_replay_expectation_rejects_invalid_non_success_envelopes",
            "test_origin_replay_rejects_fully_rehashed_evidence_tampering",
            "test_origin_replay_rejects_cross_scope_provenance_substitution",
        ),
        "human_challenge_tests": (
            "test_handoff_receipt_rejects_rehashed_conflicting_kernel_proofs",
            "test_handoff_non_preflight_receipt_requires_kernel_context",
            "test_handoff_non_preflight_rejects_orphan_kernel_proof",
            "test_handoff_preflight_rejects_orphan_kernel_proof",
            "test_handoff_receipt_rejects_kernel_state_status_mismatch",
            "test_handoff_non_replay_status_rejects_replay_flag",
            "test_handoff_replayed_success_requires_complete_kernel_proof",
            "test_handoff_result_rejects_cross_projection_binding",
            "test_handoff_replay_reconstruction_requires_exact_terminal_provenance",
            "test_handoff_non_success_terminal_replays_use_complete_envelope",
            "test_handoff_replay_expectation_rejects_invalid_non_success_envelopes",
            "test_handoff_replay_rejects_fully_rehashed_evidence_tampering",
            "test_handoff_replay_rejects_cross_transaction_recipe_context",
        ),
        "task_composer_tests": (
            "test_serialized_external_receipt_snapshot_rejects_conflicting_rehashed_kernel_proofs",
            "test_serialized_task_composition_receipt_rejects_conflicting_rehashed_kernel_proofs",
            "test_incomplete_succeeded_kernel_proof_is_content_free_without_plan",
            "test_incomplete_succeeded_kernel_evidence_is_content_free_without_plan",
            "test_started_or_prepared_kernel_state_is_outcome_ambiguous",
            "test_preflight_receipt_rejects_orphan_replay_flag",
            "test_complete_success_proof_cannot_downgrade_to_proof_incomplete",
            "test_task_composer_replay_wrappers_require_exact_terminal_provenance",
            "test_task_composer_non_success_terminal_replays_use_complete_envelope",
            "test_task_composer_replay_expectation_rejects_invalid_non_success_envelopes",
            "test_task_composer_replay_rejects_fully_rehashed_evidence_tampering",
            "test_task_composer_replay_rejects_cross_transaction_recipe_context",
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
            "exact durable-terminal provenance",
            "lane/operation-specific ordered evidence",
            "independent content-free operation proof",
            "exact terminal kernel row",
            "structural provenance only",
            "not signatures",
            "legacy proof or terminal binding fails closed",
            "fresh durable terminal commit",
            "Every replay context",
            "proof-less",
            "owner-level rewriting",
            "cross-transaction substitution",
        ),
    }
    texts = {
        "contracts": contracts,
        "transaction": transaction,
        "hardening": hardening,
        "replay_provenance": replay_provenance,
        "operation_proofs": operation_proofs,
        "operation_proof_tests": operation_proof_tests,
        "operation_proof_service_binding_tests": (
            operation_proof_service_binding_tests
        ),
        "replay_provenance_tests": replay_provenance_tests,
        "external_operations": external_operations,
        "financial_operations": projection_sources[
            "src/ultimate_ai_agent/core/governed_browser/financial_operation_contracts.py"
        ],
        "artifact_transfers": projection_sources[
            "src/ultimate_ai_agent/core/governed_browser/artifact_transfers.py"
        ],
        "browser_actions": browser_actions,
        "observations": projection_sources[
            "src/ultimate_ai_agent/core/governed_browser/evidence_recipes.py"
        ],
        "human_challenges": projection_sources[
            "src/ultimate_ai_agent/core/governed_browser/human_challenges.py"
        ],
        "origin_sessions": origin_sessions,
        "task_composer": projection_sources[
            "src/ultimate_ai_agent/core/governed_browser/task_composer.py"
        ],
        "post_forms": post_forms,
        "tests": tests,
        "external_operation_tests": external_operation_tests,
        "financial_operation_tests": financial_operation_tests,
        "artifact_transfer_review_tests": artifact_transfer_review_tests,
        "observation_tests": observation_tests,
        "browser_action_tests": browser_action_tests,
        "post_form_tests": post_form_tests,
        "origin_session_tests": origin_session_tests,
        "human_challenge_tests": human_challenge_tests,
        "task_composer_tests": task_composer_tests,
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
            failures.append(f"Queue 02 budget release projection missing: {relative}")
    if (
        '"budget_release_ref": (' not in origin_sessions
        or "external_receipt.budget_release_ref" not in origin_sessions
    ):
        failures.append(
            "Queue 02 budget release projection missing: origin_sessions.py"
        )
    identity_sources = {
        relative: source
        for relative, source in projection_sources.items()
        if relative.endswith(
            (
                "artifact_transfers.py",
                "browser_actions.py",
                "evidence_recipes.py",
                "financial_operation_contracts.py",
                "human_challenges.py",
                "post_forms.py",
            )
        )
    }
    identity_sources[
        "src/ultimate_ai_agent/core/governed_browser/origin_sessions.py"
    ] = origin_sessions
    if "def governed_receipt_identity_payload" not in contracts:
        failures.append("Queue 02 governed receipt identity helper missing")
    for relative, source in identity_sources.items():
        if "governed_receipt_identity_payload" not in source:
            failures.append(f"Queue 02 portable receipt identity missing: {relative}")
        if "exclude_if" in source:
            failures.append(
                f"Queue 02 version-sensitive receipt identity present: {relative}"
            )

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
