from __future__ import annotations

from collections.abc import Iterator
from enum import Enum

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capabilities import (
    CapabilityOutcomeProjection,
    OperatorCorrectionEvidence,
    OutcomeLifecycleEvidence,
    OutcomeObservationClass,
    OutcomePriorEvidence,
    TerminalReceiptStatus,
    build_attempt_start_evidence,
    build_capability_outcome_contract,
    build_outcome_evaluation_policy,
    build_terminal_receipt_evidence,
    evaluate_operator_correction,
    project_capability_outcomes,
    project_outcome_lifecycle,
)
from ultimate_ai_agent.core.capabilities import outcomes


OPERATION_SCHEMA_REF = "operation-schema-ref:taw01:sha256:" + "a" * 64


def _policy(
    *,
    evaluator_revision_ref: str = "evaluator-revision-ref:taw05:v1",
    repository_hard_max_window_seconds: int = 300,
):
    return build_outcome_evaluation_policy(
        policy_snapshot_ref="policy-snapshot-ref:taw05:v1",
        evaluator_revision_ref=evaluator_revision_ref,
        reviewed_completion_sla_ref="completion-sla-ref:taw05:reviewed-v1",
        reviewed_completion_sla_seconds=60,
        repository_hard_max_window_seconds=repository_hard_max_window_seconds,
        clock_source_ref="clock-source-ref:taw05:monotonic-v1",
    )


def _contract(*, policy=None, operation_schema_ref: str = OPERATION_SCHEMA_REF):
    policy = policy or _policy()
    return build_capability_outcome_contract(
        operation_id="operation-ref:taw05:reviewed-action",
        capability_contract_version="1.0.0",
        operation_schema_fingerprint_ref=operation_schema_ref,
        policy=policy,
        completion_window_seconds=60,
        environment_class_refs=("environment-class-ref:taw05:local-private",),
        terminal_status_refs={
            status: f"terminal-status-ref:taw05:{status.value}"
            for status in TerminalReceiptStatus
        },
    )


def _start(contract, index: int, *, started_at: int = 100):
    return build_attempt_start_evidence(
        contract=contract,
        execution_attempt_ref=f"execution-attempt-ref:taw05:{index}",
        durable_start_evidence_ref=f"durable-start-evidence-ref:taw05:{index}",
        environment_class_ref="environment-class-ref:taw05:local-private",
        started_at_epoch_seconds=started_at,
    )


def _receipt(contract, start, status: TerminalReceiptStatus, *, terminal_at: int = 120):
    return build_terminal_receipt_evidence(
        contract=contract,
        start=start,
        terminal_receipt_ref=(
            f"terminal-receipt-evidence-ref:taw05:"
            f"{start.execution_attempt_ref.rsplit(':', 1)[-1]}:{status.value}"
        ),
        terminal_status=status,
        terminal_at_epoch_seconds=terminal_at,
        terminal_evidence_refs=(f"terminal-proof-ref:taw05:{status.value}",),
    )


def _projection_payload_with_fingerprint(projection, **updates):
    payload = projection.model_dump(mode="python")
    payload.update(updates)
    payload["projection_fingerprint_ref"] = outcomes._fingerprint(
        {
            key: value
            for key, value in payload.items()
            if key != "projection_fingerprint_ref"
        },
        prefix="outcome-projection-ref:taw05",
    )
    return payload


def test_terminal_enums_use_the_python_310_compatible_string_enum_pattern() -> None:
    assert TerminalReceiptStatus.__bases__ == (str, Enum)
    assert OutcomeObservationClass.__bases__ == (str, Enum)


