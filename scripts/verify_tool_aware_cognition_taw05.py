from __future__ import annotations

from ultimate_ai_agent.core.capabilities import (
    OperatorCorrectionEvidence,
    OutcomeLifecycleEvidence,
    TerminalReceiptStatus,
    build_attempt_start_evidence,
    build_capability_outcome_contract,
    build_outcome_evaluation_policy,
    evaluate_operator_correction,
    project_capability_outcomes,
    project_outcome_lifecycle,
)


def verify() -> None:
    policy = build_outcome_evaluation_policy(
        policy_snapshot_ref="policy-snapshot-ref:taw05:verifier-v1",
        evaluator_revision_ref="evaluator-revision-ref:taw05:verifier-v1",
        reviewed_completion_sla_ref="completion-sla-ref:taw05:verifier-v1",
        reviewed_completion_sla_seconds=60,
        repository_hard_max_window_seconds=300,
        clock_source_ref="clock-source-ref:taw05:verifier-v1",
    )
    contract = build_capability_outcome_contract(
        operation_id="operation-ref:taw05:verifier",
        capability_contract_version="1.0.0",
        operation_schema_fingerprint_ref=(
            "operation-schema-ref:taw01:sha256:" + "5" * 64
        ),
        policy=policy,
        completion_window_seconds=60,
        environment_class_refs=("environment-class-ref:taw05:private-dogfood",),
        terminal_status_refs={
            status: f"terminal-status-ref:taw05:verifier:{status.value}"
            for status in TerminalReceiptStatus
        },
    )
    start = build_attempt_start_evidence(
        contract=contract,
        execution_attempt_ref="execution-attempt-ref:taw05:verifier",
        durable_start_evidence_ref="durable-start-evidence-ref:taw05:verifier",
        environment_class_ref="environment-class-ref:taw05:private-dogfood",
        started_at_epoch_seconds=100,
    )
    projection = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
    )
    if (
        projection.unresolved_overdue_count != 1
        or projection.non_success_count != 1
        or projection.health_rate_denominator != 1
        or projection.prior_status != "absent"
    ):
        raise RuntimeError("TAW-05 verifier detected outcome census drift")
    if (
        not projection.non_authoritative
        or any(
            (
                projection.durable_statistics_store_mutated,
                projection.receipt_arrival_handler_registered,
                projection.online_training_performed,
                projection.automatic_policy_or_alias_promotion,
                projection.provider_call_performed,
                projection.runtime_execution_performed,
                projection.connector_call_performed,
                projection.external_write_performed,
                projection.public_claim_made,
                projection.authority_granted,
                projection.production_authority_granted,
            )
        )
        or projection.model_call_count != 0
        or projection.second_ordinary_chat_model_call_count != 0
    ):
        raise RuntimeError("TAW-05 verifier detected authority expansion")

    lifecycle = project_outcome_lifecycle(
        OutcomeLifecycleEvidence(
            proposal_ref="proposal-ref:taw05:verifier",
            approval_ref="approval-ref:taw05:verifier",
        )
    )
    if (
        lifecycle.posture != "ordinary_canonical_lifecycle"
        or not lifecycle.ordinary_lifecycle_posture_preserved
    ):
        raise RuntimeError("TAW-05 verifier detected lifecycle posture drift")

    correction = evaluate_operator_correction(
        OperatorCorrectionEvidence(
            correction_ref="correction-ref:taw05:verifier",
            source_revision_ref="source-revision-ref:taw05:verifier",
            transformation_kind="untransformed",
            review_status="pending",
            content_safety_status="not_run",
        )
    )
    if correction.disposition != "blocked" or correction.durable_eval_eligible:
        raise RuntimeError("TAW-05 verifier detected unsafe correction promotion")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-05 outcome evidence verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