def test_projection_recomputes_complete_census_and_keeps_authority_zero() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    starts = tuple(
        _start(contract, index, started_at=100 if index < 5 else 190)
        for index in range(6)
    )
    statuses = tuple(TerminalReceiptStatus)
    receipts = tuple(
        _receipt(contract, starts[index], status)
        for index, status in enumerate(statuses)
    )

    projection = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=starts,
        receipts=receipts,
        as_of_epoch_seconds=200,
    )

    assert projection.attempt_inventory_count == 6
    assert projection.terminal_count == 4
    assert projection.still_live_count == 1
    assert projection.unresolved_overdue_count == 1
    assert projection.succeeded_count == 1
    assert projection.non_success_count == 4
    assert projection.health_rate_denominator == 5
    assert projection.reliability_rate_denominator == 5
    assert projection.familiarity_rate_denominator == 5
    assert projection.success_basis_points == 2_000
    assert projection.prior_status == "absent"
    assert projection.non_authoritative
    assert not any(
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
    assert projection.model_call_count == 0
    assert projection.second_ordinary_chat_model_call_count == 0


def test_exact_replay_is_deduplicated() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    start = _start(contract, 1)
    receipt = _receipt(contract, start, TerminalReceiptStatus.succeeded)

    projection = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start, start),
        receipts=(receipt, receipt),
        as_of_epoch_seconds=200,
    )

    assert projection.attempt_inventory_count == 1
    assert projection.terminal_count == 1
    assert projection.succeeded_count == 1


def test_projection_deserialization_rejects_duplicate_observation_identities() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    projection = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(_start(contract, 1),),
        receipts=(),
        as_of_epoch_seconds=200,
    )
    observation = projection.observations[0].model_dump(mode="json")
    duplicated = _projection_payload_with_fingerprint(
        projection,
        attempt_inventory_count=2,
        unresolved_overdue_count=2,
        non_success_count=2,
        health_rate_denominator=2,
        reliability_rate_denominator=2,
        familiarity_rate_denominator=2,
        observations=(observation, observation),
    )

    with pytest.raises(ValidationError, match="unique attempt refs"):
        CapabilityOutcomeProjection.model_validate(duplicated)


def test_conflicting_attempt_or_receipt_reuse_invalidates_projection() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    start = _start(contract, 1)
    conflicting_start_payload = start.model_dump(mode="python")
    conflicting_start_payload["started_at_epoch_seconds"] = 101
    conflicting_start_payload["start_fingerprint_ref"] = outcomes._fingerprint(
        {
            key: value
            for key, value in conflicting_start_payload.items()
            if key != "start_fingerprint_ref"
        },
        prefix="attempt-start-ref:taw05",
    )
    receipt = _receipt(contract, start, TerminalReceiptStatus.succeeded)
    conflicting_receipt = _receipt(contract, start, TerminalReceiptStatus.failed)

    with pytest.raises(ValueError, match="conflicting reuse of attempt ref"):
        project_capability_outcomes(
            policy=policy,
            contract=contract,
            starts=(start, conflicting_start_payload),
            receipts=(),
            as_of_epoch_seconds=200,
        )
    with pytest.raises(ValueError, match="conflicting reuse of attempt receipt"):
        project_capability_outcomes(
            policy=policy,
            contract=contract,
            starts=(start,),
            receipts=(receipt, conflicting_receipt),
            as_of_epoch_seconds=200,
        )


def test_receipts_require_exact_start_binding_and_valid_time() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    start = _start(contract, 1)
    other_start = _start(contract, 2)
    receipt = _receipt(contract, start, TerminalReceiptStatus.succeeded)
    other_receipt = _receipt(contract, other_start, TerminalReceiptStatus.succeeded)

    with pytest.raises(ValueError, match="no exact bound start"):
        project_capability_outcomes(
            policy=policy,
            contract=contract,
            starts=(),
            receipts=(receipt,),
            as_of_epoch_seconds=200,
        )
    with pytest.raises(ValueError, match="no exact bound start"):
        project_capability_outcomes(
            policy=policy,
            contract=contract,
            starts=(start,),
            receipts=(other_receipt,),
            as_of_epoch_seconds=200,
        )
    with pytest.raises(ValueError, match="after the as-of cutoff"):
        project_capability_outcomes(
            policy=policy,
            contract=contract,
            starts=(start,),
            receipts=(receipt,),
            as_of_epoch_seconds=110,
        )
    with pytest.raises(ValueError, match="durable start binding mismatch"):
        _receipt(
            contract,
            _start(contract, 3, started_at=150),
            TerminalReceiptStatus.failed,
            terminal_at=149,
        )


def test_policy_window_and_environment_bindings_fail_closed() -> None:
    policy = _policy()
    with pytest.raises(ValueError, match="must equal the reviewed completion SLA"):
        build_capability_outcome_contract(
            operation_id="operation-ref:taw05:reviewed-action",
            capability_contract_version="1.0.0",
            operation_schema_fingerprint_ref=OPERATION_SCHEMA_REF,
            policy=policy,
            completion_window_seconds=61,
            environment_class_refs=("environment-class-ref:taw05:local-private",),
            terminal_status_refs={
                status: f"terminal-status-ref:taw05:{status.value}"
                for status in TerminalReceiptStatus
            },
        )
    with pytest.raises(ValueError, match="hard maximum"):
        build_outcome_evaluation_policy(
            policy_snapshot_ref="policy-snapshot-ref:taw05:v1",
            evaluator_revision_ref="evaluator-revision-ref:taw05:v1",
            reviewed_completion_sla_ref="completion-sla-ref:taw05:reviewed-v1",
            reviewed_completion_sla_seconds=301,
            repository_hard_max_window_seconds=300,
            clock_source_ref="clock-source-ref:taw05:monotonic-v1",
        )
    contract = _contract(policy=policy)
    with pytest.raises(ValueError, match="binding mismatch"):
        build_attempt_start_evidence(
            contract=contract,
            execution_attempt_ref="execution-attempt-ref:taw05:wrong-environment",
            durable_start_evidence_ref="durable-start-evidence-ref:taw05:wrong",
            environment_class_ref="environment-class-ref:taw05:not-reviewed",
            started_at_epoch_seconds=100,
        )


def test_iterable_inputs_are_bounded_before_full_materialization() -> None:
    policy = _policy()

    def environments() -> Iterator[str]:
        for index in range(17):
            yield f"environment-class-ref:taw05:{index}"
        raise AssertionError("environment iterator was over-consumed")

    with pytest.raises(ValueError, match="bound of 16"):
        build_capability_outcome_contract(
            operation_id="operation-ref:taw05:reviewed-action",
            capability_contract_version="1.0.0",
            operation_schema_fingerprint_ref=OPERATION_SCHEMA_REF,
            policy=policy,
            completion_window_seconds=60,
            environment_class_refs=environments(),
            terminal_status_refs={
                status: f"terminal-status-ref:taw05:{status.value}"
                for status in TerminalReceiptStatus
            },
        )


def test_priors_are_non_authoritative_and_stale_bindings_are_invalidated() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    start = _start(contract, 1)
    baseline = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
    )
    prior = OutcomePriorEvidence(
        prior_evidence_ref="prior-evidence-ref:taw05:one",
        projection_fingerprint_ref=baseline.projection_fingerprint_ref,
        contract_fingerprint_ref=contract.contract_fingerprint_ref,
        policy_fingerprint_ref=policy.policy_fingerprint_ref,
        operation_schema_fingerprint_ref=contract.operation_schema_fingerprint_ref,
        policy_snapshot_ref=policy.policy_snapshot_ref,
        evaluator_revision_ref=policy.evaluator_revision_ref,
    )
    current = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
        prior=prior,
    )
    stale = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
        prior=prior.model_copy(
            update={"evaluator_revision_ref": "evaluator-revision-ref:taw05:old"}
        ),
    )

    assert current.prior_status == "current_non_authoritative"
    assert stale.prior_status == "invalidated_stale"
    assert current.succeeded_count == stale.succeeded_count == 0
    assert current.non_success_count == stale.non_success_count == 1


def test_prior_policy_fingerprint_change_invalidates_otherwise_matching_prior() -> None:
    policy = _policy()
    contract = _contract(policy=policy)
    start = _start(contract, 1)
    baseline = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
    )
    prior = OutcomePriorEvidence(
        prior_evidence_ref="prior-evidence-ref:taw05:policy-change",
        projection_fingerprint_ref=baseline.projection_fingerprint_ref,
        contract_fingerprint_ref=contract.contract_fingerprint_ref,
        policy_fingerprint_ref=policy.policy_fingerprint_ref,
        operation_schema_fingerprint_ref=contract.operation_schema_fingerprint_ref,
        policy_snapshot_ref=policy.policy_snapshot_ref,
        evaluator_revision_ref=policy.evaluator_revision_ref,
    )
    revised_policy = _policy(repository_hard_max_window_seconds=600)

    projection = project_capability_outcomes(
        policy=revised_policy,
        contract=contract,
        starts=(start,),
        receipts=(),
        as_of_epoch_seconds=200,
        prior=prior,
    )

    assert revised_policy.policy_fingerprint_ref != policy.policy_fingerprint_ref
    assert projection.prior_status == "invalidated_stale"


def test_lifecycle_marks_only_started_missing_terminal_as_uncertain() -> None:
    contract = _contract()
    start = _start(contract, 1)
    receipt = _receipt(contract, start, TerminalReceiptStatus.rolled_back)

    ordinary = project_outcome_lifecycle(
        OutcomeLifecycleEvidence(
            proposal_ref="proposal-ref:taw05:one",
            approval_ref="approval-ref:taw05:one",
        )
    )
    uncertain = project_outcome_lifecycle(
        OutcomeLifecycleEvidence(contract=contract, start_evidence=start)
    )
    terminal = project_outcome_lifecycle(
        OutcomeLifecycleEvidence(
            contract=contract,
            start_evidence=start,
            terminal_receipt=receipt,
        )
    )

    assert ordinary.posture == "ordinary_canonical_lifecycle"
    assert ordinary.ordinary_lifecycle_posture_preserved
    assert uncertain.posture == "outcome_uncertain"
    assert terminal.posture == "terminal_evidence_available"
    assert terminal.model_call_count == 0
    assert terminal.second_ordinary_chat_model_call_count == 0
    assert not terminal.runtime_execution_performed
    assert not terminal.provider_call_performed
    assert not terminal.connector_call_performed
    assert not terminal.external_write_performed
    assert not terminal.public_claim_made
    assert not terminal.authority_granted
    assert not terminal.production_authority_granted


def test_lifecycle_requires_governing_contract_for_durable_start() -> None:
    contract = _contract()

    with pytest.raises(ValidationError, match="requires governing contract"):
        OutcomeLifecycleEvidence(start_evidence=_start(contract, 1))


def test_lifecycle_rejects_receipt_from_a_different_contract() -> None:
    contract = _contract()
    start = _start(contract, 1)
    receipt = _receipt(contract, start, TerminalReceiptStatus.succeeded)
    other_contract = _contract(
        policy=_policy(evaluator_revision_ref="evaluator-revision-ref:taw05:v2")
    )
    substituted_payload = receipt.model_dump(mode="python")
    substituted_payload.update(
        operation_id=other_contract.operation_id,
        contract_fingerprint_ref=other_contract.contract_fingerprint_ref,
        operation_schema_fingerprint_ref=(
            other_contract.operation_schema_fingerprint_ref
        ),
        policy_snapshot_ref=other_contract.policy_snapshot_ref,
        evaluator_revision_ref=other_contract.evaluator_revision_ref,
    )
    substituted_payload["receipt_fingerprint_ref"] = outcomes._fingerprint(
        {
            key: value
            for key, value in substituted_payload.items()
            if key != "receipt_fingerprint_ref"
        },
        prefix="terminal-receipt-ref:taw05",
    )
    substituted_receipt = outcomes.TerminalReceiptEvidence.model_validate(
        substituted_payload
    )

    with pytest.raises(ValueError, match="outcome contract binding mismatch"):
        OutcomeLifecycleEvidence(
            contract=contract,
            start_evidence=start,
            terminal_receipt=substituted_receipt,
        )


def test_lifecycle_rejects_terminal_status_ref_rebound_outside_contract() -> None:
    contract = _contract()
    start = _start(contract, 1)
    receipt = _receipt(contract, start, TerminalReceiptStatus.succeeded)
    rebound_payload = receipt.model_dump(mode="python")
    rebound_payload["terminal_status"] = TerminalReceiptStatus.failed
    rebound_payload["receipt_fingerprint_ref"] = outcomes._fingerprint(
        {
            key: value
            for key, value in rebound_payload.items()
            if key != "receipt_fingerprint_ref"
        },
        prefix="terminal-receipt-ref:taw05",
    )
    rebound_receipt = outcomes.TerminalReceiptEvidence.model_validate(rebound_payload)

    with pytest.raises(ValueError, match="outcome contract binding mismatch"):
        OutcomeLifecycleEvidence(
            contract=contract,
            start_evidence=start,
            terminal_receipt=rebound_receipt,
        )


def test_operator_corrections_require_transformation_review_and_safety() -> None:
    blocked = evaluate_operator_correction(
        OperatorCorrectionEvidence(
            correction_ref="correction-ref:taw05:blocked",
            source_revision_ref="source-revision-ref:taw05:one",
            transformation_kind="untransformed",
            review_status="pending",
            content_safety_status="not_run",
        )
    )
    eligible = evaluate_operator_correction(
        OperatorCorrectionEvidence(
            correction_ref="correction-ref:taw05:eligible",
            source_revision_ref="source-revision-ref:taw05:two",
            transformation_kind="fully_redacted",
            transformed_fixture_ref="transformed-fixture-ref:taw05:two",
            review_status="accepted",
            independent_review_ref="independent-review-ref:taw05:two",
            content_safety_status="passed",
            content_safety_receipt_ref="content-safety-receipt-ref:taw05:two",
        )
    )

    assert blocked.disposition == "blocked"
    assert eligible.disposition == "eligible_for_separate_durable_promotion"
    assert eligible.durable_eval_eligible
    assert not any(
        (
            eligible.automatic_eval_promotion_performed,
            eligible.durable_fixture_written,
            eligible.policy_or_alias_updated,
            eligible.online_training_performed,
            eligible.provider_call_performed,
            eligible.runtime_execution_performed,
            eligible.connector_call_performed,
            eligible.external_write_performed,
            eligible.public_claim_made,
            eligible.authority_granted,
            eligible.production_authority_granted,
        )
    )
    assert eligible.model_call_count == 0
    assert eligible.second_ordinary_chat_model_call_count == 0


def test_correction_decision_fingerprint_binds_exact_reviewed_evidence() -> None:
    first = OperatorCorrectionEvidence(
        correction_ref="correction-ref:taw05:shared",
        source_revision_ref="source-revision-ref:taw05:first",
        transformation_kind="fully_redacted",
        transformed_fixture_ref="transformed-fixture-ref:taw05:first",
        review_status="accepted",
        independent_review_ref="independent-review-ref:taw05:first",
        content_safety_status="passed",
        content_safety_receipt_ref="content-safety-receipt-ref:taw05:first",
    )
    second = first.model_copy(
        update={
            "source_revision_ref": "source-revision-ref:taw05:second",
            "transformed_fixture_ref": "transformed-fixture-ref:taw05:second",
            "independent_review_ref": "independent-review-ref:taw05:second",
            "content_safety_receipt_ref": (
                "content-safety-receipt-ref:taw05:second"
            ),
        }
    )

    first_decision = evaluate_operator_correction(first)
    second_decision = evaluate_operator_correction(second)

    assert first_decision.correction_ref == second_decision.correction_ref
    assert (
        first_decision.evidence_fingerprint_ref
        != second_decision.evidence_fingerprint_ref
    )
    assert (
        first_decision.decision_fingerprint_ref
        != second_decision.decision_fingerprint_ref
    )


def test_raw_correction_content_and_recomputed_count_drift_are_rejected() -> None:
    with pytest.raises(ValidationError):
        OperatorCorrectionEvidence.model_validate(
            {
                "correction_ref": "correction-ref:taw05:raw",
                "source_revision_ref": "source-revision-ref:taw05:raw",
                "transformation_kind": "untransformed",
                "review_status": "pending",
                "content_safety_status": "not_run",
                "raw_prompt": "disallowed",
            }
        )

    policy = _policy()
    contract = _contract(policy=policy)
    projection = project_capability_outcomes(
        policy=policy,
        contract=contract,
        starts=(_start(contract, 1),),
        receipts=(),
        as_of_epoch_seconds=200,
    )
    corrupted = _projection_payload_with_fingerprint(
        projection,
        still_live_count=1,
        unresolved_overdue_count=0,
        non_success_count=0,
        health_rate_denominator=0,
        reliability_rate_denominator=0,
        familiarity_rate_denominator=0,
        success_basis_points=None,
    )
    with pytest.raises(ValidationError, match="recomputed from observations"):
        CapabilityOutcomeProjection.model_validate(corrupted)
